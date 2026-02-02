"""
Scraper para 3 filmes clássicos específicos:
- O Poderoso Chefão (ID: 238)
- A Lista de Schindler (ID: 424)
- Um Sonho de Liberdade (ID: 278)

Fluxo: Home → Login → /movie/ → Find → Extract ID → /play/ → Extract MP4 → Update DB
Sempre mantendo na MESMA aba.
"""

import logging
import re
import time
import sys
import os
from playwright.sync_api import sync_playwright

# Add parent dir to import database
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_embed, get_conn

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 3 filmes para buscar
TARGET_MOVIES = [
    {
        "tmdb_id": "238",
        "title": "O Poderoso Chefão",
        "search_names": ["O Poderoso Chefão", "The Godfather", "Poderoso Chefão"],
    },
    {
        "tmdb_id": "424",
        "title": "A Lista de Schindler",
        "search_names": [
            "A Lista de Schindler",
            "Schindler's List",
            "Lista de Schindler",
        ],
    },
    {
        "tmdb_id": "278",
        "title": "Um Sonho de Liberdade",
        "search_names": [
            "Um Sonho de Liberdade",
            "The Shawshank Redemption",
            "Sonho de Liberdade",
        ],
    },
]


class ThreeMoviesScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = False
        self.base_url = "http://web.operatopzera.net/#/"

    def start_session(self, headless=False):
        """Inicia sessão: Home → Login"""
        try:
            logger.info("[Scraper] Starting browser session...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=headless)
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            self.page = self.context.new_page()
            self.is_running = True

            # 1. VAI PARA HOME
            logger.info(f"[Scraper] Navigating to HOME: {self.base_url}")
            self.page.goto(self.base_url, timeout=60000)
            self.page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(2)

            # 2. FAZ LOGIN (se necessário)
            try:
                login_selector = "input[name='username']"
                if self.page.locator(login_selector).is_visible(timeout=5000):
                    logger.info("[Scraper] Login form detected. Logging in...")
                    self.page.fill("input[name='username']", "t2TGgarYJ")
                    self.page.fill("input[name='password']", "66e74xKRJ")
                    self.page.click("button:has-text('Login')")
                    self.page.wait_for_url("**/#/", timeout=30000)
                    logger.info("[Scraper] Login successful!")
                    time.sleep(2)
                else:
                    logger.info("[Scraper] Already logged in or no login form found.")
            except Exception as e:
                logger.warning(f"[Scraper] Login check warning: {e}")

            # 3. VAI PARA /movie/ (mesma aba!)
            movies_url = f"{self.base_url}movie/"
            logger.info(f"[Scraper] Navigating to MOVIES list: {movies_url}")
            self.page.goto(movies_url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)

            logger.info("[Scraper] Session ready! Now on movies list page.")
            return True

        except Exception as e:
            logger.error(f"[Scraper] Failed to start session: {e}")
            self.stop_session()
            return False

    def stop_session(self):
        """Encerra sessão"""
        logger.info("[Scraper] Stopping session...")
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

    def find_movie_in_list(self, movie_data):
        """
        Procura o filme na lista de filmes (/movie/)
        Retorna: {"found": bool, "title": str, "detail_url": str, "movie_id": str, "category_id": str}
        """
        search_names = movie_data["search_names"]
        tmdb_id = movie_data["tmdb_id"]

        logger.info(f"\n{'=' * 60}")
        logger.info(f"[Scraper] Looking for: {movie_data['title']} (TMDB: {tmdb_id})")
        logger.info(f"[Scraper] Search variations: {search_names}")
        logger.info(f"{'=' * 60}")

        # Primeiro, tenta encontrar sem scroll (filmes visíveis)
        for attempt in range(3):  # 3 tentativas com scroll
            logger.info(f"[Scraper] Scanning attempt {attempt + 1}/3...")

            # Procura todos os cards de filme na página
            cards = self.page.locator(
                "a[href*='/movie/category/'][href*='/info/']"
            ).all()
            logger.info(f"[Scraper] Found {len(cards)} movie cards on screen")

            for card in cards:
                try:
                    href = card.get_attribute("href")
                    text = card.inner_text().strip()

                    # Pega só a primeira linha (título)
                    card_title = text.split("\n")[0].strip()

                    # Verifica se algum dos nomes de busca corresponde
                    for search_name in search_names:
                        # Match case-insensitive e parcial
                        if (
                            search_name.lower() in card_title.lower()
                            or card_title.lower() in search_name.lower()
                        ):
                            logger.info(f"[Scraper] ✓ FOUND MATCH!")
                            logger.info(f"[Scraper]   Card text: {card_title}")
                            logger.info(f"[Scraper]   Href: {href}")

                            # Extrai IDs da URL: /movie/category/XXX/YYYY/info
                            match = re.search(r"/category/(\d+)/(\d+)/info", href)
                            if match:
                                category_id = match.group(1)
                                movie_id = match.group(2)

                                logger.info(f"[Scraper]   Category ID: {category_id}")
                                logger.info(f"[Scraper]   Movie ID: {movie_id}")

                                return {
                                    "found": True,
                                    "title": card_title,
                                    "detail_url": href,
                                    "movie_id": movie_id,
                                    "category_id": category_id,
                                }
                except Exception as e:
                    continue

            # Se não achou, scrolla para baixo e tenta novamente
            if attempt < 2:
                logger.info("[Scraper] Movie not found, scrolling down...")
                self.page.mouse.wheel(0, 800)
                time.sleep(2)

        logger.warning(
            f"[Scraper] ✗ Movie not found after scrolling: {movie_data['title']}"
        )
        return {"found": False}

    def extract_video_from_play_page(self, category_id, movie_id, expected_title):
        """
        Navega para a página de play e extrai o URL do vídeo MP4
        Fluxo: /movie/category/{cat}/{id}/info/ → /movie/category/{cat}/{id}/play/
        """
        try:
            # Monta URL da página de play
            play_url = f"{self.base_url}movie/category/{category_id}/{movie_id}/play/"
            logger.info(f"[Scraper] Navigating to PLAY page: {play_url}")

            # Navega para play (mesma aba!)
            self.page.goto(play_url, timeout=30000)
            self.page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)

            # Verifica se a página carregou corretamente (título do filme)
            try:
                # Procura o título na página
                title_found = False
                for search_name in [expected_title]:
                    try:
                        short_name = search_name[:15]  # Primeiros 15 chars
                        self.page.wait_for_selector(f"text={short_name}", timeout=5000)
                        title_found = True
                        logger.info(
                            f"[Scraper] ✓ Page loaded correctly (title found: {short_name})"
                        )
                        break
                    except:
                        continue

                if not title_found:
                    logger.warning(
                        "[Scraper] ⚠ Title not found on page, but continuing..."
                    )
            except:
                pass

            # Extrai o vídeo
            logger.info("[Scraper] Extracting video source...")
            video_url = None

            # Espera pelo elemento video
            try:
                self.page.wait_for_selector("video", timeout=20000)
                logger.info("[Scraper] ✓ Video element found")
            except:
                logger.warning("[Scraper] ⚠ Video element not found immediately")

            # Tenta extrair o src várias vezes (pode demorar para carregar)
            for attempt in range(15):
                # Tenta pegar src do video tag
                video_url = self.page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        if (video && video.src) return video.src;
                        
                        // Tenta encontrar source tags dentro do video
                        const sources = video ? video.querySelectorAll('source') : [];
                        for (let src of sources) {
                            if (src.src && src.src.includes('.mp4')) return src.src;
                        }
                        
                        return null;
                    }
                """)

                if video_url and video_url.startswith("http") and ".mp4" in video_url:
                    logger.info(f"[Scraper] ✓ MP4 FOUND on attempt {attempt + 1}!")
                    logger.info(f"[Scraper]   URL: {video_url[:80]}...")
                    return video_url

                # Se não achou, tenta forçar play e esperar
                if attempt == 5:
                    logger.info("[Scraper] Trying to force play...")
                    self.page.evaluate("""
                        () => {
                            const video = document.querySelector('video');
                            if (video) {
                                video.play().catch(() => {});
                            }
                        }
                    """)

                time.sleep(1)

            # Se chegou aqui, não achou MP4
            logger.warning("[Scraper] ✗ No MP4 found after 15 attempts")
            return None

        except Exception as e:
            logger.error(f"[Scraper] Error extracting video: {e}")
            return None

    def scrape_movie(self, movie_data):
        """
        Scraping completo de um filme:
        1. Encontra na lista
        2. Extrai ID
        3. Vai para play
        4. Extrai MP4
        5. Salva no banco
        """
        logger.info(f"\n{'#' * 60}")
        logger.info(f"[Scraper] STARTING: {movie_data['title']}")
        logger.info(f"{'#' * 60}\n")

        # Passo 1: Encontra na lista
        result = self.find_movie_in_list(movie_data)

        if not result["found"]:
            logger.error(
                f"[Scraper] ✗ FAILED to find {movie_data['title']} in movie list"
            )
            return False

        # Passo 2: Extrai vídeo da página de play
        video_url = self.extract_video_from_play_page(
            result["category_id"], result["movie_id"], result["title"]
        )

        if not video_url:
            logger.error(
                f"[Scraper] ✗ FAILED to extract video for {movie_data['title']}"
            )
            return False

        # Passo 3: Salva no banco de dados
        try:
            logger.info(f"[Scraper] Saving to database...")
            save_embed(
                title=movie_data["title"],
                embed_url=video_url,
                tmdb_id=movie_data["tmdb_id"],
                original_raw_title=result["title"],
            )
            logger.info(f"[Scraper] ✓ SAVED to database!")
            return True
        except Exception as e:
            logger.error(f"[Scraper] Error saving to database: {e}")
            return False

    def run(self):
        """Executa scraping dos 3 filmes"""
        logger.info("\n" + "=" * 60)
        logger.info("THREE CLASSICS SCRAPER - Starting...")
        logger.info("=" * 60)
        logger.info("\nTarget movies:")
        for i, movie in enumerate(TARGET_MOVIES, 1):
            logger.info(f"  {i}. {movie['title']} (TMDB: {movie['tmdb_id']})")
        logger.info("")

        # Inicia sessão
        if not self.start_session(
            headless=False
        ):  # False para debug, mudar para True depois
            logger.error("[Scraper] Failed to start session!")
            return

        results = {}

        try:
            # Scrape cada filme
            for movie in TARGET_MOVIES:
                success = self.scrape_movie(movie)
                results[movie["title"]] = success

                # Volta para a lista de filmes (mesma aba!)
                if movie != TARGET_MOVIES[-1]:  # Se não for o último
                    logger.info("\n[Scraper] Returning to movies list...")
                    movies_url = f"{self.base_url}movie/"
                    self.page.goto(movies_url, timeout=30000)
                    time.sleep(2)

        except Exception as e:
            logger.error(f"[Scraper] Fatal error: {e}")
        finally:
            self.stop_session()

        # Resumo
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING COMPLETE - Summary:")
        logger.info("=" * 60)
        for title, success in results.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            logger.info(f"  {status}: {title}")
        logger.info("=" * 60 + "\n")

        return results


if __name__ == "__main__":
    scraper = ThreeMoviesScraper()
    scraper.run()
