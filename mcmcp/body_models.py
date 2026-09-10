"""Models for data that crosses the Node body boundary."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from .models import (
    BlockCount,
    ContainerWindow,
    Direction6,
    EntityRef,
    InventoryItem,
    InventorySlot,
    PlayerStatus,
    Vec3f,
    Vec3i,
    ViewTransform,
    WalkDiagnostics,
)


class CatalogEntry(BaseModel):
    """One name in the Minecraft block or item registry."""

    model_config = ConfigDict(extra="forbid")

    name: str
    display_name: str


class BodyCatalog(BaseModel):
    """Names loaded for the configured Minecraft version."""

    model_config = ConfigDict(extra="forbid")

    blocks: list[CatalogEntry]
    items: list[CatalogEntry]


class BodyBlock(BaseModel):
    """One block cell that the Mineflayer body loaded."""

    model_config = ConfigDict(extra="forbid")

    position: Vec3i
    name: str
    display_name: str
    replaceable: bool


class BodyBlocks(BaseModel):
    """Block cells returned in request order."""

    model_config = ConfigDict(extra="forbid")

    blocks: list[BodyBlock]


class BodyState(BaseModel):
    """The current connection state of the Mineflayer body."""

    model_config = ConfigDict(extra="forbid")

    connected: bool
    spawned: bool
    death_count: int
    uptime_seconds: float
    dimension: str | None
    camera: ViewTransform | None
    inventory_count: int
    inventory: list[InventoryItem]
    player: PlayerStatus | None
    held_item: InventoryItem | None
    hotbar: list[InventorySlot]
    active_hotbar_slot: int | None


class BodyExposedBlock(BaseModel):
    """One exposed block found by the body scan."""

    model_config = ConfigDict(extra="forbid")

    position: Vec3i
    block_name: str
    display_name: str
    distance: float
    exposed_faces: list[Direction6]
    harvestable_with_held: bool


class BodyScanCoverage(BaseModel):
    """What part of the loaded world a scan looked at."""

    model_config = ConfigDict(extra="forbid")

    center: Vec3f
    chunks_loaded: int
    columns_scanned: int


class BodyFindBlocks(BaseModel):
    """Result of one body block scan."""

    model_config = ConfigDict(extra="forbid")

    blocks: list[BodyExposedBlock]
    total_matches: int
    coverage: BodyScanCoverage


class BodyRaytrace(BaseModel):
    """The first block the body view ray hits."""

    model_config = ConfigDict(extra="forbid")

    hit: bool
    hit_position: Vec3i | None
    hit_block: str | None
    hit_face: Direction6 | None
    distance: float | None


class BodyObserveSnapshot(BodyState):
    """The full body snapshot including nearby blocks and entities."""

    nearby_blocks: list[BlockCount]
    nearby_entities: list[EntityRef]


class BodyRotate(BaseModel):
    """Camera pose after a body rotation."""

    model_config = ConfigDict(extra="forbid")

    camera: ViewTransform


class BodyScreenshot(BaseModel):
    """One PNG returned by the local browser renderer."""

    model_config = ConfigDict(extra="forbid")

    png_base64: str
    width: int
    height: int


class BodyFineControl(BaseModel):
    """Observed result of one raw movement pulse."""

    model_config = ConfigDict(extra="forbid")

    controls: dict[str, bool]
    duration_ms: float
    pose_before: Vec3f
    pose_after: Vec3f
    camera: ViewTransform
    on_ground: bool
    frame: BodyScreenshot


class BodyWalk(BaseModel):
    """Observed result of one body pathfinding command."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    reason: str | None
    message: str | None
    status: Literal["reached", "partial", "no_path", "timeout"]
    requested: Vec3f
    final_position: Vec3f
    distance_remaining: float
    target_offset: Vec3f
    diagnostics: WalkDiagnostics
    hops: int
    camera: ViewTransform
    duration_ms: float


class BodyBlockRef(BaseModel):
    """One block cell that the body names as a path blocker."""

    model_config = ConfigDict(extra="forbid")

    block_name: str
    position: Vec3i


class BodyPathPreview(BaseModel):
    """Dry-run pathfinding result, computed without movement."""

    model_config = ConfigDict(extra="forbid")

    state: Literal["reachable", "blocked", "unknown"]
    path_length: float | None
    hops: int | None
    estimated_seconds: float | None
    blocker: BodyBlockRef | None
    duration_ms: float


class BodyUseBlock(BaseModel):
    """Observed result of one Mineflayer block activation."""

    model_config = ConfigDict(extra="forbid")

    action: Literal[
        "door_opened", "door_closed", "gate_opened", "gate_closed",
        "trapdoor_opened", "trapdoor_closed", "container_opened",
        "crafting_table_opened", "furnace_opened", "button_pressed",
        "lever_toggled", "bed_entered", "activated",
    ]
    window: ContainerWindow | None


class BodyStop(BaseModel):
    """What the body stopped and its resulting pose."""

    model_config = ConfigDict(extra="forbid")

    stopped_command: str | None
    stopped_skill: str | None
    camera: ViewTransform | None


class BodyEquip(BaseModel):
    previous_held: InventoryItem | None
    held_item: InventoryItem | None
    hotbar: list[InventorySlot]


class BodyUseItem(BaseModel):
    action: Literal["ate", "drank", "threw", "activated", "nothing"]
    reason: Literal["food_full", "not_usable"] | None
    item: InventoryItem | None
    before: BodyState
    after: BodyState


class BodyIngredientNeed(BaseModel):
    """One ingredient that the body reports as short."""

    model_config = ConfigDict(extra="forbid")

    item: str
    required: int
    have: int


class BodyCraft(BaseModel):
    ok: bool
    reason: str | None
    missing: list[BodyIngredientNeed]
    item: InventoryItem | None
    repetitions: int
    table: Vec3i | None


class BodyMine(BaseModel):
    ok: bool
    reason: Literal["unharvestable", "target_changed"] | None
    block: BodyBlock
    tool_used: str | None
    can_harvest: bool
    drops: list[str]


class BodyAttack(BaseModel):
    entity_id: int
    entity_type: str | None
    killed: bool
    interrupted: bool
    hits: int
    health: float | None
    drops: list[str]


class BodyChestMove(BaseModel):
    moved_count: int
    available_count: int
    inventory_space: int
    window: ContainerWindow | None


class BodySmelt(BaseModel):
    ok: bool
    reason: Literal["target_changed"] | None
    output: InventoryItem | None
    input_consumed: int
    fuel_consumed: int
    window: ContainerWindow | None


class BodyDrop(BaseModel):
    item: str | None
    dropped: int
    drop_position: Vec3f | None


class BodyEat(BaseModel):
    action: Literal["ate", "drank", "threw", "activated", "nothing"]
    item: InventoryItem | None
    considered: list[str]
    before: BodyState
    after: BodyState


class BodyEquipBest(BaseModel):
    target_block: str | None
    best_possible_tool: str | None
    previous_held: InventoryItem | None
    held_item: InventoryItem | None
    hotbar: list[InventorySlot]


class BodyHazard(BaseModel):
    kind: str
    direction: str
    position: Vec3i | None
    distance_band: str
    note: str | None


class BodySafety(BaseModel):
    risk: Literal["low_risk", "warning", "unknown"]
    hazards: list[BodyHazard]
    will_fall: bool | None
    fall_depth: int | None


class BodyCraftMax(BaseModel):
    reason: str | None
    missing: list[BodyIngredientNeed]
    item: str | None
    crafted: int
    table: Vec3i | None


class BodySleep(BaseModel):
    ok: bool
    reason: str | None
    slept: bool
    is_day_now: bool
    blocking_entity: EntityRef | None


class BodyPillar(BaseModel):
    ok: bool
    reason: str | None
    climbed: int
    blocks_placed: int
    camera: ViewTransform


class BodyIngredientLine(BaseModel):
    item: str
    required: int
    have: int


class BodyRecipeEntry(BaseModel):
    item_name: str
    display_name: str
    grid: str
    legend: dict[str, str]
    ingredients: list[BodyIngredientLine]
    output_count: int
    needs_crafting_table: bool
    craftable_now: bool


class BodyRecipeSearch(BaseModel):
    matches: list[BodyRecipeEntry]
    total_recipes: int


class BodyHorizonRay(BaseModel):
    heading_degrees: int
    cardinal: str
    pitch: int
    hit: bool
    block_name: str | None
    distance: float | None


class BodyHorizonSector(BaseModel):
    cardinal: str
    terrain: str
    notable_blocks: list[str]


class BodyHorizonLandmark(BaseModel):
    kind: str
    cardinal: str
    confidence: str
    evidence: list[str]


class BodyScanHorizon(BaseModel):
    origin: Vec3f
    rays: list[BodyHorizonRay]
    sectors: list[BodyHorizonSector]
    landmarks: list[BodyHorizonLandmark]
    duration_ms: float


class BodyStaircase(BaseModel):
    """Result of carving a descending staircase."""

    model_config = ConfigDict(extra="forbid")

    depth_requested: int
    depth_achieved: int
    end_position: Vec3f
    blocks_dug: int
    hazards_found: list[str]
    torches_placed: int


class BodySkillOutcome(BaseModel):
    """Result of running a sandboxed TypeScript skill."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "timeout", "stopped", "typescript_error", "access_denied"]
    reason: str | None
    stdout_tail: str | None
    stderr_tail: str | None
    heartbeats: int
    duration_ms: float
