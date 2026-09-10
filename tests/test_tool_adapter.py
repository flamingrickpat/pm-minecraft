import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Event

import pytest
from fastmcp import Client, FastMCP

from mcmcp.models import DistanceResult, ToolOutcome, Vec3f
from mcmcp.server import CommandGate, _tool_output_schema, _wrap_tool


def test_gate_rejects_overlap_and_allows_control_tools():
    gate = CommandGate()
    entered, release = Event(), Event()

    def minecraft_walk_to_exact():
        entered.set()
        assert release.wait(5)
        return ToolOutcome(ok=True)

    def other():
        return ToolOutcome(ok=True)

    with ThreadPoolExecutor() as pool:
        running = pool.submit(gate.call, minecraft_walk_to_exact)
        try:
            assert entered.wait(5)
            rejected = gate.call(other)
            assert rejected.reason == "concurrent_tool_call"
            assert "minecraft_walk_to_exact" in rejected.message
            assert "seconds" in rejected.message
            for name in ("info", "status", "screenshot", "stop"):
                other.__name__ = f"minecraft_{name}"
                assert gate.call(other).ok
            other.__name__ = "other"
            assert gate.call(other).ok is False
        finally:
            release.set()
        assert running.result().ok
    assert gate.call(other).ok


def test_gate_releases_after_exception():
    gate = CommandGate()

    def broken():
        raise ValueError("broken")

    with pytest.raises(ValueError, match="broken"):
        gate.call(broken)
    assert gate.running is None


def test_mcp_rounding_and_busy_schema(tmp_path):
    gate = CommandGate()

    def minecraft_distance() -> DistanceResult:
        return DistanceResult(ok=True, distance=1.23456, manhattan=2.34567,
                              dx=-0.12345, dy=0.0, dz=1.23456)

    mcp = FastMCP("adapter-test")
    mcp.tool(output_schema=_tool_output_schema(minecraft_distance))(_wrap_tool(minecraft_distance, tmp_path, gate))

    async def check():
        async with Client(mcp) as client:
            result = await client.call_tool("minecraft_distance", {})
            assert result.structured_content["distance"] == 1.23
            assert result.structured_content["dx"] == -0.12
            assert "1.23456" not in result.content[0].text
            assert json.loads(result.content[0].text) == result.structured_content
            gate.running = ("minecraft_build", 0.0)
            result = await client.call_tool("minecraft_distance", {})
            assert result.structured_content["reason"] == "concurrent_tool_call"
            assert json.loads(result.content[0].text) == result.structured_content

    asyncio.run(check())


def test_mcp_text_preserves_nested_values_and_datetime(tmp_path):
    class NestedResult(ToolOutcome):
        position: Vec3f
        inventory: list[dict[str, int | str]]
        timestamp: datetime

    original = NestedResult(
        ok=True,
        position=Vec3f(x=120.5, y=65, z=-30.5),
        inventory=[{"name": "raw_iron", "count": 8}],
        timestamp=datetime(2026, 9, 9, tzinfo=timezone.utc),
        message="Collected iron — ready to smelt.",
    )

    def nested_result():
        return original

    mcp = FastMCP("nested-adapter-test")
    mcp.tool()(_wrap_tool(nested_result, tmp_path, CommandGate()))

    async def check():
        async with Client(mcp) as client:
            result = await client.call_tool("nested_result", {})
            text_data = json.loads(result.content[0].text)
            assert text_data == result.structured_content == original.model_dump(mode="json")
            assert text_data["position"]["y"] == 65
            assert text_data["inventory"][0]["count"] == 8
            assert text_data["timestamp"] == "2026-09-09T00:00:00Z"
            assert "—" in result.content[0].text

    asyncio.run(check())


def test_nested_rounding_preserves_other_values():
    from mcmcp.server import _round_floats

    assert _round_floats({"camera": {"x": -5.35147}, "items": [1.2345, 2, True, "1.2345"]}) == {
        "camera": {"x": -5.35}, "items": [1.23, 2, True, "1.2345"]
    }
