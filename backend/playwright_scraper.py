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

            # Wait for results with scroll
            try:
                # Try to find it, if not, scroll and try again
                for _ in range(5):
                    try:
                        self.page.locator(f"a[href*='/movie/']").filter(has_text=title).first.wait_for(state="visible", timeout=2000)
                        break
                    except:
                        self.page.mouse.wheel(0, 500)
                        time.sleep(1)
                
                # Final wait check
                self.page.locator(f"a[href*='/movie/']").filter(has_text=title).first.wait_for(state="visible", timeout=5000)
            except:
                logging.warning(f"Title '{title}' not found in results after scrolling.")
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

    def navigate_to_movies(self):
        """Navigate to the main movies listing page."""
        if not self.page:
            if not self.start_session():
                return False
        
        try:
            movies_url = "http://web.operatopzera.net/#/movie/"
            if self.page.url != movies_url:
                logging.info(f"Navigating to movie catalog: {movies_url}")
                self.page.goto(movies_url)
                # Wait for ANY movie card to appear
                self.page.wait_for_selector("a[href*='/movie/']", timeout=20000) 
            return True
        except Exception as e:
            logging.error(f"Failed to navigate to content: {e}")
            return False

    def scrape_current_page_cards(self):
        """Extracts (title, detail_url) from all observable cards on the screen."""
        if not self.page:
            return []
            
        items = []
        try:
            # Selector for movie cards - usually 'a' tags inside a grid
            # Based on previous HTML dumps, links contain '/movie/'
            cards = self.page.locator("a[href*='/movie/']").all()
            logging.info(f"Found {len(cards)} card candidates on screen.")
            
            for card in cards:
                try:
                    href = card.get_attribute("href")
                    # inner_text might contain title + year + misc info
                    # We usually want the title. Let's get the full text and clean it later.
                    raw_text = card.inner_text().strip()
                    
                    if href and "/movie/" in href and raw_text:
                        # Clean title
                        lines = raw_text.split('\n')
                        cleaned_title = lines[0].strip()
                        
                        # Try to find a year (4 digits) in the text
                        import re
                        year_match = re.search(r'\b(19|20)\d{2}\b', raw_text)
                        card_year = year_match.group(0) if year_match else None
                        
                        if len(cleaned_title) < 2 or cleaned_title.lower() in ["play", "assistir", "more info", "info"]:
                            continue
                            
                        items.append({
                            "raw_title": cleaned_title, 
                            "detail_url": href,
                            "year": card_year,
                            "full_text": raw_text
                        })
                except:
                    pass
        except Exception as e:
            logging.error(f"Error extracting cards: {e}")
            
        return items

    def get_video_source(self, detail_url: str, expected_title: str = None) -> str | None:
        """
        Navigates to the detail page and extracts the video source.
        Uses 'expected_title' to verify the page has correctly loaded the target movie.
        """
        if not self.is_running or not self.page:
             # Auto start if needed
             self.start_session()

        try:
            full_url = detail_url if detail_url.startswith("http") else f"http://web.operatopzera.net/{detail_url}"
            
            # Navigate Logic
            # Force reload if we are 'stuck' on the timestamp or if hash didn't trigger load
            logging.info(f"Navigating to detail page: {full_url}")
            self.page.goto(full_url, timeout=45000)
            
            try:
                self.page.wait_for_load_state("networkidle", timeout=5000)
            except: pass
            time.sleep(2)
            
            # TITLE VALIDATION (CRITICAL FIX)
            if expected_title:
                # Clean title for fuzzy matching (remove year, special chars)
                import re
                short_title = re.sub(r'\(\d{4}\)', '', expected_title).split(':')[0].strip()
                if len(short_title) > 20: short_title = short_title[:20]
                
                logging.info(f"Validating page content matches title: '{short_title}'...")
                try:
                    # Look for h1, h2, or any strong text containing the title
                    self.page.wait_for_selector(f"text={short_title}", timeout=10000)
                    logging.info("  -> Page title validation PASSED.")
                except:
                    logging.warning(f"  -> Page validation FAILED. Title '{short_title}' not found in DOM.")
                    # Try a reload once
                    logging.info("  -> Retrying with RELOAD...")
                    self.page.reload()
                    time.sleep(5)
                    try:
                        self.page.wait_for_selector(f"text={short_title}", timeout=10000)
                        logging.info("  -> Reload validation PASSED.")
                    except:
                        logging.error("  -> Validation FAILED after reload. Aborting to prevent mismatch.")
                        return None
            
            # Play button logic
            try:
                play_btn = self.page.locator("a[href*='/play/'], button:has-text('Play'), button:has-text('Assistir')").first
                if play_btn.is_visible(timeout=5000):
                    logging.info("Clicking Play button (Forced)...")
                    play_btn.click(force=True)
                    time.sleep(3) # Wait for player to init
            except: pass

            # Extract Video
            video_src = None
            try:
                # Increased timeout to 45s for slow loaders
                self.page.wait_for_selector("video, iframe", timeout=45000)
                
                # Check video tag first
                video_src = self.page.evaluate("document.querySelector('video') ? document.querySelector('video').src : null")
                
                if not video_src:
                     # Fallback to iframe
                     iframe = self.page.query_selector("iframe")
                     if iframe:
                         video_src = iframe.get_attribute("src")
                         
            except Exception as e:
                logging.error(f"Error extracting video from page: {e}")

            return video_src
        except Exception as e:
            logging.error(f"Failed to get video source from {detail_url}: {e}")
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
    # Test block
    logging.basicConfig(level=logging.INFO)
    s = OperaScraper()
    s.start_session(headless=False)
    # s.search_and_extract("Americana") # This method does not exist in the class
    print("Scraping 'A Empregada'...")
    link = s.scrape_title("A Empregada") 
    print(f"Result: {link}")
    s.stop_session()
