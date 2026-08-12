"""Now Playing widget for TermTune (High-Contrast Progress Bar)."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label

from termtune.models.track import Track
from termtune.player.mpv import PlaybackState
from termtune.utils.formatting import format_progress_bar


class NowPlayingWidget(Vertical):
    """Widget displaying current playback state, track info, and progress in B&W."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_track: Track | None = None
        self.playback_state: PlaybackState = PlaybackState.IDLE
        self.position: float = 0.0
        self.duration: float = 0.0
        self.volume: int = 80
        self.muted: bool = False
        self.shuffle: bool = False
        self.repeat: str = "off"

    def compose(self) -> ComposeResult:
        yield Label("NOW PLAYING", id="now-playing-header")
        yield Label("🎵  [dim]No track playing[/dim]", id="now-playing-title")
        yield Label("🎤  [dim]Select a song to start playback[/dim]", id="now-playing-artist")
        yield Label("00:00 ━━━━━━━━━━━━━━━━━━━━ 00:00", id="now-playing-progress")
        yield Label("[bold black on #ffffff] IDLE [/]", id="now-playing-info-bar")
        yield Label("[bold white]⏮    ◀◀    ▶    ⏸    ▶▶    ⏭[/bold white]", id="now-playing-controls-bar")

    def update_playback(
        self,
        track: Track | None,
        state: PlaybackState,
        position: float,
        duration: float,
        volume: int,
        muted: bool,
        shuffle: bool,
        repeat: str,
    ) -> None:
        """Refresh all Now Playing UI labels."""
        self.current_track = track
        self.playback_state = state
        self.position = position
        self.duration = duration
        self.volume = volume
        self.muted = muted
        self.shuffle = shuffle
        self.repeat = repeat

        title_lbl = self.query_one("#now-playing-title", Label)
        artist_lbl = self.query_one("#now-playing-artist", Label)
        progress_lbl = self.query_one("#now-playing-progress", Label)
        info_lbl = self.query_one("#now-playing-info-bar", Label)
        controls_lbl = self.query_one("#now-playing-controls-bar", Label)

        if track:
            title_lbl.update(f"🎵  [bold white]{track.title}[/bold white]")
            artist_lbl.update(f"🎤  [dim #a1a1aa]{track.artist}[/dim #a1a1aa]")
            tot = duration or track.duration or 0
            progress_lbl.update(format_progress_bar(position, tot))
        else:
            title_lbl.update("🎵  [dim]No track playing[/dim]")
            artist_lbl.update("🎤  [dim]Select a song to start playback[/dim]")
            progress_lbl.update("[dim]00:00  ━━━━━━━━━━━━━━━━━━━━━━━━  00:00[/dim]")

        # B&W State Badges
        state_badge_map = {
            PlaybackState.PLAYING: "[bold black on #ffffff] ▶ PLAYING [/bold black on #ffffff]",
            PlaybackState.PAUSED: "[bold black on #a1a1aa] Ⅱ PAUSED [/bold black on #a1a1aa]",
            PlaybackState.LOADING: "[bold black on #ffffff] ◌ LOADING [/bold black on #ffffff]",
            PlaybackState.STOPPED: "[bold black on #71717a] ■ STOPPED [/bold black on #71717a]",
            PlaybackState.ERROR: "[bold black on #ffffff] ✕ ERROR [/bold black on #ffffff]",
            PlaybackState.IDLE: "[bold black on #71717a] IDLE [/bold black on #71717a]",
        }
        st_badge = state_badge_map.get(state, f"[bold white]{state}[/bold white]")

        shuf_badge = "  [bold black on #ffffff] 🔀 ON [/]" if shuffle else ""
        rep_badge = f"  [bold black on #ffffff] ↻ {repeat.upper()} [/]" if repeat != "off" else ""

        # Clean Info line without volume text
        info_lbl.update(f"{st_badge}{shuf_badge}{rep_badge}")

        # Controls bar visual
        if state == PlaybackState.PLAYING:
            controls_lbl.update("[bold white]⏮    ◀◀    [bold black on #ffffff] ▶ [/]    ⏸    ▶▶    ⏭[/bold white]")
        elif state == PlaybackState.PAUSED:
            controls_lbl.update("[bold white]⏮    ◀◀    ▶    [bold black on #ffffff] ⏸ [/]    ▶▶    ⏭[/bold white]")
        else:
            controls_lbl.update("[bold #71717a]⏮    ◀◀    ▶    ⏸    ▶▶    ⏭[/bold #71717a]")
