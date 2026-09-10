"""Publish `MinecraftTools` through one FastMCP server.

Tool code errors pass to FastMCP without a catch in this module.
FastMCP validates external arguments before it calls a tool method.
The adapter converts one result model into structured and text content.
"""

from __future__ import annotations

import base64
from contextlib import asynccontextmanager
import functools
import inspect
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Literal, get_type_hints

from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from mcp.types import ImageContent, TextContent
from pydantic import TypeAdapter
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .config import Configuration, load_configuration
from .inspector import start_inspector
from . import constants
from .log_setup import setup_logging
from .models import ImageRef, ToolOutcome
from .runtime import MinecraftRuntime
from .startup import initialize_agent_home
from .tools import MinecraftTools


PATH = "/mcp"
log = logging.getLogger("mcmcp.tools")

CONCURRENT_TOOLS = {"minecraft_screenshot", "minecraft_info", "minecraft_status", "minecraft_stop"}
COMMAND_BUDGETS = {
    "minecraft_walk_to_visible": constants.VISIBLE_WALK_SECONDS,
    "minecraft_walk_to_surface": constants.SURFACE_WALK_SECONDS,
    "minecraft_walk_to_exact": constants.EXACT_WALK_SECONDS,
    "minecraft_find_path": constants.PATH_SEARCH_SECONDS,
    "minecraft_execute_typescript": constants.SKILL_SECONDS,
}
MCP_REQUEST_GRACE_SECONDS = 15


class ConcurrentToolCallResult(ToolOutcome):
    ok: Literal[False] = False
    reason: Literal["concurrent_tool_call"] = "concurrent_tool_call"


class CommandGate:
    def __init__(self) -> None:
        self.mutex = threading.Lock()
        self.running: tuple[str, float] | None = None

    def call(self, method: Any, *args: Any, **kwargs: Any) -> Any:
        if method.__name__ in CONCURRENT_TOOLS:
            return method(*args, **kwargs)
        # Hold the mutex only while checking/updating ownership. Never queue commands.
        with self.mutex:
            if self.running is not None:
                name, started = self.running
                budget = COMMAND_BUDGETS.get(name)
                timing = "no fixed overall timeout"
                if budget is not None:
                    remaining = max(0, budget - (time.monotonic() - started))
                    timing = f"{remaining:.{constants.FLOAT_PRECISION}f} seconds until its action budget expires"
                return ConcurrentToolCallResult(
                    message=f"Command {name} is still running, {timing}. You can only call info, status, screenshot and stop.",
                )
            self.running = (method.__name__, time.monotonic())
        try:
            return method(*args, **kwargs)
        finally:
            with self.mutex:
                self.running = None


def _round_floats(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, constants.FLOAT_PRECISION)
    if isinstance(value, dict):
        return {key: _round_floats(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_round_floats(item) for item in value]
    return value


def _serialize_result(result: ToolOutcome) -> tuple[dict[str, Any], str]:
    """Serialize once for matching structured and JSON text content."""
    data = _round_floats(result.model_dump(mode="json"))
    return data, json.dumps(data, ensure_ascii=False, indent=2)


def _wrap_tool(method: Any, frame_directory: Path, gate: CommandGate, runtime: MinecraftRuntime | None = None) -> Any:
    """Adapt one typed method result to FastMCP content."""

    @functools.wraps(method)
    def action(*args: Any, **kwargs: Any) -> Any:
        if runtime is None or method.__name__ in CONCURRENT_TOOLS:
            return method(*args, **kwargs)
        return runtime.call_with_warnings(method, *args, **kwargs)

    @functools.wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> ToolResult:
        started = time.monotonic()
        try:
            result = gate.call(action, *args, **kwargs)
        except Exception:
            log.exception("%s args=%s failed after %.0f ms", method.__name__, kwargs, (time.monotonic() - started) * 1000)
            raise
        log.info(
            "%s args=%s -> %s in %.0f ms",
            method.__name__,
            kwargs,
            f"ok={getattr(result, 'ok', None)} reason={getattr(result, 'reason', None)}",
            (time.monotonic() - started) * 1000,
        )
        if log.isEnabledFor(logging.DEBUG):
            log.debug("%s result=%r", method.__name__, result)
        data, text = _serialize_result(result)
        content: list[Any] = [TextContent(type="text", text=text)]
        image = getattr(result, "image", None)
        if isinstance(image, ImageRef):
            pixels = (frame_directory / f"{image.frame_id}.png").read_bytes()
            content.append(
                ImageContent(
                    type="image",
                    data=base64.b64encode(pixels).decode("ascii"),
                    mimeType="image/png",
                )
            )
        return ToolResult(
            content=content,
            structured_content=data,
            meta={"mode": "live", "tool": method.__name__},
        )

    wrapper.__annotations__ = get_type_hints(method)
    return wrapper


def _tool_output_schema(method: Any) -> dict:
    schema = TypeAdapter(get_type_hints(method)["return"] | ConcurrentToolCallResult).json_schema()
    return {"type": "object", **schema}


def _request_timeout_ms() -> int:
    """Return one client timeout that covers every server time limit."""
    maximum_seconds = max(
        value
        for name, value in constants.DOC_CONSTANTS.items()
        if name.endswith("_SECONDS") and isinstance(value, (int, float))
    )
    return int((maximum_seconds + MCP_REQUEST_GRACE_SECONDS) * 1000)


def update_agent_mcp_configuration(configuration: Configuration) -> Path:
    """Keep the character repository connected to this MCP instance."""
    path = configuration.agent_home / ".mcp.json"
    document = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    minecraft = document.setdefault("mcpServers", {}).setdefault("minecraft", {})
    minecraft["url"] = f"http://127.0.0.1:{configuration.mcp_port}{PATH}"
    minecraft["requestTimeoutMs"] = _request_timeout_ms()
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path


def build_server(configuration: Configuration) -> FastMCP:
    """Create the runtime, tool set, and MCP transport adapter."""
    setup_logging()
    log.info("starting mcp, test_mode=%s", configuration.test_mode)
    runtime = MinecraftRuntime(configuration)
    tools = MinecraftTools(runtime)
    @asynccontextmanager
    async def lifespan(_: FastMCP):
        if configuration.inspector_enabled:
            url = str(start_inspector(configuration)).replace("0.0.0.0", "127.0.0.1")
            print(f"Manual MCP inspector: {url}")
        yield

    mcp = FastMCP(
        name="minecraft-v2",
        instructions=(
            "Control one real survival player. Read each tool description. "
            "Fixed limits protect the survival game loop."
        ),
        lifespan=lifespan,
    )
    frame_directory = configuration.agent_home / "frames"
    gate = CommandGate()
    for name, method in inspect.getmembers(tools, inspect.ismethod):
        if name.startswith("minecraft_"):
            mcp.tool(output_schema=_tool_output_schema(method))(_wrap_tool(method, frame_directory, gate, runtime))
    if configuration.test_mode:
        @mcp.custom_route("/test/body/start", methods=["POST"], include_in_schema=False)
        async def start_test_body(request: Request) -> Response:
            runtime.start_body()
            return JSONResponse({"ok": True})

        @mcp.custom_route("/test/body/stop", methods=["POST"], include_in_schema=False)
        async def stop_test_body(request: Request) -> Response:
            runtime.stop_body()
            return JSONResponse({"ok": True})

        @mcp.custom_route("/test/reset", methods=["POST"], include_in_schema=False)
        async def reset_test_state(request: Request) -> Response:
            runtime.reset_test_state()
            return JSONResponse({"ok": True})

        @mcp.custom_route("/test/entity/interrupted", methods=["POST"], include_in_schema=False)
        async def mark_test_entity_interrupted(request: Request) -> Response:
            value = await request.json()
            runtime.mark_test_entity_interrupted(int(value["entity_id"]))
            return JSONResponse({"ok": True})
    return mcp


def main(config_file: Path | None = None) -> None:
    """Read the local configuration and start the MCP server."""
    configuration = load_configuration(config_file)
    initialize_agent_home(configuration)
    mcp_config = update_agent_mcp_configuration(configuration)
    print(f"Updated MCP client configuration: {mcp_config}")
    mcp = build_server(configuration)
    mcp.run(
        transport="streamable-http",
        host=configuration.mcp_host,
        port=configuration.mcp_port,
        path=PATH,
        show_banner=True,
    )


if __name__ == "__main__":
    main()
