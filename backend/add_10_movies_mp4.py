#!/usr/bin/env python3
"""
Add MP4 for 10 Specific Movies
Adiciona links MP4 apenas para os 10 filmes selecionados
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_conn, save_embed
from opera_catalog_browser import OperaCatalogBrowser
import time

# Lista dos 10 filmes específicos
TARGET_MOVIES = [
    "96 Minutos",
    "A Guerra dos Mundos",
    "A Lista de Schindler",
    "A Sombra do Perigo",
    "A Vida é Bela",
    "Anaconda",
    "Avatar: Fogo e Cinzas",
    "Bob Esponja: Em Busca da Calça Quadrada",
    "Demon Slayer: Kimetsu no Yaiba Castelo Infinito",
    "Davi: Nasce Um Rei",
]


def add_mp4_for_specific_movies():
    """Adiciona MP4 apenas para os 10 filmes da lista"""
    print("=" * 80)
    print("🎬 ADICIONANDO MP4 PARA 10 FILMES ESPECÍFICOS")
    print("=" * 80)
    print()

    # Pega IDs do banco
    conn = get_conn()
    c = conn.cursor()

    movies_to_process = []
    for title in TARGET_MOVIES:
        c.execute("SELECT id, title, tmdb_id FROM links WHERE title = ?", (title,))
        row = c.fetchone()
        if row:
            movies_to_process.append(row)
            print(f"✅ Encontrado: {title}")
        else:
            print(f"❌ Não encontrado no banco: {title}")

    conn.close()

    if not movies_to_process:
        print("\n❌ Nenhum filme da lista encontrado no banco!")
        return

    print(f"\n🎬 Total para processar: {len(movies_to_process)} filmes")
    print()

    # Inicializa browser
    browser = OperaCatalogBrowser()

    print("🚀 Iniciando navegador...")
    if not browser.start_session(headless=False):
        print("❌ Falha ao iniciar")
        return

    success_count = 0
    fail_count = 0

    try:
        for i, (link_id, title, tmdb_id) in enumerate(movies_to_process, 1):
            print(f"\n[{i}/{len(movies_to_process)}] {title}")
            print("-" * 60)

            try:
                # Busca no Opera
                result = browser.search_and_extract(title)

                if result["success"]:
                    video_url = result["video_url"]
                    print(f"   ✅ Encontrado: {result['scraped_title']}")
                    print(f"   🎥 Video ID: {result['movie_id']}")
                    print(f"   🎬 MP4: {video_url}")

                    # Atualiza no banco (mantém tudo, só muda o link)
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute(
                        "UPDATE links SET embed_url = ?, original_raw_title = ? WHERE id = ?",
                        (video_url, result["scraped_title"], link_id),
                    )
                    conn.commit()
                    conn.close()

                    print(f"   💾 Link MP4 adicionado!")
                    success_count += 1
                else:
                    print(
                        f"   ❌ Não encontrado: {result.get('error', 'Desconhecido')}"
                    )
                    fail_count += 1

            except Exception as e:
                print(f"   ❌ Erro: {e}")
                fail_count += 1

            # Pausa entre filmes
            if i < len(movies_to_process):
                print(f"   😴 Pausa de 2s...")
                time.sleep(2)

    finally:
        browser.stop_session()

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO")
    print("=" * 80)
    print(f"✅ Links adicionados: {success_count}/{len(movies_to_process)}")
    print(f"❌ Falhas: {fail_count}/{len(movies_to_process)}")
    print()

    # Status atualizado
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM links WHERE embed_url != 'NOT_FOUND'")
    with_link = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM links")
    total = c.fetchone()[0]
    conn.close()

    print(f"📁 Total com MP4 agora: {with_link}/{total} filmes")
    print()
    print("🎉 Processo concluído!")
    print("   Dê refresh no frontend (F5) para ver os filmes disponíveis.")
    print("=" * 80)


if __name__ == "__main__":
    add_mp4_for_specific_movies()
