"""
Fetches recently played tracks from Spotify and updates README.md
with the track list. Called by the GitHub Action.
"""

import os
import re
import requests
from datetime import datetime

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]


def get_access_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    return response.json()["access_token"]


def get_recently_played(token, limit=8):
    response = requests.get(
        "https://api.spotify.com/v1/me/player/recently-played",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": limit},
    )
    return response.json()["items"]


def format_tracks(items):
    seen = set()
    lines = []
    for item in items:
        track = item["track"]
        name = track["name"]
        artist = track["artists"][0]["name"]
        url = track["external_urls"]["spotify"]
        key = f"{name}-{artist}"
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"| [{name}]({url}) | {artist} |")
    return lines


def build_section(track_lines):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "<!-- SPOTIFY:START -->\n"
        f"🎧 **Recently Played** *(updated {now})*\n\n"
        "| Track | Artist |\n"
        "|---|---|\n"
    )
    footer = "\n<!-- SPOTIFY:END -->"
    return header + "\n".join(track_lines) + footer


def update_readme(section):
    with open("README.md", "r") as f:
        content = f.read()

    pattern = r"<!-- SPOTIFY:START -->.*?<!-- SPOTIFY:END -->"
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, section, content, flags=re.DOTALL)
    else:
        content = content.rstrip() + "\n\n" + section + "\n"

    with open("README.md", "w") as f:
        f.write(content)


def main():
    token = get_access_token()
    items = get_recently_played(token)
    track_lines = format_tracks(items)
    section = build_section(track_lines)
    update_readme(section)
    print(f"Updated README with {len(track_lines)} tracks")


if __name__ == "__main__":
    main()
