#!/usr/bin/env python3
"""
Series Scraper - Versão Corrigida
Entra no player do episódio e extrai o MP4 do jt0x.com
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
        # Procurar por URL que contenha o ID da série
        pattern = f"%jt0x.com%series%{series_id}%"
        c.execute("SELECT title FROM links WHERE embed_url LIKE ?", (pattern,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except:
        return False


def extract_episode_mp4(page, series_info, season, episode):
    """
    Navega para o PLAYER do episódio e extrai o MP4
    URL: #/series/category/{cat_id}/{series_id}/play/season/{season}/episode/{episode}/
    """
    title = series_info['title']
    cat_id = series_info['category_id']
    series_id = series_info['series_id']
    
    ep_title = f"{title} - S{season:02d}E{episode:02d}"
    
    try:
        # Construir URL do PLAYER do episódio
        episode_url = f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/play/season/{season}/episode/{episode}/"
        
        logger.info(f"    🌐 Player: {episode_url}")
        
        # Navegar para o player
        page.goto(episode_url, timeout=20000)
        
        # ESPERAR o player carregar (5-8 segundos)
        logger.info(f"    ⏳ Aguardando player carregar...")
        time.sleep(6)
        
        # Tirar screenshot para debug
        page.screenshot(path=f"/tmp/episode_{series_id}_s{season}e{episode}.png")
        
        # Procurar o elemento VIDEO e extrair o src
        logger.info(f"    🔍 Procurando elemento <video>...")
        
        video_url = None
        
        # Tentativa 1: Direto do elemento video
        video_elem = page.locator("video").first
        if video_elem.is_visible(timeout=5000):
            video_url = video_elem.get_attribute("src")
            if video_url:
                logger.info(f"    ✅ Video src encontrado!")
        
        # Tentativa 2: Via JavaScript (mais confiável)
        if not video_url:
            for attempt in range(10):
                video_url = page.evaluate("""
                    () => {
                        // Procurar elemento video
                        const video = document.querySelector('video');
                        if (video) {
                            // Src direto
                            if (video.src && video.src.includes('.mp4')) {
                                return video.src;
                            }
                            // Sources
                            const sources = video.querySelectorAll('source');
                            for (let src of sources) {
                                if (src.src && src.src.includes('.mp4')) {
                                    return src.src;
                                }
                            }
                        }
                        
                        // Procurar no documento inteiro
                        const allVideos = document.querySelectorAll('video');
                        for (let v of allVideos) {
                            if (v.src && v.src.includes('.mp4')) {
                                return v.src;
                            }
                        }
                        
                        // Procurar por elementos com jt0x
                        const all = document.querySelectorAll('*');
                        for (let el of all) {
                            if (el.src && el.src.includes('jt0x.com') && el.src.includes('.mp4')) {
                                return el.src;
                            }
                        }
                        
                        return null;
                    }
                """)
                
                if video_url and 'jt0x.com' in video_url and '.mp4' in video_url:
                    logger.info(f"    ✅ MP4 encontrado (tentativa {attempt + 1})!")
                    break
                
                time.sleep(1)
        
        if video_url and 'jt0x.com' in video_url and '.mp4' in video_url:
            logger.info(f"    ✅ {ep_title}")
            logger.info(f"       {video_url[:60]}...")
            return {
                'title': ep_title,
                'series_title': title,
                'series_id': series_id,
                'season': season,
                'episode': episode,
                'video_url': video_url
            }
        else:
            logger.warning(f"    ⚠️  {ep_title} - MP4 não encontrado")
            return None
        
    except Exception as e:
        logger.error(f"    ❌ Erro: {e}")
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
        
        logger.info(f"   📂 Categoria {cat_id}...")
        
        page.goto(f"{BASE_URL}/#/series/category/{cat_id}/", timeout=20000)
        time.sleep(3)
        
        # Scroll e coleta
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
    logger.info("🚀 SERIES SCRAPER - Versão Corrigida (Player -> MP4)")
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
                logger.info(f"[{i}/{len(series_list)}] {series['title']}")
                logger.info(f"   ID: {series['series_id']}")
                
                # Tentar temporada 1
                logger.info(f"   📁 Temporada 1")
                
                season_extracted = 0
                for episode in range(1, 4):  # Max 3 episódios por série
                    if check_episode_exists(series['series_id'], 1, episode):
                        logger.info(f"    ⏭️  S01E{episode:02d} já existe")
                        season_extracted += 1
                        continue
                    
                    result = extract_episode_mp4(page, series, 1, episode)
                    
                    if result:
                        try:
                            save_embed(
                                title=result['title'],
                                embed_url=result['video_url'],
                                tmdb_id=f"{result['series_id']}_S01E{episode:02d}",
                                original_raw_title=result['title']
                            )
                            logger.info(f"    💾 Salvo no banco!")
                            all_extracted.append(result)
                            season_extracted += 1
                        except Exception as e:
                            logger.error(f"    ❌ Erro ao salvar: {e}")
                    else:
                        # Se não achou este episódio, assume fim da temporada
                        if episode == 1:
                            logger.info(f"    ❌ Série não disponível no player")
                        else:
                            logger.info(f"    🏁 Fim da temporada")
                        break
                    
                    time.sleep(2)
                
                if season_extracted == 0:
                    logger.info(f"   ❌ Nenhum episódio extraído")
                
                time.sleep(3)  # Pausa entre séries
            
            # Resumo
            logger.info(f"\n{'='*70}")
            logger.info("✅ COMPLETO!")
            logger.info(f"{'='*70}")
            logger.info(f"Total de episódios MP4: {len(all_extracted)}")
            
            for ep in all_extracted:
                logger.info(f"  ✓ {ep['title']}")
                logger.info(f"    {ep['video_url'][:50]}...")
            
        except Exception as e:
            logger.error(f"\n💥 Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
