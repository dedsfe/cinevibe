"""
Opera Topzera - Catalog Browser
Navega pelo catálogo diretamente e extrai links com IDs fixos
"""

import logging
import re
import time
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class OperaCatalogBrowser:
    """
    Navega pelo catálogo do Opera de forma estável:
    1. Mantém mesma aba
    2. Usa lista direta de filmes em /movie/
    3. Extrai ID da URL (category/XXX/YYYYY/)
    4. Navega para play page
    5. Extrai MP4
    """

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = False
        self.base_url = "http://web.operatopzera.net/#/"

    def start_session(self, headless=True):
        """Inicia sessão mantendo mesma aba"""
        try:
            logger.info("[Catalog Browser] Starting session...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            self.page = self.context.new_page()
            self.is_running = True

            # Login
            logger.info("[Catalog Browser] Navigating to home...")
            self.page.goto(self.base_url, timeout=60000)
            self.page.wait_for_load_state("networkidle", timeout=60000)

            # Handle login
            try:
                if self.page.locator("input[name='username']").is_visible(timeout=5000):
                    logger.info("[Catalog Browser] Logging in...")
                    self.page.fill("input[name='username']", "t2TGgarYJ")
                    self.page.fill("input[name='password']", "66e74xKRJ")
                    self.page.click("button:has-text('Login')")
                    self.page.wait_for_url("**/#/", timeout=30000)
                    time.sleep(2)
            except:
                pass

            logger.info("[Catalog Browser] Session ready!")
            return True

        except Exception as e:
            logger.error(f"[Catalog Browser] Failed to start: {e}")
            self.stop_session()
            return False

    def stop_session(self):
        """Encerra sessão"""
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

    def search_and_extract(self, search_title):
        """
        Busca um filme específico no catálogo
        """
        logger.info(f"[Catalog Browser] Searching for: {search_title}")

        # Navigate to search page directly
        search_url = f"{self.base_url}movie/search/"
        logger.info(f"[Catalog Browser] Navigating to: {search_url}")
        self.page.goto(search_url, timeout=30000)
        self.page.wait_for_load_state("load", timeout=15000)
        time.sleep(2)

        # Try variations of the title
        variations = [
            search_title,
            search_title.lower(),
            search_title.split(":")[0].strip() if ":" in search_title else search_title,
            " ".join(search_title.split()[:2])
            if len(search_title.split()) > 2
            else search_title,
        ]

        for variation in variations:
            logger.info(f"[Catalog Browser] Trying variation: {variation}")

            try:
                # Fill search input
                search_input = self.page.locator(
                    "input[placeholder='Search stream...']"
                )
                search_input.fill("")
                time.sleep(0.3)
                search_input.fill(variation)
                time.sleep(0.3)
                self.page.keyboard.press("Enter")
                time.sleep(3)

                # Get results
                cards = self.page.locator(
                    "a[href*='/movie/category/'][href*='/info/']"
                ).all()
                logger.info(f"[Catalog Browser] Found {len(cards)} results")

                # Find best match
                for card in cards:
                    try:
                        href = card.get_attribute("href")
                        text = card.inner_text().strip()
                        title = text.split("\n")[0].strip()

                        # Check if match
                        if (
                            variation.lower() in title.lower()
                            or title.lower() in variation.lower()
                        ):
                            logger.info(f"[Catalog Browser] Found match: {title}")

                            # Extract IDs from URL
                            match = re.search(r"/category/(\d+)/(\d+)/info", href)
                            if match:
                                category_id = match.group(1)
                                movie_id = match.group(2)

                                # Navigate to play page
                                play_url = f"{self.base_url}movie/category/{category_id}/{movie_id}/play/"
                                logger.info(
                                    f"[Catalog Browser] Navigating to play page..."
                                )
                                self.page.goto(play_url, timeout=15000)
                                time.sleep(3)

                                # Extract video URL
                                video_url = None
                                for attempt in range(10):
                                    src = self.page.evaluate("""
                                        () => {
                                            const video = document.querySelector('video');
                                            return video ? video.src : null;
                                        }
                                    """)
                                    if src and src.startswith("http") and ".mp4" in src:
                                        video_url = src
                                        break
                                    time.sleep(1)

                                if video_url:
                                    logger.info(
                                        f"[Catalog Browser] Found video: {video_url[:60]}..."
                                    )
                                    return {
                                        "success": True,
                                        "scraped_title": title,
                                        "movie_id": movie_id,
                                        "category_id": category_id,
                                        "video_url": video_url,
                                    }
                    except Exception as e:
                        logger.warning(f"[Catalog Browser] Error processing card: {e}")
                        continue

            except Exception as e:
                logger.error(f"[Catalog Browser] Error with variation: {e}")
                continue

        return {
            "success": False,
            "error": "Movie not found in catalog",
            "attempted_variations": variations,
        }


# Global instance
_catalog_browser = None


def get_catalog_browser():
    """Get or create catalog browser instance"""
    global _catalog_browser
    if _catalog_browser is None:
        _catalog_browser = OperaCatalogBrowser()
    return _catalog_browser


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Test
    browser = OperaCatalogBrowser()
    browser.start_session(headless=False)

    print("\n" + "=" * 80)
    print("TEST: Search for specific movie")
    print("=" * 80)
    result = browser.search_and_extract("96 Minutos")
    print(f"\nResult: {result}")

    browser.stop_session()
