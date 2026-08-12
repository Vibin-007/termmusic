"""Linux platform adapter implementation."""

from pathlib import Path

from termtune.platform.base import BasePlatformAdapter


class LinuxPlatformAdapter(BasePlatformAdapter):
    """Linux specific platform adapter."""

    def get_platform_name(self) -> str:
        return "Linux"

    def get_mpv_search_paths(self) -> list[str]:
        return [
            "/usr/bin/mpv",
            "/usr/local/bin/mpv",
            "/snap/bin/mpv",
            "~/.local/bin/mpv",
        ]

    def get_ipc_socket_path(self) -> str:
        sock_dir = Path.home() / ".termtune"
        sock_dir.mkdir(parents=True, exist_ok=True)
        return str(sock_dir / "mpv.sock")

    def get_installation_instructions(self) -> str:
        return (
            "✕ MPV was not found.\n\n"
            "Install MPV using your package manager:\n"
            "  Ubuntu/Debian: sudo apt install mpv\n"
            "  Fedora: sudo dnf install mpv\n"
            "  Arch Linux: sudo pacman -S mpv\n\n"
            "Then restart TermTune."
        )
