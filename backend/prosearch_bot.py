import os
import re
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

API_ID = os.environ.get("TELEGRAM_API_ID")
API_HASH = os.environ.get("TELEGRAM_API_HASH")
PHONE = os.environ.get("TELEGRAM_PHONE")

SESSION_FILE = "prosearch_session"


async def search_movie_on_bot(movie_title):
    """
    Sends a message to @ProSearchM11Bot and reads the response
    """
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

    try:
        await client.start(phone=PHONE)

        bot_username = "ProSearchM11Bot"

        await client.send_message(bot_username, movie_title)

        await asyncio.sleep(3)

        messages = await client.get_messages(bot_username, limit=5)

        for message in messages:
            if message.out and movie_title in message.text:
                continue

            text = message.text if message.text else ""

            embed_patterns = [
                r"(https?://streamtape\.com/embed-[\w-]+)",
                r"(https?://mixdrop\.co/e/[\w-]+)",
                r"(https?://dood\.watch/e/[\w-]+)",
                r"(https?://voe\.sx/[\w-]+)",
                r"(https?://mp4upload\.com/embed-[\w-]+)",
                r"(https?://uqload\.com/[\w-]+)",
                r"(https?://filelions\.com/embed/[\w-]+)",
            ]

            for pattern in embed_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    await client.disconnect()
                    return match.group(1)

        await client.disconnect()
        return None

    except SessionPasswordNeededError:
        print("2FA password required")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


async def main():
    if not API_ID or not API_HASH or not PHONE:
        print("Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        return

    movie = input("Movie name: ")
    result = await search_movie_on_bot(movie)

    if result:
        print(f"Found: {result}")
    else:
        print("Not found")


if __name__ == "__main__":
    asyncio.run(main())
