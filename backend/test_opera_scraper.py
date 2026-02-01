from playwright_scraper import scrape_operatopzera
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_scrape():
    # Use a likely movie title
    title = "Deadpool"
    print(f"Testing scrape for: {title}")
    
    url = scrape_operatopzera(title)
    
    if url:
        print(f"SUCCESS: Extracted URL: {url}")
    else:
        print("FAILURE: No URL extracted")

if __name__ == "__main__":
    test_scrape()
