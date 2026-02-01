import logging
import sys
from playwright_scraper import scrape_operatopzera

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

print("--- Testing Scraper Function for 'Anaconda' (2025) ---")
result = scrape_operatopzera("Anaconda", "2025")
print(f"--- Result: {result} ---")
