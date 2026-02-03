from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import threading
from datetime import datetime, timedelta
from functools import wraps

# Password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# Local modules
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
    search_movies_locally,
    search_series_locally,
)
from scraper import scrape_for_title
from validator import validate_embed

# Simple token storage
active_tokens = {}

def generate_token(user_id):
    import secrets
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=7)
    active_tokens[token] = {"user_id": user_id, "expires": expires}
    return token

def verify_token(token):
    if not token or token not in active_tokens:
        return None
    session = active_tokens[token]
    if datetime.utcnow() > session["expires"]:
        del active_tokens[token]
        return None
    return session["user_id"]

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        dummy_user_id = 1
        return f(dummy_user_id, *args, **kwargs)
    return decorated

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization", "Accept"]}})

# Global OPTIONS handler
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_api_options(path):
    response = app.make_response('')
    response.status_code = 204
    origin = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

# Initialize database
try:
    init_db()
    init_users_table()
    print("✅ Database initialized")
except Exception as e:
    print(f"⚠️ DB init warning: {e}

# Create default admin
def create_default_admin():
    try:
        users = get_all_users()
        if not users:
            password_hash = generate_password_hash("admin123")
            create_user("admin", password_hash, "Administrador", is_admin=True)
            print("✅ Usuário admin criado: admin / admin123")
    except Exception as e:
        print(f"⚠️ Admin warning: {e}")

create_default_admin()

@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "ok", "message": "Filfil API", "endpoints": ["/api/health", "/api/catalog", "/api/series", "/api/search"]})

@app.route("/api/health", methods=["GET"])
def health():
    try:
        series_count = get_series_count()
        movie_count = get_cache_count().get("cached_links", 0)
        return jsonify({"status": "ok", "database": {"series": series_count, "movies": movie_count}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/catalog", methods=["GET"])
def get_catalog():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    movies = get_catalog_movies(limit, offset)
    return jsonify({"results": movies})

@app.route("/api/search/all", methods=["GET", "POST"])
def unified_search_all():
    """Search movies and series locally."""
    query = request.args.get("q", "") or (request.json.get("q") if request.is_json else "")
    query = query.strip()
    limit = int(request.args.get("limit", 50))
    
    if not query:
        return jsonify({"results": []})
    
    try:
        movies = search_movies_locally(query, limit)
        series = search_series_locally(query, limit)
        results = movies + series
        
        # Sort by title
        results.sort(key=lambda x: x.get('title', '').lower())
        
        return jsonify({"results": results[:limit]})
    except Exception as e:
        logging.error(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-embed", methods=["POST"])
def get_embed():
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    tmdb_id = data.get("tmdbId")
    year = data.get("year")

    if not title:
        return jsonify({"error": "Título é obrigatório"}), 400

    # Check cache by ID
    if tmdb_id:
        cached_by_id = get_cached_embed_by_id(tmdb_id)
        if cached_by_id and validate_embed(cached_by_id):
            return jsonify({"embedUrl": cached_by_id, "cached": True})

    # Check cache by title
    cached = get_cached_embed(title)
    if cached and validate_embed(cached):
        return jsonify({"embedUrl": cached, "cached": True})

    # Scrape
    embed = scrape_for_title(title, tmdb_id, year=year)
    if embed and validate_embed(embed):
        save_embed(title, embed, tmdb_id)
        return jsonify({"embedUrl": embed, "cached": False})

    return jsonify({"error": "Embed não encontrado"}), 404

@app.route("/api/series", methods=["GET"])
def get_series():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    series = get_catalog_series(limit, offset)
    total = get_series_count()
    return jsonify({"results": series, "total": total, "limit": limit, "offset": offset})

@app.route("/api/series/<int:series_id>", methods=["GET"])
def get_series_detail(series_id):
    series = get_series_by_id(series_id)
    if not series:
        return jsonify({"error": "Série não encontrada"}), 404
    
    seasons = get_series_seasons(series_id)
    for season in seasons:
        season["episodes"] = get_season_episodes(season["id"])
    
    series["seasons"] = seasons
    return jsonify(series)

@app.route("/api/mylist/movies", methods=["GET"])
def get_my_list_movies_endpoint():
    movies = get_my_list_movies(1)  # dummy user_id
    return jsonify({"results": movies})

@app.route("/api/mylist/series", methods=["GET"])
def get_my_list_series_endpoint():
    series = get_my_list_series(1)
    return jsonify({"results": series})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Server: http://127.0.0.1:{port}/")
    app.run(host="0.0.0.0", port=port, debug=False)
