# Live test infrastructure

This suite uses a real Fabric server and real Mineflayer clients. It does not use Minecraft mocks.

Checkpoint mode is the default mode. One Minecraft server stays active for the complete test session.

## Start the server

1. Start the checkpoint server from the project root:

```powershell
uv run python start_checkpoint_server.py
```

2. Wait for the `Checkpoint server ready` message.
3. Start pytest in a second terminal.
4. After pytest stops, press Ctrl+C in the server terminal.

The launcher disables natural mob, trader, patrol, and insomnia spawns. Then it removes non-player entities and runs `/commit`.

On Ctrl+C, the launcher runs `/revert` before it stops Minecraft. This action keeps the saved world clean for the next session.

## Test lifecycle

Each test uses this sequence in checkpoint mode:

1. Require the configured Minecraft port.
2. Create a new agent directory.
3. Connect `tdd_operator` and a temporary `tdd_player`.
4. Run `/revert`.
5. Reset the temporary player's inventory, effects, experience, health, and food.
6. Remove all non-player entities.
7. Create the complete world state with operator commands.
8. Read each setup fact through Mineflayer.
9. Disconnect the temporary player.
10. Start the MCP as `tdd_player`.
11. Call one MCP tool without an LLM.
12. Read the final state through `tdd_operator`.
13. Stop the MCP and both Mineflayer clients.
14. Remove the agent directory.

Pytest does not stop or remove the Minecraft server in checkpoint mode. The operator remains connected during each MCP call.

Set `USE_SERVER_CHECKPOINTING=false` in `.env` to use isolated mode. Isolated mode creates and removes one server world for each test.

## Commands

Run the infrastructure tests:

```powershell
uv run pytest -m infrastructure -v
```

Run one tool:

```powershell
uv run pytest tests/test_minecraft_find_block.py -v
```

Run one scenario:

```powershell
uv run pytest tests/test_minecraft_find_block.py -k east_limit -v
```

Run the smoke cases:

```powershell
uv run pytest -m smoke -v
```

Run all cases overnight:

```powershell
uv run pytest tests -v
```

## Reliability guarantees

The infrastructure suite proves these guarantees. Checkpoint mode takes about four minutes on this computer.

Each test requires a real local server. Checkpoint mode stops immediately when the server port is not active.

- **Process cleanup.** Teardown stops the MCP and both Mineflayer clients.
  Checkpoint mode keeps Minecraft active. Isolated mode also stops Minecraft.
- **Command replies are reaped by silence, not a timer.** A large `/fill` or
  `/clear` reply can out-last a fixed delay. The driver now waits for a quiet
  window, so reads never race a still-running command.
- **During-action waits are real.** `tests/test_harness_mechanics.py` proves
  every wait in the tool harness against the live driver: block-break
  progress, entity hurt, chest lid, block-property changes, and player
  movement.
- **Scenario fills are read back.** The operator counts each block in every
  arranged fill region before the MCP starts.
- **Result JSON has one exact shape.** Nested results fail when a declared
  field is absent or an unknown field is present.
- **Inventory deltas use server truth.** The operator reads the full player
  inventory before and after the action. The test compares every changed item.
- **The mod is live, not merely installed.** `test_babymode_mod_is_live`
  damages the player and waits, then drops an item at distance 3 to prove
  natural regeneration is off and the pickup magnet is absent.
  `test_playability_regressions.py`: direct mined-loot collection and overflow.
- **The MCP process is reusable and self-cleaning.** The restart test
  launches concurrent tool calls, restarts the MCP, confirms the same tool
  set, and proves the port is released.

The current MCP is a stub. Behavior cases stop at player handoff until a live backend owns `tdd_player`.

If a required path is absent, test collection stops. The error lists each absent path.

Read `tests/CONTRACT.md` for the result rules. Read `tests/SCENARIOS.md` for the scenario rationale.
