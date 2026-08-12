"""Formatting utilities for TermTune with clean high-contrast progress bars."""

import unicodedata


def sanitize_terminal_text(text: str) -> str:
    """Sanitize string for clean, glitch-free terminal rendering in Textual."""
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", text)

    cleaned_chars = []
    for char in normalized:
        category = unicodedata.category(char)
        if category.startswith("C"):
            continue
        cleaned_chars.append(char)

    result = "".join(cleaned_chars).strip()
    return result or text.strip()


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    if seconds is None or seconds < 0:
        return "00:00"

    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


# Alias for backward compatibility
format_time = format_duration


def format_progress_bar(position: float, duration: float, width: int = 24) -> str:
    """Format progress bar string with clean white knob indicator."""
    pos_str = format_duration(position)
    dur_str = format_duration(duration)

    if duration <= 0:
        bar = "[dim #52525b]" + "━" * width + "[/dim #52525b]"
        return f"{pos_str}  {bar}  {dur_str}"

    ratio = min(1.0, max(0.0, position / duration))
    filled_len = int(round(ratio * width))

    knob = "[bold white]●[/bold white]"
    filled_str = "[bold white]" + "━" * max(0, filled_len - 1) + "[/bold white]"
    unfilled_len = max(0, width - filled_len)
    unfilled_str = "[dim #52525b]" + "━" * unfilled_len + "[/dim #52525b]"

    bar_str = f"{filled_str}{knob}{unfilled_str}"
    return f"[bold white]{pos_str}[/bold white]  {bar_str}  [dim #a1a1aa]{dur_str}[/dim #a1a1aa]"


def format_volume_bar(volume: int, width: int = 10) -> str:
    """Format volume visual meter string: [████████░░]."""
    vol = min(100, max(0, volume))
    filled = int(round((vol / 100) * width))
    return "█" * filled + "░" * (width - filled)
