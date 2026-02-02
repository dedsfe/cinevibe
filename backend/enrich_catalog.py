import sqlite3
import os
import requests
import time
from database import get_conn, save_embed

# Reuse TMDB logic or import? Better to import if possible, but bulk_scrape_tmdb has mixed logic.
# Let's simple implementation here for clarity.

TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"
BASE_URL = "https://api.themoviedb.org/3"


def clean_title(title):
    # Remove text like (2014), (Dual), [4K], etc.
    import re

    title = re.sub(r"\(\d{4}\)", "", title)
    title = re.sub(r"\[.*?\]", "", title)
    title = re.sub(r"\(.*?\)", "", title)
    return title.strip()


def search_tmdb(title, year=None):
    try:
        cleaned_title = clean_title(title)
        url = f"{BASE_URL}/search/movie"

        # Try with year first if provided
        params = {
            "api_key": TMDB_API_KEY,
            "query": cleaned_title,
            "language": "pt-BR",
            "page": 1,
        }
        if year:
            params["year"] = year

        res = requests.get(url, params=params)
        data = res.json()

        # If no result with year, try without year
        if not data.get("results") and year:
            del params["year"]
            res = requests.get(url, params=params)
            data = res.json()

        if data.get("results"):
            return data["results"][0]
    except Exception as e:
        print(f"Error searching TMDB: {e}")
    return None


def enrich_catalog():
    conn = get_conn()
    c = conn.cursor()

    # Get unenriched items (those in catalog_raw but not in links??)
    # Or just iterate all and upsert.
    # Get unenriched items (those in catalog_raw but not in links)
    c.execute("""
        SELECT raw_title, detail_url, year 
        FROM catalog_raw 
        WHERE raw_title NOT IN (
            SELECT title FROM links 
            WHERE embed_url IS NOT NULL AND embed_url != 'NOT_FOUND'
        )
    """)
    rows = c.fetchall()

    print(f"Found {len(rows)} new items in catalog to process.")

    # Initialize scraper - USE STRICT VALIDATION SCRAPER
    from strict_opera_scraper import StrictOperaScraper

    scraper = StrictOperaScraper()
    scraper.start_session(headless=True)

    try:
        for row in rows:
            raw_title = row["raw_title"]
            detail_url = row["detail_url"]
            item_year = row["year"]

            # FILTER: Only process actual movie pages (containing /info/)
            if "/info/" not in detail_url:
                print(f"Skipping category/invalid link: {raw_title} ({detail_url})")
                continue

            # OPTIONAL: Filter out likely adult content if desired, or just let TMDB fail to match
            if "XXX" in raw_title:
                print(f"Skipping likely adult content: {raw_title}")
                continue

            # Check if already in links (by title? by tmdb_id? we don't know tmdb_id yet)
            # Check by title to skip processed.
            # ALSO CHECK IF THE LINK IS VALID (not the page url)
            # Check if already in links (by title)
            c.execute(
                "SELECT embed_url, poster_path FROM links WHERE title = ?", (raw_title,)
            )
            existing = c.fetchone()

            should_enrich = True
            if existing:
                embed_url = existing[0]
                poster_path = existing[1]

                # If we have a valid link (not NOT_FOUND) AND a poster, we can skip
                # Assumption: web.operatopzera.net links are legacy/invalid
                if (
                    embed_url != "NOT_FOUND"
                    and poster_path
                    and "web.operatopzera.net" not in embed_url
                ):
                    print(f"Skipping {raw_title} (completed)")
                    should_enrich = False
                elif embed_url == "NOT_FOUND":
                    print(f"Retrying video for {raw_title} (previously not found)...")
                    should_enrich = True
                elif "web.operatopzera.net" in embed_url:
                    print(f"Re-processing {raw_title} (invalid link)...")
                    should_enrich = True
                elif not poster_path:
                    print(f"Enriching metadata for {raw_title} (missing poster)...")
                    should_enrich = True
            else:
                print(f"Enriching new item: {raw_title}...")

            if not should_enrich:
                continue

            # 1. Search TMDB
            tmdb_data = search_tmdb(raw_title, item_year)

            if tmdb_data:
                tmdb_id = str(tmdb_data["id"])
                real_title = tmdb_data["title"]
                poster_path = tmdb_data.get("poster_path")
                backdrop_path = tmdb_data.get("backdrop_path")
                overview = tmdb_data.get("overview")
                release_date = tmdb_data.get("release_date", "")

                # VALIDATION: Check Year and Title Similarity
                # If we have a scraped year, and TMDB has a date, they must be close.
                valid_match = True
                if item_year and release_date:
                    tmdb_year = release_date.split("-")[0]
                    try:
                        diff = abs(int(item_year) - int(tmdb_year))
                        if diff > 1:
                            print(
                                f"  -> REJECTED: Year mismatch. Scraped: {item_year}, TMDB: {tmdb_year}"
                            )
                            valid_match = False
                    except:
                        pass

                # Title check (basic) - prevents "The Pitt" -> "The Steeler..."
                # If the raw title is short, we need exact match or close substring
                if len(raw_title) < 10:
                    if (
                        raw_title.lower() not in real_title.lower()
                        and real_title.lower() not in raw_title.lower()
                    ):
                        print(
                            f"  -> REJECTED: Title mismatch. Raw: {raw_title}, TMDB: {real_title}"
                        )
                        valid_match = False

                if not valid_match:
                    continue

                print(f"  -> Match: {real_title} (ID: {tmdb_id})")

                # IMMEDIATE SAVE: Save metadata so it appears in UI even if video is processing
                save_embed(
                    real_title,
                    "NOT_FOUND",
                    tmdb_id,
                    poster_path,
                    backdrop_path,
                    overview,
                )
                print("  -> Saved metadata (initial NOT_FOUND). checking text...")

                # DECISION: Do we need to scrape video?
                need_video = True
                final_video_url = None

                if existing:
                    current_embed = existing[0]
                    if (
                        "web.operatopzera.net" not in current_embed
                        and current_embed != "NOT_FOUND"
                    ):
                        # Existing link is valid, keep it
                        final_video_url = current_embed
                        need_video = False
                        print("  -> Existing link is valid. Updating metadata only.")

                if need_video:
                    print(f"  -> Fetching video from Opera Topzera for: {raw_title}")
                    # Use strict validation scraper
                    scrape_result = scraper.scrape_with_validation(raw_title, item_year)

                    if scrape_result["success"] and scrape_result["validation_passed"]:
                        final_video_url = scrape_result["video_url"]
                        print(f"  -> ✅ Video Found & Validated!")
                        print(f"  -> Title match: {scrape_result['similarity']:.1%}")
                        print(f"  -> Video ID: {scrape_result['video_id']}")
                    else:
                        print(f"  -> ❌ Failed: {scrape_result['error']}")
                        final_video_url = "NOT_FOUND"

                # Update if we found a video
                if final_video_url and final_video_url != "NOT_FOUND":
                    save_embed(
                        real_title,
                        final_video_url,
                        tmdb_id,
                        poster_path,
                        backdrop_path,
                        overview,
                    )
                    print("  -> Updated with Video URL!")
            else:
                print("  -> No TMDB match found.")

            time.sleep(0.5)

    finally:
        scraper.stop_session()
        conn.close()


if __name__ == "__main__":
    enrich_catalog()
