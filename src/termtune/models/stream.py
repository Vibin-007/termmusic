"""Stream metadata model."""

from dataclasses import dataclass


@dataclass
class StreamInfo:
    """Resolved audio stream information for playback."""

    url: str
    mime_type: str | None = None
    duration: int | None = None
