"""Playlist manager handling creating, editing, loading, and deleting playlists on disk."""

import json
import logging
from pathlib import Path

from termtune.config import settings
from termtune.models.track import Track

logger = logging.getLogger(__name__)


class PlaylistManager:
    """Manages persistent playlists stored as JSON files under ~/.termtune/playlists/."""

    def __init__(self, storage_dir: Path | None = None):
        self.storage_dir = storage_dir or (settings.config_dir / "playlists")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_playlist_path(self, name: str) -> Path:
        """Sanitize playlist name and return Path object."""
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip().lower()
        if not safe_name:
            safe_name = "unnamed"
        return self.storage_dir / f"{safe_name}.json"

    def list_playlists(self) -> list[str]:
        """Return sorted list of saved playlist names."""
        if not self.storage_dir.exists():
            return []
        playlists = []
        for file in self.storage_dir.glob("*.json"):
            playlists.append(file.stem)
        return sorted(playlists)

    def create_playlist(self, name: str) -> bool:
        """Create a new empty playlist file if it doesn't already exist."""
        path = self._get_playlist_path(name)
        if path.exists():
            return False
        self.save_playlist(name, [])
        return True

    def delete_playlist(self, name: str) -> bool:
        """Delete a playlist file."""
        path = self._get_playlist_path(name)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.error(f"Failed to delete playlist '{name}': {e}")
        return False

    def load_playlist(self, name: str) -> list[Track]:
        """Load list of Tracks from playlist file."""
        path = self._get_playlist_path(name)
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tracks_data = data.get("tracks", [])
            return [Track.from_dict(t) for t in tracks_data if isinstance(t, dict)]
        except Exception as e:
            logger.error(f"Failed to load playlist '{name}': {e}")
            return []

    def save_playlist(self, name: str, tracks: list[Track]) -> bool:
        """Save list of Tracks to playlist file."""
        path = self._get_playlist_path(name)
        try:
            data = {
                "name": name,
                "count": len(tracks),
                "tracks": [t.to_dict() for t in tracks],
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save playlist '{name}': {e}")
            return False

    def add_track(self, name: str, track: Track) -> tuple[bool, str]:
        """Add track to playlist. Returns (success, message)."""
        tracks = self.load_playlist(name)
        # Check for duplicate in playlist
        if any(t.id == track.id for t in tracks):
            return False, f"Track is already in playlist '{name}'"

        tracks.append(track)
        if self.save_playlist(name, tracks):
            return True, f"Added '{track.title}' to playlist '{name}'"
        return False, "Failed to save playlist"

    def remove_track(self, name: str, track_id: str) -> bool:
        """Remove track from playlist by ID."""
        tracks = self.load_playlist(name)
        filtered = [t for t in tracks if t.id != track_id]
        if len(filtered) < len(tracks):
            return self.save_playlist(name, filtered)
        return False
