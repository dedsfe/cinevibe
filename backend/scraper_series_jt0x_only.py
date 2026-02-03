#!/usr/bin/env python3
"""
Series Scraper - Apenas jt0x.com (sem YouTube)
Filtra apenas MP4s de alta qualidade
"""

import logging
import re
import time
import sys
import os
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_embed, get_conn

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "http://web.operatopzera.net"


def check_episode_exists(series_id, season, episode):
    """Verifica se episódio já existe"""
    try:
        conn = get_conn()
        c = conn.cursor()
        pattern = f"%/series/%/{series_id}/play/season/{season}/episode/{episode}/%"
        c.execute("SELECT title FROM links WHERE embed_url LIKE ?", (pattern,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except:
        return False


def is_valid_video_url(url):
    """Verifica se URL é válida (jt0x apenas, não YouTube)"""
    if not url:
        return False
    # Aceitar apenas jt0x.com (MP4 de qualidade)
    if "jt0x.com" in url and ".mp4" in url:
        return True
    return False


def extract_episode(page, series_info, season, episode):
    """Extrai episódio da série"""
    title = series_info['title']
    cat_id = series_info['category_id']
    series_id = series_info['series_id']
    
    ep_title = f"{title} - S{season:02d}E{episode:02d}"
    
    try:
        episode_url = f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/play/season/{season}/episode/{episode}/"
        page.goto(episode_url, timeout=15000)
        time.sleep(5)
        
        # Extrair vídeo
        for _ in range(10):
            video_url = page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (v && v.src) return v.src;
                    const sources = v ? v.querySelectorAll('source') : [];
                    for (let s of sources) if (s.src) return s.src;
                    const iframe = document.querySelector('iframe');
                    if (iframe && iframe.src) return iframe.src;
                    return null;
                }
            """)
            
            if video_url:
                # Verificar se é jt0x (não YouTube)
                if is_valid_video_url(video_url):
                    logger.info(f"    ✅ {ep_title}")
                    logger.info(f"       {video_url[:50]}...")
                    return {
                        'title': ep_title,
                        'series_title': title,
                        'series_id': series_id,
                        'season': season,
                        'episode': episode,
                        'video_url': video_url
                    }
                else:
                    logger.info(f"    ⚠️  {ep_title} - YouTube (pulando)")
                    return None
            
            time.sleep(1)
        
        return None
        
    except Exception as e:
        return None


def discover_series(page, max_series=20):
    """Descobre séries disponíveis"""
    logger.info("\n📺 Descobrindo séries...")
    
    categories = ['105', '106', '51', '66']
    series_list = []
    seen_ids = set()
    
    for cat_id in categories:
        if len(series_list) >= max_series:
            break
        
        page.goto(f"{BASE_URL}/#/series/category/{cat_id}/", timeout=20000)
        time.sleep(3)
        
        for _ in range(3):
            cards = page.locator("a[href*='/series/category/'][href*='/info/']").all()
            
            for card in cards:
                try:
                    href = card.get_attribute("href")
                    text = card.inner_text().strip()
                    title = text.split('\n')[0] if text else None
                    
                    if not title or title in ["", "More info"]:
                        continue
                    
                    match = re.search(r'/series/category/(\d+)/(\d+)/info', href)
                    if match:
                        found_cat_id = match.group(1)
                        series_id = match.group(2)
                        
                        if series_id in seen_ids:
                            continue
                        seen_ids.add(series_id)
                        
                        series_list.append({
                            'title': title,
                            'category_id': found_cat_id,
                            'series_id': series_id
                        })
                        
                        if len(series_list) >= max_series:
                            break
                except:
                    pass
            
            page.mouse.wheel(0, 1000)
            time.sleep(1)
    
    logger.info(f"✅ {len(series_list)} séries encontradas")
    return series_list


def main():
    """Executa scraper"""
    logger.info("="*70)
    logger.info("🚀 SERIES SCRAPER - Apenas jt0x.com (Alta Qualidade)")
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
            
            # Descobrir séries
            series_list = discover_series(page, max_series=15)
            
            # Extrair episódios
            all_extracted = []
            
            for i, series in enumerate(series_list, 1):
                logger.info(f"\n{'='*70}")
                logger.info(f"[{i}/{len(series_list)}] {series['title']}")
                
                # Tentar temporada 1
                logger.info(f"   📁 Temporada 1")
                season_extracted = 0
                
                for episode in range(1, 6):  # Max 5 episódios
                    if check_episode_exists(series['series_id'], 1, episode):
                        logger.info(f"    ⏭️  S01E{episode:02d} já existe")
                        season_extracted += 1
                        continue
                    
                    result = extract_episode(page, series, 1, episode)
                    
                    if result:
                        try:
                            save_embed(
                                title=result['title'],
                                embed_url=result['video_url'],
                                tmdb_id=f"{result['series_id']}_S01E{episode:02d}",
                                original_raw_title=result['title']
                            )
                            logger.info(f"    💾 Salvo!")
                            all_extracted.append(result)
                            season_extracted += 1
                        except Exception as e:
                            logger.error(f"    ❌ Erro ao salvar: {e}")
                    else:
                        # Se não achou este episódio, assume fim da temporada
                        if episode == 1:
                            logger.info(f"    ❌ Série não disponível")
                        else:
                            logger.info(f"    🏁 Fim da temporada")
                        break
                    
                    time.sleep(1)
                
                if season_extracted == 0:
                    logger.info(f"   ❌ Nenhum episódio extraído")
                
                time.sleep(2)
            
            # Resumo
            logger.info(f"\n{'='*70}")
            logger.info("✅ COMPLETO!")
            logger.info(f"{'='*70}")
            logger.info(f"Total de episódios jt0x: {len(all_extracted)}")
            
            for ep in all_extracted:
                logger.info(f"  ✓ {ep['title']}")
            
        except Exception as e:
            logger.error(f"\n💥 Erro: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
