#!/usr/bin/env python3
"""
Database Schema para Séries
Cria tabelas: series, seasons, episodes
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_FILE_PATH", os.path.join(os.path.dirname(__file__), "links.db"))


def get_conn():
    # Ensure directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_series_tables():
    """Cria tabelas para séries"""
    with get_conn() as conn:
        c = conn.cursor()
        
        # Tabela de Séries
        c.execute("""
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opera_id TEXT UNIQUE,
                title TEXT NOT NULL,
                overview TEXT,
                poster_path TEXT,
                backdrop_path TEXT,
                tmdb_id TEXT,
                category_id TEXT,
                year INTEGER,
                genres TEXT,
                rating REAL,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de Temporadas
        c.execute("""
            CREATE TABLE IF NOT EXISTS seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL,
                season_number INTEGER NOT NULL,
                title TEXT,
                overview TEXT,
                poster_path TEXT,
                episode_count INTEGER DEFAULT 0,
                air_date TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (series_id) REFERENCES series(id),
                UNIQUE(series_id, season_number)
            )
        """)
        
        # Tabela de Episódios
        c.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_id INTEGER NOT NULL,
                series_id INTEGER NOT NULL,
                episode_number INTEGER NOT NULL,
                title TEXT,
                overview TEXT,
                still_path TEXT,
                video_url TEXT,
                video_type TEXT DEFAULT 'mp4',
                duration INTEGER,
                air_date TEXT,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (season_id) REFERENCES seasons(id),
                FOREIGN KEY (series_id) REFERENCES series(id),
                UNIQUE(series_id, season_id, episode_number)
            )
        """)
        
        # Índices para performance
        c.execute("CREATE INDEX IF NOT EXISTS idx_series_opera_id ON series(opera_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_series_tmdb ON series(tmdb_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_seasons_series ON seasons(series_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_episodes_season ON episodes(season_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_episodes_series ON episodes(series_id)")
        
        conn.commit()
        print("✅ Tabelas de séries criadas com sucesso!")


def save_series(opera_id, title, overview=None, poster_path=None, backdrop_path=None,
                tmdb_id=None, category_id=None, year=None, genres=None, rating=None):
    """Salva ou atualiza uma série"""
    with get_conn() as conn:
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO series (opera_id, title, overview, poster_path, backdrop_path,
                               tmdb_id, category_id, year, genres, rating, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(opera_id) DO UPDATE SET
                title=excluded.title,
                overview=excluded.overview,
                poster_path=excluded.poster_path,
                backdrop_path=excluded.backdrop_path,
                tmdb_id=excluded.tmdb_id,
                category_id=excluded.category_id,
                year=excluded.year,
                genres=excluded.genres,
                rating=excluded.rating,
                updated_at=excluded.updated_at
            RETURNING id
        """, (opera_id, title, overview, poster_path, backdrop_path, 
              tmdb_id, category_id, year, genres, rating, datetime.utcnow()))
        
        result = c.fetchone()
        conn.commit()
        return result[0] if result else None


def save_season(series_id, season_number, title=None, overview=None, 
                poster_path=None, episode_count=0, air_date=None):
    """Salva ou atualiza uma temporada"""
    with get_conn() as conn:
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO seasons (series_id, season_number, title, overview, 
                                poster_path, episode_count, air_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(series_id, season_number) DO UPDATE SET
                title=excluded.title,
                overview=excluded.overview,
                poster_path=excluded.poster_path,
                episode_count=excluded.episode_count,
                air_date=excluded.air_date
            RETURNING id
        """, (series_id, season_number, title, overview, poster_path, episode_count, air_date))
        
        result = c.fetchone()
        conn.commit()
        return result[0] if result else None


def save_episode(series_id, season_id, episode_number, title=None, overview=None,
                 still_path=None, video_url=None, video_type='mp4', duration=None, air_date=None):
    """Salva ou atualiza um episódio"""
    with get_conn() as conn:
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO episodes (series_id, season_id, episode_number, title, overview,
                                 still_path, video_url, video_type, duration, air_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(series_id, season_id, episode_number) DO UPDATE SET
                title=excluded.title,
                overview=excluded.overview,
                still_path=excluded.still_path,
                video_url=excluded.video_url,
                video_type=excluded.video_type,
                duration=excluded.duration,
                air_date=excluded.air_date
            RETURNING id
        """, (series_id, season_id, episode_number, title, overview, 
              still_path, video_url, video_type, duration, air_date))
        
        result = c.fetchone()
        conn.commit()
        return result[0] if result else None


def get_series_with_episodes():
    """Retorna séries com contagem de episódios"""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT s.*, COUNT(e.id) as episode_count
            FROM series s
            LEFT JOIN episodes e ON e.series_id = s.id
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """)
        return [dict(row) for row in c.fetchall()]


def get_series_episodes(series_id):
    """Retorna episódios de uma série"""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT e.*, se.season_number
            FROM episodes e
            JOIN seasons se ON e.season_id = se.id
            WHERE e.series_id = ?
            ORDER BY se.season_number, e.episode_number
        """, (series_id,))
        return [dict(row) for row in c.fetchall()]


def search_series_locally(query: str, limit=50):
    """Search for series in the local database."""
    if not query:
        return []

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            """
            SELECT id, title, overview, poster_path, backdrop_path, tmdb_id, year, rating
            FROM series
            WHERE title LIKE ?
            ORDER BY 
              CASE WHEN title LIKE ? THEN 1 ELSE 2 END,
              created_at DESC
            LIMIT ?
        """,
            (f"%{query}%", f"{query}%", limit),
        )
        rows = c.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row["tmdb_id"] or row["id"],
                    "title": row["title"],
                    "poster_path": row["poster_path"],
                    "backdrop_path": row["backdrop_path"],
                    "overview": row["overview"],
                    "release_date": str(row["year"]) if row["year"] else "",
                    "media_type": "tv",
                    "vote_average": row["rating"],
                    "isAvailable": True,
                }
            )
        return results


def get_stats():
    """Retorna estatísticas do banco"""
    with get_conn() as conn:
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM series")
        series_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM seasons")
        seasons_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM episodes WHERE video_url IS NOT NULL")
        episodes_count = c.fetchone()[0]
        
        return {
            'series': series_count,
            'seasons': seasons_count,
            'episodes': episodes_count
        }


if __name__ == "__main__":
    print("🗄️  Configurando banco de séries...")
    print("="*50)
    
    init_series_tables()
    
    print("\n📊 Estatísticas:")
    stats = get_stats()
    print(f"   Séries: {stats['series']}")
    print(f"   Temporadas: {stats['seasons']}")
    print(f"   Episódios: {stats['episodes']}")
    
    print("\n✅ Pronto!")
