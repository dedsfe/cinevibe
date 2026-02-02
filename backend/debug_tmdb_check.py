import requests

TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"
BASE_URL = "https://api.themoviedb.org/3"

def search(query):
    print(f"Searching for: {query}")
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "language": "pt-BR"
    }
    res = requests.get(url, params=params)
    data = res.json()
    if data.get("results"):
        first = data["results"][0]
        print(f"MATCH FOUND: {first['title']} (ID: {first['id']})")
        print(f"Overview: {first['overview'][:50]}...")
        print(f"Date: {first.get('release_date')}")
    else:
        print("NO MATCH found in /search/movie")

search("The Pitt")
