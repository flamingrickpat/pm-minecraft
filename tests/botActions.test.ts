import { describe, expect, it, vi } from "vitest";
import { Vec3 } from "vec3";
import { configureNavigationMovements, createPhysicalCommandActions, summarizeNavigation } from "../src/bot/actions.js";

describe("navigation diagnostics", () => {
  it("reports route shape and planned world modifications", () => {
    const report = summarizeNavigation({
      status: "success",
      path: [
        { x: 1, y: 65, z: 0, toBreak: [{}] },
        { x: 2, y: 64, z: 0, toPlace: [{}, {}] }
      ]
    }, { x: 0, y: 64, z: 0 }, { x: 2, y: 64, z: 0 }, false);

    expect(report).toMatchObject({
      profile: "adaptive",
      pathStatus: "success",
      pathNodes: 2,
      ascents: 1,
      drops: 1,
      blocksToBreak: 1,
      blocksToPlace: 2,
      stalled: false
    });
  });

  it("explains when a high target needs a deliberate construction strategy", () => {
    const report = summarizeNavigation(
      { status: "noPath", path: [] },
      { x: 0, y: 64, z: 0 },
      { x: 4, y: 70, z: 0 },
      false
    );
    expect(report.diagnosis).toContain("staircase or tunnel");
  });

  it("labels an exhausted search as likely unreachable or out of loaded chunks", () => {
    const report = summarizeNavigation(
      { status: "timeout", path: [] },
      { x: 0, y: 64, z: 0 },
      { x: 40, y: 64, z: 40 },
      false
    );
    expect(report.diagnosis).toContain("unreachable");
  });

  it("labels a stalled bot as likely unreachable or outside the loaded world", () => {
    const report = summarizeNavigation(
      { status: "partial", path: [], toBreak: [], toPlace: [] } as never,
      { x: 0, y: 64, z: 0 },
      { x: 16, y: 64, z: 16 },
      true
    );
    expect(report.stalled).toBe(true);
    expect(report.diagnosis).toContain("unreachable");
  });

  it("reports walk-only limits without suggesting destructive recovery", () => {
    const report = summarizeNavigation(
      { status: "noPath", path: [] },
      { x: 0, y: 64, z: 0 },
      { x: 0, y: 66, z: 0 },
      false,
      "walk_only"
    );

    expect(report).toMatchObject({ profile: "walk_only" });
    expect(report.diagnosis).toContain("no existing ascent");
    expect(report.diagnosis).not.toContain("staircase");
  });

  it("configures walk-only movement without destructive pathfinder capabilities", () => {
    const movements = {
      canDig: true,
      allow1by1towers: true,
      allowParkour: true,
      scafoldingBlocks: [1, 2],
      maxDropDown: 4,
      infiniteLiquidDropdownDistance: true
    };

    const configured = configureNavigationMovements(movements as never, "walk_only");

    expect(configured).toMatchObject({
      canDig: false,
      allow1by1towers: false,
      allowParkour: false,
      scafoldingBlocks: [],
      maxDropDown: 1,
      infiniteLiquidDropdownDistance: false
    });
  });

  it("preserves adaptive movement defaults", () => {
    const movements = {
      canDig: true,
      allow1by1towers: true,
      allowParkour: true,
      scafoldingBlocks: [1, 2],
      maxDropDown: 4,
      infiniteLiquidDropdownDistance: true
    };

    expect(configureNavigationMovements(movements as never, "adaptive")).toBe(movements);
    expect(movements).toEqual({
      canDig: true,
      allow1by1towers: true,
      allowParkour: true,
      scafoldingBlocks: [1, 2],
      maxDropDown: 4,
      infiniteLiquidDropdownDistance: true
    });
  });
});

describe("physical bot actions", () => {
  it("finds a block only when the head-origin visibility ray is clear, regardless of rotation", async () => {
    const target = block("oak_log", new Vec3(3, 64, 2));
    const findBlock = vi.fn((options: { useExtraInfo?: (candidate: ReturnType<typeof block>) => boolean }) =>
      options.useExtraInfo?.(target) ? target : null
    );
    const bot = fakeBot({
      heldItem: null,
      blocks: {},
      canSeeBlock: () => true,
      findBlock,
      registry: { blocksByName: { oak_log: { id: 17 } } },
      yaw: Math.PI
    });

    const result = await createPhysicalCommandActions(bot).findBlock({ blockName: "oak_log", maxDistance: 48 });

    expect(result).toMatchObject({ ok: true, data: { blockName: "oak_log" } });
    expect(findBlock).toHaveBeenCalledWith(expect.objectContaining({ useExtraInfo: expect.any(Function) }));
  });

  it("rejects mining a loaded but head-ray-hidden block beyond tunnel reach", async () => {
    // Outside the 3-block tunnel-ignore distance, the head-line-of-sight gate
    // still applies.
    const target = block("iron_ore", new Vec3(6, 96, -6));
    const dig = vi.fn(async () => undefined);
    const bot = fakeBot({
      heldItem: null,
      blocks: { "6,96,-6": target },
      canSeeBlock: () => false,
      dig
    });

    const result = await createPhysicalCommandActions(bot).mineBlock({
      block: { x: 6, y: 96, z: -6 },
      walkIntoRange: false
    });

    expect(result).toMatchObject({ ok: false, reason: "block_not_visible" });
    expect(dig).not.toHaveBeenCalled();
  });

  it("mines a head-ray-hidden block within the 3-block tunnel-ignore distance", async () => {
    // A 1-wide shaft's adjacent feet-level block is not visible from the head;
    // within the tunnel distance the gate is skipped so the bot can tunnel.
    const target = block("stone", new Vec3(0, 94, -3));
    const dig = vi.fn(async () => undefined);
    const bot = fakeBot({
      heldItem: null,
      blocks: { "0,94,-3": target },
      canSeeBlock: () => false,
      dig
    });

    const result = await createPhysicalCommandActions(bot).mineBlock({
      block: { x: 0, y: 94, z: -3 },
      walkIntoRange: false
    });

    expect(result).toMatchObject({ ok: true });
    expect(dig).toHaveBeenCalledTimes(1);
  });

  it("refuses to destroy a block when the held item cannot harvest it", async () => {
    const position = new Vec3(0, 94, -2);
    const target = {
      ...block("stone", position),
      canHarvest: vi.fn(() => false)
    };
    const blocks = { "0,94,-2": target };
    const dig = vi.fn(async () => {
      blocks["0,94,-2"] = block("air", position) as typeof target;
    });
    const bot = fakeBot({
      heldItem: { name: "crafting_table", count: 1, type: 58 },
      blocks,
      dig
    });

    const result = await createPhysicalCommandActions(bot).mineBlock({
      block: { x: 0, y: 94, z: -2 },
      walkIntoRange: false
    });

    expect(result).toMatchObject({
      ok: false,
      reason: "unharvestable",
      data: {
        blockName: "stone",
        heldItemBefore: { name: "crafting_table", count: 1 },
        canHarvest: false
      }
    });
    expect(target.canHarvest).toHaveBeenCalledWith(58);
    expect(dig).not.toHaveBeenCalled();
  });

  it("inspects target harvestability without mutating the block", async () => {
    const position = new Vec3(0, 94, -2);
    const target = {
      ...block("gravel", position),
      canHarvest: vi.fn(() => true)
    };
    const bot = fakeBot({
      heldItem: { name: "oak_pressure_plate", count: 1, type: 72 },
      blocks: { "0,94,-2": target }
    });

    const result = await createPhysicalCommandActions(bot).inspectBlock({
      x: 0,
      y: 94,
      z: -2
    });

    expect(result).toMatchObject({
      ok: true,
      data: {
        blockName: "gravel",
        heldItem: { name: "oak_pressure_plate", count: 1 },
        canHarvestWithHeldItem: true
      }
    });
    expect(target.canHarvest).toHaveBeenCalledWith(72);
  });

  it("reports place-block timeout as failed when placement is not verified", async () => {
    const reference = block("stone", new Vec3(-1, 94, -3));
    const bot = fakeBot({
      heldItem: { name: "dirt", count: 1 },
      blocks: {
        "-1,94,-3": reference,
        "-1,95,-3": block("air", new Vec3(-1, 95, -3))
      },
      placeBlock: vi.fn(async () => {
        throw new Error("Event blockUpdate did not fire within timeout");
      })
    });

    const result = await createPhysicalCommandActions(bot).placeBlock({
      referenceBlock: { x: -1, y: 94, z: -3 },
      face: { x: 0, y: 1, z: 0 },
      walkIntoRange: false
    });

    expect(result).toMatchObject({
      ok: false,
      reason: "place_unverified"
    });
  });

  it("jump-place holds jump while placing and clears it afterward", async () => {
    const reference = block("stone", new Vec3(-1, 94, -3));
    const placed = block("dirt", new Vec3(-1, 95, -3));
    const setControlState = vi.fn();
    const blocks = {
      "-1,94,-3": reference,
      "-1,95,-3": block("air", new Vec3(-1, 95, -3))
    };
    const placeBlock = vi.fn(async () => {
      blocks["-1,95,-3"] = placed;
    });
    const bot = fakeBot({
      heldItem: { name: "dirt", count: 1 },
      blocks,
      placeBlock,
      setControlState
    });

    const result = await createPhysicalCommandActions(bot).jumpPlaceBlock({
      referenceBlock: { x: -1, y: 94, z: -3 },
      face: { x: 0, y: 1, z: 0 },
      walkIntoRange: false
    });

    expect(result).toMatchObject({
      ok: true,
      data: { verified: true }
    });
    expect(setControlState).toHaveBeenCalledWith("jump", true);
    expect(setControlState).toHaveBeenLastCalledWith("jump", false);
    expect(placeBlock).toHaveBeenCalledWith(reference, new Vec3(0, 1, 0));
  });

  it("rejects jump-placement when the target is already occupied", async () => {
    const reference = block("dirt", new Vec3(54, 69, -23));
    const placeBlock = vi.fn(async () => undefined);
    const bot = fakeBot({
      heldItem: { name: "dirt", count: 32 },
      blocks: {
        "54,69,-23": reference,
        "54,68,-23": block("dirt", new Vec3(54, 68, -23))
      },
      placeBlock
    });

    const result = await createPhysicalCommandActions(bot).jumpPlaceBlock({
      referenceBlock: { x: 54, y: 69, z: -23 },
      face: { x: 0, y: -1, z: 0 },
      walkIntoRange: false
    });

    expect(result).toMatchObject({ ok: false, reason: "place_target_occupied" });
    expect(placeBlock).not.toHaveBeenCalled();
  });

  it("pillars up using the held block without requiring coordinates", async () => {
    const reference = block("stone", new Vec3(-1, 94, -3));
    const placed = block("dirt", new Vec3(-1, 95, -3));
    const blocks = {
      "-1,94,-3": reference,
      "-1,95,-3": block("air", new Vec3(-1, 95, -3))
    };
    const placeBlockWithOptions = vi.fn(async () => {
      blocks["-1,95,-3"] = placed;
    });
    const bot = fakeBot({
      heldItem: { name: "dirt", count: 3 },
      blocks,
      placeBlockWithOptions
    });

    const result = await createPhysicalCommandActions(bot).pillarUp();

    expect(result).toMatchObject({
      ok: true,
      message: "Pillared up one block and landed.",
      data: {
        attempts: 1,
        referenceBlock: { x: -1, y: 94, z: -3 },
        placedBlock: { x: -1, y: 95, z: -3 },
        placedBlockName: "dirt"
      }
    });
    expect(placeBlockWithOptions).toHaveBeenCalledWith(
      reference,
      new Vec3(0, 1, 0),
      {
        forceLook: "ignore",
        swingArm: "right"
      }
    );
  });

  it("retries pillar placement internally after an unverified jump", async () => {
    const reference = block("stone", new Vec3(-1, 94, -3));
    const blocks = {
      "-1,94,-3": reference,
      "-1,95,-3": block("air", new Vec3(-1, 95, -3))
    };
    const placeBlock = vi.fn(async () => {
      if (placeBlock.mock.calls.length === 2) {
        blocks["-1,95,-3"] = block("cobblestone", new Vec3(-1, 95, -3));
      }
    });
    const bot = fakeBot({ heldItem: { name: "cobblestone", count: 3 }, blocks, placeBlock });

    const result = await createPhysicalCommandActions(bot).pillarUp();

    expect(result).toMatchObject({ ok: true, data: { attempts: 2, placedBlockName: "cobblestone" } });
    expect(placeBlock).toHaveBeenCalledTimes(2);
  });

  it("rejects pillar placement when the landing headroom is occupied", async () => {
    const reference = block("stone", new Vec3(-1, 94, -3));
    const placeBlock = vi.fn(async () => undefined);
    const bot = fakeBot({
      heldItem: { name: "dirt", count: 3 },
      blocks: {
        "-1,94,-3": reference,
        "-1,95,-3": block("air", new Vec3(-1, 95, -3)),
        "-1,97,-3": block("stone", new Vec3(-1, 97, -3))
      },
      placeBlock
    });

    const result = await createPhysicalCommandActions(bot).pillarUp();

    expect(result).toMatchObject({
      ok: false,
      reason: "pillar_headroom_blocked",
      data: {
        blockedHeadPosition: { x: -1, y: 97, z: -3 },
        blockedBy: "stone"
      }
    });
    expect(placeBlock).not.toHaveBeenCalled();
  });
});

function fakeBot(options: {
  heldItem: { name: string; count: number; type?: number } | null;
  blocks: Record<string, ReturnType<typeof block>>;
  placeBlock?: ReturnType<typeof vi.fn>;
  placeBlockWithOptions?: ReturnType<typeof vi.fn>;
  dig?: ReturnType<typeof vi.fn>;
  canSeeBlock?: (candidate: ReturnType<typeof block>) => boolean;
  findBlock?: ReturnType<typeof vi.fn>;
  registry?: { blocksByName: Record<string, { id: number; boundingBox?: string }> };
  yaw?: number;
  setControlState?: ReturnType<typeof vi.fn>;
}) {
  return {
    entity: {
      position: new Vec3(-0.5, 95, -2.5),
      yaw: options.yaw ?? 0,
      pitch: 0,
      eyeHeight: 1.62
    },
    heldItem: options.heldItem,
    blockAt: (position: Vec3) => options.blocks[key(position)] ?? null,
    canDigBlock: () => true,
    canSeeBlock: options.canSeeBlock ?? (() => true),
    findBlock: options.findBlock,
    registry: options.registry ?? {
      blocksByName: {
        dirt: { id: 1, boundingBox: "block" },
        cobblestone: { id: 2, boundingBox: "block" },
        stone: { id: 3, boundingBox: "block" }
      }
    },
    lookAt: vi.fn(async () => undefined),
    dig: options.dig ?? vi.fn(async () => undefined),
    placeBlock: options.placeBlock ?? vi.fn(async () => undefined),
    _placeBlockWithOptions: options.placeBlockWithOptions,
    setControlState: options.setControlState ?? vi.fn()
  } as never;
}

function block(name: string, position: Vec3) {
  return {
    name,
    type: name === "air" ? 0 : 1,
    position,
    diggable: name !== "air",
    boundingBox: name === "air" ? "empty" : "block",
    displayName: name
  };
}

function key(position: Vec3): string {
  return `${Math.floor(position.x)},${Math.floor(position.y)},${Math.floor(position.z)}`;
}
