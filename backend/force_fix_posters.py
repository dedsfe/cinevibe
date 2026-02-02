import sqlite3
import requests
from database import get_conn, save_embed

TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"
BASE_URL = "https://api.themoviedb.org/3"

def search_tmdb(title, year=None):
    try:
        url = f"{BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "language": "pt-BR",
            "page": 1
        }
        if year:
            params["year"] = year
        res = requests.get(url, params=params)
        data = res.json()
        if data.get("results"):
            return data["results"][0]
    except Exception as e:
        print(f"Error searching TMDB: {e}")
    return None

def force_fix():
    targets = ["Interestelar", "Parasita", "Bob Esponja", "Pecadores", "Zootopia 2", "Anaconda"]
    
    conn = get_conn()
    c = conn.cursor()
    
    for title in targets:
        print(f"Fixing {title}...")
        # Get existing link
        c.execute("SELECT embed_url FROM links WHERE title LIKE ?", (f"%{title}%",))
        row = c.fetchone()
        current_embed = row[0] if row else None
        
        if not current_embed:
             # Try to find in catalog_raw
             c.execute("SELECT video_url FROM catalog_raw WHERE raw_title LIKE ?", (f"%{title}%",))
             row = c.fetchone()
             current_embed = row[0] if row else "NOT_FOUND"

        tmdb_data = search_tmdb(title)
        if tmdb_data:
            print(f"  -> Found TMDB match: {tmdb_data['title']}")
            poster_path = tmdb_data.get("poster_path")
            backdrop_path = tmdb_data.get("backdrop_path")
            overview = tmdb_data.get("overview")
            tmdb_id = str(tmdb_data["id"])
            
            save_embed(tmdb_data['title'], current_embed, tmdb_id, poster_path, backdrop_path, overview)
            print(f"  -> Updated {title} with poster {poster_path}")
        else:
            print(f"  -> No TMDB data for {title}")

if __name__ == "__main__":
    force_fix()
