"""In-memory queue manager with strict duplicate prevention and persistence."""

import json
import logging
import os
import random
from pathlib import Path
from typing import Literal

from termtune.models.track import Track
from termtune.utils.formatting import format_duration

logger = logging.getLogger(__name__)

RepeatMode = Literal["off", "all", "track"]


class QueueManager:
    """Manages the current playback queue in memory with strict duplicate prevention."""

    def __init__(self):
        self._queue: list[Track] = []
        self._current_index: int = -1
        self._shuffle: bool = False
        self._repeat: RepeatMode = "off"
        self._history: list[int] = []

    @property
    def items(self) -> list[Track]:
        """Return shallow copy of queue items."""
        return list(self._queue)

    @property
    def current_index(self) -> int:
        """Return index of currently playing track, or -1 if none."""
        return self._current_index

    @property
    def shuffle(self) -> bool:
        """Return whether shuffle is enabled."""
        return self._shuffle

    @shuffle.setter
    def shuffle(self, value: bool) -> None:
        self._shuffle = bool(value)

    @property
    def repeat(self) -> RepeatMode:
        """Return current repeat mode ('off', 'all', 'track')."""
        return self._repeat

    @repeat.setter
    def repeat(self, value: RepeatMode) -> None:
        if value in ("off", "all", "track"):
            self._repeat = value

    @property
    def total_duration(self) -> int:
        """Return total duration of all tracks in queue (in seconds)."""
        return sum(t.duration for t in self._queue if t.duration is not None)

    @property
    def formatted_total_duration(self) -> str:
        """Return formatted total queue duration string."""
        return format_duration(self.total_duration)

    def count(self) -> int:
        """Return number of tracks in queue."""
        return len(self._queue)

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._queue) == 0

    def find_track_index(self, track_id: str) -> int:
        """Return index of track in queue if duplicate, or -1 if not found."""
        for idx, t in enumerate(self._queue):
            if t.id == track_id:
                return idx
        return -1

    def add(self, track: Track) -> tuple[int, bool]:
        """Add track to end of queue. If duplicate, blocks addition and returns (existing_index, True)."""
        existing_idx = self.find_track_index(track.id)
        if existing_idx >= 0:
            return existing_idx, True

        self._queue.append(track)
        new_idx = len(self._queue) - 1
        return new_idx, False

    def add_next(self, track: Track) -> tuple[int, bool]:
        """Add track after current track. If duplicate, blocks addition and returns (existing_index, True)."""
        existing_idx = self.find_track_index(track.id)
        if existing_idx >= 0:
            return existing_idx, True

        insert_idx = self._current_index + 1 if self._current_index >= 0 else len(self._queue)
        self._queue.insert(insert_idx, track)
        return insert_idx, False

    def remove(self, index: int) -> Track | None:
        """Remove track at given index with accurate index recalculation."""
        if 0 <= index < len(self._queue):
            removed = self._queue.pop(index)

            # Update history stack
            self._history = [i - 1 if i > index else i for i in self._history if i != index]

            if index < self._current_index:
                self._current_index -= 1
            elif index == self._current_index:
                if self._current_index >= len(self._queue):
                    self._current_index = len(self._queue) - 1

            return removed
        return None

    def clear(self) -> None:
        """Clear all songs from queue."""
        self._queue.clear()
        self._current_index = -1
        self._history.clear()

    def get_current_track(self) -> Track | None:
        """Return currently selected track or None."""
        if 0 <= self._current_index < len(self._queue):
            return self._queue[self._current_index]
        return None

    def set_current_index(self, index: int) -> Track | None:
        """Explicitly set current playing track index."""
        if 0 <= index < len(self._queue):
            if self._current_index >= 0 and self._current_index != index:
                self._history.append(self._current_index)
            self._current_index = index
            return self._queue[self._current_index]
        return None

    def peek_next(self) -> Track | None:
        """Return the next track in queue without advancing current index."""
        if not self._queue:
            return None
        next_idx = self._current_index + 1
        if 0 <= next_idx < len(self._queue):
            return self._queue[next_idx]
        elif self._repeat == "all" and self._queue:
            return self._queue[0]
        return None

    def next(self) -> Track | None:
        """Advance to next track according to repeat and shuffle settings."""
        if not self._queue:
            return None

        if self._repeat == "track" and self._current_index >= 0:
            return self._queue[self._current_index]

        if self._shuffle and len(self._queue) > 1:
            indices = [i for i in range(len(self._queue)) if i != self._current_index]
            next_idx = random.choice(indices)
        else:
            next_idx = self._current_index + 1
            if next_idx >= len(self._queue):
                if self._repeat == "all":
                    next_idx = 0
                else:
                    return None

        if self._current_index >= 0:
            self._history.append(self._current_index)
        self._current_index = next_idx
        return self._queue[self._current_index]

    def previous(self) -> Track | None:
        """Go back to previous track using history stack."""
        if not self._queue:
            return None

        if self._history:
            prev_idx = self._history.pop()
            if 0 <= prev_idx < len(self._queue):
                self._current_index = prev_idx
                return self._queue[self._current_index]

        prev_idx = self._current_index - 1
        if prev_idx < 0:
            if self._repeat == "all":
                prev_idx = len(self._queue) - 1
            else:
                prev_idx = 0

        if 0 <= prev_idx < len(self._queue):
            self._current_index = prev_idx
            return self._queue[self._current_index]
        return None

    def move_up(self, index: int) -> bool:
        """Move track at index one position up (earlier in queue)."""
        if 1 <= index < len(self._queue):
            self._queue[index - 1], self._queue[index] = (
                self._queue[index],
                self._queue[index - 1],
            )
            if self._current_index == index:
                self._current_index -= 1
            elif self._current_index == index - 1:
                self._current_index += 1
            return True
        return False

    def move_down(self, index: int) -> bool:
        """Move track at index one position down (later in queue)."""
        if 0 <= index < len(self._queue) - 1:
            self._queue[index + 1], self._queue[index] = (
                self._queue[index],
                self._queue[index + 1],
            )
            if self._current_index == index:
                self._current_index += 1
            elif self._current_index == index + 1:
                self._current_index -= 1
            return True
        return False

    def toggle_shuffle(self) -> bool:
        """Toggle shuffle mode on/off."""
        self._shuffle = not self._shuffle
        return self._shuffle

    def toggle_repeat(self) -> RepeatMode:
        """Cycle repeat mode: off -> all -> track -> off."""
        modes: list[RepeatMode] = ["off", "all", "track"]
        cur_idx = modes.index(self._repeat) if self._repeat in modes else 0
        self._repeat = modes[(cur_idx + 1) % len(modes)]
        return self._repeat

    # Persistence Methods
    def save_state(self, filepath: str | Path) -> None:
        """Save queue items and state to JSON file."""
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "current_index": self._current_index,
                "shuffle": self._shuffle,
                "repeat": self._repeat,
                "tracks": [t.to_dict() for t in self._queue],
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Queue state saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save queue state: {e}")

    def load_state(self, filepath: str | Path) -> None:
        """Load queue items and state from JSON file with automatic deduplication."""
        try:
            path = Path(filepath)
            if not path.exists():
                return

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            tracks_data = data.get("tracks", [])
            seen_ids = set()
            unique_tracks = []
            for t in tracks_data:
                if isinstance(t, dict):
                    t_obj = Track.from_dict(t)
                    if t_obj.id not in seen_ids:
                        seen_ids.add(t_obj.id)
                        unique_tracks.append(t_obj)

            self._queue = unique_tracks
            self._current_index = data.get("current_index", -1)
            if self._current_index >= len(self._queue):
                self._current_index = len(self._queue) - 1

            self._shuffle = data.get("shuffle", False)
            self._repeat = data.get("repeat", "off")
            logger.info(f"Queue state loaded from {filepath} ({len(self._queue)} unique tracks)")
        except Exception as e:
            logger.error(f"Failed to load queue state: {e}")
