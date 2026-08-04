# pm-minecraft

A self-contained Minecraft survival body for MCP clients. 

It runs Mineflayer, Prismarine Viewer, a local web UI, and a Streamable HTTP MCP server. 

It does not contain an agent, model, or cognitive runtime. Only some minimal instruction
telling your agent of choice how to use the MCP, look at screenshots and make
custom TypeScript scripts, that can be executed via MCP.

Huge thanks to https://github.com/minedojo/voyager and https://github.com/Mega-Gorilla/Discovery :3

This is part of an ongoing effort on my side to make a fun cognitive architecture AI companion that can play minecraft with you. Also works as standalone ^_^

## Setup

Requirements: Windows PowerShell, Node.js 20+, Python 3.12 through `py`, and a
reachable Minecraft Java 1.19.x server with the character in survival mode.

```powershell
Set-Location C:\workspace\pm-minecraft-mcp
.\setup.ps1
```

The setup follows the shared PM workflow: it uses `uv` to create this
repository's Python 3.12 `.venv`, syncs its lockfile, and installs locked Node
packages. `scripts/setup.ps1` remains as a compatibility wrapper.

If it doesn't work tell your coding agent to fix it.

## Minecraft

I stole the setup from https://github.com/Mega-Gorilla/Discovery.

I have never modded Minecraft manually, what works for me: 

- Download Prism
- Install 1.19.4
- Install Fabric Loader 0.19.3 
- Install these mods via Prism:
    - Fabric API
    - CompleteConfig
    - Mod Menu
    - Multiplayer Server Pause (Forge)
    - item-pickup-range by wenhao (/setPickupRange 5)
- Make Survival World, Cheats Enabled, Peaceful
- Enter and "Open to LAN" on Port 12345

## Create and start a character

```powershell
.\scripts\init_character.ps1 `
  -Name Floppa `
  -AgentRoot C:/Temp/Floppa `
  -ArtifactRoot C:/Temp/Floppa/artifacts/minecraft

.\scripts\start_minecraft_mcp.ps1 `
  -Name Floppa `
  -MinecraftHost 127.0.0.1 `
  -MinecraftPort 12345 `
  -AgentRoot C:/Temp/Floppa `
  -ArtifactRoot C:/Temp/Floppa/artifacts/minecraft
```

The initializer creates the agent workspace, `memory/minecraft/`, `drafts/`,
`skills/`, `lib/minecraft.ts`, and `.mcp.json`. The launcher prints the local
web UI, Prismarine viewer, and MCP URLs. For multiple characters, use unique
`-WebPort`, `-ViewerPort`, and `-McpPort` values.

Stop an instance with:

```powershell
.\scripts\stop_minecraft_mcp.ps1 -ArtifactRoot C:/Temp/Floppa/artifacts/minecraft
```

Then use it from the workspace:

```powershell
Set-Location C:/Temp/Floppa
codex
```

Codex reads `.mcp.json`. Prompt it to use the `minecraft` server; state logs
and screenshots are under `./artifacts/minecraft`.

## Perception and viewer modes

`minecraft_find_block` defaults to `require_visible: true`. This is the normal
survival setting: it returns only blocks with an unobstructed ray from the
character's head. An agent must explore, move to a better viewpoint, or use a
different observation when it cannot see the target. For long-range planning,
set `require_visible: false`; the result is a loaded-world location only and
must still be reached and visibly verified before mining.

## Navigation profiles

`minecraft_walk_to` uses the `adaptive` profile by default. This profile keeps
the existing behavior. It can dig, place scaffold blocks, use towers, use
parkour, and drop as many as four blocks to reach the target.

Set `profile: walk_only` when the route must not change blocks. This profile
disables digging, scaffold placement, towers, and parkour. It also limits drops
to one block and disables unlimited liquid drops. The command fails if no such
route exists.

`walk_only` does not guarantee that inventory stays unchanged. The character
can still pick up an item that is on the route. Compare before-state and
after-state inventory when that postcondition is required.

## Cool stuff

Here is the WebUI where you can manually control the character or look at how the coding agent uses the MCP.

[<img src="./docs/webui.png">](https://top.lel)

And here is Codex describing my character's skin. Prismarine only renders default Steve :(

[<img src="./docs/agent.png">](https://top.lel)


## Development

```powershell
npm test
npm run build
.\.venv\Scripts\python.exe -m compileall mcp
```
