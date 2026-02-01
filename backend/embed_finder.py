import logging
import re
import asyncio
from telegram_search import search_telegram_and_process

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_EMBED_DOMAINS = [
    "streamtape.com",
    "mixdrop.co",
    "dood.watch",
    "voe.sx",
    "mp4upload.com",
    "uqload.com",
]


def extract_embed_from_text(text):
    if not text:
        return None

    pattern = r"(https?://(?:" + "|".join(VALID_EMBED_DOMAINS) + r")[^\s<>\"\'\]]+)"
    match = re.search(pattern, text, re.IGNORECASE)

    return match.group(1) if match else None


async def find_embed_for_title(title, tmdb_id=None):
    logger.info(f"Buscando embed para: {title}")

    try:
        embed_url = await search_telegram_and_process(title)

        if embed_url:
            logger.info(f"Encontrado: {embed_url}")
            return embed_url

        logger.warning(f"Nenhum embed encontrado para: {title}")
        return None

    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        return None


def validate_embed_url(url):
    import requests

    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.status_code == 200
    except:
        return False


async def get_or_search_embed(title, tmdb_id=None):
    from database import get_cached_embed, save_embed

    cached = get_cached_embed(title)

    if cached:
        logger.info(f"Cache hit para: {title}")
        if validate_embed_url(cached["embed_url"]):
            return cached["embed_url"]
        else:
            logger.warning(f"Link cacheado expirado: {title}")

    embed_url = await find_embed_for_title(title, tmdb_id)

    if embed_url:
        save_embed(title, embed_url, tmdb_id=tmdb_id)

    return embed_url
