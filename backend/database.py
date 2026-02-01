import sqlite3
from datetime import datetime
import os
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "links.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tmdb_id TEXT,
                title TEXT UNIQUE,
                embed_url TEXT,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.commit()


def get_cached_embed(title: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT embed_url FROM links WHERE title = ?", (title,))
        row = c.fetchone()
        return row[0] if row else None


def get_cached_embed_by_id(tmdb_id: str):
    if not tmdb_id:
        return None
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT embed_url FROM links WHERE tmdb_id = ?", (str(tmdb_id),))
        row = c.fetchone()
        return row[0] if row else None


def save_embed(title: str, embed_url: str, tmdb_id: Optional[str] = None):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO links (tmdb_id, title, embed_url, added_at) VALUES (?, ?, ?, ?)",
            (tmdb_id, title, embed_url, datetime.utcnow()),
        )
        conn.commit()


def get_cache_count():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM links")
        row = c.fetchone()
        total = row[0] if row else 0
        # For educational purposes, tmdb_items mirrors cached_links
        return {"cached_links": total, "tmdb_items": total}


def get_cached_ids(tmdb_ids: list) -> list:
    """
    Returns a list of tmdb_ids that are present in the links table.
    """
    if not tmdb_ids:
        return []
        
    formatted_ids = [str(tid) for tid in tmdb_ids]
    placeholders = ",".join("?" for _ in formatted_ids)
    
    with get_conn() as conn:
        c = conn.cursor()
        query = f"SELECT tmdb_id FROM links WHERE tmdb_id IN ({placeholders})"
        c.execute(query, formatted_ids)
        rows = c.fetchall()
        return [row[0] for row in rows]
