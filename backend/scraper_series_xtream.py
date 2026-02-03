#!/usr/bin/env python3
"""
Scraper de Séries via API Xtream Codes
Extrai todas as séries da API do jt0x
"""

import sqlite3
import os
import sys
import time
import json
import requests
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "links.db")
BASE_API = "http://jt0x.com/player_api.php"
USERNAME = "t2TGgarYJ"
PASSWORD = "66e74xKRJ"

# URL base para streams de séries
# Formato: http://jt0x.com:80/series/{username}/{password}/{stream_id}.mp4
SERIES_STREAM_BASE = f"http://jt0x.com:80/series/{USERNAME}/{PASSWORD}"


def init_db():
    """Inicializa o banco de dados se necessário"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela de séries
    c.execute('''CREATE TABLE IF NOT EXISTS series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opera_id TEXT,
        tmdb_id TEXT,
        title TEXT NOT NULL,
        overview TEXT,
        poster_path TEXT,
        backdrop_path TEXT,
        year TEXT,
        genres TEXT,
        rating REAL,
        status TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tabela de temporadas
    c.execute('''CREATE TABLE IF NOT EXISTS seasons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        series_id INTEGER,
        season_number INTEGER,
        title TEXT,
        overview TEXT,
        poster_path TEXT,
        episode_count INTEGER,
        air_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (series_id) REFERENCES series(id)
    )''')
    
    # Tabela de episódios
    c.execute('''CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season_id INTEGER,
        series_id INTEGER,
        episode_number INTEGER,
        title TEXT,
        overview TEXT,
        still_path TEXT,
        video_url TEXT,
        video_type TEXT,
        duration INTEGER,
        air_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (season_id) REFERENCES seasons(id),
        FOREIGN KEY (series_id) REFERENCES series(id)
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado")


def api_request(action, **params):
    """Faz uma requisição à API Xtream Codes"""
    url = f"{BASE_API}?username={USERNAME}&password={PASSWORD}&action={action}"
    for key, value in params.items():
        url += f"&{key}={value}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Erro na API: {e}")
        return None


def get_all_series():
    """Obtém lista de todas as séries"""
    print("📺 Buscando todas as séries...")
    data = api_request("get_series")
    if not data:
        return []
    print(f"✅ {len(data)} séries encontradas")
    return data


def get_series_info(series_id):
    """Obtém informações detalhadas de uma série"""
    data = api_request("get_series_info", series_id=series_id)
    return data


def extract_series_data(series_list, max_series=None):
    """Extrai dados completos das séries"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    total_episodes = 0
    series_count = 0
    
    for series in series_list[:max_series] if max_series else series_list:
        series_id = series.get("series_id")
        title = series.get("name", "Sem Título")
        
        print(f"\n{'='*60}")
        print(f"📺 [{series_count + 1}] {title}")
        print(f"   ID: {series_id}")
        
        # Verificar se série já existe
        c.execute("SELECT id FROM series WHERE opera_id = ?", (str(series_id),))
        existing = c.fetchone()
        if existing:
            print(f"   ⚠️  Série já existe, pulando...")
            continue
        
        # Buscar info detalhada
        info = get_series_info(series_id)
        if not info:
            print(f"   ❌ Erro ao buscar info")
            continue
        
        # Inserir série
        poster = series.get("cover", "")
        backdrop_path = series.get("backdrop_path", [])
        if isinstance(backdrop_path, list) and len(backdrop_path) > 0:
            backdrop = backdrop_path[0]
        elif isinstance(backdrop_path, str):
            backdrop = backdrop_path
        else:
            backdrop = ""
        year = str(series.get("year", ""))
        genres = ", ".join(series.get("genre", [])) if isinstance(series.get("genre"), list) else series.get("genre", "")
        rating = series.get("rating", 0)
        plot = series.get("plot", "")
        
        c.execute("""
            INSERT INTO series (opera_id, title, overview, poster_path, backdrop_path, year, genres, rating, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(series_id), title, plot, poster, backdrop, year, genres, rating, "active"))
        
        db_series_id = c.lastrowid
        
        # Processar episódios
        episodes = info.get("episodes", {})
        if not episodes:
            print(f"   ⚠️  Sem episódios")
            conn.commit()
            continue
        
        for season_num, eps in episodes.items():
            season_int = int(season_num) if season_num.isdigit() else 0
            
            print(f"   📁 Temporada {season_int}: {len(eps)} episódios")
            
            # Inserir temporada
            c.execute("""
                INSERT INTO seasons (series_id, season_number, episode_count)
                VALUES (?, ?, ?)
            """, (db_series_id, season_int, len(eps)))
            
            db_season_id = c.lastrowid
            
            # Inserir episódios
            for ep in eps:
                ep_num = ep.get("episode_num", 0)
                ep_title = ep.get("title", f"Episódio {ep_num}")
                stream_id = ep.get("id")
                container = ep.get("container_extension", "mp4")
                
                # URL do vídeo (formato Xtream Codes)
                video_url = f"{SERIES_STREAM_BASE}/{stream_id}.{container}"
                
                # Info adicional
                ep_info = ep.get("info", {})
                still_path = ep_info.get("movie_image", "")
                duration = ep_info.get("duration_secs", 0)
                air_date = ep_info.get("release_date", "")
                ep_plot = ep_info.get("plot", "")
                
                # Verificar se episódio já existe
                c.execute("""
                    SELECT id FROM episodes 
                    WHERE series_id = ? AND season_id = ? AND episode_number = ?
                """, (db_series_id, db_season_id, ep_num))
                
                if c.fetchone():
                    # Atualizar episódio existente
                    c.execute("""
                        UPDATE episodes SET
                            title = ?, overview = ?, still_path = ?, video_url = ?,
                            video_type = ?, duration = ?, air_date = ?
                        WHERE series_id = ? AND season_id = ? AND episode_number = ?
                    """, (ep_title, ep_plot, still_path, video_url, "mp4", duration, air_date,
                          db_series_id, db_season_id, ep_num))
                else:
                    # Inserir novo episódio
                    c.execute("""
                        INSERT INTO episodes 
                        (season_id, series_id, episode_number, title, overview, still_path, 
                         video_url, video_type, duration, air_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (db_season_id, db_series_id, ep_num, ep_title, ep_plot, still_path,
                          video_url, "mp4", duration, air_date))
                
                total_episodes += 1
        
        conn.commit()
        series_count += 1
        print(f"   ✅ Série salva (DB ID: {db_series_id})")
        
        # Delay para não sobrecarregar a API
        time.sleep(0.5)
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ SCRAPER COMPLETO!")
    print(f"   Séries: {series_count}")
    print(f"   Episódios: {total_episodes}")
    
    return series_count, total_episodes


def main():
    print("="*60)
    print("🚀 SCRAPER DE SÉRIES - API XTREAM CODES")
    print("="*60)
    
    # Inicializar banco
    init_db()
    
    # Buscar todas as séries
    series_list = get_all_series()
    if not series_list:
        print("❌ Nenhuma série encontrada")
        return
    
    # Extrair todas as séries
    total_series = len(series_list)
    print(f"\n⚙️  Iniciando extração de {total_series} séries...")
    extract_series_data(series_list, max_series=None)


if __name__ == "__main__":
    main()
