"""Modal pop-up screens for TermTune (Action Choice & Playlist Selection Dialogs)."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView

from termtune.models.track import Track
from termtune.playlist.manager import PlaylistManager


class TrackActionModal(ModalScreen[str]):
    """Modal dialog asking whether to 'Play Now', 'Play Next', 'Add Queue', or 'Add Playlist'."""

    BINDINGS = [
        Binding("p", "choose_play_now", "Play Now"),
        Binding("n", "choose_play_next", "Play Next"),
        Binding("a", "choose_add_queue", "Add Queue"),
        Binding("l", "choose_add_playlist", "Add Playlist"),
        Binding("escape", "choose_cancel", "Cancel"),
    ]

    def __init__(self, track: Track, **kwargs):
        super().__init__(**kwargs)
        self.track = track

    def compose(self) -> ComposeResult:
        with Container(id="modal-dialog"):
            yield Label("🎵 TRACK ACTION", id="modal-title")
            yield Label(
                "A track is currently playing. What would you like to do with:",
                id="modal-message",
            )
            yield Label(
                f"[bold white]'{self.track.title}'[/bold white]\n[dim #a1a1aa]by {self.track.artist}[/dim #a1a1aa]",
                id="modal-track-info",
            )
            with Horizontal(id="modal-buttons"):
                yield Button("Play Now (P)", id="btn-play-now", variant="primary")
                yield Button("Play Next (N)", id="btn-play-next", variant="default")
                yield Button("Add Queue (A)", id="btn-add-queue", variant="default")
                yield Button("Playlist (L)", id="btn-add-playlist", variant="default")
                yield Button("Cancel (ESC)", id="btn-cancel", variant="error")

    def on_mount(self) -> None:
        """Focus the primary button on mount."""
        self.query_one("#btn-play-now", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button click/keypress."""
        btn_id = event.button.id
        if btn_id == "btn-play-now":
            self.dismiss("play_now")
        elif btn_id == "btn-play-next":
            self.dismiss("play_next")
        elif btn_id == "btn-add-queue":
            self.dismiss("add_to_queue")
        elif btn_id == "btn-add-playlist":
            self.dismiss("add_to_playlist")
        else:
            self.dismiss("cancel")

    def action_choose_play_now(self) -> None:
        self.dismiss("play_now")

    def action_choose_play_next(self) -> None:
        self.dismiss("play_next")

    def action_choose_add_queue(self) -> None:
        self.dismiss("add_to_queue")

    def action_choose_add_playlist(self) -> None:
        self.dismiss("add_to_playlist")

    def action_choose_cancel(self) -> None:
        self.dismiss("cancel")


class CreatePlaylistModal(ModalScreen[str]):
    """Modal asking for a new playlist name."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="modal-dialog"):
            yield Label("📁 CREATE NEW PLAYLIST", id="modal-title")
            yield Label("Enter a name for the new playlist:", id="modal-message")
            yield Input(placeholder="e.g. Workout, Lo-Fi Chill, Favorites", id="playlist-name-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Create (ENTER)", id="btn-create", variant="primary")
                yield Button("Cancel (ESC)", id="btn-cancel", variant="error")

    def on_mount(self) -> None:
        self.query_one("#playlist-name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        if val:
            self.dismiss(val)
        else:
            self.dismiss("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create":
            val = self.query_one("#playlist-name-input", Input).value.strip()
            self.dismiss(val)
        else:
            self.dismiss("")

    def action_cancel(self) -> None:
        self.dismiss("")


class PlaylistSelectModal(ModalScreen[tuple[str, str]]):
    """Modal to select a playlist to Load or Add track to. Returns (action, playlist_name)."""

    BINDINGS = [
        Binding("c,plus", "create_new", "Create New"),
        Binding("d,delete", "delete_selected", "Delete Playlist"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, playlist_mgr: PlaylistManager, mode: str = "select", **kwargs):
        super().__init__(**kwargs)
        self.playlist_mgr = playlist_mgr
        self.mode = mode  # "load" or "add_track"

    def compose(self) -> ComposeResult:
        title = "📁 SELECT PLAYLIST TO LOAD" if self.mode == "load" else "➕ ADD TRACK TO PLAYLIST"
        with Container(id="modal-dialog"):
            yield Label(title, id="modal-title")
            yield Label("Press [bold white]ENTER[/bold white] to select • [bold white]C[/bold white] New Playlist • [bold white]D[/bold white] Delete", id="modal-message")
            yield ListView(id="playlist-list")
            with Horizontal(id="modal-buttons"):
                yield Button("Create New (C)", id="btn-new", variant="default")
                yield Button("Cancel (ESC)", id="btn-cancel", variant="error")

    def on_mount(self) -> None:
        self.refresh_list()
        self.query_one("#playlist-list", ListView).focus()

    def refresh_list(self) -> None:
        list_view = self.query_one("#playlist-list", ListView)
        list_view.clear()
        playlists = self.playlist_mgr.list_playlists()
        if not playlists:
            list_view.mount(ListItem(Label("[dim]No playlists found. Press 'C' to create one.[/dim]")))
        else:
            for name in playlists:
                tracks = self.playlist_mgr.load_playlist(name)
                list_view.mount(ListItem(Label(f"📁 [bold white]{name}[/bold white] [dim]({len(tracks)} tracks)[/dim]")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        list_view = self.query_one("#playlist-list", ListView)
        playlists = self.playlist_mgr.list_playlists()
        if list_view.index is not None and 0 <= list_view.index < len(playlists):
            selected_name = playlists[list_view.index]
            self.dismiss(("select", selected_name))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new":
            self.action_create_new()
        else:
            self.dismiss(("cancel", ""))

    def action_create_new(self) -> None:
        def on_created(name: str | None) -> None:
            if name:
                self.playlist_mgr.create_playlist(name)
                self.refresh_list()

        self.app.push_screen(CreatePlaylistModal(), on_created)

    def action_delete_selected(self) -> None:
        list_view = self.query_one("#playlist-list", ListView)
        playlists = self.playlist_mgr.list_playlists()
        if list_view.index is not None and 0 <= list_view.index < len(playlists):
            selected_name = playlists[list_view.index]
            self.playlist_mgr.delete_playlist(selected_name)
            self.refresh_list()

    def action_cancel(self) -> None:
        self.dismiss(("cancel", ""))
