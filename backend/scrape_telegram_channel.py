import os
import re
import asyncio
import logging
import unicodedata
from pyrogram import Client

# Import Database Functions
try:
    from database import save_embed
except ImportError:
    save_embed = lambda *a, **k: print("DB(Movie) Missing", a)

try:
    from database_series import save_series, save_season, save_episode
    HAS_SERIES_DB = True
except ImportError:
    HAS_SERIES_DB = False
    print("⚠️  Warning: backend/database_series.py not found. Series scraping will fail.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credentials
API_ID = "36556563"
API_HASH = "c04c26a0877db8f2b998813eab3cebc1" 
SESSION_NAME = "user_scraper_session"

# Patterns
LINK_PATTERNS = [
    r"(https?://streamtape\.[a-z]+/e/[a-zA-Z0-9_-]+)",
    r"(https?://mixdrop\.[a-z]+/e/[a-zA-Z0-9_-]+)",
    r"(https?://dood\.[a-z]+/e/[a-zA-Z0-9_-]+)",
    r"(https?://voe\.sx/[a-zA-Z0-9_-]+)",
    r"(https?://mp4upload\.com/embed-[a-zA-Z0-9_-]+)",
    r"(https?://filelions\.[a-z]+/v/[a-zA-Z0-9_-]+)",
    r"(https?://gofile\.io/d/[a-zA-Z0-9-]+)", 
    r"(https?://mega\.nz/file/[a-zA-Z0-9#_-]+)",
]

# Regex for extraction
URL_PATTERN = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
SERIES_PATTERN = r'(?:S|T|Temporada)?\s?(\d+)[^\d]+(?:E|Ep|Episódio)?\s?(\d+)'

SERIES_PATTERNS = [
    r"S(\d{1,2})E(\d{1,2})",       # S01E01
    r"(\d{1,2})ª?\s*Temp",         # 1ª Temporada or 1 Temp
    r"Temporada\s*(\d{1,2})",      # Temporada 1
    r"Epis[oó]dio\s*(\d{1,2})",    # Episodio 1
]

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def extract_links(message):
    """Extrai links do texto, entidades e botões."""
    links = []
    
    # 1. Plain text links
    raw_text = message.text or message.caption or ""
    found = re.findall(URL_PATTERN, raw_text)
    links.extend(found)
    
    # 2. Format entities (Hyperlinks)
    entities = message.entities or message.caption_entities
    if entities:
        for ent in entities:
            if ent.type == "text_link":
                links.append(ent.url)
            elif ent.type == "url":
                # Some clients don't put URL in text_link but just 'url'
                 # We already got these via regex, but let's be safe
                 pass

    # 3. Buttons (Reply Markup)
    if message.reply_markup and hasattr(message.reply_markup, 'inline_keyboard'):
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                if button.url:
                    links.append(button.url)
                    
    return list(set(links))

def clean_title(text):
    if not text: return "Sem Título"
    title_line = text.split('\n')[0].strip()
    # Remove common junk
    title_line = re.sub(r"S\d{1,2}E\d{1,2}.*", "", title_line) # Remove S01E01... from title
    title_line = re.sub(r"#\w+", "", title_line) # Remove hashtags
    return title_line.strip(" -|")

def parse_series_info(text):
    """Returns (season_num, episode_num) or (None, None)"""
    # Try S01E01 format first (most reliable)
    match = re.search(r"S(\d{1,2})E(\d{1,2})", text, re.I)
    if match:
        return int(match.group(1)), int(match.group(2))
    
    # Try separate Season/Episode info
    season = 1
    episode = None
    
    s_match = re.search(r"(\d{1,2})ª?\s*Temp|Temporada\s*(\d{1,2})", text, re.I)
    if s_match:
        season = int(s_match.group(1) or s_match.group(2))
        
    e_match = re.search(r"Epis[oó]dio\s*(\d{1,2})|E(\d{1,2})", text, re.I)
    if e_match:
        episode = int(e_match.group(1) or e_match.group(2))
        
    return season, episode

async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default="BaixarSeriesMP4Club", help="Target channel")
    parser.add_argument("--query", default="", help="Search query")
    parser.add_argument("--limit", type=int, default=50, help="Max messages to scan")
    parser.add_argument("--count", type=int, default=0, help="Stop after N items saved (0 = no limit)")
    args = parser.parse_args()

    print("=== Telegram Smart Scraper ===")
    
    # Use args if provided, otherwise fallback to defaults (avoid interactive input if args present)
    # But to support "manual" run without args, we should check if any args were passed or just default.
    # Decision: Fully switch to argparse to allow Agent to run it easily.
    
    print(f"Target: {args.channel}")
    print(f"Query: {args.query if args.query else '[ALL]'}")
    print(f"Limit: {args.limit}")
    print(f"Max items to save: {args.count if args.count > 0 else 'No limit'}")

    await scrape_channel(args.channel, args.query, args.limit, args.count)

async def scrape_channel(target_channel, search_query, limit, max_success):
    print(f"\n🚀 Conectando ao Telegram...")
    async with Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH) as app:
        print(f"✅ Conectado!")
        
        # Generator: Search in Channel, Global Search, or History
        if search_query:
            print(f"🔎 Buscando por '{search_query}'...")
            if target_channel:
                print(f"   (Filtro: {target_channel})")
                message_iterator = app.search_messages(target_channel, query=search_query, limit=limit)
            else:
                message_iterator = app.search_global(query=search_query, limit=limit)
        else:
            print(f"📚 Lendo histórico de {target_channel}...")
            message_iterator = app.get_chat_history(target_channel, limit=limit)
        
        count_movies = 0
        count_series = 0
        count_total = 0
        found_any = False
        
        async for message in message_iterator:
            found_any = True
            if max_success > 0 and count_total >= max_success:
                break
            
            # For Global search fallback, if user specified a channel, only pick that channel
            if target_channel and not search_query.startswith("GLOBAL:"):
                # verify chat
                pass # search_messages already filters
            
            try:
                # 1. Get Content
                raw_text = message.text or message.caption or ""
                
                # Check for Video File
                file_id = None
                if message.video:
                    file_id = f"tg_file_id:{message.video.file_id}"
                
                # Check for Links
                links = extract_links(message)
                
                # If it's a "following" message redirecting to another channel
                # e.g., t.me/c/123/456 or @Channel
                # For now, let's just take the first link found
                video_url = file_id if file_id else (links[0] if links else None)
                
                if not video_url:
                    continue 

                # 2. Analyze Content
                title = clean_title(raw_text)
                if not title or len(title) < 3:
                    # Try to get title from video file name
                    if message.video and message.video.file_name:
                        title = clean_title(message.video.file_name)
                
                if not title: title = f"Video_{message.id}"

                season, episode = parse_series_info(raw_text)
                
                # 3. Save to DB
                success = False
                if season is not None and episode is not None and HAS_SERIES_DB:
                    print(f"📺 [S{season:02}E{episode:02}] {title}")
                    
                    opera_id = slugify(title)
                    s_id = save_series(opera_id, title, overview=raw_text)
                    if s_id:
                        ses_id = save_season(s_id, season, title=f"Temporada {season}")
                        if ses_id:
                             save_episode(s_id, ses_id, episode, 
                                        title=f"Episódio {episode}", 
                                        video_url=video_url,
                                        video_type='tg_file' if 'tg_file_id' in video_url else 'mp4')
                             count_series += 1
                             success = True
                else:
                    print(f"🎬 [Movie] {title}")
                    save_embed(title, video_url, tmdb_id=None, overview=raw_text)
                    count_movies += 1
                    success = True
                
                if success:
                    count_total += 1
                    if max_success > 0 and count_total >= max_success:
                        break
                    
            except Exception as e:
                pass # Silently skip errors for global search noise

        if not found_any and search_query:
            print(f"⚠️  Nenhuma mensagem encontrada para '{search_query}'.")

        print(f"\n✨ Finalizado!")
        print(f"   Filmes: {count_movies}")
        print(f"   Episódios: {count_series}")

if __name__ == "__main__":
    asyncio.run(main())
