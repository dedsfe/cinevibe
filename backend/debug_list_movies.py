"""
Debug script to list all movies visible on /movie/ page
"""

from playwright.sync_api import sync_playwright
import time
import re


def list_all_movies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        # Login
        print("Logging in...")
        page.goto("http://web.operatopzera.net/#/", timeout=60000)
        page.wait_for_load_state("networkidle", timeout=60000)
        time.sleep(2)

        try:
            if page.locator("input[name='username']").is_visible(timeout=5000):
                page.fill("input[name='username']", "t2TGgarYJ")
                page.fill("input[name='password']", "66e74xKRJ")
                page.click("button:has-text('Login')")
                page.wait_for_url("**/#/", timeout=30000)
                time.sleep(2)
                print("Logged in!")
        except:
            print("Already logged in")

        # Go to movies page
        print("\nGoing to movies page...")
        page.goto("http://web.operatopzera.net/#/movie/", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3)

        print(f"Current URL: {page.url}")
        print(f"Page title: {page.title()}")

        # Extract all movie cards
        all_movies = []

        # Scroll and collect movies (max 10 scrolls)
        for scroll in range(10):
            cards = page.locator("a[href*='/movie/category/'][href*='/info/']").all()
            print(f"\nScroll {scroll + 1}: Found {len(cards)} cards")

            for i, card in enumerate(cards):
                try:
                    href = card.get_attribute("href")
                    text = card.inner_text().strip()
                    title = text.split("\n")[0].strip()

                    # Extract IDs
                    match = re.search(r"/category/(\d+)/(\d+)/info", href)
                    if match:
                        cat_id = match.group(1)
                        movie_id = match.group(2)

                        movie_data = {
                            "title": title,
                            "href": href,
                            "category_id": cat_id,
                            "movie_id": movie_id,
                        }

                        # Add if not duplicate
                        if movie_data not in all_movies:
                            all_movies.append(movie_data)

                except Exception as e:
                    continue

            # Scroll down
            page.mouse.wheel(0, 1000)
            time.sleep(2)

        browser.close()

        # Print results
        print(f"\n{'=' * 80}")
        print(f"TOTAL UNIQUE MOVIES FOUND: {len(all_movies)}")
        print(f"{'=' * 80}\n")

        # Look for our target movies
        targets = [
            "Poderoso Chefão",
            "Godfather",
            "Schindler",
            "Shawshank",
            "Liberdade",
        ]
        found_targets = []

        for i, movie in enumerate(all_movies, 1):
            print(f"{i:3d}. {movie['title'][:60]:<60} | ID: {movie['movie_id']}")

            # Check if it's a target
            for target in targets:
                if target.lower() in movie["title"].lower():
                    found_targets.append((target, movie))

        print(f"\n{'=' * 80}")
        print("TARGET MOVIES FOUND:")
        print(f"{'=' * 80}")
        if found_targets:
            for target, movie in found_targets:
                print(f"✓ {target} -> {movie['title']} (ID: {movie['movie_id']})")
        else:
            print("✗ None of the target movies were found in the list")
            print("\nPossible reasons:")
            print("1. Movies are not in the current catalog")
            print("2. Movies have different names")
            print("3. Need to check different category/page")


if __name__ == "__main__":
    list_all_movies()
