/**
 * Own the live Mineflayer bot and its survival-safe physical actions.
 *
 * Minecraft disconnects retry in connect(). Expected world failures such as
 * no path are returned as typed results. Invalid internal state and action API
 * failures are programming errors and stop the body with their original stack.
 */
import { skillRunner } from "./skill-runner.js";
import mineflayer from "mineflayer";
import pathfinderPackage from "mineflayer-pathfinder";
import { Vec3 } from "vec3";
import { ViewerCapture } from "./capture.js";
const { goals, Movements, pathfinder } = pathfinderPackage;
const WALK_SPEED_BLOCKS_PER_SECOND = 4.3;
export class MinecraftBody {
    configuration;
    bot = null;
    connected = false;
    spawned = false;
    deathCount = 0;
    stopped = false;
    retry = null;
    currentCommand = null;
    commandStopped = false;
    currentSkill = null;
    skillStopRequested = false;
    recentSounds = [];
    startedAt = performance.now();
    capture;
    constructor(configuration) {
        this.configuration = configuration;
        this.capture = new ViewerCapture(configuration.viewerPort, configuration.browserExecutable);
    }
    connect() {
        const bot = mineflayer.createBot({
            host: this.configuration.host,
            port: this.configuration.port,
            version: this.configuration.version,
            username: this.configuration.username,
            auth: "offline",
        });
        bot.loadPlugin(pathfinder);
        this.bot = bot;
        bot.once("login", () => {
            this.connected = true;
        });
        bot.on("spawn", () => {
            this.connected = true;
            this.spawned = true;
            this.capture.start(bot);
        });
        bot.on("death", () => {
            this.deathCount += 1;
            this.spawned = false;
        });
        bot.on("error", (error) => {
            console.error(`Minecraft connection error: ${error.message}`);
        });
        bot.on("soundEffectHeard", (name, position, volume) => {
            this.recentSounds.push({ name, x: position.x, y: position.y, z: position.z, volume, at: Date.now() });
        });
        bot.once("end", (reason) => {
            this.connected = false;
            this.spawned = false;
            console.error(`Minecraft connection ended: ${reason}`);
            if (!this.stopped) {
                this.retry = setTimeout(() => this.connect(), 2000);
            }
        });
    }
    state() {
        const bot = this.bot;
        const entity = bot?.entity;
        const camera = this.spawned && entity ? cameraFromBot(bot) : null;
        const inventory = aggregateInventory(bot);
        return {
            connected: this.connected,
            spawned: this.spawned,
            death_count: this.deathCount,
            uptime_seconds: (performance.now() - this.startedAt) / 1000,
            dimension: bot?.game?.dimension ?? null,
            camera,
            inventory_count: inventory.reduce((count, item) => count + item.count, 0),
            inventory,
            player: this.spawned ? playerStatus(bot) : null,
            held_item: this.spawned ? itemFromStack(bot.heldItem) : null,
            hotbar: this.spawned ? hotbar(bot) : [],
            active_hotbar_slot: this.spawned ? bot.quickBarSlot : null,
        };
    }
    nearbyBlocks(origin, radius) {
        const bot = this.bot;
        const cell = blockCell(origin);
        const aggregate = new Map();
        for (let dx = -radius; dx <= radius; dx += 1) {
            for (let dy = -radius; dy <= radius; dy += 1) {
                for (let dz = -radius; dz <= radius; dz += 1) {
                    const position = { x: cell.x + dx, y: cell.y + dy, z: cell.z + dz };
                    const block = bot.blockAt(new Vec3(position.x, position.y, position.z));
                    if (block === null) {
                        continue;
                    }
                    const existing = aggregate.get(block.name) ?? {
                        block_name: block.name,
                        display_name: block.displayName,
                        count: 0,
                        nearest: position,
                        distance: Number.MAX_VALUE,
                    };
                    const distance = blockDistance(origin, position);
                    if (distance < existing.distance) {
                        existing.nearest = position;
                        existing.distance = distance;
                    }
                    existing.count += 1;
                    aggregate.set(block.name, existing);
                }
            }
        }
        return [...aggregate.values()].sort((a, b) => a.distance - b.distance);
    }
    nearbyEntities(origin, radius) {
        const bot = this.bot;
        const list = [];
        for (const entity of Object.values(bot.entities)) {
            if (entity === bot.entity) {
                continue;
            }
            const distance = blockDistance(origin, entity.position);
            if (distance > radius) {
                continue;
            }
            list.push(entityRef(entity, distance));
        }
        return list.sort((a, b) => a.distance - b.distance);
    }
    findBlocks(options) {
        const bot = this.bot;
        const center = blockCell(options.center);
        const matches = new Set(options.names);
        const found = [];
        const columnsLoaded = bot.world.getColumns().length;
        for (let dx = -options.horizontal; dx <= options.horizontal; dx += 1) {
            for (let dy = -options.down; dy <= options.up; dy += 1) {
                for (let dz = -options.horizontal; dz <= options.horizontal; dz += 1) {
                    const position = { x: center.x + dx, y: center.y + dy, z: center.z + dz };
                    const block = bot.blockAt(new Vec3(position.x, position.y, position.z));
                    if (block === null) {
                        continue;
                    }
                    if (!matches.has(block.name)) {
                        continue;
                    }
                    const faces = exposedFaces(bot, position);
                    if (faces.length === 0) {
                        continue;
                    }
                    found.push({
                        position,
                        block_name: block.name,
                        display_name: block.displayName,
                        distance: blockDistance(options.center, position),
                        exposed_faces: faces,
                        harvestable_with_held: block.canHarvest(bot.heldItem?.type ?? null) === true,
                    });
                }
            }
        }
        found.sort((a, b) => a.distance - b.distance ||
            a.position.y - b.position.y ||
            a.position.x - b.position.x ||
            a.position.z - b.position.z);
        const unique = dedupe(found);
        return {
            blocks: unique.slice(0, options.limit),
            total_matches: unique.length,
            coverage: {
                center: options.center,
                chunks_loaded: columnsLoaded,
                columns_scanned: columnsLoaded,
            },
        };
    }
    raytrace() {
        const bot = this.bot;
        const head = bot.entity.position.offset(0, 1.62, 0);
        const yaw = bot.entity.yaw;
        const pitch = bot.entity.pitch;
        const horizontal = Math.cos(pitch);
        const direction = new Vec3(-Math.sin(yaw) * horizontal, Math.sin(pitch), -Math.cos(yaw) * horizontal).normalize();
        const range = 256;
        let lastCell = null;
        for (let rayDistance = 0; rayDistance <= range; rayDistance += 0.25) {
            const point = head.offset(direction.x * rayDistance, direction.y * rayDistance, direction.z * rayDistance);
            const cell = point.floored();
            if (lastCell !== null && lastCell.equals(cell)) {
                continue;
            }
            lastCell = cell;
            const block = bot.blockAt(cell);
            if (block === null || VOID_BLOCKS.has(block.name)) {
                continue;
            }
            if (block.name === "water" && block.metadata !== 0) {
                continue;
            }
            return {
                hit: true,
                hit_position: { x: block.position.x, y: block.position.y, z: block.position.z },
                hit_block: block.name,
                hit_face: faceFromRay(yaw, pitch),
                distance: head.distanceTo(block.position),
            };
        }
        return { hit: false, hit_position: null, hit_block: null, hit_face: null, distance: null };
    }
    async rotate(yawDegrees, pitchDegrees, absolute) {
        const bot = this.bot;
        const currentYaw = normalizeDegrees(bot.entity.yaw * 180 / Math.PI);
        const currentPitch = bot.entity.pitch * 180 / Math.PI;
        const yaw = normalizeDegrees(absolute ? yawDegrees : currentYaw + yawDegrees + 180);
        const pitch = clamp(absolute ? pitchDegrees : currentPitch + pitchDegrees, -90, 90);
        await bot.look(yaw * Math.PI / 180, pitch * Math.PI / 180, true);
        return cameraFromBot(bot);
    }
    async lookAt(position) {
        const bot = this.bot;
        await bot.lookAt(new Vec3(position.x, position.y, position.z), true);
        return cameraFromBot(bot);
    }
    async fineControl(controls, durationMs) {
        const bot = this.bot;
        const before = vector(bot.entity.position);
        this.currentCommand = "minecraft_fine_control";
        this.commandStopped = false;
        for (const [name, enabled] of Object.entries(controls)) {
            bot.setControlState(name, enabled);
        }
        const started = performance.now();
        await delay(durationMs);
        bot.clearControlStates();
        const heldDuration = performance.now() - started;
        bot.entity.velocity.x = 0;
        bot.entity.velocity.z = 0;
        if (!controls.jump) {
            await delay(150);
        }
        else {
            bot.entity.velocity.y = 0;
            const gravity = bot.physics.gravity;
            // Keep the released jump pose stable while HTTP and the viewer read it.
            bot.physics.gravity = 0;
            setTimeout(() => {
                bot.physics.gravity = gravity;
            }, 750);
        }
        const frame = await this.capture.capture();
        if (controls.jump) {
            bot.entity.velocity.y = 0;
        }
        this.currentCommand = null;
        return {
            controls,
            duration_ms: heldDuration,
            pose_before: before,
            pose_after: vector(bot.entity.position),
            camera: cameraFromBot(bot),
            on_ground: bot.entity.onGround,
            frame,
        };
    }
    async walkVisible(target, limit, timeoutMs) {
        const bot = this.bot;
        if (distance(bot.entity.position, target) > limit) {
            return walkFailure(bot, target, "no_path", `No path: the target is outside the ${limit}-block local search distance.`, "no_path", 0, 0, walkDiagnostics(bot, target, "target_outside_search_distance"));
        }
        const targetBlock = bot.blockAt(new Vec3(Math.floor(target.x), Math.floor(target.y), Math.floor(target.z)));
        const goal = targetBlock !== null && targetBlock.boundingBox !== "empty"
            ? new goals.GoalGetToBlock(targetBlock.position.x, targetBlock.position.y, targetBlock.position.z)
            : new goals.GoalBlock(target.x, target.y, target.z);
        return this.walk("minecraft_walk_to_visible", target, goal, timeoutMs);
    }
    async walkExact(target, timeoutMs) {
        const bot = this.bot;
        if (!standable(bot, target)) {
            return walkFailure(bot, target, "target_not_standable", "The target is not standable.", "no_path", 0, 0);
        }
        return this.walk("minecraft_walk_to_exact", target, new goals.GoalBlock(target.x, target.y, target.z), timeoutMs);
    }
    async walkSurface(x, z, timeoutMs) {
        const bot = this.bot;
        // Approximate travel: the exact column can be liquid or filled, so a
        // standable cell within a small ring is an acceptable destination. A
        // larger body of water still reports no_standable_surface.
        const surface = standableSurfaceNear(bot, x, z, 2);
        if (surface === null) {
            const requested = { x, y: bot.entity.position.y, z };
            return walkFailure(bot, requested, "no_standable_surface", "No standable surface near the target.", "no_path", 0, 0);
        }
        const result = await this.walk("minecraft_walk_to_surface", surface, new goals.GoalBlock(surface.x, surface.y, surface.z), timeoutMs);
        if (result.status === "reached")
            return result;
        // The direct surface column is unreachable. If the partial path stopped
        // at the base of an open vertical shaft, pillar up is the next step.
        const shaftBase = openShaftBaseNear(bot, result.final_position, 8);
        if (shaftBase !== null) {
            const approach = await this.walk("minecraft_walk_to_surface", shaftBase, new goals.GoalBlock(shaftBase.x, shaftBase.y, shaftBase.z), timeoutMs);
            if (approach.ok) {
                return walkFailure(bot, surface, "pillar_up_required", `Walked to ${shaftBase.x}, ${shaftBase.y}, ${shaftBase.z}; pillar up is required to reach the surface.`, "partial", approach.hops, result.duration_ms + approach.duration_ms);
            }
        }
        const directShaft = standableBelow(bot, x, z, surface.y - 1);
        if (directShaft === null)
            return result;
        const approach = await this.walk("minecraft_walk_to_surface", directShaft, new goals.GoalBlock(directShaft.x, directShaft.y, directShaft.z), timeoutMs);
        if (!approach.ok)
            return result;
        return walkFailure(bot, surface, "pillar_up_required", `Walked to ${directShaft.x}, ${directShaft.y}, ${directShaft.z}; pillar up is required to reach the surface.`, "partial", approach.hops, result.duration_ms + approach.duration_ms);
    }
    findPath(target, limit, timeoutMs) {
        const bot = this.bot;
        const started = performance.now();
        const start = vector(bot.entity.position);
        if (distance(start, target) > limit) {
            return unknownPreview(started);
        }
        const targetBlock = bot.blockAt(new Vec3(Math.floor(target.x), Math.floor(target.y), Math.floor(target.z)));
        const goal = targetBlock !== null && targetBlock.boundingBox !== "empty"
            ? new goals.GoalGetToBlock(targetBlock.position.x, targetBlock.position.y, targetBlock.position.z)
            : new goals.GoalBlock(target.x, target.y, target.z);
        const movements = survivalMovements(bot, target);
        bot.pathfinder.setMovements(movements);
        let preview = null;
        const search = bot.pathfinder.getPathFromTo(movements, bot.entity.position, goal, { timeout: timeoutMs });
        for (const step of search) {
            preview = step.result;
            if (preview.status !== "partial")
                break;
        }
        const elapsed = performance.now() - started;
        if (preview === null || preview.status === "noPath") {
            return {
                state: "blocked",
                path_length: null,
                hops: null,
                estimated_seconds: null,
                blocker: findBlockingCell(bot, start, target),
                duration_ms: elapsed,
            };
        }
        if (preview.status === "timeout") {
            return unknownPreview(started);
        }
        const pathLength = measurePathLength(preview.path);
        return {
            state: "reachable",
            path_length: pathLength,
            hops: preview.path.length,
            estimated_seconds: pathLength / WALK_SPEED_BLOCKS_PER_SECOND,
            blocker: null,
            duration_ms: elapsed,
        };
    }
    async useBlock(position, kind) {
        const bot = this.bot;
        const block = bot.blockAt(new Vec3(position.x, position.y, position.z));
        const properties = block.getProperties();
        await bot.lookAt(block.position.offset(0.5, 0.5, 0.5), true);
        await bot.activateBlock(block);
        await delay(300);
        return {
            action: activationAction(kind, properties.open === true),
            window: openedWindow(bot, kind, position),
        };
    }
    async equip(itemName) {
        const bot = this.bot;
        const previous = itemFromStack(bot.heldItem);
        const stack = bot.inventory.items().find((item) => item.name === itemName);
        await bot.equip(stack, "hand");
        return { previous_held: previous, held_item: itemFromStack(bot.heldItem), hotbar: hotbar(bot) };
    }
    async useItem() {
        const bot = this.bot;
        const before = this.state();
        const item = bot.heldItem;
        if (item === null)
            return { action: "nothing", reason: "not_usable", item: null, before, after: before };
        const name = item.name;
        if (bot.registry.foods[item.type] !== undefined) {
            if ((bot.food ?? 20) >= 20)
                return { action: "nothing", reason: "food_full", item: itemFromStack(item), before, after: before };
            await bot.consume();
            await delay(300);
            return { action: "ate", reason: null, item: itemFromStack(item), before, after: this.state() };
        }
        if (name === "potion" || name.endsWith("_potion")) {
            await bot.consume();
            await delay(300);
            return { action: "drank", reason: null, item: itemFromStack(item), before, after: this.state() };
        }
        if (name === "snowball" || name === "egg" || name === "ender_pearl" || name === "fishing_rod") {
            bot.activateItem();
            await delay(300);
            bot.deactivateItem();
            return { action: "threw", reason: null, item: itemFromStack(item), before, after: this.state() };
        }
        if (name === "shield") {
            bot.activateItem();
            await delay(300);
            bot.deactivateItem();
            return { action: "activated", reason: null, item: itemFromStack(item), before, after: this.state() };
        }
        return { action: "nothing", reason: "not_usable", item: itemFromStack(item), before, after: before };
    }
    async craft(itemName, repetitions) {
        const bot = this.bot;
        if (bot.currentWindow !== null)
            bot.closeWindow(bot.currentWindow);
        const item = bot.registry.itemsByName[itemName];
        const tables = Object.values(bot.findBlocks({ matching: bot.registry.blocksByName.crafting_table.id, maxDistance: 4, count: 1 }));
        const tablePosition = tables[0] ?? null;
        const table = tablePosition ? bot.blockAt(tablePosition) : null;
        const candidates = bot.recipesAll(item.id, null, true);
        if (candidates.length === 0) {
            return { ok: false, reason: "not_craftable", missing: [], item: null, repetitions: 0, table: null };
        }
        let recipe = null;
        let missing = [];
        let needsTable = false;
        for (const candidate of candidates) {
            const candidateMissing = missingIngredientsFor(bot, candidate, repetitions);
            if (candidateMissing.length === 0 && candidate.requiresTable && table === null)
                needsTable = true;
            if (candidateMissing.length === 0 && (!candidate.requiresTable || table !== null)) {
                recipe = candidate;
                break;
            }
            if (missing.length === 0)
                missing = candidateMissing;
        }
        if (recipe === null) {
            const reason = needsTable ? "crafting_table_not_found" : "missing_ingredients";
            return { ok: false, reason, missing: needsTable ? [] : missing, item: null, repetitions: 0, table: tablePosition ? vector(tablePosition) : null };
        }
        await bot.craft(recipe, repetitions, recipe.requiresTable ? table : undefined);
        await delay(300);
        const stack = bot.inventory.items().find((entry) => entry.name === itemName && entry.metadata === recipe.result.metadata);
        return { ok: true, reason: null, missing: [], item: stack ? itemFromStack(stack) : null, repetitions, table: tablePosition ? vector(tablePosition) : null };
    }
    async dropItem(itemName, count) {
        const bot = this.bot;
        const available = bot.inventory.items().filter((entry) => entry.name === itemName).reduce((sum, entry) => sum + entry.count, 0);
        const amount = count === null ? available : Math.min(count, available);
        const stack = bot.inventory.items().find((entry) => entry.name === itemName);
        if (amount > 0 && stack !== undefined) {
            await bot.toss(stack.type, stack.metadata, amount);
        }
        await delay(300);
        return { item: itemName, dropped: amount, drop_position: vector(bot.entity.position) };
    }
    async eatBest() {
        const bot = this.bot;
        const before = this.state();
        const foods = bot.inventory.items().filter((item) => bot.registry.foods[item.type] !== undefined);
        foods.sort((a, b) => ((bot.registry.foods[b.type]?.saturation ?? 0) - (bot.registry.foods[a.type]?.saturation ?? 0)));
        const considered = foods.map((item) => item.name);
        const best = foods[0];
        if (best === undefined)
            return { action: "nothing", item: null, considered, before, after: before };
        await bot.equip(best, "hand");
        if ((bot.food ?? 20) >= 20)
            return { action: "nothing", item: itemFromStack(best), considered, before, after: this.state() };
        await bot.consume();
        await delay(200);
        return { action: "ate", item: itemFromStack(best), considered, before, after: this.state() };
    }
    async equipBestTool(target) {
        const bot = this.bot;
        const previous = itemFromStack(bot.heldItem);
        const block = bot.blockAt(new Vec3(Math.floor(target.x), Math.floor(target.y), Math.floor(target.z)));
        const best = block === null ? null : bot.pathfinder.bestHarvestTool(block);
        if (best !== null && best !== undefined) {
            await bot.equip(best, "hand");
        }
        return {
            target_block: block?.name ?? null,
            best_possible_tool: best?.name ?? null,
            previous_held: previous,
            held_item: itemFromStack(bot.heldItem),
            hotbar: hotbar(bot),
        };
    }
    async safeToDig(target) {
        const bot = this.bot;
        const center = { x: Math.floor(target.x), y: Math.floor(target.y), z: Math.floor(target.z) };
        const hazards = [];
        const cells = [];
        for (let dx = -2; dx <= 2; dx += 1) {
            for (let dz = -2; dz <= 2; dz += 1) {
                for (let dy = -2; dy <= 2; dy += 1) {
                    if (dx === 0 && dy === 0 && dz === 0)
                        continue;
                    cells.push({ x: center.x + dx, y: center.y + dy, z: center.z + dz });
                }
            }
        }
        const loaded = this.blocks(cells);
        const byKey = new Map(loaded.map((cell) => [`${cell.position.x},${cell.position.y},${cell.position.z}`, cell]));
        for (const cell of loaded) {
            const dx = cell.position.x - center.x;
            const dy = cell.position.y - center.y;
            const dz = cell.position.z - center.z;
            if (cell.name === "lava") {
                hazards.push(liquidHazard(dx, dy, dz, cell.position, "lava"));
            }
            else if (cell.name === "water" || cell.name.startsWith("water")) {
                hazards.push(liquidHazard(dx, dy, dz, cell.position, "water"));
            }
        }
        const player = bot.entity.position;
        const offsetX = center.x - player.x;
        const offsetZ = center.z - player.z;
        const step = Math.abs(offsetX) >= Math.abs(offsetZ)
            ? { x: Math.sign(offsetX), z: 0 }
            : { x: 0, z: Math.sign(offsetZ) };
        const behind = byKey.get(`${center.x + step.x},${center.y},${center.z + step.z}`);
        const behindIsLiquid = behind !== undefined
            && (behind.name === "lava" || behind.name.startsWith("water"));
        const willFall = behind !== undefined && behind.replaceable && !behindIsLiquid;
        if (willFall) {
            hazards.push({ kind: "fall", direction: directionFromOffset(step.x, 0, step.z), position: behind.position, distance_band: "immediate", note: "Open space behind the block can cause a fall." });
        }
        else if (behind?.name === "bedrock" || behind?.name === "gravel") {
            hazards.push({ kind: behind.name === "bedrock" ? "cave" : "fall", direction: directionFromOffset(step.x, 0, step.z), position: behind.position, distance_band: "immediate", note: `${behind.display_name} is directly behind the target.` });
        }
        const now = Date.now();
        this.recentSounds = this.recentSounds.filter((sound) => now - sound.at <= 15000);
        for (const sound of this.recentSounds) {
            const kind = sound.name.includes("lava") ? "lava" : sound.name.includes("water") ? "water" : null;
            if (kind === null)
                continue;
            const soundPosition = { x: sound.x, y: sound.y, z: sound.z };
            if (distance(player, soundPosition) > 16 * sound.volume)
                continue;
            hazards.push({
                kind,
                direction: directionFromOffset(sound.x - center.x, sound.y - center.y, sound.z - center.z),
                position: null,
                distance_band: "audible",
                note: `Recent ${kind} sound nearby.`,
            });
        }
        const fallDepth = willFall ? measureFallDepth(bot, center) : null;
        const risk = hazards.length > 0 ? "warning" : "low_risk";
        return { risk, hazards, will_fall: willFall ? true : false, fall_depth: fallDepth };
    }
    async craftMax(itemName, limit) {
        const bot = this.bot;
        const item = bot.registry.itemsByName[itemName];
        if (item === undefined)
            return { item: itemName, crafted: 0, table: null, reason: "not_found", missing: [] };
        const recipes = bot.recipesAll(item.id, null, true);
        if (recipes.length === 0)
            return { item: itemName, crafted: 0, table: null, reason: "not_craftable", missing: [] };
        const hasTable = bot.findBlocks({ matching: bot.registry.blocksByName.crafting_table.id, maxDistance: 4, count: 1 }).length > 0;
        recipes.sort((a, b) => ((!b.requiresTable || hasTable) ? maxCraftRuns(bot, b) * b.result.count : 0)
            - ((!a.requiresTable || hasTable) ? maxCraftRuns(bot, a) * a.result.count : 0));
        const recipe = recipes[0];
        const outputCount = recipe.result.count;
        const itemCap = limit === null ? Number.MAX_SAFE_INTEGER : Math.floor(limit / outputCount);
        const maxRuns = Math.min(itemCap, maxCraftRuns(bot, recipe));
        if (itemCap <= 0)
            return { item: itemName, crafted: 0, table: null, reason: "limit_below_output", missing: [] };
        if (maxRuns <= 0) {
            const result = await this.craft(itemName, 1);
            return { item: itemName, crafted: 0, table: result.table, reason: result.reason, missing: result.missing };
        }
        const result = await this.craft(itemName, maxRuns);
        await delay(300);
        const runs = result.ok ? result.repetitions : 0;
        return { item: itemName, crafted: runs * outputCount, table: result.table, reason: result.reason, missing: result.missing };
    }
    async sleep(bed) {
        const bot = this.bot;
        const bedBlock = bed === null ? findNearestBed(bot) : bot.blockAt(new Vec3(Math.floor(bed.x), Math.floor(bed.y), Math.floor(bed.z)));
        if (bedBlock === null || !isBed(bedBlock)) {
            return { ok: false, reason: "no_bed", slept: false, is_day_now: bot.time?.isDay ?? false, blocking_entity: null };
        }
        if (distance(vector(bot.entity.position), blockVector(bedBlock)) > 5) {
            return { ok: false, reason: "out_of_range", slept: false, is_day_now: bot.time?.isDay ?? false, blocking_entity: null };
        }
        try {
            await bot.sleep(bedBlock);
            const deadline = Date.now() + 15000;
            while (Date.now() < deadline && !bot.time.isDay) {
                await delay(100);
            }
            const isDayNow = bot.time.isDay;
            // Never leave the player lying in the bed when the night did not skip.
            if (bot.isSleeping)
                await bot.wake();
            return { ok: true, reason: null, slept: true, is_day_now: isDayNow, blocking_entity: null };
        }
        catch (error) {
            const message = String(error.message);
            if (message.includes("monsters")) {
                return { ok: false, reason: "monster_nearby", slept: false, is_day_now: bot.time?.isDay ?? false, blocking_entity: nearestHostileRef(bot, bedBlock.position) };
            }
            if (message.includes("too far")) {
                return { ok: false, reason: "out_of_range", slept: false, is_day_now: bot.time?.isDay ?? false, blocking_entity: null };
            }
            if (message.includes("half bed")) {
                return { ok: false, reason: "bed_obstructed", slept: false, is_day_now: bot.time?.isDay ?? false, blocking_entity: null };
            }
            return { ok: false, reason: "bed_occupied", slept: false, is_day_now: bot.time?.isDay ?? false, blocking_entity: null };
        }
    }
    async pillarUp() {
        const bot = this.bot;
        const feet = bot.entity.position;
        const feetCell = new Vec3(Math.floor(feet.x), Math.floor(feet.y), Math.floor(feet.z));
        const held = bot.heldItem;
        if (held === null)
            return { ok: false, reason: "no_held_item", climbed: 0, blocks_placed: 0, camera: cameraFromBot(bot) };
        if (!itemIsBlock(bot, held))
            return { ok: false, reason: "not_placeable", climbed: 0, blocks_placed: 0, camera: cameraFromBot(bot) };
        const headBlock = bot.blockAt(feetCell.offset(0, 2, 0));
        if (headBlock !== null && headBlock.boundingBox !== "empty") {
            return { ok: false, reason: "no_headroom", climbed: 0, blocks_placed: 0, camera: cameraFromBot(bot) };
        }
        const below = bot.blockAt(feetCell.offset(0, -1, 0));
        if (below === null || below.boundingBox === "empty") {
            return { ok: false, reason: "not_placeable", climbed: 0, blocks_placed: 0, camera: cameraFromBot(bot) };
        }
        await bot.equip(held, "hand");
        await bot.lookAt(feetCell.offset(0.5, -0.5, 0.5), true);
        bot.setControlState("jump", true);
        await delay(300);
        try {
            await bot.placeBlock(below, new Vec3(0, 1, 0));
            await delay(120);
        }
        catch {
            bot.clearControlStates();
            return { ok: false, reason: "not_placeable", climbed: 0, blocks_placed: 0, camera: cameraFromBot(bot) };
        }
        bot.clearControlStates();
        await delay(250);
        return { ok: true, reason: null, climbed: 1, blocks_placed: 1, camera: cameraFromBot(bot) };
    }
    async recipeSearch(itemNames, craftableNow, limit) {
        const bot = this.bot;
        const matches = [];
        for (const itemName of itemNames) {
            if (matches.length >= limit)
                break;
            const item = bot.registry.itemsByName[itemName];
            if (item === undefined)
                continue;
            const recipes = bot.recipesAll(item.id, null, true);
            if (recipes.length === 0)
                continue;
            matches.push(recipeEntryFrom(bot, itemName, recipes[0], craftableNow));
        }
        const total = Object.keys(bot.registry.recipes).length;
        return { matches, total_recipes: total };
    }
    async scanHorizon() {
        const bot = this.bot;
        const started = performance.now();
        const head = bot.entity.position.offset(0, 1.62, 0);
        const rays = [];
        for (let index = 0; index < 24; index += 1) {
            const heading = index * 15;
            for (const pitch of [15, 0, -15]) {
                const hit = this.raycastDirection(head, heading, pitch);
                rays.push({ heading_degrees: heading, cardinal: eightCardinal(heading), pitch, hit: hit.hit, block_name: hit.hit_block, distance: hit.distance });
            }
        }
        return {
            origin: vector(bot.entity.position),
            rays,
            sectors: aggregateSectors(rays),
            landmarks: inferLandmarks(rays),
            duration_ms: performance.now() - started,
        };
    }
    raycastDirection(head, yawDeg, pitchDeg) {
        const bot = this.bot;
        const yaw = yawDeg * Math.PI / 180;
        const pitch = pitchDeg * Math.PI / 180;
        const horizontal = Math.cos(pitch);
        const direction = new Vec3(-Math.sin(yaw) * horizontal, Math.sin(pitch), -Math.cos(yaw) * horizontal).normalize();
        let lastCell = null;
        for (let rayDistance = 0; rayDistance <= 128; rayDistance += 0.25) {
            const point = head.offset(direction.x * rayDistance, direction.y * rayDistance, direction.z * rayDistance);
            const cell = point.floored();
            if (lastCell !== null && lastCell.equals(cell))
                continue;
            lastCell = cell;
            const block = bot.blockAt(cell);
            if (block === null || VOID_BLOCKS.has(block.name))
                continue;
            return { hit: true, hit_block: block.name, distance: head.distanceTo(block.position) };
        }
        return { hit: false, hit_block: null, distance: null };
    }
    async staircaseDown(depth, torch) {
        const bot = this.bot;
        const notchianDegrees = normalizeDegrees((Math.PI - bot.entity.yaw) * 180 / Math.PI);
        const dir = forwardStep(notchianDegrees);
        const hazards = [];
        let blocksDug = 0;
        let torchesPlaced = 0;
        let depthAchieved = 0;
        for (let step = 0; step < depth; step += 1) {
            const feet = bot.entity.position.floored();
            const stepCell = feet.offset(dir.x, -1, dir.z);
            const stepBlock = bot.blockAt(stepCell);
            const stepHazard = stairHazardName(stepBlock);
            if (stepHazard !== null) {
                hazards.push(stepHazard);
                break;
            }
            let stopped = false;
            for (const cell of [
                feet.offset(dir.x, 1, dir.z),
                feet.offset(dir.x, 0, dir.z),
                stepCell,
            ]) {
                const block = bot.blockAt(cell);
                if (block === null || VOID_BLOCKS.has(block.name))
                    continue;
                const cellHazard = stairHazardName(block);
                if (cellHazard !== null) {
                    hazards.push(cellHazard);
                    stopped = true;
                    break;
                }
                await this.equipBestTool(vector(cell));
                const mineResult = await this.mine(vector(cell));
                if (!mineResult.can_harvest) {
                    hazards.push(block.name);
                    stopped = true;
                    break;
                }
                blocksDug += 1;
            }
            if (stopped)
                break;
            await this.stepForward();
            depthAchieved += 1;
            if (torch && depthAchieved % 3 === 0) {
                if (await this.placeTorch())
                    torchesPlaced += 1;
            }
        }
        return {
            depth_requested: depth,
            depth_achieved: depthAchieved,
            end_position: vector(bot.entity.position),
            blocks_dug: blocksDug,
            hazards_found: hazards,
            torches_placed: torchesPlaced,
        };
    }
    async stepForward() {
        const bot = this.bot;
        const startY = Math.floor(bot.entity.position.y);
        for (let attempt = 0; attempt < 3; attempt += 1) {
            if (Math.floor(bot.entity.position.y) < startY)
                break;
            await bot.look(bot.entity.yaw, 0, true);
            bot.setControlState("forward", true);
            await delay(500);
            bot.clearControlStates();
            await delay(500);
        }
        await delay(600);
    }
    async placeTorch() {
        const bot = this.bot;
        const torch = bot.inventory.items().find((item) => item.name === "torch");
        if (torch === undefined)
            return false;
        await bot.equip(torch, "hand");
        const feet = bot.entity.position.floored();
        const candidates = [
            { block: feet.offset(1, 1, 0), face: new Vec3(-1, 0, 0) },
            { block: feet.offset(-1, 1, 0), face: new Vec3(1, 0, 0) },
            { block: feet.offset(0, 2, 0), face: new Vec3(0, -1, 0) },
        ];
        for (const candidate of candidates) {
            const block = bot.blockAt(candidate.block);
            if (block !== null && block.boundingBox !== "empty") {
                try {
                    await bot.placeBlock(block, candidate.face);
                    return true;
                }
                catch {
                    // try the next candidate face
                }
            }
        }
        return false;
    }
    async executeSkill(path, source, argumentsValue, budgetMs) {
        const started = performance.now();
        const denied = detectForbiddenAccess(source);
        if (denied !== null) {
            return { status: "access_denied", reason: denied, stdout_tail: null, stderr_tail: null,
                heartbeats: 0, duration_ms: performance.now() - started };
        }
        this.currentSkill = path;
        this.skillStopRequested = false;
        let heartbeats = 0;
        const api = this.survivalApi(started + budgetMs, () => { heartbeats += 1; });
        try {
            const result = await skillRunner.run(source, argumentsValue, budgetMs, api, () => {
                this.skillStopRequested = true;
                this.commandStopped = true;
                this.bot.pathfinder.setGoal(null);
                this.bot.clearControlStates();
                this.bot.stopDigging();
            });
            return { ...result, heartbeats, duration_ms: performance.now() - started };
        }
        finally {
            this.currentSkill = null;
        }
    }
    survivalApi(deadline, heartbeat) {
        const bot = this.bot;
        const check = () => {
            if (this.skillStopRequested)
                throw new SkillStoppedError("The skill was stopped.");
            if (performance.now() > deadline)
                throw new SkillAbortError("The skill time budget expired.");
        };
        const methods = {
            observe: async (args = {}) => {
                check();
                heartbeat();
                const radius = args.radius ?? 8;
                const state = this.state();
                return {
                    ...state,
                    nearby_blocks: this.nearbyBlocks(state.camera.feet_position, radius),
                    nearby_entities: this.nearbyEntities(state.camera.feet_position, radius),
                };
            },
            rotate: async (args) => {
                check();
                heartbeat();
                return { camera: await this.rotate(args.yawDegrees, args.pitchDegrees, args.absolute) };
            },
            lookAt: async (args) => {
                check();
                heartbeat();
                return { camera: await this.lookAt(args.position) };
            },
            fineControl: async (args = {}) => {
                check();
                heartbeat();
                const { durationMs, ...controls } = args;
                return await this.fineControl(controls, durationMs ?? 250);
            },
            walkVisible: async (args) => {
                check();
                heartbeat();
                return await this.walkVisible(args.target, args.limit, args.timeoutMs);
            },
            walkExact: async (args) => {
                check();
                heartbeat();
                return await this.walkExact(args.target, args.timeoutMs);
            },
            walkSurface: async (args) => {
                check();
                heartbeat();
                return await this.walkSurface(args.x, args.z, args.timeoutMs);
            },
            findPath: (args) => {
                check();
                heartbeat();
                return this.findPath(args.target, args.limit, args.timeoutMs);
            },
            useBlock: async (args) => {
                check();
                heartbeat();
                return await this.useBlock(args.position, args.kind);
            },
            equip: async (args) => {
                check();
                heartbeat();
                return await this.equip(args.item);
            },
            useItem: async () => {
                check();
                heartbeat();
                return await this.useItem();
            },
            craft: async (args) => {
                check();
                heartbeat();
                return await this.craft(args.item, args.repetitions);
            },
            mineBlock: async (args) => {
                check();
                heartbeat();
                return await this.mine(args.position);
            },
            attack: async (args) => {
                check();
                heartbeat();
                return await this.attack(args.entityId, args.limit);
            },
            chestMove: async (args) => {
                check();
                heartbeat();
                return await this.chestMove(args.position, args.item, args.count, args.direction);
            },
            smelt: async (args) => {
                check();
                heartbeat();
                return await this.smelt(args.position, args.input, args.inputCount, args.fuel, args.fuelCount);
            },
            drop: async (args) => {
                check();
                heartbeat();
                return await this.dropItem(args.item, args.count);
            },
            eatBest: async () => {
                check();
                heartbeat();
                return await this.eatBest();
            },
            equipBestTool: async (args) => {
                check();
                heartbeat();
                return await this.equipBestTool(args.target);
            },
            safeToDig: async (args) => {
                check();
                heartbeat();
                return await this.safeToDig(args.position);
            },
            craftMax: async (args) => {
                check();
                heartbeat();
                return await this.craftMax(args.item, args.limit);
            },
            sleep: async (args) => {
                check();
                heartbeat();
                return await this.sleep(args.bed ?? null);
            },
            pillarUp: async () => {
                check();
                heartbeat();
                return await this.pillarUp();
            },
            recipeSearch: async (args) => {
                check();
                heartbeat();
                return await this.recipeSearch(args.itemNames, args.craftableNow, args.limit);
            },
            scanHorizon: async () => {
                check();
                heartbeat();
                return await this.scanHorizon();
            },
            findBlocks: (args) => {
                check();
                heartbeat();
                return this.findBlocks(args);
            },
            stop: async () => {
                check();
                heartbeat();
                return await this.stopCommand();
            },
        };
        return new Proxy(methods, {
            get(target, property) {
                if (typeof property === "symbol")
                    return undefined;
                if (property in target)
                    return target[property];
                return () => {
                    throw new AccessDeniedError(`The survival API does not expose '${property}'.`);
                };
            },
        });
    }
    async mine(position) {
        const bot = this.bot;
        const block = bot.blockAt(new Vec3(position.x, position.y, position.z));
        if (block.boundingBox === "empty")
            throw new Error("target is not a solid block");
        await bot.lookAt(block.position.offset(0.5, 0.5, 0.5), true);
        const tool = bot.heldItem?.name ?? null;
        const canHarvest = block.canHarvest(bot.heldItem?.type ?? null) === true;
        const drops = (block.drops ?? [])
            .map((drop) => typeof drop === "number" ? drop : typeof drop.drop === "number" ? drop.drop : drop.drop.id)
            .map((id) => bot.registry.items[id]?.name)
            .filter((name) => name !== undefined);
        if (!canHarvest) {
            return { ok: false, reason: "unharvestable", block: { position, name: block.name, display_name: block.displayName, replaceable: false }, tool_used: tool, can_harvest: false, drops: [] };
        }
        try {
            await bot.dig(block, true);
        }
        catch (error) {
            const current = bot.blockAt(new Vec3(position.x, position.y, position.z));
            if (current === null || current.name !== block.name) {
                return { ok: false, reason: "target_changed", block: { position, name: current?.name ?? "air", display_name: current?.displayName ?? "Air", replaceable: current?.boundingBox === "empty" }, tool_used: tool, can_harvest: canHarvest, drops: [] };
            }
            throw error;
        }
        await delay(1000);
        // mineflayer resolves dig() without waiting for the server ack; a
        // mid-dig block swap aborts the server-side dig and leaves a block here.
        // A completed dig can expose cave air or be replaced by flowing liquid.
        const after = bot.blockAt(new Vec3(position.x, position.y, position.z));
        if (after === null || !["air", "cave_air", "void_air", "water", "lava"].includes(after.name)) {
            return { ok: false, reason: "target_changed", block: { position, name: after?.name ?? "unknown", display_name: after?.displayName ?? "Unknown", replaceable: after?.boundingBox === "empty" }, tool_used: tool, can_harvest: canHarvest, drops: [] };
        }
        return { ok: true, reason: null, block: { position, name: "air", display_name: "Air", replaceable: true }, tool_used: tool, can_harvest: canHarvest, drops };
    }
    async attack(entityId, limit) {
        const bot = this.bot;
        const entity = bot.entities[entityId];
        let hits = 0;
        let interrupted = false;
        const recordDamage = (packet) => {
            if (packet.entityId === entityId && packet.sourceCauseId !== bot.entity.id + 1) {
                interrupted = true;
            }
        };
        bot._client.on("damage_event", recordDamage);
        try {
            while (hits < limit && bot.entities[entityId] !== undefined) {
                const target = bot.entities[entityId];
                if (target.position.distanceTo(bot.entity.position) > 3) {
                    await bot.lookAt(target.position, true);
                    bot.setControlState("forward", true);
                    await delay(250);
                    bot.clearControlStates();
                    continue;
                }
                await bot.lookAt(target.position, true);
                await bot.attack(target);
                hits += 1;
                await delay(700);
            }
        }
        finally {
            bot.clearControlStates();
            bot._client.removeListener("damage_event", recordDamage);
        }
        const remaining = bot.entities[entityId];
        return { entity_id: entityId, entity_type: entity.name ?? targetName(entity), killed: remaining === undefined && !interrupted, interrupted, hits, health: remaining?.health ?? null, drops: [] };
    }
    async chestMove(position, itemName, count, direction) {
        const bot = this.bot;
        const block = bot.blockAt(new Vec3(position.x, position.y, position.z));
        const window = await bot.openContainer(block);
        await delay(250);
        const current = bot.blockAt(new Vec3(position.x, position.y, position.z));
        if (current === null || !["chest", "trapped_chest", "barrel", "shulker_box"].includes(current.name)) {
            window.close();
            return { moved_count: 0, available_count: 0, inventory_space: 0, window: null };
        }
        const item = bot.registry.itemsByName[itemName];
        const availableCount = direction === "withdraw"
            ? window.slots.slice(0, window.inventoryStart).filter((stack) => stack?.type === item?.id).reduce((sum, stack) => sum + stack.count, 0)
            : bot.inventory.items().filter((stack) => stack.type === item?.id).reduce((sum, stack) => sum + stack.count, 0);
        const partialSpace = direction === "withdraw"
            ? bot.inventory.items().filter((stack) => stack.type === item?.id).reduce((sum, stack) => sum + Math.max(0, stack.stackSize - stack.count), 0)
            : count;
        const inventorySpace = direction === "withdraw" ? partialSpace + bot.inventory.emptySlotCount() * (item?.stackSize ?? 64) : count;
        const movedCount = Math.min(count, availableCount, inventorySpace);
        if (movedCount > 0 && item !== undefined) {
            if (direction === "deposit")
                await window.deposit(item.id, null, movedCount);
            else
                await window.withdraw(item.id, null, movedCount);
        }
        await delay(250);
        const result = { moved_count: movedCount, available_count: availableCount, inventory_space: inventorySpace, window: openedWindow(bot, "chest", position) };
        window.close();
        return result;
    }
    async smelt(position, inputName, inputCount, fuelName, fuelCount) {
        const bot = this.bot;
        const block = bot.blockAt(new Vec3(position.x, position.y, position.z));
        const furnace = await bot.openFurnace(block);
        const input = bot.registry.itemsByName[inputName];
        const fuel = bot.registry.itemsByName[fuelName];
        await furnace.putInput(input.id, null, inputCount);
        await furnace.putFuel(fuel.id, null, fuelCount);
        while ((furnace.outputItem()?.count ?? 0) < inputCount) {
            await delay(250);
            const current = bot.blockAt(new Vec3(position.x, position.y, position.z));
            if (current === null || current.name !== "furnace") {
                furnace.close();
                return { ok: false, reason: "target_changed", output: null, input_consumed: inputCount, fuel_consumed: fuelCount, window: null };
            }
        }
        const output = itemFromStack(furnace.outputItem());
        await furnace.takeOutput();
        await delay(300);
        const window = openedWindow(bot, "furnace", position);
        furnace.close();
        return { ok: true, reason: null, output, input_consumed: inputCount, fuel_consumed: fuelCount, window };
    }
    async stopCommand(scope = "both") {
        const command = scope === "command" || scope === "both" ? this.currentCommand : null;
        const skill = scope === "skill" || scope === "both" ? this.currentSkill : null;
        this.commandStopped = command !== null;
        this.skillStopRequested = skill !== null;
        if (skill !== null)
            skillRunner.stop();
        const bot = this.bot;
        bot.pathfinder.setGoal(null);
        bot.clearControlStates();
        bot.entity.velocity.x = 0;
        bot.entity.velocity.z = 0;
        await delay(150);
        return { stopped_command: command, stopped_skill: skill, camera: cameraFromBot(bot) };
    }
    screenshot() {
        return this.capture.capture();
    }
    /**
     * One fresh debug line: full state, camera, live 5x5x5 surroundings, and
     * nearby entities. Every block read happens at call time; nothing is reused
     * from an earlier request.
     */
    debugSnapshot() {
        const bot = this.bot;
        const state = this.state();
        const cell = blockCell(state.camera?.feet_position ?? { x: 0, y: 0, z: 0 });
        const rows = [];
        for (let dy = 2; dy >= -2; dy -= 1) {
            const row = [];
            for (let dz = -2; dz <= 2; dz += 1) {
                for (let dx = -2; dx <= 2; dx += 1) {
                    row.push(bot.blockAt(new Vec3(cell.x + dx, cell.y + dy, cell.z + dz))?.name ?? "null");
                }
            }
            rows.push(`y${dy >= 0 ? "+" : ""}${dy}[${row.join(" ")}]`);
        }
        const entities = Object.values(bot.entities)
            .filter((entity) => entity !== bot.entity)
            .slice(0, 20)
            .map((entity) => `${entity.name ?? entity.username ?? entity.id}@${Math.round(entity.position.x)},${Math.round(entity.position.y)},${Math.round(entity.position.z)}`);
        return `${JSON.stringify(state)} surroundings=${rows.join(" ")} entities=[${entities.join(", ")}]`;
    }
    async walk(command, target, goal, timeoutMs) {
        const bot = this.bot;
        const started = performance.now();
        const startPosition = vector(bot.entity.position);
        const movements = survivalMovements(bot, target);
        bot.pathfinder.setMovements(movements);
        bot.pathfinder.thinkTimeout = timeoutMs;
        let effectiveGoal = goal;
        const preview = bot.pathfinder.getPathTo(movements, goal, timeoutMs);
        const diagnostic = (cause, error) => ({
            ...walkDiagnostics(bot, target, cause),
            path_status: preview.status,
            error_name: error instanceof Error ? error.name : null,
            error_message: error === undefined ? null : error instanceof Error ? error.message : String(error),
        });
        if (preview.status === "noPath") {
            const partialNode = furthestReachableNode(bot, movements, goal, timeoutMs);
            if (partialNode === null) {
                return walkFailure(bot, target, "no_path", "No route found within the configured movement rules and search corridor.", "no_path", 0, performance.now() - started, diagnostic("search_no_path"));
            }
            effectiveGoal = new goals.GoalBlock(partialNode.x, partialNode.y, partialNode.z);
        }
        if (preview.status === "timeout") {
            return walkFailure(bot, target, "timeout", "The path search time limit expired.", "timeout", 0, performance.now() - started, diagnostic("search_timeout"));
        }
        this.currentCommand = command;
        this.commandStopped = false;
        let timeout = null;
        try {
            await Promise.race([
                bot.pathfinder.goto(effectiveGoal),
                new Promise((_resolve, reject) => {
                    timeout = setTimeout(() => {
                        bot.pathfinder.setGoal(null);
                        const error = new Error("The walk time limit expired.");
                        error.name = "WalkTimeout";
                        reject(error);
                    }, timeoutMs);
                }),
            ]);
            await delay(150);
            const duration = performance.now() - started;
            this.currentCommand = null;
            if (distance(bot.entity.position, target) > this.configuration.walkReachedDistanceBlocks) {
                return walkFailure(bot, target, "no_path", `The path ended ${distance(bot.entity.position, target).toFixed(2)} blocks from the target, outside the ${this.configuration.walkReachedDistanceBlocks}-block reached distance.`, "partial", 1, duration, diagnostic("outside_reached_distance"));
            }
            return walkSuccess(bot, target, duration, diagnostic(effectiveGoal === goal ? "goal_reached" : "partial_goal_within_tolerance"));
        }
        catch (error) {
            await delay(150);
            const duration = performance.now() - started;
            const stopped = this.commandStopped;
            this.currentCommand = null;
            if (stopped) {
                return walkFailure(bot, target, "stopped", "The walk was stopped.", "partial", 0, duration, diagnostic("stopped", error));
            }
            if (error instanceof Error && (error.name === "WalkTimeout" || error.name === "Timeout")) {
                const replanning = error.name === "Timeout";
                return walkFailure(bot, target, "timeout", error.message, "timeout", 0, duration, diagnostic(replanning ? "replanning_timeout" : "movement_timeout", error));
            }
            const status = distance(startPosition, bot.entity.position) > 0.05 ? "partial" : "no_path";
            const noPath = error instanceof Error && error.name === "NoPath";
            return walkFailure(bot, target, noPath ? "no_path" : "movement_error", error instanceof Error ? `${error.name}: ${error.message}` : String(error), status, 0, duration, diagnostic(noPath ? "movement_no_path" : "movement_error", error));
        }
        finally {
            if (timeout !== null) {
                clearTimeout(timeout);
            }
            bot.clearControlStates();
        }
    }
    catalog() {
        const bot = this.bot;
        return {
            blocks: Object.values(bot.registry.blocksByName).map((block) => ({
                name: block.name,
                display_name: block.displayName,
            })),
            items: Object.values(bot.registry.itemsByName).map((item) => ({
                name: item.name,
                display_name: item.displayName,
            })),
        };
    }
    blocks(positions) {
        const bot = this.bot;
        return positions.map((position) => {
            const block = bot.blockAt(new Vec3(position.x, position.y, position.z));
            return {
                position,
                name: block.name,
                display_name: block.displayName,
                replaceable: block.boundingBox === "empty",
            };
        });
    }
    async close() {
        await skillRunner.close();
        this.stopped = true;
        if (this.retry !== null) {
            clearTimeout(this.retry);
        }
        this.bot?.quit("MCP stopped");
        await this.capture.close();
    }
}
function survivalMovements(bot, target) {
    const movements = new Movements(bot);
    movements.canDig = false;
    movements.allow1by1towers = false;
    movements.allowParkour = false;
    movements.scafoldingBlocks = [];
    movements.maxDropDown = 1;
    movements.infiniteLiquidDropdownDistance = false;
    if (target !== null) {
        // A generous corridor around the start-to-target line. It must be wide
        // enough for real detours (cave exits, staircases) while keeping an
        // unreachable goal fast to prove: without it the search would need to
        // exhaust every loaded chunk before reporting no path.
        const margin = 32;
        const start = bot.entity.position;
        const minimumX = Math.min(Math.floor(start.x), Math.floor(target.x)) - margin;
        const maximumX = Math.max(Math.floor(start.x), Math.floor(target.x)) + margin;
        const minimumZ = Math.min(Math.floor(start.z), Math.floor(target.z)) - margin;
        const maximumZ = Math.max(Math.floor(start.z), Math.floor(target.z)) + margin;
        movements.exclusionAreasStep.push((block) => block.position.x < minimumX || block.position.x > maximumX ||
            block.position.z < minimumZ || block.position.z > maximumZ ? 100 : 0);
    }
    return movements;
}
function missingIngredientsFor(bot, recipe, repetitions) {
    const missing = [];
    for (const delta of recipe.delta) {
        if (delta.count >= 0)
            continue;
        const need = -delta.count * repetitions;
        const have = bot.inventory.count(delta.id, delta.metadata);
        if (have < need) {
            const item = bot.registry.items[delta.id];
            missing.push({ item: item && item.name ? item.name : String(delta.id), required: need, have });
        }
    }
    return missing;
}
function liquidHazard(dx, dy, dz, position, kind) {
    const direction = directionFromOffset(dx, dy, dz);
    const distance = Math.max(Math.abs(dx), Math.abs(dy), Math.abs(dz));
    const band = distance === 1 ? "immediate" : distance === 2 ? "near" : "audible";
    return {
        kind,
        direction,
        position,
        distance_band: band,
        note: kind === "lava" ? "Lava can flow in when you break the block." : "Water can flow in when you break the block.",
    };
}
function directionFromOffset(dx, dy, dz) {
    if (Math.abs(dx) >= Math.abs(dy) && Math.abs(dx) >= Math.abs(dz))
        return dx >= 0 ? "east" : "west";
    if (Math.abs(dz) >= Math.abs(dy))
        return dz >= 0 ? "south" : "north";
    return dy >= 0 ? "up" : "down";
}
function measureFallDepth(bot, center) {
    let depth = 0;
    for (let y = center.y - 2; y >= -64; y -= 1) {
        const block = bot.blockAt(new Vec3(center.x, y, center.z));
        if (block === null || block.boundingBox === "empty") {
            depth += 1;
        }
        else {
            break;
        }
    }
    return depth;
}
function isBed(block) {
    return block.name.endsWith("_bed");
}
function findNearestBed(bot) {
    const bedIds = Object.values(bot.registry.blocksByName)
        .filter((block) => block.name.endsWith("_bed"))
        .map((block) => block.id);
    const positions = Object.values(bot.findBlocks({ matching: bedIds, maxDistance: 8, count: 10 }));
    if (positions.length === 0)
        return null;
    return bot.blockAt(new Vec3(positions[0].x, positions[0].y, positions[0].z));
}
function nearestHostileRef(bot, position) {
    let nearest = null;
    for (const entity of Object.values(bot.entities)) {
        if (entity.kind !== "Hostile mobs")
            continue;
        const d = entity.position.distanceTo(new Vec3(position.x, position.y, position.z));
        if (nearest === null || d < nearest.distance)
            nearest = { entity, distance: d };
    }
    return nearest === null ? null : entityRef(nearest.entity, nearest.distance);
}
function itemIsBlock(bot, item) {
    return bot.registry.blocksByName[item.name] !== undefined;
}
function maxCraftRuns(bot, recipe) {
    let max = Number.MAX_SAFE_INTEGER;
    for (const delta of recipe.delta) {
        if (delta.count >= 0)
            continue;
        const have = bot.inventory.count(delta.id, delta.metadata);
        max = Math.min(max, Math.floor(have / -delta.count));
    }
    return max;
}
function allIngredientsFor(bot, recipe, repetitions) {
    const result = [];
    for (const delta of recipe.delta) {
        if (delta.count >= 0)
            continue;
        const need = -delta.count * repetitions;
        const have = bot.inventory.count(delta.id, delta.metadata);
        const item = bot.registry.items[delta.id];
        result.push({ item: item && item.name ? item.name : String(delta.id), required: need, have });
    }
    return result;
}
function recipeEntryFrom(bot, itemName, recipe, craftableNow) {
    let grid = "";
    const legend = {};
    if (recipe.inShape) {
        const symbols = "ABCDEFGHI".split("");
        let index = 0;
        grid = recipe.inShape.map((row) => row.map((cell) => {
            if (cell.id === -1)
                return ".";
            const symbol = symbols[index++];
            const item = bot.registry.items[cell.id];
            legend[symbol] = item && item.name ? item.name : String(cell.id);
            return symbol;
        }).join("")).join("\n");
    }
    else if (recipe.ingredients) {
        const symbols = "ABCDEFGHI".split("");
        grid = recipe.ingredients.map((ing, index) => {
            const symbol = symbols[index];
            const item = bot.registry.items[ing.id];
            legend[symbol] = item && item.name ? item.name : String(ing.id);
            return symbol;
        }).join("");
    }
    const ingredients = allIngredientsFor(bot, recipe, 1);
    const missing = missingIngredientsFor(bot, recipe, 1);
    return {
        item_name: itemName,
        display_name: bot.registry.itemsByName[itemName]?.displayName ?? itemName,
        grid,
        legend,
        ingredients,
        output_count: recipe.result.count,
        needs_crafting_table: recipe.requiresTable,
        craftable_now: craftableNow === null ? missing.length === 0 : craftableNow === (missing.length === 0),
    };
}
function eightCardinal(heading) {
    const names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
    return names[Math.round((heading / 45) % 8) % 8];
}
function aggregateSectors(rays) {
    const byCardinal = new Map();
    for (const ray of rays) {
        const list = byCardinal.get(ray.cardinal) ?? [];
        list.push(ray);
        byCardinal.set(ray.cardinal, list);
    }
    const sectors = [];
    for (const cardinal of ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]) {
        const list = byCardinal.get(cardinal);
        if (list === undefined)
            continue;
        const hits = list.filter((ray) => ray.hit);
        const terrain = hits.length >= 7 ? "solid_wall" : hits.length >= 2 ? "_terrain" : "open";
        const notable = distinctNames(hits.map((ray) => ray.block_name));
        sectors.push({ cardinal, terrain, notable_blocks: notable });
    }
    return sectors;
}
function distinctNames(names) {
    const seen = new Set();
    const result = [];
    for (const name of names) {
        if (name === null || seen.has(name))
            continue;
        seen.add(name);
        result.push(name);
    }
    return result;
}
function inferLandmarks(rays) {
    const landmarks = [];
    const villageBlock = (name) => name !== null && (name === "bell" || name === "hay_block" || name === "dirt_path" || name === "composter" ||
        name === "barrel" || name === "lantern" || name.endsWith("_bed") || name.endsWith("_stairs") ||
        name === "oak_fence" || name === "oak_log");
    const village = rays.find((ray) => ray.hit && villageBlock(ray.block_name));
    if (village !== undefined)
        landmarks.push({ kind: "possible_village", cardinal: village.cardinal, confidence: "high", evidence: ["village blocks visible"] });
    const water = rays.find((ray) => ray.hit && ((ray.block_name ?? "") === "water" || (ray.block_name ?? "").startsWith("water")));
    if (water !== undefined)
        landmarks.push({ kind: "water", cardinal: water.cardinal, confidence: "high", evidence: ["water visible"] });
    const light = rays.find((ray) => ray.hit && ((ray.block_name ?? "") === "torch" || (ray.block_name ?? "").endsWith("_torch")));
    if (light !== undefined)
        landmarks.push({ kind: "light_source", cardinal: light.cardinal, confidence: "medium", evidence: ["torch visible"] });
    const cliff = rays.find((ray) => ray.hit && (ray.block_name === "stone" || ray.block_name === "cobblestone") && ray.pitch === -15);
    if (cliff !== undefined)
        landmarks.push({ kind: "cliff", cardinal: cliff.cardinal, confidence: "low", evidence: ["stone at down pitch"] });
    return landmarks;
}
function unknownPreview(started) {
    return {
        state: "unknown",
        path_length: null,
        hops: null,
        estimated_seconds: null,
        blocker: null,
        duration_ms: performance.now() - started,
    };
}
function measurePathLength(path) {
    let total = 0;
    for (let index = 1; index < path.length; index += 1) {
        total += distance(path[index - 1], path[index]);
    }
    return total;
}
function blockVector(block) {
    return {
        x: Math.floor(block.position.x),
        y: Math.floor(block.position.y),
        z: Math.floor(block.position.z),
    };
}
function findBlockingCell(bot, start, target) {
    const dx = target.x - start.x;
    const dz = target.z - start.z;
    const steps = Math.max(1, Math.floor(Math.hypot(dx, dz)));
    const stepX = dx / steps;
    const stepZ = dz / steps;
    const referenceY = Math.floor(target.y);
    for (let index = 1; index <= steps; index += 1) {
        const cellX = Math.floor(start.x + stepX * index);
        const cellZ = Math.floor(start.z + stepZ * index);
        if (cellX === Math.floor(start.x) && cellZ === Math.floor(start.z))
            continue;
        const feet = bot.blockAt(new Vec3(cellX, referenceY, cellZ));
        const head = bot.blockAt(new Vec3(cellX, referenceY + 1, cellZ));
        const floor = bot.blockAt(new Vec3(cellX, referenceY - 1, cellZ));
        if (feet === null || head === null || floor === null)
            continue;
        if (feet.boundingBox !== "empty")
            return { block_name: feet.name, position: blockVector(feet) };
        if (head.boundingBox !== "empty")
            return { block_name: head.name, position: blockVector(head) };
        if (floor.boundingBox === "empty")
            return { block_name: floor.name, position: blockVector(floor) };
    }
    return null;
}
function standable(bot, target) {
    const cell = new Vec3(Math.floor(target.x), Math.floor(target.y), Math.floor(target.z));
    const feet = bot.blockAt(cell);
    const head = bot.blockAt(cell.offset(0, 1, 0));
    const floor = bot.blockAt(cell.offset(0, -1, 0));
    // Water has an empty bounding box, so without the liquid check on feet and
    // head a two-deep water column looks like a place to stand.
    return feet.boundingBox === "empty" && head.boundingBox === "empty"
        && !isLiquid(feet.name) && !isLiquid(head.name)
        && floor.boundingBox !== "empty" && !isLiquid(floor.name);
}
function standableSurfaceNear(bot, x, z, radius) {
    const cellX = Math.floor(x);
    const cellZ = Math.floor(z);
    const found = [];
    for (let ring = 0; ring <= radius; ring += 1) {
        for (let dx = -ring; dx <= ring; dx += 1) {
            for (let dz = -ring; dz <= ring; dz += 1) {
                if (Math.max(Math.abs(dx), Math.abs(dz)) !== ring)
                    continue;
                for (let y = 320; y >= -64; y -= 1) {
                    const target = { x: cellX + dx, y, z: cellZ + dz };
                    if (standable(bot, target)) {
                        found.push({ target, ring });
                        break;
                    }
                }
            }
        }
    }
    found.sort((a, b) => b.target.y - a.target.y || a.ring - b.ring);
    return found[0]?.target ?? null;
}
function standableBelow(bot, x, z, startY) {
    for (let y = Math.floor(startY); y >= -64; y -= 1) {
        const target = { x: Math.floor(x), y, z: Math.floor(z) };
        if (standable(bot, target))
            return target;
    }
    return null;
}
function furthestReachableNode(bot, movements, goal, timeoutMs) {
    let bestPath = null;
    const search = bot.pathfinder.getPathFromTo(movements, bot.entity.position, goal, { timeout: timeoutMs });
    for (const step of search) {
        if (step.result.path.length > (bestPath?.length ?? 0)) {
            bestPath = step.result.path.map((node) => ({ x: node.x, y: node.y, z: node.z }));
        }
        if (step.result.status !== "partial")
            break;
    }
    if (bestPath === null || bestPath.length < 2)
        return null;
    return bestPath[bestPath.length - 1];
}
function openShaftBaseNear(bot, position, radius) {
    const cellX = Math.floor(position.x);
    const cellZ = Math.floor(position.z);
    const startY = Math.floor(position.y) + 1;
    const found = [];
    for (let ring = 0; ring <= radius; ring += 1) {
        for (let dx = -ring; dx <= ring; dx += 1) {
            for (let dz = -ring; dz <= ring; dz += 1) {
                if (Math.max(Math.abs(dx), Math.abs(dz)) !== ring)
                    continue;
                const target = standableBelow(bot, cellX + dx, cellZ + dz, startY);
                if (target === null)
                    continue;
                if (openAirAbove(bot, target, 4))
                    found.push({ target, ring });
            }
        }
    }
    found.sort((a, b) => a.ring - b.ring);
    return found[0]?.target ?? null;
}
function openAirAbove(bot, target, minimum) {
    const cell = new Vec3(Math.floor(target.x), Math.floor(target.y), Math.floor(target.z));
    for (let dy = 1; dy <= minimum; dy += 1) {
        const block = bot.blockAt(cell.offset(0, dy, 0));
        if (block === null || block.boundingBox !== "empty")
            return false;
    }
    // Must have a solid cap somewhere above (not open sky).
    for (let dy = minimum + 1; dy <= minimum + 20; dy += 1) {
        const block = bot.blockAt(cell.offset(0, dy, 0));
        if (block === null)
            return false; // unloaded chunk
        if (block.boundingBox === "block")
            return true; // capped shaft
    }
    return false; // open sky (no cap found within 20 blocks)
}
function isLiquid(name) {
    return name === "water" || name === "lava";
}
function walkDiagnostics(bot, target, cause) {
    const cell = blockCell(target);
    const feet = blockCell(bot.entity.position);
    const name = (p, dy = 0) => bot.blockAt(new Vec3(p.x, p.y + dy, p.z))?.name ?? null;
    return {
        cause, path_status: null, error_name: null, error_message: null,
        target_block: name(cell), target_head_block: name(cell, 1), target_floor_block: name(cell, -1),
        feet_block: name(feet), head_block: name(feet, 1),
    };
}
function targetOffset(position, target) {
    return { x: target.x - position.x, y: target.y - position.y, z: target.z - position.z };
}
function walkSuccess(bot, target, durationMs, diagnostics) {
    const finalPosition = vector(bot.entity.position);
    return {
        ok: true,
        reason: null,
        message: null,
        status: "reached",
        requested: target,
        final_position: finalPosition,
        distance_remaining: distance(finalPosition, target),
        target_offset: targetOffset(finalPosition, target),
        diagnostics,
        hops: 1,
        camera: cameraFromBot(bot),
        duration_ms: durationMs,
    };
}
function walkFailure(bot, target, reason, message, status, hops, durationMs, diagnostics) {
    const finalPosition = vector(bot.entity.position);
    return {
        ok: false,
        reason,
        message,
        status,
        requested: target,
        final_position: finalPosition,
        distance_remaining: distance(finalPosition, target),
        target_offset: targetOffset(finalPosition, target),
        diagnostics: diagnostics ?? walkDiagnostics(bot, target, reason ?? "unknown"),
        hops,
        camera: cameraFromBot(bot),
        duration_ms: durationMs,
    };
}
function activationAction(kind, wasOpen) {
    if (kind === "door")
        return wasOpen ? "door_closed" : "door_opened";
    if (kind === "gate")
        return wasOpen ? "gate_closed" : "gate_opened";
    if (kind === "trapdoor")
        return wasOpen ? "trapdoor_closed" : "trapdoor_opened";
    if (kind === "chest" || kind === "barrel" || kind === "shulker_box" || kind === "hopper")
        return "container_opened";
    if (kind === "furnace")
        return "furnace_opened";
    if (kind === "crafting_table")
        return "crafting_table_opened";
    if (kind === "button")
        return "button_pressed";
    if (kind === "lever")
        return "lever_toggled";
    if (kind === "bed")
        return "bed_entered";
    return "activated";
}
function openedWindow(bot, kind, position) {
    const window = bot.currentWindow;
    if (window === null) {
        return null;
    }
    const windowKind = kind === "furnace" ? "furnace"
        : kind === "crafting_table" ? "crafting_table"
            : kind === "barrel" ? "barrel"
                : kind === "shulker_box" ? "shulker_box" : "chest";
    return {
        kind: windowKind,
        position,
        slots: window.slots.slice(0, window.inventoryStart).map((item, slot) => ({
            slot,
            item: item?.name ?? null,
            count: item?.count ?? 0,
        })),
    };
}
function vector(point) {
    return { x: point.x, y: point.y, z: point.z };
}
class SkillAbortError extends Error {
    constructor(message) {
        super(message);
        this.name = "SkillAbort";
    }
}
class SkillStoppedError extends Error {
    constructor(message) {
        super(message);
        this.name = "SkillStopped";
    }
}
class AccessDeniedError extends Error {
    constructor(message) {
        super(message);
        this.name = "AccessDenied";
    }
}
function detectForbiddenAccess(source) {
    if (/\brequire\s*\(/.test(source))
        return "The skill used require, which is not available.";
    if (/from\s*["']node:/.test(source))
        return "The skill imported a Node.js builtin module.";
    if (/\bchild_process\b/.test(source))
        return "The skill attempted to run a process.";
    if (/\bfetch\s*\(/.test(source))
        return "The skill attempted network access.";
    if (/\bXMLHttpRequest\b|\bWebSocket\b/.test(source))
        return "The skill attempted network access.";
    if (/\bprocess\./.test(source))
        return "The skill accessed the host process.";
    if (/\bimport\s*\(/.test(source))
        return "The skill used a dynamic import.";
    return null;
}
function distance(from, to) {
    return Math.sqrt((to.x - from.x) ** 2 + (to.y - from.y) ** 2 + (to.z - from.z) ** 2);
}
function delay(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
}
function blockCell(point) {
    return {
        x: Math.floor(point.x),
        y: Math.floor(point.y),
        z: Math.floor(point.z),
    };
}
function blockDistance(from, to) {
    return Math.sqrt((to.x - from.x) ** 2 + (to.y - from.y) ** 2 + (to.z - from.z) ** 2);
}
function itemFromStack(stack) {
    if (stack === null) {
        return null;
    }
    return {
        name: stack.name,
        display_name: stack.displayName ?? stack.name,
        count: stack.count ?? 0,
        durability: stack.maxDurability ? stack.maxDurability - (stack.durabilityUsed ?? 0) : null,
        max_durability: stack.maxDurability ?? null,
    };
}
function targetName(entity) {
    return entity.name ?? entity.mobType ?? entity.kind ?? null;
}
function hotbar(bot) {
    const slots = [];
    for (let index = 0; index < 9; index += 1) {
        const item = bot.inventory.slots[bot.inventory.hotbarStart + index];
        slots.push({
            slot: index,
            item: item?.name ?? null,
            count: item?.count ?? 0,
        });
    }
    return slots;
}
function playerStatus(bot) {
    const feet = bot.entity.position;
    const footBlock = bot.blockAt(feet.floored()) ?? null;
    const biomeId = bot.world.getBiome(feet) ?? 0;
    const biome = bot.registry.biomes?.[biomeId]?.name ?? "plains";
    const inWater = footBlock !== null && footBlock.name.startsWith("water");
    return {
        health: bot.health ?? 20,
        max_health: 20,
        food: bot.food ?? 20,
        oxygen: bot.oxygenLevel ?? 20,
        xp_level: bot.experience?.level ?? 0,
        biome,
        dimension: bot.game?.dimension ?? "overworld",
        time_of_day: bot.time?.timeOfDay ?? 0,
        is_day: bot.time?.isDay ?? true,
        is_raining: bot.isRaining ?? false,
        on_ground: bot.entity?.onGround ?? false,
        in_water: inWater,
    };
}
function entityRef(entity, distance) {
    const player = entity.username !== undefined;
    const name = entity.name ?? entity.mobType ?? entity.kind ?? "entity";
    return {
        entity_id: entity.id,
        entity_type: player ? "player" : name,
        display_name: entity.displayName ?? name,
        position: { x: entity.position.x, y: entity.position.y, z: entity.position.z },
        distance,
        health: entity.health ?? null,
        hostile: player ? null : isHostile(name),
    };
}
function isHostile(name) {
    return HOSTILE_MOBS.has(name);
}
const HOSTILE_MOBS = new Set([
    "zombie", "skeleton", "spider", "creeper", "enderman", "drowned",
    "pillager", "witch", "blaze", "ghast", "hoglin", "zombified_piglin",
    "guardian", "elder_guardian", "phantom", "silverfish", "endermite",
    "shulker", "vex", "evoker", "vindicator", "ravager", "stray", "husk",
    "wither_skeleton", "cave_spider", "magma_cube", "slime", "wither",
    "dragon", "zombie_villager", "spider_jockey", "bogged", "breeze",
]);
const VOID_BLOCKS = new Set(["air", "cave_air", "void_air"]);
const FACE_OFFSETS = {
    north: { x: 0, y: 0, z: -1 },
    south: { x: 0, y: 0, z: 1 },
    east: { x: 1, y: 0, z: 0 },
    west: { x: -1, y: 0, z: 0 },
    up: { x: 0, y: 1, z: 0 },
    down: { x: 0, y: -1, z: 0 },
};
function exposedFaces(bot, position) {
    const faces = [];
    for (const direction of Object.keys(FACE_OFFSETS)) {
        const offset = FACE_OFFSETS[direction];
        const neighbor = bot.blockAt(new Vec3(position.x + offset.x, position.y + offset.y, position.z + offset.z));
        if (neighbor !== null && neighbor.boundingBox === "empty") {
            faces.push(direction);
        }
    }
    return faces;
}
function faceFromRay(yaw, pitch) {
    const y = Math.sin(pitch);
    if (y > 0.6) {
        return "down";
    }
    if (y < -0.6) {
        return "up";
    }
    const x = -Math.sin(yaw);
    const z = Math.cos(yaw);
    if (Math.abs(x) > Math.abs(z)) {
        return x > 0 ? "west" : "east";
    }
    return z > 0 ? "north" : "south";
}
function dedupe(blocks) {
    const seen = new Set();
    return blocks.filter((block) => {
        const key = `${block.block_name}|${block.position.x},${block.position.y},${block.position.z}`;
        if (seen.has(key)) {
            return false;
        }
        seen.add(key);
        return true;
    });
}
function aggregateInventory(bot) {
    if (bot === null) {
        return [];
    }
    const items = new Map();
    // Mineflayer items() omits armor and the off-hand slot.
    for (const stack of bot.inventory.slots.slice(5)) {
        if (stack === null) {
            continue;
        }
        const item = items.get(stack.name) ?? {
            name: stack.name,
            display_name: stack.displayName,
            count: 0,
        };
        item.count += stack.count;
        items.set(stack.name, item);
    }
    return [...items.values()].sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}
function cameraFromBot(bot) {
    const feet = bot.entity.position;
    const yaw = normalizeDegrees(bot.entity.yaw * 180 / Math.PI);
    const pitch = bot.entity.pitch * 180 / Math.PI;
    const yawRadians = bot.entity.yaw;
    const pitchRadians = bot.entity.pitch;
    const horizontal = Math.cos(pitchRadians);
    return {
        feet_position: { x: feet.x, y: feet.y, z: feet.z },
        eye_position: { x: feet.x, y: feet.y + 1.62, z: feet.z },
        block_position: { x: Math.floor(feet.x), y: Math.floor(feet.y), z: Math.floor(feet.z) },
        yaw,
        pitch,
        cardinal: cardinalFromYaw(yaw),
        look_vector: {
            x: -Math.sin(yawRadians) * horizontal,
            y: Math.sin(pitchRadians),
            z: Math.cos(yawRadians) * horizontal,
        },
    };
}
function normalizeDegrees(value) {
    return ((value % 360) + 360) % 360;
}
function cardinalFromYaw(yaw) {
    const directions = ["south", "west", "north", "east"];
    return directions[Math.round(yaw / 90) % 4];
}
function stairHazardName(block) {
    if (block === null)
        return "cave";
    const name = block.name;
    if (name === "lava")
        return "lava";
    if (name === "water" || name.startsWith("water"))
        return "water";
    if (name === "bedrock")
        return "bedrock";
    if (name === "gravel")
        return "gravel";
    if (VOID_BLOCKS.has(name))
        return "cave";
    return null;
}
function forwardStep(yawDegrees) {
    switch (cardinalFromYaw(yawDegrees)) {
        case "south": return { x: 0, z: 1 };
        case "north": return { x: 0, z: -1 };
        case "east": return { x: 1, z: 0 };
        case "west": return { x: -1, z: 0 };
    }
}
