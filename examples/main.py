"""Embed pm-minecraft in your own process with two daemon threads.

Starts a Minecraft character body (Node) and its MCP server (Python) as
children of this process. Ctrl-D (EOF) shuts everything down, and so does a
hard kill of this process: the children are attached through stdin pipes and
exit cleanly when the pipe ends. No detached processes, no taskkill.

Install first:
    pip install git+https://github.com/flamingrickpat/pm-minecraft.git

Requires Node.js 20+ on PATH. On first use the package installs its Node
dependency tree once into the current Python environment
(`<venv>/pm-minecraft-runtime/<version>`); later starts are instant.
"""

import threading
from pathlib import Path

from pm_minecraft_mcp import (
    ServerConfig,
    execute_node_main_loop,
    execute_python_main_loop,
    init_character,
)

AGENT_ROOT = Path.home() / "characters" / "Floppa"
ARTIFACT_ROOT = AGENT_ROOT / "artifacts" / "minecraft"

# One-time character workspace initialization (same content as
# scripts/init_character.ps1). Guard it so restarts do not wipe the workspace.
if not (AGENT_ROOT / "AGENTS.md").exists():
    init_character(
        name="Floppa",
        agent_root=AGENT_ROOT,
        artifact_root=ARTIFACT_ROOT,
        minecraft_host="127.0.0.1",
        minecraft_port=12345,
        web_port=3000,
        viewer_port=3007,
        mcp_port=8765,
    )

# All settings in one typed object. Every character needs unique
# web/viewer/mcp ports and a unique username; prerequisites are checked
# before anything spawns and raise immediately (no Minecraft server, wrong
# negotiated version, occupied ports, missing agent home, ...).
config = ServerConfig(
    minecraft_host="127.0.0.1",
    minecraft_port=12345,
    username="Floppa",
    agent_home=AGENT_ROOT,
    artifact_root=ARTIFACT_ROOT,
    web_host="127.0.0.1",
    web_port=3000,
    viewer_port=3007,
    mcp_host="127.0.0.1",
    mcp_port=8765,
    startup_timeout_seconds=90,
    capture_images=True,
    max_skill_characters=50000,
    viewer_scale=1,
    viewer_fov=80,
    view_distance=24,
)

# Thread 1: the Minecraft body (Node process).
body_thread = threading.Thread(
    target=execute_node_main_loop,
    args=(config,),
    daemon=True,
)
# Thread 2: the MCP server (Python), connecting to the external body.
mcp_thread = threading.Thread(
    target=execute_python_main_loop,
    args=(config,),
    kwargs={"manage_body": False},
    daemon=True,
)
body_thread.start()
mcp_thread.start()

print(f"Floppa is starting: body http://127.0.0.1:{config.web_port}, MCP {config.mcp_url}")
print("Press Ctrl-D to stop everything.")
try:
    while True:
        input()
except (EOFError, KeyboardInterrupt):
    # Daemon threads die with the process; the OS closes the stdin pipes and
    # both children (body and any running skill) shut down cleanly.
    print("shutting down")
