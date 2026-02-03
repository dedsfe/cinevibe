import asyncio
from pyrogram import Client

API_ID = "36556563"
API_HASH = "c04c26a0877db8f2b998813eab3cebc1"
SESSION_NAME = "user_scraper_session"

async def main():
    async with Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH) as app:
        print("🔎 Buscando 'Bridgerton' (Filtrando vídeos/links)...")
        async for msg in app.search_global("Bridgerton", limit=50):
            text = msg.text or msg.caption or ""
            links = [b.url for row in (msg.reply_markup.inline_keyboard if msg.reply_markup and hasattr(msg.reply_markup, 'inline_keyboard') else []) for b in row if b.url]
            
            if msg.video or links:
                chat_name = msg.chat.title or "Unknown"
                username = msg.chat.username or "NoUser"
                print(f"\n--- [{chat_name}] (@{username}) ---")
                print(f"ID: {msg.id}")
                if msg.video:
                    print(f"VIDEO: {msg.video.file_name} ({msg.video.file_size // 1024 // 1024}MB)")
                if links:
                    print(f"LINKS: {links}")
                print(f"TEXT: {text[:100]}...")
            chat_name = msg.chat.title or "Unknown"
            username = msg.chat.username or "NoUser"
            text = msg.text or msg.caption or "No Text"
            print(f"\n--- Chat: {chat_name} (@{username}) ---")
            print(f"ID: {msg.id}")
            print(f"Text: {text[:200]}...")
            
            if msg.reply_markup and hasattr(msg.reply_markup, 'inline_keyboard'):
                print("Buttons:")
                for row in msg.reply_markup.inline_keyboard:
                    for btn in row:
                        if btn.url:
                            print(f"  [{btn.text}] -> {btn.url}")
            
            if msg.video:
                print(f"Video File: {msg.video.file_name} ({msg.video.file_size} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
