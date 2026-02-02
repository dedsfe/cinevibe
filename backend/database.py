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
                original_raw_title TEXT,
                embed_url TEXT,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                poster_path TEXT,
                backdrop_path TEXT,
                overview TEXT,
                repair_attempts INTEGER DEFAULT 0,
                last_repair_date DATETIME
            )"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS catalog_raw (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_title TEXT UNIQUE,
                year TEXT,
                video_url TEXT,
                detail_url TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
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


def save_embed(
    title: str,
    embed_url: str,
    tmdb_id: Optional[str] = None,
    poster_path: str = None,
    backdrop_path: str = None,
    overview: str = None,
    original_raw_title: str = None,
):
    with get_conn() as conn:
        c = conn.cursor()

        # Check if we should update an existing record (preserving data if new is None)
        c.execute(
            "SELECT tmdb_id, poster_path, backdrop_path, overview, original_raw_title FROM links WHERE title = ?",
            (title,),
        )
        existing = c.fetchone()

        if existing:
            tmdb_id = tmdb_id or existing[0]
            poster_path = poster_path or existing[1]
            backdrop_path = backdrop_path or existing[2]
            overview = overview or existing[3]
            original_raw_title = original_raw_title or existing[4]

            c.execute(
                """UPDATE links SET 
                   tmdb_id = ?, embed_url = ?, added_at = ?, 
                   poster_path = ?, backdrop_path = ?, overview = ?, 
                   original_raw_title = ?
                   WHERE title = ?""",
                (
                    tmdb_id,
                    embed_url,
                    datetime.utcnow(),
                    poster_path,
                    backdrop_path,
                    overview,
                    original_raw_title,
                    title,
                ),
            )
        else:
            c.execute(
                """INSERT INTO links 
                   (tmdb_id, title, embed_url, added_at, poster_path, backdrop_path, overview, original_raw_title) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tmdb_id,
                    title,
                    embed_url,
                    datetime.utcnow(),
                    poster_path,
                    backdrop_path,
                    overview,
                    original_raw_title,
                ),
            )
        conn.commit()


def get_cache_count():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM links")
        row = c.fetchone()
        total = row[0] if row else 0
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


def get_cached_statuses(tmdb_ids: list) -> dict:
    """
    Returns a dictionary of {tmdb_id: embed_url} for the given IDs.
    """
    if not tmdb_ids:
        return {}

    formatted_ids = [str(tid) for tid in tmdb_ids]
    placeholders = ",".join("?" for _ in formatted_ids)

    with get_conn() as conn:
        c = conn.cursor()
        query = (
            f"SELECT tmdb_id, embed_url FROM links WHERE tmdb_id IN ({placeholders})"
        )
        c.execute(query, formatted_ids)
        rows = c.fetchall()
        return {str(row["tmdb_id"]): row["embed_url"] for row in rows}


def get_catalog_movies(limit=100, offset=0):
    """Retrieve enriched movies from the catalog (links table) locally."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            """
            SELECT tmdb_id, title, embed_url, poster_path, backdrop_path, overview
            FROM links
            WHERE embed_url IS NOT NULL
              AND embed_url != 'NOT_FOUND'
            ORDER BY added_at DESC
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )
        rows = c.fetchall()

        movies = []
        for row in rows:
            # Use tmdb_id if available, otherwise generate ID from embed_url or title
            movie_id = row["tmdb_id"]
            if not movie_id:
                # Extract ID from embed_url (e.g., .../217376.mp4 -> 217376)
                import re

                match = re.search(r"/(\d+)\.mp4", row["embed_url"] or "")
                if match:
                    movie_id = match.group(1)
                else:
                    # Fallback: use title hash
                    movie_id = str(hash(row["title"]) % 10000000)

            movies.append(
                {
                    "id": movie_id,
                    "title": row["title"],
                    "poster_path": row["poster_path"],
                    "backdrop_path": row["backdrop_path"],
                    "overview": row["overview"],
                    "isAvailable": row["embed_url"] != "NOT_FOUND",
                    "embedUrl": row["embed_url"],
                }
            )
        return movies
