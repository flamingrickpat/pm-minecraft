"""Return-type models for the v2 Minecraft MCP surface.

Every MCP tool returns exactly ONE instance of one of these models. There are
no generic envelopes, no "state file links", no raw dicts. The model IS the
contract: it describes, field by field, what the tool did to the world and
what the agent should do with that information.

Shared conventions for ALL result models
========================================

ok / reason / message
    Every model inherits `ToolOutcome`. `ok` is True when the tool completed
    its documented contract. When `ok` is False, `reason` carries a short
    machine-readable code (e.g. "not_found", "ambiguous", "out_of_range",
    "missing_ingredients", "no_path") and `message` a
    human-readable sentence. Success payloads are Optional and are None on
    failure; failure payloads (candidates, missing lists) are None on success.
    A tool never raises for game-world problems. Invalid arguments and an
    unavailable player body are MCP errors.

Units and coordinates
    - One block = 1.0 distance unit. Y points up.
    - `Vec3i` addresses a block CELL (integer corner coordinates).
    - `Vec3f` addresses a player-space position (block centers are x.5/z.5).
    - yaw: degrees, 0 = south (+Z), 90 = west (-X), 180 = north (-Z),
      270 = east (+X). pitch: degrees, positive = looking up.

Image policy
    Tools whose outcome changes what you SEE return an `image` field
    (observe, rotate, fine_control, mine_block, pillar_up). Tools whose
    outcome is pure bookkeeping (craft, eat, equip, smelt, chest moves,
    remember, waypoints) have NO image field at all. The PNG pixels travel
    as an MCP image content part; `ImageRef` only carries metadata.

Glob / name resolution
    Anywhere a tool accepts a block/item/material name it also accepts a glob
    pattern ("*log", "*_ore", "diamond*", "oak_?oor"). If exactly one known
    name matches, the tool acts on it. If several match, nothing happens and
    `candidates` lists the choices. If none match, `candidates` lists the
    closest known names by edit distance so typos can be corrected in one
    round trip.

Timing
    `duration_ms` fields are wall-clock durations of the whole tool call,
    kept for benchmark regression tests.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared type aliases
# ---------------------------------------------------------------------------

Direction6 = Literal["north", "south", "east", "west", "up", "down"]
"""The six orthogonal face directions of a block cell."""


# ---------------------------------------------------------------------------
# Geometry primitives
# ---------------------------------------------------------------------------


class Vec3i(BaseModel):
    """Integer block-cell coordinates.

    Addresses one whole block cube in the world grid (what F3 shows as "Block").
    Used for mining targets, build placements, block inspections.
    """

    x: int = Field(description="East-west axis. +X = east.")
    y: int = Field(description="Vertical axis. +Y = up. Sea level is ~63.")
    z: int = Field(description="North-south axis. +Z = south.")


class Vec3f(BaseModel):
    """Float player-space coordinates (a point, not a cell).

    Player feet positions are usually at x.5 / z.5 (block centers).
    Used for entity positions, walk targets and camera poses.
    """

    x: float = Field(description="East-west axis. +X = east.")
    y: float = Field(description="Vertical axis. +Y = up.")
    z: float = Field(description="North-south axis. +Z = south.")


class Box(BaseModel):
    """An axis-aligned rectangular region between two block cells, inclusive.

    `min` and `max` are the diagonal corner cells; every cell with
    min.x <= x <= max.x etc. belongs to the box. This is the same convention
    as the vanilla `/fill` command.
    """

    min: Vec3i = Field(description="Corner with the smallest x, y, z.")
    max: Vec3i = Field(description="Corner with the largest x, y, z.")


# ---------------------------------------------------------------------------
# Common reference objects
# ---------------------------------------------------------------------------


class ImageRef(BaseModel):
    """Metadata about the screenshot attached to a tool result.

    The PNG pixels are attached to the tool response as a separate MCP image
    content part; this object only identifies and describes that image.
    """

    frame_id: str = Field(description="Stable id of the captured frame.")
    captured_at: str = Field(
        description="ISO-8601 UTC timestamp of the capture."
    )
    width: int = Field(ge=0, description="Image width in pixels.")
    height: int = Field(ge=0, description="Image height in pixels.")


class NameCandidate(BaseModel):
    """One alternative name offered when a glob/exact name did not resolve.

    Returned in `candidates` lists. Always actionable: re-call the tool with
    one of these names verbatim.
    """

    name: str = Field(description="Exact internal name to re-send.")
    display_name: str = Field(description="Human-readable in-game name.")
    similarity: float = Field(
        description="0.0..1.0. How close this candidate is to what you asked for."
    )
    match_kind: Literal["glob", "fuzzy", "prefix"] = Field(
        description="'glob' = matched your pattern, 'fuzzy'/'prefix' = "
        "spelling correction suggestions for a pattern that matched nothing."
    )


class BlockRef(BaseModel):
    """A block that exists (or existed) at a position."""

    position: Vec3i = Field(description="Cell the block occupies.")
    block_name: str = Field(description="Internal name, e.g. 'diamond_ore'.")
    display_name: str = Field(description="Human name, e.g. 'Diamond Ore'.")


class InventoryItem(BaseModel):
    """One stack of items in your inventory, aggregated view."""

    name: str = Field(description="Internal item name, e.g. 'oak_planks'.")
    display_name: str = Field(description="Human-readable item name.")
    count: int = Field(ge=0, description="How many you hold across all slots.")
    slot: int | None = Field(
        default=None,
        description="Slot index when this refers to exactly one slot, else None.",
    )
    durability: int | None = Field(
        default=None,
        description="Remaining uses for tools/weapons, else None.",
    )
    max_durability: int | None = Field(
        default=None, description="Total uses when new, for tools/weapons."
    )


class InventorySlot(BaseModel):
    """The content of one inventory slot.

    Slot numbering: 0-8 hotbar (0 = main hand slot the game selects),
    9-35 main inventory, 36-39 armor, 40 off-hand.
    """

    slot: int = Field(description="Slot index, see class docstring for ranges.")
    item: str | None = Field(
        default=None, description="Internal item name, or None when empty."
    )
    count: int = Field(default=0, description="Stack size; 0 when empty.")


class InventoryChange(BaseModel):
    """How the count of one item changed across a tool call."""

    item: str = Field(description="Internal item name.")
    before: int = Field(ge=0, description="Count before the action.")
    after: int = Field(ge=0, description="Count after the action.")
    delta: int = Field(description="after - before. Negative = consumed.")


class InventoryDelta(BaseModel):
    """Everything that changed in your inventory during one tool call.

    Only items whose count actually changed are listed. An empty `changes`
    list means the action consumed and produced nothing.
    """

    changes: list[InventoryChange] = Field(
        description="One entry per item whose count changed, any order."
    )
    total_items_before: int = Field(ge=0, description="Sum of all stack sizes before.")
    total_items_after: int = Field(ge=0, description="Sum of all stack sizes after.")


class StatDelta(BaseModel):
    """Vitals before and after an action that can affect them (eating, damage).

    Compare *_before with *_after; unchanged stats are still reported so you
    never have to guess whether a field is stale.
    """

    health_before: float = Field(description="Health points before, 0..20.")
    health_after: float = Field(description="Health points after, 0..20.")
    food_before: int = Field(description="Hunger points before, 0..20.")
    food_after: int = Field(description="Hunger points after, 0..20.")
    oxygen_before: int = Field(
        description="Air bubbles before, 0..20 (20 = full air)."
    )
    oxygen_after: int = Field(
        description="Air bubbles after, 0..20 (20 = full air)."
    )
    xp_level_before: int = Field(description="XP level before.")
    xp_level_after: int = Field(description="XP level after.")


class PlayerStatus(BaseModel):
    """Your current vitals and world context."""

    health: float = Field(description="Health points, 0..20.")
    max_health: float = Field(description="Maximum health points.")
    food: int = Field(description="Hunger points, 0..20.")
    oxygen: int = Field(description="Air bubbles, 0..20. 20 = not underwater.")
    xp_level: int = Field(description="Current experience level.")
    biome: str = Field(description="Biome you stand in, e.g. 'forest'.")
    dimension: str = Field(description="'overworld', 'the_nether', 'the_end'.")
    time_of_day: int = Field(
        description="World time in ticks, 0..24000. 0-12000 = day."
    )
    is_day: bool = Field(description="True while the sun is up.")
    is_raining: bool = Field(description="True while rain/thunder is active.")
    on_ground: bool = Field(description="True when standing on solid ground.")
    in_water: bool = Field(description="True when at least feet-deep in liquid.")


class ViewTransform(BaseModel):
    """Where your camera is and where it points - the 'world transform'.

    Returned by every tool that moves or turns you, so you always know your
    exact pose after acting without a separate observation.
    """

    feet_position: Vec3f = Field(description="Where your feet are.")
    eye_position: Vec3f = Field(
        description="Where your eyes are (feet + ~1.62 blocks)."
    )
    block_position: Vec3i = Field(
        description="Block cell your feet occupy."
    )
    yaw: float = Field(
        description="Absolute horizontal view angle in degrees: "
        "0 = south (+Z), 90 = west (-X), 180 = north (-Z), 270 = east (+X)."
    )
    pitch: float = Field(
        description="Absolute vertical view angle in degrees. Positive looks "
        "UP, negative looks down, 0 is level."
    )
    cardinal: Literal["north", "south", "east", "west"] = Field(
        description="The cardinal direction you face, rounded from yaw."
    )
    look_vector: Vec3f = Field(
        description="Unit vector pointing where you look. Tip: look_vector "
        "rounded gives you 'one block in front of me'."
    )


class EntityRef(BaseModel):
    """A living thing or dropped item near you."""

    entity_id: int = Field(
        description="Server entity id. Use this for attack_entity."
    )
    entity_type: str = Field(
        description="Internal type, e.g. 'zombie', 'cow', 'item', 'player'."
    )
    display_name: str = Field(description="Human-readable name.")
    position: Vec3f = Field(description="Current position.")
    distance: float = Field(description="Distance from you in blocks.")
    health: float | None = Field(
        default=None, description="Current health for living entities."
    )
    hostile: bool | None = Field(
        default=None,
        description="True when the entity attacks players on sight.",
    )


class BlockCount(BaseModel):
    """How many blocks of one type are near you (aggregated)."""

    block_name: str = Field(description="Internal block name.")
    display_name: str = Field(description="Human-readable block name.")
    count: int = Field(ge=0, description="How many exist within the search bounds.")
    nearest: Vec3i = Field(description="Cell of the closest instance.")
    distance: float = Field(description="Distance to the closest instance.")


class ExposedBlock(BaseModel):
    """A found block plus how it is exposed to the world.

    'Exposed' means at least one of the six face-adjacent cells is non-solid
    (air, water, lava, or any block you can walk through). This is
    'theoretically visible': it does NOT depend on where you stand, and it
    never reports blocks that are fully buried in solid material.
    """

    position: Vec3i = Field(description="Cell of the block.")
    block_name: str = Field(description="Internal block name.")
    display_name: str = Field(description="Human-readable block name.")
    distance: float = Field(
        description="Distance from the search center (bot or `near`)."
    )
    exposed_faces: list[Direction6] = Field(
        description="Which faces touch a non-solid cell. At least one."
    )
    harvestable_with_held: bool | None = Field(
        default=None,
        description="True when your CURRENT held item can harvest drops "
        "from this block. None when irrelevant.",
    )


class SearchCoverage(BaseModel):
    """What part of the world a search actually looked at.

    Lets you distinguish 'there is none' from 'I did not look there'.
    """

    center: Vec3f = Field(description="Where the search was centered.")
    bounds: Box = Field(description="Exact block-cell bounds of the search.")
    chunks_loaded: int = Field(
        description="How many chunks around you are loaded and were searched."
    )
    columns_scanned: int = Field(
        description="How many vertical columns were examined."
    )
    note: str | None = Field(
        default=None,
        description="Extra search coverage information.",
    )


class NeighborCell(BaseModel):
    """One of the six face-adjacent cells around an inspected block."""

    direction: Direction6 = Field(description="Which side of the center block.")
    position: Vec3i = Field(description="Cell of the neighbor.")
    block_name: str = Field(description="Internal block name, 'air' if empty.")
    solid: bool = Field(
        description="True when the block blocks movement (full collision box)."
    )


class PickupStatus(BaseModel):
    """Loot delivery for one mined block.

    Babymode inserts normal mined loot directly into the miner's
    inventory. Only overflow that does not fit drops at the block; walk
    to the position in `drop_hint` to collect it.
    """

    picked_up: bool = Field(
        description="True when the loot is in the inventory."
    )
    drop_items: list[str] = Field(
        description="Internal names of the items that dropped."
    )
    drop_hint: str | None = Field(
        default=None,
        description="Where the overflow lies, when picked_up is False.",
    )


class InteractableRef(BaseModel):
    """A nearby block you can right-click / activate."""

    position: Vec3i = Field(description="Cell of the interactable block.")
    block_name: str = Field(description="Internal block name.")
    display_name: str = Field(description="Human-readable block name.")
    kind: Literal[
        "door",
        "gate",
        "trapdoor",
        "chest",
        "barrel",
        "shulker_box",
        "furnace",
        "crafting_table",
        "bed",
        "button",
        "lever",
        "hopper",
        "other",
    ] = Field(description="Interaction category.")
    distance: float = Field(description="Distance from you in blocks.")
    state: str | None = Field(
        default=None,
        description="Current state when observable, e.g. 'open'/'closed' "
        "for doors.",
    )


class HorizonRay(BaseModel):
    """One ray of a horizon scan: what the view ray hits in one heading."""

    heading_degrees: int = Field(
        description="Compass heading of the ray, 0..345 in 15 degree steps."
    )
    cardinal: str = Field(description="Nearest cardinal, e.g. 'NE'.")
    pitch: Literal[15, 0, -15] = Field(
        description="Ray pitch: +15 looks up, 0 level, -15 looks down."
    )
    hit: bool = Field(description="True when the ray hit a block or liquid.")
    block_name: str | None = Field(
        default=None, description="Internal name of the first thing hit."
    )
    distance: float | None = Field(
        default=None, description="Distance to the hit in blocks."
    )


class HorizonSector(BaseModel):
    """Summary of one compass sector in a horizon scan."""

    cardinal: str = Field(description="Compass sector, for example north-east.")
    terrain: str = Field(description="Short description of the visible terrain.")
    notable_blocks: list[str] = Field(
        description="Visible blocks that can identify a useful landmark."
    )


class HorizonLandmark(BaseModel):
    """A possible landmark inferred from raytraceable surface evidence."""

    kind: Literal[
        "possible_village",
        "possible_structure",
        "light_source",
        "path",
        "water",
        "cliff",
        "forest",
    ] = Field(description="Possible landmark type.")
    cardinal: str = Field(description="Compass direction of the evidence.")
    confidence: Literal["low", "medium", "high"] = Field(
        description="Confidence from visible evidence. This is not proof."
    )
    evidence: list[str] = Field(description="Visible facts that support the result.")


class ContainerWindow(BaseModel):
    """The container window currently open (chest, furnace, crafting table)."""

    kind: Literal[
        "chest", "barrel", "shulker_box", "furnace", "crafting_table"
    ] = Field(description="Window type.")
    position: Vec3i | None = Field(
        default=None, description="Cell of the container block, if any."
    )
    slots: list[InventorySlot] = Field(
        description="Contents by slot index. Empty slots carry item=None."
    )


class IngredientNeed(BaseModel):
    """How much of one ingredient a recipe needs vs. how much you have."""

    item: str = Field(description="Internal ingredient name.")
    display_name: str = Field(description="Human-readable ingredient name.")
    required: int = Field(ge=0, description="Amount needed for one craft.")
    have: int = Field(ge=0, description="Amount currently in your inventory.")
    missing: int = Field(ge=0, description="required - have, at least 0.")


class RecipeEntry(BaseModel):
    """One craftable item from the recipe book."""

    item_name: str = Field(description="Internal item name to craft.")
    display_name: str = Field(description="Human-readable item name.")
    grid: str = Field(
        description="Recipe grid as rows, e.g. 'PP\\nPS' for a wooden axe "
        "where P=planks, S=stick. 2 rows = 2x2 recipe."
    )
    legend: dict[str, str] = Field(
        description="Symbol -> ingredient name mapping for `grid`."
    )
    ingredients: list[IngredientNeed] = Field(
        description="Full ingredient list for ONE craft, with have/missing."
    )
    output_count: int = Field(
        description="Items produced per craft (usually 1, sometimes 4)."
    )
    needs_crafting_table: bool = Field(
        description="True when the recipe is 3x3 and requires a placed "
        "crafting table within reach."
    )
    craftable_now: bool = Field(
        description="True when you currently have all ingredients (and a "
        "table is in range when needed)."
    )


class Waypoint(BaseModel):
    """A persistent marker for a place you want to find again."""

    id: str = Field(description="Stable id of the waypoint.")
    description: str = Field(description="What you noted about this place.")
    position: Vec3i = Field(description="Saved cell.")
    dimension: str = Field(description="Dimension that contains the place.")
    tags: list[str] = Field(description="Short labels for place searches.")
    created_at: str = Field(description="ISO-8601 UTC timestamp.")
    last_visited_at: str | None = Field(
        default=None, description="ISO-8601 UTC time of the last visit."
    )


class Capability(BaseModel):
    """One reusable skill available for execution."""

    name: str = Field(description="Skill name to pass to execute_typescript.")
    description: str = Field(description="What the skill does and when to use.")
    path: str = Field(description="File the skill lives in.")
    arguments: list[str] = Field(
        default_factory=list,
        description="Argument names the skill accepts.",
    )
    required_items: list[str] = Field(
        default_factory=list, description="Items required before execution."
    )
    stopping_conditions: list[str] = Field(
        default_factory=list, description="Conditions that stop the skill."
    )
    postconditions: list[str] = Field(
        default_factory=list, description="Observed facts that define success."
    )


class PostconditionReport(BaseModel):
    """Outcome of the deterministic postcondition check for a skill run."""

    passed: bool = Field(description="True when the after-state matched.")
    spec: str = Field(description="The postcondition spec as JSON.")
    detail: str | None = Field(
        default=None, description="Human explanation on failure."
    )


# ---------------------------------------------------------------------------
# Base outcome convention
# ---------------------------------------------------------------------------


class ToolOutcome(BaseModel):
    """Fields every tool result shares.

    `ok` True  -> the tool completed its documented contract. Some read and
                  bounded-action tools can report a negative status.
    `ok` False -> `reason` is a short machine-readable code, `message` a
                  human sentence; failure payload fields (e.g. candidates,
                  missing_ingredients) are populated where applicable.
    """

    warnings: list[str] = Field(default_factory=list, description="Observed tool loss or unexpected held-item changes.")
    ok: bool = Field(description="True when the tool completed its documented contract.")
    reason: str | None = Field(
        default=None,
        description="Machine-readable failure code, None on success.",
    )
    message: str | None = Field(
        default=None,
        description="Human-readable summary or failure explanation.",
    )


# ---------------------------------------------------------------------------
# Per-tool result models
# ---------------------------------------------------------------------------


class ObserveResult(ToolOutcome):
    """A compact, immediately-usable snapshot of your situation.

    This is the orientation tool: where you are, what you hold, what is near
    you, and (by default) a screenshot. Everything needed to decide the next
    action in one call - no file links to chase.
    """

    camera: ViewTransform = Field(
        description="Your exact pose: position, yaw, pitch, look vector."
    )
    player: PlayerStatus = Field(description="Vitals and world context.")
    held_item: InventoryItem | None = Field(
        default=None, description="Item in your main hand, None when empty."
    )
    hotbar: list[InventorySlot] = Field(
        description="Your 9 hotbar slots, index 0-8."
    )
    inventory: list[InventoryItem] = Field(
        description="Whole inventory aggregated by item name."
    )
    nearby_blocks: list[BlockCount] = Field(
        description="Block types within the observation bounds, nearest first."
    )
    nearby_entities: list[EntityRef] = Field(
        description="Mobs, players and dropped items nearby, nearest first."
    )
    image: ImageRef | None = Field(
        default=None,
        description="Screenshot metadata; pixels attached as image content.",
    )


class FindBlockResult(ToolOutcome):
    """Surface-exposed blocks that match a glob pattern.

    A block matches when its name matches and one adjacent cell is non-solid.
    The block does not need a clear ray from the player. Buried blocks never
    appear. Fixed horizontal and vertical limits prevent deep remote scans.
    """

    pattern: str = Field(description="The glob pattern you sent.")
    matched_types: list[str] = Field(
        description="Block names that matched the pattern, e.g. "
        "['oak_log', 'birch_log']."
    )
    total_matches: int = Field(
        description="Exposed matches found before applying `limit`."
    )
    nearest: ExposedBlock | None = Field(
        default=None,
        description="Closest match, also first element of `results`.",
    )
    results: list[ExposedBlock] = Field(
        description="Matches after the fixed diversity rule, nearest first."
    )
    coverage: SearchCoverage | None = Field(
        default=None,
        description="Where was searched, so 'not found' is unambiguous.",
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="When the pattern matched NO known block name: closest "
        "known names, so you can fix a typo in one round trip.",
    )
    duration_ms: float = Field(
        description="Query time. RAM-resident index: typically < 10 ms."
    )


class FindInteractablesResult(ToolOutcome):
    """Right-clickable blocks near you, filtered by a glob pattern."""

    pattern: str = Field(description="Glob pattern applied to block names.")
    results: list[InteractableRef] = Field(
        description="Interactables, nearest first."
    )
    coverage: SearchCoverage | None = Field(
        default=None, description="Where was searched."
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="Alternative names when the pattern matched nothing known.",
    )
    duration_ms: float = Field(description="Query time in milliseconds.")


class InspectBlockResult(ToolOutcome):
    """Everything about one block cell and its six neighbors.

    The microscope: use it before mining, before building next to something,
    or to find out why a find/mine/build call behaved unexpectedly.
    """

    position: Vec3i = Field(description="Cell you inspected.")
    block_name: str = Field(
        description="Internal name of the block, 'air' when empty."
    )
    display_name: str = Field(description="Human-readable block name.")
    is_solid: bool = Field(
        description="True when the block has a full collision box."
    )
    exposed_faces: list[Direction6] = Field(
        description="Faces touching a non-solid cell. Empty = fully buried."
    )
    neighbors: list[NeighborCell] = Field(
        description="All six face-adjacent cells with their contents."
    )
    best_tools: list[str] = Field(
        default_factory=list,
        description="Item names that harvest this block fastest, fastest first.",
    )
    can_harvest_with_held: bool | None = Field(
        default=None,
        description="True when your CURRENT held item gets drops from it.",
    )
    drops: list[str] = Field(
        default_factory=list,
        description="Items this block drops when harvested correctly.",
    )
    hardness: float | None = Field(
        default=None,
        description="Mining hardness; higher = slower to break.",
    )
    image: ImageRef | None = Field(
        default=None, description="Screenshot when requested."
    )


class RaytraceResult(ToolOutcome):
    """The first block your view ray hits.

    Use for precise aiming: what exactly am I looking at, and on which face?
    """

    hit: bool = Field(description="True when the ray hit something.")
    hit_position: Vec3i | None = Field(
        default=None, description="Cell of the block that was hit."
    )
    hit_block: str | None = Field(
        default=None, description="Internal name of the block that was hit."
    )
    hit_face: Direction6 | None = Field(
        default=None,
        description="Face of the hit block the ray entered through.",
    )
    distance: float | None = Field(
        default=None, description="Distance from your eyes to the hit."
    )
    camera: ViewTransform = Field(description="Pose the ray was cast from.")
    image: ImageRef | None = Field(
        default=None, description="Screenshot when requested."
    )


class ScanHorizonResult(ToolOutcome):
    """A full horizon scan from fixed headings and pitches.

    The panorama overview: what surrounds you at ground level, and how far.
    """

    origin: Vec3f = Field(description="Position the scan started from.")
    rays: list[HorizonRay] = Field(
        description="Raw rays. A sky ray has hit=False."
    )
    sectors: list[HorizonSector] = Field(
        description="Terrain and notable visible blocks by compass sector."
    )
    landmarks: list[HorizonLandmark] = Field(
        description="Possible landmarks inferred only from visible evidence."
    )
    image: ImageRef | None = Field(
        default=None, description="Screenshot when requested."
    )
    duration_ms: float = Field(description="Scan time in milliseconds.")


class RecipeSearchResult(ToolOutcome):
    """Recipe book search results for a glob pattern.

    The kitchen catalogue: search '*pickaxe' to see every pickaxe, or send
    '*' with craftable_now=true to see everything you can craft RIGHT NOW
    from your inventory.
    """

    pattern: str = Field(description="Glob pattern you searched for.")
    matches: list[RecipeEntry] = Field(
        description="Recipes whose item name matched, best matches first."
    )
    total_recipes: int = Field(
        description="Total recipes in the book (size of the catalogue)."
    )
    duration_ms: float = Field(description="Search time in milliseconds.")


class CraftItemResult(ToolOutcome):
    """Outcome of a crafting attempt, with the inventory delta.

    On success: what was crafted, how the inventory changed, and your hotbar
    afterwards. On failure: either name candidates (unknown/ambiguous name)
    or a precise missing-ingredients list. No image is ever attached.
    """

    requested: str = Field(description="Name or glob you asked to craft.")
    resolved_item: str | None = Field(
        default=None,
        description="Exact item actually crafted, None when nothing was.",
    )
    repetitions_requested: int = Field(
        description="How many recipe runs you asked for."
    )
    repetitions_crafted: int = Field(
        description="How many recipe runs actually happened."
    )
    output: InventoryItem | None = Field(
        default=None, description="The crafted stack, None on failure."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None,
        description="Everything gained/lost. None when nothing was crafted.",
    )
    hotbar: list[InventorySlot] = Field(
        description="Hotbar AFTER the craft, index 0-8."
    )
    crafting_table_used: Vec3i | None = Field(
        default=None,
        description="Table cell used for a 3x3 recipe, None for 2x2 recipes.",
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="When the name matched nothing or several items: the "
        "choices. Re-call with one exact name.",
    )
    missing_ingredients: list[IngredientNeed] | None = Field(
        default=None,
        description="When ingredients are short: what is missing, item by "
        "item, with have/required counts.",
    )


class EquipResult(ToolOutcome):
    """Outcome of putting an item into your main hand.

    Always reports the hotbar afterwards and verifies what actually ended up
    in hand, so 'silent equip failure' (old place/mine bug class) is visible.
    """

    requested: str = Field(description="Name or glob you asked to equip.")
    equipped: InventoryItem | None = Field(
        default=None,
        description="What is now in your main hand. None when equip failed.",
    )
    previous_held: InventoryItem | None = Field(
        default=None, description="What was in hand before, if anything."
    )
    hotbar: list[InventorySlot] = Field(
        description="Hotbar AFTER the swap, index 0-8."
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="Alternative names when the request was unknown/ambiguous.",
    )


class UseItemResult(ToolOutcome):
    """Outcome of using the held item: eating, drinking, throwing.

    Reports the stat delta (hunger/health/oxygen) and the inventory delta.
    No image is ever attached.
    """

    action: Literal[
        "ate", "drank", "threw", "activated", "nothing"
    ] | None = Field(
        default=None,
        description="What using the item did. 'nothing' e.g. when food is "
        "already full - see message.",
    )
    item: InventoryItem | None = Field(
        default=None, description="The item that was used, None when hand "
        "was empty."
    )
    stat_delta: StatDelta | None = Field(
        default=None,
        description="Vitals before/after. Populated for food and potions.",
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None,
        description="Items consumed/produced (e.g. bowl left after stew).",
    )


class SmeltItemResult(ToolOutcome):
    """Outcome of smelting items in a nearby furnace.

    The furnace is found, loaded, waited on, and unloaded automatically.
    """

    furnace: Vec3i | None = Field(
        default=None, description="Furnace cell that was used."
    )
    input_item: str | None = Field(
        default=None, description="Internal name of the smelted input."
    )
    input_consumed: int = Field(
        description="Input items actually smelted."
    )
    fuel_item: str | None = Field(
        default=None, description="Internal name of the fuel burned."
    )
    fuel_consumed: int = Field(ge=0, description="Fuel items actually burned.")
    output: InventoryItem | None = Field(
        default=None, description="Smelted stack added to your inventory."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Net inventory change of the whole smelt."
    )
    duration_ms: float = Field(description="Total smelt wall time.")
    missing: list[IngredientNeed] | None = Field(
        default=None,
        description="When input or fuel is short: what is missing.",
    )


class MineBlockResult(ToolOutcome):
    """Outcome of mining one block, with loot-delivery status.

    The body walks into range and digs with the held tool. Babymode
    inserts the loot directly into the inventory; only overflow drops at
    the block. The result reports a screenshot of the new hole.
    """

    block: BlockRef | None = Field(
        default=None, description="The block that was mined, None on failure."
    )
    tool_used: str | None = Field(
        default=None, description="Held item used to dig, None for fists."
    )
    can_harvest: bool | None = Field(
        default=None,
        description="True when the tool was correct and drops could fall. "
        "False means the block broke but dropped NOTHING (wrong tool tier).",
    )
    pickup: PickupStatus | None = Field(
        default=None,
        description="Loot delivery outcome; None when nothing dropped.",
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Items gained by mining this block."
    )
    image: ImageRef | None = Field(
        default=None, description="Screenshot of the mined-out area."
    )
    duration_ms: float = Field(description="Total mine wall time.")


class PlacedCell(BaseModel):
    """One cell affected by a build."""

    position: Vec3i = Field(description="Cell address.")
    block_name: str = Field(description="Block now in that cell.")


class BuildResult(ToolOutcome):
    """Outcome of a programmatic build (wall/floor/box/staircase/...).

    The bot does not look or aim; it spawns blocks directly at the requested
    cells with server-assisted placement. Every placement consumes an
    inventory block. The tool never replaces a solid block. Skipped cells
    are grouped as occupied, out of range, or missing material.
    """

    shape: Literal[
        "fill", "shell", "wall", "floor", "ceiling", "column", "staircase",
        "bridge", "frame",
    ] = Field(description="Shape that was built.")
    material_requested: str = Field(
        description="Material name or glob you asked for."
    )
    material_resolved: str | None = Field(
        default=None,
        description="Exact block placed. None when the glob was ambiguous.",
    )
    bounds: Box | None = Field(
        default=None, description="Bounding box of the planned cells."
    )
    planned_cells: int = Field(
        description="Total cells the shape wants."
    )
    placed_count: int = Field(
        description="Cells actually placed in this call."
    )
    placed: list[PlacedCell] = Field(
        description="Every placed cell. For huge builds this can be long; "
        "use placed_count when you only need the number."
    )
    occupied: list[PlacedCell] = Field(
        description="Skipped cells that already contained a solid block."
    )
    out_of_range: list[Vec3i] = Field(
        description="Skipped cells beyond the fixed build distance."
    )
    missing_material_cells: int = Field(
        default=0,
        description="Cells skipped because the inventory had no material.",
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None,
        description="Material consumed from the inventory.",
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="When the material glob matched several blocks (e.g. "
        "'*log' -> oak_log, spruce_log): the choices. Nothing was placed.",
    )
    image: ImageRef | None = Field(
        default=None, description="After-build screenshot when requested."
    )
    duration_ms: float = Field(description="Total build wall time.")


class RotateResult(ToolOutcome):
    """Outcome of turning the view: the new world transform plus a screenshot.

    The camera pose after the turn is the whole point of this call - use
    `camera.yaw/pitch/look_vector` to know exactly where you face now.
    """

    camera: ViewTransform = Field(
        description="Your exact pose AFTER the rotation."
    )
    yaw_delta: float = Field(description="How far yaw moved, in degrees.")
    pitch_delta: float = Field(description="How far pitch moved, in degrees.")
    image: ImageRef = Field(
        description="Screenshot from the new view direction."
    )


class FineControlResult(ToolOutcome):
    """Outcome of a raw movement nudge (walk keys for a short duration).

    For the last meter where pathfinding is overkill. Returns the pose
    before/after and a screenshot so you can verify the nudge visually.
    """

    controls: dict[str, bool] = Field(
        description="The keys that were held, e.g. {'forward': true}."
    )
    duration_ms: float = Field(
        description="How long the fixed control pulse lasted."
    )
    pose_before: Vec3f = Field(description="Feet position before the nudge.")
    pose_after: Vec3f = Field(description="Feet position after the nudge.")
    camera: ViewTransform = Field(description="Pose AFTER the nudge.")
    on_ground: bool = Field(
        description="True when you ended standing on solid ground."
    )
    image: ImageRef = Field(description="Screenshot after the nudge.")


class PillarUpResult(ToolOutcome):
    """Outcome of mechanically placing held blocks beneath the player.

    The server places each block in the current feet cell and moves the player
    up. The action stops before the remaining clearance is less than two cells.
    """

    camera: ViewTransform = Field(description="Pose after the climb.")
    blocks_placed: int = Field(
        description="Blocks placed under your feet."
    )
    climbed: int = Field(
        description="Blocks of height gained."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Blocks consumed from your inventory."
    )
    image: ImageRef = Field(description="Screenshot from the new height.")


class WalkDiagnostics(BaseModel):
    """Navigation evidence, without guessing which obstacle caused a failure."""

    cause: str = Field(description="Specific outcome: goal_reached, partial_goal_within_tolerance, search_no_path, search_timeout, outside_reached_distance, movement_timeout, replanning_timeout, movement_no_path, movement_error, stopped, target_outside_search_distance, or a target validation failure. Search failure only applies to the configured movement rules and search corridor.")
    path_status: str | None = Field(description="Raw initial pathfinder search status; null if no search ran.")
    error_name: str | None = Field(description="Original movement exception name, if any.")
    error_message: str | None = Field(description="Original movement exception message, if any.")
    target_block: str | None = Field(description="Block at the requested feet cell; null means unloaded or unknown.")
    target_head_block: str | None = Field(description="Block above the target feet cell.")
    target_floor_block: str | None = Field(description="Block below the target feet cell.")
    feet_block: str | None = Field(description="Block at the final player feet cell.")
    head_block: str | None = Field(description="Block above the final player feet cell. Check for liquid before treating arrival as an escape.")


class WalkResult(ToolOutcome):
    """Outcome of a navigation command.

    `status` says how far you got: 'reached', 'partial' (moved but not
    there), 'no_path' (nothing moved), or 'timeout'. On failure `reason`
    and `message` explain what blocked the route (water, cliff, unload...).
    """

    status: Literal["reached", "partial", "no_path", "timeout"] | None = Field(
        default=None, description="How the walk ended."
    )
    requested: Vec3f = Field(description="Where you asked to go.")
    final_position: Vec3f | None = Field(
        default=None, description="Where you actually ended up."
    )
    distance_remaining: float | None = Field(
        default=None,
        description="Distance from the final position to the requested target. "
        "A reached result can retain distance within the configured reached distance.",
    )
    target_offset: Vec3f = Field(description="Requested target minus final feet position, in blocks. Positive y means the target is still above you. Reached can mean only within tolerance; inspect this offset to verify arrival.")
    diagnostics: WalkDiagnostics = Field(description="Specific cause, original error, and observed block context for choosing another action.")
    hops: int | None = Field(
        default=None,
        description="Pathfinding segments used. High numbers hint at "
        "detours.",
    )
    camera: ViewTransform | None = Field(
        default=None, description="Pose after the walk."
    )
    image: ImageRef | None = Field(
        default=None, description="Screenshot after arrival when requested."
    )
    duration_ms: float = Field(description="Total walk wall time.")


class UseBlockResult(ToolOutcome):
    """Outcome of right-clicking a block: doors, chests, tables, buttons...

    When a container opened, `window` carries its full contents so you can
    immediately follow up with deposit/withdraw calls.
    """

    block: BlockRef | None = Field(
        default=None, description="The block that was activated."
    )
    action: Literal[
        "door_opened",
        "door_closed",
        "gate_opened",
        "gate_closed",
        "trapdoor_opened",
        "trapdoor_closed",
        "container_opened",
        "crafting_table_opened",
        "furnace_opened",
        "button_pressed",
        "lever_toggled",
        "bed_entered",
        "activated",
        "nothing",
    ] | None = Field(
        default=None, description="What the activation did."
    )
    window: ContainerWindow | None = Field(
        default=None,
        description="Container window state when one opened, else None.",
    )
    image: ImageRef | None = Field(
        default=None, description="Screenshot when requested."
    )


class ChestMoveResult(ToolOutcome):
    """Outcome of moving items between your inventory and a container.

    Works on the open window (use_block) or opens `chest` itself when given.
    """

    item: str | None = Field(
        default=None, description="Internal name of the moved item."
    )
    moved_count: int = Field(ge=0, description="Stack size actually moved.")
    window: ContainerWindow | None = Field(
        default=None, description="Container contents AFTER the move."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Your inventory change from the move."
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="Alternative item names when unknown/ambiguous.",
    )


class AttackEntityResult(ToolOutcome):
    """Outcome of attacking an entity until it dies or hits run out.

    Swings with the held weapon, re-approaching as the target moves, and
    collects the drops afterwards.
    """

    entity_id: int = Field(description="The entity you attacked.")
    entity_type: str | None = Field(
        default=None, description="Internal type of the entity."
    )
    killed: bool = Field(description="True when the entity died.")
    hits: int = Field(ge=0, description="Swings that connected.")
    entity_health_remaining: float | None = Field(
        default=None,
        description="Health left when the entity survived, else None.",
    )
    self_damage_taken: float | None = Field(
        default=None,
        description="Damage YOU took during the fight, e.g. from lava or "
        "counterattacks.",
    )
    drops_collected: list[str] = Field(
        default_factory=list,
        description="Internal names of items looted from the kill.",
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Inventory gained from the drops."
    )


class StopResult(ToolOutcome):
    """What an emergency stop actually stopped."""

    scope: Literal["command", "skill", "both"] = Field(
        description="What you asked to stop."
    )
    stopped_command: str | None = Field(
        default=None,
        description="Name of the halted physical command, if one ran.",
    )
    stopped_skill: str | None = Field(
        default=None, description="Name of the halted skill process, if any."
    )
    camera: ViewTransform | None = Field(
        default=None, description="Where you stand after the halt."
    )


class RememberResult(ToolOutcome):
    """Confirmation that a durable memory note was appended.

    The note survives restarts. The file path is the
    durable evidence location, not a substitute for the data itself.
    """

    kind: str = Field(description="Memory category the note went to.")
    note_id: str = Field(description="Id of the appended note.")
    file: str = Field(description="Memory file the note was appended to.")
    notes_in_file: int = Field(ge=0, description="Notes now in that file.")
    appended_chars: int = Field(ge=0, description="Length of the appended markdown.")


class AddWaypointResult(ToolOutcome):
    """Outcome of saving a persistent waypoint in the capped list."""

    waypoint: Waypoint | None = Field(
        default=None, description="The waypoint that was saved."
    )
    waypoints: list[Waypoint] = Field(
        description="All waypoints after the save, oldest first."
    )
    evicted: Waypoint | None = Field(
        default=None,
        description="Waypoint that fell out when the list (capacity 6) "
        "was full.",
    )


class ListWaypointsResult(ToolOutcome):
    """All persistent places, oldest first."""

    waypoints: list[Waypoint] = Field(
        description="Current waypoints, oldest first."
    )
    capacity: int = Field(ge=0, description="Maximum waypoints kept (6).")


class ExecuteSkillResult(ToolOutcome):
    """Outcome of running a TypeScript skill in the world.

    Long-running skills stream heartbeats; this result is the final state.
    The postcondition check is the objective success criterion.
    """

    execution_id: str = Field(description="Id of this execution run.")
    skill_path: str = Field(description="File that was executed.")
    duration_ms: float = Field(description="Total skill wall time.")
    postcondition: PostconditionReport | None = Field(
        default=None,
        description="Deterministic after-state check. `passed` is the "
        "success gate.",
    )
    stdout_tail: str | None = Field(
        default=None, description="Last lines the skill printed."
    )
    stderr_tail: str | None = Field(
        default=None, description="Last error lines, when any."
    )
    heartbeats: int = Field(
        description="Progress heartbeats received while it ran."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Net inventory change caused by the skill."
    )
    camera: ViewTransform | None = Field(
        default=None, description="Pose after the skill finished."
    )


class ListCapabilitiesResult(ToolOutcome):
    """The reusable skills available to execute_typescript."""

    skills: list[Capability] = Field(
        description="Skills with name, description and accepted arguments."
    )


class InfoResult(ToolOutcome):
    """Identity, connection and layout information for this character."""

    username: str = Field(description="Minecraft username of this body.")
    server: str = Field(description="Game server address this body joins.")
    body_url: str = Field(description="HTTP endpoint of the body process.")
    agent_home: str = Field(description="Workspace root directory.")
    connected: bool = Field(description="True when the game connection is up.")
    spawned: bool = Field(
        description="True when the avatar is spawned in the world."
    )
    death_count: int = Field(description="Deaths this character has suffered.")
    schema_version: str = Field(
        description="Version tag of this MCP surface."
    )
    uptime_seconds: float = Field(description="Body process uptime.")


class RespawnResult(ToolOutcome):
    """Outcome of killing this avatar to escape an unescapable situation."""

    deaths: int = Field(ge=0, description="Total deaths after this respawn.")
    respawn_position: Vec3f | None = Field(
        default=None, description="Where you woke up."
    )
    cause: str = Field(description="Reason you supplied for the suicide.")
    inventory_lost: bool = Field(
        description="True when the items were not recovered before death."
    )


# ---------------------------------------------------------------------------
# Canon tools (former suggestions)
# ---------------------------------------------------------------------------


class RelativePositionResult(ToolOutcome):
    """An absolute block cell computed from a facing-relative offset.

    The anti-arithmetic helper: you say '3 forward, 1 up' and this returns
    the exact world cell plus the pose it was computed from, so you never
    do 3D math in your head.
    """

    cell: Vec3i = Field(
        description="Absolute block cell the offset points at."
    )
    camera: ViewTransform = Field(
        description="Pose the offset was computed from (sanity check)."
    )


class DistanceResult(ToolOutcome):
    """Distance between two points, with per-axis breakdown."""

    distance: float = Field(
        description="Euclidean (straight-line) distance in blocks."
    )
    manhattan: float = Field(
        description="Manhattan distance (|dx|+|dy|+|dz|), the walking-ish "
        "lower bound on real paths."
    )
    dx: float = Field(description="x component of a-b.")
    dy: float = Field(description="y component of a-b.")
    dz: float = Field(description="z component of a-b.")


class MineVeinResult(ToolOutcome):
    """Outcome of mining an entire connected ore vein as one action."""

    block: str | None = Field(
        default=None, description="Ore block name that was mined."
    )
    mined_cells: list[Vec3i] = Field(
        description="Every cell that was mined, in mining order."
    )
    mined_count: int = Field(
        description="How many blocks the vein contained (= mined_cells "
        "length)."
    )
    drops: list[str] = Field(
        description="Item names that dropped from the whole vein."
    )
    pickup: PickupStatus | None = Field(
        default=None, description="Drop collection outcome for the vein."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Net inventory gain from the vein."
    )
    image: ImageRef | None = Field(
        default=None, description="Screenshot of the mined-out vein."
    )


class HarvestTreeResult(ToolOutcome):
    """Outcome of chopping one whole tree (trunk + reachable branches)."""

    base: Vec3i | None = Field(
        default=None, description="Base log cell the harvest started at."
    )
    logs_collected: int = Field(
        description="Log items added to your inventory."
    )
    saplings_collected: int = Field(
        description="Saplings that fell and were collected."
    )
    other_drops: list[str] = Field(
        description="Apples, sticks or other bonuses the tree dropped."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Net inventory change of the harvest."
    )
    image: ImageRef | None = Field(
        default=None, description="Screenshot of the tree site."
    )


class CraftMaxResult(ToolOutcome):
    """Outcome of crafting as many of an item as materials allow."""

    resolved_item: str | None = Field(
        default=None, description="Exact item that was crafted."
    )
    crafted: int = Field(
        description="Number of output items crafted."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Net inventory change of the batch."
    )
    hotbar: list[InventorySlot] = Field(
        description="Hotbar AFTER the batch, index 0-8."
    )
    still_missing: list[IngredientNeed] | None = Field(
        default=None,
        description="What is still short for ONE more craft, when any.",
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="Alternative names when the request was "
        "unknown/ambiguous.",
    )


class EquipBestToolResult(EquipResult):
    """Outcome of auto-equipping the best tool for a target block.

    Extends EquipResult with what was inspected: the target block and the
    theoretically best tool, so you learn what to CRAFT when your own
    tools are not good enough.
    """

    target_block: str | None = Field(
        default=None, description="Block the tool was chosen for."
    )
    best_possible_tool: str | None = Field(
        default=None,
        description="Best tool that exists for that block, even when you "
        "do not own it yet (craft hint).",
    )


class EatBestResult(UseItemResult):
    """Outcome of eating the best food you carry.

    Extends UseItemResult with the foods that were considered.
    """

    considered: list[str] = Field(
        description="Foods evaluated before the best was picked."
    )


class StaircaseResult(ToolOutcome):
    """Outcome of carving a safe descending staircase."""

    depth_requested: int = Field(
        description="How deep you asked to descend."
    )
    depth_achieved: int = Field(
        description="How deep the staircase actually reached."
    )
    end_position: Vec3f | None = Field(
        default=None, description="Where you stand after the descent."
    )
    blocks_dug: int = Field(
        description="Blocks removed to carve the staircase."
    )
    hazards_found: list[str] = Field(
        default_factory=list,
        description="Hazards encountered on the way (lava/water pockets "
        "etc.); the dig stops safely at the first one.",
    )
    torches_placed: int = Field(
        description="Torches placed along the staircase for light."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Blocks/torches consumed, ores gained."
    )
    image: ImageRef | None = Field(
        default=None, description="Screenshot inside the staircase."
    )


class SleepResult(ToolOutcome):
    """Outcome of trying to sleep in a bed."""

    bed: Vec3i | None = Field(
        default=None, description="Bed cell that was used or attempted."
    )
    slept: bool = Field(
        description="True when you actually slept and the night was "
        "skipped."
    )
    is_day_now: bool = Field(description="Whether it is day after the try.")
    blocking_entity: EntityRef | None = Field(
        default=None,
        description="The hostile mob that blocked sleep, when one did - "
        "deal with it and retry.",
    )


class DropResult(ToolOutcome):
    """Outcome of tossing items out of your inventory.

    WARNING: dropped items lie at your feet and normal pickup can collect
    them again when you walk over them. Dropping is only useful to hand
    items to another player. To destroy trash use minecraft_discard_items
    instead; it creates no drop entity.
    """

    item: str | None = Field(
        default=None, description="Item that was dropped."
    )
    dropped: int = Field(ge=0, description="Stack size that left the inventory.")
    drop_position: Vec3f | None = Field(
        default=None, description="Where the item stack landed."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Your inventory change from the drop."
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="Alternative names when unknown/ambiguous.",
    )


class DiscardResult(ToolOutcome):
    """Outcome of destroying items outright (the trash can).

    Uses the server-assisted channel (same as build placement): the items
    are removed from your inventory directly - no drop entity, no pickup,
    no lava choreography. This is a deliberate cheat for hygiene; it never
    touches anything you did not name.
    """

    pattern: str = Field(
        description="The glob pattern you asked to destroy."
    )
    resolved_items: list[str] = Field(
        description="Exact item names that were removed."
    )
    discarded_count: int = Field(
        description="Total items destroyed across all stacks."
    )
    inventory_delta: InventoryDelta | None = Field(
        default=None, description="Your inventory change (all negative)."
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="When the pattern matched nothing you own: closest "
        "owned item names.",
    )


class CountResult(ToolOutcome):
    """How many items you own, filtered by glob."""

    pattern: str = Field(description="The glob pattern you counted.")
    matches: list[InventoryItem] = Field(
        description="Matching items with counts, most numerous first."
    )
    total_matching_items: int = Field(
        description="Sum of all matching item counts."
    )
    candidates: list[NameCandidate] | None = Field(
        default=None,
        description="Alternative names when the pattern is unknown.",
    )


class BlockTally(BaseModel):
    """How many blocks of one type are inside a analyzed region."""

    block_name: str = Field(description="Internal block name.")
    display_name: str = Field(description="Human-readable block name.")
    count: int = Field(ge=0, description="Cells of this type inside the region.")


class AreaReportResult(ToolOutcome):
    """Histogram of raytraceable blocks in a nearby region."""

    bounds: Box | None = Field(
        default=None, description="The analyzed region, inclusive corners."
    )
    blocks: list[BlockTally] = Field(
        description="Visible block types, most numerous first."
    )
    total_cells: int = Field(
        description="All cells in the region (width x height x depth)."
    )
    solid_cells: int = Field(
        description="Raytraceable cells with a full collision box."
    )
    air_cells: int = Field(
        description="Raytraceable empty cells."
    )
    unseen_cells: int = Field(
        description="Cells hidden by terrain and excluded from all block counts."
    )
    entities: list[EntityRef] = Field(
        default_factory=list,
        description="Raytraceable entities inside the region.",
    )


class ObstacleRef(BaseModel):
    """The single obstacle that blocks a previewed path."""

    block_name: str = Field(description="Internal name of the blocker.")
    position: Vec3i = Field(description="Cell of the blocker.")


class PathPreviewResult(ToolOutcome):
    """Dry-run pathfinding: can I walk there, how long, what blocks me."""

    state: Literal["reachable", "blocked", "unknown"] = Field(
        description="Path result. Unknown means that the search budget ended."
    )
    path_length: float | None = Field(
        ge=0,
        default=None,
        description="Route length in blocks, when reachable.",
    )
    hops: int | None = Field(
        ge=0,
        default=None,
        description="Pathfinding segments (high = many detours).",
    )
    estimated_seconds: float | None = Field(
        ge=0,
        default=None,
        description="Rough walking time at normal speed.",
    )
    blocker: ObstacleRef | None = Field(
        default=None,
        description="What makes the target unreachable: the first "
        "obstacle on the way (water gap, cliff, wall...).",
    )


class HazardRef(BaseModel):
    """One hazard detected around a cell you plan to dig."""

    kind: Literal["lava", "water", "cave", "fall", "fire", "entity"] = Field(
        description="Hazard category."
    )
    direction: Direction6 = Field(
        description="Where the hazard sits relative to the target cell."
    )
    position: Vec3i | None = Field(
        default=None,
        description="Hazard cell when visible. Hidden sounds have no cell.",
    )
    distance_band: Literal["immediate", "near", "audible"] = Field(
        description="Approximate distance. Hidden hazards never give exact distance."
    )
    note: str | None = Field(
        default=None, description="Consequence, e.g. 'water flows in "
        "when broken' or 'you will fall 12 blocks'."
    )


class SafetyReportResult(ToolOutcome):
    """Hazard report for a cell you plan to dig."""

    position: Vec3i = Field(description="The cell you probed.")
    risk: Literal["low_risk", "warning", "unknown"] = Field(
        description="Sensory risk estimate. Low risk is not a safety guarantee."
    )
    hazards: list[HazardRef] = Field(
        description="Hazards found around the cell."
    )
    will_fall: bool | None = Field(
        default=None,
        description="True when breaking the cell drops you into a hole.",
    )
    fall_depth: int | None = Field(
        default=None, description="How deep the drop is, when will_fall."
    )


class MemoryHit(BaseModel):
    """One memory note that matched a recall search."""

    kind: str = Field(description="Memory category of the note.")
    file: str = Field(description="Memory file the note lives in.")
    note_id: str = Field(description="Id of the note.")
    markdown: str = Field(description="The note text itself.")
    created_at: str = Field(description="When the note was written.")


class RecallResult(ToolOutcome):
    """Search results over your durable memory notes."""

    pattern: str = Field(description="The glob pattern you searched for.")
    hits: list[MemoryHit] = Field(
        description="Matching notes, newest first."
    )
    total_notes: int = Field(
        description="Notes in the whole memory (search space size)."
    )


class ScreenshotResult(ToolOutcome):
    """A fresh screenshot of the current view, nothing else."""

    image: ImageRef = Field(
        description="Metadata of the captured frame; pixels are attached "
        "as an image content part."
    )
