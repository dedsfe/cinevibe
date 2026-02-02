from playwright_scraper import OperaScraper
from database import get_conn
import time
import logging

logging.basicConfig(level=logging.INFO)

def save_raw_item(item):
    try:
        conn = get_conn()
        c = conn.cursor()
        # raw_title is unique, so INSERT OR IGNORE avoids duplicates
        c.execute("""
            INSERT OR IGNORE INTO catalog_raw (raw_title, year, detail_url)
            VALUES (?, ?, ?)
        """, (item['raw_title'], item['year'], item['detail_url']))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logging.error(f"DB Error: {e}")
        return False
    finally:
        conn.close()

def crawl_catalog():
    scraper = OperaScraper()
    scraper.start_session(headless=True) # Visible for debugging
    
    try:
        # 1. Go to Movie Catalog
        if not scraper.navigate_to_movies():
            logging.error("Could not navigate to movies.")
            return

        logging.info("Starting Crawl...")
        
        # 2. Iterate (Scroll/Pagination)
        # For now, let's just grab the first few pages/scrolls
        consecutive_no_new_items = 0
        total_items = 0
        
        for i in range(200): # Increased to 200 scrolls to go deeper
            logging.info(f"--- Scroll {i+1} ---")
            
            # Scrape visible cards
            items = scraper.scrape_current_page_cards()
            new_count = 0
            
            for item in items:
                if save_raw_item(item):
                    new_count += 1
                    logging.info(f"NEW: {item['raw_title']}")
            
            logging.info(f"Found {len(items)} items on screen, {new_count} new.")
            total_items += new_count
            
            if new_count == 0:
                consecutive_no_new_items += 1
            else:
                consecutive_no_new_items = 0
                
            if consecutive_no_new_items >= 3:
                logging.info("No new items for 3 scrolls. Stopping.")
                break
                
            # Scroll down
            # Using mouse wheel offers better compatibility with some lazy loaders than 'End' key
            scraper.page.mouse.wheel(0, 15000) 
            time.sleep(1.5)
            
            # Backup: Press End occasionally
            if i % 5 == 0:
                scraper.page.keyboard.press("End")
                time.sleep(1)
            
        logging.info(f"Crawl finished. Total new items: {total_items}")

    except Exception as e:
        logging.error(f"Crawl failed: {e}")
    finally:
        scraper.stop_session()

if __name__ == "__main__":
    crawl_catalog()
