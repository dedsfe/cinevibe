from playwright_scraper import OperaScraper
import time
import logging

logging.basicConfig(level=logging.INFO)

def debug_search():
    scraper = OperaScraper()
    try:
        scraper.start_session(headless=True)
        page = scraper.page
        
        # Navigate to search if not already (start_session leaves us there)
        page.goto("http://web.operatopzera.net/#/movie/search/")
        
        title = "Housemaid"
        logging.info(f"Searching for: {title}")
        
        INPUT_SELECTOR = "input[placeholder='Search stream...']"
        page.wait_for_selector(INPUT_SELECTOR, state="visible")
        page.fill(INPUT_SELECTOR, "")
        page.fill(INPUT_SELECTOR, title)
        
        # Verify input
        val = page.input_value(INPUT_SELECTOR)
        logging.info(f"Input value verified: '{val}'")
        
        page.keyboard.press("Enter")
        
        # Click submit if exists
        try:
             SUBMIT_SELECTOR = "button[type='submit']"
             if page.locator(SUBMIT_SELECTOR).is_visible(timeout=2000):
                 page.click(SUBMIT_SELECTOR)
                 logging.info("Clicked submit button")
        except: pass
                 
        logging.info("Waiting 5s for results...")
        time.sleep(5)
        
        logging.info("Dumping page innerText:")
        text = page.inner_text("body")
        logging.info(f"--- PAGE TEXT ---\n{text}\n-----------------")
        
        page.screenshot(path="debug_text_dump.png")
        logging.info("Screenshot saved to debug_text_dump.png")
        
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        scraper.stop_session()

if __name__ == "__main__":
    debug_search()
