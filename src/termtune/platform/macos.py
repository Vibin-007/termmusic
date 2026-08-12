"""macOS platform adapter implementation."""

from pathlib import Path

from termtune.platform.base import BasePlatformAdapter


class MacOSPlatformAdapter(BasePlatformAdapter):
    """macOS specific platform adapter."""

    def get_platform_name(self) -> str:
        return "macOS"

    def get_mpv_search_paths(self) -> list[str]:
        return [
            "/opt/homebrew/bin/mpv",
            "/usr/local/bin/mpv",
            "/Applications/mpv.app/Contents/MacOS/mpv",
        ]

    def get_ipc_socket_path(self) -> str:
        sock_dir = Path.home() / ".termtune"
        sock_dir.mkdir(parents=True, exist_ok=True)
        return str(sock_dir / "mpv.sock")

    def get_installation_instructions(self) -> str:
        return (
            "✕ MPV was not found.\n\n"
            "Install MPV using Homebrew:\n"
            "  brew install mpv\n\n"
            "Then restart TermTune."
        )
