import sys
import os
import logging
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock database module BEFORE importing scraper
sys.modules['database'] = MagicMock()
sys.modules['database'].save_embed = MagicMock(side_effect=lambda *args, **kwargs: print(f"  [MOCK] Saved embed: {kwargs.get('title', 'Unknown')}"))
sys.modules['database'].get_conn = MagicMock()

# Import scraper functions
from scraper_series_working import discover_series, extract_series_episodes
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def test_series_scraping():
    print("="*60)
    print("TESTING SERIES SCRAPING LOGIC (Dry Run)")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        
        try:
            # 1. Login
            print("\n1. Testing Login...")
            page.goto("http://web.operatopzera.net/#/", timeout=60000)
            if page.locator("input[name='username']").is_visible(timeout=5000):
                page.fill("input[name='username']", "t2TGgarYJ")
                page.fill("input[name='password']", "66e74xKRJ")
                page.click("button:has-text('Login')")
                print("   Login submitted.")
                page.wait_for_url("**/#/", timeout=30000)
                print("   Login successful.")
            else:
                print("   Already logged in or no login required.")
            
            # Wait for any redirects to settle
            print("   Waiting for redirects to settle...")
            import time
            time.sleep(5)
            
            # 2. Discover Series
            print("\n2. Testing Series Discovery (Limit 1)...")
            series_list = discover_series(page, max_series=1)
            
            if not series_list:
                print("   ❌ No series found. Scraper logic might be broken.")
                return
            
            print(f"   ✅ Found {len(series_list)} series.")
            target_series = series_list[0]
            print(f"   Target: {target_series['title']} (ID: {target_series['series_id']})")
            
            # 3. Extract Episodes
            print("\n3. Testing Episode Extraction (1 Season, 1 Episode)...")
            episodes = extract_series_episodes(
                page, target_series, 
                max_seasons=1, 
                max_episodes=1
            )
            
            if episodes:
                print(f"   ✅ Successfully extracted {len(episodes)} episode(s).")
                print(f"   Video URL: {episodes[0]['video_url']}")
            else:
                print("   ❌ Failed to extract episodes.")

        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    test_series_scraping()
