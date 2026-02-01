import logging
import urllib.parse
import time
from playwright.sync_api import sync_playwright

# Configure logging to show in terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OperaScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = False

    def start_session(self, headless=True):
        """
        Launches browser, logs in, and navigates to the search page.
        Must be called once before scraping.
        """
        try:
            logging.info("Starting Playwright session...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self.page = self.context.new_page()
            self.is_running = True

            # 1. Go to Home Page & Login
            base_url = "http://web.operatopzera.net/#/"
            logging.info(f"Navigating to home: {base_url}")
            self.page.goto(base_url, timeout=60000)
            self.page.wait_for_load_state("networkidle", timeout=60000)

            # Check for login
            try:
                login_selector = "input[name='username']"
                if self.page.locator(login_selector).is_visible(timeout=5000):
                    logging.info("Login page detected. Logging in...")
                    USER = "t2TGgarYJ"
                    PASS = "66e74xKRJ"
                    
                    self.page.fill("input[name='username']", USER)
                    self.page.fill("input[name='password']", PASS)
                    self.page.click("button:has-text('Login')")
                    
                    logging.info("Login submitted. Waiting for home/dashboard...")
                    self.page.wait_for_url("**/#/", timeout=30000)
                    time.sleep(2) 
                else:
                    logging.info("Already logged in or no login form found.")
            except Exception as e:
                logging.warning(f"Login check encountered error: {e}")

            # 2. Go to Movies Page
            movies_url = "http://web.operatopzera.net/#/movie/"
            logging.info(f"Navigating to movies: {movies_url}")
            self.page.goto(movies_url, timeout=30000)
            time.sleep(2)

            # 3. Go to Search Page (Stay here!)
            search_page_url = "http://web.operatopzera.net/#/movie/search/"
            logging.info(f"Navigating to search page: {search_page_url}")
            self.page.goto(search_page_url, timeout=30000)
            
            # Verify we are ready to search
            INPUT_SELECTOR = "input[placeholder='Search stream...']"
            self.page.wait_for_selector(INPUT_SELECTOR, state="visible", timeout=15000)
            logging.info("Session started successfully. Ready to scrape.")

        except Exception as e:
            logging.error(f"Failed to start session: {e}")
            self.stop_session()
            raise e

    def stop_session(self):
        """Closes the browser and cleanup."""
        logging.info("Stopping Playwright session...")
        if self.page: self.page.close()
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.is_running = False

    def scrape_title(self, title: str, year: str = None) -> str | None:
        """
        Scrapes a single title using the existing session.
        Assumes we are already on the Search Page or can easily get back to it.
        """
        if not self.is_running or not self.page:
            logging.error("Scraper session is not running. Call start_session() first.")
            return None

        try:
            # Ensure we are on search page
            if "/movie/search" not in self.page.url:
                logging.info("Not on search page, navigating back...")
                self.page.goto("http://web.operatopzera.net/#/movie/search/", timeout=15000)
            
            INPUT_SELECTOR = "input[placeholder='Search stream...']"
            SUBMIT_SELECTOR = "button[type='submit']"
            
            # Clear input and type
            self.page.wait_for_selector(INPUT_SELECTOR, state="visible", timeout=5000)
            self.page.fill(INPUT_SELECTOR, "")
            self.page.fill(INPUT_SELECTOR, title)
            time.sleep(0.5)
            
            logging.info(f"Searching for: {title}")
            self.page.keyboard.press("Enter")
            
            # Check if submit click is needed (wait briefly)
            try:
                if self.page.locator(SUBMIT_SELECTOR).is_visible(timeout=1000):
                     self.page.click(SUBMIT_SELECTOR, timeout=2000)
            except: pass

            # Wait for results
            try:
                # Wait for A MOVIE LINK with the title text
                self.page.locator(f"a[href*='/movie/']").filter(has_text=title).first.wait_for(state="visible", timeout=10000)
            except:
                logging.warning(f"Title '{title}' not found in results.")
                return None

            # Find target
            target_link = None
            target_locator = self.page.locator(f"a[href*='/movie/']").filter(has_text=title).first
            
            if target_locator.is_visible():
                target_link = target_locator
                # Year check
                if year:
                    txt = target_link.inner_text().lower()
                    try:
                        alt = target_link.locator("img").get_attribute("alt") or ""
                        txt += " " + alt.lower()
                    except: pass
                    if year not in txt:
                        logging.warning(f"Year mismatch for {title}. Found in {txt}")
                        target_link = None
            
            # Fallback loop (same as before but using self.page)
            if not target_link:
                # ... (Simplified logic: if direct match failed despite wait, sticking to direct match for speed for now. 
                # If the wait passed, target_locator.is_visible should be true. 
                # If wait failed, we returned None earlier.)
                pass

            if not target_link:
                logging.warning("No valid link found after search.")
                return None

            # Determine if we need to open in new tab or same tab?
            # User workflow says: Select -> Play -> Extract
            # If we click, we navigate AWAY from search. 
            # To handle iteration efficiently, we should probably do this in the same tab 
            # and then GO BACK to search for the next movie.
            
            logging.info("Clicking movie link...")
            target_link.scroll_into_view_if_needed()
            target_link.click()
            
            # On Movie Page
            time.sleep(2)
            
            # Play button logic
            if "/play/" not in self.page.url:
                try:
                    play_btn = self.page.locator("a[href*='/play/'], button:has-text('Play'), button:has-text('Assistir')").first
                    if play_btn.is_visible(timeout=5000):
                        play_btn.click()
                    else:
                        logging.warning("Play button not found.")
                except: pass

            # Extract Video
            video_src = None
            try:
                self.page.wait_for_selector("video", timeout=20000)
                # Force play
                self.page.evaluate("document.querySelector('video').play().catch(() => {})")
                
                for _ in range(10):
                    src = self.page.evaluate("document.querySelector('video').src")
                    if src and src.startswith("http") and "blob" not in src:
                        video_src = src
                        break
                    time.sleep(1)
            except Exception as e:
                logging.error(f"Error extracting video: {e}")

            # RESET FOR NEXT SEARCH: Go back to search page
            logging.info("Returning to search page...")
            self.page.goto("http://web.operatopzera.net/#/movie/search/")
            
            return video_src

        except Exception as e:
            logging.error(f"Error checking {title}: {e}")
            # Try to recover session state
            try: 
                self.page.goto("http://web.operatopzera.net/#/movie/search/")
            except: pass
            return None

# Global instance
_scraper_instance = None

def get_scraper():
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = OperaScraper()
    return _scraper_instance

def scrape_operatopzera(title: str, year: str = None) -> str | None:
    """Wrapper to maintain compatibility or simple usage"""
    s = get_scraper()
    if not s.is_running:
        s.start_session()
    return s.scrape_title(title, year)

if __name__ == "__main__":
    s = OperaScraper()
    s.start_session(headless=True)
    print("Scraping 'A Empregada'...")
    link = s.scrape_title("A Empregada") 
    print(f"Result: {link}")
    s.stop_session()
