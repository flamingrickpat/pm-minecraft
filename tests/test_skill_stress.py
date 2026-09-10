"""Stress real MCP tools and child processes with short skill deadlines."""

import asyncio
import inspect
import random
import re
import subprocess
import time
from pathlib import Path

import pytest
from fastmcp import Client, FastMCP

from mcmcp import runtime as runtime_module
from mcmcp.config import load_configuration
from mcmcp.runtime import MinecraftRuntime
from mcmcp.server import COMMAND_BUDGETS, CommandGate, _tool_output_schema, _wrap_tool
from mcmcp.tools import MinecraftTools

pytestmark = pytest.mark.infrastructure


@pytest.fixture
def skill_mcp(live_test, monkeypatch):
    """Use the real body and tools. Change only the skill timeout."""
    monkeypatch.setattr(runtime_module, "SKILL_SECONDS", 4)
    monkeypatch.setitem(COMMAND_BUDGETS, "minecraft_execute_typescript", 4)
    live_test.release_setup_player()
    configuration = load_configuration()
    runtime = MinecraftRuntime(configuration)
    try:
        live_test.wait_for("the skill test player", runtime.body.state, lambda state: state.spawned)
        tools = MinecraftTools(runtime)
        gate = CommandGate()
        mcp = FastMCP("skill-stress")
        for name, method in inspect.getmembers(tools, inspect.ismethod):
            if name.startswith("minecraft_"):
                mcp.tool(output_schema=_tool_output_schema(method))(
                    _wrap_tool(method, configuration.agent_home / "frames", gate)
                )
        yield mcp, runtime, gate, configuration
    finally:
        runtime.stop_body()


LOOPS = [
    ("top_timeout", 'while (true) {} export async function run() {}', False),
    ("async_timeout", 'export async function run() { await Promise.resolve(); while (true) {} }', False),
    ("top_stop", 'export async function run() { while (true) {} }', True),
    ("pending_stop", 'export async function run() { await new Promise(() => {}); }', True),
]


@pytest.mark.parametrize("name,source,stop", LOOPS, ids=[case[0] for case in LOOPS])
def test_random_tool_bursts_during_endless_skill(skill_mcp, name, source, stop):
    mcp, runtime, gate, configuration = skill_mcp
    draft = configuration.agent_home / "drafts" / "stress-loop.ts"
    recovery = configuration.agent_home / "drafts" / "stress-recovery.ts"
    draft.write_text(source, encoding="utf-8")
    recovery.write_text('''export async function run(api) {
      const state = await api.observe();
      const center = state.camera.feet_position;
      const blocks = api.findBlocks({center, names: ["grass_block"], horizontal: 1, up: 1, down: 2, limit: 4});
      const path = api.findPath({target: center, limit: 4, timeoutMs: 100});
      console.log("recovered", blocks.blocks.length, path.state);
    }''', encoding="utf-8")
    log_path = Path.home() / ".pm" / "pm-minecraft" / "body.log"

    async def exercise():
        async with Client(mcp) as client:
            # Prepare the browser before the short deadline starts.
            await client.call_tool("minecraft_screenshot", {})
            before = runtime.body.state()
            log_offset = log_path.stat().st_size
            started = time.monotonic()
            active = asyncio.create_task(client.call_tool("minecraft_execute_typescript", {
                "path": "drafts/stress-loop.ts", "postcondition": {},
            }))
            try:
                while gate.running is None:
                    assert time.monotonic() - started < 2
                    await asyncio.sleep(0.01)

                calls = [
                    ("minecraft_execute_typescript", {"path": "drafts/stress-loop.ts", "postcondition": {}}),
                    ("minecraft_observe", {"include_image": False}),
                    ("minecraft_count_inventory", {"pattern": "*"}),
                    ("minecraft_relative", {"forward": 1}),
                    ("minecraft_rotate", {"yaw_degrees": 45, "pitch_degrees": 0}),
                    ("minecraft_remember", {"kind": "journal", "markdown": "This call must be rejected."}),
                ]
                burst = calls * 4
                random.Random(name).shuffle(burst)
                results = await asyncio.wait_for(asyncio.gather(*[
                    client.call_tool(tool, args, raise_on_error=False) for tool, args in burst
                ]), timeout=3)
                for result in results:
                    assert not result.is_error, result
                    assert result.structured_content["reason"] == "concurrent_tool_call"

                reads = await asyncio.wait_for(asyncio.gather(
                    client.call_tool("minecraft_info", {}),
                    client.call_tool("minecraft_screenshot", {}),
                    client.call_tool("minecraft_info", {}),
                ), timeout=3)
                assert all(result.structured_content["ok"] for result in reads)
                assert any(part.type == "image" for part in reads[1].content)

                # Invalid calls must not release another call's gate or crash MCP.
                for tool, args in [("minecraft_no_such_tool", {}), ("minecraft_rotate", {"yaw_degrees": "oops"})]:
                    invalid = await client.call_tool(tool, args, raise_on_error=False)
                    assert invalid.is_error
                if stop:
                    stopped = await asyncio.gather(*[
                        client.call_tool("minecraft_stop", {"scope": "both"}) for _ in range(5)
                    ])
                    assert all(result.structured_content["ok"] for result in stopped)
                result = await asyncio.wait_for(active, timeout=8)
                assert result.structured_content["reason"] == ("stopped" if stop else "timeout")
                assert gate.running is None
                assert time.monotonic() - started < 10

                with log_path.open("rb") as file:
                    file.seek(log_offset)
                    log = file.read().decode("utf-8")
                pids = re.findall(r"skill process started pid=(\d+)", log)
                assert len(pids) == 1, log
                assert f"skill process exited pid={pids[0]}" in log
                subprocess.run([str(configuration.node), "-e", '''
                  try { process.kill(Number(process.argv[1]), 0); process.exit(1); }
                  catch (error) { if (error.code !== "ESRCH") throw error; }
                ''', pids[0]], check=True, timeout=5)
                assert runtime.body.alive
                after = runtime.body.state()
                assert after.spawned
                assert after.camera.feet_position == before.camera.feet_position
                assert after.inventory == before.inventory

                recovered = await client.call_tool("minecraft_execute_typescript", {
                    "path": "drafts/stress-recovery.ts", "postcondition": {},
                })
                assert recovered.structured_content["ok"], recovered.structured_content
                assert "recovered" in recovered.structured_content["stdout_tail"]
                assert gate.running is None
            finally:
                if not active.done():
                    await client.call_tool("minecraft_stop", {"scope": "both"})
                    await asyncio.gather(active, return_exceptions=True)

    try:
        asyncio.run(exercise())
    finally:
        draft.unlink(missing_ok=True)
        recovery.unlink(missing_ok=True)
