from playwright_scraper import OperaScraper
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

def debug_scrape():
    scraper = OperaScraper()
    try:
        logging.info("Starting Debug Session...")
        scraper.start_session(headless=True)
        
        # Target URL found in DB (Failing One: A Garota Ideal)
        target_suffix = "#/movie/category/34/216865/info/"
        # Construct full URL manually to match logic
        full_url = f"http://web.operatopzera.net/{target_suffix}"
        
        logging.info(f"Attempting to scrape video from: {full_url}")
        
        # Navigate
        scraper.page.goto(full_url, timeout=60000)
        try:
             scraper.page.wait_for_load_state("networkidle", timeout=5000)
        except: pass
        time.sleep(2)
        
        # Take screenshot of the page
        scraper.page.screenshot(path="debug_Fail_1_PageLoad.png")
        logging.info("Screenshot 1: Page Load")
        
        # Check for Play button
        try:
            play_btn = scraper.page.locator("a[href*='/play/'], button:has-text('Play'), button:has-text('Assistir')").first
            if play_btn.is_visible(timeout=5000):
                logging.info("Play button found. Clicking (Forced)...")
                play_btn.click(force=True)
                
                # Capture shots after click
                time.sleep(2)
                scraper.page.screenshot(path="debug_Fail_2_AfterClick2s.png")
                time.sleep(3)
                scraper.page.screenshot(path="debug_Fail_3_AfterClick5s.png")
            else:
                logging.warning("Play button NOT found.")
        except Exception as e:
            logging.warning(f"Error checking play button: {e}")

        # Check for Video
        logging.info("Waiting for video element...")
        try:
            # Check for iframe too
            scraper.page.wait_for_selector("video, iframe", timeout=15000)
            logging.info("Video/Iframe element found!")
            
            # Simple check
            video_el = scraper.page.query_selector("video")
            if video_el:
                src = scraper.page.evaluate("document.querySelector('video').src")
                logging.info(f"Video SRC: {src}")
            else:
                logging.info("Found element but not video tag directly (maybe iframe).")
                scraper.page.screenshot(path="debug_Fail_4_FoundSomething.png")
            
        except Exception as e:
            logging.error(f"Video element NOT found: {e}")
            scraper.page.screenshot(path="debug_Fail_5_Timeout.png")

    except Exception as e:
        logging.error(f"Debug failed: {e}")
    finally:
        scraper.stop_session()

if __name__ == "__main__":
    debug_scrape()
