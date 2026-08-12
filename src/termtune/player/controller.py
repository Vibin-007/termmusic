"""Player controller unifying UI, Queue, Playlist, Provider, and MPV playback engine."""

import asyncio
import logging
from typing import Callable

from termtune.config import settings
from termtune.models.stream import StreamInfo
from termtune.models.track import Track
from termtune.player.mpv import MPVAdapter, PlaybackState
from termtune.playlist.manager import PlaylistManager
from termtune.providers.base import MusicProvider
from termtune.providers.youtube import YouTubeProvider
from termtune.queue.manager import QueueManager
from termtune.utils.errors import PlaybackError, ProviderError, TermTuneError

logger = logging.getLogger(__name__)


class PlayerController:
    """Controller orchestrating media playback, queue, playlist, and stream resolution."""

    def __init__(self, provider: MusicProvider | None = None, load_queue: bool = True):
        self.provider = provider or YouTubeProvider()
        self.queue_manager = QueueManager()
        self.playlist_manager = PlaylistManager()
        self.mpv = MPVAdapter()
        self.current_track: Track | None = None
        self.current_stream: StreamInfo | None = None
        self._stream_cache: dict[str, StreamInfo] = {}

        # Apply settings defaults
        self.mpv.volume = settings.volume
        self.queue_manager.shuffle = settings.shuffle
        self.queue_manager.repeat = settings.repeat

        self.queue_file = settings.config_dir / "queue_state.json"
        if load_queue:
            self.load_queue_state()

        self._on_track_change_callback: Callable[[Track | None], None] | None = None
        self._on_error_callback: Callable[[TermTuneError], None] | None = None

        # Attach auto-next handler when track ends
        self.mpv.set_on_end_file(self._handle_track_finished)

    def load_queue_state(self) -> None:
        """Load queue from disk if available."""
        self.queue_manager.load_state(self.queue_file)
        self.current_track = self.queue_manager.get_current_track()

    def save_queue_state(self) -> None:
        """Save queue to disk."""
        self.queue_manager.save_state(self.queue_file)
        settings.save()

    def set_on_track_change(self, callback: Callable[[Track | None], None]) -> None:
        """Register callback for track change events."""
        self._on_track_change_callback = callback

    def set_on_error(self, callback: Callable[[TermTuneError], None]) -> None:
        """Register callback for playback errors."""
        self._on_error_callback = callback

    def _notify_track_change(self) -> None:
        if self._on_track_change_callback:
            try:
                self._on_track_change_callback(self.current_track)
            except Exception as e:
                logger.error(f"Error in track change callback: {e}")

    def _notify_error(self, err: TermTuneError) -> None:
        if self._on_error_callback:
            try:
                self._on_error_callback(err)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    def _handle_track_finished(self) -> None:
        """Invoked when MPV finishes playing current track."""
        asyncio.create_task(self.next())

    def _prefetch_next_track(self) -> None:
        """Pre-resolve stream URL for the next track in queue for instant zero-latency transition."""
        next_track = self.queue_manager.peek_next()
        if next_track and next_track.id not in self._stream_cache:
            asyncio.create_task(self._resolve_and_cache(next_track))

    async def _resolve_and_cache(self, track: Track) -> None:
        try:
            info = await self.provider.resolve_stream(track)
            self._stream_cache[track.id] = info
            logger.info(f"Pre-fetched stream for '{track.title}'")
        except Exception as e:
            logger.debug(f"Pre-fetch skipped for '{track.title}': {e}")

    async def play_track(self, track: Track, add_to_queue: bool = True, play_next: bool = False) -> tuple[int, bool]:
        """Resolve stream URL and start playback for a track with zero-latency caching."""
        is_dup = False
        if add_to_queue:
            if play_next:
                idx, is_dup = self.queue_manager.add_next(track)
            else:
                idx, is_dup = self.queue_manager.add(track)
            self.queue_manager.set_current_index(idx)

        self.current_track = track
        self._notify_track_change()

        try:
            if track.id in self._stream_cache:
                stream_info = self._stream_cache[track.id]
            else:
                stream_info = await self.provider.resolve_stream(track)

            self.current_stream = stream_info
            await self.mpv.play_url(stream_info.url)

            # Pre-fetch next track in background for immediate playback
            self._prefetch_next_track()
            self.save_queue_state()

        except TermTuneError as e:
            logger.error(f"Failed to play track '{track.title}': {e}")
            self._notify_error(e)
        except Exception as e:
            logger.error(f"Unexpected error playing track '{track.title}': {e}")
            err = PlaybackError(f"Unable to play '{track.title}'.")
            self._notify_error(err)

        return self.queue_manager.current_index, is_dup

    async def play_queue_index(self, index: int) -> None:
        """Play track at specific queue index."""
        track = self.queue_manager.set_current_index(index)
        if track:
            await self.play_track(track, add_to_queue=False)

    async def load_playlist_into_queue(self, playlist_name: str, replace: bool = True) -> int:
        """Load tracks from a playlist into the queue."""
        tracks = self.playlist_manager.load_playlist(playlist_name)
        if not tracks:
            return 0
        if replace:
            self.queue_manager.clear()

        for track in tracks:
            self.queue_manager.add(track)

        self.save_queue_state()
        return len(tracks)

    async def toggle_play_pause(self) -> PlaybackState:
        """Toggle play / pause."""
        return await self.mpv.toggle_play_pause()

    async def pause(self) -> None:
        """Pause playback."""
        await self.mpv.pause()

    async def resume(self) -> None:
        """Resume playback."""
        await self.mpv.resume()

    async def stop(self) -> None:
        """Stop playback."""
        await self.mpv.stop()

    async def next(self) -> None:
        """Advance to next track in queue and play immediately."""
        next_track = self.queue_manager.next()
        if next_track:
            await self.play_track(next_track, add_to_queue=False)
        else:
            await self.stop()
            self.current_track = None
            self._notify_track_change()

    async def previous(self) -> None:
        """Go back to previous track using history stack."""
        prev_track = self.queue_manager.previous()
        if prev_track:
            await self.play_track(prev_track, add_to_queue=False)

    async def seek(self, seconds: float) -> None:
        """Seek forward/backward by relative seconds."""
        await self.mpv.seek(seconds, absolute=False)

    async def set_volume(self, volume: int) -> None:
        """Set volume (0 to 100)."""
        await self.mpv.set_volume(volume)
        settings.volume = self.mpv.volume

    async def increase_volume(self, amount: int = 5) -> int:
        """Increase volume."""
        new_vol = min(100, self.mpv.volume + amount)
        await self.set_volume(new_vol)
        return self.mpv.volume

    async def decrease_volume(self, amount: int = 5) -> int:
        """Decrease volume."""
        new_vol = max(0, self.mpv.volume - amount)
        await self.set_volume(new_vol)
        return self.mpv.volume

    async def toggle_mute(self) -> bool:
        """Toggle mute state."""
        return await self.mpv.toggle_mute()

    def toggle_shuffle(self) -> bool:
        """Toggle queue shuffle mode."""
        res = self.queue_manager.toggle_shuffle()
        settings.shuffle = res
        return res

    def toggle_repeat(self) -> str:
        """Toggle queue repeat mode."""
        res = self.queue_manager.toggle_repeat()
        settings.repeat = res
        return res

    async def shutdown(self) -> None:
        """Stop playback and persist queue state to disk."""
        self.save_queue_state()
        await self.mpv.close()
