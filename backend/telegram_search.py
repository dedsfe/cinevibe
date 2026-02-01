import os
import re
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeededError

API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
SESSION_NAME = "cinevibe_session"

client = None


async def init_client():
    global client
    if client is None:
        client = Client(SESSION_NAME, API_ID, API_HASH)
        await client.start()
    return client


async def search_movie(movie_title):
    app = await init_client()

    await app.send_message("ProSearchM11Bot", movie_title)
    import asyncio

    await asyncio.sleep(3)

    async for message in app.get_chat_history("ProSearchM11Bot", limit=5):
        if message.outgoing:
            continue

        text = message.text or ""

        patterns = [
            r"(https?://streamtape\.com/embed-[\w-]+)",
            r"(https?://mixdrop\.co/e/[\w-]+)",
            r"(https?://dood\.watch/e/[\w-]+)",
            r"(https?://voe\.sx/[\w-]+)",
            r"(https?://mp4upload\.com/embed-[\w-]+)",
        ]

        for p in patterns:
            match = re.search(p, text, re.I)
            if match:
                return match.group(1)

    return None


async def search_telegram_and_process(title):
    try:
        return await search_movie(title)
    except Exception as e:
        print(f"Error: {e}")
        return None
