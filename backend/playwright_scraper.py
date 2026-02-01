import logging
import urllib.parse
import time
from playwright.sync_api import sync_playwright

def scrape_operatopzera(title: str, year: str = None) -> str | None:
    """
    Scrapes the video embed URL from operatopzera.net using Playwright.
    Follows strict navigation: Home -> Movies -> Search -> Type Query.
    Uses 'Title Year' for more precise search if year is provided.
    """
    try:
        with sync_playwright() as p:
            # Launch browser
            # headless=True for production
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # 1. Go to Home Page
            base_url = "http://web.operatopzera.net/#/"
            logging.info(f"Navigating to home: {base_url}")
            page.goto(base_url)
            time.sleep(5) # Wait for check, sometimes it redirects to login

            # Check if we are on login page or need to login
            if page.locator("input[name='username']").is_visible():
                logging.info("Login page detected. Logging in...")
                try:
                    # Credentials
                    USER = "t2TGgarYJ"
                    PASS = "66e74xKRJ"
                    
                    page.fill("input[name='username']", USER)
                    page.fill("input[name='password']", PASS)
                    page.click("button:has-text('Login')")
                    
                    logging.info("Login submitted. Waiting for navigation...")
                    page.wait_for_url("**/#/", timeout=15000) # Should go back to home or dashboard
                    time.sleep(3)
                except Exception as e:
                    logging.error(f"Login failed: {e}")
                    # Save page source for debugging login failure
                    with open("login_fail_dump.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    browser.close()
                    return None

            
            # 2. Go to Movies Page
            movies_url = "http://web.operatopzera.net/#/movie/"
            logging.info(f"Navigating to movies: {movies_url}")
            page.goto(movies_url)
            time.sleep(3)
            
            # 3. Go to Search Page and Type Query
            search_page_url = "http://web.operatopzera.net/#/movie/search/"
            logging.info(f"Navigating to search page: {search_page_url}")
            page.goto(search_page_url)
            
            try:
                # Wait for search input
                INPUT_SELECTOR = "input[placeholder='Search stream...']"
                SUBMIT_SELECTOR = "button[type='submit']"
                
                logging.info(f"Waiting for search input: {INPUT_SELECTOR}")
                page.wait_for_selector(INPUT_SELECTOR, timeout=5000)
                
                # Type query and Click Submit (Enter key is unreliable)
                # Use ONLY title for search (site search might be exact match and fail with year)
                search_query = title
                logging.info(f"Typing query: '{search_query}'")
                
                page.fill(INPUT_SELECTOR, search_query)
                time.sleep(1) # Small delay to ensure input is registered
                
                logging.info(f"Clicking submit button: {SUBMIT_SELECTOR}")
                page.click(SUBMIT_SELECTOR)
                
            except Exception as e:
                logging.error(f"Failed to interact with search bar: {e}")
                browser.close()
                return None
            try:
                # Wait for results to appear
                # Logic: The first 'a' tag inside the results grid often points to the movie
                # We expect a link containing '/movie/category' or similar structure for details/play
                result_selector = 'a[href*="/movie/"]'
                logging.info("Waiting for search results...")
                # Give it time to render results after Enter
                page.wait_for_selector(result_selector, state="visible", timeout=8000)
                
                # Get the first result (Index 0 often might be a nav item, so be careful. 
                # But usually the grid results appear after nav)
                # Let's target links specifically inside a grid/list container if possible, 
                # but 'a[href*="/movie/category"]' or similar is a good bet for a result.
                
                # We can refine this using the user's hint if needed, but 'a[href*="/movie/"]' is standard for their SPA routing
                results = page.locator(result_selector).all()
                target_link = None
                
                # Filter out 'search' or 'category' generics if possible, trying to find a specific movie link
                # Typical pattern: #/movie/category/118/217376/play/ or #/movie/category/118/217376
                # Filter out 'search' or 'category' generics if possible, trying to find a specific movie link
                # Typical pattern: #/movie/category/118/217376/play/ or #/movie/category/118/217376
                for res in results:
                    href = res.get_attribute("href")
                    text_content = res.inner_text().strip().lower()
                    
                    # Capture Image Alt Text (Crucial for Year)
                    img_alt = ""
                    try:
                        img = res.locator("img").first
                        # Even if hidden (width=0), the alt text is valuable for validation
                        img_alt = img.get_attribute("alt") or ""
                    except:
                        pass
                    
                    full_validation_text = f"{text_content} {img_alt.lower()}"

                    if href and "search" not in href and len(href.split("/")) > 4:
                        # Strict Validation
                        title_clean = title.lower()
                        if title_clean in full_validation_text:
                            # Verify Year if provided (Critical for precision)
                            if year and year not in full_validation_text:
                                logging.info(f"Skipping result: '{full_validation_text}' matches title but not year '{year}'")
                                continue

                            logging.info(f"Match found: '{full_validation_text}' matches '{title}'" + (f" and '{year}'" if year else ""))
                            target_link = res
                            break
                        else:
                             logging.info(f"Skipping result: '{full_validation_text}' does not contain '{title}'")

                if not target_link:
                     logging.warning(f"No results matched the title '{title}' strictly.")
                     browser.close()
                     return None

                logging.info(f"Clicking result with href: {target_link.get_attribute('href')}")
                target_link.click()
                
            except Exception as e:
                logging.error(f"Failed to find or click search result: {e}")
                # Save page source for debugging
                with open("page_dump.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                browser.close()
                return None

            # 5. Handle 'Details' vs 'Play' page
            time.sleep(3)
            current_url = page.url
            logging.info(f"Current URL: {current_url}")
            
            if "/play/" not in current_url:
                logging.info("Not on play page, looking for Play/Assistir button...")
                try:
                    # 5.1 VERIFY PAGE CONTENT (especially Year)
                    # If we blindly clicked a candidate, ensure it's the right one
                    if year:
                        page_text = page.inner_text("body").lower()
                        if year not in page_text:
                             logging.warning(f"Year '{year}' not found on details page. Wrong movie selected?")
                             # We could return None here, or rely on user check. 
                             # But sticking to strict validation:
                             browser.close()
                             return None
                             
                    # Try clicking a button that contains "Assistir" or "Play"
                    # Or a link with '/play/'
                    play_link_selector = 'a[href*="/play/"]'
                    if page.is_visible(play_link_selector):
                         page.locator(play_link_selector).first.click()
                    else:
                         # Try generic text match (case insensitive typically handled by get_by_text roughly)
                         page.get_by_text("Assistir").first.click()
                except Exception as e:
                    logging.warning(f"Could not find explicit play button: {e}")
                    # Sometimes you are already on the correct page or just need to click the poster
                    pass
            
            # 6. Extract Video Src
            try:
                logging.info("Waiting for video player...")
                page.wait_for_selector('video', timeout=10000)
                
                # Attempt to play
                page.evaluate("document.querySelector('video').play().catch(e => {})")
                
                # Poll for src
                logging.info("Polling for video.src...")
                for i in range(15):
                    src = page.evaluate("document.querySelector('video').src")
                    if src and src.startswith("http") and "blob" not in src:
                        logging.info(f"Found source: {src}")
                        browser.close()
                        return src
                    time.sleep(1)
                    
                logging.error("Timeout waiting for video src")
                    
            except Exception as e:
                logging.error(f"Error extracting video source: {e}")

            browser.close()
            return None

    except Exception as e:
        logging.error(f"Playwright error: {e}")
        return None
