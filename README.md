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

`minecraft_mine_block` can dig breakable vegetation, including grass and tall grass.
`minecraft_inspect_block.is_solid` describes collision bounds.
Grass and tall grass have empty bounds and support digging.
The body uses Mineflayer's normal digging path and checks the resulting block.
If the target becomes air before digging starts, the body reports `target_changed`.
The Python tool still rejects an air target observed before the action as `not_found`.

`minecraft_recipe_search` checks every ingredient variant for each matching item.
It reports a recipe that uses available inventory when one is usable.
Otherwise, it reports the variant with the smallest ingredient deficit.
Failed `minecraft_craft_item` calls use that same deficit rule for missing ingredients.
Birch planks can therefore satisfy a stick recipe without requiring oak planks.
The `craftable_now` field also requires a nearby crafting table for a 3 by 3 recipe.
The table search uses the same four-block range as `minecraft_craft_item`.
The optional filter selects available or unavailable items; it does not change that field's meaning.
This search reads the recipe registry, inventory, and loaded terrain. It does not consume items.

Block searches allow 30 seconds for the body HTTP response.
Broad patterns inspect exposed faces across the full search box and can exceed the two-second timeout used for status reads.
The result retains its actual search coverage and matching block count.

Each walk uses one deadline for path search, partial-route search, movement, and replanning.
Surface shaft approaches use the time left in that same deadline.
A timed-out or stopped approach returns its current position and camera.
The internal HTTP grace period can then receive the normal failure result.

Player oxygen comes from the player's own air metadata on the 0 to 20 bubble scale.
Mineflayer 4.38 can overwrite its global oxygen value when another entity's metadata arrives.
That global value does not establish the player's air supply.

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

### Body ownership and restart

PM's actor uses one shared operating-system lease per MCP endpoint.
The server retains the matching epoch in `MCMCP_AGENT_HOME/body-epoch.json`.
`minecraft_body_claim(owner, epoch, session)` waits for an active command, then commits a higher epoch.
`minecraft_body_call(owner, epoch, session, tool, arguments)` validates that token before calling the original typed tool.
`minecraft_body_release(owner, epoch, session)` waits for cleanup and retains an inactive epoch.
An identical active claim is idempotent.
An old epoch, changed session, or inactive equal epoch fails before body access.

Original tool arguments and results keep their existing schemas.
Direct observations remain available.
Direct mutations require the token while an owner holds the body.
The concurrent stop tool validates the same token before cancelling its command.
A client disconnect does not release an active server command.
A replacement claim waits until that command finishes.
MCP startup invalidates any retained active token and preserves its high-water epoch.
The test-controlled body stop does the same before disconnecting the character.

Keep the character directory across server restarts.
Keep PM's shared lease registry across application restarts.
All local PM instances must use the same registry and one endpoint per avatar.
The protocol assumes trusted local clients and one MCP service per avatar.
Epochs reject stale commands; they do not authenticate clients or restore world effects.
The [A12 application manual](https://github.com/flamingrickpat/pm_next_v2/blob/main/docs/subsystems/body-recovery.md) documents explicit recovery and retained evidence.

The build tool uses native placement for doors. Request the lower cell.
One door item creates lower and upper halves. The result lists both cells,
including the automatic upper cell outside a one-cell request.
Fresh inspection checks both halves. The block interaction tool opens or
closes the door. Ordinary block shapes keep their existing server assistance
and inventory consumption.

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

`minecraft_observe` includes the public `body_session` identity and `death_count`.
`minecraft_info.server_rules` contains the server's current `babymode help` response.
This read does not change world or player state.
Check natural regeneration and enabled nutrition effects before choosing health recovery.
Equipping closes an open container window before selecting the player-inventory item.
The equip HTTP request allows thirty seconds for Mineflayer's bounded inventory update.
The count increases when Mineflayer reports the player's death.
A new Node body process starts a new session and counter.
Respawn does not undo a death or prove that a hazard was survived.
The body log appends a session marker so later body startup preserves earlier logs.

Agentic Babymode 0.5.0 or newer is required. MCP checks the version at startup.
Mined loot enters the miner's inventory. Only overflow drops at the block.
Normal loot, tool requirements, enchantments, and durability apply.
The separate pickup-range mod is obsolete. Custom gameplay requires a custom fork.

The staircase helper checks loaded solid support below each notch before digging.
It preserves that floor and uses the normal pathfinder for one exact landing.
Only a grounded one-block descent in the same life counts as a step.
Unknown support, an unstable floor, changed clearance, failed movement, cancellation, or death stops the descent.
Partial descent returns `ok=false` with a reason and retained dug-block quantities.
The result includes the body session and death counters before and after the action.
Inventory loss across death does not prove block placement or ingredient consumption.

Run the captured staircase boundaries after building the body:

```powershell
node --test body/test/staircase-boundary.test.mjs
```

These checks use captured real-server geometry and an actual failed descent.
The positive one-step control is a contract projection, not a live gameplay pass.

## Harvesting prerequisites and occupied body space

M3-34 accepted the revised respawn reconciliation through verifier 111.
This fifth certificate does not establish native healing.
The next actor rebuilt ordinary wood stock but repeatedly tried to mine exposed iron with a stick.
Its block search reported false harvestability.
The exact inspector returned empty tools, null harvesting eligibility, empty drops, and null hardness.
Those omitted fields failed the inspector contract.

The body now supplies tool names sorted by actual breaking time, current held-tool harvestability, registry drops, and hardness.
The MCP inspector publishes those typed facts.
After two wrong-tool failures, the gateway requires a fresh true harvestability read for each requested target.
Changing coordinates or writing another diagnosis cannot override false or missing eligibility.
A fresh block search can also provide exact-target eligibility.
Reads must follow the latest wrong-tool failure and belong to the current actor source.
Other prerequisite actions remain available, subject to the existing recovery guards.
Historical tool certificates remain valid evidence of earlier work; they do not prove current ownership after death.

The same actor dug below its body and placed birch planks inside its feet cell.
The server recorded `tdd_player suffocated in a wall`.
Its final observation reported one death and an empty inventory.
The body now refuses mining below every horizontal column touched by the player's 0.6-block width.
The MCP build path rejects an entire request that overlaps the standing 1.8-block body before any placement or inventory consumption.
The check includes a door's upper half.
A floor ending at the feet and construction from a supported side remain permitted.
Crouching uses the conservative standing-height bound.
These guards use fresh production body positions rather than an old journal pose.

`a13-harvesting-body-space.json` retains the original reads, false-tool calls, placement, death observation, and source digests.
Minecraft's `a13-body-space.json` retains the actual pose and affected cells.
Captured and projected boundary tests are engineering checks; they do not establish repaired native behavior.
No inventory, world, or accepted specification was restored to conceal either death.
M3 remains pending and must continue from M3-34 in the same retained world.

Equipment now reports fresh held-tool eligibility and a registry-based theoretical craft hint.
Success can mean the already-held item remains suitable; it does not establish resource progress.
The companion pauses repeated equipment no-ops after two calls.
M3-36 exercised real inspection, support refusal, and adjacent soil gains, but did not complete the iron chain.

## Bounded smelting and retained furnace contents

M3-37 mined three fresh raw iron and independently verified the mining leaf.
Its next actor requested three smelts with one birch log, then hit a body HTTP timeout.
The original body waited indefinitely for all requested output.
One log or plank smelts 1.5 items; three iron require two logs or planks.

Smelting now stops after observed fuel exhaustion or a 90-second body wait.
Partial output and unused input and fuel return to inventory.
`furnace_before` records actual slots before the action.
`recovered_output` reports existing output separately from the new batch.
The body collects retained contents before loading another batch and closes the window in its final cleanup.
A protocol error can still leave inserted items; closing the window does not undo them.
The next call must inspect retained effects rather than repeat the original count blindly.
The public result preserves partial quantities and the actual failure reason.
Captured and projected checks use `body/test/fixtures/a13-smelt-timeout.json`; they do not establish native acceptance.

M3-39 independently opened that furnace and observed two raw iron and one ingot, with no fuel.
Its actor then passed the furnace to chest withdrawal, causing an unsupported-container exception.
Storage transfer now validates the current block type and five-block distance before opening.
Invalid targets return `not_storage_container`, `out_of_range`, or `target_changed` without transfer.
The public tools require an explicit chest, barrel, or shulker-box cell.
Colored shulker boxes remain supported.
Furnaces use `minecraft_smelt_item`, which collects previous output and smelts the remaining input with supplied fuel.
`a13-furnace-storage-target.json` retains the real inspection, window, wrong tool calls, and original error.

M3-41 used the correct smelting tool and recovered two raw iron and one ingot.
The tool then reported missing input because Mineflayer's main inventory remained stale until the furnace window closed.
Smelting now counts player inventory directly from the live window's inventory range.
Furnace slots remain separate, so retained input cannot count twice.
The actual reply and subsequent observations remain in `body/test/fixtures/a13-window-inventory.json`.
The reply records recovered output and no new smelt; later observations confirm the real inventory gains.
These captures and window-count boundaries establish the repair contract. Fresh native completion remains pending.

## Observed block activation

M3-58 completed and independently accepted the roof and construction story.
Its next actor stopped at the entrance after a tool reported `door_opened` while independent server reads still showed a closed door.
The reply also attached the old furnace window as a chest window at the door.
Later native interactions left the door open before shutdown. Those effects remain preserved.

The Node body's `useBlock` now closes the previous container window before another activation.
Doors, gates, and trapdoors require an observed change in their `open` property.
Container activation requires a new window. Other interaction kinds retain their existing packet-activation contract.
One ten-second wait bounds confirmation; the Python body client allows fifteen seconds for that request.
`activation_unconfirmed` returns `ok=false` and no claimed action.
The public result includes `open_before` and `open_after` when the target has this property.
A delayed server effect can still occur after an unconfirmed result; inspect current state before retrying.

The real `a13-block-activation60` probe opened the furnace and toggled the same door twice.
Independent server reads confirmed both door halves after each toggle.
The door reply contained no stale window. Position, inventory, and vitals remained unchanged.
Both toggles returned the door to its initial observed state through ordinary tool calls.
The original mismatch and successful probe remain in `body/test/fixtures/a13-block-activation.json`.
These protocol results do not establish native entry or complete M3 acceptance.
