"""
Scraper para adicionar MP4 aos filmes disponíveis no catálogo Opera
Pega filmes da lista /movie/, filtra CAM/TS, extrai MP4
"""

import logging
import re
import time
import sys
import os
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_embed, get_conn


def check_movie_exists_in_db(movie_id):
    """Verifica se o filme já existe no banco de dados pelo Opera ID"""
    try:
        conn = get_conn()
        c = conn.cursor()
        # Procura pelo movie_id no embed_url (ex: .../movie/t2TGgarYJ/66e74xKRJ/217376.mp4)
        c.execute(
            "SELECT title FROM links WHERE embed_url LIKE ?", (f"%/{movie_id}.mp4%",)
        )
        result = c.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"[Scraper] Error checking database: {e}")
        return False  # Se der erro, assume que não existe e tenta processar


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Palavras-chave para identificar filmes de baixa qualidade (CAM/TS)
LOW_QUALITY_KEYWORDS = [
    "cam",
    "ts",
    "hdts",
    "hdcam",
    "telesync",
    "telecine",
    "dvdscr",
    "screener",
]


class CatalogMovieScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = False
        self.base_url = "http://web.operatopzera.net/#/"

    def start_session(self, headless=False):
        """Inicia sessão: Home → Login → /movie/"""
        try:
            logger.info("[Scraper] Starting browser...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            self.page = self.context.new_page()
            self.is_running = True

            # 1. HOME
            logger.info(f"[Scraper] Home: {self.base_url}")
            self.page.goto(self.base_url, timeout=60000)
            self.page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(2)

            # 2. LOGIN
            try:
                if self.page.locator("input[name='username']").is_visible(timeout=5000):
                    logger.info("[Scraper] Logging in...")
                    self.page.fill("input[name='username']", "t2TGgarYJ")
                    self.page.fill("input[name='password']", "66e74xKRJ")
                    self.page.click("button:has-text('Login')")
                    self.page.wait_for_url("**/#/", timeout=30000)
                    time.sleep(2)
            except:
                pass

            # 3. /movie/ (lista)
            movies_url = f"{self.base_url}movie/"
            logger.info(f"[Scraper] Movies list: {movies_url}")
            self.page.goto(movies_url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)

            logger.info("[Scraper] Session ready!")
            return True

        except Exception as e:
            logger.error(f"[Scraper] Failed: {e}")
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

    def is_low_quality(self, title):
        """Verifica se é CAM/TS/etc"""
        title_lower = title.lower()
        for keyword in LOW_QUALITY_KEYWORDS:
            if keyword in title_lower:
                return True
        return False

    def get_movie_cards(self):
        """Pega todos os cards de filmes da página atual"""
        try:
            # Aguarda pelo menos um card aparecer (máx 5 segundos)
            self.page.wait_for_selector(
                "a[href*='/movie/category/'][href*='/info/']",
                state="attached",
                timeout=5000,
            )
            cards = self.page.locator(
                "a[href*='/movie/category/'][href*='/info/']"
            ).all()
            return cards
        except:
            return []

    def extract_movie_info(self, card):
        """Extrai info do card: titulo, href, IDs"""
        try:
            href = card.get_attribute("href")
            text = card.inner_text().strip()
            title = text.split("\n")[0].strip()

            # Extrai IDs: /category/XXX/YYYY/info
            match = re.search(r"/category/(\d+)/(\d+)/info", href)
            if match:
                return {
                    "title": title,
                    "href": href,
                    "category_id": match.group(1),
                    "movie_id": match.group(2),
                }
        except:
            pass
        return None

    def get_video_from_play(self, category_id, movie_id, movie_title):
        """Navega para play page e extrai MP4 - versão rápida"""
        try:
            play_url = f"{self.base_url}movie/category/{category_id}/{movie_id}/play/"
            logger.info(f"[Scraper] Play page: {play_url}")

            self.page.goto(play_url, timeout=15000)
            time.sleep(2)

            # Extrai video - max 8 segundos
            video_url = None
            for attempt in range(8):
                video_url = self.page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        if (video && video.src && video.src.includes('.mp4')) return video.src;
                        const sources = video ? video.querySelectorAll('source') : [];
                        for (let src of sources) {
                            if (src.src && src.src.includes('.mp4')) return src.src;
                        }
                        // Tenta iframe também
                        const iframe = document.querySelector('iframe');
                        if (iframe && iframe.src) return iframe.src;
                        return null;
                    }
                """)

                if video_url and video_url.startswith("http"):
                    logger.info(f"[Scraper] ✓ Video found!")
                    return video_url

                time.sleep(1)

            logger.warning("[Scraper] ✗ No video found")
            return None

        except Exception as e:
            logger.error(f"[Scraper] Error: {e}")
            return None

        except Exception as e:
            logger.error(f"[Scraper] Error: {e}")
            return None

    def scrape_movies(self, max_movies=5):
        """
        Scrapeia N filmes do catálogo
        Pega da lista, filtra CAM/TS, extrai MP4
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"[Scraper] Starting - will scrape {max_movies} movies")
        logger.info(f"{'=' * 60}\n")

        if not self.start_session(headless=True):
            return

        results = []
        processed = set()  # Evita duplicatas
        scroll_count = 0
        max_scrolls = 20

        try:
            # Aguarda página carregar completamente antes de começar
            logger.info("[Scraper] Waiting for page to fully load...")
            time.sleep(3)

            while len(results) < max_movies and scroll_count < max_scrolls:
                logger.info(f"\n[Scraper] Scanning page (scroll {scroll_count + 1})...")

                # Aguarda após scroll (exceto primeira vez)
                if scroll_count > 0:
                    time.sleep(2)

                cards = self.get_movie_cards()
                logger.info(f"[Scraper] Found {len(cards)} cards")

                for card in cards:
                    if len(results) >= max_movies:
                        break

                    movie_info = self.extract_movie_info(card)
                    if not movie_info:
                        continue

                    movie_id = movie_info["movie_id"]

                    # Pula se já processou nesta sessão
                    if movie_id in processed:
                        continue
                    processed.add(movie_id)

                    # ✅ VERIFICA SE JÁ EXISTE NO BANCO
                    if check_movie_exists_in_db(movie_id):
                        logger.info(
                            f"[Scraper] Skip (already in DB): {movie_info['title']} (ID: {movie_id})"
                        )
                        continue

                    title = movie_info["title"]

                    # Pula se é CAM/TS
                    if self.is_low_quality(title):
                        logger.info(f"[Scraper] Skip (low quality): {title}")
                        continue

                    logger.info(f"\n{'#' * 60}")
                    logger.info(
                        f"[Scraper] Movie {len(results) + 1}/{max_movies}: {title}"
                    )
                    logger.info(f"[Scraper] ID: {movie_id}")
                    logger.info(f"{'#' * 60}")

                    # Extrai MP4
                    video_url = self.get_video_from_play(
                        movie_info["category_id"], movie_id, title
                    )

                    if video_url:
                        # Salva no banco
                        try:
                            save_embed(
                                title=title,
                                embed_url=video_url,
                                tmdb_id=None,  # Não temos TMDB ID para filmes do catálogo
                                original_raw_title=title,
                            )
                            logger.info(f"[Scraper] ✓ Saved to database!")
                            results.append(
                                {
                                    "title": title,
                                    "movie_id": movie_id,
                                    "video_url": video_url,
                                    "success": True,
                                }
                            )
                        except Exception as e:
                            logger.error(f"[Scraper] ✗ Database error: {e}")
                            logger.error(
                                "[Scraper] 🛑 STOPPING - Error detected as requested!"
                            )
                            raise
                    else:
                        logger.error(f"[Scraper] ✗ No MP4 found for: {title}")
                        logger.error(
                            "[Scraper] 🛑 STOPPING - Error detected as requested!"
                        )
                        raise Exception(f"MP4 extraction failed for {title} - STOPPING")

                    # Volta para lista (se não for o último filme)
                    if len(results) < max_movies:
                        logger.info("[Scraper] Returning to list...")
                        self.page.goto(f"{self.base_url}movie/", timeout=15000)
                        time.sleep(1)

                # Scroll para mais filmes
                if len(results) < max_movies:
                    logger.info("[Scraper] Scrolling for more...")
                    self.page.mouse.wheel(0, 800)
                    time.sleep(2)
                    scroll_count += 1

        except Exception as e:
            logger.error(f"[Scraper] Fatal error: {e}")
        finally:
            self.stop_session()

        # Resumo
        logger.info(f"\n{'=' * 60}")
        logger.info("SCRAPING COMPLETE")
        logger.info(f"{'=' * 60}")
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"Total: {len(results)} movies")
        logger.info(f"Success: {success_count}")
        logger.info(f"Failed: {len(results) - success_count}")

        for r in results:
            status = "✓" if r.get("success") else "✗"
            logger.info(f"  {status} {r['title']}")

        return results


if __name__ == "__main__":
    scraper = CatalogMovieScraper()
    scraper.scrape_movies(max_movies=15)  # Pula filmes já existentes no DB
