import os
import re
import asyncio
from pyrogram import Client

API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
PHONE = os.environ.get("TELEGRAM_PHONE")


async def search_movie(movie_title):
    app = Client("prosearch_session", api_id=API_ID, api_hash=API_HASH)

    async with app:
        await app.send_message("ProSearchM11Bot", movie_title)
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


if __name__ == "__main__":
    if not API_ID:
        print("Set TELEGRAM_API_ID and TELEGRAM_API_HASH")
    else:
        movie = input("Movie: ")
        result = asyncio.run(search_movie(movie))
        print(f"Result: {result}" if result else "Not found")
