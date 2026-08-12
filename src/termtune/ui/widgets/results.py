"""Search results list widget for TermTune (Strict Keyboard Navigation Only, Mouse Completely Disabled)."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, ListView, ListItem
from textual.message import Message

from termtune.models.track import Track


class KeyboardListView(ListView):
    """ListView that completely disables all mouse interactions (click, hover, mouse down/move)."""

    def on_mouse_down(self, event) -> None:
        event.prevent_default()
        event.stop()

    def _on_mouse_down(self, event) -> None:
        event.prevent_default()
        event.stop()

    def on_mouse_move(self, event) -> None:
        event.prevent_default()
        event.stop()

    def _on_mouse_move(self, event) -> None:
        event.prevent_default()
        event.stop()

    def on_click(self, event) -> None:
        event.prevent_default()
        event.stop()

    def _on_click(self, event) -> None:
        event.prevent_default()
        event.stop()


class SearchResultsWidget(Vertical):
    """Widget displaying search results as a styled B&W list of tracks."""

    class TrackSelected(Message):
        """Posted when user presses ENTER on a track."""

        def __init__(self, track: Track) -> None:
            super().__init__()
            self.track = track

    class TrackAddToQueue(Message):
        """Posted when user presses 'A' to add selected track to queue."""

        def __init__(self, track: Track) -> None:
            super().__init__()
            self.track = track

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tracks: list[Track] = []

    def compose(self) -> ComposeResult:
        yield Label("SEARCH RESULTS", id="results-header")
        yield KeyboardListView(id="results-list")

    def set_results(self, tracks: list[Track]) -> None:
        """Update list with search results."""
        self.tracks = tracks
        list_view = self.query_one("#results-list", KeyboardListView)
        list_view.clear()

        if not tracks:
            list_view.mount(
                ListItem(
                    Label("[dim]No search results found. Type a query above and press ENTER.[/dim]")
                )
            )
            return

        for idx, track in enumerate(tracks, 1):
            dur = track.formatted_duration
            title = track.title
            if len(title) > 65:
                title = title[:62] + "..."

            item_markup = (
                f"[bold white]{idx:2d}. {title}[/bold white]  [bold white]({dur})[/bold white]\n"
                f"    [#a1a1aa]{track.artist}  •  {track.source}[/#a1a1aa]"
            )
            list_view.mount(ListItem(Label(item_markup)))

    def get_selected_index(self) -> int | None:
        """Return currently selected index or None."""
        list_view = self.query_one("#results-list", KeyboardListView)
        if list_view.index is not None and 0 <= list_view.index < len(self.tracks):
            return list_view.index
        return None

    def get_selected_track(self) -> Track | None:
        """Return currently selected Track or None."""
        idx = self.get_selected_index()
        if idx is not None:
            return self.tracks[idx]
        return None

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter key on item."""
        track = self.get_selected_track()
        if track:
            self.post_message(self.TrackSelected(track))
