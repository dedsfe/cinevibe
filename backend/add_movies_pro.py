#!/usr/bin/env python3
"""
Catalog Scraper PRO - Opera Topzera
Versão robusta com retries, validação e tratamento de erros
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from opera_catalog_browser import OperaCatalogBrowser
from database import save_embed, get_conn
import requests
import time
from functools import wraps

TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"


def retry_on_error(max_retries=3, delay=2):
    """Decorator para retry automático"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"   ⚠️  Tentativa {attempt + 1} falhou: {e}")
                        print(f"   🔄 Tentando novamente em {delay}s...")
                        time.sleep(delay)
                    else:
                        raise e
            return None

        return wrapper

    return decorator


def validate_mp4_link(url):
    """Verifica se o link MP4 realmente funciona"""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except:
        return False


def search_tmdb(title):
    """Busca filme no TMDB com melhor matching"""
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

        if data.get("results"):
            # Pega o primeiro resultado que tem poster
            for movie in data["results"]:
                if movie.get("poster_path"):
                    return {
                        "id": str(movie["id"]),
                        "title": movie["title"],
                        "poster_path": movie.get("poster_path"),
                        "backdrop_path": movie.get("backdrop_path"),
                        "overview": movie.get("overview"),
                        "vote_average": movie.get("vote_average"),
                        "release_date": movie.get("release_date", ""),
                    }

            # Se nenhum tem poster, pega o primeiro mesmo
            movie = data["results"][0]
            return {
                "id": str(movie["id"]),
                "title": movie["title"],
                "poster_path": movie.get("poster_path"),
                "backdrop_path": movie.get("backdrop_path"),
                "overview": movie.get("overview"),
                "vote_average": movie.get("vote_average"),
                "release_date": movie.get("release_date", ""),
            }
    except Exception as e:
        print(f"   ⚠️  Erro TMDB: {e}")

    return None


def is_valid_movie_title(title):
    """Verifica se é um título de filme válido (não genérico)"""
    invalid_keywords = [
        "more info",
        "loading",
        "error",
        "404",
        "null",
        "undefined",
        "season",
        "episódio",
        "episode",
        "temporada",
    ]

    title_lower = title.lower()

    # Muito curto
    if len(title) < 3:
        return False

    # Contém palavras inválidas
    for keyword in invalid_keywords:
        if keyword in title_lower:
            return False

    return True


@retry_on_error(max_retries=3, delay=2)
def process_movie_with_retry(browser, movie_data, tmdb_cache):
    """Processa um filme com retry automático"""
    title = movie_data["title"]
    category_id = movie_data["category_id"]
    movie_id = movie_data["movie_id"]

    print(f"\n🎬 {title}")
    print(f"   ID Opera: {category_id}/{movie_id}")

    # Verifica se é título válido
    if not is_valid_movie_title(title):
        print(f"   ⚠️  Título inválido, pulando...")
        return None

    # Extrai vídeo com retry
    print(f"   🎥 Extraindo vídeo...")
    video_url = browser.extract_video_from_movie(category_id, movie_id)

    if not video_url:
        print(f"   ❌ Falha ao extrair vídeo")
        return None

    # Valida link MP4
    print(f"   🔍 Validando link...")
    if not validate_mp4_link(video_url):
        print(f"   ⚠️  Link parece inválido, mas vamos tentar salvar mesmo assim")

    print(f"   ✅ Vídeo: {video_url}")

    # Busca TMDB (com cache)
    tmdb_data = None
    if title in tmdb_cache:
        print(f"   💾 TMDB (cache)")
        tmdb_data = tmdb_cache[title]
    else:
        print(f"   🔍 Buscando no TMDB...")
        tmdb_data = search_tmdb(title)
        if tmdb_data:
            tmdb_cache[title] = tmdb_data

    if tmdb_data:
        print(
            f"   ✅ TMDB: {tmdb_data['title']} ⭐ {tmdb_data.get('vote_average', 'N/A')}"
        )

        # Salva no banco
        save_embed(
            title=tmdb_data["title"],
            embed_url=video_url,
            tmdb_id=tmdb_data["id"],
            poster_path=tmdb_data["poster_path"],
            backdrop_path=tmdb_data["backdrop_path"],
            overview=tmdb_data["overview"],
        )
        print(f"   💾 Salvo com TMDB!")
        return {"status": "success", "tmdb": True}
    else:
        # Salva sem TMDB
        save_embed(
            title=title,
            embed_url=video_url,
            tmdb_id=movie_id,
            poster_path="",
            backdrop_path="",
            overview="",
        )
        print(f"   💾 Salvo sem TMDB")
        return {"status": "success", "tmdb": False}


def add_movies_robust(max_movies=None):
    """Adiciona filmes de forma robusta com todas as melhorias"""
    print("=" * 80)
    print("🎬 CATALOG SCRAPER PRO - Opera Topzera")
    print("=" * 80)
    print()
    print("✨ Melhorias:")
    print("   • Retry automático (3 tentativas)")
    print("   • Validação de links MP4")
    print("   • Cache TMDB (não repete buscas)")
    print("   • Filtragem de títulos inválidos")
    print("   • Rate limiting (não sobrecarrega)")
    if max_movies:
        print(f"   • LIMITE: Apenas {max_movies} filmes")
    print()

    # Inicializa browser
    browser = OperaCatalogBrowser()

    print("🚀 Iniciando navegador...")
    if not browser.start_session(headless=True):
        print("❌ Falha ao iniciar navegador")
        return

    tmdb_cache = {}
    success_count = 0
    fail_count = 0
    skip_count = 0

    try:
        # Coleta filmes do catálogo
        print("\n📚 Coletando filmes do catálogo...")
        movies = browser.scroll_and_get_all_movies(max_scrolls=10)

        # Aplica limite se especificado
        if max_movies and len(movies) > max_movies:
            movies = movies[:max_movies]
            print(f"\n🎬 Limitado a: {max_movies} filmes")
        else:
            print(f"\n🎬 Total encontrados: {len(movies)}")

        print(f"⏱️  Estimativa: ~{len(movies) * 3} segundos")
        print()

        # Processa cada filme
        for i, movie in enumerate(movies, 1):
            print(f"\n[{i}/{len(movies)}]", end=" ")

            try:
                result = process_movie_with_retry(browser, movie, tmdb_cache)

                if result:
                    success_count += 1
                else:
                    skip_count += 1

            except Exception as e:
                print(f"   ❌ Erro após retries: {e}")
                fail_count += 1

            # Rate limiting - descanso a cada 5 filmes
            if i % 5 == 0:
                print(f"\n   😴 Pausa de 2s para não sobrecarregar...")
                time.sleep(2)

    finally:
        browser.stop_session()

    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO FINAL")
    print("=" * 80)
    print(f"✅ Sucessos: {success_count}")
    print(f"⚠️  Pulados: {skip_count}")
    print(f"❌ Falhas: {fail_count}")
    print(
        f"📊 Total processados: {success_count + skip_count + fail_count}/{len(movies)}"
    )
    print()

    # Mostra estatísticas do banco
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM links WHERE embed_url != 'NOT_FOUND'")
    total_db = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(*) FROM links WHERE poster_path IS NOT NULL AND poster_path != ''"
    )
    with_poster = c.fetchone()[0]
    conn.close()

    print(f"📁 Total no banco: {total_db} filmes")
    print(f"🖼️  Com poster TMDB: {with_poster} filmes")
    print()
    print("🎉 Catálogo atualizado com sucesso!")
    print("   Recarregue o frontend (F5) para ver as mudanças.")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limitar quantidade de filmes")
    args = parser.parse_args()

    add_movies_robust(max_movies=args.limit)
