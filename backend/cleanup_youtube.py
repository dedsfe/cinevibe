#!/usr/bin/env python3
"""
Clean up duplicate/wrong YouTube links from database
Replaces YouTube embeds with NOT_FOUND so they can be re-scraped correctly
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_conn


def cleanup_youtube_links():
    """Remove or mark YouTube links as NOT_FOUND"""
    conn = get_conn()
    c = conn.cursor()

    print("=" * 80)
    print("🧹 LIMPEZA DE LINKS DO YOUTUBE (INCORRETOS)")
    print("=" * 80)
    print()

    # Find all YouTube links
    c.execute("""
        SELECT id, title, embed_url, tmdb_id 
        FROM links 
        WHERE embed_url LIKE '%youtube%' 
        AND embed_url NOT LIKE '%NOT_FOUND%'
    """)
    youtube_links = c.fetchall()

    print(f"📊 Encontrados {len(youtube_links)} links do YouTube")
    print()

    if not youtube_links:
        print("✅ Nenhum link do YouTube encontrado. Nada a limpar.")
        conn.close()
        return

    # Show some examples
    print("📝 Exemplos de links que serão limpos:")
    for link in youtube_links[:5]:
        link_id, title, url, tmdb_id = link
        video_id = (
            url.split("/embed/")[-1].split("?")[0] if "/embed/" in url else "unknown"
        )
        print(f"   • {title} (ID: {tmdb_id}) - Video: {video_id}")

    if len(youtube_links) > 5:
        print(f"   ... e mais {len(youtube_links) - 5} filmes")

    print()

    # Count duplicates
    c.execute("""
        SELECT embed_url, COUNT(*) as count, GROUP_CONCAT(title, ' | ') as titles
        FROM links 
        WHERE embed_url LIKE '%youtube%' AND embed_url NOT LIKE '%NOT_FOUND%'
        GROUP BY embed_url
        HAVING count > 1
    """)
    duplicates = c.fetchall()

    if duplicates:
        print(f"⚠️  ATENÇÃO: Encontrados {len(duplicates)} links duplicados!")
        for url, count, titles in duplicates:
            print(f"   • {count} filmes compartilham o mesmo link")
        print()

    # Ask for confirmation
    print("-" * 80)
    print("🚨 ATENÇÃO: Isso vai marcar TODOS os links do YouTube como 'NOT_FOUND'")
    print(
        "   O que significa que o sistema tentará extrair os links corretos do Opera depois."
    )
    print()

    # Auto-confirm for now (can be changed to interactive)
    print("✅ Executando limpeza automática...")
    print()

    # Update all YouTube links to NOT_FOUND
    c.execute("""
        UPDATE links 
        SET embed_url = 'NOT_FOUND'
        WHERE embed_url LIKE '%youtube%' 
        AND embed_url NOT LIKE '%NOT_FOUND%'
    """)

    updated = c.rowcount
    conn.commit()
    conn.close()

    print(f"✅ {updated} links do YouTube marcados como 'NOT_FOUND'")
    print()
    print("💡 Próximos passos:")
    print("   1. Execute: python3 enrich_catalog.py")
    print("   2. Ou: python3 bulk_scrape_tmdb.py")
    print("   3. O sistema tentará extrair os links corretos do Opera Topzera")
    print()
    print("=" * 80)


def show_integrity_report():
    """Show current integrity status"""
    conn = get_conn()
    c = conn.cursor()

    print("\n" + "=" * 80)
    print("📊 RELATÓRIO DE INTEGRIDADE ATUAL")
    print("=" * 80)

    # Total stats
    c.execute("SELECT COUNT(*) FROM links WHERE embed_url IS NOT NULL")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM links WHERE embed_url != 'NOT_FOUND'")
    valid = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM links WHERE embed_url = 'NOT_FOUND'")
    not_found = c.fetchone()[0]

    print(f"\n📈 Estatísticas Gerais:")
    print(f"   • Total de filmes no catálogo: {total}")
    print(f"   • Links válidos (MP4/jt0x): {valid}")
    print(f"   • Aguardando link (NOT_FOUND): {not_found}")

    # Check for duplicates again
    c.execute("""
        SELECT embed_url, COUNT(*) as count
        FROM links 
        WHERE embed_url != 'NOT_FOUND'
        GROUP BY embed_url
        HAVING count > 1
    """)
    duplicates = c.fetchall()

    if duplicates:
        print(f"\n⚠️  Links duplicados encontrados: {len(duplicates)}")
        for url, count in duplicates:
            if "youtube" in url:
                print(f"   • {count}x (YouTube - PROBLEMA): {url[:60]}...")
            else:
                print(f"   • {count}x: {url[:60]}...")
    else:
        print(f"\n✅ Nenhum link duplicado encontrado!")

    # Show sample of valid jt0x links
    c.execute("""
        SELECT title, embed_url 
        FROM links 
        WHERE embed_url LIKE '%jt0x.com%'
        ORDER BY RANDOM()
        LIMIT 5
    """)
    valid_links = c.fetchall()

    if valid_links:
        print(f"\n✅ Exemplos de links válidos (jt0x.com):")
        for title, url in valid_links:
            print(f"   • {title}")

    conn.close()
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Limpeza de integridade - Opera Topzera"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Limpar links do YouTube"
    )
    parser.add_argument(
        "--report", action="store_true", help="Mostrar relatório apenas"
    )

    args = parser.parse_args()

    if args.cleanup:
        cleanup_youtube_links()
    elif args.report:
        show_integrity_report()
    else:
        # Default: show report first, then offer to cleanup
        show_integrity_report()
        print("\n💡 Use --cleanup para limpar os links do YouTube")
        print("   Ou --report para apenas ver o relatório")
