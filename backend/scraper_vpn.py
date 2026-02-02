"""
Scraper contínuo com VPN/Proxy - adiciona filmes usando IPs diferentes
Roda lotes de 10 filmes com pausas de 30 segundos e muda de IP periodicamente
"""

import logging
import re
import time
import sys
import os
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_embed, get_conn, get_catalog_movies

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TARGET_MOVIES = 200  # Meta: 200 filmes

# Lista de proxies VPN (você precisa substituir pelos seus)
# Formato: "protocol://user:pass@host:port" ou "protocol://host:port"
PROXY_LIST = [
    None,  # Primeiro lote sem VPN (IP local)
    # Adicione seus proxies VPN aqui:
    # "http://user:pass@proxy1.com:8080",
    # "http://user:pass@proxy2.com:8080",
    # "socks5://proxy3.com:1080",
]

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


def check_movie_exists_in_db(movie_id):
    """Verifica se o filme já existe no banco pelo Opera ID"""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT title FROM links WHERE embed_url LIKE ?", (f"%/{movie_id}.mp4%",)
        )
        result = c.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking DB: {e}")
        return False


def is_low_quality(title):
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in LOW_QUALITY_KEYWORDS)


def get_db_stats():
    """Retorna estatísticas do banco"""
    try:
        movies = get_catalog_movies(limit=1000)
        return len(movies)
    except:
        return 0


def get_current_proxy(batch_number):
    """Retorna o proxy para o lote atual (rotaciona pela lista)"""
    if len(PROXY_LIST) <= 1:
        return None

    # Rotaciona pelos proxies disponíveis
    proxy_index = batch_number % len(PROXY_LIST)
    return PROXY_LIST[proxy_index]


def create_browser_context(p, proxy=None):
    """Cria um contexto de browser com ou sem proxy"""
    browser = p.chromium.launch(headless=True)

    context_options = {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "viewport": {"width": 1920, "height": 1080},
    }

    if proxy:
        context_options["proxy"] = {"server": proxy}
        logger.info(f"🌐 Using proxy: {proxy}")
    else:
        logger.info("🌐 Using local IP (no proxy)")

    context = browser.new_context(**context_options)
    return browser, context


def scrape_batch(p, max_movies=10, proxy=None, initial_scroll=0):
    """Processa um lote de filmes com ou sem proxy"""
    browser, context = create_browser_context(p, proxy)
    page = context.new_page()

    try:
        # Login
        logger.info("Navigating to home...")
        page.goto("http://web.operatopzera.net/#/", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)
        time.sleep(2)

        try:
            if page.locator("input[name='username']").is_visible(timeout=5000):
                logger.info("Logging in...")
                page.fill("input[name='username']", "t2TGgarYJ")
                page.fill("input[name='password']", "66e74xKRJ")
                page.click("button:has-text('Login')")
                page.wait_for_url("**/#/", timeout=30000)
                time.sleep(2)
                logger.info("Logged in!")
        except:
            logger.info("Already logged in")

        # Go to movies
        logger.info("Going to movies page...")
        page.goto("http://web.operatopzera.net/#/movie/", timeout=30000)
        time.sleep(3)

        results = []
        processed_ids = set()
        scroll_count = initial_scroll
        errors_count = 0

        # Scroll inicial para posição correta
        if initial_scroll > 0:
            logger.info(f"Initial scroll to position {initial_scroll}...")
            for _ in range(initial_scroll):
                page.mouse.wheel(0, 800)
                time.sleep(0.5)
            time.sleep(2)

        while (
            len(results) < max_movies
            and scroll_count < (initial_scroll + 30)
            and errors_count < 3
        ):
            logger.info(f"\n📄 Scanning page (scroll {scroll_count + 1})...")

            try:
                cards = page.locator(
                    "a[href*='/movie/category/'][href*='/info/']"
                ).all()
                logger.info(f"Found {len(cards)} cards")

                if len(cards) == 0:
                    logger.warning("No cards found, scrolling more...")
                    page.mouse.wheel(0, 1000)
                    time.sleep(2)
                    scroll_count += 1
                    continue

                for card in cards:
                    if len(results) >= max_movies:
                        break

                    try:
                        href = card.get_attribute("href")
                        if not href:
                            continue
                        text = card.inner_text().strip()
                        title = text.split("\n")[0].strip()

                        match = re.search(r"/category/(\d+)/(\d+)/info", href)
                        if not match:
                            continue

                        category_id = match.group(1)
                        movie_id = match.group(2)

                        if movie_id in processed_ids:
                            continue
                        processed_ids.add(movie_id)

                        if check_movie_exists_in_db(movie_id):
                            logger.info(
                                f"⏭️  SKIP (already in DB): {title} (ID: {movie_id})"
                            )
                            continue

                        if is_low_quality(title):
                            logger.info(f"⏭️  SKIP (low quality): {title}")
                            continue

                        logger.info(f"\n🎬 Processing: {title} (ID: {movie_id})")

                        play_url = f"http://web.operatopzera.net/#/movie/category/{category_id}/{movie_id}/play/"
                        page.goto(play_url, timeout=15000)
                        time.sleep(2)

                        video_url = None
                        for _ in range(8):
                            video_url = page.evaluate(
                                """
                                () => {
                                    const video = document.querySelector('video');
                                    if (video && video.src && video.src.includes('.mp4')) return video.src;
                                    const sources = video ? video.querySelectorAll('source') : [];
                                    for (let src of sources) {
                                        if (src.src && src.src.includes('.mp4')) return src.src;
                                    }
                                    const iframe = document.querySelector('iframe');
                                    if (iframe && iframe.src) return iframe.src;
                                    return null;
                                }
                            """
                            )
                            if video_url:
                                break
                            time.sleep(1)

                        if video_url:
                            try:
                                save_embed(
                                    title=title,
                                    embed_url=video_url,
                                    tmdb_id=None,
                                    original_raw_title=title,
                                )
                                logger.info(f"✅ SAVED: {title}")
                                results.append(
                                    {
                                        "title": title,
                                        "movie_id": movie_id,
                                        "success": True,
                                    }
                                )
                            except Exception as e:
                                logger.error(f"❌ DB error: {e}")
                                errors_count += 1
                        else:
                            logger.warning(f"⚠️  No MP4: {title}")

                        if len(results) < max_movies:
                            page.goto(
                                "http://web.operatopzera.net/#/movie/", timeout=15000
                            )
                            time.sleep(2)
                            # Re-scroll to position
                            if scroll_count > 0:
                                for _ in range(scroll_count):
                                    page.mouse.wheel(0, 800)
                                    time.sleep(0.3)
                            break

                    except Exception as e:
                        logger.error(f"Error processing card: {e}")
                        errors_count += 1
                        if errors_count >= 3:
                            logger.error("Too many errors, stopping batch")
                            break

                if len(results) < max_movies:
                    logger.info("Scrolling for more...")
                    page.mouse.wheel(0, 800)
                    time.sleep(2)
                    scroll_count += 1

            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                errors_count += 1
                if errors_count >= 3:
                    break

        return results

    finally:
        page.close()
        context.close()
        browser.close()


def run_continuous_scraper_with_vpn():
    """Roda o scraper com VPN rotacionando até atingir TARGET_MOVIES"""
    logger.info("\n" + "=" * 60)
    logger.info("🔄 VPN SCRAPER STARTED")
    logger.info("=" * 60)
    logger.info(f"🎯 TARGET: {TARGET_MOVIES} movies")
    logger.info("🌐 VPN Mode: Rotating IPs every batch")
    logger.info(f"📋 Available proxies: {len(PROXY_LIST)}")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60 + "\n")

    if len(PROXY_LIST) <= 1:
        logger.warning("⚠️  No VPN proxies configured! Add proxies to PROXY_LIST")
        logger.info("Continuing with local IP only...\n")

    batch_count = 0
    total_added = 0

    with sync_playwright() as p:
        try:
            while True:
                batch_count += 1
                current_total = get_db_stats()

                if current_total >= TARGET_MOVIES:
                    logger.info(f"\n{'=' * 60}")
                    logger.info(f"🎉 TARGET REACHED! {current_total} movies in DB!")
                    logger.info(f"{'=' * 60}")
                    break

                # Seleciona proxy para este lote
                proxy = get_current_proxy(batch_count)

                logger.info(f"\n{'=' * 60}")
                logger.info(
                    f"📦 BATCH #{batch_count} - Current: {current_total}/{TARGET_MOVIES} movies"
                )
                if proxy:
                    logger.info(f"🌐 Using VPN: {proxy}")
                else:
                    logger.info("🌐 No VPN (local IP)")
                logger.info(f"{'=' * 60}")

                start_time = time.time()
                results = scrape_batch(p, max_movies=10, proxy=proxy)
                elapsed = time.time() - start_time

                added_in_batch = len(results)
                total_added += added_in_batch

                new_total = get_db_stats()

                logger.info(f"\n✅ Batch #{batch_count} complete:")
                logger.info(f"   Added this batch: {added_in_batch}")
                logger.info(f"   Total added: {total_added}")
                logger.info(f"   DB total: {new_total} movies")
                logger.info(f"   Time: {elapsed:.1f}s")

                if added_in_batch == 0:
                    logger.warning("⚠️  No new movies added in this batch")

                for r in results:
                    logger.info(f"   ✓ {r['title']}")

                # Pausa antes do próximo lote
                logger.info(f"\n⏳ Pausing 30 seconds before next batch...")
                logger.info(
                    f"   (Next proxy: {get_current_proxy(batch_count + 1) or 'local IP'})"
                )
                logger.info(f"   (Ctrl+C to stop)")
                time.sleep(30)

        except KeyboardInterrupt:
            logger.info("\n\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"\n💥 Fatal error: {e}")

        final_count = get_db_stats()
        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Batches completed: {batch_count}")
        logger.info(f"Total movies added: {total_added}")
        logger.info(f"Final DB count: {final_count}")
        logger.info("=" * 60)


if __name__ == "__main__":
    run_continuous_scraper_with_vpn()
