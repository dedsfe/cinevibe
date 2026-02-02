#!/usr/bin/env python3
"""
Fix Missing Posters - Busca alternativa por nome
Tenta encontrar capas buscando por nome quando ID falha
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_conn
import requests
import time

TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"


def search_movie_by_name(title):
    """Busca filme no TMDB por nome"""
    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "language": "pt-BR",
            "page": 1,
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("results") and len(data["results"]) > 0:
            # Pega o primeiro resultado
            movie = data["results"][0]
            return {
                "id": str(movie["id"]),
                "title": movie["title"],
                "poster_path": movie.get("poster_path"),
                "backdrop_path": movie.get("backdrop_path"),
                "overview": movie.get("overview"),
                "vote_average": movie.get("vote_average"),
            }
    except Exception as e:
        print(f"   ⚠️  Erro: {e}")

    return None


def fix_missing_posters():
    """Tenta encontrar capas pelos nomes"""
    print("=" * 80)
    print("🖼️  BUSCANDO CAPAS POR NOME")
    print("=" * 80)
    print()

    # Pega filmes sem poster
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, tmdb_id 
        FROM links 
        WHERE (poster_path IS NULL OR poster_path = '') 
        AND tmdb_id IS NOT NULL
        ORDER BY title
    """)

    movies = c.fetchall()
    conn.close()

    if not movies:
        print("✅ Todos já têm capas!")
        return

    print(f"🎬 Tentando {len(movies)} filmes...")
    print()

    success_count = 0

    for link_id, title, old_tmdb_id in movies:
        print(f"\n🔍 {title}")
        print(f"   TMDB ID antigo: {old_tmdb_id}")

        # Busca por nome
        result = search_movie_by_name(title)

        if result and result["poster_path"]:
            print(f"   ✅ Encontrado!")
            print(f"   🆕 Novo TMDB ID: {result['id']}")
            print(f"   🖼️  Poster: {result['poster_path']}")

            # Atualiza no banco (incluindo novo TMDB ID)
            conn = get_conn()
            c = conn.cursor()
            c.execute(
                """
                UPDATE links 
                SET tmdb_id = ?, 
                    poster_path = ?, 
                    backdrop_path = ?, 
                    overview = ?
                WHERE id = ?
            """,
                (
                    result["id"],
                    result["poster_path"],
                    result["backdrop_path"] or "",
                    result["overview"] or "",
                    link_id,
                ),
            )
            conn.commit()
            conn.close()

            print(f"   💾 Capa adicionada!")
            success_count += 1
        else:
            print(f"   ❌ Não encontrado por nome")

        time.sleep(0.5)  # Respeitar rate limit

    print("\n" + "=" * 80)
    print("📊 RESUMO")
    print("=" * 80)
    print(f"✅ Capas encontradas: {success_count}/{len(movies)}")
    print()

    # Status final
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) FROM links WHERE poster_path IS NOT NULL AND poster_path != ''"
    )
    with_poster = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM links")
    total = c.fetchone()[0]
    conn.close()

    print(f"📁 Total com capas: {with_poster}/{total}")
    print(f"📊 {(with_poster / total * 100):.1f}% completo")
    print("=" * 80)


if __name__ == "__main__":
    fix_missing_posters()
