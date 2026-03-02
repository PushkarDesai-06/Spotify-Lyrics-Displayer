import asyncio
from time import sleep
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
)


async def get_track_info(session):
    info = await session.try_get_media_properties_async()
    timeline = session.get_timeline_properties()
    return {
        "title": info.title,
        "artist": info.artist,
        "album": info.album_title,
        "position": timeline.position.total_seconds(),
        "duration": timeline.end_time.total_seconds(),
    }


async def main():
    sessions = await MediaManager.request_async()
    current = sessions.get_current_session()

    if not current:
        print("No media session found")
        return

    # Print initial state
    track = await get_track_info(current)
    print(f"Now playing: {track['artist']} - {track['title']}  [{track['position']:.1f}s / {track['duration']:.1f}s]")

    # Event: track/metadata changed
    async def on_media_properties_changed(sender, args):
        track = await get_track_info(sender)
        print(f"Track changed: {track['artist']} - {track['title']}")

    # Event: playback state changed (play/pause/stop)
    def on_playback_info_changed(sender, args):
        pb = sender.get_playback_info()
        print(f"Playback status: {pb.playback_status}")

    # Event: timeline position changed
    def on_timeline_properties_changed(sender, args):
        timeline = sender.get_timeline_properties()
        print(f"Position: {timeline.position.total_seconds():.1f}s")

    # Subscribe to events
    current.add_media_properties_changed(
        lambda s, a: asyncio.ensure_future(on_media_properties_changed(s, a))
    )
    current.add_playback_info_changed(on_playback_info_changed)
    current.add_timeline_properties_changed(on_timeline_properties_changed)

    # Watch for session switches (e.g. different app takes focus)
    def on_current_session_changed(manager, args):
        print("Active session changed")

    sessions.add_current_session_changed(on_current_session_changed)

    # Keep the event loop alive
    print("Listening for events... (Ctrl+C to stop)")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")
        print(f"Now playing: {result['artist']} - {result['title']}")
        print(f"Position : {result['position']}")
        sleep(0.5)
