"""YouTube provider implementation using yt-dlp with optimized high-speed stream resolution."""

import asyncio
import logging
import yt_dlp

from termtune.models.stream import StreamInfo
from termtune.models.track import Track
from termtune.providers.base import MusicProvider
from termtune.utils.errors import NetworkError, ProviderError

logger = logging.getLogger(__name__)


class YouTubeProvider(MusicProvider):
    """YouTube music provider using yt-dlp."""

    def _sync_search(self, query: str) -> list[Track]:
        """Perform synchronous yt-dlp search."""
        search_query = f"ytsearch20:{query}"
        ydl_opts = {
            "extract_flat": "in_playlist",
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "nocheckcertificate": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
        except Exception as e:
            logger.error(f"yt-dlp search failed for '{query}': {e}")
            if "network" in str(e).lower() or "connection" in str(e).lower():
                raise NetworkError("Unable to connect to YouTube search service.")
            raise ProviderError("Search failed. Please try again.")

        if not info or "entries" not in info:
            return []

        tracks: list[Track] = []
        for entry in info.get("entries") or []:
            if not entry or not isinstance(entry, dict):
                continue

            track_id = entry.get("id", "")
            title = entry.get("title", "Unknown Title")
            artist = (
                entry.get("uploader")
                or entry.get("channel")
                or entry.get("artist")
                or "Unknown Artist"
            )
            duration = entry.get("duration")
            if duration is not None:
                try:
                    duration = int(duration)
                except (ValueError, TypeError):
                    duration = None

            webpage_url = (
                entry.get("webpage_url")
                or entry.get("url")
                or f"https://www.youtube.com/watch?v={track_id}"
            )

            thumbnails = entry.get("thumbnails")
            thumb_url = None
            if thumbnails and isinstance(thumbnails, list):
                thumb_url = thumbnails[-1].get("url")
            elif entry.get("thumbnail"):
                thumb_url = entry.get("thumbnail")

            tracks.append(
                Track(
                    id=track_id,
                    title=title,
                    artist=artist,
                    duration=duration,
                    webpage_url=webpage_url,
                    thumbnail_url=thumb_url,
                    source="YouTube",
                )
            )

        return tracks

    async def search(self, query: str) -> list[Track]:
        """Search music tracks by query asynchronously."""
        query_str = query.strip()
        if not query_str:
            return []

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_search, query_str)

    def _sync_resolve_stream(self, track: Track) -> StreamInfo:
        """Perform synchronous fast stream resolution."""
        url_to_resolve = track.webpage_url or f"https://www.youtube.com/watch?v={track.id}"

        ydl_opts = {
            "format": "ba/b",
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "socket_timeout": 2,
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "mweb"],
                    "skip": ["dash", "hls"],
                }
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url_to_resolve, download=False)
                if info and info.get("url"):
                    return StreamInfo(
                        url=info["url"],
                        mime_type=info.get("ext") or info.get("acodec"),
                        duration=info.get("duration") or track.duration,
                    )
        except Exception as e:
            logger.warning(f"yt-dlp fast stream extraction warning for '{track.title}': {e}")

        # Instant fallback to webpage URL (MPV plays webpage URL natively via its yt-dlp hook)
        return StreamInfo(
            url=url_to_resolve,
            mime_type="audio/mp4",
            duration=track.duration,
        )

    async def resolve_stream(self, track: Track) -> StreamInfo:
        """Resolve audio stream URL asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_resolve_stream, track)
