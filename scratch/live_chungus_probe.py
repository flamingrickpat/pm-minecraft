"""Record the real Chungus placement and cave-navigation failures through MCP.

Run after starting the production MCP with C:\\Temp\\Grog\\.env:
    uv run python scratch/live_chungus_probe.py
"""

import asyncio
import json
import time

from fastmcp import Client


URL = "http://127.0.0.1:8765/mcp"


async def call(client, name, arguments):
    started = time.monotonic()
    result = await client.call_tool_mcp(name, arguments)
    return {
        "tool": name,
        "arguments": arguments,
        "seconds": round(time.monotonic() - started, 3),
        "is_error": result.isError,
        "result": result.structuredContent,
    }


async def main():
    async with Client(URL) as client:
        results = []
        results.append(await call(client, "minecraft_observe", {"include_image": False}))
        results.append(await call(client, "minecraft_walk_to_surface", {"x": -9, "z": 25}))
        results.append(await call(client, "minecraft_walk_to_visible", {"x": 2, "y": 65, "z": 25}))
        results.append(await call(client, "minecraft_walk_to_visible", {"x": 4, "y": 64, "z": 27}))
        results.append(await call(client, "minecraft_find_path", {"x": 2, "y": 67, "z": 25}))
        print(json.dumps(results, indent=2))


asyncio.run(main())
