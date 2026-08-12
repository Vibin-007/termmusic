"""Windows platform adapter implementation."""

from termtune.platform.base import BasePlatformAdapter


class WindowsPlatformAdapter(BasePlatformAdapter):
    """Windows specific platform adapter."""

    def get_platform_name(self) -> str:
        return "Windows"

    def get_mpv_search_paths(self) -> list[str]:
        return [
            r"C:\Program Files\mpv\mpv.exe",
            r"C:\Program Files (x86)\mpv\mpv.exe",
            r"C:\ProgramData\chocolatey\bin\mpv.exe",
        ]

    def get_ipc_socket_path(self) -> str:
        return r"\\.\pipe\termtune_mpv"

    def get_installation_instructions(self) -> str:
        return (
            "✕ MPV was not found.\n\n"
            "Install MPV using Winget, Scoop, or Chocolatey:\n"
            "  Winget: winget install io.mpv.mpv\n"
            "  Scoop: scoop install mpv\n"
            "  Choco: choco install mpv\n\n"
            "Ensure mpv.exe is added to your PATH and restart TermTune."
        )
