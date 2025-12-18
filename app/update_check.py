import requests
import re

GITHUB_REPO = "anthonyhales/TrackRota"

def get_latest_release():
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        return {
            "tag": data["tag_name"].lstrip("v"),
            "url": data["html_url"],
        }
    except Exception as e:
        print("GitHub update check failed:", e)
        return None

def normalize(v: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", v)
    return tuple(int(p) for p in parts)
