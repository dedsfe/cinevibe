import time
import requests
from bs4 import BeautifulSoup
import re
import logging

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

EMBED_REGEX = re.compile(
    r'(https?://(?:streamtape\.com/embed/|mixdrop\.co/e/|dood(?:stream)?\.to/|filemoon\.[a-z]+/embed/|voe\.sx/)[^"\'\s]+)'
)

SOURCES = [
    {
        "name": "Internet Archive",
        "search_url": "https://archive.org/search.php?query={query}",
    },
    {
        "name": "YouTube Trailers",
        "search_url": "https://www.youtube.com/results?search_query={query}+trailer",
    },
]


def validate_embed(url: str) -> bool:
    try:
        r = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def extract_embeds_from_html(html: str) -> list:
    embeds = []
    for m in EMBED_REGEX.finditer(html):
        embeds.append(m.group(1))
    return embeds


def scrape_for_title(title: str, tmdb_id: str = None, year: str = None) -> str | None:
    query = title.strip().replace(" ", "+")
    if year:
        query += f"+{year}"
        
    # 1) Internet Archive search -> try to find archive embed
    try:
        url = SOURCES[0]["search_url"].format(query=query)
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Heuristic: look for links to details pages containing embeds
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/details/" in href or "archive.org/details" in href:
                    page = (
                        href
                        if href.startswith("http")
                        else "https://archive.org" + href
                    )
                    p = requests.get(page, headers=HEADERS, timeout=12)
                    if p.status_code == 200:
                        embeds = extract_embeds_from_html(p.text)
                        for e in embeds:
                            if validate_embed(e):
                                return e
    except Exception:
        pass

    time.sleep(2)
    # 2) YouTube trailers search
    try:
        url = SOURCES[1]["search_url"].format(query=query)
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            # Try to find video ids in links
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/watch?v=" in href:
                    vid = href.split("watch?v=")[-1]
                    embed = f"https://www.youtube-nocookie.com/embed/{vid}"
                    if validate_embed(embed):
                        return embed
    except Exception:
        pass

    # 3) Opera Topzera (Playwright)
    try:
        from playwright_scraper import scrape_operatopzera
        logging.info(f"Attempting Opera Topzera scrape for: {title} (Year: {year})")
        embed = scrape_operatopzera(title, year=year)
        if embed:
             # Basic validation since it comes from a trusted scrape logic
            return embed
    except Exception as e:
        logging.error(f"Opera Topzera scraper failed: {e}")

    return None
