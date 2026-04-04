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


def esc(text):
    """Escape pipe characters that break markdown tables."""
    return text.replace("|", "\\|")


def build_table(header_cols, rows):
    """Build a markdown table string."""
    lines = []
    lines.append("| " + " | ".join(header_cols) + " |")
    lines.append("| " + " | ".join("---" for _ in header_cols) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_section(tracks, artists, albums):
    track_rows = []
    for i, track in enumerate(tracks, 1):
        name = esc(track["name"])
        artist = esc(track["artists"][0]["name"])
        url = track["external_urls"]["spotify"]
        track_rows.append([str(i), f"[{name}]({url})", artist])
    tracks_table = build_table(["#", "Track", "Artist"], track_rows)

    artist_rows = []
    for i, artist in enumerate(artists, 1):
        name = esc(artist["name"])
        url = artist["external_urls"]["spotify"]
        artist_rows.append([str(i), f"[{name}]({url})"])
    artists_table = build_table(["#", "Artist"], artist_rows)

    album_rows = []
    for i, album in enumerate(albums, 1):
        album_rows.append([str(i), f"[{esc(album['name'])}]({album['url']})", esc(album["artist"])])
    albums_table = build_table(["#", "Album", "Artist"], album_rows)

    lines = [
        "<!-- SPOTIFY:START -->",
        "## My Spotify This Month",
        "",
        "<table>",
        "  <tr>",
        '    <td valign="top">',
        "",
        "**Top Tracks**",
        "",
        tracks_table,
        "",
        "   </td>",
        '    <td valign="top">',
        "",
        "**Top Artists**",
        "",
        artists_table,
        "",
        "   </td>",
        '    <td valign="top">',
        "",
        "**Top Albums**",
        "",
        albums_table,
        "",
        "   </td>",
        "  </tr>",
        "</table>",
        "<!-- SPOTIFY:END -->",
    ]
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
