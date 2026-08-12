"""IPC (Inter-Process Communication) server and client for CLI command pipeline (termtune play/next/pause)."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable

from termtune.config import settings

logger = logging.getLogger(__name__)


def get_socket_path() -> Path:
    """Return UNIX socket path for TermTune IPC."""
    sock_dir = settings.config_dir
    sock_dir.mkdir(parents=True, exist_ok=True)
    return sock_dir / "termtune.sock"


class IPCServer:
    """Async UNIX domain socket server running inside TermTune TUI."""

    def __init__(self, command_handler: Callable[[dict[str, Any]], asyncio.Future | Any]):
        self.socket_path = get_socket_path()
        self.command_handler = command_handler
        self.server: asyncio.Server | None = None

    async def start(self) -> None:
        """Start UNIX domain socket server."""
        # Clean up stale socket if it exists
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except OSError:
                pass

        try:
            self.server = await asyncio.start_unix_server(
                self._handle_client, path=str(self.socket_path)
            )
            logger.info(f"IPC Server started on {self.socket_path}")
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle incoming IPC client requests."""
        try:
            data = await reader.read(4096)
            if not data:
                return
            req = json.loads(data.decode("utf-8"))
            if asyncio.iscoroutinefunction(self.command_handler):
                res = await self.command_handler(req)
            else:
                res = self.command_handler(req)

            if res is None:
                res = {"status": "ok"}
            writer.write(json.dumps(res).encode("utf-8"))
            await writer.drain()
        except Exception as e:
            logger.error(f"Error handling IPC client: {e}")
            writer.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def stop(self) -> None:
        """Stop IPC server and clean up socket file."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if self.socket_path.exists():
            try:
                self.socket_path.unlink()
            except OSError:
                pass


class IPCClient:
    """IPC Client used by CLI binary when running termtune play/next/pause from shell."""

    @staticmethod
    async def send_command(cmd: dict[str, Any]) -> dict[str, Any] | None:
        """Send command to running TermTune server via UNIX socket."""
        sock_path = get_socket_path()
        if not sock_path.exists():
            return None

        try:
            reader, writer = await asyncio.open_unix_connection(str(sock_path))
            writer.write(json.dumps(cmd).encode("utf-8"))
            await writer.drain()

            data = await reader.read(4096)
            writer.close()
            await writer.wait_closed()

            if data:
                return json.loads(data.decode("utf-8"))
        except (ConnectionRefusedError, FileNotFoundError, OSError):
            # Server not running or stale socket
            if sock_path.exists():
                try:
                    sock_path.unlink()
                except OSError:
                    pass
        except Exception as e:
            logger.error(f"IPC client error: {e}")

        return None
