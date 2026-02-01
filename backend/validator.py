import requests


def validate_embed(url: str) -> bool:
    try:
        r = requests.head(url, timeout=8, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False
