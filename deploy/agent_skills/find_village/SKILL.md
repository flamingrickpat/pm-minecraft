---
name: find-village
description: How to search for a village from a high vantage point using minecraft_raytrace, minecraft_rotate, minecraft_walk_to (with settable chunk_limit), and scanning the surroundings, hopping from high point to high point until a village is found. Use when the goal is to find a village, villagers, or village structures.
---

# Find a Village from high points

Finding a village over long distance requires height + sight, not a straight
line on the ground. Follow this loop.

## Strategy (high-point to high-point)

1. **Get to a high vantage point.** Climb a hill / mountain or pillar up a few
   blocks (outdoors). You need line of sight over the terrain.

2. **Scan in a full circle** (or in 30–45° wedges):
   - Use `minecraft_rotate(yaw_degrees=...)` to pan. It takes settable degrees,
     so turn in precise steps (e.g. 30°) rather than fixed increments.
   - At each heading, call `minecraft_observe(include_image=false)` and look at
     `surroundings.nearbyBlocks` for village tell-tale blocks:
     `hay_bale`, `dirt_path`, `wheat`, `carrots`, `potatoes`, `barrel`,
     `composter`, `bee_nest`, any `*_bed`, `cobblestone`, and
     `nearbyEntities` for `villager`.

3. **Confirm what you actually see with raytrace.** When any candidate village
   block is in `nearbyBlocks`:
   - `minecraft_rotate` to aim at it.
   - `minecraft_raytrace(max_distance=...)` returns the exact block under the
     crosshair: `{ blockName, position }`.
   - If it reads `cobblestone`, `*_planks`, `stripped_*_log`, `hay_bale` or a
     farm block, you are close enough — the position is valid. **Save it** with
     `minecraft_add_waypoint(x=..., y=..., z=..., description="village")`.

4. **Travel to the waypoint.** `minecraft_walk_to` reaches it:
   - It takes a settable `chunk_limit` (default 3, up to 8). For long hops use
     `chunk_limit=6` or `8` so one call spans more than a chunk.
   - walk_to routes to the nearest safe standable cell, so a land-based target
     usually "just works".
   - If it returns `target_not_standable` or `no_paths_findable` (e.g. across a
     ravine), do NOT give up: use `minecraft_pillar_up` or a staircase to gain
     height, or pick another high point and hop around the obstacle.

5. **After arriving**, get high again and repeat. Keep hopping between high
   points in a different heading each cycle to cover ground, not wander.

## Rules

- Never run `find_village.ts` — it is legacy and does not work reliably. Use
  this manual high-point + raytrace loop instead.
- Save every confirmed village/ore/landmark with `minecraft_add_waypoint` and
  recall with `minecraft_list_waypoints`.
- Keep waypoints in mind (cap 6, oldest dropped) only for short-lived targets.
- Confirm sightings with `minecraft_raytrace` — don't walk 200 blocks on a
  maybe.
