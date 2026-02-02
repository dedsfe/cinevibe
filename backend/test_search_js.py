#!/usr/bin/env python3
"""
Teste manual da busca no Opera com JavaScript click
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://web.operatopzera.net/#/"


def test_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        print("1️⃣ Navegando para home...")
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # Login
        try:
            if page.locator("input[name='username']").is_visible(timeout=5000):
                print("2️⃣ Fazendo login...")
                page.fill("input[name='username']", "t2TGgarYJ")
                page.fill("input[name='password']", "66e74xKRJ")
                page.click("button:has-text('Login')")
                page.wait_for_url("**/#/", timeout=30000)
                time.sleep(2)
        except:
            pass

        print(f"3️⃣ URL após login: {page.url}")

        # Navigate to movie catalog first
        print("4️⃣ Navegando para catálogo...")
        page.goto(f"{BASE_URL}movie/", timeout=30000)
        time.sleep(3)
        print(f"5️⃣ URL no catálogo: {page.url}")

        # Click SEARCH button using JavaScript
        print("6️⃣ Clicando no botão SEARCH via JavaScript...")
        try:
            # Use JavaScript to find and click the button
            clicked = page.evaluate("""() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const searchBtn = buttons.find(btn => btn.textContent.trim() === 'SEARCH');
                if (searchBtn) {
                    searchBtn.click();
                    return true;
                }
                return false;
            }""")

            if clicked:
                print("✅ Botão clicado via JavaScript!")
                time.sleep(3)
                print(f"7️⃣ URL após clique: {page.url}")
            else:
                print("❌ Botão não encontrado via JavaScript")
                browser.close()
                return
        except Exception as e:
            print(f"❌ Erro ao clicar: {e}")
            browser.close()
            return

        # Look for search input
        print("8️⃣ Procurando campo de busca...")
        search_input = page.locator("input[placeholder='Search stream...']")
        if search_input.is_visible(timeout=5000):
            print("✅ Campo de busca encontrado!")

            # Try searching for each movie
            movies = ["96 Minutos", "A Guerra dos Mundos", "A Lista de Schindler"]

            for movie in movies:
                print(f"\n🔍 Buscando: {movie}")
                search_input.fill("")
                time.sleep(0.5)
                search_input.fill(movie)
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(3)

                # Check for results
                cards = page.locator(
                    "a[href*='/movie/category/'][href*='/info/']"
                ).all()
                print(f"   🎬 {len(cards)} filmes encontrados")
                for card in cards[:2]:
                    try:
                        text = card.inner_text().strip().split("\n")[0]
                        print(f"      - {text}")
                    except:
                        pass

                if cards:
                    # Click first result
                    print("   👆 Clicando no primeiro resultado...")
                    cards[0].click()
                    time.sleep(2)

                    # Navigate to play page
                    current_url = page.url
                    play_url = current_url.replace("/info/", "/play/")
                    print(f"   🎥 Navegando para: {play_url}")
                    page.goto(play_url)
                    time.sleep(3)

                    # Extract video URL
                    video_url = None
                    for attempt in range(10):
                        src = page.evaluate("""
                            () => {
                                const video = document.querySelector('video');
                                return video ? video.src : null;
                            }
                        """)
                        if src and src.startswith("http") and ".mp4" in src:
                            video_url = src
                            break
                        time.sleep(1)

                    if video_url:
                        print(f"   ✅ MP4 encontrado: {video_url[:80]}...")
                    else:
                        print("   ❌ MP4 não encontrado")

                    # Go back to search
                    print("   🔙 Voltando para busca...")
                    page.goto(f"{BASE_URL}movie/search/")
                    time.sleep(2)
                    search_input = page.locator("input[placeholder='Search stream...']")

        else:
            print("❌ Campo de busca não encontrado!")
            # Debug: show all inputs
            inputs = page.locator("input").all()
            print(f"📋 Total de inputs na página: {len(inputs)}")
            for i, inp in enumerate(inputs):
                try:
                    ph = inp.get_attribute("placeholder") or "N/A"
                    print(f"   Input {i}: placeholder='{ph}'")
                except:
                    pass

        print("\n✅ Teste concluído!")
        time.sleep(3)
        browser.close()


if __name__ == "__main__":
    test_search()
