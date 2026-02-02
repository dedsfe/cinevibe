from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import threading
from datetime import datetime

# Local modules (to be created below in this patch)
from database import (
    init_db,
    get_cached_embed,
    get_cached_embed_by_id,
    save_embed,
    get_cache_count,
    get_cached_ids,
    get_cached_statuses,
    get_catalog_movies,
)
from scraper import scrape_for_title
from validator import validate_embed
from bulk_scrape_tmdb import run_bulk_scrape, get_scraper_state

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


if __name__ == "__main__":
    # Start auto-precache in background (daemon thread so it doesn't block exit)
    logging.info("Starting background auto-precache task...")
    threading.Thread(target=run_bulk_scrape, daemon=True).start()

    # Run locally on 127.0.0.1:5000 (or from PORT env var)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
