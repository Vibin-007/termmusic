"""Data models for audio tracks and metadata."""

from dataclasses import dataclass
from termtune.utils.formatting import format_duration, sanitize_terminal_text


@dataclass
class Track:
    """Represents a music track item with metadata."""

    id: str
    title: str
    artist: str
    duration: float  # In seconds
    webpage_url: str
    thumbnail_url: str | None = None
    album: str | None = None
    source: str = "YouTube"

    def __post_init__(self):
        """Sanitize title and artist string for terminal rendering."""
        self.title = sanitize_terminal_text(self.title or "Unknown Title")
        self.artist = sanitize_terminal_text(self.artist or "Unknown Artist")

    @property
    def formatted_duration(self) -> str:
        """Return formatted duration string (MM:SS)."""
        return format_duration(self.duration)

    def to_dict(self) -> dict:
        """Convert track model to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "webpage_url": self.webpage_url,
            "thumbnail_url": self.thumbnail_url,
            "album": self.album,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Track":
        """Reconstruct Track instance from dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", "Unknown Title"),
            artist=data.get("artist", "Unknown Artist"),
            duration=float(data.get("duration", 0)),
            webpage_url=data.get("webpage_url", ""),
            thumbnail_url=data.get("thumbnail_url"),
            album=data.get("album"),
            source=data.get("source", "YouTube"),
        )
