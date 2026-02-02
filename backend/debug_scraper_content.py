from playwright_scraper import OperaScraper
import time
import logging

logging.basicConfig(level=logging.INFO)

def debug_search():
    scraper = OperaScraper()
    try:
        scraper.start_session(headless=True)
        page = scraper.page
        
        # Navigate to search if not already (start_session leaves    try:
        page.goto("http://web.operatopzera.net/#/movie/", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(5)
        
        print("Page Title:", page.title())
        print("URL:", page.url)
        
        # Dump some HTML
        content = page.content()
        print("HTML Snippet:", content[:5000]) # First 5k chars
        
        # Try to find class names of grid items
        print("Searching for grid items...")
        # Check for common grid classes or just listing all divs
        divs = page.locator("div[class*='container'], div[class*='grid'], div[class*='list']").all()
        for i, div in enumerate(divs[:5]):
            print(f"Div {i} class: {div.get_attribute('class')}")
            
    except Exception as e:
        print(f"Error: {e}")
        
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
