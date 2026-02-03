#!/usr/bin/env python3
"""
Series Scraper for Opera Topzera
Extrai MP4s de séries do http://web.operatopzera.net/#/series/
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

# Configurações
TARGET_SERIES = 50  # Meta de séries para extrair
BASE_URL = "http://web.operatopzera.net"


def check_series_exists_in_db(series_id):
    """Verifica se a série já existe no banco pelo ID"""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT title FROM links WHERE embed_url LIKE ? OR tmdb_id = ?",
            (f"%/{series_id}.mp4%", str(series_id))
        )
        result = c.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking DB: {e}")
        return False


def get_db_stats():
    """Retorna estatísticas do banco de séries"""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM links WHERE embed_url LIKE '%/series/%'")
        series_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM links WHERE embed_url IS NOT NULL AND embed_url != 'NOT_FOUND'")
        total_count = c.fetchone()[0]
        conn.close()
        return {"series": series_count, "total": total_count}
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"series": 0, "total": 0}


def scrape_series_list(page):
    """Coleta lista de todas as séries disponíveis"""
    logger.info("📺 Coletando lista de séries...")
    
    page.goto(f"{BASE_URL}/#/series/", timeout=30000)
    time.sleep(3)
    
    series_list = []
    seen_ids = set()
    scroll_count = 0
    max_scrolls = 30
    
    while scroll_count < max_scrolls and len(series_list) < 100:
        # Encontrar todos os cards de séries
        cards = page.locator("a[href*='/series/category/']").all()
        
        found_new = False
        for card in cards:
            try:
                href = card.get_attribute("href")
                text = card.inner_text().strip()
                title = text.split("\n")[0].strip()
                
                if not href or not title or title in ["More info", "", " "]:
                    continue
                
                # Extrair IDs
                match = re.search(r'/series/category/(\d+)/(\d+)/info', href)
                if not match:
                    continue
                
                category_id = match.group(1)
                series_id = match.group(2)
                
                if series_id in seen_ids:
                    continue
                seen_ids.add(series_id)
                
                series_list.append({
                    'title': title,
                    'category_id': category_id,
                    'series_id': series_id,
                    'href': href
                })
                found_new = True
                
            except Exception as e:
                continue
        
        if not found_new and scroll_count > 5:
            break
        
        # Scroll para mais conteúdo
        page.mouse.wheel(0, 1000)
        time.sleep(1.5)
        scroll_count += 1
    
    logger.info(f"✅ {len(series_list)} séries encontradas")
    return series_list


def extract_series_episodes(page, series_info):
    """Extrai episódios de uma série"""
    title = series_info['title']
    series_id = series_info['series_id']
    category_id = series_info['category_id']
    
    logger.info(f"\n🎬 Processando: {title}")
    logger.info(f"   ID: {series_id}")
    
    try:
        # Navegar para a página da série
        series_url = f"{BASE_URL}/#/series/category/{category_id}/{series_id}/info/"
        page.goto(series_url, timeout=15000)
        time.sleep(3)
        
        # Procurar por episódios
        episodes = []
        
        # Diferentes estratégias para encontrar episódios
        selectors = [
            "a[href*='/play/']",
            ".episode-item",
            "[class*='episode'] a",
            ".v-list-item a",
        ]
        
        for selector in selectors:
            eps = page.locator(selector).all()
            for ep in eps:
                try:
                    href = ep.get_attribute("href")
                    ep_text = ep.inner_text().strip()
                    
                    if href and "/play/" in href:
                        # Extrair episode_id
                        match = re.search(r'/play/(\d+)/', href)
                        if match:
                            episode_id = match.group(1)
                            episodes.append({
                                'episode_id': episode_id,
                                'href': href,
                                'text': ep_text
                            })
                except:
                    continue
        
        if not episodes:
            logger.warning(f"   ⚠️ Nenhum episódio encontrado")
            return None
        
        logger.info(f"   📺 {len(episodes)} episódio(s) encontrado(s)")
        
        # Extrair o primeiro episódio (ou todos se quiser)
        first_ep = episodes[0]
        
        # Clicar no episódio para obter o vídeo
        play_url = f"{BASE_URL}/#/series/category/{category_id}/{series_id}/play/{first_ep['episode_id']}/"
        page.goto(play_url, timeout=15000)
        time.sleep(4)
        
        # Extrair URL do vídeo
        video_url = None
        for attempt in range(10):
            video_url = page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    if (video && video.src && video.src.includes('.mp4')) return video.src;
                    
                    const sources = video ? video.querySelectorAll('source') : [];
                    for (let src of sources) {
                        if (src.src && src.src.includes('.mp4')) return src.src;
                    }
                    
                    const iframe = document.querySelector('iframe');
                    if (iframe && iframe.src) return iframe.src;
                    
                    return null;
                }
            """)
            
            if video_url:
                break
            time.sleep(1)
        
        if video_url:
            logger.info(f"   ✅ MP4: {video_url[:80]}...")
            return {
                'title': title,
                'series_id': series_id,
                'video_url': video_url,
                'episodes_count': len(episodes)
            }
        else:
            logger.warning(f"   ❌ MP4 não encontrado")
            return None
            
    except Exception as e:
        logger.error(f"   💥 Erro: {e}")
        return None


def save_series_to_db(series_data):
    """Salva a série no banco de dados"""
    try:
        save_embed(
            title=series_data['title'],
            embed_url=series_data['video_url'],
            tmdb_id=str(series_data['series_id']),
            original_raw_title=series_data['title'],
        )
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar no banco: {e}")
        return False


def run_series_scraper():
    """Executa o scraper de séries completo"""
    logger.info("="*70)
    logger.info("🚀 SERIES SCRAPER - Opera Topzera")
    logger.info("="*70)
    
    stats = get_db_stats()
    logger.info(f"📊 Séries no banco: {stats['series']}")
    logger.info(f"📊 Total de itens: {stats['total']}")
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
            logger.info("\n🔐 Fazendo login...")
            page.goto(f"{BASE_URL}/#/", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(2)
            
            if page.locator("input[name='username']").is_visible(timeout=5000):
                page.fill("input[name='username']", "t2TGgarYJ")
                page.fill("input[name='password']", "66e74xKRJ")
                page.click("button:has-text('Login')")
                page.wait_for_url("**/#/", timeout=30000)
                time.sleep(2)
                logger.info("✅ Login OK")
            
            # Coletar lista de séries
            series_list = scrape_series_list(page)
            
            if not series_list:
                logger.error("❌ Nenhuma série encontrada")
                return
            
            # Filtrar séries já existentes
            new_series = []
            for s in series_list:
                if not check_series_exists_in_db(s['series_id']):
                    new_series.append(s)
            
            logger.info(f"\n📺 Séries novas para processar: {len(new_series)}")
            
            # Processar séries
            added_count = 0
            failed_count = 0
            
            for i, series_info in enumerate(new_series[:TARGET_SERIES], 1):
                logger.info(f"\n{'='*70}")
                logger.info(f"[{i}/{min(len(new_series), TARGET_SERIES)}] Processando série...")
                
                result = extract_series_episodes(page, series_info)
                
                if result:
                    if save_series_to_db(result):
                        logger.info(f"   💾 Salvo no banco!")
                        added_count += 1
                    else:
                        logger.error(f"   ❌ Falha ao salvar")
                        failed_count += 1
                else:
                    failed_count += 1
                
                # Pausa entre séries
                time.sleep(2)
            
            logger.info(f"\n{'='*70}")
            logger.info("✅ SCRAPER COMPLETO")
            logger.info(f"{'='*70}")
            logger.info(f"Adicionadas: {added_count}")
            logger.info(f"Falhas: {failed_count}")
            
            stats_final = get_db_stats()
            logger.info(f"\n📊 Estatísticas finais:")
            logger.info(f"   Séries: {stats_final['series']}")
            logger.info(f"   Total: {stats_final['total']}")
            
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Interrompido pelo usuário")
        except Exception as e:
            logger.error(f"\n💥 Erro fatal: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    run_series_scraper()
