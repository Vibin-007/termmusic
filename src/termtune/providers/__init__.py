"""Providers package for TermTune."""

from termtune.providers.base import MusicProvider
from termtune.providers.youtube import YouTubeProvider

__all__ = ["MusicProvider", "YouTubeProvider"]
