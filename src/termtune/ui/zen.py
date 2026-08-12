"""Zen Mode Screen: Minimalist animated ASCII vinyl screensaver for TermTune."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Label

from termtune.player.controller import PlayerController
from termtune.player.mpv import PlaybackState
from termtune.utils.formatting import format_progress_bar, format_time

VINYL_FRAMES = [
    r"""
           .-------------------.
          /   .-------------.   \
         |   /   .-'●'-.     \   |
         |  |   /   |   \     |  |
         |  |  |  ──◯──  |    |  |
         |  |   \   |   /     |  |
         |   \   '-.●.-'     /   |
          \   '-------------'   /
           '-------------------'
""",
    r"""
           .-------------------.
          /   .-------------.   \
         |   /   .---.       \   |
         |  |   /  / \ \      |  |
         |  |  |  ──◯──  |    |  |
         |  |   \  \ / /      |  |
         |   \   '---'       /   |
          \   '-------------'   /
           '-------------------'
""",
    r"""
           .-------------------.
          /   .-------------.   \
         |   /   .-'│'-.     \   |
         |  |   /   ●   \     |  |
         |  |  |  ──◯──  |    |  |
         |  |   \   ●   /     |  |
         |   \   '-.│.-'     /   |
          \   '-------------'   /
           '-------------------'
""",
    r"""
           .-------------------.
          /   .-------------.   \
         |   /   .---.       \   |
         |  |   /  \ / \      |  |
         |  |  |  ──◯──  |    |  |
         |  |   \  / \ /      |  |
         |   \   '---'       /   |
          \   '-------------'   /
           '-------------------'
""",
]


class ZenScreen(Screen):
    """Full-screen minimalist Zen Mode animated vinyl screensaver."""

    BINDINGS = [
        Binding("escape", "exit_zen", "Exit Zen Mode"),
        Binding("Z", "exit_zen", "Exit Zen Mode"),
        Binding("z", "exit_zen", "Exit Zen Mode"),
        Binding("shift+z", "exit_zen", "Exit Zen Mode"),
        Binding("ctrl+z", "exit_zen", "Exit Zen Mode"),
        Binding("space", "toggle_play_pause", "Play/Pause"),
        Binding("n", "next_track", "Next Track"),
        Binding("b", "prev_track", "Previous Track"),
    ]

    def __init__(self, controller: PlayerController, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.frame_idx = 0

    def compose(self) -> ComposeResult:
        with Container(id="zen-container"):
            yield Label("✨ ZEN MODE ✨", id="zen-header")
            yield Label(VINYL_FRAMES[0], id="zen-vinyl")
            yield Label("", id="zen-title")
            yield Label("", id="zen-artist")
            yield Label("", id="zen-progress")
            yield Label("", id="zen-status-bar")
            yield Label("[dim #a1a1aa]Press [bold white]ESC[/bold white] or [bold white]Z[/bold white] to exit Zen Mode[/dim #a1a1aa]", id="zen-footer")

    def on_mount(self) -> None:
        """Start animation loop timer."""
        self.set_interval(0.2, self.anim_tick)

    def anim_tick(self) -> None:
        """Update vinyl animation frame and track info."""
        mpv = self.controller.mpv
        track = self.controller.current_track

        # Rotate vinyl frame if playing
        if mpv.state == PlaybackState.PLAYING:
            self.frame_idx = (self.frame_idx + 1) % len(VINYL_FRAMES)

        vinyl_widget = self.query_one("#zen-vinyl", Label)
        vinyl_widget.update(VINYL_FRAMES[self.frame_idx])

        title_widget = self.query_one("#zen-title", Label)
        artist_widget = self.query_one("#zen-artist", Label)
        progress_widget = self.query_one("#zen-progress", Label)
        status_widget = self.query_one("#zen-status-bar", Label)

        if track:
            title_widget.update(f"[bold white]{track.title}[/bold white]")
            artist_widget.update(f"[dim #a1a1aa]by {track.artist}[/dim #a1a1aa]")

            pos_str = format_time(mpv.position)
            dur_str = format_time(mpv.duration)
            pbar = format_progress_bar(mpv.position, mpv.duration, width=32)
            progress_widget.update(f"[bold white]{pbar}[/bold white]\n[dim]{pos_str} / {dur_str}[/dim]")

            state_str = "▶ PLAYING" if mpv.state == PlaybackState.PLAYING else "⏸ PAUSED"
            status_widget.update(f"[bold white]{state_str}[/bold white]")
        else:
            title_widget.update("[bold white]No track playing[/bold white]")
            artist_widget.update("[dim]Search and play music to start[/dim]")
            progress_widget.update("")
            status_widget.update("[dim]STOPPED[/dim]")

    def action_exit_zen(self) -> None:
        """Exit Zen Screen and return to Main Screen."""
        self.app.pop_screen()

    async def action_toggle_play_pause(self) -> None:
        await self.controller.toggle_play_pause()
        self.anim_tick()

    async def action_next_track(self) -> None:
        await self.controller.next()
        self.anim_tick()

    async def action_prev_track(self) -> None:
        await self.controller.previous()
        self.anim_tick()
