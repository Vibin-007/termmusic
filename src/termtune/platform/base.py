"""Base platform adapter interface."""

from abc import ABC, abstractmethod
import os
from pathlib import Path
import shutil


class BasePlatformAdapter(ABC):
    """Abstract base class for OS-specific behavior."""

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return human-readable OS name."""
        pass

    @abstractmethod
    def get_mpv_search_paths(self) -> list[str]:
        """Return list of common MPV binary paths to check."""
        pass

    @abstractmethod
    def get_ipc_socket_path(self) -> str:
        """Return path for MPV IPC socket or named pipe."""
        pass

    @abstractmethod
    def get_installation_instructions(self) -> str:
        """Return platform-specific installation instructions for MPV."""
        pass

    def get_mpv_path(self) -> str | None:
        """Locate mpv binary executable on system."""
        which_path = shutil.which("mpv")
        if which_path:
            return which_path

        for path in self.get_mpv_search_paths():
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    def is_mpv_installed(self) -> bool:
        """Check if mpv binary is available."""
        return self.get_mpv_path() is not None
