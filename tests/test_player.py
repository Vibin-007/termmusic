"""Unit tests for PlayerController and volume / queue controls."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from termtune.models.stream import StreamInfo
from termtune.models.track import Track
from termtune.player.controller import PlayerController
from termtune.player.mpv import MPVAdapter


def get_mock_provider():
    provider = MagicMock()
    provider.search = AsyncMock(return_value=[])
    provider.resolve_stream = AsyncMock(
        return_value=StreamInfo(url="http://stream.test/audio.mp3", duration=180)
    )
    return provider


def test_player_controller_volume_controls():
    async def _test():
        provider = get_mock_provider()
        controller = PlayerController(provider=provider, load_queue=False)

        mpv_mock = MagicMock(spec=MPVAdapter)
        mpv_mock.volume = 80
        mpv_mock.muted = False

        async def fake_set_volume(vol):
            mpv_mock.volume = max(0, min(100, vol))

        mpv_mock.set_volume = AsyncMock(side_effect=fake_set_volume)
        controller.mpv = mpv_mock

        vol = await controller.increase_volume(10)
        assert vol == 90

        vol = await controller.decrease_volume(20)
        assert vol == 70

    asyncio.run(_test())


def test_player_controller_play_track():
    async def _test():
        provider = get_mock_provider()
        controller = PlayerController(provider=provider, load_queue=False)

        mpv_mock = MagicMock(spec=MPVAdapter)
        mpv_mock.volume = 80
        mpv_mock.play_url = AsyncMock()
        controller.mpv = mpv_mock

        track = Track(
            id="t1",
            title="Test Song",
            artist="Test Artist",
            duration=180,
            webpage_url="http://test.com",
        )

        await controller.play_track(track, add_to_queue=True)

        assert controller.current_track.title == "Test Song"
        assert controller.queue_manager.count() == 1
        provider.resolve_stream.assert_called_once_with(track)
        mpv_mock.play_url.assert_called_once_with("http://stream.test/audio.mp3")

    asyncio.run(_test())


def test_player_controller_queue_navigation():
    async def _test():
        provider = get_mock_provider()
        controller = PlayerController(provider=provider, load_queue=False)

        mpv_mock = MagicMock(spec=MPVAdapter)
        mpv_mock.play_url = AsyncMock()
        controller.mpv = mpv_mock

        t1 = Track(id="1", title="A", artist="X", duration=100, webpage_url="http://1.com")
        t2 = Track(id="2", title="B", artist="Y", duration=100, webpage_url="http://2.com")

        controller.queue_manager.add(t1)
        controller.queue_manager.add(t2)

        await controller.play_queue_index(0)
        assert controller.current_track.title == "A"

        await controller.next()
        assert controller.current_track.title == "B"

    asyncio.run(_test())
