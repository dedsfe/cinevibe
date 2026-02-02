#!/usr/bin/env python3
"""
Update Posters - Apenas metadados TMDB
Busca posters, backdrops e overviews para filmes existentes
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_conn
import requests
import time

TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"


def get_movie_details(tmdb_id):
    """Busca detalhes do filme no TMDB"""
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        params = {"api_key": TMDB_API_KEY, "language": "pt-BR"}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return {
                "poster_path": data.get("poster_path"),
                "backdrop_path": data.get("backdrop_path"),
                "overview": data.get("overview"),
                "vote_average": data.get("vote_average"),
                "title": data.get("title"),
            }
    except Exception as e:
        print(f"   ⚠️  Erro TMDB: {e}")

    return None


def update_posters():
    """Atualiza apenas os posters dos filmes existentes"""
    print("=" * 80)
    print("🖼️  ATUALIZANDO CAPAS E METADADOS TMDB")
    print("=" * 80)
    print()
    print("⚠️  Apenas atualiza filmes EXISTENTES")
    print("   Mantém todos os links intactos!")
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
        print("✅ Todos os filmes já têm capas!")
        return

    print(f"🎬 Encontrados {len(movies)} filmes sem capa:")
    for _, title, _ in movies[:10]:  # Mostra primeiros 10
        print(f"   • {title}")

    if len(movies) > 10:
        print(f"   ... e mais {len(movies) - 10} filmes")
    print()

    success_count = 0
    fail_count = 0

    for i, (link_id, title, tmdb_id) in enumerate(movies, 1):
        print(f"\n[{i}/{len(movies)}] {title}")
        print(f"   TMDB ID: {tmdb_id}")

        try:
            # Busca no TMDB
            details = get_movie_details(tmdb_id)

            if details and (details["poster_path"] or details["backdrop_path"]):
                print(f"   ✅ Encontrado: {details['title']}")
                print(f"   🖼️  Poster: {details['poster_path'] or 'N/A'}")
                print(f"   🎬 Backdrop: {details['backdrop_path'] or 'N/A'}")
                print(f"   ⭐ Rating: {details['vote_average']}")

                # Atualiza no banco (apenas metadados, NÃO toca no link!)
                conn = get_conn()
                c = conn.cursor()
                c.execute(
                    """
                    UPDATE links 
                    SET poster_path = ?, 
                        backdrop_path = ?, 
                        overview = ?
                    WHERE id = ?
                """,
                    (
                        details["poster_path"] or "",
                        details["backdrop_path"] or "",
                        details["overview"] or "",
                        link_id,
                    ),
                )
                conn.commit()
                conn.close()

                print(f"   💾 Capas atualizadas!")
                success_count += 1
            else:
                print(f"   ❌ Sem capas disponíveis no TMDB")
                fail_count += 1

        except Exception as e:
            print(f"   ❌ Erro: {e}")
            fail_count += 1

        # Pausa para não sobrecarregar API
        if i % 10 == 0:
            print(f"\n   😴 Pausa de 1s...")
            time.sleep(1)

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO")
    print("=" * 80)
    print(f"✅ Capas adicionadas: {success_count}/{len(movies)}")
    print(f"❌ Sem capas: {fail_count}/{len(movies)}")
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

    print(f"📁 Total com capas: {with_poster}/{total} filmes")
    print(f"📊 {(with_poster / total * 100):.1f}% do catálogo com capas")
    print()
    print("🎉 Capas atualizadas!")
    print("   Dê refresh no frontend (F5) para ver as mudanças.")
    print("=" * 80)


if __name__ == "__main__":
    update_posters()
