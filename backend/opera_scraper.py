"""
Dedicated Opera Topzera Scraper
Scrapes ONLY from Opera Topzera - no fallbacks to avoid mismatches
"""

import logging
import time
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class OperaTopzeraScraper:
    """
    Scraper dedicado exclusivamente ao Opera Topzera.
    NÃO tem fallbacks para YouTube ou outras fontes.
    """

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = False
        self.session_start_time = None

    def start_session(self, headless=True):
        """Inicia sessão no Opera Topzera"""
        try:
            logger.info("[Opera] Starting dedicated session...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            self.page = self.context.new_page()
            self.is_running = True
            self.session_start_time = time.time()

            # Login
            base_url = "http://web.operatopzera.net/#/"
            logger.info(f"[Opera] Navigating to {base_url}")
            self.page.goto(base_url, timeout=60000)
            self.page.wait_for_load_state("networkidle", timeout=60000)

            # Check for login form
            try:
                login_selector = "input[name='username']"
                if self.page.locator(login_selector).is_visible(timeout=5000):
                    logger.info("[Opera] Login page detected. Logging in...")
                    USER = "t2TGgarYJ"
                    PASS = "66e74xKRJ"

                    self.page.fill("input[name='username']", USER)
                    self.page.fill("input[name='password']", PASS)
                    self.page.click("button:has-text('Login')")

                    self.page.wait_for_url("**/#/", timeout=30000)
                    time.sleep(2)
                    logger.info("[Opera] Login successful")
                else:
                    logger.info("[Opera] Already logged in")
            except Exception as e:
                logger.warning(f"[Opera] Login check warning: {e}")

            # Navigate to search page
            search_url = "http://web.operatopzera.net/#/movie/search/"
            logger.info(f"[Opera] Navigating to search page")
            self.page.goto(search_url, timeout=30000)

            INPUT_SELECTOR = "input[placeholder='Search stream...']"
            self.page.wait_for_selector(INPUT_SELECTOR, state="visible", timeout=15000)
            logger.info("[Opera] Session ready")

        except Exception as e:
            logger.error(f"[Opera] Failed to start session: {e}")
            self.stop_session()
            raise e

    def stop_session(self):
        """Encerra sessão"""
        logger.info("[Opera] Stopping session...")
        if self.page:
            try:
                self.page.close()
            except:
                pass
        if self.context:
            try:
                self.context.close()
            except:
                pass
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
        self.is_running = False

    def _ensure_session_alive(self):
        """Verifica se a sessão ainda está viva, reinicia se necessário"""
        if not self.is_running or not self.page:
            logger.warning("[Opera] Session dead, restarting...")
            self.start_session(headless=True)
            return

        # Check if session is too old (30 minutes)
        if self.session_start_time and (time.time() - self.session_start_time) > 1800:
            logger.info("[Opera] Session expired (30min), restarting...")
            self.stop_session()
            self.start_session(headless=True)

    def search_and_extract(self, title: str, year: str = None) -> dict:
        """
        Busca um título no Opera e extrai o link do vídeo.

        Returns:
            dict: {
                'success': bool,
                'video_url': str or None,
                'scraped_title': str,  # Título real encontrado no Opera
                'error': str or None
            }
        """
        self._ensure_session_alive()

        result = {
            "success": False,
            "video_url": None,
            "scraped_title": None,
            "error": None,
        }

        try:
            # Ensure we're on search page
            if "/movie/search" not in self.page.url:
                logger.info("[Opera] Navigating to search page...")
                self.page.goto(
                    "http://web.operatopzera.net/#/movie/search/", timeout=15000
                )

            INPUT_SELECTOR = "input[placeholder='Search stream...']"
            self.page.wait_for_selector(INPUT_SELECTOR, state="visible", timeout=5000)

            # Clear and type search
            self.page.fill(INPUT_SELECTOR, "")
            self.page.fill(INPUT_SELECTOR, title)
            time.sleep(0.5)

            logger.info(f"[Opera] Searching for: {title}")
            self.page.keyboard.press("Enter")
            time.sleep(2)

            # Wait for results
            try:
                # Try to find the title in results
                result_selector = f"a[href*='/movie/']"
                self.page.wait_for_selector(result_selector, timeout=5000)
            except:
                result["error"] = f"No results found for '{title}'"
                logger.warning(f"[Opera] {result['error']}")
                return result

            # Find the best matching result
            cards = self.page.locator("a[href*='/movie/']").all()
            target_card = None
            scraped_title = None

            for card in cards:
                try:
                    card_text = card.inner_text().strip()
                    card_href = card.get_attribute("href")

                    # Skip if not a movie info link
                    if "/info/" not in card_href:
                        continue

                    # Check if title matches (case insensitive, partial match)
                    search_title_clean = title.lower().replace(" ", "")
                    card_title_clean = card_text.lower().replace(" ", "")

                    if (
                        search_title_clean in card_title_clean
                        or card_title_clean in search_title_clean
                    ):
                        # Year validation if provided
                        if year and year in card_text:
                            target_card = card
                            scraped_title = card_text.split("\n")[0].strip()
                            break
                        elif not year:
                            target_card = card
                            scraped_title = card_text.split("\n")[0].strip()
                            break

                except:
                    continue

            if not target_card:
                result["error"] = f"No matching result found for '{title}'"
                logger.warning(f"[Opera] {result['error']}")
                return result

            result["scraped_title"] = scraped_title
            logger.info(f"[Opera] Found match: {scraped_title}")

            # Click on the result
            target_card.scroll_into_view_if_needed()
            target_card.click()
            time.sleep(2)

            # Now on movie detail page - extract video URL
            video_url = self._extract_video_from_page()

            if video_url:
                result["success"] = True
                result["video_url"] = video_url
                logger.info(f"[Opera] Video extracted: {video_url}")
            else:
                result["error"] = "Could not extract video URL from page"
                logger.warning(f"[Opera] {result['error']}")

            # Return to search page for next query
            self.page.goto("http://web.operatopzera.net/#/movie/search/")

        except Exception as e:
            result["error"] = f"Scraping error: {str(e)}"
            logger.error(f"[Opera] {result['error']}")
            # Try to recover
            try:
                self.page.goto("http://web.operatopzera.net/#/movie/search/")
            except:
                pass

        return result

    def _extract_video_from_page(self) -> str:
        """Extrai URL do vídeo da página atual"""
        video_url = None

        try:
            # Try to find and click play button
            if "/play/" not in self.page.url:
                play_btn = self.page.locator(
                    "a[href*='/play/'], button:has-text('Play'), button:has-text('Assistir')"
                ).first
                if play_btn.is_visible(timeout=5000):
                    logger.info("[Opera] Clicking play button...")
                    play_btn.click()
                    time.sleep(3)

            # Extract video source
            self.page.wait_for_selector("video", timeout=20000)

            # Try multiple times to get the src
            for attempt in range(15):
                src = self.page.evaluate(
                    "document.querySelector('video') ? document.querySelector('video').src : null"
                )
                if src and src.startswith("http") and "blob" not in src:
                    video_url = src
                    break
                time.sleep(1)

            # Fallback: try to find iframe
            if not video_url:
                iframe = self.page.query_selector("iframe")
                if iframe:
                    src = iframe.get_attribute("src")
                    if src and src.startswith("http"):
                        video_url = src

        except Exception as e:
            logger.error(f"[Opera] Error extracting video: {e}")

        return video_url


# Global instance for reuse
_dedicated_scraper = None


def get_dedicated_scraper():
    """Get or create the dedicated Opera scraper instance"""
    global _dedicated_scraper
    if _dedicated_scraper is None:
        _dedicated_scraper = OperaTopzeraScraper()
    return _dedicated_scraper


def scrape_opera_only(title: str, year: str = None) -> dict:
    """
    Scrape ONLY from Opera Topzera - no fallbacks.
    Returns dict with success status and video URL.
    """
    scraper = get_dedicated_scraper()

    if not scraper.is_running:
        scraper.start_session(headless=True)

    return scraper.search_and_extract(title, year)


def scrape_opera_only_simple(title: str, year: str = None) -> str:
    """
    Simple wrapper that returns only the video URL or None.
    Use this for backward compatibility.
    """
    result = scrape_opera_only(title, year)
    if result["success"]:
        return result["video_url"]
    return None


# Backward compatibility
scrape_operatopzera = scrape_opera_only_simple


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test
    scraper = OperaTopzeraScraper()
    scraper.start_session(headless=False)

    test_title = "A Lista de Schindler"
    print(f"\nTesting: {test_title}")
    result = scraper.search_and_extract(test_title)

    print(f"Success: {result['success']}")
    print(f"Scraped Title: {result['scraped_title']}")
    print(f"Video URL: {result['video_url']}")
    print(f"Error: {result['error']}")

    scraper.stop_session()
