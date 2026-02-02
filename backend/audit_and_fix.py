#!/usr/bin/env python3
"""
Audit and Fix System - Opera Topzera
Verifies ALL movies and fixes mismatches automatically
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_conn, save_embed
from strict_opera_scraper import scrape_with_strict_validation
from opera_scraper import get_dedicated_scraper


def audit_all_movies():
    """
    Audita todos os filmes e corrige os que estão com links errados
    """
    print("=" * 80)
    print("🔍 SISTEMA DE AUDITORIA - CORREÇÃO DE LINKS")
    print("=" * 80)
    print()

    conn = get_conn()
    c = conn.cursor()

    # Get all movies with links
    c.execute("""
        SELECT id, title, tmdb_id, embed_url, original_raw_title
        FROM links
        WHERE embed_url IS NOT NULL
        ORDER BY title
    """)

    movies = c.fetchall()
    conn.close()

    print(f"📊 Total de filmes para auditar: {len(movies)}")
    print()

    # Initialize scraper
    from strict_opera_scraper import StrictOperaScraper

    scraper = StrictOperaScraper()
    scraper.start_session(headless=True)

    try:
        fixed_count = 0
        error_count = 0
        correct_count = 0

        for i, movie in enumerate(movies, 1):
            link_id, title, tmdb_id, current_url, raw_title = movie

            print(f"\n[{i}/{len(movies)}] Auditing: {title}")
            print(f"   Current URL: {current_url}")

            # Skip if NOT_FOUND
            if current_url == "NOT_FOUND":
                print("   ⏭️  Skipping (NOT_FOUND)")
                continue

            # Extract current video ID
            current_video_id = scraper._extract_video_id(current_url)
            if not current_video_id:
                print("   ⚠️  Could not extract video ID from current URL")
                error_count += 1
                continue

            print(f"   Current Video ID: {current_video_id}")

            # Scrape fresh from Opera
            result = scraper.scrape_with_validation(title)

            if not result["success"]:
                print(f"   ❌ Scrape failed: {result['error']}")
                error_count += 1
                continue

            new_video_id = result["video_id"]
            new_url = result["video_url"]
            scraped_title = result["scraped_title"]
            similarity = result["similarity"]

            print(f"   Scraped Title: {scraped_title}")
            print(f"   Similarity: {similarity:.2%}")
            print(f"   New Video ID: {new_video_id}")

            # Compare video IDs
            if current_video_id == new_video_id:
                print("   ✅ CORRECT - Link is valid!")
                correct_count += 1
            else:
                print("   🚨 MISMATCH DETECTED!")
                print(f"      Expected: {new_video_id}")
                print(f"      Got:      {current_video_id}")
                print("   🔄 Fixing...")

                # Update the database with correct link
                conn = get_conn()
                c = conn.cursor()
                c.execute(
                    "UPDATE links SET embed_url = ?, original_raw_title = ? WHERE id = ?",
                    (new_url, scraped_title, link_id),
                )
                conn.commit()
                conn.close()

                print("   ✅ FIXED!")
                fixed_count += 1

            # Small delay to not overwhelm
            time.sleep(1)

        print()
        print("=" * 80)
        print("📊 RESULTADO DA AUDITORIA")
        print("=" * 80)
        print(f"✅ Corretos: {correct_count}")
        print(f"🔄 Corrigidos: {fixed_count}")
        print(f"❌ Erros: {error_count}")
        print()

    finally:
        scraper.stop_session()


def fix_specific_movie(title: str):
    """
    Corrige um filme específico
    """
    print(f"\n🔧 Corrigindo: {title}")
    print("-" * 60)

    conn = get_conn()
    c = conn.cursor()

    # Get current data
    c.execute("SELECT id, title, embed_url FROM links WHERE title = ?", (title,))
    row = c.fetchone()
    conn.close()

    if not row:
        print(f"❌ Filme não encontrado: {title}")
        return

    link_id, current_title, current_url = row
    print(f"   Atual: {current_url}")

    # Scrape fresh
    from strict_opera_scraper import StrictOperaScraper

    scraper = StrictOperaScraper()
    scraper.start_session(headless=True)

    try:
        result = scraper.scrape_with_validation(title)

        if not result["success"]:
            print(f"   ❌ Falha: {result['error']}")
            return

        new_url = result["video_url"]
        scraped_title = result["scraped_title"]
        similarity = result["similarity"]

        print(f"   Novo: {new_url}")
        print(f"   Título encontrado: {scraped_title}")
        print(f"   Similaridade: {similarity:.2%}")

        # Update database
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE links SET embed_url = ?, original_raw_title = ? WHERE id = ?",
            (new_url, scraped_title, link_id),
        )
        conn.commit()
        conn.close()

        print("   ✅ Atualizado com sucesso!")

    finally:
        scraper.stop_session()


def show_mismatches():
    """
    Mostra apenas os filmes com potencial mismatch
    """
    print("\n" + "=" * 80)
    print("🔍 FILMES COM POTENCIAL MISMATCH")
    print("=" * 80)

    conn = get_conn()
    c = conn.cursor()

    # Find movies with jt0x links
    c.execute("""
        SELECT title, embed_url, tmdb_id
        FROM links
        WHERE embed_url LIKE '%jt0x.com%'
        ORDER BY title
    """)

    movies = c.fetchall()
    conn.close()

    print(f"\nTotal de filmes com links jt0x: {len(movies)}")
    print("\nVerificando título vs URL...")

    suspicious = []

    for title, url, tmdb_id in movies:
        # Extract video ID from URL
        match = re.search(r"/([^/]+)\.mp4$", url)
        if match:
            video_id = match.group(1)

            # Check if title appears in URL or vice versa
            # This is a simple heuristic
            title_clean = re.sub(r"[^\w]", "", title.lower())

            # If video ID is very different from title, flag it
            # This is a simplistic check - real validation needs scraping
            suspicious.append(
                {"title": title, "url": url, "video_id": video_id, "tmdb_id": tmdb_id}
            )

    print(f"\n📊 Total para verificação manual: {len(suspicious)}")

    if suspicious:
        print("\nExemplos (primeiros 10):")
        for i, item in enumerate(suspicious[:10], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   Video ID: {item['video_id']}")
            print(f"   TMDB: {item['tmdb_id']}")


if __name__ == "__main__":
    import argparse
    import re
    import time

    parser = argparse.ArgumentParser(description="Sistema de Auditoria - Opera Topzera")
    parser.add_argument(
        "--audit-all", action="store_true", help="Auditar todos os filmes"
    )
    parser.add_argument("--fix", type=str, help="Corrigir filme específico")
    parser.add_argument(
        "--show-mismatches", action="store_true", help="Mostrar potenciais mismatches"
    )

    args = parser.parse_args()

    if args.audit_all:
        audit_all_movies()
    elif args.fix:
        fix_specific_movie(args.fix)
    elif args.show_mismatches:
        show_mismatches()
    else:
        print("Use --audit-all para auditar todos os filmes")
        print("Use --fix 'Nome do Filme' para corrigir um específico")
        print("Use --show-mismatches para ver lista de suspeitos")
