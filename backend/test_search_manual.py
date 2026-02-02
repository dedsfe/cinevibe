#!/usr/bin/env python3
"""
Teste manual da busca no Opera
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

        # Click SEARCH button
        print("6️⃣ Procurando botão SEARCH...")
        search_btn = page.locator("button:has-text('SEARCH')")
        if search_btn.is_visible(timeout=5000):
            print("7️⃣ Botão encontrado! Clicando (com force=True)...")
            # Use force=True to click even if outside viewport
            search_btn.click(force=True)
            time.sleep(3)
            print(f"8️⃣ URL após clique: {page.url}")
        else:
            print("❌ Botão SEARCH não encontrado!")
            browser.close()
            return

        # Look for search input
        print("9️⃣ Procurando campo de busca...")
        search_input = page.locator("input[placeholder='Search stream...']")
        if search_input.is_visible(timeout=5000):
            print("✅ Campo de busca encontrado!")

            # Try searching
            print("🔍 Digitando '96 Minutos'...")
            search_input.fill("")
            time.sleep(0.5)
            search_input.fill("96 Minutos")
            time.sleep(0.5)
            page.keyboard.press("Enter")
            time.sleep(3)

            print(f"⏹️  URL final: {page.url}")

            # Check for results
            cards = page.locator("a[href*='/movie/category/'][href*='/info/']").all()
            print(f"🎬 {len(cards)} filmes encontrados")
            for card in cards[:3]:
                try:
                    text = card.inner_text().strip().split("\n")[0]
                    print(f"   - {text}")
                except:
                    pass
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
        time.sleep(5)  # Keep browser open to see result
        browser.close()


if __name__ == "__main__":
    test_search()
