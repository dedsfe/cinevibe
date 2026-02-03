#!/usr/bin/env python3
"""
Series Scraper v2 - Opera Topzera
Estrutura: Categorias -> Séries -> Episódios
"""

import logging
import re
import time
import sys
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_embed, get_conn

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "http://web.operatopzera.net"


def check_series_exists(series_id):
    """Verifica se série já existe no banco"""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT title FROM links WHERE tmdb_id = ? OR embed_url LIKE ?",
            (str(series_id), f"%series%{series_id}%")
        )
        result = c.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False


def get_categories(page):
    """Obtém lista de categorias de séries"""
    logger.info("📂 Coletando categorias...")
    
    page.goto(f"{BASE_URL}/#/series/", timeout=30000)
    time.sleep(3)
    
    categories = []
    cards = page.locator("a[href*='/series/category/']").all()
    
    for card in cards:
        try:
            href = card.get_attribute("href")
            text = card.inner_text().strip()
            
            if href and "/series/category/" in href:
                # Extrair category_id
                match = re.search(r'/series/category/(\d+)', href)
                if match:
                    cat_id = match.group(1)
                    categories.append({
                        'name': text.split('\n')[0] if text else f"Cat {cat_id}",
                        'id': cat_id,
                        'href': href
                    })
        except:
            pass
    
    logger.info(f"✅ {len(categories)} categorias encontradas")
    return categories


def get_series_from_category(page, category_id):
    """Obtém séries de uma categoria"""
    logger.info(f"\n📺 Explorando categoria {category_id}...")
    
    page.goto(f"{BASE_URL}/#/series/category/{category_id}/", timeout=30000)
    time.sleep(3)
    
    series_list = []
    seen = set()
    
    # Scroll para carregar tudo
    for _ in range(5):
        cards = page.locator("a[href*='/series/category/'][href*='/info/']").all()
        
        for card in cards:
            try:
                href = card.get_attribute("href")
                text = card.inner_text().strip()
                title = text.split('\n')[0] if text else "Unknown"
                
                if not href or title in ["", "More info"]:
                    continue
                
                match = re.search(r'/series/category/(\d+)/(\d+)/info', href)
                if match:
                    cat_id = match.group(1)
                    series_id = match.group(2)
                    
                    if series_id in seen:
                        continue
                    seen.add(series_id)
                    
                    series_list.append({
                        'title': title,
                        'category_id': cat_id,
                        'series_id': series_id
                    })
            except:
                pass
        
        page.mouse.wheel(0, 800)
        time.sleep(1)
    
    logger.info(f"   {len(series_list)} séries nesta categoria")
    return series_list


def extract_series_video(page, series_info):
    """Extrai vídeo de uma série"""
    title = series_info['title']
    series_id = series_info['series_id']
    cat_id = series_info['category_id']
    
    logger.info(f"\n🎬 {title}")
    
    try:
        # Navegar para página da série
        page.goto(f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/info/", timeout=15000)
        time.sleep(3)
        
        # Procurar por episódios/play
        play_links = []
        
        # Tentar vários seletores
        selectors = [
            "a[href*='/play/']",
            ".episode",
            "[class*='episodio']",
            ".v-list-item a"
        ]
        
        for selector in selectors:
            links = page.locator(selector).all()
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and "/play/" in href:
                        match = re.search(r'/play/(\d+)', href)
                        if match:
                            play_links.append({
                                'episode_id': match.group(1),
                                'href': href
                            })
                except:
                    pass
        
        if not play_links:
            # Tentar clicar no primeiro elemento clicável
            all_links = page.locator("a").all()
            for link in all_links:
                try:
                    text = link.inner_text().strip().lower()
                    if any(x in text for x in ['ep', 'cap', 'play', 'assistir']):
                        link.click()
                        time.sleep(3)
                        
                        # Verificar se mudou de URL
                        if "/play/" in page.url:
                            match = re.search(r'/play/(\d+)', page.url)
                            if match:
                                play_links.append({
                                    'episode_id': match.group(1),
                                    'href': page.url
                                })
                        break
                except:
                    pass
        
        if not play_links:
            logger.warning("   ⚠️ Sem episódios")
            return None
        
        # Pegar primeiro episódio
        ep = play_links[0]
        
        # Navegar para o player
        play_url = f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/play/{ep['episode_id']}/"
        page.goto(play_url, timeout=15000)
        time.sleep(5)
        
        # Extrair vídeo
        for attempt in range(10):
            video_url = page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (v && v.src) return v.src;
                    
                    const sources = v ? v.querySelectorAll('source') : [];
                    for (let s of sources) if (s.src) return s.src;
                    
                    const iframes = document.querySelectorAll('iframe');
                    for (let f of iframes) if (f.src) return f.src;
                    
                    const all = document.querySelectorAll('*');
                    for (let e of all) {
                        if (e.src && (e.src.includes('.mp4') || e.src.includes('.m3u8'))) {
                            return e.src;
                        }
                    }
                    return null;
                }
            """)
            
            if video_url:
                logger.info(f"   ✅ {video_url[:60]}...")
                return {
                    'title': title,
                    'series_id': series_id,
                    'video_url': video_url,
                    'category_id': cat_id
                }
            
            time.sleep(1)
        
        logger.warning("   ❌ MP4 não encontrado")
        return None
        
    except Exception as e:
        logger.error(f"   💥 Erro: {e}")
        return None


def run_scraper():
    """Executa scraper completo"""
    logger.info("="*70)
    logger.info("🚀 SERIES SCRAPER v2 - Opera Topzera")
    logger.info("="*70)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        
        try:
            # Login
            logger.info("\n🔐 Login...")
            page.goto(f"{BASE_URL}/#/", timeout=60000)
            time.sleep(2)
            
            if page.locator("input[name='username']").is_visible(timeout=5000):
                page.fill("input[name='username']", "t2TGgarYJ")
                page.fill("input[name='password']", "66e74xKRJ")
                page.click("button:has-text('Login')")
                time.sleep(3)
                logger.info("✅ Logado")
            
            # Coletar categorias
            categories = get_categories(page)
            
            # Coletar todas as séries
            all_series = []
            for cat in categories[:3]:  # Limitar a 3 categorias por enquanto
                series = get_series_from_category(page, cat['id'])
                all_series.extend(series)
            
            logger.info(f"\n📊 Total de séries: {len(all_series)}")
            
            # Filtrar já existentes
            new_series = [s for s in all_series if not check_series_exists(s['series_id'])]
            logger.info(f"📊 Séries novas: {len(new_series)}")
            
            # Processar
            added = 0
            for i, s in enumerate(new_series[:20], 1):  # Limitar a 20 por enquanto
                logger.info(f"\n{'='*70}")
                logger.info(f"[{i}/20] {s['title']}")
                
                result = extract_series_video(page, s)
                if result:
                    try:
                        save_embed(
                            title=result['title'],
                            embed_url=result['video_url'],
                            tmdb_id=str(result['series_id']),
                            original_raw_title=result['title']
                        )
                        logger.info("   💾 Salvo!")
                        added += 1
                    except Exception as e:
                        logger.error(f"   ❌ Erro ao salvar: {e}")
                
                time.sleep(2)
            
            logger.info(f"\n{'='*70}")
            logger.info("✅ COMPLETO!")
            logger.info(f"Adicionadas: {added}")
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Interrompido")
        except Exception as e:
            logger.error(f"\n💥 Erro fatal: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    run_scraper()
