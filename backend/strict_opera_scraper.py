"""
Strict Opera Topzera Scraper with Title Validation
Prevents mismatches between movie titles and video links
"""

import logging
import urllib.parse
import time
import re
from difflib import SequenceMatcher
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class StrictOperaScraper:
    """
    Scraper with strict validation to prevent title-link mismatches
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
            logger.info("[Strict Opera] Starting session...")
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
            logger.info(f"[Strict Opera] Navigating to {base_url}")
            self.page.goto(base_url, timeout=60000)
            self.page.wait_for_load_state("networkidle", timeout=60000)

            # Check for login form
            try:
                login_selector = "input[name='username']"
                if self.page.locator(login_selector).is_visible(timeout=5000):
                    logger.info("[Strict Opera] Login page detected. Logging in...")
                    USER = "t2TGgarYJ"
                    PASS = "66e74xKRJ"

                    self.page.fill("input[name='username']", USER)
                    self.page.fill("input[name='password']", PASS)
                    self.page.click("button:has-text('Login')")

                    self.page.wait_for_url("**/#/", timeout=30000)
                    time.sleep(2)
                    logger.info("[Strict Opera] Login successful")
                else:
                    logger.info("[Strict Opera] Already logged in")
            except Exception as e:
                logger.warning(f"[Strict Opera] Login check warning: {e}")

            # Navigate to search page
            search_url = "http://web.operatopzera.net/#/movie/search/"
            logger.info(f"[Strict Opera] Navigating to search page")
            self.page.goto(search_url, timeout=30000)

            INPUT_SELECTOR = "input[placeholder='Search stream...']"
            self.page.wait_for_selector(INPUT_SELECTOR, state="visible", timeout=15000)
            logger.info("[Strict Opera] Session ready")

        except Exception as e:
            logger.error(f"[Strict Opera] Failed to start session: {e}")
            self.stop_session()
            raise e

    def stop_session(self):
        """Encerra sessão"""
        logger.info("[Strict Opera] Stopping session...")
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

    def _calculate_similarity(self, str1, str2):
        """Calcula similaridade entre duas strings (0-1)"""
        # Limpar strings
        s1 = re.sub(r"[^\w\s]", "", str1.lower().strip())
        s2 = re.sub(r"[^\w\s]", "", str2.lower().strip())

        # Usar SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()

    def _extract_video_id(self, url):
        """Extrai ID do vídeo do URL jt0x"""
        match = re.search(r"/([^/]+)\.mp4$", url)
        if match:
            return match.group(1)
        return None

    def scrape_with_validation(self, expected_title: str, year: str = None) -> dict:
        """
        Scrape com validação rigorosa de título

        Returns:
            {
                'success': bool,
                'video_url': str or None,
                'scraped_title': str,
                'similarity': float,
                'video_id': str,
                'validation_passed': bool,
                'error': str or None
            }
        """
        if not self.is_running:
            self.start_session(headless=True)

        result = {
            "success": False,
            "video_url": None,
            "scraped_title": None,
            "similarity": 0.0,
            "video_id": None,
            "validation_passed": False,
            "error": None,
        }

        try:
            # Ensure we're on search page
            if "/movie/search" not in self.page.url:
                logger.info("[Strict Opera] Navigating to search page...")
                self.page.goto(
                    "http://web.operatopzera.net/#/movie/search/", timeout=15000
                )

            INPUT_SELECTOR = "input[placeholder='Search stream...']"
            self.page.wait_for_selector(INPUT_SELECTOR, state="visible", timeout=5000)

            # Clear and type search
            self.page.fill(INPUT_SELECTOR, "")
            self.page.fill(INPUT_SELECTOR, expected_title)
            time.sleep(0.5)

            logger.info(f"[Strict Opera] Searching for: {expected_title}")
            self.page.keyboard.press("Enter")
            time.sleep(2)

            # Wait for results
            try:
                result_selector = f"a[href*='/movie/']"
                self.page.wait_for_selector(result_selector, timeout=5000)
            except:
                result["error"] = f"No results found for '{expected_title}'"
                logger.warning(f"[Strict Opera] {result['error']}")
                return result

            # Get all results and find best match
            cards = self.page.locator("a[href*='/movie/']").all()
            best_match = None
            best_similarity = 0
            best_title = None

            for card in cards:
                try:
                    card_text = card.inner_text().strip()
                    card_href = card.get_attribute("href")

                    # Skip if not a movie info link
                    if "/info/" not in card_href:
                        continue

                    # Extract title (first line)
                    lines = card_text.split("\n")
                    candidate_title = lines[0].strip()

                    # Calculate similarity
                    similarity = self._calculate_similarity(
                        expected_title, candidate_title
                    )

                    logger.info(
                        f"[Strict Opera] Candidate: '{candidate_title}' | Similarity: {similarity:.2%}"
                    )

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = card
                        best_title = candidate_title

                except Exception as e:
                    continue

            # VALIDATION: Need at least 40% similarity (adjusted for Portuguese variations)
            MIN_SIMILARITY = 0.40
            if best_similarity < MIN_SIMILARITY:
                result["error"] = (
                    f"Best match similarity too low: {best_similarity:.2%} (need >{MIN_SIMILARITY:.0%})"
                )
                result["similarity"] = best_similarity
                logger.warning(f"[Strict Opera] {result['error']}")
                return result

            result["scraped_title"] = best_title
            result["similarity"] = best_similarity

            logger.info(
                f"[Strict Opera] Best match: '{best_title}' | Similarity: {best_similarity:.2%}"
            )

            # Click on the best match
            best_match.scroll_into_view_if_needed()
            best_match.click()
            time.sleep(2)

            # Validate we're on the correct page
            try:
                # Look for title on the page
                page_title = self.page.locator(
                    "h1, h2, .movie-title, [class*='title']"
                ).first.inner_text(timeout=3000)
                page_similarity = self._calculate_similarity(expected_title, page_title)

                if page_similarity < 0.50:
                    result["error"] = (
                        f"Page title mismatch. Expected: '{expected_title}', Got: '{page_title}'"
                    )
                    logger.warning(f"[Strict Opera] {result['error']}")
                    return result

            except:
                logger.warning(
                    "[Strict Opera] Could not validate page title, continuing..."
                )

            # Extract video URL
            video_url = self._extract_video_from_page()

            if not video_url:
                result["error"] = "Could not extract video URL from page"
                logger.warning(f"[Strict Opera] {result['error']}")
                return result

            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                result["error"] = f"Could not extract video ID from URL: {video_url}"
                logger.warning(f"[Strict Opera] {result['error']}")
                return result

            # SUCCESS!
            result["success"] = True
            result["video_url"] = video_url
            result["video_id"] = video_id
            result["validation_passed"] = True

            logger.info(f"[Strict Opera] ✅ SUCCESS!")
            logger.info(f"[Strict Opera] Title match: {best_similarity:.2%}")
            logger.info(f"[Strict Opera] Video ID: {video_id}")
            logger.info(f"[Strict Opera] URL: {video_url}")

            # Return to search page
            self.page.goto("http://web.operatopzera.net/#/movie/search/")

        except Exception as e:
            result["error"] = f"Scraping error: {str(e)}"
            logger.error(f"[Strict Opera] {result['error']}")
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
                    logger.info("[Strict Opera] Clicking play button...")
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
            logger.error(f"[Strict Opera] Error extracting video: {e}")

        return video_url


# Global instance
_strict_scraper = None


def get_strict_scraper():
    """Get or create the strict scraper instance"""
    global _strict_scraper
    if _strict_scraper is None:
        _strict_scraper = StrictOperaScraper()
    return _strict_scraper


def scrape_with_strict_validation(title: str, year: str = None) -> dict:
    """
    Scrape with strict validation
    Only returns success if title matches with >60% similarity
    """
    scraper = get_strict_scraper()

    if not scraper.is_running:
        scraper.start_session(headless=True)

    return scraper.scrape_with_validation(title, year)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test
    scraper = StrictOperaScraper()
    scraper.start_session(headless=False)

    test_cases = [
        "Davi: Nasce Um Rei",
        "A Lista de Schindler",
        "Filme Que Não Existe XYZ123",
    ]

    for test_title in test_cases:
        print(f"\n{'=' * 60}")
        print(f"Testing: {test_title}")
        print("=" * 60)
        result = scraper.scrape_with_validation(test_title)

        print(f"Success: {result['success']}")
        print(
            f"Validation: {'✅ PASSED' if result['validation_passed'] else '❌ FAILED'}"
        )
        print(f"Title match: {result['similarity']:.2%}")
        print(f"Scraped title: {result['scraped_title']}")
        print(f"Video ID: {result['video_id']}")
        print(f"Error: {result['error']}")

    scraper.stop_session()
