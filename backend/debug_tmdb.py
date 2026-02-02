import requests

TMDB_API_KEY = "909fc389a150847bdd4ffcd92809cff7"
BASE_URL = "https://api.themoviedb.org/3"

def test_search(title):
    print(f"Searching for: '{title}'")
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "pt-BR",
        "page": 1
    }
    res = requests.get(url, params=params)
    print("Status:", res.status_code)
    data = res.json()
    if data.get("results"):
        print("Match:", data["results"][0]["title"])
    else:
        print("No match.")
        print("Response:", data)

if __name__ == "__main__":
    test_search("Americana")
    test_search("O Falsário")
    test_search("Play") # Should fail
