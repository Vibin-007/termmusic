"""Footer controls & keybindings guide widget (Monochrome B&W Theme)."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label


class ControlsWidget(Horizontal):
    """Footer bar displaying keybindings with B&W keycap badges."""

    def compose(self) -> ComposeResult:
        shortcuts = (
            "[bold black on #ffffff] S [/] Search  "
            "[bold black on #ffffff] ENTER [/] Play  "
            "[bold black on #ffffff] SPACE [/] Pause  "
            "[bold black on #ffffff] N [/] Next  "
            "[bold black on #ffffff] B [/] Prev  "
            "[bold black on #ffffff] +/- [/] Vol  "
            "[bold black on #ffffff] A [/] Add Queue  "
            "[bold black on #ffffff] Q [/] Quit"
        )
        yield Label(shortcuts, id="controls-text")
