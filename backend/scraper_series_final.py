#!/usr/bin/env python3
"""
Series Scraper Final - Múltiplas estratégias
Tenta diferentes abordagens para extrair séries do Opera Topzera
"""

import logging
import re
import time
import sys
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import save_embed, get_conn

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "http://web.operatopzera.net"


class SeriesScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        
    def start(self):
        """Inicia o navegador"""
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        self.page = self.context.new_page()
        
    def stop(self):
        """Para o navegador"""
        if self.browser:
            self.browser.close()
    
    def login(self):
        """Faz login no site"""
        logger.info("🔐 Login...")
        self.page.goto(f"{BASE_URL}/#/", timeout=60000)
        time.sleep(2)
        
        try:
            if self.page.locator("input[name='username']").is_visible(timeout=5000):
                self.page.fill("input[name='username']", "t2TGgarYJ")
                self.page.fill("input[name='password']", "66e74xKRJ")
                self.page.click("button:has-text('Login')")
                self.page.wait_for_url("**/#/", timeout=30000)
                time.sleep(3)
                logger.info("✅ Logado")
                return True
        except Exception as e:
            logger.error(f"❌ Erro no login: {e}")
            return False
        
        return True
    
    def discover_series_structure(self):
        """
        Descobre a estrutura de uma série
        Retorna dict com temporadas e episódios
        """
        logger.info("\n🔍 Analisando estrutura da página atual...")
        
        info = {
            'has_seasons': False,
            'seasons': [],
            'episodes': [],
            'direct_video': None
        }
        
        # 1. Procurar por select de temporadas
        try:
            selects = self.page.locator("select").all()
            for sel in selects:
                opts = sel.locator("option").all()
                if len(opts) > 1:
                    info['has_seasons'] = True
                    info['seasons'] = [{'value': o.get_attribute('value'), 
                                       'text': o.inner_text().strip()} for o in opts]
                    logger.info(f"   📺 {len(opts)} temporadas no select")
                    break
        except:
            pass
        
        # 2. Procurar por links de episódios/play
        try:
            links = self.page.locator("a").all()
            for link in links:
                href = link.get_attribute("href") or ""
                text = link.inner_text().strip()
                
                if "/play/" in href:
                    match = re.search(r'/play/(\d+)', href)
                    if match:
                        info['episodes'].append({
                            'id': match.group(1),
                            'title': text[:50],
                            'href': href
                        })
        except:
            pass
        
        logger.info(f"   🎬 {len(info['episodes'])} episódios encontrados")
        
        # 3. Verificar se tem player direto
        try:
            video = self.page.locator("video").first
            if video.is_visible(timeout=2000):
                src = video.get_attribute("src")
                if src:
                    info['direct_video'] = src
                    logger.info(f"   ✅ Player direto: {src[:60]}...")
        except:
            pass
        
        return info
    
    def extract_series_from_category(self, category_id, max_series=5):
        """
        Extrai séries de uma categoria
        Estratégia: Cada "série" na lista é tratada como um item com um link direto
        """
        logger.info(f"\n📂 Categoria {category_id}")
        
        self.page.goto(f"{BASE_URL}/#/series/category/{category_id}/", timeout=30000)
        time.sleep(4)
        
        # Scroll para carregar tudo
        for _ in range(3):
            self.page.mouse.wheel(0, 800)
            time.sleep(1)
        
        # Encontrar cards de séries
        series_found = []
        
        # Procurar por imagens com links (posters)
        cards = self.page.locator("a[href*='/series/category/'][href*='/info/']").all()
        
        for card in cards[:max_series]:
            try:
                href = card.get_attribute("href")
                text = card.inner_text().strip()
                title = text.split('\n')[0] if text else "Unknown"
                
                match = re.search(r'/series/category/(\d+)/(\d+)/info', href)
                if match:
                    series_found.append({
                        'title': title,
                        'category_id': match.group(1),
                        'series_id': match.group(2),
                        'href': href
                    })
            except:
                pass
        
        logger.info(f"   ✅ {len(series_found)} séries encontradas")
        return series_found
    
    def extract_video_from_series(self, series_info):
        """
        Tenta extrair vídeo de uma série
        Estratégia: Trata cada série como um item único (filme-like)
        """
        title = series_info['title']
        series_id = series_info['series_id']
        cat_id = series_info['category_id']
        
        logger.info(f"\n🎬 {title}")
        
        try:
            # Tentar ir direto para o play (padrão comum)
            # URL guess: /series/category/X/Y/play/Z/ onde Z é episode_id
            # Vamos tentar episode_id = 1 primeiro
            
            play_url = f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/play/1/"
            logger.info(f"   🌐 Tentando: {play_url}")
            
            self.page.goto(play_url, timeout=15000)
            time.sleep(5)
            
            # Verificar se carregou player
            video_url = self.page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (v && v.src) return v.src;
                    
                    const sources = v ? v.querySelectorAll('source') : [];
                    for (let s of sources) if (s.src) return s.src;
                    
                    const iframes = document.querySelectorAll('iframe');
                    for (let f of iframes) if (f.src) return f.src;
                    
                    return null;
                }
            """)
            
            if video_url:
                logger.info(f"   ✅ Vídeo: {video_url[:60]}...")
                return {
                    'title': title,
                    'series_id': series_id,
                    'video_url': video_url
                }
            
            # Se não achou, tentar navegar pela página info
            logger.info("   🔍 Tentando pela página info...")
            self.page.goto(f"{BASE_URL}/#/series/category/{cat_id}/{series_id}/info/", timeout=15000)
            time.sleep(4)
            
            # Clicar no primeiro elemento que pareça episódio/play
            clickable = self.page.locator("a, button").all()
            for elem in clickable:
                try:
                    text = elem.inner_text().strip().lower()
                    if any(x in text for x in ['play', 'assistir', 'ep', 'cap', '▶']):
                        elem.click()
                        time.sleep(5)
                        
                        # Verificar se carregou vídeo
                        video_url = self.page.evaluate("""
                            () => {
                                const v = document.querySelector('video');
                                if (v && v.src) return v.src;
                                const sources = v ? v.querySelectorAll('source') : [];
                                for (let s of sources) if (s.src) return s.src;
                                return null;
                            }
                        """)
                        
                        if video_url:
                            logger.info(f"   ✅ Vídeo (via click): {video_url[:60]}...")
                            return {
                                'title': title,
                                'series_id': series_id,
                                'video_url': video_url
                            }
                        break
                except:
                    continue
            
            logger.warning("   ❌ Vídeo não encontrado")
            return None
            
        except Exception as e:
            logger.error(f"   💥 Erro: {e}")
            return None
    
    def run(self, max_series=10):
        """Executa o scraper completo"""
        logger.info("="*70)
        logger.info("🚀 SERIES SCRAPER - Versão Final")
        logger.info("="*70)
        
        self.start()
        
        try:
            if not self.login():
                return
            
            # Descobrir categorias
            logger.info("\n📂 Descobrindo categorias...")
            self.page.goto(f"{BASE_URL}/#/series/", timeout=30000)
            time.sleep(3)
            
            cats = self.page.locator("a[href*='/series/category/']").all()
            category_ids = set()
            for c in cats:
                try:
                    href = c.get_attribute("href")
                    match = re.search(r'/series/category/(\d+)', href)
                    if match:
                        category_ids.add(match.group(1))
                except:
                    pass
            
            logger.info(f"✅ {len(category_ids)} categorias: {sorted(category_ids)[:5]}")
            
            # Extrair séries
            all_series = []
            for cat_id in sorted(category_ids)[:2]:  # Limitar a 2 categorias
                series = self.extract_series_from_category(cat_id, max_series=5)
                all_series.extend(series)
            
            logger.info(f"\n📊 Total: {len(all_series)} séries")
            
            # Extrair vídeos
            results = []
            for i, s in enumerate(all_series[:max_series], 1):
                logger.info(f"\n{'='*70}")
                logger.info(f"[{i}/{min(len(all_series), max_series)}]")
                
                result = self.extract_video_from_series(s)
                if result:
                    try:
                        save_embed(
                            title=result['title'],
                            embed_url=result['video_url'],
                            tmdb_id=str(result['series_id']),
                            original_raw_title=result['title']
                        )
                        logger.info("   💾 Salvo no banco!")
                        results.append(result)
                    except Exception as e:
                        logger.error(f"   ❌ Erro ao salvar: {e}")
                
                time.sleep(2)
            
            # Resumo
            logger.info(f"\n{'='*70}")
            logger.info("✅ COMPLETO!")
            logger.info(f"{'='*70}")
            logger.info(f"Séries adicionadas: {len(results)}")
            
        except Exception as e:
            logger.error(f"\n💥 Erro fatal: {e}")
        finally:
            self.stop()


def main():
    scraper = SeriesScraper()
    scraper.run(max_series=5)  # Começar com pouco para testar


if __name__ == "__main__":
    main()
