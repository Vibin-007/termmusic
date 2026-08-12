"""Utility exceptions for TermTune."""


class TermTuneError(Exception):
    """Base exception for TermTune errors."""

    def __init__(self, message: str, user_friendly_msg: str | None = None):
        super().__init__(message)
        self.user_friendly_msg = user_friendly_msg or message


class MPVNotFoundError(TermTuneError):
    """Raised when MPV executable is not installed or found on system PATH."""

    def __init__(self, platform_name: str = "Linux"):
        msg = (
            "✕ MPV was not found.\n\n"
            f"Install MPV for {platform_name} and restart TermTune."
        )
        super().__init__("MPV binary not found in PATH", user_friendly_msg=msg)


class ProviderError(TermTuneError):
    """Raised when media search or stream resolution fails."""

    def __init__(self, message: str = "Search failed. Please try again."):
        super().__init__(message, user_friendly_msg=f"✕ {message}")


class NetworkError(TermTuneError):
    """Raised when internet or network request fails."""

    def __init__(self, message: str = "Unable to connect. Check your internet connection."):
        super().__init__(message, user_friendly_msg=f"✕ {message}")


class PlaybackError(TermTuneError):
    """Raised when track playback fails."""

    def __init__(self, message: str = "Unable to play this track. Try another result."):
        super().__init__(message, user_friendly_msg=f"✕ {message}")
