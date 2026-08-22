import { describe, it, expect } from "vitest";
import { reconnectDelayMs } from "../reconnectPolicy.js";

describe("reconnectDelayMs", () => {
  it("starts at the base delay for the first failure", () => {
    expect(reconnectDelayMs(0)).toBe(1000);
    expect(reconnectDelayMs(1)).toBe(2000);
  });

  it("doubles with each additional failure", () => {
    expect(reconnectDelayMs(2)).toBe(4000);
    expect(reconnectDelayMs(3)).toBe(8000);
    expect(reconnectDelayMs(4)).toBe(15000);
  });

  it("caps at the maximum delay", () => {
    expect(reconnectDelayMs(10)).toBe(15000);
    expect(reconnectDelayMs(100)).toBe(15000);
    expect(reconnectDelayMs(4)).toBe(15_000);
  });

  it("clamps at a custom max", () => {
    expect(reconnectDelayMs(1, 500, 3000)).toBe(1000);
    expect(reconnectDelayMs(3, 500, 3000)).toBe(3000);
  });

  it("never returns a negative delay for bad inputs", () => {
    expect(reconnectDelayMs(0, -5, -1)).toBe(0);
    expect(reconnectDelayMs(2, 0, 0)).toBe(0);
  });
});
