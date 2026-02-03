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

async def join_and_scrape_content(app, invite_link, series_title, limit, max_success):
    print(f"🔄 Tentando entrar no canal de conteúdo: {invite_link}")
    try:
        try:
            chat = await app.join_chat(invite_link)
            chat_id = chat.id
            print(f"✅ Entrou com sucesso no canal: {chat.title} ({chat_id})")
        except Exception as e:
            if "USER_ALREADY_PARTICIPANT" in str(e):
                # We need to resolve the chat_id from the invite link if possible, 
                # or simpler: just use get_chat if it was a public username, but for +links we might need to peek.
                # If we are already participant, join_chat usually returns the chat anyway in recent Pyrogram versions?
                # If not, we might need another way. Let's assume join_chat works or returns info.
                print("   (Já é membro do canal)")
                # Inspecting invite link to see if we can get preview or just try to continue if we knew the ID.
                # For now, let's treat it as a skip or try to get chat from invite link info.
                try:
                    chat = await app.get_chat(invite_link)
                    chat_id = chat.id
                except:
                    print(f"❌ Não foi possível obter ID do chat já participado: {e}")
                    return 0, 0
            else:
                print(f"❌ Erro ao entrar: {e}")
                return 0, 0

        print(f"📚 Lendo episódios de {chat.title}...")
        
        count_series = 0
        count_movies = 0
        
        async for message in app.get_chat_history(chat_id, limit=limit):
            # Same parsing logic as before, but focused on this chat
            try:
                raw_text = message.text or message.caption or ""
                
                file_id = None
                if message.video:
                    file_id = f"tg_file_id:{message.video.file_id}"
                
                links = extract_links(message)
                video_url = file_id if file_id else (links[0] if links else None)
                
                if not video_url:
                    continue

                # Use the passed series_title, but look for specific episode info in this message
                season, episode = parse_series_info(raw_text)
                
                # If failing to parse season/ep from text, try filename
                if message.video and message.video.file_name and (season is None or episode is None):
                    fs, fe = parse_series_info(message.video.file_name)
                    if season is None: season = fs
                    if episode is None: episode = fe

                # Fallback: if we are in a "Series channel", and have video, but no explicit S/E info,
                # we might be looking at a movie file or just a tough filename.
                # But usually these channels have "S01 E01" etc.
                
                # Clean title for episode might just be "Episódio 1"
                ep_title = clean_title(raw_text) or f"Episódio {episode}"

                if season and episode and HAS_SERIES_DB:
                    print(f"   📺 [S{season:02}E{episode:02}] Found in content channel")
                    
                    opera_id = slugify(series_title)
                    s_id = save_series(opera_id, series_title, overview=f"Imported from {chat.title}")
                    if s_id:
                         ses_id = save_season(s_id, season, title=f"Temporada {season}")
                         if ses_id:
                              save_episode(s_id, ses_id, episode, 
                                         title=ep_title, 
                                         video_url=video_url,
                                         video_type='tg_file' if 'tg_file_id' in video_url else 'mp4')
                              count_series += 1
                else:
                    # Maybe it's a movie inside a collection channel?
                    pass

            except Exception as e:
                print(f"Error parsing msg {message.id}: {e}")
                
        return count_movies, count_series

    except Exception as e:
        print(f"❌ Critical error accessing content channel: {e}")
        return 0, 0


async def scrape_channel(target_channel, search_query, limit, max_success):
    print(f"\n🚀 Conectando ao Telegram...")
    async with Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH) as app:
        print(f"✅ Conectado!")
        
        # Generator: Search in Channel
        if search_query:
            print(f"🔎 Buscando por '{search_query}' em {target_channel}...")
            message_iterator = app.search_messages(target_channel, query=search_query, limit=limit)
        else:
            print(f"📚 Lendo histórico de {target_channel}...")
            message_iterator = app.get_chat_history(target_channel, limit=limit)
        
        total_movies = 0
        total_episodes = 0
        processed_links = set()
        
        async for message in message_iterator:
            # Check for "Assistir" functionality first (The new flow)
            found_assistir = False
            invite_link = None
            
            # Check Text Links
            if message.entities or message.caption_entities:
                ents = message.entities or message.caption_entities
                for ent in ents:
                    if ent.type.name == "TEXT_LINK" and ent.url:
                        # Check if it looks like a telegram invite
                        if "t.me/+" in ent.url or "t.me/joinchat" in ent.url:
                             invite_link = ent.url
                             found_assistir = True
            
            # Check Buttons
            if not found_assistir and message.reply_markup and hasattr(message.reply_markup, 'inline_keyboard'):
                for row in message.reply_markup.inline_keyboard:
                    for btn in row:
                        if "Assistir" in (btn.text or "") and btn.url:
                            invite_link = btn.url
                            found_assistir = True
            
            if found_assistir and invite_link:
                if invite_link in processed_links:
                    print(f"⏩ Link já processado, pulando: {invite_link}")
                    continue
                
                processed_links.add(invite_link)

                # Get the Series Title from this main message
                raw_text = message.text or message.caption or ""
                series_title = clean_title(raw_text)
                
                # If the title is generic "Assistir", try to parse from first line
                if "Assistir" in series_title or len(series_title) < 3:
                     # Heuristic: First line often has "Serie: Title"
                     lines = raw_text.split('\n')
                     for line in lines:
                         if "ie:" in line or "fix:" in line: # Série: or Serie:
                             parts = line.split(":")
                             if len(parts) > 1:
                                 series_title = parts[1].strip()
                                 break
                
                print(f"\n🎯 FOUND CATALOG ENTRY: {series_title}")
                print(f"   Link: {invite_link}")
                
                # Go Deep!
                m, s = await join_and_scrape_content(app, invite_link, series_title, limit=100, max_success=max_success)
                total_movies += m
                total_episodes += s
                
            else:
                # fallback to old logic for direct files in main channel
                pass 
        
        print(f"\n✨ Finalizado!")
        print(f"   Filmes: {total_movies}")
        print(f"   Episódios: {total_episodes}")

if __name__ == "__main__":
    asyncio.run(main())
