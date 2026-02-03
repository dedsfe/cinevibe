from playwright_scraper import scrape_operatopzera
import logging
import sys

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

print("Starting debug scrape for Barbie...")
try:
    # Try a specific known Barbie movie
    title = "Barbie"
    print(f"Searching for: {title}")
    
    link = scrape_operatopzera(title)
    
    if link:
        print(f"SUCCESS! Found link: {link}")
    else:
        print("FAILED: No link found.")

except Exception as e:
    print(f"ERROR: {e}")
