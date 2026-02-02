#!/usr/bin/env python3
"""
Teste Controlado - 3 Filmes
Limpa o banco e testa com apenas 3 filmes conhecidos
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_conn, save_embed
from improved_opera_scraper import ImprovedOperaScraper


def backup_and_clean():
    """Faz backup e limpa os links (mantém metadados)"""
    print("=" * 80)
    print("🧹 FAZENDO BACKUP E LIMPANDO LINKS")
    print("=" * 80)

    conn = get_conn()
    c = conn.cursor()

    # Count current
    c.execute("SELECT COUNT(*) FROM links WHERE embed_url != 'NOT_FOUND'")
    count = c.fetchone()[0]
    print(f"\n📊 Links atuais no banco: {count}")

    # Backup (rename table)
    try:
        c.execute("ALTER TABLE links RENAME TO links_backup")
        conn.commit()
        print("✅ Backup criado: links_backup")
    except:
        print("⚠️  Backup já existe ou erro ao criar")

    # Create new clean table
    c.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            tmdb_id TEXT,
            embed_url TEXT,
            poster_path TEXT,
            backdrop_path TEXT,
            overview TEXT,
            original_raw_title TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    print("✅ Nova tabela 'links' criada (vazia)")
    print()


def test_3_movies():
    """Testa com 3 filmes específicos"""
    print("=" * 80)
    print("🎬 TESTE COM 3 FILMES")
    print("=" * 80)
    print()

    # 3 filmes populares e bem conhecidos
    test_movies = [
        {"title": "A Lista de Schindler", "tmdb_id": "424", "year": "1993"},
        {"title": "O Poderoso Chefão", "tmdb_id": "238", "year": "1972"},
        {"title": "Davi: Nasce Um Rei", "tmdb_id": "1167307", "year": "2025"},
    ]

    print("Filmes escolhidos para teste:")
    for i, movie in enumerate(test_movies, 1):
        print(f"{i}. {movie['title']} ({movie['year']}) - TMDB: {movie['tmdb_id']}")
    print()

    # Initialize scraper
    scraper = ImprovedOperaScraper()
    scraper.start_session(headless=True)

    results = []

    try:
        for movie in test_movies:
            print(f"\n🎬 Processando: {movie['title']}")
            print("-" * 60)

            # Scrape with improved validation
            result = scraper.scrape_movie(movie["title"], movie["year"])

            if result["success"] and result["validation_passed"]:
                print(f"✅ SUCESSO!")
                print(f"   Título encontrado: {result['scraped_title']}")
                print(f"   Similaridade: {result['similarity']:.1%}")
                print(f"   Video ID: {result['video_id']}")
                print(f"   URL: {result['video_url']}")

                # Save to database
                save_embed(
                    movie["title"],
                    result["video_url"],
                    movie["tmdb_id"],
                    None,  # poster
                    None,  # backdrop
                    None,  # overview
                )
                print("   💾 Salvo no banco!")

                results.append({"movie": movie, "result": result, "status": "success"})
            else:
                print(f"❌ FALHA!")
                print(f"   Erro: {result['error']}")

                # Save as NOT_FOUND
                save_embed(
                    movie["title"], "NOT_FOUND", movie["tmdb_id"], None, None, None
                )
                print("   💾 Salvo como NOT_FOUND")

                results.append({"movie": movie, "result": result, "status": "failed"})
    finally:
        scraper.stop_session()

    return results


def show_results(results):
    """Mostra resultados finais"""
    print("\n" + "=" * 80)
    print("📊 RESULTADO DO TESTE")
    print("=" * 80)

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")

    print(f"\n✅ Sucessos: {success_count}/3")
    print(f"❌ Falhas: {failed_count}/3")
    print()

    for r in results:
        movie = r["movie"]
        if r["status"] == "success":
            print(f"\n🟢 {movie['title']}")
            print(f"   Video ID: {r['result']['video_id']}")
            print(f"   Similaridade: {r['result']['similarity']:.1%}")
            print(f"   URL: {r['result']['video_url']}")
        else:
            print(f"\n🔴 {movie['title']}")
            print(f"   Erro: {r['result']['error']}")

    print("\n" + "=" * 80)

    if success_count == 3:
        print("🎉 PERFEITO! Todos os 3 filmes foram adicionados corretamente!")
        print("   Podemos agora aplicar a todos os filmes.")
    elif success_count >= 2:
        print(f"⚠️  {success_count}/3 filmes OK. Podemos tentar com mais.")
    else:
        print("❌ Poucos sucessos. Precisamos ajustar o sistema.")

    print("=" * 80)


def restore_backup():
    """Restaura backup se necessário"""
    conn = get_conn()
    c = conn.cursor()

    try:
        c.execute("DROP TABLE links")
        c.execute("ALTER TABLE links_backup RENAME TO links")
        conn.commit()
        print("\n✅ Backup restaurado!")
    except:
        print("\n⚠️  Não foi possível restaurar backup")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Teste com 3 filmes")
    parser.add_argument("--restore", action="store_true", help="Restaurar backup")

    args = parser.parse_args()

    if args.restore:
        restore_backup()
    else:
        # Run test
        backup_and_clean()
        results = test_3_movies()
        show_results(results)

        print("\n💡 INSTRUÇÕES:")
        print("   1. Verifique os resultados acima")
        print("   2. Acesse o frontend e confira os 3 filmes")
        print("   3. Se estiverem corretos, podemos aplicar a todos")
        print(
            "   4. Se quiser voltar aos dados antigos: python3 test_3_movies.py --restore"
        )
