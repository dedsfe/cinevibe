import requests
import time
import logging
import sys
from scraper import scrape_for_title
from database import init_db, save_embed, get_cached_embed
from validator import validate_embed

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_KEY = "909fc389a150847bdd4ffcd92809cff7"
BASE_URL = "https://api.themoviedb.org/3"

CATEGORIES = [
    "/trending/all/week",
    "/movie/popular",
    "/movie/top_rated",
]

def fetch_movies(endpoint):
    url = f"{BASE_URL}{endpoint}?api_key={API_KEY}&language=pt-BR&page=1"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.json().get("results", [])
        else:
            logging.error(f"Failed to fetch {endpoint}: {res.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error fetching {endpoint}: {e}")
        return []

# State tracking
SCRAPER_STATE = {
    "is_running": False,
    "current_movie": None,
    "progress": {"current": 0, "total": 0},
    "logs": []
}

def log_state(message, level="INFO"):
    """Update logs in state and print to standard logging"""
    if level == "INFO":
        logging.info(message)
    elif level == "WARNING":
        logging.warning(message)
    elif level == "ERROR":
        logging.error(message)
        
    # Append to state logs (keep last 50)
    timestamp = time.strftime("%H:%M:%S")
    SCRAPER_STATE["logs"].append(f"[{timestamp}] {message}")
    if len(SCRAPER_STATE["logs"]) > 50:
        SCRAPER_STATE["logs"].pop(0)

def get_scraper_state():
    return SCRAPER_STATE

def run_bulk_scrape():
    global SCRAPER_STATE
    SCRAPER_STATE["is_running"] = True
    SCRAPER_STATE["logs"] = []
    
    try:
        init_db()
        
        # Start persistent session
        from playwright_scraper import get_scraper
        scraper_instance = get_scraper()
        try:
            scraper_instance.start_session(headless=True)
        except Exception as e:
            log_state(f"Failed to start scraper session: {e}", "ERROR")
            return

        all_movies = []
        
        # 1. Collect all movies from categories
        log_state("Fetching movie lists from TMDB...")
        for cat in CATEGORIES:
            log_state(f"Fetching {cat}...")
            movies = fetch_movies(cat)
            all_movies.extend(movies)
            
        # Deduplicate by ID
        unique_movies = {m["id"]: m for m in all_movies if m.get("title") or m.get("name")}.values()
        log_state(f"Found {len(unique_movies)} unique movies to process.")
        
        SCRAPER_STATE["progress"]["total"] = len(unique_movies)
        
        # 2. Scrape each
        count = 0
        for movie in unique_movies:
            # Check if session is still alive
            if not scraper_instance.is_running:
                 log_state("Scraper session died, restarting...", "WARNING")
                 scraper_instance.start_session(headless=True)

            SCRAPER_STATE["progress"]["current"] = count + 1
            
            title = movie.get("title") or movie.get("name")
            tmdb_id = str(movie["id"])
            
            if not title:
                continue
                
            SCRAPER_STATE["current_movie"] = title
            log_state(f"[{count+1}/{len(unique_movies)}] Checking: {title} (ID: {tmdb_id})")
            
            # Check DB first
            cached = get_cached_embed(title)
            if cached:
                log_state(f" -> Already in DB: {cached}")
                count += 1
                continue
                
            # Scrape
            try:
                log_state(" -> Scraping...")
                embed = scrape_for_title(title, tmdb_id)
                if embed and validate_embed(embed):
                    save_embed(title, embed, tmdb_id)
                    log_state(" -> Saved!")
                else:
                    # Save as NOT_FOUND so we know we checked it
                    save_embed(title, "NOT_FOUND", tmdb_id)
                    log_state(" -> No embed found (marked as NOT_FOUND).", "WARNING")
            except Exception as e:
                log_state(f" -> Failed: {e}", "ERROR")
                # Optionally also mark as checked/error? For now just log.
                
            count += 1
            time.sleep(1) # Reduced sleep since we don't need to be as nice to our own session, but still good practice
            
    except Exception as e:
         log_state(f"Fatal Scraper Error: {e}", "ERROR")
    finally:
        # Close session
        try:
            if 'scraper_instance' in locals():
                scraper_instance.stop_session()
        except: pass
        
        SCRAPER_STATE["is_running"] = False
        SCRAPER_STATE["current_movie"] = "Done"

if __name__ == "__main__":
    run_bulk_scrape()
