import sqlite3
import requests
import re
import time
import logging
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime
from database import get_conn, save_embed

# Configuration
TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"
BASE_URL = "https://api.themoviedb.org/3"
MIN_SIMILARITY_SCORE = 0.85 # High threshold for safety
CHECK_INTERVAL_SECONDS = 60 # Check every minute

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [PosterDaemon] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("poster_daemon.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def normalize_title(title):
    """Normalize title for comparison (remove accents, lowercase)"""
    # Remove accents
    normalized = unicodedata.normalize("NFKD", title)
    normalized = "".join([c for c in normalized if not unicodedata.combining(c)])
    # Remove special chars and lowercase
    normalized = re.sub(r"[^\w\s]", "", normalized.lower())
    return normalized.strip()

def calculate_similarity(str1, str2):
    """Calculates string similarity (0-1)"""
    s1 = normalize_title(str1)
    s2 = normalize_title(str2)
    
    # Check for direct containment
    if s1 == s2: return 1.0
    if s1 in s2 or s2 in s1:
        # If one is a subtitle of other, check length ratio
        return max(len(s1), len(s2)) / max(len(s1), len(s2)) * 0.95
        
    return SequenceMatcher(None, s1, s2).ratio()

def clean_search_title(title):
    title = re.sub(r'\(\d{4}\)', '', title)
    title = re.sub(r'\[.*?\]', '', title)
    title = re.sub(r'\(.*?\)', '', title)
    if ":" in title:
        title = title.split(":")[0] # Try main title only
    return title.strip()

def search_tmdb(title, year=None):
    try:
        search_query = clean_search_title(title)
        url = f"{BASE_URL}/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": search_query, "language": "pt-BR", "page": 1}
        if year: params["year"] = year
        
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        
        if not data.get("results") and year:
            del params["year"]
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            
        return data.get("results", [])
    except Exception as e:
        logger.error(f"TMDB API Error: {e}")
    return []

def get_pending_movies():
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        query = """
            SELECT l.title, l.tmdb_id, l.embed_url, c.year, c.raw_title
            FROM links l
            LEFT JOIN catalog_raw c ON (l.title = c.raw_title OR l.original_raw_title = c.raw_title)
            WHERE (l.poster_path IS NULL OR l.poster_path = '')
              AND l.embed_url IS NOT NULL 
              AND l.embed_url != 'NOT_FOUND'
        """
        c.execute(query)
        return c.fetchall()

def run_poster_daemon():
    logger.info("Poster Enforcement Daemon started.")
    logger.info(f"Threshold-Safety: {MIN_SIMILARITY_SCORE*100}% | Interval: {CHECK_INTERVAL_SECONDS}s")
    
    while True:
        try:
            pending = get_pending_movies()
            if not pending:
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue
                
            logger.info(f"Found {len(pending)} movies missing posters. Processing...")
            
            for movie in pending:
                title = movie['title']
                year = movie['year']
                raw_title = movie['raw_title'] or title
                
                results = search_tmdb(title, year)
                
                best_match = None
                highest_score = 0
                
                for candidate in results:
                    c_title = candidate.get('title', '')
                    c_original = candidate.get('original_title', '')
                    
                    # Score both titles
                    score1 = calculate_similarity(title, c_title)
                    score2 = calculate_similarity(title, c_original)
                    score = max(score1, score2)
                    
                    if score > highest_score:
                        highest_score = score
                        best_match = candidate
                
                if best_match and highest_score >= MIN_SIMILARITY_SCORE:
                    poster_path = best_match.get('poster_path')
                    if poster_path:
                        tid = str(best_match['id'])
                        logger.info(f"✅ Match Found for '{title}': '{best_match['title']}' (Score: {highest_score:.2f})")
                        save_embed(
                            title=title,
                            embed_url=movie['embed_url'],
                            tmdb_id=tid,
                            poster_path=poster_path,
                            backdrop_path=best_match.get('backdrop_path'),
                            overview=best_match.get('overview'),
                            original_raw_title=raw_title
                        )
                    else:
                        logger.warning(f"⚠️  Match found for '{title}' but no poster available on TMDB.")
                else:
                    if best_match:
                        logger.warning(f"❌ REJECTED '{title}': Best match '{best_match['title']}' score too low ({highest_score:.2f})")
                    else:
                        logger.warning(f"❌ NO RESULTS for '{title}'")
            
            logger.info("Cycle completed. Sleeping...")
            time.sleep(CHECK_INTERVAL_SECONDS)
            
        except Exception as e:
            logger.error(f"Critical error in daemon loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run_poster_daemon()
