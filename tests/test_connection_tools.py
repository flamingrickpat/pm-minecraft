import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastmcp import Client

from mcmcp import server


@pytest.mark.parametrize("enabled", [True, False])
def test_connection_tool_visibility_and_offline_dispatch(tmp_path, monkeypatch, enabled):
    runtime = Mock()
    runtime.body = object()
    runtime.stop_body.side_effect = lambda: setattr(runtime, "body", None)
    runtime.start_body.side_effect = lambda: setattr(runtime, "body", object())
    monkeypatch.setattr(server, "MinecraftRuntime", lambda config: runtime)
    configuration = SimpleNamespace(agent_home=tmp_path, test_mode=False,
                                    inspector_enabled=False, connection_tools=enabled)

    async def exercise():
        async with Client(server.build_server(configuration)) as client:
            tools = {t.name: t for t in await client.list_tools()}
            names = {"minecraft_connect", "minecraft_disconnect"}
            assert names.intersection(tools) == (names if enabled else set())
            if enabled:
                assert all(not tools[name].inputSchema["properties"] for name in names)
                assert (await client.call_tool("minecraft_disconnect")).structured_content["ok"]
                for name in ("minecraft_info", "minecraft_disconnect", "minecraft_screenshot"):
                    reply = await client.call_tool(name)
                    assert reply.structured_content["message"] == "not connected, pls connect"
                assert (await client.call_tool("minecraft_connect")).structured_content["ok"]
                assert runtime.body is not None
    asyncio.run(exercise())
