"""Entry point for TermTune CLI binary supporting TUI launch & CLI command pipeline."""

import asyncio
import sys
from termtune.app import TermTuneApp
from termtune.ipc import IPCClient


def print_usage() -> None:
    print("""
🎵 TermTune CLI Command Pipeline

Usage:
  termtune                     Launch interactive TUI
  termtune play "<query>"      Play or search track directly from terminal
  termtune pause               Pause active playback
  termtune resume              Resume active playback
  termtune next                Skip to next track in queue
  termtune prev                Go back to previous track
  termtune status              Display current track status and progress
""")


async def run_cli_command(args: list[str]) -> bool:
    """Try executing command via IPC client if server is active. Returns True if handled."""
    cmd_type = args[0].lower()

    if cmd_type in ("--help", "-h", "help"):
        print_usage()
        return True

    if cmd_type == "play":
        query = " ".join(args[1:])
        res = await IPCClient.send_command({"action": "play", "query": query})
        if res:
            if res.get("status") == "ok":
                print(f"🎵 TermTune: {res.get('message')}")
            else:
                print(f"❌ Error: {res.get('message')}")
            return True
        # If server is not running and query provided, we'll launch TUI and search
        return False

    elif cmd_type in ("pause", "stop"):
        res = await IPCClient.send_command({"action": "pause"})
        if res:
            print("⏸ TermTune: Paused playback")
        else:
            print("⚠️ TermTune is not currently running.")
        return True

    elif cmd_type in ("resume", "toggle"):
        res = await IPCClient.send_command({"action": "toggle"})
        if res:
            print(f"⏯ TermTune: {res.get('message', 'Toggled playback')}")
        else:
            print("⚠️ TermTune is not currently running.")
        return True

    elif cmd_type == "next":
        res = await IPCClient.send_command({"action": "next"})
        if res:
            print(f"⏭ TermTune: {res.get('message', 'Next track')}")
        else:
            print("⚠️ TermTune is not currently running.")
        return True

    elif cmd_type in ("prev", "previous"):
        res = await IPCClient.send_command({"action": "prev"})
        if res:
            print(f"⏮ TermTune: {res.get('message', 'Previous track')}")
        else:
            print("⚠️ TermTune is not currently running.")
        return True

    elif cmd_type == "status":
        res = await IPCClient.send_command({"action": "status"})
        if res:
            if res.get("state") != "STOPPED":
                print(f"🎵 Status: {res.get('state')}")
                print(f"   Track:  {res.get('title')}")
                print(f"   Artist: {res.get('artist')}")
                print(f"   Time:   {res.get('position')} / {res.get('duration')}")
            else:
                print("🎵 TermTune Status: STOPPED (No track playing)")
        else:
            print("⚠️ TermTune is not currently running.")
        return True

    return False


def main() -> None:
    args = sys.argv[1:]
    if args:
        # Check if CLI IPC command handled
        handled = asyncio.run(run_cli_command(args))
        if handled:
            sys.exit(0)

    # Launch Textual TUI Application
    app = TermTuneApp()
    app.run()


if __name__ == "__main__":
    main()
