from syrics.api import Spotify
import os
import requests
from dotenv import load_dotenv
from authorise import SpotifyAuth

load_dotenv()

SP_DC     = os.environ["SP_DC"]
_CLIENT_ID = os.environ["CLIENT_ID"]

# ── OAuth auth (for search) ──────────────────────────────────────────────────
# Loads client_secret from env or prompts. Run `ensure_logged_in()` once at startup.

_auth: SpotifyAuth | None = None

def ensure_logged_in():
    """Call once at startup. Opens browser login if no saved token exists."""
    global _auth
    client_id     = _CLIENT_ID
    client_secret = _load_client_secret()
    _auth = SpotifyAuth(client_id, client_secret, "http://127.0.0.1:8080/callback")
    token = _auth.login_interactive()
    if not token:
        raise RuntimeError("Spotify login failed — cannot search without an OAuth token.")
    return token

def _load_client_secret() -> str:
    """Load client secret from .env / environment, or prompt the user."""
    secret = os.environ.get("CLIENT_SECRET", "").strip()
    if secret:
        return secret
    return input("Enter your Spotify Client Secret: ").strip()

def get_oauth_token() -> str:
    """Return a valid OAuth access token, refreshing if needed."""
    if _auth is None:
        raise RuntimeError("Call ensure_logged_in() before fetching.")
    token = _auth.get_valid_token()
    if not token:
        raise RuntimeError("OAuth token expired and could not be refreshed. Re-run to log in again.")
    return token

# keep private alias for internal use
_get_oauth_token = get_oauth_token

# ── sp_dc instance (for lyrics only) ────────────────────────────────────────

_sp_instance: Spotify | None = None

# Cache lyrics keyed by track_id so we never fetch the same song twice
_lyrics_cache: dict = {}

# Cache search results keyed by "title||artist" so search() is only called once per song
_search_cache: dict = {}

def _get_sp() -> Spotify:
    global _sp_instance
    if _sp_instance is None:
        _sp_instance = Spotify(SP_DC)
    return _sp_instance

def _parse_lyrics(track_id: str):
    sp = _get_sp()
    lyrics = sp.get_lyrics(track_id)
    if not lyrics or 'lyrics' not in lyrics:
        return None
    lines = lyrics['lyrics']['lines']
    TimeValues = []
    for i in lines:
        startTime = float(i['startTimeMs']) / 1000.0
        TimeValues.append({'startTime': startTime, 'words': i['words']})
    return sorted(TimeValues, key=lambda x: x['startTime'])

def getLyricsData(trackUrl):
    """Fetch lyrics by full Spotify track URL."""
    return getLyricsById(trackUrl[31:])

def getLyricsById(track_id: str):
    """Fetch lyrics by Spotify track ID (cached)."""
    if track_id not in _lyrics_cache:
        _lyrics_cache[track_id] = _parse_lyrics(track_id)
    return _lyrics_cache[track_id]

def searchTrack(title: str, artist: str) -> str | None:
    """Search Spotify for a track using the OAuth token. Returns track ID or None."""
    key = f"{title}||{artist}"
    if key in _search_cache:
        return _search_cache[key]
    token = _get_oauth_token()
    resp = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": f"{title} {artist}", "type": "track", "limit": 1}
    )
    try:
        item = resp.json()['tracks']['items'][0]
        _search_cache[key] = item['id']
        return _search_cache[key]
    except (KeyError, IndexError, TypeError):
        pass
    _search_cache[key] = None
    return None
