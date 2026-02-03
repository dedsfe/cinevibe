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


# ==================== SERIES FUNCTIONS ====================

def get_catalog_series(limit=100, offset=0):
    """Retrieve series from the database (only series with at least 1 episode)."""
    with get_conn() as conn:
        c = conn.cursor()
        # Only return series that have at least 1 episode
        c.execute(
            """
            SELECT s.id, s.opera_id, s.tmdb_id, s.title, s.overview, s.poster_path, 
                   s.backdrop_path, s.year, s.genres, s.rating, s.status
            FROM series s
            WHERE s.status = 'active'
              AND EXISTS (
                  SELECT 1 FROM episodes e 
                  WHERE e.series_id = s.id 
                  LIMIT 1
              )
            ORDER BY s.created_at DESC
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )
        rows = c.fetchall()

        series = []
        for row in rows:
            series.append(
                {
                    "id": row["id"],
                    "opera_id": row["opera_id"],
                    "tmdb_id": row["tmdb_id"],
                    "title": row["title"],
                    "overview": row["overview"],
                    "poster_path": row["poster_path"],
                    "backdrop_path": row["backdrop_path"],
                    "year": row["year"],
                    "genres": row["genres"],
                    "rating": row["rating"],
                }
            )
        return series


def get_series_seasons(series_id):
    """Get all seasons for a series."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT id, season_number, title, overview, poster_path, episode_count, air_date
            FROM seasons
            WHERE series_id = ?
            ORDER BY season_number
        """,
            (series_id,),
        )
        rows = c.fetchall()

        seasons = []
        for row in rows:
            seasons.append(
                {
                    "id": row["id"],
                    "season_number": row["season_number"],
                    "title": row["title"],
                    "overview": row["overview"],
                    "poster_path": row["poster_path"],
                    "episode_count": row["episode_count"],
                    "air_date": row["air_date"],
                }
            )
        return seasons


def get_season_episodes(season_id):
    """Get all episodes for a season."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT id, episode_number, title, overview, still_path, video_url,
                   video_type, duration, air_date
            FROM episodes
            WHERE season_id = ?
            ORDER BY episode_number
        """,
            (season_id,),
        )
        rows = c.fetchall()

        episodes = []
        for row in rows:
            episodes.append(
                {
                    "id": row["id"],
                    "episode_number": row["episode_number"],
                    "title": row["title"],
                    "overview": row["overview"],
                    "still_path": row["still_path"],
                    "video_url": row["video_url"],
                    "video_type": row["video_type"],
                    "duration": row["duration"],
                    "air_date": row["air_date"],
                }
            )
        return episodes


def get_series_by_id(series_id):
    """Get a single series by ID."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT id, opera_id, tmdb_id, title, overview, poster_path, backdrop_path,
                   year, genres, rating, status
            FROM series
            WHERE id = ?
        """,
            (series_id,),
        )
        row = c.fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "opera_id": row["opera_id"],
            "tmdb_id": row["tmdb_id"],
            "title": row["title"],
            "overview": row["overview"],
            "poster_path": row["poster_path"],
            "backdrop_path": row["backdrop_path"],
            "year": row["year"],
            "genres": row["genres"],
            "rating": row["rating"],
        }


def get_series_count():
    """Get total count of series (only series with at least 1 episode)."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM series s
            WHERE s.status = 'active'
              AND EXISTS (
                  SELECT 1 FROM episodes e 
                  WHERE e.series_id = s.id 
                  LIMIT 1
              )
        """)
        row = c.fetchone()
        return row[0] if row else 0


# ==================== USERS & AUTH ====================

def init_users_table():
    """Initialize users table for authentication."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        conn.commit()


def create_user(username, password_hash, name=None, is_admin=False):
    """Create a new user."""
    with get_conn() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password_hash, name, is_admin) VALUES (?, ?, ?, ?)",
                (username, password_hash, name, 1 if is_admin else 0)
            )
            conn.commit()
            return c.lastrowid
        except sqlite3.IntegrityError:
            return None


def get_user_by_username(username):
    """Get user by username."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, username, password_hash, name, is_admin, created_at FROM users WHERE username = ?",
            (username,)
        )
        row = c.fetchone()
        if row:
            return {
                "id": row["id"],
                "username": row["username"],
                "password_hash": row["password_hash"],
                "name": row["name"],
                "is_admin": bool(row["is_admin"]),
                "created_at": row["created_at"]
            }
        return None


def update_last_login(user_id):
    """Update user's last login timestamp."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        conn.commit()


def get_all_users():
    """Get all users (for admin)."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, username, name, is_admin, created_at, last_login FROM users ORDER BY created_at DESC"
        )
        rows = c.fetchall()
        return [
            {
                "id": row["id"],
                "username": row["username"],
                "name": row["name"],
                "is_admin": bool(row["is_admin"]),
                "created_at": row["created_at"],
                "last_login": row["last_login"]
            }
            for row in rows
        ]


def delete_user(user_id):
    """Delete a user."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return c.rowcount > 0


# ==================== MY LIST ====================

def add_to_my_list_movies(user_id, movie_data):
    """Add movie to user's list."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS my_list_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id TEXT,
                title TEXT,
                poster_path TEXT,
                backdrop_path TEXT,
                overview TEXT,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, movie_id)
            )
        ''')
        try:
            c.execute('''
                INSERT INTO my_list_movies (user_id, movie_id, title, poster_path, backdrop_path, overview)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, str(movie_data.get('id')), movie_data.get('title'), 
                  movie_data.get('poster_path'), movie_data.get('backdrop_path'), movie_data.get('overview')))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def remove_from_my_list_movies(user_id, movie_id):
    """Remove movie from user's list."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM my_list_movies WHERE user_id = ? AND movie_id = ?", (user_id, str(movie_id)))
        conn.commit()
        return c.rowcount > 0


def get_my_list_movies(user_id):
    """Get user's movie list."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS my_list_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_id TEXT,
                title TEXT,
                poster_path TEXT,
                backdrop_path TEXT,
                overview TEXT,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, movie_id)
            )
        ''')
        c.execute('''
            SELECT movie_id, title, poster_path, backdrop_path, overview
            FROM my_list_movies
            WHERE user_id = ?
            ORDER BY added_at DESC
        ''', (user_id,))
        rows = c.fetchall()
        return [
            {
                "id": row["movie_id"],
                "title": row["title"],
                "poster_path": row["poster_path"],
                "backdrop_path": row["backdrop_path"],
                "overview": row["overview"],
                "media_type": "movie"
            }
            for row in rows
        ]


def add_to_my_list_series(user_id, series_id):
    """Add series to user's list."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS my_list_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                series_id INTEGER,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (series_id) REFERENCES series(id),
                UNIQUE(user_id, series_id)
            )
        ''')
        try:
            c.execute('''
                INSERT INTO my_list_series (user_id, series_id)
                VALUES (?, ?)
            ''', (user_id, series_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def remove_from_my_list_series(user_id, series_id):
    """Remove series from user's list."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM my_list_series WHERE user_id = ? AND series_id = ?", (user_id, series_id))
        conn.commit()
        return c.rowcount > 0


def get_my_list_series(user_id):
    """Get user's series list with full details."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS my_list_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                series_id INTEGER,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (series_id) REFERENCES series(id),
                UNIQUE(user_id, series_id)
            )
        ''')
        c.execute('''
            SELECT s.id, s.opera_id, s.title, s.overview, s.poster_path, s.backdrop_path, s.year, s.genres, s.rating
            FROM my_list_series mls
            JOIN series s ON mls.series_id = s.id
            WHERE mls.user_id = ?
            ORDER BY mls.added_at DESC
        ''', (user_id,))
        rows = c.fetchall()
        return [
            {
                "id": row["id"],
                "opera_id": row["opera_id"],
                "title": row["title"],
                "overview": row["overview"],
                "poster_path": row["poster_path"],
                "backdrop_path": row["backdrop_path"],
                "year": row["year"],
                "genres": row["genres"],
                "rating": row["rating"],
                "media_type": "tv",
                "isLocalSeries": True
            }
            for row in rows
        ]


def is_in_my_list_movies(user_id, movie_id):
    """Check if movie is in user's list."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM my_list_movies WHERE user_id = ? AND movie_id = ?", (user_id, str(movie_id)))
        return c.fetchone() is not None


def is_in_my_list_series(user_id, series_id):
    """Check if series is in user's list."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM my_list_series WHERE user_id = ? AND series_id = ?", (user_id, series_id))
        return c.fetchone() is not None
