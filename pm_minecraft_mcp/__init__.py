"""pm-minecraft: a Mineflayer Minecraft body plus MCP server.

Runs standalone via the PowerShell scripts, or embedded in a Python process
via :func:`execute_python_main_loop` (and optionally
:func:`execute_node_main_loop` for a two-thread layout).
"""

__version__ = "0.1.0"

from ._runtime import ensure_node_runtime, node_executable, runtime_dir
from .minecraft_mcp import (
    ServerConfig,
    check_prerequisites,
    execute_node_main_loop,
    execute_python_main_loop,
    init_character,
)

__all__ = [
    "ServerConfig",
    "__version__",
    "check_prerequisites",
    "ensure_node_runtime",
    "execute_node_main_loop",
    "execute_python_main_loop",
    "init_character",
    "node_executable",
    "runtime_dir",
]
