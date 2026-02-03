#!/usr/bin/env python3
"""
Series Scraper - Versão Funcional
URL: #/series/category/{cat_id}/{series_id}/play/season/{season}/episode/{ep}/
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


def check_episode_exists(series_id, season, episode):
    """Verifica se episódio já existe no banco"""
    try:
        conn = get_conn()
        c = conn.cursor()
        # Procurar por URL que contenha o padrão da série/temporada/episódio
        pattern = f"%/series/%/{series_id}/play/season/{season}/episode/{episode}/%"
        c.execute("SELECT title FROM links WHERE embed_url LIKE ?", (pattern,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"DB Error: {e}")
        return False


def extract_episode_video(page, series_info, season, episode):
    """
    Extrai vídeo de um episódio específico
    URL: #/series/category/{cat_id}/{series_id}/play/season/{season}/episode/{episode}/
    """
    title = series_info['title']
    cat_id = series_info['category_id']
    series_id = series_info['series_id']
    
    ep_title = f"{title} - S{season:02d}E{episode:02d}"
    
    logger.info(f"    🎬 {ep_title}")
    
    try:
        # Construir URL do episódio
        episode_url = f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/play/season/{season}/episode/{episode}/"
        
        page.goto(episode_url, timeout=15000)
        time.sleep(5)  # Esperar player carregar
        
        # Extrair vídeo
        for attempt in range(10):
            video_url = page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (v && v.src) return v.src;
                    
                    const sources = v ? v.querySelectorAll('source') : [];
                    for (let s of sources) {
                        if (s.src) return s.src;
                    }
                    
                    const iframe = document.querySelector('iframe');
                    if (iframe && iframe.src) return iframe.src;
                    
                    return null;
                }
            """)
            
            if video_url:
                logger.info(f"    ✅ {video_url[:50]}...")
                return {
                    'title': ep_title,
                    'series_title': title,
                    'series_id': series_id,
                    'season': season,
                    'episode': episode,
                    'video_url': video_url
                }
            
            time.sleep(1)
        
        return None
        
    except Exception as e:
        logger.error(f"    ❌ Erro: {e}")
        return None


def extract_series_episodes(page, series_info, max_seasons=2, max_episodes=5):
    """
    Extrai episódios de uma série
    Tenta temporada 1 e 2, até 5 episódios cada
    """
    title = series_info['title']
    series_id = series_info['series_id']
    
    logger.info(f"\n🎬 {title}")
    logger.info(f"   ID: {series_id}")
    
    extracted = []
    
    # Tentar múltiplas temporadas
    for season in range(1, max_seasons + 1):
        logger.info(f"\n   📁 Temporada {season}")
        
        season_found = False
        
        # Tentar múltiplos episódios
        for episode in range(1, max_episodes + 1):
            # Verificar se já existe
            if check_episode_exists(series_id, season, episode):
                logger.info(f"    ⏭️  S{season:02d}E{episode:02d} já existe")
                season_found = True
                continue
            
            result = extract_episode_video(page, series_info, season, episode)
            
            if result:
                # Salvar no banco
                try:
                    save_embed(
                        title=result['title'],
                        embed_url=result['video_url'],
                        tmdb_id=f"{series_id}_S{season}E{episode}",
                        original_raw_title=result['title']
                    )
                    logger.info(f"    💾 Salvo!")
                    extracted.append(result)
                    season_found = True
                except Exception as e:
                    logger.error(f"    ❌ Erro ao salvar: {e}")
            else:
                # Se não achou este episódio, assume que temporada acabou
                if episode == 1:
                    logger.info(f"    ⚠️  Temporada {season} não encontrada")
                    break
                else:
                    logger.info(f"    🏁 Fim da temporada {season}")
                    break
            
            time.sleep(1)
        
        # Se não achou nada na temporada 1, para
        if season == 1 and not season_found:
            logger.info(f"   ❌ Série não disponível")
            break
    
    return extracted


def discover_series(page, max_series=20):
    """Descobre séries disponíveis"""
    logger.info("\n📺 Descobrindo séries...")
    
    # Navegar para página de séries
    page.goto(f"{BASE_URL}/#/series/", timeout=30000)
    time.sleep(4)
    
    series_list = []
    seen_ids = set()
    
    # Coletar de múltiplas categorias
    categories = ['105', '106', '51', '66']
    
    for cat_id in categories:
        if len(series_list) >= max_series:
            break
        
        logger.info(f"   📂 Categoria {cat_id}...")
        
        page.goto(f"{BASE_URL}/#/series/category/{cat_id}/", timeout=20000)
        time.sleep(3)
        
        # Scroll para carregar
        for _ in range(3):
            # Encontrar cards
            cards = page.locator("a[href*='/series/category/'][href*='/info/']").all()
            
            for card in cards:
                try:
                    href = card.get_attribute("href")
                    text = card.inner_text().strip()
                    title = text.split('\n')[0] if text else None
                    
                    if not title or title in ["", "More info"]:
                        continue
                    
                    # Extrair IDs
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
    """Executa scraper de séries"""
    logger.info("="*70)
    logger.info("🚀 SERIES SCRAPER - Versão Funcional")
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
            series_list = discover_series(page, max_series=10)
            
            # Extrair episódios
            all_extracted = []
            
            for i, series in enumerate(series_list, 1):
                logger.info(f"\n{'='*70}")
                logger.info(f"[{i}/{len(series_list)}]")
                
                episodes = extract_series_episodes(
                    page, series, 
                    max_seasons=2, 
                    max_episodes=5
                )
                
                all_extracted.extend(episodes)
                
                # Pausa entre séries
                time.sleep(2)
            
            # Resumo
            logger.info(f"\n{'='*70}")
            logger.info("✅ COMPLETO!")
            logger.info(f"{'='*70}")
            logger.info(f"Total de episódios: {len(all_extracted)}")
            
            for ep in all_extracted[:10]:
                logger.info(f"  - {ep['title']}")
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Interrompido")
        except Exception as e:
            logger.error(f"\n💥 Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
