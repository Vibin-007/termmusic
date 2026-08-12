"""Unit tests for YouTubeProvider with mocked responses."""

import asyncio
from unittest.mock import MagicMock, patch

from termtune.models.track import Track
from termtune.providers.youtube import YouTubeProvider


def test_youtube_provider_empty_query():
    async def _test():
        provider = YouTubeProvider()
        results = await provider.search("   ")
        assert results == []

    asyncio.run(_test())


def test_youtube_provider_search_mock():
    async def _test():
        mock_info = {
            "entries": [
                {
                    "id": "vid123",
                    "title": "Starboy",
                    "uploader": "The Weeknd",
                    "duration": 230,
                    "webpage_url": "https://www.youtube.com/watch?v=vid123",
                    "thumbnail": "https://img.youtube.com/vi/vid123/0.jpg",
                }
            ]
        }

        provider = YouTubeProvider()
        with patch("yt_dlp.YoutubeDL") as MockYTDL:
            instance = MockYTDL.return_value
            instance.__enter__.return_value = instance
            instance.extract_info.return_value = mock_info

            results = await provider.search("Starboy")

            assert len(results) == 1
            assert results[0].title == "Starboy"
            assert results[0].artist == "The Weeknd"
            assert results[0].duration == 230
            assert results[0].id == "vid123"

    asyncio.run(_test())


def test_youtube_provider_resolve_stream_mock():
    async def _test():
        mock_stream_info = {
            "url": "https://googlevideo.com/videoplayback?id=123",
            "ext": "m4a",
            "duration": 230,
        }

        track = Track(
            id="vid123",
            title="Starboy",
            artist="The Weeknd",
            duration=230,
            webpage_url="https://www.youtube.com/watch?v=vid123",
        )

        provider = YouTubeProvider()
        with patch("yt_dlp.YoutubeDL") as MockYTDL:
            instance = MockYTDL.return_value
            instance.__enter__.return_value = instance
            instance.extract_info.return_value = mock_stream_info

            stream = await provider.resolve_stream(track)

            assert stream.url == "https://googlevideo.com/videoplayback?id=123"
            assert stream.mime_type == "m4a"
            assert stream.duration == 230

    asyncio.run(_test())
