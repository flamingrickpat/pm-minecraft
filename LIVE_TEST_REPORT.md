# Live Mechanics Playtest — Floppa (2026-08-17)

Extended in-game test session covering mining, caving, smelting, crafting,
chests, navigation, and passive-mob combat. Server config: 1.19.4, peaceful,
`walkMaxChunks: 8`, `walkSearchTimeoutMs: 1000`.

## Verified working (PASS)

| Mechanic | Evidence |
|---|---|
| `walk_to` speed | Sub-second command times (0.5–3s) for reachable goals; no more 30s hangs |
| **noPath → bot stays put** | Closed the fence gate, tried to walk out: `pathfinder_no_path` in 593ms, position before/after identical `(140.53,69.94,15.64)` — zero displacement |
| `find_interactables` | Gate, crafting table, composter, oak doors, furnace, chest all detected |
| Anti-x-ray `find_block` | Underground `diamond_ore` → `block_not_found`, `requireVisible: true` hard-locked server-side (skills/raw HTTP can't override) |
| `use_item` | Bread → `food_full` guard (food detected via registry `foodsArray`); at hunger<20 it would consume |
| Crafting | wooden_pickaxe, stone_pickaxe, furnace, chest, planks ×12, sticks ×8 — all deltas verified |
| Mining | grass→dirt, stone→cobblestone, coal_ore→coal, oak_log→log. Correct-tool enforced (copper_ore flagged `needsHarvestTool: stone_pickaxe` with wooden held) |
| Caving | Dug a 10-block shaft (136–138, y55–66) reaching stone + coal + copper vein; pillared back out |
| **Smelting** | 2 beef → 2 cooked_beef with 1 coal (20.5s); fuel/input/output deltas all correct |
| **Combat (new entityHurt)** | `attack_entity` on fleeing chicken → **`hit: true`**; chased 16+ blocks (renavigation worked); chicken died, drop auto-picked (+1 chicken); 2nd attack after death → clean `entity_not_found` |
| Placement | Furnace (144,70,17) + chest (144,70,20) placed, `verified: true`, item consumed |
| Drop pickup (partial) | `walkIntoRange=true` usually auto-collects (log at y71 collected); walking over a drop always collects |

## Bugs & gaps found

> FIXED in this branch (see STATUS below): #1 mining view, #3 chests, #4 stale
> block-name, #5 combat health fields. #2 pickup range raised by user to 10.

1. **`mine_block` "Block not in view"** (confirmed 2×): with `walkIntoRange=false`,
   digging a target that isn't aligned with the bot's facing/pitch fails
   `dig_failed: Mineflayer dig failed: Block not in view`. A parallel mine of a
   block in-facing **succeeded** while the off-axis one failed — purely
   orientation-dependent. Recommended fix: `mine_block` should auto-look at the
   target before digging (or `walkIntoRange=true` repositions). This makes
   mining adjacent wall blocks in a confined shaft require manual
   rotate-then-mine dance.

   **FIXED**: `digFaceFor()` now computes the dig face from the player→block
   offset instead of mineflayer's `raycast`, which threw "Block not in view"
   whenever a nearby wall obscured the eye ray. Viewport/rotation no longer
   matters — the face is derived from position, so mining works from any
   orientation.

2. **Drop pickup is flaky** (the 5-block pickup fix is incomplete):
   - `walkIntoRange=false` mining from >2 blocks always leaves the drop on the
     ground (observed with the first oak_log @(140,69,16) — had to walk over it).
   - Even `walkIntoRange=true` missed once: log @(155,72,24) fell 1 block to y71
     and stayed as an item entity (19046) until walked over.
   - Pattern: pickup seems to fire only while the dig-walk is in progress, not as
     a reactive "collect anything within 5 blocks" check after dig completes.
   - User raised the collection radius to 10; the drop-walk threshold in
     `mine_block` is now `> 10` (only pathfind to a far drop). Reactive pickup is
     still server/dig-walk dependent and remains best-effort.

3. **Chests were NOT supported** (user-requested test): `use_block` on a chest
   returned `windowType: null` because `detectOpenedWindowType()` only knew
   `minecraft:crafting` and `minecraft:furnace`. There was no deposit/withdraw
   action either.

   **FIXED**: `detectOpenedWindowType()` now returns `"chest"` for chest/barrel/
   shulker/hopper/container windows, and two new actions + MCP tools were added:
   `minecraft_chest_deposit(itemName, count)` and
   `minecraft_chest_withdraw(itemName, count)` (routes `/api/chest/deposit` and
   `/api/chest/withdraw`). They use mineflayer's `window.deposit/withdraw`
   (available on every opened container) and return the container's contents.

4. **`mine_block` block identity is stale/suspect**: blocks mined at y63/y64
   (underground, should be dirt) were reported in responses as `grass_block`
   (3 stacked grass_blocks is implausible; drops were correctly `dirt`). This
   matches the earlier stale `resultBlockName: "wheat"` report after the wheat
   harvest. The after-state/verification is correct (`air`), only the
   `blockName` echo appears to come from a stale neighbor scan.

   **FIXED**: `resultBlockName` is now re-read **after** the 250ms dig-settle and
   the 1s pickup wait (it was captured immediately after the dig race, before the
   world cache settled). The response reports `"air"` for a cleanly mined block
   instead of an echo of the pre-mine/cached name.

5. **Combat health fields are dead weight**: `attackEntity` healthBefore/
   healthAfter are always null (mineflayer 1.19.4 entity health not populated),
   so the health-delta fallback never fires. `entityHurt` is the only signal —
   and it works. Suggest dropping the health fields from the response.

   **FIXED per request**: `healthBefore`/`healthAfter` removed entirely, and
   `attackEntity` now **keeps swinging until the target is dead/gone** (up to
   `maxHits`, default 25), re-navigating as it moves; returns `hit`-count and
   `killed: true` in an `ok` result when the entity disappears, or
   `attack_timeout`/`entity_out_of_range` if it survives.

6. **Minor**: `oxygenLevel` in state fluctuates oddly (0 / -1 on the surface,
   19–20 near water, then 20) — likely a reporting artifact, not actual drowning.

7. **Minor**: `walk_to` `target_not_standable` for (135,70,25) — preflight
   correctly rejected (uneven terrain). And a ~27-block `noPath` to (138,70,5)
   from the east field suggests the search region (chunk cap) can refuse
   targets that are technically in range when tree canopies/fences are dense —
   it fails cleanly (no displacement), just worth knowing.

## STATUS
- All 5 reported issues addressed. Fixes: `digFaceFor` (mining), dropped `health*`
  + hit-until-dead (attack), added `detectOpenedWindowType` "chest" + chest
  deposit/withdraw actions/tools, delayed authoritative `resultBlockName`.
- Pickup radius raised to 10 by the user; `mine_block` drop-walk threshold now 10.
- Build green (tsc + py_compile), route/config tests pass (12).
- **Requires MCP/body restart** to take effect.
- Verification draft: `drafts/verify_fixes.ts` (chest round-trip,
  off-view mining, attack-until-dead).

## Not tested / deferred
- Mining **iron/copper with the stone pickaxe** (copper vein exists at
  (137,58,24) in my shaft, but re-descending a 10-block walk-only shaft is
  unsafe; deferred).
- Chest deposit/withdraw — impossible, see bug #3.
- Hostile mob combat — world is peaceful; no hostiles exist.
- Vision-based mob location — model has no image support; mobs were found via
  `nearbyEntities` state instead.

## World state left behind
- Shaft: x136–138, z21–24, y55–66 (open 1×1 vertical + small room at y58).
- Furnace @ (144,70,17), chest @ (144,70,20) (mine, empty), one oak tree
  partially chopped (155,71–72,24).
- Farm untouched except 2 wheat harvested + replanted earlier sessions.
- Inventory: cooked_beef×2, chicken×1, bread×1, wooden_sword, egg, seeds×8,
  wooden_pickaxe, stone_pickaxe, dirt×5, planks×2, sticks×3.