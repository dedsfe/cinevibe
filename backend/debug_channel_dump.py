import asyncio
from pyrogram import Client

API_ID = "36556563"
API_HASH = "c04c26a0877db8f2b998813eab3cebc1"
SESSION_NAME = "user_scraper_session"

async def main():
    async with Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH) as app:
        print("🔍 Procurando ID do canal...")
        async for dialog in app.get_dialogs():
            if "Stranger Things" in (dialog.chat.title or ""):
                print(f"FOUND: {dialog.chat.title} | ID: {dialog.chat.id}")
                print(f"📚 Lendo últimas 20 mensagens...")
                async for msg in app.get_chat_history(dialog.chat.id, limit=20):
                    text = (msg.text or msg.caption or "No Text")[:100].replace('\n', ' ')
                    has_video = bool(msg.video)
                    print(f"[{msg.id}] Video: {has_video} | {text}")
                break

if __name__ == "__main__":
    asyncio.run(main())
