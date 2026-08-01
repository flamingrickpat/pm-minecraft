import type { Bot } from "mineflayer";
import { describe, expect, it, vi } from "vitest";
import { Vec3 } from "vec3";
import { buildLLMState } from "../src/state/llmState.js";

describe("buildLLMState", () => {
  it("reports whether the held item can harvest each observed block", () => {
    const stone = {
      name: "stone",
      position: new Vec3(1, 64, 0),
      canHarvest: vi.fn(() => false),
      harvestTools: { "270": true }
    };
    const bot = {
      username: "spamuel_test",
      version: "1.19.4",
      entity: {
        position: new Vec3(0, 64, 0),
        velocity: new Vec3(0, 0, 0),
        yaw: 0,
        pitch: 0,
        onGround: true
      },
      inventory: { slots: new Array(45).fill(null) },
      heldItem: {
        name: "oak_pressure_plate",
        count: 1,
        type: 123
      },
      quickBarSlot: 0,
      registry: {
        items: { 270: { name: "wooden_pickaxe" } }
      },
      entities: {},
      canSeeBlock: vi.fn(() => true),
      blockAt: vi.fn((position: Vec3) => (
        position.equals(stone.position)
          ? stone
          : { name: "air", position }
      ))
    } as unknown as Bot;

    const state = buildLLMState(bot, { nearbyBlockRadius: 1 });

    expect(state.surroundings.nearbyBlocks).toEqual([
      {
        name: "stone",
        count: 1,
        nearest: { x: 1, y: 64, z: 0 },
        distance: 1.66,
        canHarvestWithHeldItem: false,
        harvestToolOptions: ["wooden_pickaxe"]
      }
    ]);
    expect(stone.canHarvest).toHaveBeenCalledWith(123);
    expect(state.surroundings.localAirspace).toMatchObject({
      scanRadius: 1,
      clearanceBlocksAboveHead: 1,
      horizontalOpenings: expect.arrayContaining([
        {
          direction: "east",
          delta: { x: 1, z: 0 },
          openBlocks: 0,
          firstBlockedBy: { feet: "solid", head: "open" }
        },
        {
          direction: "south",
          delta: { x: 0, z: 1 },
          openBlocks: 1,
          firstBlockedBy: null
        }
      ])
    });
  });

  it("summarizes reachable standable waypoints without prescribing a route", () => {
    const corridor = new Set([
      "0,64,0",
      "1,64,0",
      "2,64,0",
      "3,64,0"
    ]);
    const bot = {
      username: "spamuel_test",
      version: "1.19.4",
      entity: {
        position: new Vec3(0, 64, 0),
        velocity: new Vec3(0, 0, 0),
        yaw: 0,
        pitch: 0,
        onGround: true
      },
      inventory: { slots: new Array(45).fill(null) },
      heldItem: null,
      quickBarSlot: 0,
      registry: { items: {} },
      entities: {},
      canSeeBlock: vi.fn(() => true),
      blockAt: vi.fn((position: Vec3) => {
        const key = `${position.x},${position.y},${position.z}`;
        const isCorridorAir = (
          corridor.has(key)
          || corridor.has(`${position.x},${position.y - 1},${position.z}`)
        );
        const isRaisedClearance = (
          position.x === 2
          && position.z === 0
          && [66, 67].includes(position.y)
        );
        const isSupport = (
          position.y === 63
          && position.z === 0
          && position.x >= 0
          && position.x <= 3
        );
        if (isCorridorAir || isRaisedClearance) {
          return { name: "air", position };
        }
        return {
          name: isSupport ? "stone" : "stone",
          position
        };
      })
    } as unknown as Bot;

    const state = buildLLMState(bot, { nearbyBlockRadius: 3 });

    expect(state.surroundings.localAirspace.navigationSummary).toMatchObject({
      reachableStandableCells: 4,
      elevationRange: {
        minimumDelta: 0,
        maximumDelta: 0
      },
      highestWaypoint: {
        position: { x: 2, y: 64, z: 0 }
      },
      maxClearanceWaypoint: {
        position: { x: 2, y: 64, z: 0 },
        clearanceBlocksAboveHead: 2
      },
      furthestWaypoint: {
        position: { x: 3, y: 64, z: 0 }
      },
      frontierWaypoints: [
        expect.objectContaining({
          position: { x: 3, y: 64, z: 0 }
        })
      ]
    });
  });
});
