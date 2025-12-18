import requests
from functools import lru_cache

GITHUB_REPO = "anthonyhales/TrackRota"

@lru_cache(maxsize=1)
def get_latest_release():
    try:
        r = requests.get(
            f"https://api.github.com/repos/anthonyhales/TrackRota/releases/latest",
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        return {
            "tag": data["tag_name"].lstrip("v"),
            "url": data["html_url"],
        }
    except Exception:
        return None

def normalize(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))
