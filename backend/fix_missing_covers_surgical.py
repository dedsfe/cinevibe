import sqlite3
import requests
import re
import time
import logging
from datetime import datetime
from database import get_conn, save_embed

# Configuration
TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"
BASE_URL = "https://api.themoviedb.org/3"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_title(title):
    # Remove text like (2014), (Dual), [4K], etc.
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
            # Retry without year if failed
            del params["year"]
            res = requests.get(url, params=params)
            data = res.json()
            
        if data.get("results"):
            return data["results"][0]
    except Exception as e:
        logging.error(f"TMDB Search Error for {title}: {e}")
    return None

def fix_posters():
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get movies that have embed_url but NO poster_path
        query = """
            SELECT l.title, l.tmdb_id, l.embed_url, c.year, c.raw_title
            FROM links l
            LEFT JOIN catalog_raw c ON (l.title = c.raw_title OR l.original_raw_title = c.raw_title)
            WHERE (l.poster_path IS NULL OR l.poster_path = '')
              AND l.embed_url IS NOT NULL 
              AND l.embed_url != 'NOT_FOUND'
        """
        c.execute(query)
        movies = c.fetchall()
        
        logging.info(f"Starting to fix {len(movies)} missing posters...")
        
        fixed_count = 0
        for movie in movies:
            title = movie['title']
            year = movie['year']
            raw_title = movie['raw_title'] or title
            
            logging.info(f"Searching cover for: {title} ({year or 'No Year'})")
            
            tmdb_data = search_tmdb(title, year)
            
            if tmdb_data:
                poster_path = tmdb_data.get('poster_path')
                tmdb_id = str(tmdb_data['id'])
                backdrop_path = tmdb_data.get('backdrop_path')
                overview = tmdb_data.get('overview')
                
                if poster_path:
                    # Use save_embed to update the record
                    # We pass the existing embed_url to keep it
                    save_embed(
                        title=title,
                        embed_url=movie['embed_url'],
                        tmdb_id=tmdb_id,
                        poster_path=poster_path,
                        backdrop_path=backdrop_path,
                        overview=overview,
                        original_raw_title=raw_title
                    )
                    logging.info(f"  ✅ Fixed: {title} (ID: {tmdb_id})")
                    fixed_count += 1
                else:
                    logging.warning(f"  ⚠️  TMDB found movie but no poster_path for: {title}")
            else:
                logging.warning(f"  ❌ Not found on TMDB: {title}")
            
            time.sleep(0.5) # Be nice to API

        logging.info(f"Done! Fixed {fixed_count} posters.")

if __name__ == "__main__":
    fix_posters()
