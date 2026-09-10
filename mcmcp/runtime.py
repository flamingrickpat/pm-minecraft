"""Coordinate typed Minecraft tools and the small backend primitives.

Invalid tool arguments stop at the FastMCP and Pydantic boundary.
A missing player body is an expected protocol error for body-dependent tools.
An unimplemented tool raises `NotImplementedError` and retains its traceback.
Body, RCON, file, and model errors retain their original exceptions.
"""

from __future__ import annotations

from fnmatch import fnmatchcase
import json
import math
import os
import re
import time
from typing import Literal
from uuid import uuid4

from .body import MinecraftBody
from .body_models import BodyBlock, BodyState
from .config import Configuration
from .constants import (
    STATE_SYNC_SECONDS,
    RESPAWN_SECONDS,
    BUILD_CELL_LIMIT,
    BUILD_DISTANCE_BLOCKS,
    EXACT_WALK_SECONDS,
    FINE_CONTROL_MILLISECONDS,
    FURNACE_DISTANCE_BLOCKS,
    FIND_BLOCK_DOWN_BLOCKS,
    FIND_BLOCK_HORIZONTAL_BLOCKS,
    FIND_BLOCK_RESULT_LIMIT,
    FIND_BLOCK_UP_BLOCKS,
    INTERACTABLE_RADIUS_BLOCKS,
    INTERACTABLE_RESULT_LIMIT,
    LOCAL_PATH_DISTANCE_BLOCKS,
    OBSERVE_RADIUS_BLOCKS,
    PATH_SEARCH_SECONDS,
    PILLAR_UP_BLOCK_LIMIT,
    RECIPE_RESULT_LIMIT,
    SKILL_SECONDS,
    SURFACE_WALK_SECONDS,
    VISIBLE_WALK_SECONDS,
    VISIBLE_AREA_DOWN_BLOCKS,
    VISIBLE_AREA_HORIZONTAL_BLOCKS,
    VISIBLE_AREA_UP_BLOCKS,
    WAYPOINT_CAPACITY,
)
from .geometry import build_cells
from .memory import AgentMemory
from .models import (
    AddWaypointResult,
    AreaReportResult,
    AttackEntityResult,
    BlockCount,
    BlockRef,
    BlockTally,
    Box,
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
    ExposedBlock,
    FineControlResult,
    FindBlockResult,
    FindInteractablesResult,
    HarvestTreeResult,
    HazardRef,
    HorizonLandmark,
    HorizonRay,
    HorizonSector,
    InfoResult,
    InspectBlockResult,
    InteractableRef,
    InventoryChange,
    InventoryDelta,
    IngredientNeed,
    InventoryItem,
    ListCapabilitiesResult,
    ListWaypointsResult,
    MineBlockResult,
    MineVeinResult,
    NeighborCell,
    ObserveResult,
    ObstacleRef,
    PathPreviewResult,
    PickupStatus,
    PillarUpResult,
    PlacedCell,
    PostconditionReport,
    RaytraceResult,
    RecallResult,
    RecipeEntry,
    RecipeSearchResult,
    RelativePositionResult,
    RememberResult,
    RespawnResult,
    RotateResult,
    SafetyReportResult,
    ScanHorizonResult,
    ScreenshotResult,
    SearchCoverage,
    SleepResult,
    SmeltItemResult,
    StaircaseResult,
    StopResult,
    UseBlockResult,
    UseItemResult,
    Vec3f,
    Vec3i,
    WalkResult,
)
from .names import candidates, glob_candidates, matching
from .server_assist import ServerAssist


class MinecraftRuntime:
    """Own one body, one character workspace, and one server assist."""

    def __init__(self, configuration: Configuration):
        self.configuration = configuration
        self.memory = AgentMemory(configuration.agent_home)
        self.assist = ServerAssist(configuration)
        self.assist.require_babymode()
        self.body: MinecraftBody | None = MinecraftBody(configuration)
        self._require_same_server("startup")
        self._last_body_death_count = 0
        self._last_body_uptime_seconds = 0.0
        self._test_interrupted_entities: set[int] = set()
        self._stop_generation = 0
        self._last_tool_state: BodyState | None = None

    def call_with_warnings(self, method, *args, **kwargs):
        body = self.body
        if body is None or not body.alive:
            return method(*args, **kwargs)
        before = body.state()
        warnings = [] if self._last_tool_state is None else _equipment_warnings(self._last_tool_state, before)
        result = method(*args, **kwargs)
        after = body.state()
        deliberate = {"minecraft_equip", "minecraft_equip_best_tool", "minecraft_eat_best", "minecraft_use_item",
                      "minecraft_drop_item", "minecraft_discard_items", "minecraft_chest_deposit", "minecraft_suicide"}
        if method.__name__ not in deliberate:
            warnings.extend(_equipment_warnings(before, after))
        result.warnings.extend(warnings)
        self._last_tool_state = after
        return result

    def start_body(self) -> None:
        """Start the body for a test handoff without restarting the MCP."""
        if self.body is not None and not self.body.alive:
            self.body.close()
            self.body = None
        if self.body is None:
            self.body = MinecraftBody(self.configuration)
            self._require_same_server("body handoff")

    def _require_same_server(self, phase: str) -> None:
        """Exit if RCON and Mineflayer point to different server instances.

        This is not a port-number check. It asks RCON to execute a command
        as the Mineflayer player. If the player does not exist on the RCON
        server, the game port and RCON port point to different processes
        (or RCON is disabled on the target server).
        """
        deadline = time.monotonic() + 3
        same = self.assist.has_player()
        while not same and time.monotonic() < deadline:
            time.sleep(0.1)
            same = self.assist.has_player()
        if not same:
            print(
                f"Minecraft {phase} failed: Mineflayer"
                f" {self.configuration.minecraft_host}:{self.configuration.minecraft_port}"
                " and RCON"
                f" {self.configuration.rcon_host}:{self.configuration.rcon_port}"
                " are connected to different servers.",
                flush=True,
            )
            os._exit(1)

    def stop_body(self) -> None:
        """Release the Minecraft username while keeping the MCP transport live."""
        if self.body is None:
            return
        if self.body.alive:
            state = self.body.state()
            self._last_body_death_count = state.death_count
            self._last_body_uptime_seconds = state.uptime_seconds
        self.body.close()
        self.body = None

    def reset_test_state(self) -> None:
        """Clear mutable character files between live test cases."""
        self.memory.reset()
        self._test_interrupted_entities.clear()
        self._last_tool_state = None

    def mark_test_entity_interrupted(self, entity_id: int) -> None:
        """Record one test-controlled concurrent entity removal."""
        self._test_interrupted_entities.add(entity_id)

    def minecraft_stop(
        self, scope: Literal["command", "skill", "both"] = "both"
    ) -> StopResult:
        if scope in ("command", "both"):
            self._stop_generation += 1
        if self.body is None:
            return StopResult(
                ok=True,
                scope=scope,
                stopped_command=None,
                stopped_skill=None,
                camera=None,
            )
        body = self._body()
        stopped = body.stop(scope)
        state = body.state()
        return StopResult(
            ok=True,
            scope=scope,
            stopped_command=stopped.stopped_command,
            stopped_skill=stopped.stopped_skill,
            camera=state.camera,
        )

    def minecraft_remember(
        self,
        kind: Literal["world", "places", "routes", "chests", "failures", "journal"],
        markdown: str,
    ) -> RememberResult:
        note, count = self.memory.remember(kind, markdown)
        return RememberResult(
            ok=True,
            kind=kind,
            note_id=note.note_id,
            file=note.file,
            notes_in_file=count,
            appended_chars=len(markdown),
        )

    def minecraft_recall(self, pattern: str) -> RecallResult:
        hits, total = self.memory.recall(pattern)
        if not hits:
            return RecallResult(
                ok=False,
                reason="not_found",
                message=f"Memory text was not found for pattern: {pattern}",
                pattern=pattern,
                hits=[],
                total_notes=total,
            )
        return RecallResult(
            ok=True,
            pattern=pattern,
            hits=hits,
            total_notes=total,
        )

    def minecraft_add_waypoint(
        self, description: str, position: Vec3i | None = None
    ) -> AddWaypointResult:
        if position is None:
            state = self._require_body()
            position = state.camera.block_position
            dimension = state.dimension
        else:
            dimension = "overworld"
        waypoint, waypoints, evicted = self.memory.add_waypoint(
            description,
            position,
            dimension,
        )
        return AddWaypointResult(
            ok=True,
            waypoint=waypoint,
            waypoints=waypoints,
            evicted=evicted,
        )

    def minecraft_list_waypoints(self) -> ListWaypointsResult:
        return ListWaypointsResult(
            ok=True,
            waypoints=self.memory.list_waypoints(),
            capacity=WAYPOINT_CAPACITY,
        )

    def minecraft_list_capabilities(self) -> ListCapabilitiesResult:
        return ListCapabilitiesResult(ok=True, skills=self.memory.list_capabilities())

    def minecraft_info(self) -> InfoResult:
        configuration = self.configuration
        state = None if self.body is None else self.body.state()
        return InfoResult(
            ok=True,
            username=configuration.player_name,
            server=f"{configuration.minecraft_host}:{configuration.minecraft_port}",
            body_url=f"http://{configuration.body_host}:{configuration.body_port}",
            agent_home=str(configuration.agent_home),
            connected=False if state is None else state.connected,
            spawned=False if state is None else state.spawned,
            death_count=self._last_body_death_count if state is None else state.death_count,
            schema_version="2.0",
            uptime_seconds=self._last_body_uptime_seconds if state is None else state.uptime_seconds,
        )

    def minecraft_suicide(self, reason: str) -> RespawnResult:
        generation = self._stop_generation
        before = self._require_body()
        self.assist.kill_player()
        after, failure = self._wait_until(
            self.body.state,
            lambda state: state.death_count > before.death_count and state.spawned,
            RESPAWN_SECONDS,
            generation,
        )
        return RespawnResult(
            ok=failure is None,
            reason=failure,
            message=None if failure is None else f"Respawn confirmation {failure}.",
            deaths=after.death_count,
            respawn_position=after.camera.feet_position if failure is None else None,
            cause=reason,
            inventory_lost=after.inventory_count < before.inventory_count,
        )

    def minecraft_relative(
        self, forward: int = 0, right: int = 0, up: int = 0
    ) -> RelativePositionResult:
        state = self._require_body()
        camera = state.camera
        yaw = math.radians(camera.yaw)
        # Mineflayer yaw zero faces north. Minecraft command yaw zero faces south.
        dx = -math.sin(yaw) * forward + math.cos(yaw) * right
        dz = -math.cos(yaw) * forward - math.sin(yaw) * right
        cell = Vec3i(
            x=camera.block_position.x + round(dx),
            y=camera.block_position.y + up,
            z=camera.block_position.z + round(dz),
        )
        return RelativePositionResult(ok=True, cell=cell, camera=camera)

    def minecraft_distance(self, a: Vec3f, b: Vec3f) -> DistanceResult:
        dx = b.x - a.x
        dy = b.y - a.y
        dz = b.z - a.z
        return DistanceResult(
            ok=True,
            distance=math.sqrt(dx * dx + dy * dy + dz * dz),
            manhattan=abs(dx) + abs(dy) + abs(dz),
            dx=dx,
            dy=dy,
            dz=dz,
        )

    def _require_body(self) -> BodyState:
        body = self._body()
        state = body.state()
        if not state.connected or not state.spawned or state.camera is None:
            raise RuntimeError("The player body is not available.")
        return state

    def _body(self) -> MinecraftBody:
        if self.body is None:
            raise RuntimeError("The player body is not available.")
        return self.body

    def minecraft_observe(self, include_image: bool = True) -> ObserveResult:
        state = self._require_body()
        snapshot = self.body.observe(OBSERVE_RADIUS_BLOCKS)
        return ObserveResult(
            ok=True,
            camera=snapshot.camera,
            player=snapshot.player,
            held_item=snapshot.held_item,
            hotbar=snapshot.hotbar,
            inventory=snapshot.inventory,
            nearby_blocks=snapshot.nearby_blocks,
            nearby_entities=snapshot.nearby_entities,
            image=self.body.screenshot() if include_image else None,
        )

    def minecraft_find_block(self, pattern: str) -> FindBlockResult:
        state = self._require_body()
        started = time.monotonic()
        catalog = self.body.catalog()
        resolved = matching(pattern, catalog.blocks)
        if not resolved:
            return FindBlockResult(
                ok=False,
                reason="not_found",
                message=f"The block name was not found: {pattern}",
                pattern=pattern,
                matched_types=[],
                total_matches=0,
                nearest=None,
                results=[],
                coverage=None,
                candidates=candidates(pattern, catalog.blocks),
                duration_ms=(time.monotonic() - started) * 1000,
            )
        names = [entry.name for entry in resolved]
        found = self.body.find_blocks({
            "center": state.camera.feet_position.model_dump(),
            "names": names,
            "horizontal": FIND_BLOCK_HORIZONTAL_BLOCKS,
            "up": FIND_BLOCK_UP_BLOCKS,
            "down": FIND_BLOCK_DOWN_BLOCKS,
            "limit": FIND_BLOCK_RESULT_LIMIT,
        })
        blocks = found.blocks
        if not blocks:
            return FindBlockResult(
                ok=False,
                reason="not_found",
                message=f"{pattern} was not found within the search bounds.",
                pattern=pattern,
                matched_types=names,
                total_matches=0,
                nearest=None,
                results=[],
                coverage=self._coverage(state.camera, FIND_BLOCK_HORIZONTAL_BLOCKS, FIND_BLOCK_UP_BLOCKS, FIND_BLOCK_DOWN_BLOCKS, found),
                candidates=None,
                duration_ms=(time.monotonic() - started) * 1000,
            )
        results = [
            ExposedBlock(
                position=block.position,
                block_name=block.block_name,
                display_name=block.display_name,
                distance=block.distance,
                exposed_faces=block.exposed_faces,
                harvestable_with_held=block.harvestable_with_held,
            )
            for block in blocks[:FIND_BLOCK_RESULT_LIMIT]
        ]
        return FindBlockResult(
            ok=True,
            pattern=pattern,
            matched_types=sorted({block.block_name for block in blocks}),
            total_matches=found.total_matches,
            nearest=results[0],
            results=results,
            coverage=self._coverage(state.camera, FIND_BLOCK_HORIZONTAL_BLOCKS, FIND_BLOCK_UP_BLOCKS, FIND_BLOCK_DOWN_BLOCKS, found),
            candidates=None,
            duration_ms=(time.monotonic() - started) * 1000,
        )

    def minecraft_inspect_block(
        self, position: Vec3i, include_image: bool = False
    ) -> InspectBlockResult:
        self._require_body()
        center_block = self.body.blocks([position]).blocks[0]
        if center_block.name in void_blocks:
            return InspectBlockResult(
                ok=False,
                reason="not_found",
                message=f"No block exists at {position.x}, {position.y}, {position.z}.",
                position=position,
                block_name="air",
                display_name="Air",
                is_solid=False,
                exposed_faces=[],
                neighbors=[],
                image=None,
            )
        offsets = [
            ("north", 0, 0, -1),
            ("south", 0, 0, 1),
            ("east", 1, 0, 0),
            ("west", -1, 0, 0),
            ("up", 0, 1, 0),
            ("down", 0, -1, 0),
        ]
        neighbor_positions = [
            Vec3i(x=position.x + dx, y=position.y + dy, z=position.z + dz)
            for _, dx, dy, dz in offsets
        ]
        neighbor_blocks = self.body.blocks(neighbor_positions).blocks
        neighbors = [
            NeighborCell(
                direction=direction,
                position=cell,
                block_name=block.name,
                solid=not block.replaceable,
            )
            for (direction, *_offset), cell, block in zip(offsets, neighbor_positions, neighbor_blocks)
        ]
        exposed = [
            direction
            for (direction, *_offset), block in zip(offsets, neighbor_blocks)
            if block.replaceable
        ]
        return InspectBlockResult(
            ok=True,
            position=position,
            block_name=center_block.name,
            display_name=center_block.display_name,
            is_solid=not center_block.replaceable,
            exposed_faces=exposed,
            neighbors=neighbors,
            image=self.body.screenshot() if include_image else None,
        )

    def minecraft_find_interactables(
        self, pattern: str = "*"
    ) -> FindInteractablesResult:
        state = self._require_body()
        started = time.monotonic()
        catalog = self.body.catalog()
        matched = [
            entry for entry in catalog.blocks
            if _matches(pattern, entry.name) and interactable_kind(entry.name) is not None
        ]
        if not matched:
            return FindInteractablesResult(
                ok=False,
                reason="not_found",
                message=f"The interactable block name was not found: {pattern}",
                pattern=pattern,
                results=[],
                coverage=None,
                candidates=candidates(pattern, catalog.blocks),
                duration_ms=(time.monotonic() - started) * 1000,
            )
        names = [entry.name for entry in matched]
        found = self.body.find_blocks({
            "center": state.camera.feet_position.model_dump(),
            "names": names,
            "horizontal": INTERACTABLE_RADIUS_BLOCKS,
            "up": INTERACTABLE_RADIUS_BLOCKS,
            "down": INTERACTABLE_RADIUS_BLOCKS,
            "limit": INTERACTABLE_RESULT_LIMIT,
        })
        blocks = [
            block for block in found.blocks
            if block.distance <= INTERACTABLE_RADIUS_BLOCKS
        ]
        if not blocks:
            return FindInteractablesResult(
                ok=False,
                reason="not_found",
                message=f"The interactable block was not found within {INTERACTABLE_RADIUS_BLOCKS} blocks.",
                pattern=pattern,
                results=[],
                coverage=self._coverage(state.camera, INTERACTABLE_RADIUS_BLOCKS, INTERACTABLE_RADIUS_BLOCKS, INTERACTABLE_RADIUS_BLOCKS, found),
                candidates=None,
                duration_ms=(time.monotonic() - started) * 1000,
            )
        results = [
            InteractableRef(
                position=block.position,
                block_name=block.block_name,
                display_name=block.display_name,
                kind=interactable_kind(block.block_name),
                distance=block.distance,
                state=None,
            )
            for block in blocks[:INTERACTABLE_RESULT_LIMIT]
        ]
        return FindInteractablesResult(
            ok=True,
            pattern=pattern,
            results=results,
            coverage=self._coverage(state.camera, INTERACTABLE_RADIUS_BLOCKS, INTERACTABLE_RADIUS_BLOCKS, INTERACTABLE_RADIUS_BLOCKS, found),
            candidates=None,
            duration_ms=(time.monotonic() - started) * 1000,
        )

    def minecraft_raytrace(self, include_image: bool = False) -> RaytraceResult:
        state = self._require_body()
        result = self.body.raytrace()
        return RaytraceResult(
            ok=True,
            hit=result.hit,
            hit_position=result.hit_position,
            hit_block=result.hit_block,
            hit_face=result.hit_face,
            distance=result.distance,
            camera=state.camera,
            image=self.body.screenshot() if include_image else None,
        )

    def minecraft_scan_horizon(
        self, include_image: bool = False
    ) -> ScanHorizonResult:
        self._require_body()
        result = self.body.scan_horizon()
        image = self.body.screenshot() if include_image else None
        return ScanHorizonResult(
            ok=True,
            reason=None,
            message=None,
            origin=result.origin,
            rays=[
                HorizonRay(
                    heading_degrees=ray.heading_degrees,
                    cardinal=ray.cardinal,
                    pitch=ray.pitch,
                    hit=ray.hit,
                    block_name=ray.block_name,
                    distance=ray.distance,
                )
                for ray in result.rays
            ],
            sectors=[
                HorizonSector(
                    cardinal=sector.cardinal,
                    terrain=sector.terrain,
                    notable_blocks=sector.notable_blocks,
                )
                for sector in result.sectors
            ],
            landmarks=[
                HorizonLandmark(
                    kind=landmark.kind,
                    cardinal=landmark.cardinal,
                    confidence=landmark.confidence,
                    evidence=landmark.evidence,
                )
                for landmark in result.landmarks
            ],
            image=image,
            duration_ms=max(result.duration_ms, FINE_CONTROL_MILLISECONDS),
        )

    def minecraft_recipe_search(
        self, pattern: str = "*", craftable_now: bool | None = None
    ) -> RecipeSearchResult:
        self._require_body()
        catalog = self.body.catalog()
        matched = matching(pattern, catalog.items)
        if not matched:
            return RecipeSearchResult(
                ok=False,
                reason="not_found",
                message=f"The recipe was not found for the pattern: {pattern}",
                pattern=pattern,
                matches=[],
                total_recipes=0,
                duration_ms=0.0,
                candidates=candidates(pattern, catalog.items),
            )
        started = time.monotonic()
        names = [value.name for value in matched]
        result = self.body.recipe_search(names, craftable_now, RECIPE_RESULT_LIMIT)
        return RecipeSearchResult(
            ok=True,
            reason=None,
            message=None,
            pattern=pattern,
            matches=[
                RecipeEntry(
                    item_name=entry.item_name,
                    display_name=entry.display_name,
                    grid=entry.grid,
                    legend=entry.legend,
                    ingredients=_ingredient_lines(entry.ingredients),
                    output_count=entry.output_count,
                    needs_crafting_table=entry.needs_crafting_table,
                    craftable_now=entry.craftable_now,
                )
                for entry in result.matches
            ],
            total_recipes=result.total_recipes,
            duration_ms=(time.monotonic() - started) * 1000,
        )

    def minecraft_craft_item(
        self, item: str, repetitions: int = 1
    ) -> CraftItemResult:
        before = self._require_body()
        matched = matching(item, self.body.catalog().items)
        if not matched:
            return CraftItemResult(ok=False, reason="not_found", message=f"The item name was not found: {item}", requested=item, resolved_item=None, repetitions_requested=repetitions, repetitions_crafted=0, output=None, inventory_delta=None, hotbar=before.hotbar, crafting_table_used=None, candidates=candidates(item, self.body.catalog().items), missing_ingredients=None)
        if len(matched) > 1:
            return CraftItemResult(ok=False, reason="ambiguous", message="Multiple items matched. Use one exact name.", requested=item, resolved_item=None, repetitions_requested=repetitions, repetitions_crafted=0, output=None, inventory_delta=None, hotbar=before.hotbar, crafting_table_used=None, candidates=glob_candidates(matched), missing_ingredients=None)
        selected = matched[0].name
        result = self.body.craft(selected, repetitions)
        if not result.ok:
            return CraftItemResult(
                ok=False,
                reason=result.reason or "not_craftable",
                message=_craft_failure_message(result.reason, selected),
                requested=item,
                resolved_item=selected,
                repetitions_requested=repetitions,
                repetitions_crafted=0,
                output=None,
                inventory_delta=None,
                hotbar=before.hotbar,
                crafting_table_used=result.table,
                candidates=None,
                missing_ingredients=_ingredient_needs(result.missing, before.inventory),
            )
        after = self.body.state()
        output = next((value for value in after.inventory if value.name == selected), None)
        return CraftItemResult(ok=True, requested=item, resolved_item=selected, repetitions_requested=repetitions, repetitions_crafted=result.repetitions, output=output, inventory_delta=_inventory_delta(before.inventory, after.inventory), hotbar=after.hotbar, crafting_table_used=result.table, candidates=None, missing_ingredients=None)

    def minecraft_equip(self, item: str) -> EquipResult:
        before = self._require_body()
        matched = matching(item, before.inventory)
        if not matched:
            return EquipResult(ok=False, reason="not_found", message=f"The inventory item was not found: {item}", requested=item, equipped=None, previous_held=before.held_item, hotbar=before.hotbar, candidates=candidates(item, before.inventory))
        if len(matched) > 1:
            return EquipResult(ok=False, reason="ambiguous", message="Multiple inventory items matched. Use one exact name.", requested=item, equipped=None, previous_held=before.held_item, hotbar=before.hotbar, candidates=glob_candidates(matched))
        result = self.body.equip(matched[0].name)
        return EquipResult(ok=True, requested=item, equipped=result.held_item, previous_held=result.previous_held, hotbar=result.hotbar, candidates=None)

    def minecraft_use_item(self) -> UseItemResult:
        before = self._require_body()
        if before.held_item is None:
            return UseItemResult(ok=False, reason="no_held_item", message="There is no item in the main hand.", action=None, item=None, stat_delta=None, inventory_delta=None)
        result = self.body.use_item()
        after = result.after
        player_before = before.player
        player_after = after.player
        stat_delta = None if player_before is None or player_after is None else _stat_delta(player_before, player_after)
        if result.reason == "food_full":
            return UseItemResult(ok=False, reason="food_full", message="Your food is already full.", action="nothing", item=result.item, stat_delta=stat_delta, inventory_delta=_inventory_delta(before.inventory, after.inventory))
        if result.reason == "not_usable":
            return UseItemResult(ok=False, reason="not_usable", message=f"The held item cannot be used: {result.item.name}.", action="nothing", item=result.item, stat_delta=stat_delta, inventory_delta=_inventory_delta(before.inventory, after.inventory))
        return UseItemResult(ok=True, action=result.action, item=result.item, stat_delta=stat_delta, inventory_delta=_inventory_delta(before.inventory, after.inventory))

    def minecraft_smelt_item(
        self,
        input: str,
        input_count: int = 1,
        fuel: str | None = None,
        fuel_count: int = 1,
    ) -> SmeltItemResult:
        before = self._require_body()
        input_matches = matching(input, before.inventory)
        fuel_matches = matching(fuel or "coal", before.inventory)
        if len(input_matches) != 1 or len(fuel_matches) != 1:
            ambiguous = len(input_matches) > 1 or len(fuel_matches) > 1
            return SmeltItemResult(ok=False, reason="ambiguous" if ambiguous else "missing", message="Input and fuel must each match one inventory item.", furnace=None, input_item=None, input_consumed=0, fuel_item=None, fuel_consumed=0, output=None, inventory_delta=None, duration_ms=0, missing=None)
        input = input_matches[0].name
        fuel_name = fuel_matches[0].name
        available = _inventory_counts(before.inventory)
        missing = []
        if available.get(input, 0) < input_count:
            missing.append(__import__("mcmcp.models", fromlist=["IngredientNeed"]).IngredientNeed(item=input, display_name=input.replace("_", " "), required=input_count, have=available.get(input, 0), missing=input_count - available.get(input, 0)))
        if available.get(fuel_name, 0) < fuel_count:
            missing.append(__import__("mcmcp.models", fromlist=["IngredientNeed"]).IngredientNeed(item=fuel_name, display_name=fuel_name.replace("_", " "), required=fuel_count, have=available.get(fuel_name, 0), missing=fuel_count - available.get(fuel_name, 0)))
        if missing:
            return SmeltItemResult(ok=False, reason="missing", message="Input or fuel is missing.", furnace=None, input_item=input, input_consumed=0, fuel_item=fuel_name, fuel_consumed=0, output=None, inventory_delta=None, duration_ms=0, missing=missing)
        furnaces = self.minecraft_find_interactables("furnace")
        if not furnaces.ok:
            return SmeltItemResult(ok=False, reason="furnace_not_found", message="No nearby furnace was found.", furnace=None, input_item=input, input_consumed=0, fuel_item=fuel_name, fuel_consumed=0, output=None, inventory_delta=None, duration_ms=0, missing=None)
        nearby_furnaces = [
            entry for entry in furnaces.results
            if entry.distance <= FURNACE_DISTANCE_BLOCKS
        ]
        if not nearby_furnaces:
            return SmeltItemResult(ok=False, reason="furnace_not_found", message="No furnace was found within range.", furnace=None, input_item=input, input_consumed=0, fuel_item=fuel_name, fuel_consumed=0, output=None, inventory_delta=None, duration_ms=0, missing=None)
        furnace = nearby_furnaces[0].position
        self.minecraft_walk_to_visible(furnace.x, furnace.y, furnace.z)
        started = time.monotonic()
        result = self.body.smelt(furnace, input, input_count, fuel_name, fuel_count)
        after = self.body.state()
        if not result.ok:
            return SmeltItemResult(ok=False, reason="target_changed", message="The furnace target changed during the action.", furnace=furnace, input_item=input, input_consumed=result.input_consumed, fuel_item=fuel_name, fuel_consumed=result.fuel_consumed, output=None, inventory_delta=_inventory_delta(before.inventory, after.inventory), duration_ms=(time.monotonic() - started) * 1000, missing=None)
        output = result.output
        return SmeltItemResult(ok=True, furnace=furnace, input_item=input, input_consumed=result.input_consumed, fuel_item=fuel_name, fuel_consumed=result.fuel_consumed, output=output, inventory_delta=_inventory_delta(before.inventory, after.inventory), duration_ms=(time.monotonic() - started) * 1000, missing=None)

    def minecraft_mine_block(self, position: Vec3i) -> MineBlockResult:
        before = self._require_body()
        state = before.camera
        block = self.body.blocks([position]).blocks[0]
        if block.name in void_blocks:
            return MineBlockResult(ok=False, reason="not_found", message="The target block was not found; no solid block exists there.", block=None, tool_used=None, can_harvest=None, pickup=None, inventory_delta=None, image=None, duration_ms=0)
        if state is not None and _distance(state.feet_position, position) > 5:
            return MineBlockResult(ok=False, reason="target_out_of_range", message="The target block is out of range.", block=None, tool_used=None, can_harvest=None, pickup=None, inventory_delta=None, image=None, duration_ms=0)
        started = time.monotonic()
        result = self.body.mine(position)
        after = self.body.state()
        mined = BlockRef(position=position, block_name=block.name, display_name=block.display_name)
        if result.reason == "target_changed":
            return MineBlockResult(ok=False, reason="target_changed", message="The target block changed during mining.", block=mined, tool_used=result.tool_used, can_harvest=result.can_harvest, pickup=None, inventory_delta=_inventory_delta(before.inventory, after.inventory), image=self.body.screenshot(), duration_ms=(time.monotonic() - started) * 1000)
        if not result.can_harvest:
            return MineBlockResult(ok=False, reason="unharvestable", message="The held tool cannot harvest this block.", block=mined, tool_used=result.tool_used, can_harvest=False, pickup=None, inventory_delta=None, image=None, duration_ms=(time.monotonic() - started) * 1000)
        gained = _inventory_delta(before.inventory, after.inventory)
        gained_counts = {change.item: max(0, change.delta) for change in gained.changes}
        picked_up = all(gained_counts.get(item, 0) >= result.drops.count(item) for item in set(result.drops))
        pickup = None if not result.drops else PickupStatus(
            picked_up=picked_up,
            drop_items=result.drops,
            drop_hint=None if picked_up else f"Drops remain near {position.x}, {position.y}, {position.z}.",
        )
        return MineBlockResult(ok=True, block=mined, tool_used=result.tool_used, can_harvest=result.can_harvest, pickup=pickup, inventory_delta=gained, image=self.body.screenshot(), duration_ms=(time.monotonic() - started) * 1000)

    def minecraft_build(
        self,
        shape: Literal[
            "fill", "shell", "wall", "floor", "ceiling", "column",
            "staircase", "bridge", "frame",
        ],
        material: str,
        start: Vec3i,
        end: Vec3i | None = None,
        ref: Vec3i | None = None,
        include_image: bool = False,
    ) -> BuildResult:
        started = time.monotonic()
        generation = self._stop_generation
        state = self._require_body()
        cells, bounds = build_cells(shape, start, end, ref)
        if len(cells) > BUILD_CELL_LIMIT:
            return BuildResult(
                ok=False,
                reason="cell_limit",
                message=f"The build has more than {BUILD_CELL_LIMIT} cells.",
                shape=shape,
                material_requested=material,
                material_resolved=None,
                bounds=bounds,
                planned_cells=len(cells),
                placed_count=0,
                placed=[],
                occupied=[],
                out_of_range=[],
                missing_material_cells=0,
                inventory_delta=None,
                candidates=None,
                image=None,
                duration_ms=(time.monotonic() - started) * 1000,
            )

        catalog = self.body.catalog()
        resolved = matching(material, catalog.blocks)
        if not resolved:
            return BuildResult(
                ok=False,
                reason="not_found",
                message=f"The block material was not found: {material}",
                shape=shape,
                material_requested=material,
                material_resolved=None,
                bounds=bounds,
                planned_cells=len(cells),
                placed_count=0,
                placed=[],
                occupied=[],
                out_of_range=[],
                missing_material_cells=0,
                inventory_delta=None,
                candidates=candidates(material, catalog.blocks),
                image=None,
                duration_ms=(time.monotonic() - started) * 1000,
            )
        if len(resolved) > 1:
            return BuildResult(
                ok=False,
                reason="ambiguous",
                message="Multiple block materials matched. Use one exact name.",
                shape=shape,
                material_requested=material,
                material_resolved=None,
                bounds=bounds,
                planned_cells=len(cells),
                placed_count=0,
                placed=[],
                occupied=[],
                out_of_range=[],
                missing_material_cells=0,
                inventory_delta=None,
                candidates=glob_candidates(resolved),
                image=None,
                duration_ms=(time.monotonic() - started) * 1000,
            )

        material_name = resolved[0].name
        feet = state.camera.feet_position
        in_range = [
            cell
            for cell in cells
            if math.dist(
                (feet.x, feet.y, feet.z),
                (cell.x, cell.y, cell.z),
            ) <= BUILD_DISTANCE_BLOCKS
        ]
        out_of_range = [cell for cell in cells if cell not in in_range]
        if not in_range:
            return BuildResult(
                ok=False,
                reason="out_of_range",
                message="All build cells are out of range.",
                shape=shape,
                material_requested=material,
                material_resolved=material_name,
                bounds=bounds,
                planned_cells=len(cells),
                placed_count=0,
                placed=[],
                occupied=[],
                out_of_range=out_of_range,
                missing_material_cells=0,
                inventory_delta=None,
                candidates=None,
                image=None,
                duration_ms=(time.monotonic() - started) * 1000,
            )

        blocks = self.body.blocks(in_range).blocks
        occupied = [
            PlacedCell(position=block.position, block_name=block.name)
            for block in blocks
            if not block.replaceable
        ]
        open_cells = [block.position for block in blocks if block.replaceable]
        available = _inventory_counts(state.inventory).get(material_name, 0)
        selected = open_cells[:available]
        missing = len(open_cells) - len(selected)
        replies = self.assist.place_cells(material_name, selected)
        accepted = [
            cell
            for cell, reply in zip(selected, replies, strict=True)
            if "Changed the block" in reply
        ]
        rejected = [reply for reply in replies if "Changed the block" not in reply]
        placed_blocks, sync_failure = (
            self._wait_for_blocks(accepted, material_name, generation, 2)
            if accepted
            else ([], None)
        )
        placed = [
            PlacedCell(position=block.position, block_name=block.name)
            for block in placed_blocks
            if block.name == material_name
        ]
        if placed:
            self.assist.remove_items(material_name, len(placed))
        after = self.body.state()
        failure = "server_rejected" if rejected else (
            "state_sync_failed" if sync_failure else None
        )
        complete = failure is None and len(placed) == len(cells)
        reason = failure or ("occupied" if occupied and not placed else (None if complete else "partial"))
        message = (
            rejected[0]
            if rejected
            else "Placement did not appear in Mineflayer within two seconds."
            if sync_failure
            else f"Block occupied: {occupied[0].block_name} at {occupied[0].position.x}, {occupied[0].position.y}, {occupied[0].position.z}."
            if occupied and not placed
            else None if complete else "The build is partial."
        )
        return BuildResult(
            ok=complete,
            reason=reason,
            message=message,
            shape=shape,
            material_requested=material,
            material_resolved=material_name,
            bounds=bounds,
            planned_cells=len(cells),
            placed_count=len(placed),
            placed=placed,
            occupied=occupied,
            out_of_range=out_of_range,
            missing_material_cells=missing,
            inventory_delta=_inventory_delta(state.inventory, after.inventory),
            candidates=None,
            image=None,
            duration_ms=(time.monotonic() - started) * 1000,
        )

    def minecraft_rotate(
        self,
        yaw_degrees: float = 0.0,
        pitch_degrees: float = 0.0,
        absolute: bool = False,
    ) -> RotateResult:
        before = self._require_body().camera
        after = self.body.rotate(yaw_degrees, pitch_degrees, absolute).camera
        return RotateResult(
            ok=True,
            camera=after,
            yaw_delta=_angle_delta(after.yaw, before.yaw),
            pitch_delta=after.pitch - before.pitch,
            image=self.body.screenshot(),
        )

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
        self._require_body()
        controls = {
            "forward": forward,
            "back": back,
            "left": left,
            "right": right,
            "jump": jump,
            "sneak": sneak,
            "sprint": sprint,
        }
        result = self.body.fine_control(controls, FINE_CONTROL_MILLISECONDS)
        return FineControlResult(
            ok=True,
            controls=result.controls,
            duration_ms=result.duration_ms,
            pose_before=result.pose_before,
            pose_after=result.pose_after,
            camera=result.camera,
            on_ground=result.on_ground,
            image=self.body.save_frame(result.frame),
        )

    def minecraft_pillar_up(self, count: int = 1) -> PillarUpResult:
        before = self._require_body()
        held = before.held_item
        if held is None:
            return PillarUpResult(
                ok=False, reason="no_held_item", message="Your main hand is empty.",
                camera=before.camera, blocks_placed=0, climbed=0,
                inventory_delta=None, image=self.body.screenshot(),
            )
        if held.name not in {entry.name for entry in self.body.catalog().blocks}:
            return PillarUpResult(
                ok=False, reason="not_placeable", message="The held item is not a placeable block.",
                camera=before.camera, blocks_placed=0, climbed=0,
                inventory_delta=None, image=self.body.screenshot(),
            )

        climbed = 0
        failure_reason = "no_headroom"
        for _ in range(min(count, PILLAR_UP_BLOCK_LIMIT, held.count)):
            state = self.body.state()
            feet = state.camera.feet_position
            feet_cell = Vec3i(x=math.floor(feet.x), y=math.floor(feet.y), z=math.floor(feet.z))
            below_cell = Vec3i(x=feet_cell.x, y=feet_cell.y - 1, z=feet_cell.z)
            head_cell = Vec3i(x=feet_cell.x, y=feet_cell.y + 2, z=feet_cell.z)
            feet_block, below_block, head_block = self.body.blocks(
                [feet_cell, below_cell, head_cell]
            ).blocks
            if not feet_block.replaceable:
                failure_reason = "not_placeable"
                break
            if below_block.replaceable:
                failure_reason = "not_grounded"
                break
            if not head_block.replaceable:
                failure_reason = "no_headroom"
                break
            reply = self.assist.pillar_step(held.name, feet_cell, feet.x, feet.y, feet.z)
            if "Changed the block" not in reply:
                failure_reason = "not_placeable"
                break
            _, sync_failure = self._wait_until(
                lambda: (
                    self.body.blocks([feet_cell]).blocks[0],
                    self.body.state(),
                ),
                lambda observed: (
                    observed[0].name == held.name
                    and observed[1].camera.feet_position.y >= feet.y + 0.9
                ),
                STATE_SYNC_SECONDS,
                self._stop_generation,
            )
            if sync_failure:
                break
            climbed += 1

        after = self.body.state()
        if climbed == 0:
            messages = {
                "no_headroom": "There is not enough headroom to pillar up.",
                "not_grounded": "You are not standing on a solid block.",
                "not_placeable": "A block cannot be placed at your feet.",
            }
            return PillarUpResult(
                ok=False, reason=failure_reason, message=messages[failure_reason],
                camera=after.camera, blocks_placed=0, climbed=0,
                inventory_delta=_inventory_delta(before.inventory, after.inventory),
                image=self.body.screenshot(),
            )
        return PillarUpResult(
            ok=True, reason=None, message=None, camera=after.camera,
            blocks_placed=climbed, climbed=climbed,
            inventory_delta=_inventory_delta(before.inventory, after.inventory),
            image=self.body.screenshot(),
        )

    def minecraft_walk_to_visible(
        self, x: float, y: float, z: float
    ) -> WalkResult:
        self._require_body()
        return self._walk_result(self.body.walk_visible(
            Vec3f(x=x, y=y, z=z),
            LOCAL_PATH_DISTANCE_BLOCKS,
            VISIBLE_WALK_SECONDS * 1000,
        ))

    def minecraft_walk_to_surface(self, x: float, z: float) -> WalkResult:
        self._require_body()
        return self._walk_result(self.body.walk_surface(
            x, z, SURFACE_WALK_SECONDS * 1000
        ))

    def minecraft_walk_to_exact(self, x: float, y: float, z: float) -> WalkResult:
        self._require_body()
        target = Vec3f(x=x, y=y, z=z)
        result = self.body.walk_exact(target, EXACT_WALK_SECONDS * 1000)
        return self._walk_result(result)

    def minecraft_use_block(self, position: Vec3i) -> UseBlockResult:
        state = self._require_body()
        block = self.body.blocks([position]).blocks[0]
        reference = BlockRef(
            position=position,
            block_name=block.name,
            display_name=block.display_name,
        )
        if block.name in void_blocks:
            return UseBlockResult(
                ok=False,
                reason="not_found",
                message="The block was not found.",
                block=None,
                action=None,
                window=None,
                image=None,
            )
        kind = interactable_kind(block.name)
        if kind is None:
            return UseBlockResult(
                ok=False,
                reason="not_interactable",
                message=f"{block.display_name} is not interactable.",
                block=reference,
                action=None,
                window=None,
                image=None,
            )
        if _distance(state.camera.feet_position, position) > 5:
            return UseBlockResult(
                ok=False,
                reason="out_of_range",
                message="The block is outside interaction range.",
                block=reference,
                action=None,
                window=None,
                image=None,
            )
        used = self.body.use_block(position, kind)
        return UseBlockResult(
            ok=True,
            block=reference,
            action=used.action,
            window=used.window,
            image=None,
        )

    def minecraft_chest_deposit(
        self, item: str, count: int | None = None, chest: Vec3i | None = None
    ) -> ChestMoveResult:
        before = self._require_body()
        if chest is None:
            return ChestMoveResult(ok=False, reason="no_chest_window", message="Open a chest first or provide its position.", item=None, moved_count=0, window=None, inventory_delta=None, candidates=None)
        matched = matching(item, before.inventory)
        if not matched:
            return ChestMoveResult(ok=False, reason="not_found", message=f"The inventory item was not found: {item}", item=None, moved_count=0, window=None, inventory_delta=None, candidates=candidates(item, before.inventory))
        if len(matched) > 1:
            return ChestMoveResult(ok=False, reason="ambiguous", message="Multiple inventory items matched. Use one exact name.", item=None, moved_count=0, window=None, inventory_delta=None, candidates=glob_candidates(matched))
        selected = matched[0]
        moved = selected.count if count is None else min(count, selected.count)
        result = self.body.chest_move(chest, selected.name, moved, "deposit")
        after = self.body.state()
        actual = selected.count - _inventory_counts(after.inventory).get(selected.name, 0)
        if result.window is None:
            return ChestMoveResult(ok=False, reason="no_chest_window", message="The chest did not stay open.", item=selected.name, moved_count=actual, window=None, inventory_delta=_inventory_delta(before.inventory, after.inventory), candidates=None)
        if count is not None and count > selected.count:
            return ChestMoveResult(ok=False, reason="insufficient", message=f"There were not enough {selected.name} items; moved all {actual} available.", item=selected.name, moved_count=actual, window=result.window, inventory_delta=_inventory_delta(before.inventory, after.inventory), candidates=None)
        return ChestMoveResult(ok=True, item=selected.name, moved_count=actual, window=result.window, inventory_delta=_inventory_delta(before.inventory, after.inventory), candidates=None)

    def minecraft_chest_withdraw(
        self, item: str, count: int | None = None, chest: Vec3i | None = None
    ) -> ChestMoveResult:
        before = self._require_body()
        if chest is None:
            return ChestMoveResult(ok=False, reason="no_chest_window", message="Open a chest first or provide its position.", item=None, moved_count=0, window=None, inventory_delta=None, candidates=None)
        matched = matching(item, self.body.catalog().items)
        if not matched:
            return ChestMoveResult(ok=False, reason="not_found", message=f"The item name was not found: {item}", item=None, moved_count=0, window=None, inventory_delta=None, candidates=candidates(item, self.body.catalog().items))
        if len(matched) > 1:
            return ChestMoveResult(ok=False, reason="ambiguous", message="Multiple items matched. Use one exact name.", item=None, moved_count=0, window=None, inventory_delta=None, candidates=glob_candidates(matched))
        item = matched[0].name
        requested = count if count is not None else 36 * 64
        result = self.body.chest_move(chest, item, requested, "withdraw")
        after = self.body.state()
        actual = _inventory_counts(after.inventory).get(item, 0) - _inventory_counts(before.inventory).get(item, 0)
        common = dict(
            item=item,
            moved_count=actual,
            window=result.window,
            inventory_delta=_inventory_delta(before.inventory, after.inventory),
            candidates=None,
        )
        if result.available_count == 0:
            return ChestMoveResult(ok=False, reason="not_found", message=f"The chest item was not found: {item}", **common)
        if result.inventory_space == 0:
            return ChestMoveResult(ok=False, reason="inventory_full", message="The inventory is full.", **common)
        if count is not None and count > result.available_count:
            return ChestMoveResult(ok=False, reason="insufficient", message=f"There were not enough {item} items; moved all {actual} available.", **common)
        return ChestMoveResult(ok=True, **common)

    def minecraft_attack_entity(self, entity_id: int) -> AttackEntityResult:
        before = self._require_body()
        visible = self.body.observe(8).nearby_entities
        target = next((entity for entity in visible if entity.entity_id == entity_id), None)
        if target is None:
            return AttackEntityResult(ok=False, reason="entity_not_found", message=f"Entity {entity_id} was not found in the visible attack range.", entity_id=entity_id, entity_type=None, killed=False, hits=0, entity_health_remaining=None, self_damage_taken=None, drops_collected=[], inventory_delta=None)
        result = self.body.attack(entity_id, 25)
        after = self.body.state()
        interrupted = result.interrupted or entity_id in self._test_interrupted_entities
        self._test_interrupted_entities.discard(entity_id)
        if interrupted:
            return AttackEntityResult(ok=False, reason="entity_not_found", message="The entity was not found before the attack completed.", entity_id=entity_id, entity_type=result.entity_type, killed=False, hits=result.hits, entity_health_remaining=None, self_damage_taken=None, drops_collected=[], inventory_delta=_inventory_delta(before.inventory, after.inventory))
        return AttackEntityResult(ok=True, entity_id=entity_id, entity_type=result.entity_type, killed=result.killed, hits=result.hits, entity_health_remaining=result.health, self_damage_taken=None, drops_collected=result.drops, inventory_delta=_inventory_delta(before.inventory, after.inventory))

    def minecraft_execute_typescript(
        self, path: str, postcondition: dict, arguments: dict | None = None
    ) -> ExecuteSkillResult:
        before = self._require_body()
        home = self.configuration.agent_home.resolve()
        normalized = path.replace("\\", "/")
        if (
            normalized.startswith("/")
            or re.match(r"^[A-Za-z]:", path)
            or ".." in normalized.split("/")
        ):
            return self._skill_result(
                path=path,
                ok=False,
                reason="access_denied",
                message="The skill path must stay inside skills/ or drafts/. Access denied.",
                before=before,
                after=None,
                postcondition=None,
                outcome=None,
            )
        parts = normalized.split("/")
        if len(parts) < 2 or parts[0] not in ("skills", "drafts"):
            return self._skill_result(
                path=path,
                ok=False,
                reason="access_denied",
                message="The skill path must start with skills/ or drafts/. Access denied.",
                before=before,
                after=None,
                postcondition=None,
                outcome=None,
            )
        resolved = (home / normalized).resolve()
        if not str(resolved).startswith(str(home)):
            return self._skill_result(
                path=path,
                ok=False,
                reason="access_denied",
                message="The skill path left the agent workspace. Access denied.",
                before=before,
                after=None,
                postcondition=None,
                outcome=None,
            )
        if not resolved.is_file():
            return self._skill_result(
                path=path,
                ok=False,
                reason="skill_not_found",
                message="The skill was not found at the requested path.",
                before=before,
                after=None,
                postcondition=None,
                outcome=None,
            )
        source = resolved.read_text(encoding="utf-8")
        started = time.monotonic()
        outcome = self.body.execute_skill(path, source, arguments, SKILL_SECONDS * 1000)
        elapsed = (time.monotonic() - started) * 1000
        after = self.body.state()
        report = self._postcondition_report(before, after, postcondition)

        if outcome.status == "timeout":
            return self._skill_result(
                path=path,
                ok=False,
                reason="timeout",
                message="The skill ran out of its time budget.",
                before=before,
                after=after,
                postcondition=report,
                outcome=outcome,
                duration_ms=elapsed,
            )
        if outcome.status == "stopped":
            return self._skill_result(
                path=path,
                ok=False,
                reason="stopped",
                message="The skill was stopped.",
                before=before,
                after=after,
                postcondition=None,
                outcome=outcome,
                duration_ms=elapsed,
            )
        if outcome.status == "access_denied":
            return self._skill_result(
                path=path,
                ok=False,
                reason="access_denied",
                message=f"The skill requested access outside the survival boundary. Access denied: {outcome.reason or ''}",
                before=before,
                after=after,
                postcondition=None,
                outcome=outcome,
                duration_ms=elapsed,
            )
        if outcome.status == "typescript_error":
            return self._skill_result(
                path=path,
                ok=False,
                reason="typescript_error",
                message=f"The skill threw a TypeScript error: {outcome.reason or ''}",
                before=before,
                after=after,
                postcondition=None,
                outcome=outcome,
                duration_ms=elapsed,
            )
        if report.passed:
            return self._skill_result(
                path=path,
                ok=True,
                reason=None,
                message=None,
                before=before,
                after=after,
                postcondition=report,
                outcome=outcome,
                duration_ms=elapsed,
            )
        return self._skill_result(
            path=path,
            ok=False,
            reason="postcondition_failed",
            message="The skill finished but did not meet its postcondition.",
            before=before,
            after=after,
            postcondition=report,
            outcome=outcome,
            duration_ms=elapsed,
        )

    def _skill_result(
        self,
        path: str,
        ok: bool,
        reason: str | None,
        message: str | None,
        before: BodyState,
        after: BodyState | None,
        postcondition: PostconditionReport | None,
        outcome,
        duration_ms: float | None = None,
    ) -> ExecuteSkillResult:
        return ExecuteSkillResult(
            ok=ok,
            reason=reason,
            message=message,
            execution_id=uuid4().hex,
            skill_path=path,
            duration_ms=outcome.duration_ms if outcome is not None and duration_ms is None else (duration_ms or 0.0),
            postcondition=postcondition,
            stdout_tail=outcome.stdout_tail if outcome is not None else None,
            stderr_tail=outcome.stderr_tail if outcome is not None else None,
            heartbeats=outcome.heartbeats if outcome is not None else 0,
            inventory_delta=_inventory_delta(before.inventory, after.inventory) if after is not None else None,
            camera=after.camera if (ok and after is not None) else None,
        )

    def _postcondition_report(
        self, before: BodyState, after: BodyState, spec: dict
    ) -> PostconditionReport:
        passed, detail = self._evaluate_postcondition(before, after, spec)
        return PostconditionReport(
            passed=passed,
            spec=json.dumps(spec, sort_keys=True),
            detail=detail,
        )

    def _evaluate_postcondition(
        self, before: BodyState, after: BodyState, spec: dict
    ) -> tuple[bool, str | None]:
        if "all" in spec:
            for sub in spec["all"]:
                passed, detail = self._evaluate_postcondition(before, after, sub)
                if not passed:
                    return False, detail
            return True, None
        counts_after = _inventory_counts(after.inventory)
        counts_before = _inventory_counts(before.inventory)
        if "inventory_min" in spec:
            for item, minimum in spec["inventory_min"].items():
                have = counts_after.get(item, 0)
                if have < minimum:
                    return False, f"inventory_min: {item} has {have}, needs {minimum}."
        if "inventory_delta_min" in spec:
            for item, minimum in spec["inventory_delta_min"].items():
                delta = counts_after.get(item, 0) - counts_before.get(item, 0)
                if delta < minimum:
                    return False, f"inventory_delta_min: {item} changed by {delta}, needs {minimum}."
        if "y_min" in spec:
            if after.camera is None or after.camera.feet_position.y < spec["y_min"]:
                return False, f"y_min: player y is not above {spec['y_min']}."
        if "y_max" in spec:
            if after.camera is None or after.camera.feet_position.y > spec["y_max"]:
                return False, f"y_max: player y is not below {spec['y_max']}."
        if "health_min" in spec:
            if after.player is None or after.player.health < spec["health_min"]:
                return False, f"health_min: health is below {spec['health_min']}."
        if "position_changed_min" in spec:
            if before.camera is None or after.camera is None:
                return False, "position_changed_min: no camera available."
            moved = _distance(before.camera.feet_position, after.camera.feet_position)
            if moved < spec["position_changed_min"]:
                return False, f"position_changed_min: moved {moved:.3f}, needs {spec['position_changed_min']}."
        if "distance_max" in spec:
            if before.camera is None or after.camera is None:
                return False, "distance_max: no camera available."
            moved = _distance(before.camera.feet_position, after.camera.feet_position)
            if moved > spec["distance_max"]:
                return False, f"distance_max: moved {moved:.3f}, max {spec['distance_max']}."
        if "held_item" in spec:
            if after.held_item is None or after.held_item.name != spec["held_item"]:
                return False, f"held_item: not holding {spec['held_item']}."
        if "entity_id_absent" in spec:
            snapshot = self.body.observe(8)
            present = {entity.entity_id for entity in snapshot.nearby_entities}
            if spec["entity_id_absent"] in present:
                return False, f"entity_id_absent: entity {spec['entity_id_absent']} is still present."
        if "block_at" in spec:
            target = spec["block_at"]
            position = Vec3i(
                x=target["position"][0],
                y=target["position"][1],
                z=target["position"][2],
            )
            blocks = self.body.blocks([position])
            actual = blocks[0].name if blocks else None
            if actual != target["block"]:
                return False, f"block_at: {actual} != {target['block']}."
        return True, None

    def minecraft_look_at(self, position: Vec3f) -> RotateResult:
        before = self._require_body().camera
        if _distance(before.eye_position, position) < 1e-9:
            return RotateResult(
                ok=False,
                reason="same_position",
                message="The target is the current eye position.",
                camera=before,
                yaw_delta=0,
                pitch_delta=0,
                image=self.body.screenshot(),
            )
        after = self.body.look_at(position).camera
        return RotateResult(
            ok=True,
            camera=after,
            yaw_delta=_angle_delta(after.yaw, before.yaw),
            pitch_delta=after.pitch - before.pitch,
            image=self.body.screenshot(),
        )

    def minecraft_screenshot(self) -> ScreenshotResult:
        self._require_body()
        return ScreenshotResult(ok=True, image=self.body.screenshot())

    def minecraft_mine_vein(self, block: str) -> MineVeinResult:
        before = self._require_body()
        found = self.minecraft_find_block(block)
        if not found.ok:
            return MineVeinResult(ok=False, reason=found.reason, message=found.message, block=None, mined_cells=[], mined_count=0, drops=[], pickup=None, inventory_delta=None, image=None)
        if len(found.matched_types) > 1:
            return MineVeinResult(ok=False, reason="ambiguous", message="Multiple ore types matched. Use one exact block name.", block=None, mined_cells=[], mined_count=0, drops=[], pickup=None, inventory_delta=None, image=self.body.screenshot())
        by_position = {
            (entry.position.x, entry.position.y, entry.position.z): entry
            for entry in found.results
        }
        connected = []
        pending = [found.results[0]]
        seen = set()
        while pending:
            exposed = pending.pop(0)
            key = (exposed.position.x, exposed.position.y, exposed.position.z)
            if key in seen:
                continue
            seen.add(key)
            connected.append(exposed)
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                neighbor = by_position.get((key[0] + dx, key[1] + dy, key[2] + dz))
                if neighbor is not None:
                    pending.append(neighbor)
        mined_cells = []
        for exposed in connected:
            walked = self.minecraft_walk_to_visible(exposed.position.x, exposed.position.y, exposed.position.z)
            if not walked.ok:
                continue
            mined = self.minecraft_mine_block(exposed.position)
            if mined.ok:
                mined_cells.append(exposed.position)
        after = self.body.state()
        return MineVeinResult(ok=bool(mined_cells), reason=None if mined_cells else "no_path", message=None if mined_cells else "No connected ore block was reachable.", block=found.results[0].block_name, mined_cells=mined_cells, mined_count=len(mined_cells), drops=[], pickup=None, inventory_delta=_inventory_delta(before.inventory, after.inventory), image=self.body.screenshot())

    def minecraft_harvest_tree(
        self, base: Vec3i | None = None
    ) -> HarvestTreeResult:
        before = self._require_body()
        found = self.minecraft_find_block("*_log")
        if not found.ok:
            return HarvestTreeResult(ok=False, reason="not_found", message="No exposed tree logs were found.", base=base, logs_collected=0, saplings_collected=0, other_drops=[], inventory_delta=None, image=None)
        selected = [value for value in found.results if base is None or _distance(value.position, base) <= 4]
        if not selected:
            return HarvestTreeResult(ok=False, reason="not_found", message="No tree logs were found near the requested base.", base=base, logs_collected=0, saplings_collected=0, other_drops=[], inventory_delta=None, image=None)
        anchor = selected[0].position
        canopy_cells = [
            Vec3i(x=x, y=y, z=z)
            for x in range(anchor.x - 3, anchor.x + 4)
            for y in range(anchor.y, anchor.y + 7)
            for z in range(anchor.z - 3, anchor.z + 4)
        ]
        canopy = self.body.blocks(canopy_cells).blocks
        if not any(cell.name.endswith("_leaves") for cell in canopy):
            return HarvestTreeResult(ok=False, reason="not_a_tree", message="The log is not part of a tree canopy.", base=anchor, logs_collected=0, saplings_collected=0, other_drops=[], inventory_delta=None, image=self.body.screenshot())
        for value in selected:
            self.minecraft_walk_to_visible(value.position.x, value.position.y, value.position.z)
            self.minecraft_mine_block(value.position)
        after = self.body.state()
        delta = _inventory_delta(before.inventory, after.inventory)
        return HarvestTreeResult(ok=True, base=selected[0].position, logs_collected=max(0, _inventory_counts(after.inventory).get(selected[0].block_name, 0) - _inventory_counts(before.inventory).get(selected[0].block_name, 0)), saplings_collected=0, other_drops=[], inventory_delta=delta, image=self.body.screenshot())

    def minecraft_craft_max(
        self, item: str, limit: int | None = None
    ) -> CraftMaxResult:
        before = self._require_body()
        matched = matching(item, self.body.catalog().items)
        if not matched:
            return CraftMaxResult(
                ok=False,
                reason="not_found",
                message=f"The item name was not found: {item}",
                resolved_item=None,
                crafted=0,
                inventory_delta=None,
                hotbar=before.hotbar,
                still_missing=None,
                candidates=candidates(item, self.body.catalog().items),
            )
        if len(matched) > 1:
            return CraftMaxResult(
                ok=False,
                reason="ambiguous",
                message="Multiple items matched. Use one exact name.",
                resolved_item=None,
                crafted=0,
                inventory_delta=None,
                hotbar=before.hotbar,
                still_missing=None,
                candidates=glob_candidates(matched),
            )
        name = matched[0].name
        result = self.body.craft_max(name, limit)
        after = self.body.state()
        return CraftMaxResult(
            ok=result.reason is None,
            reason=result.reason,
            message=None if result.reason is None else f"Crafted {result.crafted}: {result.reason}.",
            resolved_item=name,
            crafted=result.crafted,
            inventory_delta=_inventory_delta(before.inventory, after.inventory),
            hotbar=after.hotbar,
            still_missing=_ingredient_lines(result.missing),
            candidates=None,
        )

    def minecraft_equip_best_tool(self, target: Vec3i) -> EquipBestToolResult:
        self._require_body()
        block = self.body.blocks([target]).blocks[0]
        if block.name in void_blocks:
            return EquipBestToolResult(
                ok=False,
                reason="not_found",
                message="The target block was not found.",
                requested=block.name,
                target_block=block.name,
                best_possible_tool=None,
                previous_held=None,
                equipped=None,
                hotbar=[],
                candidates=None,
            )
        result = self.body.equip_best_tool(target)
        if result.best_possible_tool is None:
            if block.name in {"dirt", "grass_block", "sand", "gravel", "clay", "soul_sand", "soul_soil"}:
                return EquipBestToolResult(
                    ok=True,
                    requested=block.name,
                    target_block=block.name,
                    best_possible_tool=None,
                    previous_held=result.previous_held,
                    equipped=result.held_item,
                    hotbar=result.hotbar,
                    candidates=None,
                )
            return EquipBestToolResult(
                ok=False,
                reason="unharvestable",
                message="No tool you own can harvest this block.",
                requested=result.target_block or "",
                target_block=result.target_block,
                best_possible_tool=None,
                previous_held=result.previous_held,
                equipped=None,
                hotbar=result.hotbar,
                candidates=None,
            )
        return EquipBestToolResult(
            ok=True,
            reason=None,
            requested=result.best_possible_tool,
            target_block=result.target_block,
            best_possible_tool=result.best_possible_tool,
            previous_held=result.previous_held,
            equipped=result.held_item,
            hotbar=result.hotbar,
            candidates=None,
        )

    def minecraft_eat_best(self) -> EatBestResult:
        before = self._require_body()
        result = self.body.eat_best()
        if not result.considered:
            return EatBestResult(
                ok=False,
                reason="no_food",
                message="The food was not found in your inventory.",
                action=None,
                item=None,
                stat_delta=None,
                inventory_delta=None,
                considered=[],
            )
        if result.action == "nothing":
            return EatBestResult(
                ok=False,
                reason="food_full",
                message="Your food is already full.",
                action="nothing",
                item=result.item,
                stat_delta=None,
                inventory_delta=_inventory_delta(before.inventory, result.after.inventory),
                considered=result.considered,
            )
        player_before = before.player
        player_after = result.after.player
        stat_delta = None if player_before is None or player_after is None else _stat_delta(player_before, player_after)
        return EatBestResult(
            ok=True,
            reason=None,
            action=result.action,
            item=result.item,
            stat_delta=stat_delta,
            inventory_delta=_inventory_delta(before.inventory, result.after.inventory),
            considered=result.considered,
        )

    def minecraft_staircase_down(
        self, depth: int = 8, torch: bool = True
    ) -> StaircaseResult:
        before = self._require_body()
        result = self.body.staircase_down(depth, torch)
        after = self.body.state()
        return StaircaseResult(
            ok=True,
            reason=None,
            message=None,
            depth_requested=result.depth_requested,
            depth_achieved=result.depth_achieved,
            end_position=result.end_position,
            blocks_dug=result.blocks_dug,
            hazards_found=result.hazards_found,
            torches_placed=result.torches_placed,
            inventory_delta=_inventory_delta(before.inventory, after.inventory),
            image=self.body.screenshot(),
        )

    def minecraft_fill_from_inventory(
        self,
        shape: Literal["fill", "wall", "floor", "column"],
        start: Vec3i,
        end: Vec3i | None = None,
        ref: Vec3i | None = None,
    ) -> BuildResult:
        state = self._require_body()
        catalog = self.body.catalog()
        block_names = {block.name for block in catalog.blocks}
        counts = _inventory_counts(state.inventory)
        material = None
        for name in sorted(counts, key=lambda value: -counts[value]):
            if name in block_names and name not in void_blocks:
                material = name
                break
        if material is None:
            return BuildResult(
                ok=False,
                reason="no_material",
                message="No placeable block is in your inventory.",
                shape=shape,
                material_requested=None,
                material_resolved=None,
                bounds=Box(min=start, max=end or start),
                planned_cells=0,
                placed_count=0,
                placed=[],
                occupied=[],
                out_of_range=[],
                missing_material_cells=0,
                inventory_delta=None,
                candidates=None,
                image=None,
                duration_ms=0,
            )
        return self.minecraft_build(shape, material, start=start, end=end, ref=ref)

    def minecraft_sleep(self, bed: Vec3i | None = None) -> SleepResult:
        state = self._require_body()
        if state.player is not None and state.player.is_day:
            return SleepResult(
                ok=False,
                reason="not_night",
                message="It is not night; you can only sleep at night.",
                bed=bed,
                slept=False,
                is_day_now=True,
                blocking_entity=None,
            )
        if bed is not None:
            around = [
                bed,
                Vec3i(x=bed.x + 1, y=bed.y, z=bed.z),
                Vec3i(x=bed.x - 1, y=bed.y, z=bed.z),
                Vec3i(x=bed.x, y=bed.y, z=bed.z + 1),
                Vec3i(x=bed.x, y=bed.y, z=bed.z - 1),
            ]
            bed_cells = [cell.position for cell in self.body.blocks(around).blocks if cell.name.endswith("_bed")]
            above = [Vec3i(x=cell.x, y=cell.y + 1, z=cell.z) for cell in bed_cells]
            if any(not cell.replaceable for cell in self.body.blocks(above).blocks):
                return SleepResult(ok=False, reason="bed_obstructed", message="The bed is obstructed by a solid block.", bed=bed, slept=False, is_day_now=False, blocking_entity=None)
        result = self.body.sleep(bed)
        if not result.ok:
            reason = result.reason or "not_night"
            messages = {
                "no_bed": "The bed was not found in range.",
                "out_of_range": "The bed is out of range.",
                "bed_obstructed": "The bed is obstructed by a solid block.",
                "bed_occupied": "The bed is occupied by another player.",
            }
            if reason == "monster_nearby":
                return SleepResult(
                    ok=True,
                    bed=bed,
                    slept=False,
                    is_day_now=result.is_day_now,
                    blocking_entity=result.blocking_entity,
                )
            return SleepResult(
                ok=False,
                reason=reason,
                message=messages.get(reason, "The bed cannot be used right now."),
                bed=bed,
                slept=False,
                is_day_now=result.is_day_now,
                blocking_entity=None,
            )
        return SleepResult(
            ok=True,
            reason=None,
            bed=bed,
            slept=result.slept,
            is_day_now=result.is_day_now,
            blocking_entity=result.blocking_entity,
        )

    def minecraft_drop_item(
        self, item: str, count: int | None = None
    ) -> DropResult:
        before = self._require_body()
        matched = matching(item, before.inventory)
        if not matched:
            return DropResult(
                ok=False,
                reason="not_found",
                message=f"The inventory item was not found: {item}",
                item=None,
                dropped=0,
                drop_position=None,
                inventory_delta=None,
                candidates=candidates(item, before.inventory),
            )
        if len(matched) > 1:
            return DropResult(
                ok=False,
                reason="ambiguous",
                message="Multiple inventory items matched. Use one exact name.",
                item=None,
                dropped=0,
                drop_position=None,
                inventory_delta=None,
                candidates=glob_candidates(matched),
            )
        name = matched[0].name
        result = self.body.drop_item(name, count)
        after = self.body.state()
        return DropResult(
            ok=True,
            reason=None,
            item=result.item,
            dropped=result.dropped,
            drop_position=result.drop_position,
            inventory_delta=_inventory_delta(before.inventory, after.inventory),
            candidates=None,
        )

    def minecraft_discard_items(
        self, item: str, count: int | None = None
    ) -> DiscardResult:
        generation = self._stop_generation
        before = self._require_body()
        resolved = matching(item, before.inventory)
        if not resolved:
            return DiscardResult(
                ok=False,
                reason="not_found",
                message=f"The inventory item was not found: {item}",
                pattern=item,
                resolved_items=[],
                discarded_count=0,
                inventory_delta=None,
                candidates=candidates(item, before.inventory),
            )
        if len(resolved) > 1:
            return DiscardResult(
                ok=False,
                reason="ambiguous",
                message="Multiple inventory items matched. Use one exact name.",
                pattern=item,
                resolved_items=[],
                discarded_count=0,
                inventory_delta=None,
                candidates=glob_candidates(resolved),
            )
        selected = resolved[0]
        discarded = selected.count if count is None else min(count, selected.count)
        self.assist.remove_items(selected.name, discarded)
        after, failure = self._wait_for_inventory(
            selected.name,
            selected.count - discarded,
            generation,
        )
        return DiscardResult(
            ok=failure is None,
            reason=failure,
            message=None if failure is None else f"Inventory confirmation {failure}; inspect inventory before retrying.",
            pattern=item,
            resolved_items=[selected.name],
            discarded_count=min(discarded, max(0, selected.count - _inventory_counts(after.inventory).get(selected.name, 0))),
            inventory_delta=_inventory_delta(before.inventory, after.inventory),
            candidates=None,
        )

    def minecraft_count_inventory(self, pattern: str = "*") -> CountResult:
        state = self._require_body()
        found = sorted(
            matching(pattern, state.inventory),
            key=lambda value: (-value.count, value.name),
        )
        if not found and pattern != "*":
            return CountResult(
                ok=False,
                reason="not_found",
                message=f"The inventory item was not found: {pattern}",
                pattern=pattern,
                matches=[],
                total_matching_items=0,
                candidates=candidates(pattern, state.inventory),
            )
        return CountResult(
            ok=True,
            pattern=pattern,
            matches=found,
            total_matching_items=sum(item.count for item in found),
            candidates=None,
        )

    def minecraft_analyze_area(
        self, start: Vec3i, end: Vec3i
    ) -> AreaReportResult:
        state = self._require_body()
        feet = state.camera.block_position
        minimum = Vec3i(
            x=min(start.x, end.x),
            y=min(start.y, end.y),
            z=min(start.z, end.z),
        )
        maximum = Vec3i(
            x=max(start.x, end.x),
            y=max(start.y, end.y),
            z=max(start.z, end.z),
        )
        if (
            minimum.x < feet.x - VISIBLE_AREA_HORIZONTAL_BLOCKS
            or maximum.x > feet.x + VISIBLE_AREA_HORIZONTAL_BLOCKS
            or minimum.z < feet.z - VISIBLE_AREA_HORIZONTAL_BLOCKS
            or maximum.z > feet.z + VISIBLE_AREA_HORIZONTAL_BLOCKS
            or minimum.y < feet.y - VISIBLE_AREA_DOWN_BLOCKS
            or maximum.y > feet.y + VISIBLE_AREA_UP_BLOCKS
        ):
            return AreaReportResult(
                ok=False,
                reason="out_of_range",
                message="The requested area is outside the visible range.",
                bounds=None,
                blocks=[],
                total_cells=0,
                solid_cells=0,
                air_cells=0,
                unseen_cells=0,
                entities=[],
            )

        cells = [
            Vec3i(x=x, y=y, z=z)
            for x in range(minimum.x, maximum.x + 1)
            for y in range(minimum.y, maximum.y + 1)
            for z in range(minimum.z, maximum.z + 1)
        ]
        body = self._body()
        scanned = []
        for index in range(0, len(cells), 2048):
            scanned.extend(body.blocks(cells[index:index + 2048]).blocks)

        solid_positions = {
            (block.position.x, block.position.y, block.position.z)
            for block in scanned
            if not block.replaceable
        }
        neighbor_positions = {
            (x + dx, y + dy, z + dz)
            for x, y, z in solid_positions
            for dx, dy, dz in (
                (1, 0, 0), (-1, 0, 0), (0, 1, 0),
                (0, -1, 0), (0, 0, 1), (0, 0, -1),
            )
        }
        neighbor_blocks = []
        neighbor_cells = [Vec3i(x=x, y=y, z=z) for x, y, z in sorted(neighbor_positions)]
        for index in range(0, len(neighbor_cells), 2048):
            neighbor_blocks.extend(body.blocks(neighbor_cells[index:index + 2048]).blocks)
        replaceable = {
            (block.position.x, block.position.y, block.position.z): block.replaceable
            for block in neighbor_blocks
        }

        tallies: dict[tuple[str, str], int] = {}
        solid_cells = 0
        air_cells = 0
        unseen_cells = 0
        for block in scanned:
            position = (block.position.x, block.position.y, block.position.z)
            if not block.replaceable and not any(
                replaceable.get((position[0] + dx, position[1] + dy, position[2] + dz), False)
                for dx, dy, dz in (
                    (1, 0, 0), (-1, 0, 0), (0, 1, 0),
                    (0, -1, 0), (0, 0, 1), (0, 0, -1),
                )
            ):
                unseen_cells += 1
                continue
            if block.name in void_blocks:
                air_cells += 1
                continue
            if not block.replaceable:
                solid_cells += 1
            key = (block.name, block.display_name)
            tallies[key] = tallies.get(key, 0) + 1

        blocks = sorted(
            (
                BlockTally(block_name=name, display_name=display, count=count)
                for (name, display), count in tallies.items()
            ),
            key=lambda item: (-item.count, item.block_name),
        )
        return AreaReportResult(
            ok=True,
            bounds=Box(min=minimum, max=maximum),
            blocks=blocks,
            total_cells=len(cells),
            solid_cells=solid_cells,
            air_cells=air_cells,
            unseen_cells=unseen_cells,
            entities=[],
        )

    def minecraft_find_path(self, x: float, y: float, z: float) -> PathPreviewResult:
        self._require_body()
        preview = self.body.find_path(
            Vec3f(x=x, y=y, z=z),
            LOCAL_PATH_DISTANCE_BLOCKS,
            PATH_SEARCH_SECONDS * 1000,
        )
        blocker = None
        if preview.blocker is not None:
            blocker = ObstacleRef(
                block_name=preview.blocker.block_name,
                position=Vec3i(
                    x=preview.blocker.position.x,
                    y=preview.blocker.position.y,
                    z=preview.blocker.position.z,
                ),
            )
        return PathPreviewResult(
            ok=True,
            reason=None,
            message="The preview path completed.",
            state=preview.state,
            path_length=preview.path_length,
            hops=preview.hops,
            estimated_seconds=preview.estimated_seconds,
            blocker=blocker,
        )

    def minecraft_is_safe_to_dig(self, position: Vec3i) -> SafetyReportResult:
        self._require_body()
        block = self.body.blocks([position]).blocks[0]
        if block.name in void_blocks:
            return SafetyReportResult(
                ok=True,
                reason=None,
                message=None,
                position=position,
                risk="unknown",
                hazards=[],
                will_fall=None,
                fall_depth=None,
            )
        result = self.body.safe_to_dig(position)
        hazards = [
            HazardRef(
                kind=h.kind,
                direction=h.direction,
                position=None if h.position is None else Vec3i(x=h.position.x, y=h.position.y, z=h.position.z),
                distance_band=h.distance_band,
                note=h.note,
            )
            for h in result.hazards
        ]
        return SafetyReportResult(
            ok=True,
            reason=None,
            message=None,
            position=position,
            risk=result.risk,
            hazards=hazards,
            will_fall=result.will_fall,
            fall_depth=result.fall_depth,
        )

    def _coverage(
        self,
        camera, horizontal, up, down, found,
    ) -> SearchCoverage:
        cell = camera.block_position
        bounds = Box(
            min=Vec3i(x=cell.x - horizontal, y=cell.y - down, z=cell.z - horizontal),
            max=Vec3i(x=cell.x + horizontal, y=cell.y + up, z=cell.z + horizontal),
        )
        return SearchCoverage(
            center=camera.feet_position,
            bounds=bounds,
            chunks_loaded=found.coverage.chunks_loaded,
            columns_scanned=found.coverage.columns_scanned,
            note=None,
        )

    def _walk_result(self, result) -> WalkResult:
        return WalkResult(
            ok=result.ok,
            reason=result.reason,
            message=result.message,
            status=result.status,
            requested=result.requested,
            final_position=result.final_position,
            distance_remaining=result.distance_remaining,
            target_offset=result.target_offset,
            diagnostics=result.diagnostics,
            hops=result.hops,
            camera=result.camera,
            image=None,
            duration_ms=result.duration_ms,
        )

    def _wait_until(self, read, ready, seconds: float, generation: int):
        deadline = time.monotonic() + seconds
        while True:
            value = read()
            if generation != self._stop_generation:
                return value, "stopped"
            if ready(value):
                return value, None
            if time.monotonic() >= deadline:
                return value, "timeout"
            time.sleep(0.05)

    def _wait_for_inventory(self, item: str, count: int, generation: int) -> tuple[BodyState, str | None]:
        return self._wait_until(
            self.body.state,
            lambda state: _inventory_counts(state.inventory).get(item, 0) == count,
            STATE_SYNC_SECONDS,
            generation,
        )

    def _wait_for_blocks(
        self, cells: list[Vec3i], material: str, generation: int,
        seconds: float = STATE_SYNC_SECONDS,
    ) -> tuple[list[BodyBlock], str | None]:
        return self._wait_until(
            lambda: self.body.blocks(cells).blocks,
            lambda blocks: len(blocks) == len(cells) and all(block.name == material for block in blocks),
            seconds,
            generation,
        )


def _equipment_warnings(before: BodyState, after: BodyState) -> list[str]:
    if not before.spawned or not after.spawned:
        return []
    held_before = before.held_item.name if before.held_item else "empty"
    held_after = after.held_item.name if after.held_item else "empty"
    active = f"active hotbar slot: {after.active_hotbar_slot} ({held_after})"
    warnings = []
    counts_before = _inventory_counts(before.inventory)
    counts_after = _inventory_counts(after.inventory)
    for slot in before.hotbar:
        name = slot.item
        if name and name.endswith(("_pickaxe", "_axe", "_shovel", "_hoe", "_sword", "bow", "shears", "fishing_rod")):
            if counts_after.get(name, 0) < counts_before.get(name, 0):
                warnings.append(f"Tool count decreased: hotbar slot {slot.slot} ({name}); {active}. Check durability and spare tools.")
    if (before.active_hotbar_slot, held_before) != (after.active_hotbar_slot, held_after):
        warnings.append(f"Held item changed: slot {before.active_hotbar_slot} ({held_before}); {active}.")
    return warnings


def _inventory_counts(items: list[InventoryItem]) -> dict[str, int]:
    return {item.name: item.count for item in items}


def _distance(a: Vec3f, b: Vec3f | Vec3i) -> float:
    return math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2 + (b.z - a.z) ** 2)


def _angle_delta(after: float, before: float) -> float:
    return (after - before + 180) % 360 - 180


def _inventory_delta(
    before_items: list[InventoryItem],
    after_items: list[InventoryItem],
) -> InventoryDelta:
    before = _inventory_counts(before_items)
    after = _inventory_counts(after_items)
    changes = [
        InventoryChange(
            item=name,
            before=before.get(name, 0),
            after=after.get(name, 0),
            delta=after.get(name, 0) - before.get(name, 0),
        )
        for name in sorted(before.keys() | after.keys())
        if before.get(name, 0) != after.get(name, 0)
    ]
    return InventoryDelta(
        changes=changes,
        total_items_before=sum(before.values()),
        total_items_after=sum(after.values()),
    )


def _craft_failure_message(reason: str | None, item: str) -> str:
    if reason == "missing_ingredients":
        return f"The item {item} is missing ingredients."
    if reason == "crafting_table_not_found":
        return f"The crafting table was not found; {item} needs a crafting table."
    return f"The item {item} cannot be crafted."


def _ingredient_lines(lines):
    """Convert body ingredient lines into IngredientNeed objects."""
    if not lines:
        return None
    needs = []
    for line in lines:
        needs.append(
            IngredientNeed(
                item=line.item,
                display_name=line.item.replace("_", " "),
                required=line.required,
                have=line.have,
                missing=max(line.required - line.have, 0),
            )
        )
    return needs


def _ingredient_needs(missing, inventory):
    if not missing:
        return None
    needs = []
    for need in missing:
        display = next(
            (item.display_name for item in inventory if item.name == need.item),
            need.item,
        )
        needs.append(
            IngredientNeed(
                item=need.item,
                display_name=display,
                required=need.required,
                have=need.have,
                missing=max(need.required - need.have, 0),
            )
        )
    return needs


def _stat_delta(before, after):
    from .models import StatDelta
    return StatDelta(
        health_before=before.health,
        health_after=after.health,
        food_before=before.food,
        food_after=after.food,
        oxygen_before=before.oxygen,
        oxygen_after=after.oxygen,
        xp_level_before=before.xp_level,
        xp_level_after=after.xp_level,
    )


void_blocks = frozenset(("air", "cave_air", "void_air"))


def _matches(pattern: str, name: str) -> bool:
    return fnmatchcase(name.lower(), pattern.lower())


def interactable_kind(name: str) -> str | None:
    if name in ("chest", "trapped_chest"):
        return "chest"
    if name == "barrel":
        return "barrel"
    if name.endswith("shulker_box"):
        return "shulker_box"
    if name in ("furnace", "blast_furnace", "smoker"):
        return "furnace"
    if name == "crafting_table":
        return "crafting_table"
    if name.endswith("_bed"):
        return "bed"
    if name.endswith("_door"):
        return "door"
    if name.endswith("_fence_gate"):
        return "gate"
    if name.endswith("_trapdoor"):
        return "trapdoor"
    if name.endswith("_button"):
        return "button"
    if name == "lever":
        return "lever"
    if name == "hopper":
        return "hopper"
    return None
