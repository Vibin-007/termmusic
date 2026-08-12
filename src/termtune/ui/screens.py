"""Main screen and UI layout for TermTune (Instant Playlist Playback & Complete Engine)."""

import asyncio
import logging
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.events import Resize
from textual.screen import Screen
from textual.widgets import Input, Label

from termtune.models.track import Track
from termtune.player.controller import PlayerController
from termtune.player.mpv import PlaybackState
from termtune.ui.modals import PlaylistSelectModal, TrackActionModal
from termtune.ui.widgets import (
    ControlsWidget,
    NowPlayingWidget,
    QueueWidget,
    SearchResultsWidget,
    SearchWidget,
)
from termtune.ui.widgets.results import KeyboardListView
from termtune.utils.errors import TermTuneError

logger = logging.getLogger(__name__)


class MainScreen(Screen):
    """Primary user interface screen for TermTune."""

    BINDINGS = [
        Binding("space", "toggle_play_pause", "Play/Pause", show=False),
        Binding("n", "next_track", "Next", show=False),
        Binding("b", "prev_track", "Previous", show=False),
        Binding("s", "focus_search", "Search", show=False),
        Binding("q", "quit_app", "Quit", show=False),
        Binding("escape", "unfocus_input", "Unfocus", show=False),
        Binding("plus,equals", "volume_up", "Volume Up", show=False),
        Binding("minus,underscore", "volume_down", "Volume Down", show=False),
        Binding("m", "toggle_mute", "Mute", show=False),
        Binding("r", "toggle_repeat", "Repeat", show=False),
        Binding("z", "toggle_shuffle", "Shuffle", show=False),
        Binding("left", "seek_backward", "Seek Back", show=False),
        Binding("right", "seek_forward", "Seek Forward", show=False),
        Binding("a", "add_to_queue", "Add Queue", show=False),
        Binding("shift+a", "add_play_next", "Play Next", show=False),
        Binding("p", "open_playlists", "Playlists", show=False),
        Binding("c", "clear_queue", "Clear Queue", show=False),
        Binding("k,up", "move_up", "Up", show=False),
        Binding("j,down", "move_down", "Down", show=False),
    ]

    def __init__(self, controller: PlayerController, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller

    def compose(self) -> ComposeResult:
        # Top Header Banner
        with Container(id="header-box"):
            yield Label("🎵 TERMTUNE", id="header-title")
            yield Label("Terminal Online Music Player", id="header-subtitle")

        # Main Workspace Container
        with Container(id="main-container"):
            with Vertical(id="left-pane"):
                yield SearchWidget(id="search-widget")
                yield SearchResultsWidget(id="results-widget")

            with Vertical(id="right-pane"):
                yield NowPlayingWidget(id="now-playing-widget")
                yield QueueWidget(id="queue-widget")

        # Keybindings Footer
        yield ControlsWidget(id="controls-footer")

    def on_mount(self) -> None:
        """Invoked when screen is mounted."""
        self._update_layout_class(self.size.width)
        self.set_interval(0.5, self.update_tick)

        # Wire controller callbacks
        self.controller.set_on_track_change(self._on_track_changed)
        self.controller.set_on_error(self._on_controller_error)

        # Initial UI refresh
        self.refresh_ui()

    def on_resize(self, event: Resize) -> None:
        """Handle screen resize for responsive layouts."""
        self._update_layout_class(event.size.width)

    def _update_layout_class(self, width: int) -> None:
        if width < 90:
            self.remove_class("wide-layout")
            self.add_class("narrow-layout")
        else:
            self.remove_class("narrow-layout")
            self.add_class("wide-layout")

    def _is_input_focused(self) -> bool:
        """Check if user is currently typing inside an Input text box."""
        return isinstance(self.focused, Input)

    def is_track_playing(self) -> bool:
        """Return True if a track is currently actively playing or paused."""
        return (
            self.controller.current_track is not None
            and self.controller.mpv.state in (PlaybackState.PLAYING, PlaybackState.PAUSED)
        )

    def update_tick(self) -> None:
        """Periodic timer updating progress bar and playing info."""
        now_playing = self.query_one("#now-playing-widget", NowPlayingWidget)
        mpv = self.controller.mpv
        now_playing.update_playback(
            track=self.controller.current_track,
            state=mpv.state,
            position=mpv.position,
            duration=mpv.duration,
            volume=mpv.volume,
            muted=mpv.muted,
            shuffle=self.controller.queue_manager.shuffle,
            repeat=self.controller.queue_manager.repeat,
        )

        queue_widget = self.query_one("#queue-widget", QueueWidget)
        queue_widget.update_queue(
            items=self.controller.queue_manager.items,
            current_index=self.controller.queue_manager.current_index,
            total_duration=self.controller.queue_manager.total_duration,
        )

    def refresh_ui(self) -> None:
        """Trigger update tick immediately."""
        self.update_tick()

    def _on_track_changed(self, track: Track | None) -> None:
        """Callback when active playing track changes."""
        self.refresh_ui()

    def _on_controller_error(self, err: TermTuneError) -> None:
        """Callback when playback error occurs."""
        search_widget = self.query_one("#search-widget", SearchWidget)
        search_widget.set_error_state(err.user_friendly_msg)
        self.notify(err.user_friendly_msg, severity="error", title="Playback Error")

    async def _play_track_with_status(self, track: Track) -> None:
        """Helper to set stream status and start playback."""
        search_widget = self.query_one("#search-widget", SearchWidget)
        search_widget.query_one("#search-status", Label).update(
            f"[bold white]◌ Resolving stream for '{track.title}'...[/bold white]"
        )
        await self.controller.play_track(track, add_to_queue=True)
        results_widget = self.query_one("#results-widget", SearchResultsWidget)
        results_widget.query_one("#results-list", KeyboardListView).focus()

    def _handle_track_selection(self, track: Track) -> None:
        """Prompt modal dialog if a song is playing, otherwise play immediately."""
        if self.is_track_playing():
            def modal_callback(choice: str | None) -> None:
                if choice == "play_now":
                    asyncio.create_task(self._play_track_with_status(track))
                elif choice == "play_next":
                    idx, is_dup = self.controller.queue_manager.add_next(track)
                    if is_dup:
                        self.notify(
                            f"⚠️ Track is already in queue at position #{idx + 1}!",
                            severity="warning",
                            timeout=3,
                        )
                    else:
                        self.notify(f"Set to Play Next: {track.title}", timeout=2)
                    self.controller.save_queue_state()
                    self.refresh_ui()
                elif choice == "add_to_queue":
                    idx, is_dup = self.controller.queue_manager.add(track)
                    if is_dup:
                        self.notify(
                            f"⚠️ Track is already in queue at position #{idx + 1}!",
                            severity="warning",
                            timeout=3,
                        )
                    else:
                        self.notify(f"Added to queue: {track.title}", timeout=2)
                    self.controller.save_queue_state()
                    self.refresh_ui()
                elif choice == "add_to_playlist":
                    self._open_add_to_playlist_modal(track)

            self.app.push_screen(TrackActionModal(track), modal_callback)
        else:
            asyncio.create_task(self._play_track_with_status(track))

    def _open_add_to_playlist_modal(self, track: Track) -> None:
        def on_selected(res: tuple[str, str]) -> None:
            action, playlist_name = res
            if action == "select" and playlist_name:
                ok, msg = self.controller.playlist_manager.add_track(playlist_name, track)
                if ok:
                    self.notify(msg, timeout=2)
                else:
                    self.notify(msg, severity="warning", timeout=3)

        self.app.push_screen(
            PlaylistSelectModal(self.controller.playlist_manager, mode="add_track"),
            on_selected,
        )

    # Search Event Handlers
    async def on_search_widget_submitted(self, message: SearchWidget.Submitted) -> None:
        """Handle search query submit - auto-plays only if idle, otherwise just displays results."""
        query = message.query
        search_widget = self.query_one("#search-widget", SearchWidget)
        results_widget = self.query_one("#results-widget", SearchResultsWidget)

        try:
            tracks = await self.controller.provider.search(query)
            results_widget.set_results(tracks)
            search_widget.set_results_state(len(tracks))
            results_widget.query_one("#results-list", KeyboardListView).focus()

            # Auto-play 1st result ONLY if no song is currently playing
            if tracks and not self.is_track_playing():
                top_track = tracks[0]
                await self._play_track_with_status(top_track)

        except TermTuneError as e:
            search_widget.set_error_state(e.user_friendly_msg)
            self.notify(e.user_friendly_msg, severity="error")
        except Exception as e:
            logger.error(f"Search exception: {e}")
            search_widget.set_error_state("Search failed. Please try again.")

    # Table/List Selection Handlers
    def on_search_results_widget_track_selected(
        self, message: SearchResultsWidget.TrackSelected
    ) -> None:
        """Handle track selection from search results list."""
        self._handle_track_selection(message.track)

    async def on_queue_widget_queue_item_selected(
        self, message: QueueWidget.QueueItemSelected
    ) -> None:
        """Play track selected from queue list."""
        await self.controller.play_queue_index(message.index)

    def on_queue_widget_queue_item_delete(
        self, message: QueueWidget.QueueItemDelete
    ) -> None:
        """Handle track deletion from queue."""
        removed = self.controller.queue_manager.remove(message.index)
        if removed:
            self.notify(f"Removed from queue: {removed.title}", timeout=2)
            self.controller.save_queue_state()
            self.refresh_ui()

    def on_queue_widget_queue_item_move_up(
        self, message: QueueWidget.QueueItemMoveUp
    ) -> None:
        """Handle moving item up in queue."""
        if self.controller.queue_manager.move_up(message.index):
            self.controller.save_queue_state()
            self.refresh_ui()

    def on_queue_widget_queue_item_move_down(
        self, message: QueueWidget.QueueItemMoveDown
    ) -> None:
        """Handle moving item down in queue."""
        if self.controller.queue_manager.move_down(message.index):
            self.controller.save_queue_state()
            self.refresh_ui()

    def on_queue_widget_queue_toggle_filter(
        self, message: QueueWidget.QueueToggleFilter
    ) -> None:
        """Handle '/' filter keypress in queue."""
        queue_widget = self.query_one("#queue-widget", QueueWidget)
        queue_widget.toggle_filter()

    # Global Action Binds
    def action_open_playlists(self) -> None:
        """Open playlist selector modal to load playlist into queue and play immediately."""
        if self._is_input_focused():
            return

        def on_selected(res: tuple[str, str]) -> None:
            action, playlist_name = res
            if action == "select" and playlist_name:
                asyncio.create_task(self._load_and_play_playlist(playlist_name))

        self.app.push_screen(
            PlaylistSelectModal(self.controller.playlist_manager, mode="load"),
            on_selected,
        )

    async def _load_and_play_playlist(self, playlist_name: str) -> None:
        """Load playlist tracks into queue and immediately start playback of track 1."""
        count = await self.controller.load_playlist_into_queue(playlist_name, replace=True)
        if count > 0:
            first_track = self.controller.queue_manager.items[0]
            search_widget = self.query_one("#search-widget", SearchWidget)
            search_widget.query_one("#search-status", Label).update(
                f"[bold white]◌ Resolving stream for '{first_track.title}'...[/bold white]"
            )
            self.notify(f"Playing playlist '{playlist_name}' ({count} tracks)", timeout=2)
            await self.controller.play_queue_index(0)
        else:
            self.notify(f"Playlist '{playlist_name}' is empty", severity="warning", timeout=2)
        self.refresh_ui()

    async def action_toggle_play_pause(self) -> None:
        if self._is_input_focused():
            return
        await self.controller.toggle_play_pause()
        self.refresh_ui()

    async def action_next_track(self) -> None:
        if self._is_input_focused():
            return
        await self.controller.next()
        self.refresh_ui()

    async def action_prev_track(self) -> None:
        if self._is_input_focused():
            return
        await self.controller.previous()
        self.refresh_ui()

    def action_focus_search(self) -> None:
        search_widget = self.query_one("#search-widget", SearchWidget)
        search_widget.focus_input()

    def action_unfocus_input(self) -> None:
        results_list = self.query_one("#results-list", KeyboardListView)
        results_list.focus()

    async def action_volume_up(self) -> None:
        if self._is_input_focused():
            return
        vol = await self.controller.increase_volume(5)
        self.notify(f"Volume: {vol}%", timeout=1)
        self.refresh_ui()

    async def action_volume_down(self) -> None:
        if self._is_input_focused():
            return
        vol = await self.controller.decrease_volume(5)
        self.notify(f"Volume: {vol}%", timeout=1)
        self.refresh_ui()

    async def action_toggle_mute(self) -> None:
        if self._is_input_focused():
            return
        muted = await self.controller.toggle_mute()
        status = "Muted" if muted else "Unmuted"
        self.notify(f"Audio {status}", timeout=1)
        self.refresh_ui()

    def action_toggle_repeat(self) -> None:
        if self._is_input_focused():
            return
        mode = self.controller.toggle_repeat()
        self.notify(f"Repeat mode: {mode.upper()}", timeout=1)
        self.refresh_ui()

    def action_toggle_shuffle(self) -> None:
        if self._is_input_focused():
            return
        shuf = self.controller.toggle_shuffle()
        status = "On" if shuf else "Off"
        self.notify(f"Shuffle: {status}", timeout=1)
        self.refresh_ui()

    async def action_seek_backward(self) -> None:
        if self._is_input_focused():
            return
        await self.controller.seek(-10)
        self.refresh_ui()

    async def action_seek_forward(self) -> None:
        if self._is_input_focused():
            return
        await self.controller.seek(10)
        self.refresh_ui()

    def action_add_to_queue(self) -> None:
        if self._is_input_focused():
            return
        results_widget = self.query_one("#results-widget", SearchResultsWidget)
        track = results_widget.get_selected_track()
        if track:
            idx, is_dup = self.controller.queue_manager.add(track)
            if is_dup:
                self.notify(
                    f"⚠️ Track is already in queue at position #{idx + 1}!",
                    severity="warning",
                    timeout=3,
                )
            else:
                self.notify(f"Added to queue: {track.title}", timeout=2)
            self.controller.save_queue_state()
            self.refresh_ui()

    def action_add_play_next(self) -> None:
        if self._is_input_focused():
            return
        results_widget = self.query_one("#results-widget", SearchResultsWidget)
        track = results_widget.get_selected_track()
        if track:
            idx, is_dup = self.controller.queue_manager.add_next(track)
            if is_dup:
                self.notify(
                    f"⚠️ Track is already in queue at position #{idx + 1}!",
                    severity="warning",
                    timeout=3,
                )
            else:
                self.notify(f"Set to Play Next: {track.title}", timeout=2)
            self.controller.save_queue_state()
            self.refresh_ui()

    def action_clear_queue(self) -> None:
        if self._is_input_focused():
            return
        self.controller.queue_manager.clear()
        self.controller.save_queue_state()
        self.notify("Queue cleared", timeout=1)
        self.refresh_ui()

    def action_move_up(self) -> None:
        if self._is_input_focused():
            return
        queue_widget = self.query_one("#queue-widget", QueueWidget)
        if self.focused == queue_widget.query_one("#queue-list"):
            idx = queue_widget.get_selected_index()
            if idx is not None:
                if self.controller.queue_manager.move_up(idx):
                    self.controller.save_queue_state()
                    self.refresh_ui()

    def action_move_down(self) -> None:
        if self._is_input_focused():
            return
        queue_widget = self.query_one("#queue-widget", QueueWidget)
        if self.focused == queue_widget.query_one("#queue-list"):
            idx = queue_widget.get_selected_index()
            if idx is not None:
                if self.controller.queue_manager.move_down(idx):
                    self.controller.save_queue_state()
                    self.refresh_ui()

    async def action_quit_app(self) -> None:
        if self._is_input_focused():
            return
        await self.controller.shutdown()
        self.app.exit()
