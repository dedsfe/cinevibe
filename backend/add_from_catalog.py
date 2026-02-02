#!/usr/bin/env python3
"""
Catalog Scraper - Opera Topzera
Navega pelo catálogo e extrai filmes com IDs fixos
Fluxo: /movie/ -> scroll -> extrai ID -> /play/ -> extrai MP4
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from opera_catalog_browser import OperaCatalogBrowser
from database import save_embed
import requests
import time

# TMDB API Key
TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"


def search_tmdb(title):
    """Busca filme no TMDB pelo título"""
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
            movie = data["results"][0]
            return {
                "id": str(movie["id"]),
                "title": movie["title"],
                "poster_path": movie.get("poster_path"),
                "backdrop_path": movie.get("backdrop_path"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date", ""),
            }
    except Exception as e:
        print(f"   ⚠️  Erro TMDB: {e}")

    return None


def add_movies_from_catalog():
    """Adiciona filmes do catálogo Opera para o banco"""
    print("=" * 80)
    print("🎬 ADICIONANDO FILMES DO CATÁLOGO OPERA")
    print("=" * 80)
    print()
    print("Fluxo:")
    print("1. Navega para /movie/ (lista de filmes)")
    print("2. Scrollea e coleta filmes")
    print("3. Para cada filme: ID da URL -> /play/ -> MP4")
    print("4. Busca no TMDB -> Salva no banco")
    print()

    # Inicializa browser
    browser = OperaCatalogBrowser()

    print("🚀 Iniciando navegador...")
    if not browser.start_session(headless=True):
        print("❌ Falha ao iniciar navegador")
        return

    try:
        # Coleta filmes do catálogo
        print("\n📚 Coletando filmes do catálogo...")
        print("   (Scrolleando página...)")

        movies = browser.scroll_and_get_all_movies(max_scrolls=5)

        print(f"\n🎬 Total de filmes encontrados: {len(movies)}")
        print()

        # Processa cada filme
        success_count = 0
        fail_count = 0

        for i, movie in enumerate(movies, 1):
            print(f"\n[{i}/{len(movies)}] {movie['title']}")
            print("-" * 60)

            # Extrai vídeo
            print(
                f"   🎥 Extraindo vídeo (ID: {movie['category_id']}/{movie['movie_id']})..."
            )
            video_url = browser.extract_video_from_movie(
                movie["category_id"], movie["movie_id"]
            )

            if not video_url:
                print(f"   ❌ Falha ao extrair vídeo")
                fail_count += 1
                continue

            print(f"   ✅ Vídeo: {video_url}")

            # Busca no TMDB
            print(f"   🔍 Buscando no TMDB...")
            tmdb_data = search_tmdb(movie["title"])

            if tmdb_data:
                print(f"   ✅ TMDB: {tmdb_data['title']} (ID: {tmdb_data['id']})")

                # Salva no banco
                save_embed(
                    title=tmdb_data["title"],
                    embed_url=video_url,
                    tmdb_id=tmdb_data["id"],
                    poster_path=tmdb_data["poster_path"],
                    backdrop_path=tmdb_data["backdrop_path"],
                    overview=tmdb_data["overview"],
                )
                print(f"   💾 Salvo no banco com TMDB!")
                success_count += 1
            else:
                # Salva sem TMDB (só título e vídeo)
                save_embed(
                    title=movie["title"],
                    embed_url=video_url,
                    tmdb_id=movie["movie_id"],  # Usa ID do Opera como TMDB temporário
                    poster_path=None,
                    backdrop_path=None,
                    overview=None,
                )
                print(f"   💾 Salvo sem TMDB (usando ID Opera)")
                success_count += 1

            # Delay entre filmes
            time.sleep(0.5)

        # Resumo
        print("\n" + "=" * 80)
        print("📊 RESUMO")
        print("=" * 80)
        print(f"✅ Sucessos: {success_count}/{len(movies)}")
        print(f"❌ Falhas: {fail_count}/{len(movies)}")
        print()

        if success_count > 0:
            print("🎉 Filmes adicionados com sucesso!")
            print("   Recarregue o frontend para ver os filmes.")

    finally:
        browser.stop_session()
        print("\n🏁 Navegador fechado.")


if __name__ == "__main__":
    add_movies_from_catalog()
