import sys
sys.path.insert(0, '.')
from opera_catalog_browser import OperaCatalogBrowser
import time

browser = OperaCatalogBrowser()
print('🚀 Starting browser...')
if browser.start_session(headless=False):
    print('✅ Browser started!')
    print(f'Current URL: {browser.page.url}')
    
    # Test search
    result = browser.search_and_extract("96 Minutos")
    print(f'\nResult: {result}')
    
    browser.stop_session()
    print('\n✅ Done!')
else:
    print('❌ Failed to start browser')
