#!/usr/bin/env python3
"""
Fill Missing Links - Apenas para filmes existentes
Busca links MP4 para filmes que já estão no banco como NOT_FOUND
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_conn, save_embed
from opera_catalog_browser import OperaCatalogBrowser
import time


def fill_missing_links():
    """Preenche links faltantes para filmes existentes"""
    print("=" * 80)
    print("🔗 PREENCHENDO LINKS FALTANTES")
    print("=" * 80)
    print()
    print("⚠️  Apenas para filmes JÁ EXISTENTES no banco")
    print("   Não vai adicionar filmes novos!")
    print()

    # Pega filmes sem link do banco
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, tmdb_id 
        FROM links 
        WHERE embed_url = 'NOT_FOUND' OR embed_url IS NULL
        ORDER BY title
    """)

    movies = c.fetchall()
    conn.close()

    if not movies:
        print("✅ Nenhum filme faltando link!")
        return

    print(f"🎬 Encontrados {len(movies)} filmes sem link:")
    for _, title, _ in movies:
        print(f"   • {title}")
    print()

    # Inicializa browser
    browser = OperaCatalogBrowser()

    print("🚀 Iniciando navegador...")
    if not browser.start_session(headless=True):
        print("❌ Falha ao iniciar")
        return

    success_count = 0
    fail_count = 0

    try:
        for i, (link_id, title, tmdb_id) in enumerate(movies, 1):
            print(f"\n[{i}/{len(movies)}] {title}")
            print("-" * 60)

            try:
                # Busca no catálogo
                result = browser.search_and_extract(title)

                if result["success"]:
                    video_url = result["video_url"]
                    print(f"   ✅ Encontrado: {result['scraped_title']}")
                    print(f"   🎥 Link: {video_url}")

                    # Atualiza no banco
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute(
                        "UPDATE links SET embed_url = ?, original_raw_title = ? WHERE id = ?",
                        (video_url, result["scraped_title"], link_id),
                    )
                    conn.commit()
                    conn.close()

                    print(f"   💾 Link atualizado!")
                    success_count += 1
                else:
                    print(
                        f"   ❌ Não encontrado no Opera: {result.get('error', 'Desconhecido')}"
                    )
                    fail_count += 1

            except Exception as e:
                print(f"   ❌ Erro: {e}")
                fail_count += 1

            # Pausa entre filmes
            if i < len(movies):
                print(f"   😴 Pausa de 1s...")
                time.sleep(1)

    finally:
        browser.stop_session()

    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO")
    print("=" * 80)
    print(f"✅ Links encontrados: {success_count}/{len(movies)}")
    print(f"❌ Não encontrados: {fail_count}/{len(movies)}")
    print()

    # Verifica status final
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM links WHERE embed_url != 'NOT_FOUND'")
    with_link = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM links WHERE embed_url = 'NOT_FOUND'")
    not_found = c.fetchone()[0]
    conn.close()

    print(f"📁 Total com link: {with_link} filmes")
    print(f"⏳ Ainda sem link: {not_found} filmes")
    print()
    print("🎉 Processo concluído!")
    print("=" * 80)


if __name__ == "__main__":
    fill_missing_links()
