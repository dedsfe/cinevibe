#!/usr/bin/env python3
"""
Teste manual da busca no Opera - v2 com melhor detecção
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

        # Navigate directly to search page with reload
        print("4️⃣ Navegando direto para página de busca...")
        page.goto(f"{BASE_URL}movie/search/", timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        print(f"5️⃣ URL: {page.url}")

        # Check if search input is there
        print("6️⃣ Verificando campo de busca...")
        search_input = page.locator("input[placeholder='Search stream...']")

        try:
            is_visible = search_input.is_visible(timeout=5000)
            print(f"   Visível: {is_visible}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            is_visible = False

        if is_visible:
            print("✅ Campo de busca encontrado!")

            # Test search
            print("\n🔍 Testando busca por '96 Minutos'...")
            search_input.fill("96 Minutos")
            time.sleep(0.5)
            page.keyboard.press("Enter")
            time.sleep(3)

            # Check results
            cards = page.locator("a[href*='/movie/category/'][href*='/info/']").all()
            print(f"   🎬 {len(cards)} resultados")

            for card in cards[:2]:
                try:
                    text = card.inner_text().strip().split("\n")[0]
                    print(f"      - {text}")
                except:
                    pass

            if cards:
                print("\n✅ Busca funcionando!")
        else:
            print("❌ Campo de busca não encontrado")
            print("\n📋 Debug - elementos na página:")

            # List all inputs
            inputs = page.locator("input").all()
            print(f"   Inputs encontrados: {len(inputs)}")
            for i, inp in enumerate(inputs):
                try:
                    ph = inp.get_attribute("placeholder") or "N/A"
                    visible = inp.is_visible()
                    print(f"      [{i}] placeholder='{ph}', visible={visible}")
                except Exception as e:
                    print(f"      [{i}] Erro: {e}")

        print("\n✅ Teste concluído")
        time.sleep(3)
        browser.close()


if __name__ == "__main__":
    test_search()
