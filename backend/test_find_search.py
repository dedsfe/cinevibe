import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from opera_catalog_browser import OperaCatalogBrowser
import time

browser = OperaCatalogBrowser()
print('🚀 Iniciando navegador...')
if browser.start_session(headless=False):
    print('✅ Navegador iniciado!')
    print(f'🌐 URL: {browser.page.url}')
    
    # Look for search-related elements
    print('\n🔍 Procurando elementos de busca...')
    
    # Try different selectors
    selectors = [
        "input[placeholder*='Search']",
        "input[placeholder*='search']",
        "input[type='search']",
        "button:has-text('Search')",
        "button:has-text('Busca')",
        "button:has-text('search')",
        "a[href*='search']",
        "[class*='search']",
        "svg[class*='search']",
        "i[class*='search']",
        "button[class*='search']",
        "a[class*='search']",
    ]
    
    for selector in selectors:
        try:
            elements = browser.page.locator(selector).all()
            if elements:
                print(f'✅ {selector}: {len(elements)} encontrado(s)')
                for i, el in enumerate(elements[:2]):
                    try:
                        text = el.inner_text()[:50] if el.is_visible() else '[invisível]'
                        print(f'   [{i}] {text}')
                    except:
                        pass
        except Exception as e:
            pass
    
    # Look for all buttons
    print('\n📋 Todos os botões visíveis:')
    buttons = browser.page.locator('button').all()
    for i, btn in enumerate(buttons):
        try:
            if btn.is_visible():
                text = btn.inner_text().strip()[:50]
                if text:
                    print(f'  Button {i}: "{text}"')
        except:
            pass
    
    # Look for all links
    print('\n🔗 Links com ícones:')
    links = browser.page.locator('a').all()
    for i, link in enumerate(links[:10]):
        try:
            if link.is_visible():
                href = link.get_attribute('href') or ''
                text = link.inner_text().strip()[:30]
                if 'search' in href.lower() or 'search' in text.lower():
                    print(f'  Link {i}: href={href}, text="{text}"')
        except:
            pass
    
    browser.stop_session()
    print('\n✅ Teste concluído')
else:
    print('❌ Falha ao iniciar navegador')
