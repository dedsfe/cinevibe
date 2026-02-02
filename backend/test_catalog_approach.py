#!/usr/bin/env python3
"""
Quick Test - Catalog Browser Approach
Test the new navigation method with 3 movies
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from opera_catalog_browser import OperaCatalogBrowser
from database import save_embed, get_conn


def test_catalog_approach():
    """Testa nova abordagem de catálogo"""
    print("=" * 80)
    print("🎬 TESTE NOVA ABORDAGEM: Navegação por Catálogo")
    print("=" * 80)
    print()
    print("Fluxo:")
    print("1. Mantém mesma aba (sem reload)")
    print("2. Vai para /movie/ (lista de filmes)")
    print("3. Extrai ID da URL: category/XXX/YYYYY/info/")
    print("4. Navega para play: category/XXX/YYYYY/play/")
    print("5. Extrai MP4")
    print()

    browser = OperaCatalogBrowser()

    print("🚀 Iniciando navegador...")
    if not browser.start_session(headless=True):
        print("❌ Falha ao iniciar")
        return

    try:
        print("\n📚 Método 1: Scrollear catálogo e pegar filmes")
        print("-" * 80)

        # Get movies from catalog
        movies = browser.scroll_and_get_all_movies(max_scrolls=3)
        print(f"\n🎬 Encontrados {len(movies)} filmes no catálogo")

        # Show first 5
        print("\nPrimeiros 5 filmes encontrados:")
        for i, movie in enumerate(movies[:5], 1):
            print(f"{i}. {movie['title']}")
            print(f"   ID: {movie['category_id']}/{movie['movie_id']}")

        # Test with first movie
        if movies:
            test_movie = movies[0]
            print(f"\n\n🧪 Testando extração com: {test_movie['title']}")
            print("-" * 80)

            video_url = browser.extract_video_from_movie(
                test_movie["category_id"], test_movie["movie_id"]
            )

            if video_url:
                print(f"✅ SUCESSO!")
                print(f"   Filme: {test_movie['title']}")
                print(f"   ID: {test_movie['category_id']}/{test_movie['movie_id']}")
                print(f"   MP4: {video_url}")

                # Save to database
                save_embed(
                    test_movie["title"],
                    video_url,
                    None,  # tmdb_id - we'll get this later from IMDB
                    None,
                    None,
                    None,
                )
                print("   💾 Salvo no banco!")
            else:
                print(f"❌ Falha ao extrair vídeo")

        print("\n\n🔍 Método 2: Buscar filme específico")
        print("-" * 80)

        search_title = "O Poderoso Chefão"
        print(f"Buscando: {search_title}")

        result = browser.search_and_extract(search_title)

        if result["success"]:
            print(f"✅ ENCONTRADO!")
            print(f"   Título: {result['title']}")
            print(f"   ID: {result['category_id']}/{result['movie_id']}")
            print(f"   MP4: {result['video_url']}")
        else:
            print(f"❌ Não encontrado")
            print(f"   Erro: {result.get('error')}")

    finally:
        browser.stop_session()

    print("\n" + "=" * 80)
    print("✅ Teste concluído!")
    print("=" * 80)


if __name__ == "__main__":
    test_catalog_approach()
