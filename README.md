# pm-minecraft

A self-contained Minecraft survival body for MCP clients.

It runs Mineflayer, Prismarine Viewer, and a Streamable HTTP MCP server. A
coding agent uses MCP tools to control one real survival player. The project
does not include an agent, model, or cognitive runtime.

Huge thanks to [Voyager](https://github.com/MineDojo/Voyager) and
[Discovery](https://github.com/Mega-Gorilla/Discovery) :3

The main difference to these projects is: **bot is forced to do real, human-like survival with no cheats or x-ray**

This project is part of an effort to make an AI companion that can play
Minecraft with you. It also works as a standalone MCP server.

## Setup

Requirements: PowerShell on Windows or Bash on Linux, Python 3.12 or newer,
Node.js 20 or newer, Java 17 or newer, and a reachable Minecraft Java 1.19.4
survival server.

```powershell
Set-Location C:\source\pm\pm-minecraft-v2
.\setup.ps1
```

On Linux, run:

```bash
./setup.sh
```

## Minecraft

The current development setup uses the test world and its checkpoint mod. For
a manual world, create a Java 1.19.4 Fabric world with cheats enabled. Open
the world to LAN, then set `MINECRAFT_HOST` and `MINECRAFT_PORT` in `.env`.

The MCP player must use survival mode. The test workflow also needs a separate
operator account and RCON access.

## Configure and start a character

The default configuration file is `.env`. Start with:

```powershell
uv run python main.py
```

You can use a character-specific file:

```powershell
uv run python main.py C:\Temp\Floppa\.env
```

There are no character setup or service wrapper scripts to run. On first
startup, `main.py` creates `MCMCP_AGENT_HOME` plus its `drafts/`, `skills/`,
`memory/`, and `frames/` directories. It also installs the shipped draft
examples and `AGENTS.md` only when those files are missing, so later runs do
not overwrite character work. Stop the foreground MCP with `Ctrl+C`.

If the selected file does not exist, `main.py` stops with code `-1` and prints
a complete copyable `.env` file. The output comes from the setting definitions
in the code. It includes every supported setting and its current default.
Any other startup error prints its full traceback and exits with `-1`.
Minecraft 1.19.4 and Node.js 20 or newer are required; unsupported versions
are rejected before the MCP starts.

Set the paths and credentials for your machine. The usual values are:

- `NODE_EXE`, `MCMCP_BODY_ENTRYPOINT`, and `BROWSER_EXECUTABLE_PATH`
- `MINECRAFT_HOST`, `MINECRAFT_PORT`, `MINECRAFT_PLAYER`, and `MINECRAFT_VERSION`
- `MINECRAFT_RCON_HOST`, `MINECRAFT_RCON_PORT`, and `MINECRAFT_RCON_PASSWORD`
- `MCMCP_AGENT_HOME`, `MCP_HOST`, and `MCP_PORT`

The MCP endpoint is `http://<MCP_HOST>:<MCP_PORT>/mcp`.

At startup, the MCP rewrites `MCMCP_AGENT_HOME/.mcp.json`. The `minecraft`
entry receives the current MCP port and a request timeout equal to the largest
server time limit plus 15 seconds. The current value is `615000` milliseconds.

For the checkpoint test server, start this before the MCP:

```powershell
uv run python start_checkpoint_server.py
```

## Manual MCP inspector

Set this in the selected `.env` file to start the manual browser inspector:

```text
MCMCP_INSPECTOR_ENABLED=true
MCMCP_INSPECTOR_HOST=0.0.0.0
MCMCP_INSPECTOR_PORT=0
```

Port `0` selects a random free port. The MCP start output shows the inspector
URL. Open that URL in a browser.

The page has a tool list, an argument editor with a send button, result state,
a screenshot area, and a local call log. It is only for manual debugging.
Each page request opens an MCP client to `/mcp`, performs one protocol call,
and closes it. The page has no direct access to the Minecraft body or the MCP
runtime. It does not stream state or provide a live view.

## MCP tools

Read each tool description before you call a tool. The descriptions state the
argument schema, survival limits, and returned data.

Examples:

```json
{"tool": "minecraft_observe", "arguments": {"include_image": true}}
```

```json
{"tool": "minecraft_walk_to_visible", "arguments": {"x": 12, "y": 1, "z": -4}}
```

```json
{"tool": "minecraft_mine_block", "arguments": {"position": {"x": 3, "y": 1, "z": 0}}}
```

Tool calls return typed world state. Tools that change the camera can attach a
PNG screenshot. The inspector shows that attached image in its right panel.

## Logging

The MCP writes logs under `~/.pm/pm-minecraft`:

- `mcmcp.log` records MCP tool calls, arguments, results, and errors.
- `body.log` records body actions.
- `driver.log` records test operator commands.

Set `MCMCP_LOG_LEVEL=debug` before you start the MCP to include a fresh state
snapshot after each body action. Debug mode is slower.

## Development

Build the body after a TypeScript change:

```powershell
Set-Location body
npm run build
Set-Location ..
```

The smoke suite uses a real Minecraft server:

```powershell
uv run python -m pytest tests -m smoke
uv run python -m pytest tests --last-failed
```

Every test returns the world to the checkpoint baseline before it starts. See
`test_infrastructure/README.md` and `tests/CONTRACT.md` for the test rules.
# Required server mod

Agentic Babymode 0.5.0 or newer is required. MCP checks the version at startup.
Mined loot enters the miner's inventory. Only overflow drops at the block.
Normal loot, tool requirements, enchantments, and durability apply.
The separate pickup-range mod is obsolete. Custom gameplay requires a custom fork.
