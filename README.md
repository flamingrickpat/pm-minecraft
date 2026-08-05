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

Every `deploy/drafts/*.ts` example is copied into the workspace's `drafts/` and
listed in its `AGENTS.md`. They run as-is through
`minecraft_execute_typescript`, so the agent can execute one directly or copy
its guard-and-verify shape into a new draft. Add an example to `deploy/drafts/`
to ship it with every new character.

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

## Model-visible state

Every tool result carries a compact view of the after-state, and the full
snapshot is written to `artifacts/minecraft/state` instead of into the context
window. The compaction rules:

- Coordinates, distances, and angles carry one decimal.
- A `nearbyBlocks` entry reports `canHarvestWithHeldItem` and
  `needsHarvestTool` only when the held item cannot harvest it;
  `needsHarvestTool` is the cheapest tool that works.
- `localAirspace.openBlocksByDirection` gives open blocks per compass
  direction, and `boundaryDetail` lists only the boundaries that are not an
  ordinary wall (a missing direction means solid feet and head).
- `localAirspace.navigation` waypoints are `{x,y,z,clearance,openNeighbors}`
  cells that can be passed straight to `walk_to`.

After the first call the results are deltas against the previous compact state;
`minecraft_observe(full_state=true)` resets that baseline.

A screenshot is captured and written to
`artifacts/minecraft/screenshots` for **every** state - before and after every
action, on every `minecraft_observe` call - regardless of `include_image`, as
long as the server is started with image capture enabled (default; disable
with `--no-images`). This gives a complete, seamless on-disk visual history of
the run for later analysis, even for states the agent itself never looked at.

`include_image` only controls whether the pixel bytes are also attached to
that specific tool call's response so the agent can see them right now;
`minecraft_observe` defaults `include_image=true` (every other tool defaults
`include_image=false` to keep routine actions cheap in context). Pass
`include_image=false` to `minecraft_observe` to skip putting the image in the
response when only state is needed - the screenshot is still captured and
saved to disk either way. A screenshot that was requested but failed to
capture (viewer/bot not ready, no supported browser found) is reported as
`screenshot: {"error": ..., "message": ...}`, distinct from `screenshot: null`
(image capture is disabled server-wide via `--no-images`).

## Navigation profiles

`minecraft_walk_to` uses the `adaptive` profile by default. It can dig, place
scaffold blocks, use towers, use parkour, and drop as many as four blocks to
reach the target. It aims at the horizontal position (GoalNearXZ, so terrain
height is chosen automatically) and uses a **dynamic goal that streams/loads
chunks as it travels**, so it can cover long overland distances in one walk —
not just one chunk. `-ViewDistance` (default 24) controls how many chunks are
loaded around the bot.

`tolerance` defaults to **1** so the body gets adjacent for pickups and
placements; raise it for long noisy hops.

Set `profile: walk_only` when the route must not change blocks. This profile
disables digging, scaffold placement, towers, and parkour. It also limits drops
to one block and disables unlimited liquid drops. The command fails if no such
route exists.

`walk_only` does not guarantee that inventory stays unchanged. The character
can still pick up an item that is on the route. Compare before-state and
after-state inventory when that postcondition is required.

## Tunneling & long-distance navigation

- `minecraft_mine_block` normally requires head-line-of-sight, which is
  impossible for the adjacent feet-level block inside a 1-wide shaft. It now
  skips that gate for targets within `--mine-visibility-ignore-distance`
  blocks (default `3`, pass `-MineVisibilityIgnoreDistance` to the start
  script) so you can tunnel straight ahead from a 1-wide tunnel.
- `minecraft_walk_to` accepts targets up to `--walk-to-max-distance` blocks
  away (default `512`, pass `-WalkToMaxDistance`). The pathfinder's A* compute
  budget (`thinkTimeout`, default 40000ms) is raised so complex mountain
  terrain resolves instead of "path search exhausted its computation budget".
- `minecraft_pillar_up` reports a clear `pillar_up_needs_placeable_block`
  error when the held item is not a placeable block, and explains that the
  landing headroom must be cleared first; `dig_up` clears headroom per-hop.
- Ship-with-every-character drafts (auto-deployed to `drafts/`):
  - `dig_staircase(height, distance, stop)` — walkable 2-tall descending ramp.
  - `clear_room(width, depth, height)` — expands a 1-wide tunnel into a room.
  - `dig_up(targetY)` / `descend_to_depth(targetY, stopOnOre)` — hazard-safe
    single-hop ascent / descent that inspects for lava/water before digging.
  - `tunnel_forward` / `tunnel_iron` / `branch_mine_safe_iron` — tunneling & ore
    mining, all hazard-guarded (they stop before digging into water/lava).
  - `place_crafting_table` / `place_block` / `climb_pillar` / `find_village`
    (long-distance patrol that reports when it sees a villager).

## Halted runs, timeouts & the anti-stall guard

- `minecraft_stop` halts the active Mineflayer command **and** terminates any
  running TypeScript skill process (kills both). `minecraft_kill_command`
  stops only the current physical command; `minecraft_kill_skill` terminates
  only the running skill process.
- **Cooperative cancellation**: skills check a kill-signal marker in every API
  call / sleep and break out cleanly (`SkillCancelledError`) when stopped, so
  `minecraft_stop`/`kill_skill` (and a client disconnect) halt a skill quickly
  and let it write its result — the runner is only hard-killed if it ignores
  the marker.
- **Configurable skill timeout**: `minecraft_set_skill_timeout(seconds)`
  (1..3600) sets the max duration for `minecraft_execute_typescript` and
  `minecraft_collect_blocks` (default 90; launch-time default via
  `-SkillTimeoutSeconds` / `--skill-timeout-seconds`). Long skills run in a
  separate subprocess and are terminated server-side at that timeout.
- **Match your client window**: the agent's `.mcp.json` `requestTimeoutMs`
  (character default `200000`) must stay ABOVE the server skill timeout,
  otherwise long skills are cut off client-side before they finish. Rule of
  thumb: set `minecraft_set_skill_timeout` to `requestTimeoutMs - 10s`.
- The repeated-no-gain circuit breaker is **disabled by default**. It was a
  relic of older, weaker models that retried an identical no-gain operation in
  a loop; keyed to a single "relevant item", it wrongly blocked unrelated
  skill ops. Re-enable it explicitly when you want it with the
  `--enable-anti-stall-guard` MCP argument (`-EnableAntiStallGuard` on the
  start script).

## State transparency

- Every state (full and delta) always carries the player `position`,
  `health`, `food`, and `foodSaturation`, and every result always reports the
  current `heldItem`, so an agent never has to infer its own vitals or held
  tool from a diff.
- `minecraft_collect_blocks` equips the cheapest tool that harvests the target
  block up front (instead of dying mid-run with an `unharvestable` rejection),
  and the body no longer swaps the held item except when `collect_blocks`
  needs a different tool.

## Tips from live testing (agent ergonomics)

These come from real in-game sessions with a coding agent and are worth
encoding into your agent's AGENTS.md or skill prompts:

- **Coordinates are flat** on the wrapper tools: `minecraft_walk_to(x,y,z,…)` /
  `minecraft_mine_block(x,y,z,…)` take separate numbers, NOT a `position`/`block`
  object. For nested action schemas use `minecraft_call` with the shapes in
  `minecraft_info` (e.g. `{"action":"place_block","parameters":{"referenceBlock":{…}}}`).
- **Probe before you dig**: read `hazards` (water/lava) and `inspect` the next
  cell before tunneling. Shipping drafts stop on a hazard; a raw `mine_block`
  into water/lava strands the bot.
- **Held-tool drift**: a climb-y `mine_block` or `pillar_up` can leave a
  placeable block (dirt/cobblestone) in hand instead of a tool. Re-equip and
  verify after any climb-y mine; tools also break on durability, so keep a
  spare pickaxe.
- **Mine wide, not 1-wide**: 1-wide tunnels only expose the front face and
  tunnel past side-wall ore. Use `clear_room`/`branch_mine_safe_iron` (3-wide)
  to expose ore, and treat `find_block`'s line-of-sight (anti-x-ray) result as
  "go look / mine to reveal it".
- **Long overland travel works** with the dynamic chunk-streaming walk; keep
  each `walk_to` under your client window and it covers far more ground than
  one-chunk hops.
- **Timeouts**: keep `minecraft_set_skill_timeout` at `requestTimeoutMs - 10s`
  so long skills finish instead of being cut off. `minecraft_info` reports the
  current value; re-read it whenever docs drift.
- **Prefer many small reversible skills** over one huge irreversible one; each
  needs a deterministic postcondition. `minecraft_observe` + `minecraft_stop`
  let you track and halt any stray run.

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
