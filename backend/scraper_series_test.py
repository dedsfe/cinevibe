#!/usr/bin/env python3
"""
Teste de Scraper de Séries - Estrutura Completa
Testa extração de: Série -> Temporadas -> Episódios -> MP4
"""

import logging
import re
import time
import sys
import os
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "http://web.operatopzera.net"

# Série de teste (exemplo do usuário)
TEST_SERIES = {
    'title': 'Série Teste',
    'category_id': '106',
    'series_id': '4165'
}


def extract_seasons_and_episodes(page, series_info):
    """
    Extrai todas as temporadas e episódios de uma série
    Retorna estrutura: {temporada: [episódios]}
    """
    title = series_info.get('title', 'Unknown')
    cat_id = series_info['category_id']
    series_id = series_info['series_id']
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🎬 ANÁLISANDO: {title}")
    logger.info(f"   ID: {series_id} | Categoria: {cat_id}")
    logger.info(f"{'='*70}")
    
    # Navegar para página da série
    series_url = f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/info/"
    logger.info(f"\n📍 URL: {series_url}")
    
    page.goto(series_url, timeout=30000)
    time.sleep(4)  # Esperar carregar
    
    # Tirar screenshot para análise
    page.screenshot(path=f"/tmp/series_{series_id}_info.png")
    logger.info(f"📸 Screenshot salvo: /tmp/series_{series_id}_info.png")
    
    # ============================================================
    # PASSO 1: ENCONTRAR SELECTOR DE TEMPORADAS
    # ============================================================
    logger.info("\n🔍 PASSO 1: Procurando selector de temporadas...")
    
    season_selectors = [
        "select[class*='season']",
        "select[class*='temporada']",
        ".v-select",
        "[role='combobox']",
        ".season-selector",
        "select",
        ".v-menu__content",
        "[class*='dropdown']"
    ]
    
    season_selector = None
    season_options = []
    
    for selector in season_selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible(timeout=2000):
                # Verificar se tem opções de temporada
                options = element.locator("option").all()
                if options:
                    logger.info(f"   ✅ Selector encontrado: {selector}")
                    logger.info(f"   📊 {len(options)} opções")
                    season_selector = selector
                    season_options = options
                    break
        except:
            continue
    
    if not season_selector:
        logger.warning("   ⚠️ Selector de temporadas não encontrado")
        logger.info("   Tentando encontrar episódios sem selector...")
    else:
        # Listar temporadas
        logger.info("\n📋 TEMPORADAS ENCONTRADAS:")
        for i, opt in enumerate(season_options[:5], 1):
            try:
                text = opt.inner_text().strip()
                value = opt.get_attribute("value")
                logger.info(f"   {i}. {text} (value: {value})")
            except:
                pass
    
    # ============================================================
    # PASSO 2: EXTRAIR EPISÓDIOS DE CADA TEMPORADA
    # ============================================================
    logger.info("\n🔍 PASSO 2: Extraindo episódios...")
    
    all_episodes = []
    
    if season_selector and season_options:
        # Para cada temporada
        for idx, option in enumerate(season_options):
            try:
                season_text = option.inner_text().strip()
                season_value = option.get_attribute("value")
                
                logger.info(f"\n🎯 TEMPORADA: {season_text}")
                
                # Selecionar temporada
                select_elem = page.locator(season_selector).first
                select_elem.select_option(value=season_value)
                time.sleep(3)  # Esperar carregar episódios
                
                # Tirar screenshot
                page.screenshot(path=f"/tmp/series_{series_id}_season_{idx}.png")
                
                # Extrair episódios desta temporada
                episodes = extract_episodes_from_page(page, season_text)
                all_episodes.extend(episodes)
                
                logger.info(f"   ✅ {len(episodes)} episódios encontrados")
                
            except Exception as e:
                logger.error(f"   ❌ Erro ao processar temporada: {e}")
    else:
        # Sem selector - tentar extrair todos os episódios visíveis
        logger.info("\n📺 Extraindo episódios (sem selector)...")
        episodes = extract_episodes_from_page(page, "Temporada única")
        all_episodes.extend(episodes)
    
    # ============================================================
    # PASSO 3: EXTRAIR MP4 DE CADA EPISÓDIO
    # ============================================================
    logger.info(f"\n🔍 PASSO 3: Extraindo MP4 de {len(all_episodes)} episódio(s)...")
    
    extracted_videos = []
    
    for i, ep in enumerate(all_episodes[:3], 1):  # Limitar a 3 para teste
        logger.info(f"\n▶️ [{i}/{min(len(all_episodes), 3)}] {ep['title']}")
        
        video_url = extract_episode_video(page, ep, cat_id, series_id)
        
        if video_url:
            extracted_videos.append({
                'series_title': title,
                'season': ep['season'],
                'episode_title': ep['title'],
                'episode_id': ep['id'],
                'video_url': video_url
            })
            logger.info(f"   ✅ MP4: {video_url[:60]}...")
        else:
            logger.warning(f"   ❌ MP4 não encontrado")
        
        time.sleep(2)
    
    return extracted_videos


def extract_episodes_from_page(page, season_name):
    """Extrai lista de episódios da página atual"""
    episodes = []
    
    # Diferentes seletores para episódios
    episode_selectors = [
        "a[href*='/play/']",
        ".episode-item",
        ".v-list-item",
        "[class*='episodio']",
        ".row a",  # Estrutura comum em lists
    ]
    
    for selector in episode_selectors:
        try:
            elements = page.locator(selector).all()
            
            for elem in elements:
                try:
                    href = elem.get_attribute("href")
                    text = elem.inner_text().strip()
                    
                    if not href:
                        continue
                    
                    # Extrair episode_id do href
                    match = re.search(r'/play/(\d+)', href)
                    if not match:
                        continue
                    
                    episode_id = match.group(1)
                    
                    episodes.append({
                        'id': episode_id,
                        'title': text.split('\n')[0] if text else f"Ep {episode_id}",
                        'season': season_name,
                        'href': href
                    })
                    
                except:
                    continue
                    
        except:
            continue
    
    # Remover duplicatas
    unique = {}
    for ep in episodes:
        if ep['id'] not in unique:
            unique[ep['id']] = ep
    
    return list(unique.values())


def extract_episode_video(page, episode, cat_id, series_id):
    """Navega para o episódio e extrai o MP4"""
    
    ep_id = episode['id']
    
    try:
        # Navegar para o player do episódio
        play_url = f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/play/{ep_id}/"
        logger.info(f"   🌐 Player: {play_url}")
        
        page.goto(play_url, timeout=20000)
        time.sleep(5)  # Esperar player carregar
        
        # Tentar extrair vídeo múltiplas vezes
        for attempt in range(15):
            video_url = page.evaluate("""
                () => {
                    // 1. Video tag
                    const video = document.querySelector('video');
                    if (video && video.src) return video.src;
                    
                    // 2. Sources dentro do video
                    const sources = video ? video.querySelectorAll('source') : [];
                    for (let src of sources) {
                        if (src.src && (src.src.includes('.mp4') || src.src.includes('.m3u8'))) {
                            return src.src;
                        }
                    }
                    
                    // 3. Iframe
                    const iframe = document.querySelector('iframe');
                    if (iframe && iframe.src) return iframe.src;
                    
                    // 4. Qualquer elemento com src
                    const all = document.querySelectorAll('*');
                    for (let el of all) {
                        if (el.src && (el.src.includes('.mp4') || el.src.includes('.m3u8'))) {
                            return el.src;
                        }
                    }
                    
                    return null;
                }
            """)
            
            if video_url:
                return video_url
            
            time.sleep(1)
        
        return None
        
    except Exception as e:
        logger.error(f"   💥 Erro: {e}")
        return None


def main():
    """Executa teste de extração"""
    logger.info("="*70)
    logger.info("🧪 TESTE: Scraper de Séries - Estrutura Completa")
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
            
            # Extrair série de teste
            results = extract_seasons_and_episodes(page, TEST_SERIES)
            
            # Resumo
            logger.info(f"\n{'='*70}")
            logger.info("📊 RESUMO DO TESTE")
            logger.info(f"{'='*70}")
            logger.info(f"Vídeos extraídos: {len(results)}")
            
            for r in results:
                logger.info(f"\n🎬 {r['series_title']}")
                logger.info(f"   📁 {r['season']}")
                logger.info(f"   🎥 {r['episode_title']}")
                logger.info(f"   🔗 {r['video_url'][:70]}...")
            
        except Exception as e:
            logger.error(f"\n💥 Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ Teste completo!")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
