"""Unit tests for Track and StreamInfo models."""

from termtune.models.stream import StreamInfo
from termtune.models.track import Track
from termtune.utils.formatting import format_progress_bar, format_time, format_volume_bar


def test_track_model_creation():
    track = Track(
        id="123",
        title="Blinding Lights",
        artist="The Weeknd",
        duration=200,
        webpage_url="https://www.youtube.com/watch?v=123",
        thumbnail_url="https://example.com/thumb.jpg",
        source="YouTube",
    )
    assert track.id == "123"
    assert track.title == "Blinding Lights"
    assert track.artist == "The Weeknd"
    assert track.duration == 200
    assert track.formatted_duration == "03:20"


def test_stream_info_creation():
    stream = StreamInfo(url="https://stream.example.com/audio.webm", mime_type="audio/webm", duration=180)
    assert stream.url == "https://stream.example.com/audio.webm"
    assert stream.mime_type == "audio/webm"
    assert stream.duration == 180


def test_time_formatting():
    assert format_time(0) == "00:00"
    assert format_time(65) == "01:05"
    assert format_time(3661) == "01:01:01"
    assert format_time(None) == "00:00"
    assert format_time(-10) == "00:00"


def test_progress_bar_formatting():
    bar = format_progress_bar(50, 100, width=10)
    assert "00:50" in bar
    assert "01:40" in bar
    assert "●" in bar


def test_volume_bar_formatting():
    bar = format_volume_bar(50, width=10)
    assert "█" in bar
    assert len(bar) == 10
