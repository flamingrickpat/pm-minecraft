---
name: minecraft-waypoints
description: Use in-memory waypoints (minecraft_add_waypoint / minecraft_list_waypoints) to remember short-lived coordinates like an ore vein, a staircase entry, or a block you can't mine yet. Because find_block cannot see underground (anti-x-ray), remember where things are instead of re-finding them.
---

# Minecraft In-Memory Waypoints

`find_block` will **not** rediscover a walled/underground target: its
anti-x-ray is hard-locked, so something you already mined (e.g. an iron vein)
returns `block_not_found` from any visible angle. The fix is to **remember** it
instead of re-finding it.

## When to save a waypoint

Save coordinates the moment they matter, while you can see them:

- A block you are mining (the vein's origin) — so you can walk back to it later.
- The entry of a staircase or a mine you dug — so you can return to it.
- A block too expensive / unmineable right now ("come back with better tool").
- A confirmed village sighting from `minecraft_raytrace`.

Anything you would otherwise have to *see* again to locate is a candidate.
Nothing that matters in the grand scheme — these are ephemeral and in-memory.

## How

- `minecraft_add_waypoint(description="iron vein", x=..., y=..., z=...)`
  stores it. Omitting any coordinate uses the **current position** — handy right
  after you stop at a spot.
- `minecraft_list_waypoints()` returns `{ waypoints: [{x,y,z,description}], count, cap }`.
- Cap is 6; when full the **oldest** is evicted. Not persisted across sessions.

## How to use them

- To revisit a saved spot: `minecraft_walk_to(x=..., y=..., z=..., chunk_limit=6)`
  and let walk_to's standable-cell routing bring you in range.
- After collecting everything at a spendable spot, replace it (add a new one for
  the next target — the oldest falls off).

## Rules

- Remember **at the moment of discovery**, not later from memory.
- Prefer a waypoint over `find_block` for anything underground, in a wall, or
  around a corner — find_block can't see those by design.
- For durable, long-term facts (base location, route home, big chests) use the
  persistent memory files instead (AGENTS.md / memory/*.md), since waypoints are
  lost across sessions and autocompacts.
