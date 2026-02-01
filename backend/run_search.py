import sys
import logging

# Configure logging to show info
logging.basicConfig(level=logging.INFO)

from scraper import scrape_for_title
from database import init_db, save_embed

# Initialize DB so we can save results
init_db()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 run_search.py <movie_title>")
        sys.exit(1)
    
    title = " ".join(sys.argv[1:])
    print(f"Searching for: {title}")
    
    try:
        embed = scrape_for_title(title)
        
        if embed:
            print(f"\nSUCCESS: Found embed: {embed}")
            save_embed(title, embed)
            print("Saved to database.")
        else:
            print("\nFAILURE: No embed found.")
            
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")
