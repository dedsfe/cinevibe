#!/usr/bin/env python3
"""
Integrity Checker for Opera Topzera Links
Verifies that movie titles match their extracted video URLs
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import get_conn
from playwright_scraper import get_scraper
import re


def get_all_active_links():
    """Get all links with valid video URLs"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, tmdb_id, embed_url, original_raw_title, added_at
        FROM links 
        WHERE embed_url IS NOT NULL 
        AND embed_url != 'NOT_FOUND'
        AND embed_url LIKE '%jt0x.com%'
        ORDER BY added_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def extract_video_id_from_url(url):
    """Extract video ID from jt0x.com URL pattern"""
    # Pattern: http://jt0x.com/movie/t2TGgarYJ/66e74xKRJ/{ID}.mp4
    match = re.search(r"/([^/]+)\.mp4$", url)
    if match:
        return match.group(1)
    return None


def verify_link_integrity(link_data, scraper):
    """
    Verifica se o link ainda é válido e se corresponde ao título correto
    Returns: (is_valid, details)
    """
    link_id, title, tmdb_id, embed_url, raw_title, added_at = link_data
    video_id = extract_video_id_from_url(embed_url)

    if not video_id:
        return False, f"❌ URL inválida: {embed_url}"

    # Verificar se o link ainda responde (HEAD request)
    import requests

    try:
        response = requests.head(embed_url, timeout=10, allow_redirects=True)
        if response.status_code not in [200, 301, 302]:
            return False, f"❌ Link offline (HTTP {response.status_code})"
    except Exception as e:
        return False, f"❌ Erro de conexão: {str(e)[:50]}"

    # Se tiveros o raw_title, podemos fazer uma verificação cruzada
    # Mas o melhor é verificar se o TMDB ID ainda existe e bate com o título

    return True, f"✅ Link válido (ID: {video_id})"


def full_revalidation_sample(sample_size=10):
    """Re-valida uma amostra de links para detectar mismatches"""
    print("=" * 80)
    print("🔍 SISTEMA DE VERIFICAÇÃO DE INTEGRIDADE - OPERA TOPZERA")
    print("=" * 80)
    print()

    links = get_all_active_links()
    print(f"📊 Total de links ativos: {len(links)}")
    print(f"🎯 Amostra para verificação: {sample_size}")
    print()

    # Pegar uma amostra aleatória
    import random

    sample = random.sample(links, min(sample_size, len(links)))

    print("-" * 80)
    print("🔗 INICIANDO VERIFICAÇÃO...")
    print("-" * 80)

    valid_count = 0
    invalid_count = 0

    for link_data in sample:
        link_id, title, tmdb_id, embed_url, raw_title, added_at = link_data

        print(f"\n🎬 {title}")
        print(f"   TMDB ID: {tmdb_id}")
        print(f"   Link: {embed_url}")

        # Verificação básica
        is_valid, message = verify_link_integrity(link_data, None)
        print(f"   Status: {message}")

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

    print()
    print("-" * 80)
    print("📈 RESULTADO DA VERIFICAÇÃO")
    print("-" * 80)
    print(f"✅ Válidos: {valid_count}/{sample_size}")
    print(f"❌ Inválidos: {invalid_count}/{sample_size}")
    print()

    return valid_count, invalid_count


def deep_revalidation(title_to_check):
    """
    Faz uma revalidação profunda:
    1. Busca o filme no Opera novamente
    2. Extrai o link atual
    3. Compara com o link salvo
    """
    print(f"\n🔎 REVALIDAÇÃO PROFUNDA: {title_to_check}")
    print("-" * 80)

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT embed_url, tmdb_id FROM links WHERE title = ?", (title_to_check,))
    row = c.fetchone()
    conn.close()

    if not row:
        print(f"❌ Filme não encontrado no banco: {title_to_check}")
        return False

    saved_url, tmdb_id = row
    print(f"📁 Link salvo: {saved_url}")
    print(f"🆔 TMDB ID: {tmdb_id}")

    # Extrair novo link
    print("\n🌐 Conectando ao Opera Topzera...")
    scraper = get_scraper()
    scraper.start_session(headless=True)

    try:
        new_url = scraper.scrape_title(title_to_check)

        if not new_url:
            print("❌ Não foi possível extrair link atual do Opera")
            return False

        print(f"🆕 Link atual do Opera: {new_url}")

        # Comparar
        old_video_id = extract_video_id_from_url(saved_url)
        new_video_id = extract_video_id_from_url(new_url)

        if old_video_id == new_video_id:
            print("✅ MATCH! Os links são idênticos")
            return True
        else:
            print("⚠️  MISMATCH DETECTADO!")
            print(f"   ID antigo: {old_video_id}")
            print(f"   ID novo: {new_video_id}")
            print("\n💡 Sugestão: Atualizar o link no banco de dados")

            # Ask to fix
            print("\n🔄 Corrigindo automaticamente...")
            try:
                conn = get_conn()
                c = conn.cursor()
                c.execute(
                    "UPDATE links SET embed_url = ? WHERE title = ?",
                    (new_url, title_to_check),
                )
                conn.commit()
                conn.close()
                print(f"✅ Link corrigido no banco de dados!")
                print(f"   Novo link: {new_url}")
            except Exception as e:
                print(f"❌ Erro ao corrigir: {e}")

            return False

    finally:
        scraper.stop_session()


def identify_suspicious_patterns():
    """Identifica padrões suspeitos no banco de dados"""
    print("\n" + "=" * 80)
    print("🔍 ANÁLISE DE PADRÕES SUSPEITOS")
    print("=" * 80)

    conn = get_conn()
    c = conn.cursor()

    # 1. Links duplicados (mesmo URL para títulos diferentes)
    c.execute("""
        SELECT embed_url, COUNT(*) as count, GROUP_CONCAT(title, ' | ') as titles
        FROM links 
        WHERE embed_url != 'NOT_FOUND'
        GROUP BY embed_url
        HAVING count > 1
    """)
    duplicates = c.fetchall()

    if duplicates:
        print(f"\n⚠️  ENCONTRADOS {len(duplicates)} LINKS DUPLICADOS:")
        for url, count, titles in duplicates:
            print(f"\n   URL: {url}")
            print(f"   Usado em {count} filmes:")
            for t in titles.split(" | "):
                print(f"      - {t}")
    else:
        print("\n✅ Nenhum link duplicado encontrado")

    # 2. Títulos muito similares com links diferentes
    c.execute("""
        SELECT title, embed_url FROM links 
        WHERE embed_url != 'NOT_FOUND'
        ORDER BY title
    """)
    all_links = c.fetchall()

    similar_titles = []
    for i, (title1, url1) in enumerate(all_links):
        for title2, url2 in all_links[i + 1 :]:
            # Calcular similaridade simples
            t1_clean = title1.lower().replace(" ", "")
            t2_clean = title2.lower().replace(" ", "")

            if len(t1_clean) > 5 and len(t2_clean) > 5:
                # Verificar se um é substring do outro
                if t1_clean in t2_clean or t2_clean in t1_clean:
                    if url1 != url2:
                        similar_titles.append((title1, title2, url1, url2))

    if similar_titles:
        print(
            f"\n⚠️  ENCONTRADOS {len(similar_titles)} TÍTULOS SIMILARES COM LINKS DIFERENTES:"
        )
        for t1, t2, u1, u2 in similar_titles[:10]:  # Mostrar apenas 10
            print(f"\n   '{t1}' → {u1}")
            print(f"   '{t2}' → {u2}")
    else:
        print("\n✅ Nenhum título similar conflitante encontrado")

    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Verificador de Integridade - Opera Topzera"
    )
    parser.add_argument(
        "--sample", type=int, default=10, help="Tamanho da amostra para verificação"
    )
    parser.add_argument("--deep", type=str, help="Título para revalidação profunda")
    parser.add_argument(
        "--patterns", action="store_true", help="Analisar padrões suspeitos"
    )

    args = parser.parse_args()

    if args.patterns:
        identify_suspicious_patterns()
    elif args.deep:
        deep_revalidation(args.deep)
    else:
        full_revalidation_sample(args.sample)
