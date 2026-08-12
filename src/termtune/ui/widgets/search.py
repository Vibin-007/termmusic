"""Search input widget for TermTune with B&W theme."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Label
from textual.message import Message


class SearchWidget(Vertical):
    """Search input widget with session history and status indicators."""

    class Submitted(Message):
        """Message posted when a search query is submitted."""

        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_recent_searches: list[str] = []

    def compose(self) -> ComposeResult:
        yield Input(
            placeholder="🔎  Search music, artists, albums, or keywords...",
            id="search-input",
        )
        yield Label("Ready to search.", id="search-status")
        yield Label("", id="recent-searches")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search enter key."""
        query = event.value.strip()
        if query:
            if query in self.session_recent_searches:
                self.session_recent_searches.remove(query)
            self.session_recent_searches.insert(0, query)
            self.session_recent_searches = self.session_recent_searches[:5]

            self.update_recent_label()
            self.set_loading_state(query)
            self.post_message(self.Submitted(query))

    def update_recent_label(self) -> None:
        """Update recent search terms string with styled B&W pills."""
        recent_lbl = self.query_one("#recent-searches", Label)
        if self.session_recent_searches:
            pills = "  ".join(f"[bold black on #ffffff] {term} [/]" for term in self.session_recent_searches)
            recent_lbl.update(f"[dim]Recent:[/dim]  {pills}")
        else:
            recent_lbl.update("")

    def set_loading_state(self, query: str) -> None:
        """Set loading message."""
        status_lbl = self.query_one("#search-status", Label)
        status_lbl.update(f"[bold white]⠋ Searching for '{query}'...[/bold white]")

    def set_results_state(self, count: int) -> None:
        """Set completed search results message."""
        status_lbl = self.query_one("#search-status", Label)
        status_lbl.update(f"[bold white]✓ {count} results found[/bold white]")

    def set_error_state(self, msg: str) -> None:
        """Set error message."""
        status_lbl = self.query_one("#search-status", Label)
        status_lbl.update(f"[bold black on #ffffff] ✕ {msg} [/bold black on #ffffff]")

    def focus_input(self) -> None:
        """Focus the input field."""
        self.query_one("#search-input", Input).focus()
