#!/usr/bin/env python3
"""
Test script to diagnose Opera Topzera search field issue
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from opera_catalog_browser import OperaCatalogBrowser
import time

browser = OperaCatalogBrowser()
print("🚀 Iniciando navegador em modo visível...")
if browser.start_session(headless=False):
    print("✅ Navegador iniciado!")
    print("🌐 URL atual:", browser.page.url)

    # Tenta navegar para a página de busca
    search_url = "http://web.operatopzera.net/#/movie/search/"
    print(f"🔍 Navegando para: {search_url}")
    browser.page.goto(search_url, timeout=15000)
    time.sleep(3)

    print(f"📍 URL atual: {browser.page.url}")

    # Verifica se o campo de busca existe
    try:
        search_input = browser.page.locator("input[placeholder='Search stream...']")
        is_visible = search_input.is_visible(timeout=5000)
        print(f"🔍 Campo de busca visível: {is_visible}")

        # Tenta encontrar todos os inputs
        inputs = browser.page.locator("input").all()
        print(f"📋 Total de inputs encontrados: {len(inputs)}")
        for i, inp in enumerate(inputs[:5]):
            try:
                placeholder = inp.get_attribute("placeholder") or "N/A"
                input_type = inp.get_attribute("type") or "N/A"
                print(f'   Input {i}: placeholder="{placeholder}", type="{input_type}"')
            except Exception as e:
                print(f"   Input {i}: [erro: {e}]")

    except Exception as e:
        print(f"❌ Erro ao verificar campo: {e}")
        import traceback

        traceback.print_exc()

    # Print page content for debugging
    try:
        print("\n📄 HTML da página (primeiros 500 caracteres):")
        html = browser.page.content()
        print(html[:500])
    except Exception as e:
        print(f"❌ Erro ao obter HTML: {e}")

    browser.stop_session()
    print("\n✅ Teste concluído")
else:
    print("❌ Falha ao iniciar navegador")
