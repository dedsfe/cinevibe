import requests
import time

API_URL = "https://frontend-videos-api-production.up.railway.app/api/get-embed"

# List of Barbie movies to pre-warm
MOVIES = [
    {"title": "Barbie", "year": "2023", "tmdbId": "346698"},
    {"title": "Barbie em A Princesa e a Plebeia", "year": "2004", "tmdbId": "15165"},
    {"title": "Barbie: Escola de Princesas", "year": "2011", "tmdbId": "73398"},
    {"title": "Barbie e as 12 Bailarinas", "year": "2006", "tmdbId": "15015"},
    {"title": "Barbie e o Castelo de Diamante", "year": "2008", "tmdbId": "15014"},
    {"title": "Barbie em as Três Mosqueteiras", "year": "2009", "tmdbId": "23356"},
    {"title": "Barbie e o Segredo das Fadas", "year": "2011", "tmdbId": "52763"},
    {"title": "Barbie em Vida de Sereia", "year": "2010", "tmdbId": "34015"},
    {"title": "Barbie: A Sereia das Pérolas", "year": "2014", "tmdbId": "252270"},
    {"title": "Barbie e o Portal Secreto", "year": "2014", "tmdbId": "283594"},
]

print(f"🔥 Pre-warming cache for {len(MOVIES)} Barbie movies on PRODUCTION...")
print(f"Target: {API_URL}")

for movie in MOVIES:
    print(f"\nProcessing: {movie['title']} ({movie['year']})...")
    try:
        start = time.time()
        # Ensure we send the correct structure
        payload = {
            "title": movie["title"],
            "tmdbId": movie["tmdbId"],
            "year": movie["year"]
        }
        
        response = requests.post(API_URL, json=payload, timeout=60)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if data.get("embedUrl"):
                cached_msg = " [CACHED]" if data.get("cached") else " [NEWLY INDEXED]"
                print(f"✅ SUCCESS ({elapsed:.1f}s): {data['embedUrl']}{cached_msg}")
            else:
                print(f"⚠️  Authorized but no URL: {data}")
        else:
            print(f"❌ FAILED ({response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"💥 ERROR: {e}")

print("\n✨ Pre-warming complete.")
