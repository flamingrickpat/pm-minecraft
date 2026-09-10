"""MCP tool definitions for the v2 Minecraft surface.

Each method contains one public contract and one typed runtime call.
The runtime contains the action logic and returns the declared Pydantic model.
At import time, `_render_doc_constants()` adds values from `constants.py`.
FastMCP publishes the return schemas without duplicate schema text.

How to read every tool
======================

World rules you can rely on
    - You are one survival player on a normal server. Tools fail loudly
      with `reason` codes instead of silently doing nothing.
    - One block = 1.0 distance. Y is up. Vec3i = block cells, Vec3f = points.
    - Nothing here needs "aiming" unless it says so. find/build/mine take
      absolute coordinates, not look directions.

Glob names
    Wherever a tool takes a block/item/material name, you can send a glob:
    "*log" (ends with log), "*_ore" (any ore), "oak_*", "diamond*", "?"
    single char. One match -> the tool acts. Several -> nothing happens,
    `candidates` lists the choices, re-call with an exact name. None ->
    `candidates` lists the closest known names (typo help).

Return value convention
    Every tool returns exactly one pydantic model: `ok`, `reason`,
    `message` plus tool-specific payload. Success payloads are None on
    failure when their schema permits None. Other failure counts are zero
    and lists are empty. Tools that change what you see carry an image.
    Bookkeeping tools never do.
    Every result carries `warnings`: observed tool loss or unexpected
    held-item changes during the action.

Error boundary
    Invalid arguments return an MCP validation error. If the player body is
    not available, body-dependent tools return an MCP error. These errors do
    not use a normal result model.
    An action interrupted by minecraft_stop returns `ok=False` with reason
    "stopped".

Removed from v1 (do not look for them)
    - place_block / jump_place_block: replaced by `minecraft_build`, which
      spawns whole structures without aiming or walking per block.
    - generic state-file links: results carry their own data now.
"""

from __future__ import annotations

import inspect
from typing import Annotated, Literal

from pydantic import Field

from .constants import DOC_CONSTANTS, PILLAR_UP_BLOCK_LIMIT
from .models import (
    AddWaypointResult,
    AreaReportResult,
    AttackEntityResult,
    BuildResult,
    ChestMoveResult,
    CountResult,
    CraftItemResult,
    CraftMaxResult,
    DiscardResult,
    DistanceResult,
    DropResult,
    EatBestResult,
    EquipBestToolResult,
    EquipResult,
    ExecuteSkillResult,
    FindBlockResult,
    FindInteractablesResult,
    HarvestTreeResult,
    InfoResult,
    InspectBlockResult,
    ListCapabilitiesResult,
    ListWaypointsResult,
    MemoryHit,
    MineBlockResult,
    MineVeinResult,
    ObserveResult,
    PathPreviewResult,
    PillarUpResult,
    RecipeSearchResult,
    RecallResult,
    RelativePositionResult,
    RememberResult,
    RespawnResult,
    RotateResult,
    RaytraceResult,
    SafetyReportResult,
    ScanHorizonResult,
    ScreenshotResult,
    SleepResult,
    SmeltItemResult,
    StaircaseResult,
    StopResult,
    UseBlockResult,
    UseItemResult,
    Vec3f,
    Vec3i,
    WalkResult,
    FineControlResult,
)
from .runtime import MinecraftRuntime


# =========================================================================
# Perception
# =========================================================================


class MinecraftTools:
    """Expose the frozen MCP contract through typed runtime calls."""

    def __init__(self, runtime: MinecraftRuntime):
        self.runtime = runtime

    def minecraft_observe(self, include_image: bool = True) -> ObserveResult:
        """Take a compact snapshot of your current situation.

        Nearby blocks and entities use a fixed {{OBSERVE_RADIUS_BLOCKS}}-block radius.
        The radius includes its boundary. Distance is Euclidean distance from
        your feet to a block-cell position or entity position.
        THE orientation tool. Start of every session, after any disorienting
        event (respawn, long walk, nightfall), and whenever you are unsure what
        is going on. The result contains your pose, vitals, inventory, nearby
        blocks, nearby entities, and a screenshot.

        WORLD BEHAVIOR:
            - Costs nothing and changes nothing. Pure read.
            - `nearby_blocks` is aggregated by type (name -> count + nearest
              cell). To locate a specific target use minecraft_find_block.
              It is also the quickest ore locator: entries report ore that
              find_block cannot see. Read the `nearest` cell of each entry.
            - Entities (mobs, dropped items, players) include their `entity_id`,
              which you need for minecraft_attack_entity.
            - `held_item` reports durability and max_durability. Tools break
              without further notice: check durability before you mine and
              carry spares.
            - Night, rain and biome are reported so you can plan (monsters,
              beds, farming).

        WHEN NOT TO USE:
            - You already know your pose and just need a target:
              use minecraft_find_block (fast, filtered, sorted).
            - You only need the inventory: results of craft/equip/mine calls
              already carry inventory deltas - no re-observe needed.

        Args:
            include_image: Attach the screenshot pixels (default). Set False to
                save tokens when you only need the numbers.

        Failure modes:
            - MCP error containing "player body" and "not available": the avatar
              is not connected or spawned. Wait, then retry. Nothing changed.

        See also: minecraft_find_block, minecraft_info
        """
        return self.runtime.minecraft_observe(include_image=include_image)


    def minecraft_find_block(
        self,
        pattern: str,
    ) -> FindBlockResult:
        """Find surface-exposed blocks near you.

        The workhorse for locating anything: trees, ores, stone, water, chests.
        Send a glob like "*log" for any log, "*_ore" for any ore, "grass_block"
        for the exact block.

        The horizontal distance is {{FIND_BLOCK_HORIZONTAL_BLOCKS}} blocks.
        The tool searches {{FIND_BLOCK_UP_BLOCKS}} blocks up and
        {{FIND_BLOCK_DOWN_BLOCKS}} blocks down. It returns at most
        {{FIND_BLOCK_RESULT_LIMIT}} blocks and applies a fixed diversity rule.

        A result needs one non-solid adjacent cell. It does not need line of
        sight from the player. Fully buried blocks never appear.

        EXPOSURE RULE (anti-x-ray):
            A block is findable when at least ONE of its six face-adjacent cells
            is non-solid (air, water, lava, torch, door, ... anything you can
            move through). This means:
            - Blocks fully buried in solid material are NEVER returned. This is
              deliberate anti-x-ray: you cannot scan for hidden diamonds.
              To mine buried ore, mine the adjacent stone first to expose it.
            - Blocks behind a wall or hill can appear. This compensates for
              the slow visual scan of an LLM.
            - No ray from your head is involved. This is why the call is fast
              (single-digit milliseconds) and never times out.
            - To LOCATE nearby ore that this tool cannot see, use
              minecraft_observe: each `nearby_blocks` entry carries the
              `nearest` {x, y, z} cell of that ore type.

        Results are nearest-first. `nearest` is the first result.

        Args:
            pattern: Glob pattern for the block name. Examples: "*log",
                "*_ore", "diamond_ore", "crafting_table", "*door*".

        Failure modes:
            - reason "not_found", candidates=None: pattern is a valid block
              name but no exposed instance is within the search bounds. Read `coverage`
              to see what was actually searched.
            - reason "not_found", candidates set: the pattern matched NO known
              block name at all (probably a typo). candidates holds the closest
              known names - re-call with one of them.
            - reason "ambiguous": reserved for multi-type reporting. This tool
              itself never fails this way (it returns across all matched types).

        Examples:
            find_block("*_ore")     -> nearby surface-exposed ores
            find_block("oak_log")   -> nearby surface-exposed oak logs
            find_block("*chest*")   -> nearby surface-exposed chests

        See also: minecraft_inspect_block, minecraft_find_interactables
        """
        return self.runtime.minecraft_find_block(pattern=pattern)


    def minecraft_inspect_block(
        self,
        position: Vec3i, include_image: bool = False
    ) -> InspectBlockResult:
        """Examine one block cell: its identity, its six neighbors, its drops.

        The microscope. Use before mining something risky, before building next
        to something, or whenever a find/mine/build result surprised you. It
        answers: what exactly is at this cell, is it exposed (and on which
        faces), what drops when harvested, which tool is fastest, and can my
        CURRENT held item get the drops at all.

        WORLD BEHAVIOR:
            - Pure read. Walks nothing, breaks nothing.
            - `neighbors` lists all six face-adjacent cells with their contents,
              so you can reason about collapses, lava behind walls, etc.
            - `can_harvest_with_held=False` means: breaking it will destroy the
              block but yield NO drops (wrong tool tier - e.g. stone with bare
              hands). Equip the right tool first; `best_tools` lists them
              fastest-first.

        Args:
            position: The cell to inspect.
            include_image: Attach a screenshot of the cell (default False).

        Failure modes:
            - reason "not_found": no block exists at the cell (or chunk not
              loaded). message says which.

        See also: minecraft_find_block, minecraft_mine_block
        """
        return self.runtime.minecraft_inspect_block(position=position, include_image=include_image)


    def minecraft_find_interactables(self, pattern: str = "*") -> FindInteractablesResult:
        """List right-clickable blocks near you: doors, chests, tables, beds...

        Perfect for finding entrances and usable furniture without knowing
        exact names: send "*" for everything, "*door*" for doors and trapdoors,
        "*chest*" for storage.

        The search distance is {{INTERACTABLE_RADIUS_BLOCKS}} blocks. It includes
        its boundary and uses block-cell distance from your feet. The result
        contains at most {{INTERACTABLE_RESULT_LIMIT}} blocks.

        Args:
            pattern: Glob on the block name. Default "*" matches all
                interactables.

        Failure modes:
            - reason "not_found": nothing matched within the search bounds.
            - reason "not_found", candidates set: pattern matched no known
              block name (typo) - candidates suggests corrections.

        See also: minecraft_use_block, minecraft_find_block
        """
        return self.runtime.minecraft_find_interactables(pattern=pattern)


    def minecraft_raytrace(self, include_image: bool = False) -> RaytraceResult:
        """Report the first block your view ray hits.

        Precise aiming: what am I looking at exactly, at which cell, on which
        face, at what distance. The range is {{RAYTRACE_DISTANCE_BLOCKS}} blocks.

        Use it after minecraft_rotate to make sure that your crosshair
        sits on the intended block (e.g. before a fine_control mining move).

        Args:
            include_image: Attach a screenshot with the crosshair (default
                False).

        Failure modes:
            - hit=False: the ray left the world or hit nothing within range
              (looking at the sky). Not an error.

        See also: minecraft_rotate, minecraft_inspect_block
        """
        return self.runtime.minecraft_raytrace(include_image=include_image)


    def minecraft_scan_horizon(self, include_image: bool = False) -> ScanHorizonResult:
        """Scan the full horizon for terrain and distant landmarks.

        The scan uses {{HORIZON_HEADING_COUNT}} compass headings. It uses the
        pitch angles {{HORIZON_PITCHES_DEGREES}}. Results are grouped by compass
        sector and include terrain, water, trees, lights, and path-like blocks.

        A landmark classification uses only raytraceable surface evidence.
        The tool never uses a Minecraft structure-location command. Treat a
        possible structure as a lead, not as proof.

        WORLD BEHAVIOR:
            - Pure read, no movement.
            - Use the scan to select a travel direction. Then call
              minecraft_walk_to_surface for a suitable target column.

        Args:
            include_image: Attach a screenshot. The numeric table usually suffices.

        See also: minecraft_walk_to_surface, minecraft_find_block
        """
        return self.runtime.minecraft_scan_horizon(include_image=include_image)


# =========================================================================
# Recipe book & crafting
# =========================================================================


    def minecraft_recipe_search(
        self,
        pattern: str = "*",
        craftable_now: bool | None = None,
    ) -> RecipeSearchResult:
        """Search the recipe book by glob - the catalogue of everything craftable.

        THE planning tool for crafting. Ask it what exists ("*pickaxe"), what
        you can afford RIGHT NOW (craftable_now=true), or what a specific item
        costs ("bed", "furnace"). Every entry includes the full ingredient list
        with have/missing counts, so you know exactly what to gather before
        you even try to craft.

        The result contains at most {{RECIPE_RESULT_LIMIT}} recipes.

        Args:
            pattern: Glob on the crafted item's name. Default "*" matches the
                whole recipe book.
            craftable_now: None (default) = report all matches regardless of
                inventory. True = only recipes you can craft right now (also
                checks crafting-table presence for 3x3 recipes). False = only
                recipes you currently CANNOT craft (shopping list).

        Failure modes:
            - reason "not_found", candidates set: pattern matched no known
              recipe (typo). `candidates` suggests the closest item names.

        Examples:
            recipe_search("*pickaxe")                    -> every pickaxe + costs
            recipe_search("*", craftable_now=True)       -> what can I make now
            recipe_search("iron_*")                      -> iron tool family

        See also: minecraft_craft_item
        """
        return self.runtime.minecraft_recipe_search(pattern=pattern, craftable_now=craftable_now)


    def minecraft_craft_item(self, item: str, repetitions: int = 1) -> CraftItemResult:
        """Craft items by exact name or glob, and report the inventory delta.

        Resolution order (first stop wins):
            1. Exact name matches a recipe            -> craft it.
            2. Glob matches exactly ONE recipe        -> craft it.
            3. Glob matches SEVERAL recipes           -> craft NOTHING,
               `candidates` lists the choices; re-call with one exact name.
               Example: craft("door") -> "oak_door or iron_door or ..."
            4. Nothing matches                        -> craft NOTHING,
               `candidates` lists the closest known names (typo help).
            5. Recipe resolved but ingredients short  -> craft NOTHING,
               `missing_ingredients` lists each item with required/have/missing.

        WORLD BEHAVIOR:
            - 2x2 recipes (planks, sticks, torches, crafting_table) craft from
              your inventory anywhere.
            - 3x3 recipes (tools, furnace, chest, bed, doors) need a crafting
              table within reach. When the ingredients are sufficient but no
              table is nearby, the call fails with reason
              "crafting_table_not_found": craft and place a table first
              (see minecraft_build), then retry. On success
              `crafting_table_used` names the table.
            - `repetitions` is recipe RUNS, not output items (crafting planks
              x4 gives 16 planks).
            - No image is ever attached; the inventory delta and hotbar are
              the outcome you care about.

        Args:
            item: Exact item name or glob, e.g. "oak_planks", "*pickaxe".
            repetitions: How many recipe runs, default 1.

        Failure modes (reason codes):
            - "ambiguous": glob matched several items - see candidates.
            - "not_found": unknown name - see candidates.
            - "missing_ingredients": see missing_ingredients list.
            - "crafting_table_not_found": 3x3 recipe, no table in range.

        Examples:
            craft_item("oak_planks", repetitions=4)   # 4 logs -> 16 planks
            craft_item("crafting_table")              # 4 planks -> 1 table
            craft_item("*sword")                      # -> candidates (which?)

        See also: minecraft_recipe_search, minecraft_equip
        """
        return self.runtime.minecraft_craft_item(item=item, repetitions=repetitions)


# =========================================================================
# Items, equipment, food, smelting
# =========================================================================


    def minecraft_equip(self, item: str) -> EquipResult:
        """Put an item from your inventory into your main hand.

        Exact name or glob, same resolution order as craft: unique match equips,
        several matches equip nothing and list candidates, unknown names list
        the closest known names.

        WHY THIS MATTERS: tools, blocks-to-place and food must be IN HAND
        before mine/use/pillar calls. After climb-y actions the held item can
        drift; this tool re-equips and VERIFIES the swap - `equipped` reports
        what is actually in hand afterwards, not what was requested.

        Args:
            item: Exact item name or glob, e.g. "wooden_pickaxe", "*pickaxe",
                "oak_planks".

        Failure modes:
            - reason "not_found": you do not own a matching item.
            - reason "ambiguous": several items match - see candidates.

        See also: minecraft_craft_item, minecraft_use_item
        """
        return self.runtime.minecraft_equip(item=item)


    def minecraft_use_item(self) -> UseItemResult:
        """Use the held item: eat food, drink potions/milk, throw eggs/pearls.

        RIGHT-CLICK with the hand. What happens depends on what you hold -
        the `action` field tells you which of ate/drank/threw/activated/nothing
        occurred. Food must be equipped first (minecraft_equip).

        WORLD BEHAVIOR:
            - Eating takes time; the call waits until the food is actually
              consumed and then reports the stat delta (food/hunger up, item
              count down).
            - reason "food_full" (message) with action "nothing": hunger is
              already maxed - the food was NOT consumed. Pick another action.
            - No image is ever attached; the stat delta is the outcome.

        Failure modes:
            - reason "no_held_item": your hand is empty. Equip first.
            - reason "not_usable": the held item has no use action.

        See also: minecraft_equip, minecraft_observe (check food level)
        """
        return self.runtime.minecraft_use_item()


    def minecraft_smelt_item(
        self,
        input: str,
        input_count: int = 1,
        fuel: str | None = None,
        fuel_count: int = 1,
    ) -> SmeltItemResult:
        """Smelt items in a nearby furnace, fully automatic.

        Finds a furnace within {{FURNACE_DISTANCE_BLOCKS}} blocks, clears stale
        slots, loads input and fuel, waits for the smelt, and returns the output
        to your inventory. The distance includes its boundary. It uses distance
        from your feet to the furnace block-cell position. The whole trip is one
        call.

        Args:
            input: Item name or glob to smelt, e.g. "raw_iron", "*raw_iron".
            input_count: How many to smelt, default 1.
            fuel: Fuel name or glob, default None = auto-pick best available
                (coal/charcoal > planks > logs > sticks).
            fuel_count: Fuel items to burn, default 1. One coal smelts 8 items.

        Failure modes:
            - reason "furnace_not_found": no furnace is within
              {{FURNACE_DISTANCE_BLOCKS}} blocks. Craft
              and place one (see minecraft_craft_item / minecraft_build).
            - reason "missing": short on input or fuel - see `missing` list.
            - reason "ambiguous": input/fuel glob matched several items.
            - reason "target_changed": the furnace disappeared after work started.

        See also: minecraft_recipe_search, minecraft_craft_item
        """
        return self.runtime.minecraft_smelt_item(input=input, input_count=input_count, fuel=fuel, fuel_count=fuel_count)


# =========================================================================
# Changing the world: mine and build
# =========================================================================


    def minecraft_mine_block(self, position: Vec3i) -> MineBlockResult:
        """Mine one block at absolute coordinates.

        The body walks into range and digs with the held item.
        The fixed action limit is {{MINE_BLOCK_SECONDS}} seconds.

        LOOT DELIVERY:
            Babymode inserts normal mined loot directly into your
            inventory. Only overflow that does not fit drops at the block
            cell. When pickup.picked_up is False, walk to the position in
            `drop_hint` to collect the overflow.
            Verify `inventory_delta`, not block removal alone.

        BEFORE YOU DIG - two checks worth doing:
            - minecraft_inspect_block tells you `can_harvest_with_held`. If
              False, the block will break but drop NOTHING (wrong tool tier).
            - NEVER mine the block directly under your feet without a plan:
              you fall, possibly into lava or a cave. Mine ahead or staircase.
            - Tools can break mid-action and the held item can drift. Check
              `warnings` in the result, then re-equip with minecraft_equip
              before the next dig.

        Args:
            position: The exact block cell to mine.

        Failure modes:
            - reason "not_found": no block at that cell.
            - reason "unharvestable": held tool cannot get drops (see
              message for the required tool. Equip it, then retry.
            - reason "target_out_of_range" / "no_path": the body did not get close
              enough. Walk closer first.
            - reason "target_changed": another actor replaced the block after
              mining started. The replacement remains unchanged.

        See also: minecraft_inspect_block, minecraft_equip
        """
        return self.runtime.minecraft_mine_block(position=position)


    def minecraft_build(
        self,
        shape: Literal[
            "fill", "shell", "wall", "floor", "ceiling", "column", "staircase",
            "bridge", "frame",
        ],
        material: str,
        start: Vec3i,
        end: Vec3i | None = None,
        ref: Vec3i | None = None,
        include_image: bool = False,
    ) -> BuildResult:
        """Build a structure programmatically - no aiming, no per-block walking.

        THE building tool. You describe a SHAPE between two corner cells made
        of a MATERIAL, and the bot spawns those blocks directly (server-assisted
        placement). This replaces the old place_block: no reference blocks, no
        face vectors, no jump-placing, no 171 calls for one house.

        A build always consumes inventory blocks and preserves solid cells.
        The build distance is {{BUILD_DISTANCE_BLOCKS}} blocks from your feet
        to each block-cell position. It includes its boundary. One call affects at most
        {{BUILD_CELL_LIMIT}} cells.

        COORDINATES:
            `start`/`end` are absolute cells, OR offsets relative to `ref` when
            you pass `ref`. Example: ref=(10,64,60), start=(0,0,0), end=(0,3,10)
            builds between absolute (10,64,60) and (10,67,70) - a wall 1 thick,
            4 high, 11 long. `end` defaults to `start` (single block/column
            start cell).

        SHAPES (cells chosen from the start..end bounding box, /fill style):
            - fill       solid box, every cell.
            - shell      hollow box: floor, ceiling and all four walls - a
                         room/house in ONE call.
            - wall       the four vertical side faces of the box (no floor/
                         roof). For a single flat wall give the box 1 thickness.
            - floor      bottom face of the box.
            - ceiling    top face of the box.
            - column     1x1 vertical run from start up/down to end (end
                         defaults to start: places one block).
            - staircase  steps from start to end, rising 1 per horizontal
                         block - safe descent/ascent, never straight down.
            - bridge     horizontal walkway from start to end (1 wide) plus
                         optional 1-high side walls for safety.
            - frame      only the 12 edges of the box.

        MATERIAL RESOLUTION (same rule as craft):
            exact name -> use it. Glob with ONE match -> use it. A glob with
            SEVERAL matches (e.g. "*log" -> oak_log, spruce_log, birch_log) ->
            place NOTHING and return candidates - re-call with the exact name.
            Nothing matches -> candidates suggests closest names.

        PARTIAL RESULT:
            `ok` is True only when every planned cell was placed. Otherwise,
            `ok` is False and `reason` is "partial". The result lists:
            - occupied: cells that already contain a solid block.
            - out_of_range: cells outside the fixed build distance.
            - missing_material_cells: you ran out of material.

            A build always consumes inventory materials. It never replaces a
            solid block. Test setup uses a separate admin interface.
            Re-calling build on the same region is cheap: finished cells
            come back in `occupied`, only the gaps get filled.

        Args:
            shape: One of the shape keywords above.
            material: Exact block name or glob, e.g. "oak_planks", "*log".
            start: First corner cell (absolute, or offset when ref is given).
            end: Second corner cell (defaults to start).
            ref: Optional reference point. If set, start/end are offsets
                relative to it.
            include_image: Attach an after-build screenshot (default False).

        Failure modes:
            - reason "ambiguous" / "not_found": material resolution - see
              candidates.
            - reason "out_of_range" (all cells): bot too far from the whole
              region.
            - reason "cell_limit": the shape contains more than
              {{BUILD_CELL_LIMIT}} cells. Nothing is placed or consumed.
            - reason "partial": read occupied, out_of_range, and
              missing_material_cells to see what remains.

        Examples:
            build("shell", "oak_planks", ref=(10,64,60), start=(-3,0,-3),
                  end=(3,4,3))              # 7x5x7 hut shell, one call
            build("wall", "*log", start=(100,64,200), end=(100,66,210))
            build("staircase", "cobblestone", start=(0,64,0),
                  end=(10,54,0))            # dig-safe descent

        See also: minecraft_mine_block, minecraft_recipe_search
        """
        return self.runtime.minecraft_build(shape=shape, material=material, start=start, end=end, ref=ref, include_image=include_image)


# =========================================================================
# Movement & camera
# =========================================================================


    def minecraft_rotate(
        self,
        yaw_degrees: float = 0.0,
        pitch_degrees: float = 0.0,
        absolute: bool = False,
    ) -> RotateResult:
        """Turn the view and receive the new world transform plus a screenshot.

        Turning is how you SEE the world: each rotation returns the complete
        new camera pose (position, yaw, pitch, cardinal, look vector) and an
        image from the new direction. Chain rotate -> raytrace/observe to aim.

        CONVENTIONS:
            - Relative by default: yaw_degrees/pitch_degrees are DELTAS from
              the current view. Positive yaw turns RIGHT, positive pitch looks
              UP.
            - absolute=True interprets them as target angles: yaw 0=south(+Z),
              90=west(-X), 180=north(-Z), 270=east(+X); pitch +90=straight up.

        Args:
            yaw_degrees: Horizontal turn in degrees (right positive).
            pitch_degrees: Vertical tilt in degrees (up positive).
            absolute: Treat the values as absolute target angles (default
                False = relative deltas).

        Failure modes:
            - MCP error containing "player body" and "not available": the avatar
              is not connected or spawned.

        See also: minecraft_raytrace, minecraft_observe
        """
        return self.runtime.minecraft_rotate(yaw_degrees=yaw_degrees, pitch_degrees=pitch_degrees, absolute=absolute)


    def minecraft_fine_control(
        self,
        forward: bool = False,
        back: bool = False,
        left: bool = False,
        right: bool = False,
        jump: bool = False,
        sneak: bool = False,
        sprint: bool = False,
    ) -> FineControlResult:
        """Hold raw walk keys for a short time - the last-meter nudging tool.

        For adjustments too small or too weird for pathfinding: step onto a
        block, shuffle sideways along a ledge, hop onto a stair. The body holds
        exactly the keys you set for {{FINE_CONTROL_MILLISECONDS}} ms. It then stops and reports the
        pose before/after plus a screenshot.

        WORLD BEHAVIOR:
            - Movement is in YOUR current view frame: forward = where you
              face (rotate first!), left/right strafe. Turn before you nudge.
            - You can and will walk off edges with forward - that is what
              sneak is for (edge-safe walking).
            - This is not for travel. Use the walk tools. Fine control past
              a few blocks wastes calls.

        Args:
            forward/back/left/right: Movement keys, false default.
            jump: Hold jump (also auto-jumps 1-block steps while walking).
            sneak: Hold sneak (slower, does not fall off edges).
            sprint: Hold sprint (needs forward).

        Failure modes:
            - MCP error containing "player body" and "not available": the avatar
              is not connected or spawned.

        See also: minecraft_rotate, minecraft_walk_to_exact
        """
        return self.runtime.minecraft_fine_control(forward=forward, back=back, left=left, right=right, jump=jump, sneak=sneak, sprint=sprint)


    def minecraft_pillar_up(
        self,
        count: Annotated[int, Field(ge=1, le=PILLAR_UP_BLOCK_LIMIT)] = 1,
    ) -> PillarUpResult:
        """Ascend mechanically by placing held blocks at your feet.

        This server-assisted action places a block directly in your current
        feet cell and moves you one block up. It repeats up to `count` times,
        stopping before fewer than two clear player cells remain. The default
        is one block and one call is capped at {{PILLAR_UP_BLOCK_LIMIT}}.

        Args:
            count: Maximum blocks to ascend, default 1, maximum
                {{PILLAR_UP_BLOCK_LIMIT}}.

        WORLD BEHAVIOR:
            - Uses the currently HELD placeable block and consumes it.
            - Reports the consumed block in inventory_delta - watch your
              supply when towering high.
            - To get DOWN safely: build a staircase (minecraft_build) or mine
              the tower from the top - never drop blindly.

        Failure modes:
            - reason "no_held_item" / "not_placeable": equip a solid block.
            - reason "no_headroom": two clear player cells are not available.

        See also: minecraft_build, minecraft_equip
        """
        return self.runtime.minecraft_pillar_up(count=count)


    def minecraft_walk_to_visible(self, x: float, y: float, z: float) -> WalkResult:
        """Walk to a spot near a position you can see.

        Use this tool for local cave movement and nearby visible targets. It
        uses a small local A* search and fails quickly at a large barrier.
        It never expands the search across the complete render distance.
        The local search distance is {{LOCAL_PATH_DISTANCE_BLOCKS}} blocks from
        your feet to the requested point. It includes its boundary.
        The fixed action limit is {{VISIBLE_WALK_SECONDS}} seconds.

        The body finds a standable cell near the target. It ends adjacent to
        an occupied target, ready to mine or use it.

        Args:
            x, y, z: The visible target point (floats fine).

        Failure modes:
            - reason "no_path": no walkable route (water, cliff, wall). Scan
              the horizon (minecraft_scan_horizon) and pick a different
              approach, or bridge (minecraft_build).
            - reason "timeout": ran out of time - status "partial" tells you
              how close you got. Call the tool again to continue.

        See also: minecraft_walk_to_surface, minecraft_walk_to_exact
        """
        return self.runtime.minecraft_walk_to_visible(x=x, y=y, z=z)


    def minecraft_walk_to_surface(self, x: float, z: float) -> WalkResult:
        """Travel to the surface above a column (x, z), over any distance.

        Use this tool for long travel above ground. The body selects a
        standable cell within a small ring around the target column and
        walks to that exact cell. It walks in bounded segments and
        recalculates each local path. Physical movement loads new chunks.
        The fixed action limit is {{SURFACE_WALK_SECONDS}} seconds.

        The local search permits generous detours (cave exits, staircases)
        inside a fixed corridor around the direct line. When no route
        exists, walk up the ramp yourself with minecraft_walk_to_visible,
        or mine/pillar your way up.

        Args:
            x, z: Target column.

        Failure modes:
            - reason "no_path" / "timeout": the route is blocked or too long.
              status/message tell you how far you got. Continue by re-calling.
            - reason "pillar_up_required": the bot reached the bottom of an
              open shaft. final_position is the place to walk to before using
              minecraft_pillar_up.
            - reason "no_standable_surface": no standable ground near the
              target column (ocean, lava lake).

        See also: minecraft_walk_to_visible, minecraft_scan_horizon
        """
        return self.runtime.minecraft_walk_to_surface(x=x, z=z)


    def minecraft_walk_to_exact(
        self,
        x: float,
        y: float,
        z: float,
    ) -> WalkResult:
        """Walk to one known, standable target cell.

        Use this tool only for a known reachable destination. Examples include
        a saved house entrance, tunnel mouth, or farm plot. The body can travel
        for a long time and recalculates bounded path segments during travel.

        Pathfinder reaches the target cell and the tool accepts a final
        position within {{EXACT_WALK_TOLERANCE_BLOCKS}} blocks of the requested
        coordinate. The fixed action limit is {{EXACT_WALK_SECONDS}} seconds.

        Give block-cell coordinates, for example (4302, 64, -411).

        Args:
            x, y, z: Exact target point.

        Failure modes:
            - reason "target_not_standable": the cell is occupied/liquid -
              message describes what is in the way.
            - reason "no_path" / "timeout": as with the other walk tools.

        See also: minecraft_walk_to_visible, minecraft_fine_control
        """
        return self.runtime.minecraft_walk_to_exact(x=x, y=y, z=z)


# =========================================================================
# Interacting with blocks and containers
# =========================================================================


    def minecraft_use_block(self, position: Vec3i) -> UseBlockResult:
        """Right-click a block: open doors, chests, tables; press buttons.

        The universal activation. A door toggles open/closed (call again to
        close), a chest opens (returns its full contents in `window`), a
        crafting table opens (enables 3x3 crafting), buttons/levers trigger.

        Args:
            position: The interactable block's cell.

        Failure modes:
            - reason "not_found": no block at the cell.
            - reason "not_interactable": the block has no use action.
            - reason "out_of_range": stand closer first.

        See also: minecraft_find_interactables, minecraft_chest_deposit
        """
        return self.runtime.minecraft_use_block(position=position)


    def minecraft_chest_deposit(
        self,
        item: str, count: int | None = None, chest: Vec3i | None = None
    ) -> ChestMoveResult:
        """Move items from your inventory into a container.

        Uses the currently open window (opened via minecraft_use_block), or
        opens `chest` itself when you pass its cell.

        Args:
            item: Exact item name or glob to move.
            count: How many; None (default) = all matching.
            chest: Optional chest/barrel cell to open when nothing is open.

        Failure modes:
            - reason "no_chest_window": nothing open and no chest given.
            - reason "ambiguous" / "not_found": item resolution - candidates.
            - reason "insufficient": you own fewer than requested; message
              says how much was moved instead.
            - reason "target_changed": the container disappeared during transfer.

        See also: minecraft_chest_withdraw, minecraft_use_block
        """
        return self.runtime.minecraft_chest_deposit(item=item, count=count, chest=chest)


    def minecraft_chest_withdraw(
        self,
        item: str, count: int | None = None, chest: Vec3i | None = None
    ) -> ChestMoveResult:
        """Take items from a container into your inventory.

        Mirror of minecraft_chest_deposit: open window or pass `chest`.

        Args:
            item: Exact item name or glob to take.
            count: How many; None (default) = all the container holds.
            chest: Optional chest/barrel cell to open when nothing is open.

        Failure modes:
            - reason "no_chest_window": nothing open and no chest given.
            - reason "ambiguous" / "not_found": item resolution - candidates.
            - reason "insufficient": container holds fewer than requested.
            - reason "inventory_full": your inventory has no output slot.
            - reason "target_changed": the container disappeared during transfer.

        See also: minecraft_chest_deposit, minecraft_use_block
        """
        return self.runtime.minecraft_chest_withdraw(item=item, count=count, chest=chest)


    def minecraft_attack_entity(self, entity_id: int) -> AttackEntityResult:
        """Attack an entity until it dies or the hit budget runs out.

        Get `entity_id` from minecraft_observe (nearby_entities). The body
        swings with the held weapon and re-approaches as the target moves.
        Mob loot is normal ground pickup: the body does NOT collect it.
        Walk over the drops afterward. Fighting at low health is a bad
        idea - eat first.
        The fixed swing limit is {{ATTACK_HIT_LIMIT}} hits.

        Args:
            entity_id: Server id of the target (from observe).

        Failure modes:
            - reason "entity_not_found": it died, despawned or moved out of
              loaded range.
            - ok=True, killed=False: hit budget exhausted while it still
              lives. `entity_health_remaining` says how close you got. Read
              your own `self_damage_taken` and consider retreating/eating.

        See also: minecraft_observe, minecraft_use_item (eat)
        """
        return self.runtime.minecraft_attack_entity(entity_id=entity_id)


# =========================================================================
# Admin, memory & skills
# =========================================================================


    def minecraft_stop(
        self,
        scope: Literal["command", "skill", "both"] = "both"
    ) -> StopResult:
        """Emergency halt. Stops physical movement and/or a running skill.

        Use whenever anything moves that you did not ask for, or before you
        replan mid-task.

        Args:
            scope: "command" stops only the current walk/dig/controls;
                "skill" only the running skill process; "both" (default)
                everything.

        See also: minecraft_execute_typescript
        """
        return self.runtime.minecraft_stop(scope=scope)


    def minecraft_remember(self, kind: Literal[
        "world", "places", "routes", "chests", "failures", "journal"
    ], markdown: str) -> RememberResult:
        """Append a durable note to this character's memory.

        Memory and waypoints survive restarts. Use memory for facts you want
        tomorrow: base coordinates, chest locations, ore veins, lessons from
        failures, daily journal. Keep notes short and coordinate-rich.

        Args:
            kind: Category - world (general), places (coordinates of things),
                routes (how to get places), chests (storage locations +
                contents), failures (what went wrong + lesson), journal
                (chronological log).
            markdown: The note itself. Include coordinates, dimension, and
                uncertainty explicitly.

        See also: minecraft_add_waypoint
        """
        return self.runtime.minecraft_remember(kind=kind, markdown=markdown)


    def minecraft_add_waypoint(
        self,
        description: str, position: Vec3i | None = None
    ) -> AddWaypointResult:
        """Save a persistent place here or at a given cell.

        Use a place for an entrance, base, staircase, ore vein, or death site.
        Places survive restarts. The capacity is {{WAYPOINT_CAPACITY}} places.
        If the list is full, the oldest place is evicted and reported.

        Args:
            description: What this waypoint marks.
            position: Cell to save. None uses your current cell.

        See also: minecraft_list_waypoints, minecraft_remember
        """
        return self.runtime.minecraft_add_waypoint(description=description, position=position)


    def minecraft_list_waypoints(self) -> ListWaypointsResult:
        """List persistent places, oldest first.

        The capacity is {{WAYPOINT_CAPACITY}} places.

        See also: minecraft_add_waypoint
        """
        return self.runtime.minecraft_list_waypoints()


    def minecraft_execute_typescript(
        self,
        path: str,
        postcondition: dict,
        arguments: dict | None = None,
    ) -> ExecuteSkillResult:
        """Run a TypeScript skill file in the world - the multi-step escape hatch.

        Use this tool for long deterministic behavior. Examples include cave
        exploration, village searches, and large building tasks.

        The skill runs in a separate process. It receives only the approved
        survival API. It cannot access the Mineflayer bot, chat commands, raw
        packets, the filesystem, processes, networking, or the full world cache.
        Each API call uses the same limits as its MCP tool.

        The process sends progress heartbeats. The fixed action limit is
        {{SKILL_SECONDS}} seconds. The postcondition decides success from the
        observed state after execution.

        OUTPUT VISIBILITY:
            The return value of the skill is NOT part of the result. You
            see only execution metadata and the postcondition verdict. To
            read data inside a skill, call console.log(...) - the output
            appears in `stdout_tail`. Use the postcondition as the real
            verification gate (for example: inventory_min raw_iron 8).

        Args:
            path: Skill file under drafts/ or skills/ (see
                minecraft_list_capabilities).
            postcondition: One spec or {"all": [...]} combining several.
                Kinds: inventory_min, inventory_delta_min, y_min, y_max,
                health_min, position_changed_min, distance_max, held_item,
                entity_id_absent, block_at.
            arguments: Extra inputs for the skill, if it accepts any.

        Failure modes:
            - reason "skill_not_found": bad path.
            - reason "timeout": killed at the budget - stdout_tail shows
              progress. The postcondition can still pass if the skill finished
              in time.
            - reason "postcondition_failed": the skill ended without its goal.
            - reason "typescript_error": the skill code threw an error.
            - reason "access_denied": the skill requested an API outside the
              approved survival boundary, or the path left drafts/ and skills/.

        See also: minecraft_list_capabilities, minecraft_stop
        """
        return self.runtime.minecraft_execute_typescript(path=path, postcondition=postcondition, arguments=arguments)


    def minecraft_list_capabilities(self) -> ListCapabilitiesResult:
        """List the reusable TypeScript skills available to execute_typescript.

        Use an existing skill when its contract matches the goal. Each entry
        gives its purpose, arguments, required items, stopping conditions, and
        postconditions. Skills can call only the approved survival API.

        See also: minecraft_execute_typescript
        """
        return self.runtime.minecraft_list_capabilities()


    def minecraft_info(self) -> InfoResult:
        """Identity, connection state and workspace layout of this character.

        Confirms who you are, whether the body is connected and spawned, how
        many deaths you have suffered, and where drafts/skills/memory live.
        Call when something feels off with the connection.

        See also: minecraft_observe
        """
        return self.runtime.minecraft_info()


    def minecraft_suicide(self, reason: str) -> RespawnResult:
        """Kill this avatar to respawn at world spawn - the last escape.

        Use this tool after the bot traps itself underground and cannot escape.
        A common cause is a broken pickaxe after digging straight down. After
        respawn, build a staircase and do not repeat the failed dig.

        Everything in the inventory drops at the death position. Persistent
        places and memory survive. Babymode can reset sleepiness and nutrition
        after death, so the result records every use for later audits.

        Args:
            reason: Short note recorded in the journal.

        See also: minecraft_remember, minecraft_add_waypoint
        """
        return self.runtime.minecraft_suicide(reason=reason)


# =========================================================================
# Coordinate math helpers
# =========================================================================


    def minecraft_relative(
        self,
        forward: int = 0, right: int = 0, up: int = 0
    ) -> RelativePositionResult:
        """Convert a facing-relative offset into an absolute block cell.

        THE anti-arithmetic tool. "Three blocks in front of me and one up"
        becomes relative(forward=3, up=1) -> the exact world cell, computed
        from your CURRENT yaw. Offsets are in your view frame: forward = where
        you face, right = your right hand side, up = sky.

        WHY THIS EXISTS: models doing 3D arithmetic in their heads get
        off-by-one cells constantly, then guess coordinates until
        block_not_found. One call makes it exact.

        Args:
            forward: Blocks ahead of you (negative = behind).
            right: Blocks to your right (negative = left).
            up: Blocks upward (negative = down).

        Examples:
            relative(forward=3, up=1)     # the cell to mine ahead and above
            relative(forward=1)           # the cell under my next step

        See also: minecraft_distance, minecraft_look_at
        """
        return self.runtime.minecraft_relative(forward=forward, right=right, up=up)


    def minecraft_distance(self, a: Vec3f, b: Vec3f) -> DistanceResult:
        """Distance between two points, with per-axis breakdown.

        Pure math helper, no world access. "Is that within my 32-block build
        range?" "How far is the chest?" - answer in one call instead of mental
        arithmetic. Returns Euclidean and Manhattan distance plus the per-axis
        deltas so you can also reason about direction.

        Args:
            a: First point.
            b: Second point.

        See also: minecraft_relative, minecraft_find_path
        """
        return self.runtime.minecraft_distance(a=a, b=b)


    def minecraft_look_at(self, position: Vec3f) -> RotateResult:
        """Aim the view at a world point - rotate without doing the math.

        Shortcut over minecraft_rotate: give the absolute point you want in
        your crosshair (block center, an entity, a distant hill) and the view
        turns there. Returns the new world transform plus a screenshot, same
        as rotate.

        Args:
            position: The point to look at (block centers are x.5/z.5).

        Failure modes:
            - reason "same_position": the target equals the current eye position.

        See also: minecraft_rotate, minecraft_raytrace
        """
        return self.runtime.minecraft_look_at(position=position)


    def minecraft_screenshot(self) -> ScreenshotResult:
        """Capture the current view - a pure vision refresh.

        Cheaper than minecraft_observe when you only want eyes, not state:
        after a fine_control nudge, or to check whether monsters appeared.

        See also: minecraft_observe
        """
        return self.runtime.minecraft_screenshot()


# =========================================================================
# Composite world actions
# =========================================================================


    def minecraft_mine_vein(self, block: str) -> MineVeinResult:
        """Mine an entire CONNECTED ore vein as one action.

        The tool finds the nearest exposed matching ore. It mines connected ore
        of the same type until the vein ends or reaches the fixed limit.
        The fixed limit is {{MINE_VEIN_BLOCK_LIMIT}} blocks.

        LOOT DELIVERY:
            Babymode inserts normal mined loot directly into your inventory.
            Only overflow drops at the mined cells. Verify `mined_count` AND
            `inventory_delta`: the mined count alone does not prove loot
            delivery. Check `warnings` for tool loss or held-item drift, then
            re-equip with minecraft_equip before the next action.

        WORLD BEHAVIOR:
            - The tool starts from surface-exposed ore (anti-x-ray). Mining
              can reveal the connected interior ore during the action. To
              LOCATE buried ore first, use minecraft_observe: each
              `nearby_blocks` entry carries the `nearest` {x, y, z} cell.
            - Stops safely at hazards (lava/water pockets are reported, not
              swum through).

        Args:
            block: Ore name or glob, e.g. "iron_ore", "*_ore", "diamond_ore".

        Failure modes:
            - reason "not_found": no exposed matching ore in range.
            - reason "ambiguous": glob matched several ore types - see
              candidates and re-call with an exact name.

        See also: minecraft_mine_block, minecraft_find_block, minecraft_observe
        """
        return self.runtime.minecraft_mine_vein(block=block)


    def minecraft_harvest_tree(self, base: Vec3i | None = None) -> HarvestTreeResult:
        """Chop one whole tree: trunk and reachable branches, collect drops.

        Give the base log cell, or omit it to auto-find the nearest tree. The
        body climbs/chops until the tree is gone. Babymode inserts normal
        mined loot directly into your inventory; only overflow drops.
        Leaf-decay drops are normal ground pickup - walk over them.
        One call replaces the chop-walk-chop loop. Verify
        `logs_collected` and `inventory_delta`, not the block removal
        alone.

        Args:
            base: Cell of the lowest trunk block; None = auto-find nearest.

        Failure modes:
            - reason "not_found": no tree nearby when auto-finding.
            - reason "not_a_tree": the given cell is not part of a tree.

        See also: minecraft_mine_vein, minecraft_equip
        """
        return self.runtime.minecraft_harvest_tree(base=base)


    def minecraft_craft_max(self, item: str, limit: int | None = None) -> CraftMaxResult:
        """Craft as many of an item as your materials allow.

        The batch-crafting tool: instead of failing on missing ingredients,
        it crafts the maximum possible count and reports what is still
        short for more. Perfect for "turn all these logs into planks" or
        "make as many torches as possible".

        When several recipe variants exist, the tool selects the variant
        that yields the most output from your current ingredients and
        table presence.

        Args:
            item: Exact item name or glob.
            limit: Optional cap on OUTPUT ITEMS, not recipe runs
                (None = as many as possible).

        Failure modes (a crafted=0 result always carries a reason):
            - reason "ambiguous" / "not_found": name resolution - candidates.
            - reason "not_craftable": the item has no recipe.
            - reason "limit_below_output": the cap is below one recipe's
              output.
            - reason "missing_ingredients": crafted=0 - read still_missing
              for the shopping list.
            - reason "crafting_table_not_found": 3x3 recipe, no table in
              range. Place one, then retry.

        See also: minecraft_craft_item, minecraft_recipe_search
        """
        return self.runtime.minecraft_craft_max(item=item, limit=limit)


    def minecraft_equip_best_tool(self, target: Vec3i) -> EquipBestToolResult:
        """Auto-equip the fastest suitable tool you own for a block.

        Inspects the block at `target`, ranks YOUR tools by harvest speed and
        tier, equips the best one. Kills the whole inspect -> craft -> equip
        -> retry dance in one call. When nothing you own is adequate,
        `best_possible_tool` names the tool to CRAFT next.

        Args:
            target: Cell of the block you want to mine.

        Failure modes:
            - reason "not_found": no block at the cell.
            - reason "unharvestable": no tool can harvest this block.

        See also: minecraft_equip, minecraft_craft_item
        """
        return self.runtime.minecraft_equip_best_tool(target=target)


    def minecraft_eat_best(self) -> EatBestResult:
        """Eat the best food you carry: most hunger restored, least waste.

        Picks from your inventory automatically - no equipping needed.
        `considered` lists the foods that were evaluated, so you also learn
        your options.

        Failure modes:
            - reason "no_food": nothing edible in your inventory.
            - reason "food_full": hunger already maxed (nothing consumed).

        See also: minecraft_use_item
        """
        return self.runtime.minecraft_eat_best()


    def minecraft_staircase_down(
        self,
        depth: int = 8, torch: bool = True
    ) -> StaircaseResult:
        """Carve a safe descending staircase - never straight down.

        Encodes the survival rule as a primitive: digs a staircase with proper
        headroom at your feet, optionally placing torches, descending `depth`
        blocks. The dig STOPS safely when it hits a hazard (lava/water pocket
        is reported, not breached).

        Args:
            depth: How deep to descend, default 8.
            torch: Place torches for light as you go (default True).

        Failure modes:
            - ok=True with depth_achieved < depth_requested: stopped at a
              hazard - read hazards_found before continuing.
            - Check `warnings` for tool loss or held-item drift. Carry
              spare tools; re-equip before the next dig.

        See also: minecraft_build (shape="staircase"), minecraft_is_safe_to_dig
        """
        return self.runtime.minecraft_staircase_down(depth=depth, torch=torch)


    def minecraft_fill_from_inventory(
        self,
        shape: Literal["fill", "wall", "floor", "column"],
        start: Vec3i,
        end: Vec3i | None = None,
        ref: Vec3i | None = None,
    ) -> BuildResult:
        """Fill a region with whatever placeable blocks you carry - most
        abundant first.

        The "use up this cobble" companion to minecraft_build: material
        identity does not matter, just volume. Consumes from your inventory
        until the shape is complete or you run out (see
        missing_material_cells).

        Args:
            shape: fill / wall / floor / column (see minecraft_build for the
                shape semantics).
            start: First corner cell (or offset when ref is given).
            end: Second corner cell (defaults to start).
            ref: Optional reference point; start/end are offsets relative to
                it when set.

        See also: minecraft_build, minecraft_count_inventory
        """
        return self.runtime.minecraft_fill_from_inventory(shape=shape, start=start, end=end, ref=ref)


    def minecraft_sleep(self, bed: Vec3i | None = None) -> SleepResult:
        """Sleep in a bed to skip the night.

        Uses the given bed, or the nearest one in range. When monsters are
        nearby the vanilla bed rule blocks sleep - the blocking mob is
        returned so you can deal with it and retry.

        Args:
            bed: Bed cell to sleep in; None = nearest bed in range.

        Failure modes:
            - reason "no_bed": no bed within range.
            - reason "not_night": the vanilla sleep window is not active.
            - reason "bed_occupied": another player occupies the bed.
            - reason "bed_obstructed": a solid block prevents bed use.
            - reason "out_of_range": the specified bed is too far away.
            - ok=True, slept=False, blocking_entity set: monsters nearby.

        See also: minecraft_observe (is_day)
        """
        return self.runtime.minecraft_sleep(bed=bed)


    def minecraft_drop_item(
        self,
        item: str, count: int | None = None
    ) -> DropResult:
        """Toss items out of your inventory.

        WARNING - READ FIRST: dropped items land at your feet. Normal
        ground pickup collects them again when you walk over them, so
        dropping is ONLY useful to hand items to another player standing
        there. To DESTROY trash use minecraft_discard_items - it never
        creates a drop entity.

        Args:
            item: Exact item name or glob to drop.
            count: How many; None (default) = the whole matching stack(s).

        Failure modes:
            - reason "not_found": you own no matching item.
            - reason "ambiguous": several items match - see candidates.

        See also: minecraft_discard_items
        """
        return self.runtime.minecraft_drop_item(item=item, count=count)


    def minecraft_discard_items(
        self,
        item: str, count: int | None = None
    ) -> DiscardResult:
        """Destroy items outright - the trash can.

        Removes matching items from your inventory directly via the
        server-assisted channel (the same mechanism minecraft_build uses to
        place blocks): no drop entity is ever created, so nothing can be
        picked back up. The lava-choreography problem does not exist here.

        This is a deliberate hygiene cheat: it only ever touches items you
        explicitly named, never equipment or containers.

        Args:
            item: Exact item name or glob of the trash, e.g. "rotten_flesh",
                "dirt", "*sapling".
            count: How many to destroy; None (default) = ALL matching. A
                safety count is wise for shared materials.

        Failure modes:
            - reason "not_found": you own nothing matching; candidates lists
              your closest owned item names (typo help).
            - reason "ambiguous": several items match - see candidates.

        Examples:
            discard_items("rotten_flesh")            # burn all the zombie loot
            discard_items("dirt", count=20)          # keep some, toss the rest

        See also: minecraft_drop_item, minecraft_count_inventory
        """
        return self.runtime.minecraft_discard_items(item=item, count=count)


# =========================================================================
# Perception & planning extras
# =========================================================================


    def minecraft_count_inventory(self, pattern: str = "*") -> CountResult:
        """Count items in your inventory by glob - "do I have 64 planks?"

        Pre-flight check for builds and crafts, cheaper than a full observe.
        Matches are listed most-numerous-first with exact counts.

        Args:
            pattern: Glob on item names, default "*" = everything.
                Item names differ from block names: mining stone gives
                cobblestone, mining iron_ore gives raw_iron. Count
                "cobblestone" or "*stone*", not "stone".

        Failure modes:
            - reason "not_found": nothing matches (candidates may suggest).

        See also: minecraft_recipe_search, minecraft_build
        """
        return self.runtime.minecraft_count_inventory(pattern=pattern)


    def minecraft_analyze_area(self, start: Vec3i, end: Vec3i) -> AreaReportResult:
        """Count raytraceable blocks in a nearby rectangular region.

        This tool reports only cells that have a clear ray from your eyes
        through non-solid blocks. It never reports blocks hidden by terrain.
        Use it to estimate visible building work or exposed materials.

        The full region must fit inside the fixed local bounds. The horizontal
        distance is {{VISIBLE_AREA_HORIZONTAL_BLOCKS}} blocks. The upward distance
        is {{VISIBLE_AREA_UP_BLOCKS}} blocks. The downward distance is
        {{VISIBLE_AREA_DOWN_BLOCKS}} blocks. These inclusive cell offsets use the
        cell that contains your feet as their origin.

        Args:
            start: First corner cell.
            end: Second corner cell (defaults handled as inclusive bounds).

        Failure modes:
            - reason "out_of_range": one or more cells are outside the fixed
              local bounds. No cell is analyzed.

        See also: minecraft_find_block, minecraft_is_safe_to_dig
        """
        return self.runtime.minecraft_analyze_area(start=start, end=end)


    def minecraft_find_path(self, x: float, y: float, z: float) -> PathPreviewResult:
        """Preview a bounded local path without movement.

        Use this tool to compare local walking with a bridge or staircase.
        The search distance is {{LOCAL_PATH_DISTANCE_BLOCKS}} blocks. The tool
        does not preview a complete long-range route.

        The result state is reachable, blocked, or unknown. Unknown means that
        the fixed search budget ended. It does not mean that no path exists.

        Args:
            x, y, z: The target point.

        Failure modes:
            - state "blocked": a known obstacle prevents the local route.
            - state "unknown": the fixed search budget ended.

        See also: minecraft_walk_to_visible, minecraft_build (bridge)
        """
        return self.runtime.minecraft_find_path(x=x, y=y, z=z)


    def minecraft_is_safe_to_dig(self, position: Vec3i) -> SafetyReportResult:
        """Sense hazards that a nearby human player can hear or see.

        The tool uses recent sounds, visible openings, and known support blocks.
        It can report nearby lava, water, entities, caves, and falls. Hidden
        hazards have an approximate direction and distance band, not coordinates.

        The sound distance is {{DIG_SOUND_RADIUS_BLOCKS}} blocks. The result is
        low_risk, warning, or unknown. It never guarantees that digging is safe.

        Args:
            position: The cell you plan to break.

        See also: minecraft_mine_block, minecraft_staircase_down
        """
        return self.runtime.minecraft_is_safe_to_dig(position=position)


    def minecraft_recall(self, pattern: str) -> RecallResult:
        """Glob-search your durable memory notes.

        This tool searches text and categories in persistent memory. It returns
        the newest matching notes first.
        The result contains at most {{RECALL_RESULT_LIMIT}} notes.

        Args:
            pattern: Glob pattern matched against note text and categories.

        Failure modes:
            - reason "not_found": nothing in memory matches.

        See also: minecraft_remember, minecraft_add_waypoint
        """
        return self.runtime.minecraft_recall(pattern=pattern)


# =========================================================================
# Docstring constant renderer (interface glue, runs on import)
# =========================================================================


def _render_doc_constants() -> None:
    """Put fixed limit values into public tool descriptions."""
    for name, fn in inspect.getmembers(MinecraftTools, inspect.isfunction):
        if not name.startswith("minecraft_") or not inspect.isfunction(fn):
            continue
        doc = fn.__doc__
        if not doc:
            continue
        for constant_name, value in DOC_CONSTANTS.items():
            doc = doc.replace(f"{{{{{constant_name}}}}}", str(value))
        if "{{" in doc or "}}" in doc:
            raise ValueError(f"Unresolved docstring constant in {name}")
        fn.__doc__ = doc


_render_doc_constants()
