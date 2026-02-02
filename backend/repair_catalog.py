import sqlite3
import os
import requests
import time
import logging
import argparse
import hashlib
import re
from datetime import datetime
from typing import Optional, List, Dict
from database import get_conn, save_embed
from playwright_scraper import get_scraper

# Configuration
TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"
BASE_URL = "https://api.themoviedb.org/3"

def setup_logging(worker_id=None):
    log_name = f"repair_{worker_id}.log" if worker_id is not None else "repair.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [Worker %(worker_id)s] - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_name),
            logging.StreamHandler()
        ]
    )

def clean_title(title):
    title = re.sub(r'\(\d{4}\)', '', title)
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\(.*?\)', '', title)
    return title.strip()

def search_tmdb(title, year=None):
    try:
        cleaned_title = clean_title(title)
        url = f"{BASE_URL}/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": cleaned_title, "language": "pt-BR", "page": 1}
        if year: params["year"] = year
        res = requests.get(url, params=params)
        data = res.json()
        if not data.get("results") and year:
            del params["year"]
            res = requests.get(url, params=params)
            data = res.json()
        if data.get("results"):
            return data["results"][0]
    except Exception as e:
        logging.error(f"TMDB Search Error: {e}")
    return None

def get_broken_items(worker_id, total_workers):
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # We look for items missing poster OR having invalid video links
        # We join with catalog_raw on title or original_raw_title to get detail_url
        query = """
            SELECT 
                l.title, l.tmdb_id, l.poster_path, l.embed_url, l.repair_attempts,
                c.raw_title, c.year, c.detail_url
            FROM links l
            LEFT JOIN catalog_raw c ON (l.original_raw_title = c.raw_title OR l.title = c.raw_title)
            WHERE 
                ( (l.poster_path IS NULL OR l.poster_path = '') AND (l.repair_attempts < 5) ) OR 
                ( (l.embed_url = 'NOT_FOUND' OR l.embed_url LIKE '%web.operatopzera.net%') AND (l.repair_attempts < 10) )
        """
        c.execute(query)
        rows = c.fetchall()
        
        # Sharding
        sharded = []
        for row in rows:
            title = row['title']
            title_hash = int(hashlib.md5(title.encode()).hexdigest(), 16)
            if title_hash % total_workers == worker_id:
                sharded.append(row)
        
        return sharded

def update_repair_status(title, success=False):
    with get_conn() as conn:
        c = conn.cursor()
        if success:
            c.execute("UPDATE links SET repair_attempts = 0, last_repair_date = ? WHERE title = ?", (datetime.utcnow(), title))
        else:
            c.execute("UPDATE links SET repair_attempts = repair_attempts + 1, last_repair_date = ? WHERE title = ?", (datetime.utcnow(), title))
        conn.commit()

def repair_worker(worker_id, total_workers):
    setup_logging(worker_id)
    logging.info(f"Starting Worker {worker_id}/{total_workers}...")
    
    scraper = get_scraper()
    scraper.start_session(headless=True)
    
    try:
        pass_count = 0
        while True:
            pass_count += 1
            items = get_broken_items(worker_id, total_workers)
            if not items:
                logging.info(f"No more broken items for worker {worker_id}. Sleeping...")
                time.sleep(60)
                continue
                
            logging.info(f"--- Starting Pass #{pass_count} ({len(items)} items) ---")
            
            for item in items:
                title = item['title']
                raw_title = item['raw_title'] or title
                detail_url = item['detail_url']
                tmdb_id = item['tmdb_id']
                poster_path = item['poster_path']
                embed_url = item['embed_url']
                
                changes_made = False
                new_embed = embed_url
                new_poster = poster_path
                new_tmdb_id = tmdb_id
                
                # 1. Fix Metadata (Poster)
                if not poster_path or poster_path == '':
                    logging.info(f"[{title}] Missing Poster. Searching TMDB...")
                    tmdb_data = search_tmdb(title, item['year'])
                    if tmdb_data:
                        new_poster = tmdb_data.get('poster_path')
                        new_tmdb_id = str(tmdb_data['id'])
                        overview = tmdb_data.get('overview')
                        backdrop = tmdb_data.get('backdrop_path')
                        logging.info(f"  -> Metadata FOUND (ID: {new_tmdb_id})")
                        save_embed(title, new_embed, new_tmdb_id, new_poster, backdrop, overview, original_raw_title=raw_title)
                        changes_made = True
                    else:
                        logging.warning(f"  -> Meta NOT FOUND on TMDB.")

                # 2. Fix Video Link
                if (new_embed == 'NOT_FOUND' or 'web.operatopzera.net' in new_embed) and detail_url:
                    logging.info(f"[{title}] Missing/Invalid Video. Scraping...")
                    try:
                        scraped_url = scraper.get_video_source(detail_url, expected_title=raw_title)
                        if scraped_url and scraped_url != "NOT_FOUND":
                            new_embed = scraped_url
                            logging.info(f"  -> Video FOUND: {new_embed}")
                            save_embed(title, new_embed, new_tmdb_id, new_poster, None, None, original_raw_title=raw_title)
                            changes_made = True
                        else:
                            logging.warning(f"  -> Video NOT_FOUND (Validation Failed or Selector Timeout).")
                    except Exception as e:
                        logging.error(f"  -> Scraper error: {e}")
                
                # 3. Final Check: Is it still broken?
                still_missing_meta = not (new_poster and new_poster != '')
                still_missing_video = (new_embed == 'NOT_FOUND' or 'web.operatopzera.net' in new_embed)
                
                actually_fixed = not (still_missing_meta or still_missing_video)
                
                # Update attempt counter. 
                # If we made ANY change (even partial), but it's STILL broken, increment attempt.
                update_repair_status(title, success=actually_fixed)
                time.sleep(1)

            logging.info(f"--- Pass #{pass_count} Completed ---")
            time.sleep(5)
            
    finally:
        scraper.stop_session()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker_id", type=int, default=0)
    parser.add_argument("--total_workers", type=int, default=1)
    args = parser.parse_args()
    
    repair_worker(args.worker_id, args.total_workers)
