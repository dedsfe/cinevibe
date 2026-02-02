"""
Improved Opera Topzera Scraper v2
Handles popups, better timeouts, flexible title matching
"""

import logging
import urllib.parse
import time
import re
import unicodedata
from difflib import SequenceMatcher
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class ImprovedOperaScraper:
    """
    Scraper melhorado com:
    - Tratamento de popups/banners
    - Timeout inteligente
    - Busca flexível com variações de título
    """

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = False

    def start_session(self, headless=True):
        """Inicia sessão no Opera Topzera"""
        try:
            logger.info("[Improved Opera] Starting session...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            self.page = self.context.new_page()
            self.is_running = True

            # Login
            base_url = "http://web.operatopzera.net/#/"
            logger.info(f"[Improved Opera] Navigating to {base_url}")
            self.page.goto(base_url, timeout=60000)
            self.page.wait_for_load_state("networkidle", timeout=60000)

            # Handle login
            try:
                login_selector = "input[name='username']"
                if self.page.locator(login_selector).is_visible(timeout=5000):
                    logger.info("[Improved Opera] Logging in...")
                    self.page.fill("input[name='username']", "t2TGgarYJ")
                    self.page.fill("input[name='password']", "66e74xKRJ")
                    self.page.click("button:has-text('Login')")
                    self.page.wait_for_url("**/#/", timeout=30000)
                    time.sleep(3)
                    logger.info("[Improved Opera] Login successful")
            except Exception as e:
                logger.warning(f"[Improved Opera] Login warning: {e}")

            # Navigate to search page
            search_url = "http://web.operatopzera.net/#/movie/search/"
            self.page.goto(search_url, timeout=30000)

            # Handle any initial popups/modals
            self._close_popups()

            INPUT_SELECTOR = "input[placeholder='Search stream...']"
            self.page.wait_for_selector(INPUT_SELECTOR, state="visible", timeout=15000)
            logger.info("[Improved Opera] Session ready")

        except Exception as e:
            logger.error(f"[Improved Opera] Failed to start session: {e}")
            self.stop_session()
            raise e

    def stop_session(self):
        """Encerra sessão"""
        logger.info("[Improved Opera] Stopping session...")
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

    def _close_popups(self):
        """Tenta fechar popups/banners comuns"""
        try:
            # Common popup selectors
            popup_selectors = [
                "button[aria-label='Close']",
                "button[class*='close']",
                "button[class*='dismiss']",
                "[class*='modal'] button",
                "[class*='popup'] button",
                "[class*='banner'] button",
                "button:has-text('Close')",
                "button:has-text('Fechar')",
                "button:has-text('X')",
            ]

            for selector in popup_selectors:
                try:
                    if self.page.locator(selector).is_visible(timeout=1000):
                        self.page.click(selector, timeout=2000)
                        logger.info(f"[Improved Opera] Closed popup: {selector}")
                        time.sleep(0.5)
                except:
                    pass
        except:
            pass

    def _normalize_title(self, title):
        """Normaliza título para comparação (remove acentos, lowercase)"""
        # Remove acentos
        normalized = unicodedata.normalize("NFKD", title)
        normalized = "".join([c for c in normalized if not unicodedata.combining(c)])
        # Remove caracteres especiais e converte para lowercase
        normalized = re.sub(r"[^\w\s]", "", normalized.lower())
        return normalized.strip()

    def _generate_title_variations(self, title):
        """Gera variações do título para busca"""
        variations = [title]

        # Normalizado (sem acentos)
        normalized = self._normalize_title(title)
        if normalized != title.lower():
            variations.append(normalized)

        # Primeiras palavras (primeiras 2-3 palavras)
        words = title.split()
        if len(words) > 2:
            variations.append(" ".join(words[:2]))
            variations.append(" ".join(words[:3]))

        # Sem subtítulo (tudo antes do :)
        if ":" in title:
            main_title = title.split(":")[0].strip()
            variations.append(main_title)

        return list(set(variations))  # Remove duplicatas

    def _calculate_similarity(self, str1, str2):
        """Calcula similaridade entre strings"""
        s1 = self._normalize_title(str1)
        s2 = self._normalize_title(str2)

        # Se um contém o outro, é match forte
        if s1 in s2 or s2 in s1:
            return max(len(s1), len(s2)) / max(len(s1), len(s2)) * 0.9

        # Usa SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()

    def _extract_video_id(self, url):
        """Extrai ID do vídeo do URL jt0x"""
        match = re.search(r"/([^/]+)\.mp4$", url)
        if match:
            return match.group(1)
        return None

    def _safe_click(self, locator, timeout=10000):
        """Click seguro que lida com overlays"""
        try:
            # Tenta click normal
            locator.click(timeout=timeout)
            return True
        except:
            try:
                # Tenta force click
                locator.click(force=True, timeout=timeout)
                return True
            except:
                try:
                    # Tenta via JavaScript
                    element = locator.element_handle()
                    self.page.evaluate("(element) => element.click()", element)
                    return True
                except:
                    return False

    def scrape_movie(self, expected_title: str, year: str = None) -> dict:
        """
        Scrape com melhorias:
        - Lida com popups
        - Tenta múltiplas variações do título
        - Click mais robusto
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
            "attempted_variations": [],
        }

        # Gera variações do título
        variations = self._generate_title_variations(expected_title)
        logger.info(
            f"[Improved Opera] Will try {len(variations)} title variations: {variations}"
        )

        for attempt, title_variation in enumerate(variations):
            try:
                logger.info(
                    f"[Improved Opera] Attempt {attempt + 1}/{len(variations)}: '{title_variation}'"
                )
                result["attempted_variations"].append(title_variation)

                # Ensure we're on search page
                if "/movie/search" not in self.page.url:
                    self.page.goto(
                        "http://web.operatopzera.net/#/movie/search/", timeout=15000
                    )
                    self._close_popups()

                INPUT_SELECTOR = "input[placeholder='Search stream...']"
                self.page.wait_for_selector(
                    INPUT_SELECTOR, state="visible", timeout=5000
                )

                # Clear and type search
                self.page.fill(INPUT_SELECTOR, "")
                time.sleep(0.3)
                self.page.fill(INPUT_SELECTOR, title_variation)
                time.sleep(0.3)

                self.page.keyboard.press("Enter")
                time.sleep(2)

                # Close any popups that appeared
                self._close_popups()

                # Wait for results
                try:
                    self.page.wait_for_selector("a[href*='/movie/']", timeout=5000)
                except:
                    logger.warning(
                        f"[Improved Opera] No results for '{title_variation}'"
                    )
                    continue

                # Get all results
                cards = self.page.locator("a[href*='/movie/']").all()

                best_match = None
                best_similarity = 0
                best_title = None

                for card in cards:
                    try:
                        card_text = card.inner_text().strip()
                        card_href = card.get_attribute("href")

                        # Skip category links
                        if "/category/" in card_href and "/info/" not in card_href:
                            continue

                        # Extract title (first line)
                        lines = card_text.split("\n")
                        candidate_title = lines[0].strip()

                        # Calculate similarity
                        similarity = self._calculate_similarity(
                            expected_title, candidate_title
                        )

                        logger.info(
                            f"[Improved Opera] Candidate: '{candidate_title}' | Similarity: {similarity:.2%}"
                        )

                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = card
                            best_title = candidate_title

                    except Exception as e:
                        continue

                # Check if we found a good match
                MIN_SIMILARITY = 0.35  # Lowered threshold
                if best_similarity >= MIN_SIMILARITY:
                    logger.info(
                        f"[Improved Opera] Good match found: '{best_title}' ({best_similarity:.2%})"
                    )

                    result["scraped_title"] = best_title
                    result["similarity"] = best_similarity

                    # Try to click with multiple strategies
                    click_success = False

                    # Strategy 1: Normal click
                    try:
                        best_match.click(timeout=5000)
                        click_success = True
                    except:
                        pass

                    # Strategy 2: Force click
                    if not click_success:
                        try:
                            best_match.click(force=True, timeout=5000)
                            click_success = True
                        except:
                            pass

                    # Strategy 3: JavaScript click
                    if not click_success:
                        try:
                            element = best_match.element_handle()
                            self.page.evaluate("(el) => el.click()", element)
                            click_success = True
                        except:
                            pass

                    if not click_success:
                        result["error"] = f"Failed to click on movie card"
                        continue

                    time.sleep(3)
                    self._close_popups()

                    # Extract video URL
                    video_url = self._extract_video_from_page()

                    if video_url:
                        video_id = self._extract_video_id(video_url)
                        if video_id:
                            result["success"] = True
                            result["video_url"] = video_url
                            result["video_id"] = video_id
                            result["validation_passed"] = True

                            logger.info(
                                f"[Improved Opera] ✅ SUCCESS with variation '{title_variation}'!"
                            )
                            logger.info(f"[Improved Opera] Title: {best_title}")
                            logger.info(f"[Improved Opera] Video ID: {video_id}")

                            # Return to search page
                            self.page.goto(
                                "http://web.operatopzera.net/#/movie/search/"
                            )
                            return result
                        else:
                            result["error"] = "Could not extract video ID"
                    else:
                        result["error"] = "Could not extract video URL"
                else:
                    logger.warning(
                        f"[Improved Opera] Best match similarity too low: {best_similarity:.2%}"
                    )

            except Exception as e:
                logger.error(
                    f"[Improved Opera] Error with variation '{title_variation}': {e}"
                )
                continue

        # If we get here, all variations failed
        result["error"] = f"Tried {len(variations)} title variations, none worked"
        return result

    def _extract_video_from_page(self) -> str:
        """Extrai URL do vídeo com retry"""
        video_url = None
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                # Close any popups
                self._close_popups()

                # Try to find and click play button if not on play page
                if "/play/" not in self.page.url:
                    play_selectors = [
                        "a[href*='/play/']",
                        "button:has-text('Play')",
                        "button:has-text('Assistir')",
                        "[class*='play']",
                        "[class*='watch']",
                    ]

                    for selector in play_selectors:
                        try:
                            btn = self.page.locator(selector).first
                            if btn.is_visible(timeout=2000):
                                logger.info(
                                    f"[Improved Opera] Clicking play button: {selector}"
                                )
                                btn.click(timeout=5000)
                                time.sleep(3)
                                break
                        except:
                            continue

                # Wait for video
                self.page.wait_for_selector("video", timeout=15000)

                # Try to get video src
                for _ in range(10):
                    src = self.page.evaluate("""
                        () => {
                            const video = document.querySelector('video');
                            return video ? video.src : null;
                        }
                    """)

                    if src and src.startswith("http") and "blob" not in src:
                        video_url = src
                        break

                    time.sleep(1)

                if video_url:
                    break

                # Try iframe fallback
                if not video_url:
                    try:
                        iframe = self.page.query_selector("iframe")
                        if iframe:
                            src = iframe.get_attribute("src")
                            if src and src.startswith("http"):
                                video_url = src
                                break
                    except:
                        pass

            except Exception as e:
                logger.error(f"[Improved Opera] Attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                continue

        return video_url


# Global instance
_improved_scraper = None


def get_improved_scraper():
    """Get or create the improved scraper instance"""
    global _improved_scraper
    if _improved_scraper is None:
        _improved_scraper = ImprovedOperaScraper()
    return _improved_scraper


def scrape_movie_improved(title: str, year: str = None) -> dict:
    """
    Scrape com scraper melhorado
    """
    scraper = get_improved_scraper()

    if not scraper.is_running:
        scraper.start_session(headless=True)

    return scraper.scrape_movie(title, year)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

    # Test
    scraper = ImprovedOperaScraper()
    scraper.start_session(headless=False)

    test_movies = ["A Lista de Schindler", "Davi: Nasce Um Rei", "O Poderoso Chefão"]

    for movie in test_movies:
        print(f"\n{'=' * 60}")
        print(f"Testing: {movie}")
        print("=" * 60)

        result = scraper.scrape_movie(movie)

        print(f"Success: {result['success']}")
        print(f"Title match: {result['similarity']:.1%}")
        print(f"Scraped title: {result['scraped_title']}")
        print(f"Video ID: {result['video_id']}")
        print(f"URL: {result['video_url']}")
        print(f"Error: {result['error']}")
        print(f"Tried variations: {result['attempted_variations']}")

    scraper.stop_session()
