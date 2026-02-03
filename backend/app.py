from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import threading
from datetime import datetime, timedelta
from functools import wraps

# Password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# Local modules (to be created below in this patch)
from database import (
    init_db,
    init_users_table,
    get_cached_embed,
    get_cached_embed_by_id,
    save_embed,
    get_cache_count,
    get_cached_ids,
    get_cached_statuses,
    get_catalog_movies,
    get_catalog_series,
    get_series_seasons,
    get_season_episodes,
    get_series_by_id,
    get_series_count,
    create_user,
    get_user_by_username,
    update_last_login,
    get_all_users,
    delete_user,
    add_to_my_list_movies,
    remove_from_my_list_movies,
    get_my_list_movies,
    add_to_my_list_series,
    remove_from_my_list_series,
    get_my_list_series,
    is_in_my_list_movies,
    is_in_my_list_series,
)
from scraper import scrape_for_title
from validator import validate_embed
from bulk_scrape_tmdb import run_bulk_scrape, get_scraper_state

# Simple token storage (in production use JWT or sessions)
# Format: {token: {user_id, expires}}
active_tokens = {}

def generate_token(user_id):
    """Generate a simple token for user session."""
    import secrets
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=7)  # 7 days
    active_tokens[token] = {"user_id": user_id, "expires": expires}
    return token

def verify_token(token):
    """Verify if token is valid and return user_id."""
    if not token or token not in active_tokens:
        return None
    session = active_tokens[token]
    if datetime.utcnow() > session["expires"]:
        del active_tokens[token]
        return None
    return session["user_id"]

def require_auth(f):
    """Decorator to require authentication (DISABLED)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # BYPASS AUTH: Always allow and pass dummy user_id=1
        dummy_user_id = 1
        return f(dummy_user_id, *args, **kwargs)
    return decorated

app = Flask(__name__)
# Enable CORS for all origins (frontend can be on Vercel, Railway, etc.)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
})

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = app.make_response(("", 204))
        origin = request.headers.get("Origin", "*")
        response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        response.headers.add("Vary", "Origin")
        return response

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin:
        response.headers.add("Access-Control-Allow-Origin", origin)
    else:
        response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    return response

# Initialize database on startup
init_db()
init_users_table()

# Create default admin user if no users exist
def create_default_admin():
    users = get_all_users()
    if not users:
        password_hash = generate_password_hash("admin123")
        create_user("admin", password_hash, "Administrador", is_admin=True)
        print("✅ Usuário admin criado: admin / admin123")
        print("   ⚠️  Por segurança, altere a senha após o primeiro login!")

create_default_admin()


@app.route("/api/health", methods=["GET"])
def health():
    try:
        # Check database connection
        from database import get_series_count, get_cache_count
        series_count = get_series_count()
        movie_count = get_cache_count().get("cached_links", 0)
        
        return jsonify({
            "status": "ok",
            "database": {
                "series": series_count,
                "movies": movie_count
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    stats = get_cache_count()
    return jsonify(
        {
            "cached_links": stats.get("cached_links", 0),
            "tmdb_items": stats.get("tmdb_items", 0),
        }
    )


@app.route("/api/cache/check-batch", methods=["POST"])
def check_cache_batch():
    data = request.get_json(force=True) or {}
    tmdb_ids = data.get("tmdbIds", [])

    if not tmdb_ids:
        return jsonify({"statuses": {}})

    statuses = get_cached_statuses(tmdb_ids)
    return jsonify({"statuses": statuses})


@app.route("/api/scraper/status", methods=["GET"])
def scraper_status():
    return jsonify(get_scraper_state())


@app.route("/api/catalog", methods=["GET"])
def get_catalog():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    movies = get_catalog_movies(limit, offset)
    return jsonify({"results": movies})


@app.route("/api/get-embed", methods=["POST"])
def get_embed():
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    tmdb_id = data.get("tmdbId")
    year = data.get("year")

    if not title:
        return jsonify({"error": "Título é obrigatório"}), 400

    # 1) Check cache by ID first (Most accurate)
    if tmdb_id:
        cached_by_id = get_cached_embed_by_id(tmdb_id)
        if cached_by_id and validate_embed(cached_by_id):
            return jsonify({"embedUrl": cached_by_id, "cached": True})

    # 2) Fallback to Title cache
    cached = get_cached_embed(title)
    if cached:
        if validate_embed(cached):
            return jsonify({"embedUrl": cached, "cached": True})
        # if cache exists but invalid, continue to scrape

    # 3) On-demand scrape from legal sources
    embed = scrape_for_title(title, tmdb_id, year=year)
    if embed and validate_embed(embed):
        save_embed(title, embed, tmdb_id)
        return jsonify({"embedUrl": embed, "cached": False})

    return jsonify({"error": "Embed não encontrado"}), 404


@app.route("/api/scrape-background", methods=["POST"])
def scrape_background():
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    tmdb_id = data.get("tmdbId")

    if not title:
        return jsonify({"error": "Título é obrigatório"}), 400

    def background_task(t, tid):
        logging.info(f"Starting background scrape for: {t}")
        try:
            # We don't have year in background task yet, but scraping might infer it or just use title
            embed = scrape_for_title(t, tid)
            if embed and validate_embed(embed):
                save_embed(t, embed, tid)
                logging.info(f"Background scrape success for: {t}")
            else:
                logging.warning(f"Background scrape found nothing for: {t}")
        except Exception as e:
            logging.error(f"Background scrape failed for {t}: {e}")

    # Start thread
    thread = threading.Thread(target=background_task, args=(title, tmdb_id))
    thread.start()

    return jsonify({"status": "processing", "message": f"Scraping started for {title}"})


@app.route("/api/verify-link", methods=["POST"])
def verify_link():
    """Verifica se o link de um filme está correto"""
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    current_url = data.get("currentUrl")

    if not title:
        return jsonify({"error": "Título é obrigatório"}), 400

    from strict_opera_scraper import StrictOperaScraper

    scraper = StrictOperaScraper()

    try:
        scraper.start_session(headless=True)
        result = scraper.scrape_with_validation(title)

        # Compare with current URL
        is_correct = False
        if current_url and result["success"]:
            current_id = scraper._extract_video_id(current_url)
            new_id = result["video_id"]
            is_correct = current_id == new_id

        return jsonify(
            {
                "title": title,
                "current_url": current_url,
                "is_correct": is_correct,
                "scraped_result": {
                    "success": result["success"],
                    "video_url": result["video_url"],
                    "video_id": result["video_id"],
                    "scraped_title": result["scraped_title"],
                    "similarity": result["similarity"],
                    "validation_passed": result["validation_passed"],
                    "error": result["error"],
                },
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        scraper.stop_session()


@app.route("/api/fix-link", methods=["POST"])
def fix_link():
    """Corrige o link de um filme"""
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    tmdb_id = data.get("tmdbId")

    if not title:
        return jsonify({"error": "Título é obrigatório"}), 400

    from strict_opera_scraper import StrictOperaScraper

    scraper = StrictOperaScraper()

    try:
        scraper.start_session(headless=True)
        result = scraper.scrape_with_validation(title)

        if result["success"] and result["validation_passed"]:
            # Save to database
            save_embed(title, result["video_url"], tmdb_id)

            return jsonify(
                {
                    "success": True,
                    "message": f"Link corrigido para {title}",
                    "video_url": result["video_url"],
                    "video_id": result["video_id"],
                    "similarity": result["similarity"],
                }
            )
        else:
            return jsonify(
                {"success": False, "error": result["error"] or "Falha na validação"}
            ), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        scraper.stop_session()


@app.route("/api/integrity-stats", methods=["GET"])
def integrity_stats():
    """Retorna estatísticas de integridade do catálogo"""
    from database import get_conn

    conn = get_conn()
    c = conn.cursor()

    # Count by type
    c.execute("SELECT COUNT(*) FROM links WHERE embed_url IS NOT NULL")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM links WHERE embed_url != 'NOT_FOUND'")
    with_links = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM links WHERE embed_url = 'NOT_FOUND'")
    not_found = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM links WHERE embed_url LIKE '%jt0x.com%'")
    opera_links = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM links WHERE embed_url LIKE '%youtube%'")
    youtube_links = c.fetchone()[0]

    conn.close()

    return jsonify(
        {
            "total": total,
            "with_links": with_links,
            "not_found": not_found,
            "opera_links": opera_links,
            "youtube_links": youtube_links,
            "needs_audit": opera_links,  # All jt0x links should be audited
        }
    )


# ==================== SERIES ENDPOINTS ====================

@app.route("/api/series", methods=["GET"])
def get_series():
    """Get catalog of series with pagination."""
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    series = get_catalog_series(limit, offset)
    total = get_series_count()
    return jsonify({"results": series, "total": total, "limit": limit, "offset": offset})


@app.route("/api/series/<int:series_id>", methods=["GET"])
def get_series_detail(series_id):
    """Get single series details with all seasons and episodes."""
    series = get_series_by_id(series_id)
    if not series:
        return jsonify({"error": "Série não encontrada"}), 404
    
    seasons = get_series_seasons(series_id)
    # Get episodes for each season
    for season in seasons:
        season["episodes"] = get_season_episodes(season["id"])
    
    series["seasons"] = seasons
    return jsonify(series)


@app.route("/api/series/<int:series_id>/seasons", methods=["GET"])
def get_series_seasons_endpoint(series_id):
    """Get all seasons for a series."""
    series = get_series_by_id(series_id)
    if not series:
        return jsonify({"error": "Série não encontrada"}), 404
    
    seasons = get_series_seasons(series_id)
    return jsonify({"series_id": series_id, "seasons": seasons})


@app.route("/api/series/seasons/<int:season_id>/episodes", methods=["GET"])
def get_season_episodes_endpoint(season_id):
    """Get all episodes for a season."""
    episodes = get_season_episodes(season_id)
    return jsonify({"season_id": season_id, "episodes": episodes})


@app.route("/api/series/search", methods=["GET"])
def search_series():
    """Search series by title (only series with at least 1 episode)."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": []})
    
    from database import get_conn
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """
        SELECT s.id, s.opera_id, s.tmdb_id, s.title, s.overview, s.poster_path, 
               s.backdrop_path, s.year, s.genres, s.rating
        FROM series s
        WHERE s.title LIKE ? AND s.status = 'active'
          AND EXISTS (
              SELECT 1 FROM episodes e 
              WHERE e.series_id = s.id 
              LIMIT 1
          )
        ORDER BY s.title
        LIMIT 50
    """,
        (f"%{query}%",),
    )
    rows = c.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "title": row["title"],
                "poster_path": row["poster_path"],
                "backdrop_path": row["backdrop_path"],
                "overview": row["overview"],
                "year": row["year"],
                "genres": row["genres"],
                "rating": row["rating"],
            }
        )
    return jsonify({"results": results})


# ==================== AUTH ENDPOINTS ====================

@app.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    name = data.get("name", "").strip()
    
    if not username or not password:
        return jsonify({"error": "Usuário e senha são obrigatórios"}), 400
    
    if len(password) < 4:
        return jsonify({"error": "Senha deve ter pelo menos 4 caracteres"}), 400
    
    # Hash password
    password_hash = generate_password_hash(password)
    
    # Create user
    user_id = create_user(username, password_hash, name)
    if not user_id:
        return jsonify({"error": "Usuário já existe"}), 409
    
    return jsonify({"message": "Usuário criado com sucesso", "user_id": user_id}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login user and return token."""
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"error": "Usuário e senha são obrigatórios"}), 400
    
    # Get user
    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "Usuário ou senha incorretos"}), 401
    
    # Check password
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Usuário ou senha incorretos"}), 401
    
    # Update last login
    update_last_login(user["id"])
    
    # Generate token
    token = generate_token(user["id"])
    
    return jsonify({
        "message": "Login realizado com sucesso",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "is_admin": user["is_admin"]
        }
    })


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def get_current_user(user_id):
    """Get current user info."""
    from database import get_conn
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, name, is_admin FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    return jsonify({
        "id": row["id"],
        "username": row["username"],
        "name": row["name"],
        "is_admin": bool(row["is_admin"])
    })


# ==================== PROTECTED MY LIST ENDPOINTS ====================

@app.route("/api/mylist/movies", methods=["GET"])
@require_auth
def get_user_movie_list(user_id):
    """Get user's movie list."""
    movies = get_my_list_movies(user_id)
    return jsonify({"results": movies, "count": len(movies)})


@app.route("/api/mylist/movies", methods=["POST"])
@require_auth
def add_movie_to_list(user_id):
    """Add movie to user's list."""
    data = request.get_json()
    success = add_to_my_list_movies(user_id, data)
    if success:
        return jsonify({"message": "Filme adicionado à lista"}), 201
    return jsonify({"error": "Filme já está na lista"}), 409


@app.route("/api/mylist/movies/<movie_id>", methods=["DELETE"])
@require_auth
def remove_movie_from_list(user_id, movie_id):
    """Remove movie from user's list."""
    success = remove_from_my_list_movies(user_id, movie_id)
    if success:
        return jsonify({"message": "Filme removido da lista"})
    return jsonify({"error": "Filme não encontrado na lista"}), 404


@app.route("/api/mylist/movies/<movie_id>/check", methods=["GET"])
@require_auth
def check_movie_in_list(user_id, movie_id):
    """Check if movie is in user's list."""
    is_in_list = is_in_my_list_movies(user_id, movie_id)
    return jsonify({"in_list": is_in_list})


@app.route("/api/mylist/series", methods=["GET"])
@require_auth
def get_user_series_list(user_id):
    """Get user's series list."""
    series = get_my_list_series(user_id)
    return jsonify({"results": series, "count": len(series)})


@app.route("/api/mylist/series", methods=["POST"])
@require_auth
def add_series_to_list(user_id):
    """Add series to user's list."""
    data = request.get_json()
    series_id = data.get("series_id")
    if not series_id:
        return jsonify({"error": "ID da série é obrigatório"}), 400
    
    success = add_to_my_list_series(user_id, series_id)
    if success:
        return jsonify({"message": "Série adicionada à lista"}), 201
    return jsonify({"error": "Série já está na lista"}), 409


@app.route("/api/mylist/series/<int:series_id>", methods=["DELETE"])
@require_auth
def remove_series_from_list(user_id, series_id):
    """Remove series from user's list."""
    success = remove_from_my_list_series(user_id, series_id)
    if success:
        return jsonify({"message": "Série removida da lista"})
    return jsonify({"error": "Série não encontrada na lista"}), 404


@app.route("/api/mylist/series/<int:series_id>/check", methods=["GET"])
@require_auth
def check_series_in_list(user_id, series_id):
    """Check if series is in user's list."""
    is_in_list = is_in_my_list_series(user_id, series_id)
    return jsonify({"in_list": is_in_list})


if __name__ == "__main__":
    # Start auto-precache in background (daemon thread so it doesn't block exit)
    logging.info("Starting background auto-precache task...")
    threading.Thread(target=run_bulk_scrape, daemon=True).start()

    # Run locally on 127.0.0.1:8080 (or from PORT env var)
    # Port 5000 is used by macOS AirPlay, so we use 8080
    port = int(os.environ.get("PORT", 8080))
    print(f"\n🚀 Flask server starting on http://127.0.0.1:{port}/")
    print(f"   API endpoints available:")
    print(f"   - http://127.0.0.1:{port}/api/health")
    print(f"   - http://127.0.0.1:{port}/api/catalog")
    print(f"   - http://127.0.0.1:{port}/api/series\n")
    app.run(host="127.0.0.1", port=port, debug=True)
