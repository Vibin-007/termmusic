"""Base interface for music providers."""

from abc import ABC, abstractmethod

from termtune.models.stream import StreamInfo
from termtune.models.track import Track


class MusicProvider(ABC):
    """Abstract base class for online music providers."""

    @abstractmethod
    async def search(self, query: str) -> list[Track]:
        """Search music tracks by query asynchronously.

        Args:
            query: The search term entered by the user.

        Returns:
            List of matching Track objects.
        """
        pass

    @abstractmethod
    async def resolve_stream(self, track: Track) -> StreamInfo:
        """Resolve a direct audio stream URL for a given track.

        Args:
            track: Track to resolve.

        Returns:
            StreamInfo object containing stream URL and metadata.
        """
        pass
