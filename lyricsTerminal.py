"""
lyricsTerminal.py
Displays synced Spotify lyrics in the terminal.

Two source modes:
  local  — Windows media session (WinSDK), event-driven, no extra API calls
  web    — Spotify Web API /me/player, poll-driven, works on any OS
"""

import asyncio
import bisect
import sys
import time
import requests

from spotifyFetch import searchTrack, getLyricsById, ensure_logged_in, get_oauth_token
from sender import SerialSender

# ── terminal helpers ─────────────────────────────────────────────────────────

CLEAR  = "\033[2J\033[H"   # clear screen + move cursor to top
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
UP     = "\033[A"

CONTEXT_BEFORE = 3   # dimmed lines shown before current
CONTEXT_AFTER  = 4   # dimmed lines shown after current

def clear_screen():
    print(CLEAR, end="", flush=True)

def render(lyrics, current_idx, track_info, position):
    """Redraw the lyrics block in the terminal."""
    clear_screen()
    title  = track_info.get("title", "")
    artist = track_info.get("artist", "")
    mins, secs = divmod(int(position), 60)

    print(f"{BOLD}{CYAN}  ♫  {artist} — {title}{RESET}")
    print(f"     {mins:02d}:{secs:02d}\n")

    start = max(0, current_idx - CONTEXT_BEFORE)
    end   = min(len(lyrics), current_idx + CONTEXT_AFTER + 1)

    for i in range(start, end):
        line = lyrics[i]['words']
        if i == current_idx:
            print(f"  {BOLD}▶  {line}{RESET}")
        elif i < current_idx:
            print(f"  {DIM}   {line}{RESET}")
        else:
            print(f"     {line}")

    sys.stdout.flush()


# ── position tracking ────────────────────────────────────────────────────────

class PositionTracker:
    """Keeps an accurate running estimate of playback position."""

    def __init__(self, initial_pos: float):
        self.base_pos   = initial_pos
        self.wall_start = time.monotonic()
        self.paused     = False
        self.paused_at  = 0.0

    def update(self, new_pos: float):
        """Called when the OS reports a new position (e.g. seek)."""
        self.base_pos   = new_pos
        self.wall_start = time.monotonic()
        if self.paused:
            self.paused_at = new_pos

    def pause(self):
        if not self.paused:
            self.paused_at = self.current()
            self.paused = True

    def resume(self):
        if self.paused:
            self.base_pos   = self.paused_at
            self.wall_start = time.monotonic()
            self.paused = False

    def current(self) -> float:
        if self.paused:
            return self.paused_at
        return self.base_pos + (time.monotonic() - self.wall_start)


# ── lyrics index helper ──────────────────────────────────────────────────────

def current_lyric_index(timestamps: list, position: float) -> int:
    """Binary search — O(log n) — for the lyric line active at `position` seconds."""
    idx = bisect.bisect_right(timestamps, position) - 1
    return max(0, idx)


# ── main ─────────────────────────────────────────────────────────────────────

class LyricsPlayer:
    def __init__(self, serial_sender: SerialSender | None = None):
        self.lyrics:      list  = []
        self.timestamps:  list  = []   # pre-built float list for bisect
        self.track_info:  dict  = {}
        self.tracker:     PositionTracker | None = None
        self.running:     bool  = False
        self._display_task = None
        self._last_track_key: str = ""
        self._load_debounce_task = None
        self._serial: SerialSender | None = serial_sender
        self._last_sent_idx: int = -1

    # called when the OS session reports a new track
    async def load_track(self, session):
        info     = await session.try_get_media_properties_async()
        timeline = session.get_timeline_properties()
        title    = info.title
        artist   = info.artist
        position = timeline.position.total_seconds()
        await self.load_track_data(title, artist, position)

    async def load_track_data(self, title: str, artist: str, position: float, track_id: str = None):
        """Core loader — called by both local and web modes."""
        track_key = f"{artist}||{title}"
        if track_key == self._last_track_key:
            return
        self._last_track_key = track_key

        if self._display_task:
            self._display_task.cancel()
            self._display_task = None
        self.lyrics  = []
        self.tracker = None

        clear_screen()
        print(f"\n{CYAN}Searching for lyrics: {artist} - {title}...{RESET}")

        if not track_id:
            track_id = searchTrack(title, artist)
        if not track_id:
            clear_screen()
            print(f"{BOLD}{CYAN}  ♫  {artist} - {title}{RESET}")
            print(f"\n  No track found on Spotify.")
            return

        lyrics = getLyricsById(track_id)
        if not lyrics:
            clear_screen()
            print(f"{BOLD}{CYAN}  ♫  {artist} - {title}{RESET}")
            print(f"\n  No synced lyrics available for this track.")
            return

        self.lyrics      = lyrics
        self.timestamps  = [line['startTime'] for line in lyrics]
        self.track_info  = {"title": title, "artist": artist}
        self.tracker     = PositionTracker(position)
        self._last_sent_idx = -1
        if self._serial:
            self._serial.send_line(f"{artist} - {title}")
        self._display_task = asyncio.ensure_future(self._display_loop())

    async def _display_loop(self):
        """Refresh the terminal ~10 times per second and send to serial on line change."""
        while True:
            if self.tracker and self.lyrics:
                pos = self.tracker.current()
                idx = current_lyric_index(self.timestamps, pos)
                render(self.lyrics, idx, self.track_info, pos)
                # Send to Arduino only when the active line changes
                if self._serial and idx != self._last_sent_idx:
                    self._last_sent_idx = idx
                    self._serial.send_line(self.lyrics[idx]['words'])
            await asyncio.sleep(0.1)

    def on_timeline_changed(self, sender, _args):
        """Sync position when the OS reports a seek or periodic update."""
        if self.tracker:
            timeline = sender.get_timeline_properties()
            self.tracker.update(timeline.position.total_seconds())

    def on_playback_changed(self, sender, _args):
        """Handle play / pause."""
        if not self.tracker:
            return
        pb = sender.get_playback_info()
        # PlaybackStatus: 4 = Playing, 5 = Paused
        status = int(pb.playback_status)
        if status == 5:
            self.tracker.pause()
        elif status == 4:
            self.tracker.resume()


async def main_local(serial_sender=None):
    """Event-driven mode using the Windows media session (WinSDK)."""
    from winsdk.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    )

    player   = LyricsPlayer(serial_sender)
    sessions = await MediaManager.request_async()
    current  = sessions.get_current_session()

    if not current:
        print("No media session found. Start playing something on Spotify.")
        return

    loop = asyncio.get_running_loop()

    def schedule(coro):
        asyncio.run_coroutine_threadsafe(coro, loop)

    await player.load_track(current)

    def on_media_properties_changed(sender, _args):
        schedule(player.load_track(sender))

    def attach_session(session):
        session.add_media_properties_changed(on_media_properties_changed)
        session.add_timeline_properties_changed(player.on_timeline_changed)
        session.add_playback_info_changed(player.on_playback_changed)

    attach_session(current)

    def on_session_changed(manager, _args):
        new_session = manager.get_current_session()
        if new_session:
            attach_session(new_session)
            schedule(player.load_track(new_session))

    sessions.add_current_session_changed(on_session_changed)

    await asyncio.Event().wait()


async def main_web(poll_interval: float = 1.0, serial_sender=None):
    """Poll-driven mode using the Spotify Web API /me/player endpoint."""
    player = LyricsPlayer(serial_sender)
    last_track_id = None

    print(f"{CYAN}Web mode: polling Spotify every {poll_interval}s...{RESET}")

    while True:
        try:
            token = get_oauth_token()
            resp  = requests.get(
                "https://api.spotify.com/v1/me/player",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )

            if resp.status_code == 204:
                # Nothing playing
                if last_track_id is not None:
                    last_track_id = None
                    player._last_track_key = ""
                    if player._display_task:
                        player._display_task.cancel()
                        player._display_task = None
                    clear_screen()
                    print(f"{DIM}  Nothing playing...{RESET}")
                await asyncio.sleep(poll_interval)
                continue

            if resp.status_code != 200:
                await asyncio.sleep(poll_interval)
                continue

            data      = resp.json()
            item      = data.get("item")
            is_playing = data.get("is_playing", False)

            if not item:
                await asyncio.sleep(poll_interval)
                continue

            track_id = item["id"]
            title    = item["name"]
            artist   = item["artists"][0]["name"]
            position = data.get("progress_ms", 0) / 1000.0

            # Sync position tracker on every poll (catches seeks too)
            if player.tracker:
                player.tracker.update(position)
                if is_playing:
                    player.tracker.resume()
                else:
                    player.tracker.pause()

            # Load new track if it changed
            if track_id != last_track_id:
                last_track_id = track_id
                await player.load_track_data(title, artist, position, track_id=track_id)

        except Exception as e:
            clear_screen()
            print(f"{DIM}  Error polling Spotify: {e}{RESET}")

        await asyncio.sleep(poll_interval)



async def main_serial(poll_interval: float = 1.0):
    """Web poll mode — alias kept for backward compat."""
    await main_web(poll_interval)
