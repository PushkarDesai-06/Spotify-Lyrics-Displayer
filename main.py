import asyncio
import sys

from lyricsTerminal import main_local, main_web, BOLD, RESET
from spotifyFetch import ensure_logged_in
from sender import SerialSender

if __name__ == "__main__":
    print(f"\n{BOLD}Spotify Lyrics Terminal{RESET}")
    print("\u2500" * 30)

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("  [1] Local      — Windows media session (event-driven, recommended)")
        print("  [2] Web        — Spotify API polling (works on any device)")
        print("  [3] Local + Serial  — Local mode + send to Arduino")
        print("  [4] Web   + Serial  — Web mode   + send to Arduino")
        choice = input("\nChoose mode [1/2/3/4]: ").strip()
        mode = {"1": "local", "2": "web", "3": "local-serial", "4": "web-serial"}.get(choice, "local")

    # Set up serial if needed
    sender = None
    if "serial" in mode:
        port = input("Serial port [COM11]: ").strip() or "COM11"
        sender = SerialSender(port=port)

    try:
        print(f"\nLogging in to Spotify...")
        ensure_logged_in()
        print(f"Starting in {BOLD}{mode}{RESET} mode...\n")
        if "web" in mode:
            asyncio.run(main_web(serial_sender=sender))
        else:
            asyncio.run(main_local(serial_sender=sender))
    except KeyboardInterrupt:
        if sender:
            sender.clear()
            sender.close()
        print(f"\n{RESET}Stopped.")
