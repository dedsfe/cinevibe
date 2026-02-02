"""
Scraper simples para adicionar MP4 - verifica DB antes de processar
"""

import logging
import re
import time
import sys
import os
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_embed, get_conn

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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


def scrape_movies(max_movies=15):
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Scraping {max_movies} movies - Checking DB first!")
    logger.info(f"{'=' * 60}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

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
        time.sleep(3)  # Wait for content

        results = []
        processed_ids = set()
        scroll_count = 0

        while len(results) < max_movies and scroll_count < 20:
            logger.info(f"\nScanning page (scroll {scroll_count + 1})...")

            # Get all cards
            cards = page.locator("a[href*='/movie/category/'][href*='/info/']").all()
            logger.info(f"Found {len(cards)} cards")

            for card in cards:
                if len(results) >= max_movies:
                    break

                try:
                    href = card.get_attribute("href")
                    if not href:
                        continue
                    text = card.inner_text().strip()
                    title = text.split("\n")[0].strip()

                    # Extract ID
                    match = re.search(r"/category/(\d+)/(\d+)/info", href)
                    if not match:
                        continue

                    category_id = match.group(1)
                    movie_id = match.group(2)

                    # Skip if already processed
                    if movie_id in processed_ids:
                        continue
                    processed_ids.add(movie_id)

                    # ✅ CHECK DATABASE FIRST
                    if check_movie_exists_in_db(movie_id):
                        logger.info(
                            f"⏭️  SKIP (already in DB): {title} (ID: {movie_id})"
                        )
                        continue

                    # Skip low quality
                    if is_low_quality(title):
                        logger.info(f"⏭️  SKIP (low quality): {title}")
                        continue

                    logger.info(f"\n{'#' * 60}")
                    logger.info(f"Movie {len(results) + 1}/{max_movies}: {title}")
                    logger.info(f"ID: {movie_id}")
                    logger.info(f"{'#' * 60}")

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
                                {"title": title, "movie_id": movie_id, "success": True}
                            )
                        except Exception as e:
                            logger.error(f"❌ DB error: {e}")
                            raise
                    else:
                        logger.error(f"❌ No MP4: {title}")
                        logger.error("🛑 STOPPING - Error detected!")
                        raise Exception(f"No MP4 for {title}")

                    # Return to list
                    if len(results) < max_movies:
                        logger.info("Returning to list...")
                        page.goto("http://web.operatopzera.net/#/movie/", timeout=15000)
                        time.sleep(2)
                        break  # Re-fetch cards after navigation

                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise

            # Scroll for more
            if len(results) < max_movies:
                logger.info("Scrolling for more...")
                page.mouse.wheel(0, 800)
                time.sleep(2)
                scroll_count += 1

        browser.close()

        # Summary
        logger.info(f"\n{'=' * 60}")
        logger.info("SCRAPING COMPLETE")
        logger.info(f"{'=' * 60}")
        logger.info(f"Total: {len(results)} movies")
        for r in results:
            logger.info(f"  ✅ {r['title']}")
        logger.info(f"{'=' * 60}")

        return results


if __name__ == "__main__":
    scrape_movies(max_movies=15)
