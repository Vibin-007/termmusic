"""UI widgets package for TermTune."""

from termtune.ui.widgets.controls import ControlsWidget
from termtune.ui.widgets.now_playing import NowPlayingWidget
from termtune.ui.widgets.queue import QueueWidget
from termtune.ui.widgets.results import SearchResultsWidget
from termtune.ui.widgets.search import SearchWidget

__all__ = [
    "SearchWidget",
    "SearchResultsWidget",
    "NowPlayingWidget",
    "QueueWidget",
    "ControlsWidget",
]
