"""
Scraper contínuo #2 - roda em paralelo, começa de posição diferente
Adiciona filmes em loop infinito a partir de uma posição diferente na lista
"""

import logging
import re
import time
import sys
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_embed, get_conn, get_catalog_movies

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Meta total de filmes
TARGET_MOVIES = 250

# SCROLL INICIAL - posiciona em filmes diferentes do scraper #1
# Scraper #1 começa do início, este começa depois de N scrolls
INITIAL_SCROLL_COUNT = 50

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


def scrape_batch(browser_context, max_movies=10):
    """Processa um lote de filmes"""
    page = browser_context.new_page()

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

        # SCROLL INICIAL - posiciona em filmes diferentes
        logger.info(
            f"🔄 Initial scroll: {INITIAL_SCROLL_COUNT} times to reach different movies..."
        )
        for i in range(INITIAL_SCROLL_COUNT):
            page.mouse.wheel(0, 800)
            time.sleep(0.5)
            if (i + 1) % 10 == 0:
                logger.info(f"   Scrolled {i + 1}/{INITIAL_SCROLL_COUNT}")
        logger.info(f"✅ Initial scroll complete! Now at different position in list.")
        time.sleep(2)

        results = []
        processed_ids = set()
        scroll_count = 0
        errors_count = 0

        while len(results) < max_movies and scroll_count < 30 and errors_count < 3:
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

                        # Check DB
                        if check_movie_exists_in_db(movie_id):
                            logger.info(
                                f"⏭️  SKIP (already in DB): {title} (ID: {movie_id})"
                            )
                            continue

                        if is_low_quality(title):
                            logger.info(f"⏭️  SKIP (low quality): {title}")
                            continue

                        logger.info(f"\n🎬 Processing: {title} (ID: {movie_id})")

                        # Go to play page
                        play_url = f"http://web.operatopzera.net/#/movie/category/{category_id}/{movie_id}/play/"
                        page.goto(play_url, timeout=15000)
                        time.sleep(2)

                        # Extract video
                        video_url = None
                        for _ in range(8):
                            video_url = page.evaluate("""
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
                            """)
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

                        # Return to list
                        if len(results) < max_movies:
                            page.goto(
                                "http://web.operatopzera.net/#/movie/", timeout=15000
                            )
                            time.sleep(2)
                            # SCROLL INICIAL ao retornar - mantém posição diferente
                            for _ in range(INITIAL_SCROLL_COUNT + scroll_count):
                                page.mouse.wheel(0, 800)
                                time.sleep(0.3)
                            time.sleep(1)
                            break  # Re-fetch cards

                    except Exception as e:
                        logger.error(f"Error processing card: {e}")
                        errors_count += 1
                        if errors_count >= 3:
                            logger.error("Too many errors, stopping batch")
                            break

                # Scroll for more
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


def run_continuous_scraper():
    """Roda o scraper até atingir TARGET_MOVIES"""
    logger.info("\n" + "=" * 60)
    logger.info("🔄 CONTINUOUS SCRAPER #2 STARTED (PARALLEL MODE)")
    logger.info("=" * 60)
    logger.info(f"🎯 TARGET: {TARGET_MOVIES} movies")
    logger.info(f"📍 Initial scroll: {INITIAL_SCROLL_COUNT} (different position)")
    logger.info("Mode: Process 10 movies per batch, 30s pause between batches")
    logger.info("This scraper works on DIFFERENT movies than scraper #1")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60 + "\n")

    batch_count = 0
    total_added = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        try:
            while True:
                batch_count += 1
                current_total = get_db_stats()

                # Verifica se atingiu a meta
                if current_total >= TARGET_MOVIES:
                    logger.info(f"\n{'=' * 60}")
                    logger.info(f"🎉 TARGET REACHED! {current_total} movies in DB!")
                    logger.info(f"{'=' * 60}")
                    break

                logger.info(f"\n{'=' * 60}")
                logger.info(
                    f"📦 BATCH #{batch_count} - Current: {current_total}/{TARGET_MOVIES} movies"
                )
                logger.info(f"{'=' * 60}")

                start_time = time.time()
                results = scrape_batch(context, max_movies=10)
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

                # Show movies added
                for r in results:
                    logger.info(f"   ✓ {r['title']}")

                # Pause before next batch
                logger.info(f"\n⏳ Pausing 30 seconds before next batch...")
                logger.info(f"   (Ctrl+C to stop)")
                time.sleep(30)

        except KeyboardInterrupt:
            logger.info("\n\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"\n💥 Fatal error: {e}")
        finally:
            context.close()
            browser.close()

            final_count = get_db_stats()
            logger.info("\n" + "=" * 60)
            logger.info("📊 FINAL STATISTICS (SCRAPER #2)")
            logger.info("=" * 60)
            logger.info(f"Batches completed: {batch_count}")
            logger.info(f"Total movies added: {total_added}")
            logger.info(f"Final DB count: {final_count}")
            logger.info("=" * 60)


if __name__ == "__main__":
    run_continuous_scraper()
