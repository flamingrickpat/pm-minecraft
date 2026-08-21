---
name: safe-mining
description: Rules for vertical travel and mining that never strand the bot. Use staircase_up / staircase_down (walkable ramp) instead of digging straight down or straight up. Keep pillar_up for outdoor open space only. Always equip the right tool, then mine. Never dig straight down.
---

# Safe Mining & Vertical Travel

The most common way to break a run is a vertical move the bot can't undo:
a straight shaft is a one-way trip.

## Never dig straight down or straight up

- Legacy skills `descend.ts` and `descend_to_depth.ts` throw a loud error on
  purpose — they carved 1-wide straight shafts. Do not use them.
- A straight shaft cannot be climbed back out and can drop you into
  undetectable lava/water/bedrock.

## Do this instead

- **Going down:** `staircase_down` (or `dig_staircase`) carves a 1-wide, 2-tall
  ramp you can walk down AND back up. Set `targetY` to your depth goal.
- **Going up / out of a mine:** `staircase_up` clears the headroom (the two
  cells above your head) then climbs one level at a time — works in the
  low-ceiling tunnels where `pillar_up` fails for lack of headroom.
- `minecraft_pillar_up` is fine **outdoors / in open space only**, where there
  is headroom. It needs a placeable solid block in hand.

## Equip the right tool first

- Call `minecraft_inventory_slots` to see the current slot layout: an
  `index -> {name}` map plus `heldItem`/`heldSlot`. This tells you exactly what
  is in your hands and which slot it is in — never guess.
- Before mining, `minecraft_equip` a matching tool (`*_pickaxe` for stone/ore,
  `*_axe` for wood, `*_shovel` for dirt/gravel). A steel pickaxe still can't
  harvest stone if you're holding cobblestone.
- If a `mine_block` returns `unharvestable`, equip the correct tool from the
  slot map and retry.

## Watch the furnace

- Smelting re-uses whatever furnace is nearby. The fix clears stale
  input/fuel and only collects output when your inventory can hold it.
- If a smelt returns `inventory_full_for_output`, free a slot first, then smelt
  again to collect — the bars are still in the furnace, not lost.
