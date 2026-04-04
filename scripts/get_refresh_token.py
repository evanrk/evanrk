"""
One-time script to get your Spotify refresh token.

Usage:
  1. pip install requests
  2. python scripts/get_refresh_token.py
  3. Paste your Client ID and Client Secret when prompted
  4. Open the URL it prints in your browser
  5. After authorizing, you'll be redirected to 127.0.0.1:3000/callback?code=...
  6. Paste that full URL back into the script
  7. It will print your refresh token - add it as a GitHub secret
"""

import requests
import urllib.parse

client_id = input("Enter your Spotify Client ID: ").strip()
client_secret = input("Enter your Spotify Client Secret: ").strip()

scope = "user-top-read"
redirect_uri = "http://127.0.0.1:3000/callback"

auth_url = (
    "https://accounts.spotify.com/authorize?"
    + urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "scope": scope,
            "redirect_uri": redirect_uri,
        }
    )
)

print(f"\nOpen this URL in your browser:\n\n{auth_url}\n")
print("After authorizing, you'll be redirected to a page that won't load.")
print("That's fine - copy the FULL URL from your browser's address bar.\n")

callback_url = input("Paste the full callback URL here: ").strip()

code = urllib.parse.parse_qs(urllib.parse.urlparse(callback_url).query)["code"][0]

response = requests.post(
    "https://accounts.spotify.com/api/token",
    data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    },
    auth=(client_id, client_secret),
)

data = response.json()
if "refresh_token" in data:
    print(f"\nYour refresh token:\n\n{data['refresh_token']}\n")
    print("Add this as a GitHub repository secret named SPOTIFY_REFRESH_TOKEN")
else:
    print(f"\nError: {data}")
