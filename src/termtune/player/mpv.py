"""MPV subprocess IPC adapter for cross-platform audio streaming with real-time property tracking."""

import asyncio
from enum import Enum
import json
import logging
import os
import sys
from typing import Any, Callable

from termtune.platform import get_platform_adapter
from termtune.utils.errors import MPVNotFoundError, PlaybackError

logger = logging.getLogger(__name__)


class PlaybackState(str, Enum):
    """Explicit playback state machine states."""

    IDLE = "IDLE"
    LOADING = "LOADING"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class MPVAdapter:
    """Controls background MPV subprocess via JSON IPC socket."""

    def __init__(self):
        self.platform = get_platform_adapter()
        self.mpv_path = self.platform.get_mpv_path()
        self.ipc_socket_path = self.platform.get_ipc_socket_path()

        self._process: asyncio.subprocess.Process | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._state: PlaybackState = PlaybackState.IDLE

        self.position: float = 0.0
        self.duration: float = 0.0
        self.volume: int = 80
        self.muted: bool = False

        self._on_end_file_callback: Callable[[], None] | None = None
        self._on_state_change_callback: Callable[[PlaybackState], None] | None = None
        self._monitor_task: asyncio.Task | None = None
        self._request_id = 0
        self._pending_requests: dict[int, str] = {}

    @property
    def state(self) -> PlaybackState:
        return self._state

    def set_on_end_file(self, callback: Callable[[], None]) -> None:
        """Register callback invoked when track playback finishes."""
        self._on_end_file_callback = callback

    def set_on_state_change(self, callback: Callable[[PlaybackState], None]) -> None:
        """Register callback invoked when playback state changes."""
        self._on_state_change_callback = callback

    def _set_state(self, state: PlaybackState) -> None:
        if self._state != state:
            self._state = state
            logger.debug(f"MPV State -> {state.value}")
            if self._on_state_change_callback:
                try:
                    self._on_state_change_callback(state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}")

    async def ensure_started(self) -> None:
        """Ensure MPV subprocess is running and connected via IPC."""
        if not self.mpv_path:
            raise MPVNotFoundError(self.platform.get_platform_name())

        if self._process and self._process.returncode is None and self._writer:
            return

        # Remove old socket file if exists on Unix
        if sys.platform != "win32" and os.path.exists(self.ipc_socket_path):
            try:
                os.unlink(self.ipc_socket_path)
            except OSError:
                pass

        cmd = [
            self.mpv_path,
            "--no-video",
            "--idle=yes",
            f"--input-ipc-server={self.ipc_socket_path}",
            "--input-terminal=no",
            "--really-quiet",
        ]

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except Exception as e:
            logger.error(f"Failed to start MPV subprocess: {e}")
            self._set_state(PlaybackState.ERROR)
            raise PlaybackError("Failed to launch MPV audio engine.")

        # Connect to IPC socket with retry loop
        connected = False
        for _ in range(30):
            await asyncio.sleep(0.1)
            try:
                if sys.platform == "win32":
                    reader, writer = await asyncio.open_connection(
                        path=self.ipc_socket_path
                    )
                else:
                    reader, writer = await asyncio.open_unix_connection(self.ipc_socket_path)
                self._reader = reader
                self._writer = writer
                connected = True
                break
            except Exception:
                continue

        if not connected:
            self._set_state(PlaybackState.ERROR)
            raise PlaybackError("Could not establish IPC connection to MPV process.")

        # Register property observers in MPV so it streams updates automatically
        await self._send_command(["observe_property", 1, "time-pos"])
        await self._send_command(["observe_property", 2, "duration"])
        await self._send_command(["observe_property", 3, "pause"])

        # Start background loop to monitor MPV status
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def _send_command(self, cmd: list[Any]) -> Any:
        """Send JSON IPC command to MPV process."""
        if not self._writer or self._writer.is_closing():
            await self.ensure_started()

        if not self._writer:
            return None

        self._request_id += 1
        req_id = self._request_id
        if len(cmd) > 1 and cmd[0] == "get_property":
            self._pending_requests[req_id] = cmd[1]

        msg = json.dumps({"command": cmd, "request_id": req_id}) + "\n"
        try:
            self._writer.write(msg.encode("utf-8"))
            await self._writer.drain()
        except Exception as e:
            logger.error(f"IPC send error: {e}")
            return None

    async def play_url(self, url: str) -> None:
        """Load and start playing stream URL in MPV."""
        self._set_state(PlaybackState.LOADING)
        self.position = 0.0
        self.duration = 0.0

        try:
            await self.ensure_started()
            await self._send_command(["loadfile", url, "replace"])
            await self._send_command(["set_property", "pause", False])
            await self._send_command(["set_property", "volume", self.volume])
            self._set_state(PlaybackState.PLAYING)
        except Exception as e:
            logger.error(f"Error loading URL in MPV: {e}")
            self._set_state(PlaybackState.ERROR)
            raise PlaybackError(f"Playback error: {e}")

    async def pause(self) -> None:
        """Pause playback."""
        if self._state == PlaybackState.PLAYING:
            await self._send_command(["set_property", "pause", True])
            self._set_state(PlaybackState.PAUSED)

    async def resume(self) -> None:
        """Resume playback."""
        if self._state in (PlaybackState.PAUSED, PlaybackState.STOPPED):
            await self._send_command(["set_property", "pause", False])
            self._set_state(PlaybackState.PLAYING)

    async def toggle_play_pause(self) -> PlaybackState:
        """Toggle between play and pause states."""
        if self._state == PlaybackState.PLAYING:
            await self.pause()
        elif self._state in (PlaybackState.PAUSED, PlaybackState.STOPPED):
            await self.resume()
        return self._state

    async def stop(self) -> None:
        """Stop playback."""
        await self._send_command(["stop"])
        self.position = 0.0
        self._set_state(PlaybackState.STOPPED)

    async def seek(self, seconds: float, absolute: bool = False) -> None:
        """Seek forward or backward."""
        mode = "absolute" if absolute else "relative"
        await self._send_command(["seek", seconds, mode])

    async def set_volume(self, volume: int) -> None:
        """Set volume (0 to 100)."""
        self.volume = max(0, min(100, volume))
        if not self.muted:
            await self._send_command(["set_property", "volume", self.volume])

    async def set_mute(self, muted: bool) -> None:
        """Set mute state."""
        self.muted = muted
        target_vol = 0 if self.muted else self.volume
        await self._send_command(["set_property", "volume", target_vol])

    async def toggle_mute(self) -> bool:
        """Toggle mute state."""
        await self.set_mute(not self.muted)
        return self.muted

    async def _monitor_loop(self) -> None:
        """Background monitoring loop reading property events from IPC socket."""
        was_playing = False
        while True:
            if not self._reader:
                await asyncio.sleep(0.5)
                continue

            try:
                line = await asyncio.wait_for(self._reader.readline(), timeout=0.3)
                if not line:
                    await asyncio.sleep(0.1)
                    continue

                data = json.loads(line.decode("utf-8").strip())
                event = data.get("event")

                # Handle property change observer events from MPV
                if event == "property-change":
                    prop_name = data.get("name")
                    prop_val = data.get("data")
                    if prop_name == "time-pos" and prop_val is not None:
                        try:
                            self.position = float(prop_val)
                        except (ValueError, TypeError):
                            pass
                    elif prop_name == "duration" and prop_val is not None:
                        try:
                            self.duration = float(prop_val)
                        except (ValueError, TypeError):
                            pass
                    elif prop_name == "pause" and prop_val is not None:
                        if prop_val and self._state == PlaybackState.PLAYING:
                            self._set_state(PlaybackState.PAUSED)
                        elif not prop_val and self._state == PlaybackState.PAUSED:
                            self._set_state(PlaybackState.PLAYING)

                # Handle get_property response data
                req_id = data.get("request_id")
                if req_id in self._pending_requests:
                    prop_name = self._pending_requests.pop(req_id)
                    prop_val = data.get("data")
                    if prop_name == "time-pos" and prop_val is not None:
                        try:
                            self.position = float(prop_val)
                        except (ValueError, TypeError):
                            pass
                    elif prop_name == "duration" and prop_val is not None:
                        try:
                            self.duration = float(prop_val)
                        except (ValueError, TypeError):
                            pass

                if event == "end-file":
                    reason = data.get("reason")
                    logger.debug(f"MPV end-file event, reason={reason}")
                    if reason in ("eof", "stop") and was_playing:
                        was_playing = False
                        self._set_state(PlaybackState.STOPPED)
                        if self._on_end_file_callback:
                            try:
                                self._on_end_file_callback()
                            except Exception as e:
                                logger.error(f"End file callback exception: {e}")

            except asyncio.TimeoutError:
                # Query time-pos and duration periodically as fallback
                if self._state in (PlaybackState.PLAYING, PlaybackState.PAUSED):
                    await self._send_command(["get_property", "time-pos"])
                    await self._send_command(["get_property", "duration"])
                    if self._state == PlaybackState.PLAYING:
                        was_playing = True
            except Exception as e:
                logger.debug(f"MPV monitor iteration exception: {e}")
                await asyncio.sleep(0.3)

    async def close(self) -> None:
        """Cleanly terminate MPV subprocess and close IPC socket."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()

        if self._writer and not self._writer.is_closing():
            try:
                await self._send_command(["quit"])
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass

        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await self._process.wait()
            except Exception:
                pass

        self._set_state(PlaybackState.STOPPED)
