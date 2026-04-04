"""
Fetches top tracks, artists, and albums from Spotify and updates README.md.
Uses short_term time range (~last 4 weeks). Called by the GitHub Action.
"""

import os
import re
import requests
from collections import Counter

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]
BLOCKED_ARTISTS = {
    name.strip().lower()
    for name in os.environ.get("SPOTIFY_BLOCKED_ARTISTS", "").split(",")
    if name.strip()
}
TIME_RANGE = "short_term"  # ~last 4 weeks (closest to "this week")


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


def is_blocked(artist_name):
    return artist_name.lower() in BLOCKED_ARTISTS


def get_top_tracks(token, limit=5):
    response = requests.get(
        "https://api.spotify.com/v1/me/top/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 50, "time_range": TIME_RANGE},
    )
    items = [t for t in response.json()["items"] if not is_blocked(t["artists"][0]["name"])]
    return items[:limit]


def get_top_artists(token, limit=5):
    response = requests.get(
        "https://api.spotify.com/v1/me/top/artists",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 50, "time_range": TIME_RANGE},
    )
    items = [a for a in response.json()["items"] if not is_blocked(a["name"])]
    return items[:limit]


def get_top_albums(token):
    """Derive top albums from top 50 tracks."""
    response = requests.get(
        "https://api.spotify.com/v1/me/top/tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 50, "time_range": TIME_RANGE},
    )
    tracks = [t for t in response.json()["items"] if not is_blocked(t["artists"][0]["name"])]
    album_counts = Counter()
    album_info = {}
    for track in tracks:
        album = track["album"]
        album_id = album["id"]
        album_counts[album_id] += 1
        if album_id not in album_info:
            album_info[album_id] = {
                "name": album["name"],
                "artist": album["artists"][0]["name"],
                "url": album["external_urls"]["spotify"],
            }
    top_ids = [aid for aid, _ in album_counts.most_common(5)]
    return [album_info[aid] for aid in top_ids]


def build_section(tracks, artists, albums):
    lines = ["<!-- SPOTIFY:START -->", "🎧 **My Spotify This Month**", ""]

    lines.append("**Top Tracks**")
    lines.append("")
    lines.append("| # | Track | Artist |")
    lines.append("|---|---|---|")
    for i, track in enumerate(tracks, 1):
        name = track["name"]
        artist = track["artists"][0]["name"]
        url = track["external_urls"]["spotify"]
        lines.append(f"| {i} | [{name}]({url}) | {artist} |")

    lines.append("")
    lines.append("**Top Artists**")
    lines.append("")
    lines.append("| # | Artist |")
    lines.append("|---|---|")
    for i, artist in enumerate(artists, 1):
        name = artist["name"]
        url = artist["external_urls"]["spotify"]
        lines.append(f"| {i} | [{name}]({url}) |")

    lines.append("")
    lines.append("**Top Albums**")
    lines.append("")
    lines.append("| # | Album | Artist |")
    lines.append("|---|---|---|")
    for i, album in enumerate(albums, 1):
        lines.append(f"| {i} | [{album['name']}]({album['url']}) | {album['artist']} |")

    lines.append("<!-- SPOTIFY:END -->")
    return "\n".join(lines)


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
    tracks = get_top_tracks(token)
    artists = get_top_artists(token)
    albums = get_top_albums(token)
    section = build_section(tracks, artists, albums)
    update_readme(section)
    print(f"Updated README with {len(tracks)} tracks, {len(artists)} artists, {len(albums)} albums")


if __name__ == "__main__":
    main()
