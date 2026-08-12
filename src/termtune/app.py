"""TermTune Application entry point and Textual App."""

import argparse
import asyncio
import logging
from pathlib import Path
import sys
from textual.app import App

from termtune.config import settings
from termtune.player.controller import PlayerController
from termtune.providers.youtube import YouTubeProvider
from termtune.ui.screens import MainScreen
from termtune.utils.formatting import format_time

__version__ = "0.1.0"


def setup_logging(debug: bool = False) -> None:
    """Configure logging for TermTune."""
    if debug:
        settings.debug = True

    if settings.debug:
        log_dir = Path.home() / ".termtune"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "termtune.log"

        logging.basicConfig(
            filename=str(log_file),
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        logging.info("TermTune started in debug mode.")
    else:
        logging.basicConfig(level=logging.CRITICAL)


class TermTuneApp(App):
    """Textual App for TermTune."""

    TITLE = "TermTune"
    CSS_PATH = "ui/styles.tcss"

    def __init__(self, controller: PlayerController | None = None, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller or PlayerController()

    def on_mount(self) -> None:
        """Mount main screen."""
        self.push_screen(MainScreen(self.controller))

    async def action_quit(self) -> None:
        """Gracefully shutdown player and exit."""
        await self.controller.shutdown()
        settings.save()
        self.exit()


async def cli_search(query: str) -> None:
    """Execute quick search from CLI and print text results to stdout."""
    print(f"🔎 Searching for: {query}...\n")
    provider = YouTubeProvider()
    try:
        results = await provider.search(query)
        if not results:
            print("✕ No results found.")
            return

        print(f"✓ {len(results)} results found:\n")
        for idx, track in enumerate(results, 1):
            dur = format_time(track.duration)
            print(f"{idx:2d}. {track.title}")
            print(f"    {track.artist}  ({dur})  [{track.webpage_url}]")
            print()
    except Exception as e:
        print(f"✕ Search failed: {e}")


def main() -> None:
    """CLI entry point for termtune binary command."""
    parser = argparse.ArgumentParser(
        prog="termtune",
        description="TermTune - Polished Cross-Platform Terminal Music Player",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"TermTune {__version__}"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging"
    )

    subparsers = parser.add_subparsers(dest="command")
    search_parser = subparsers.add_parser("search", help="Search music from CLI")
    search_parser.add_argument("query", type=str, help="Search query string")

    args = parser.parse_args()

    setup_logging(args.debug)

    if args.command == "search":
        asyncio.run(cli_search(args.query))
        return

    # Run TUI application
    controller = PlayerController()
    app = TermTuneApp(controller=controller)

    try:
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.run(controller.shutdown())
        settings.save()


if __name__ == "__main__":
    main()
