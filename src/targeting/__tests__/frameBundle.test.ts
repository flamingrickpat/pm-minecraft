import { describe, it, expect } from "vitest";
import { Vec3 } from "vec3";
import type { Bot } from "mineflayer";
import { botHudLines } from "../frameBundle.js";

function fakeBot(overrides: {
  x?: number;
  y?: number;
  z?: number;
  yaw?: number;
  pitch?: number;
  health?: number;
  food?: number;
  timeOfDay?: number;
}): Bot {
  return {
    entity: {
      position: new Vec3(overrides.x ?? 70.5, overrides.y ?? 64.02, overrides.z ?? -215.34),
      yaw: overrides.yaw ?? 0,
      pitch: overrides.pitch ?? 0
    },
    health: overrides.health ?? 16,
    food: overrides.food ?? 18,
    time: { timeOfDay: overrides.timeOfDay ?? 6000 },
    world: { getBiome: () => 1 },
    registry: { biomes: { 1: { name: "savanna" } } }
  } as unknown as Bot;
}

describe("botHudLines", () => {
  it("renders position, heading, yaw/pitch, biome, day, and vitals", () => {
    const lines = botHudLines(fakeBot({}));
    expect(lines).toHaveLength(2);
    expect(lines[0]).toContain("pos (70.5, 64, -215.3)");
    expect(lines[0]).toContain("heading 0° N");
    expect(lines[0]).toContain("yaw 0° pitch 0°");
    expect(lines[1]).toContain("biome savanna");
    expect(lines[1]).toContain("day");
    expect(lines[1]).toContain("hp 16");
    expect(lines[1]).toContain("food 18");
  });

  it("maps mineflayer yaw 90deg (facing west) to compass heading 270 W", () => {
    const lines = botHudLines(fakeBot({ yaw: Math.PI / 2 }));
    expect(lines[0]).toContain("heading 270° W");
    expect(lines[0]).toContain("yaw 90°");
  });

  it("maps mineflayer yaw 180deg (facing south) to compass heading 180 S", () => {
    const lines = botHudLines(fakeBot({ yaw: Math.PI }));
    expect(lines[0]).toContain("heading 180° S");
  });

  it("wraps negative and >360 yaw values into [0, 360)", () => {
    const lines = botHudLines(fakeBot({ yaw: -Math.PI / 4 }));
    expect(lines[0]).toContain("yaw 315°");
    expect(lines[0]).toContain("heading 45° NE");
  });

  it("reports night for late-day times", () => {
    const lines = botHudLines(fakeBot({ timeOfDay: 14000 }));
    expect(lines[1]).toContain("night");
  });

  it("returns no lines without an entity", () => {
    expect(botHudLines({} as Bot)).toEqual([]);
  });
});
