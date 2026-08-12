"""Queue list widget for TermTune (Keyboard-Driven, Filtering, Removal & Reordering)."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Input, Label, ListView, ListItem
from textual.message import Message

from termtune.models.track import Track
from termtune.utils.formatting import format_duration


class KeyboardListView(ListView):
    """ListView that disables mouse click/hover selection, handling queue keybindings."""

    BINDINGS = [
        Binding("d,delete", "delete_item", "Delete Track", show=False),
        Binding("alt+up", "move_up", "Move Up", show=False),
        Binding("alt+down", "move_down", "Move Down", show=False),
        Binding("slash", "filter_queue", "Filter Queue", show=False),
    ]

    def _on_click(self, event) -> None:
        event.prevent_default()
        event.stop()

    def _on_mouse_down(self, event) -> None:
        event.prevent_default()
        event.stop()

    def _on_mouse_move(self, event) -> None:
        event.prevent_default()
        event.stop()

    def action_delete_item(self) -> None:
        if self.index is not None:
            self.post_message(QueueWidget.QueueItemDelete(self.index))

    def action_move_up(self) -> None:
        if self.index is not None:
            self.post_message(QueueWidget.QueueItemMoveUp(self.index))

    def action_move_down(self) -> None:
        if self.index is not None:
            self.post_message(QueueWidget.QueueItemMoveDown(self.index))

    def action_filter_queue(self) -> None:
        self.post_message(QueueWidget.QueueToggleFilter())


class QueueWidget(Vertical):
    """Widget displaying the playback queue with duration, filter, and management."""

    class QueueItemSelected(Message):
        """Posted when user presses ENTER on a queue item."""

        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class QueueItemDelete(Message):
        """Posted when user presses 'D' or Delete to remove an item."""

        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class QueueItemMoveUp(Message):
        """Posted when user presses Alt+Up to swap item position."""

        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class QueueItemMoveDown(Message):
        """Posted when user presses Alt+Down to swap item position."""

        def __init__(self, index: int) -> None:
            super().__init__()
            self.index = index

    class QueueToggleFilter(Message):
        """Posted when user presses '/' to filter queue."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_signature: tuple | None = None
        self.filter_query: str = ""

    def compose(self) -> ComposeResult:
        yield Label("PLAYBACK QUEUE (0 tracks • 00:00 total)", id="queue-header")
        yield Input(placeholder="🔍 Filter queue...", id="queue-filter-input")
        yield KeyboardListView(id="queue-list")

    def on_mount(self) -> None:
        """Hide filter input initially."""
        filter_input = self.query_one("#queue-filter-input", Input)
        filter_input.display = False

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter queue items as user types."""
        if event.input.id == "queue-filter-input":
            self.filter_query = event.value.strip().lower()
            self._last_signature = None  # Force redraw

    def toggle_filter(self) -> None:
        """Toggle filter input box visibility."""
        filter_input = self.query_one("#queue-filter-input", Input)
        if filter_input.display:
            filter_input.display = False
            self.filter_query = ""
            self._last_signature = None
            self.query_one("#queue-list", KeyboardListView).focus()
        else:
            filter_input.display = True
            filter_input.focus()

    def update_queue(self, items: list[Track], current_index: int, total_duration: int = 0) -> None:
        """Refresh queue list only if contents, index, or filter have changed."""
        signature = (tuple(t.id for t in items), current_index, total_duration, self.filter_query)
        if signature == self._last_signature:
            return  # Skip redundant redraw to prevent flickering

        self._last_signature = signature

        header = self.query_one("#queue-header", Label)
        list_view = self.query_one("#queue-list", KeyboardListView)

        dur_str = format_duration(total_duration)
        header.update(f"PLAYBACK QUEUE ({len(items)} tracks • {dur_str} total)")

        old_idx = list_view.index
        list_view.clear()

        if not items:
            list_view.mount(
                ListItem(
                    Label("[dim]Queue is empty. Select a song and press 'A' or ENTER to play.[/dim]")
                )
            )
            return

        for idx, track in enumerate(items):
            # Check filter query match
            if self.filter_query and (
                self.filter_query not in track.title.lower()
                and self.filter_query not in track.artist.lower()
            ):
                continue

            dur = track.formatted_duration
            title = track.title
            if len(title) > 55:
                title = title[:52] + "..."

            if idx == current_index:
                item_markup = (
                    f"[bold white]▶ {idx + 1:2d}. {title}[/bold white]  [bold white]({dur})[/bold white]\n"
                    f"     [bold black on #ffffff] NOW PLAYING [/bold black on #ffffff]  [bold white]{track.artist}[/bold white]"
                )
            else:
                item_markup = (
                    f"[bold white]  {idx + 1:2d}. {title}[/bold white]  [bold white]({dur})[/bold white]\n"
                    f"     [#a1a1aa]{track.artist}[/#a1a1aa]"
                )
            list_view.mount(ListItem(Label(item_markup)))

        if old_idx is not None and old_idx < len(items):
            list_view.index = old_idx

    def get_selected_index(self) -> int | None:
        """Return index of selected queue item or None."""
        list_view = self.query_one("#queue-list", KeyboardListView)
        return list_view.index

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle Enter key on queue row."""
        idx = self.get_selected_index()
        if idx is not None:
            self.post_message(self.QueueItemSelected(idx))
