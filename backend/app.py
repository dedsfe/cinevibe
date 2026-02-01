from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

# Local modules (to be created below in this patch)
from database import init_db, get_cached_embed, save_embed, get_cache_count
from scraper import scrape_for_title
from validator import validate_embed

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_db()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    stats = get_cache_count()
    return jsonify(
        {
            "cached_links": stats.get("cached_links", 0),
            "tmdb_items": stats.get("tmdb_items", 0),
        }
    )


@app.route("/api/get-embed", methods=["POST"])
def get_embed():
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    tmdb_id = data.get("tmdbId")

    if not title:
        return jsonify({"error": "Título é obrigatório"}), 400

    # 1) Check cache
    cached = get_cached_embed(title)
    if cached:
        if validate_embed(cached):
            return jsonify({"embedUrl": cached, "cached": True})
        # if cache exists but invalid, continue to scrape

    # 2) On-demand scrape from legal sources
    embed = scrape_for_title(title, tmdb_id)
    if embed and validate_embed(embed):
        save_embed(title, embed, tmdb_id)
        return jsonify({"embedUrl": embed, "cached": False})

    return jsonify({"error": "Embed não encontrado"}), 404


if __name__ == "__main__":
    # Run locally on 127.0.0.1:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
