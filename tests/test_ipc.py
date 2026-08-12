"""Unit tests for TermTune IPC server and client command pipeline."""

import asyncio
from termtune.ipc import IPCClient, IPCServer


def test_ipc_command_pipeline(tmp_path, monkeypatch):
    async def _async_test():
        # Override socket path to tmp_path
        sock_file = tmp_path / "termtune_test.sock"
        monkeypatch.setattr("termtune.ipc.get_socket_path", lambda: sock_file)

        async def mock_handler(req):
            action = req.get("action")
            if action == "play":
                return {"status": "ok", "message": f"Playing {req.get('query')}"}
            elif action == "next":
                return {"status": "ok", "message": "Next track"}
            elif action == "status":
                return {"status": "ok", "state": "PLAYING", "title": "Test Song"}
            return {"status": "error", "message": "Unknown"}

        server = IPCServer(mock_handler)
        await server.start()

        # Test send command play
        res_play = await IPCClient.send_command({"action": "play", "query": "lo-fi hip hop"})
        assert res_play is not None
        assert res_play["status"] == "ok"
        assert "lo-fi hip hop" in res_play["message"]

        # Test send command next
        res_next = await IPCClient.send_command({"action": "next"})
        assert res_next is not None
        assert res_next["status"] == "ok"
        assert res_next["message"] == "Next track"

        # Test status
        res_status = await IPCClient.send_command({"action": "status"})
        assert res_status is not None
        assert res_status["state"] == "PLAYING"

        # Stop server
        await server.stop()
        assert not sock_file.exists()

    asyncio.run(_async_test())
