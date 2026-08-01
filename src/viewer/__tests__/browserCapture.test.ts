import { describe, it, expect } from "vitest";
import {
  assessFrameQuality,
  BROWSER_EXTENSIONS_ENABLED,
  BROWSER_LAUNCH_ARGUMENTS,
  type FrameQualityAssessment,
} from "../browserCapture.js";

// ---------------------------------------------------------------------------
// Helpers: generate test PNGs using the canvas package
// ---------------------------------------------------------------------------

async function createSolidColorPng(
  r: number,
  g: number,
  b: number,
  width: number,
  height: number
): Promise<Buffer> {
  const { createCanvas } = await import("canvas");
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = `rgb(${r},${g},${b})`;
  ctx.fillRect(0, 0, width, height);
  return Buffer.from(canvas.toBuffer("image/png"));
}

/**
 * Create a terrain-like PNG with enough pixel-level detail to exceed the
 * minimum byte size. Adds noise, textures, and varied edges to simulate
 * real prismarine-viewer output (~64KB for real terrain).
 */
async function createTerrainPng(width: number, height: number): Promise<Buffer> {
  const { createCanvas } = await import("canvas");
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext("2d");

  // Sky gradient (not uniform — real renders have gradients)
  const skyGrad = ctx.createLinearGradient(0, 0, 0, height * 0.4);
  skyGrad.addColorStop(0, "rgb(100,180,220)");
  skyGrad.addColorStop(1, "rgb(173,216,230)");
  ctx.fillStyle = skyGrad;
  ctx.fillRect(0, 0, width, height * 0.4);

  // Ground with varied terrain blocks at pixel level for high entropy
  const terrainColors = [
    [139, 69, 19], [101, 67, 33], [34, 139, 34], [46, 139, 87],
    [105, 105, 105], [128, 128, 128], [160, 82, 45], [210, 105, 30],
    [85, 107, 47], [60, 179, 113], [205, 133, 63], [244, 164, 96],
    [188, 143, 143], [119, 136, 153], [112, 128, 144],
  ];

  // Draw terrain with per-pixel variation (simulates Minecraft texture noise)
  const imgData = ctx.createImageData(width, height);
  const data = imgData.data;
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      if (y < height * 0.4) {
        // Sky pixels (gradient already drawn, skip)
        continue;
      }
      // Pick a base color based on position
      const colorIdx = ((x * 7 + y * 13 + (x * y) % 1000) % terrainColors.length);
      const base = terrainColors[colorIdx];
      // Add per-pixel noise (simulates texture detail)
      const noise = ((x * 31 + y * 17 + x * y) % 30) - 15;
      data[idx] = Math.max(0, Math.min(255, base[0] + noise));
      data[idx + 1] = Math.max(0, Math.min(255, base[1] + noise));
      data[idx + 2] = Math.max(0, Math.min(255, base[2] + noise));
      data[idx + 3] = 255;
    }
  }
  // Put the pixel data on top of the sky gradient
  ctx.putImageData(imgData, 0, 0);

  // Add some "entity" pixels (bot character)
  ctx.fillStyle = "#0000FF";
  ctx.fillRect(width / 2 - 5, height * 0.35, 10, 20);
  ctx.fillStyle = "#FF0000";
  ctx.fillRect(width / 2 - 3, height * 0.35, 6, 6);

  return Buffer.from(canvas.toBuffer("image/png"));
}

/**
 * Create a half-sky/half-terrain PNG with enough pixel-level detail to exceed min byte size.
 */
async function createHalfSkyHalfTerrainPng(
  width: number,
  height: number
): Promise<Buffer> {
  const { createCanvas } = await import("canvas");
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext("2d");

  const terrainColors = [
    [139, 69, 19], [101, 67, 33], [34, 139, 34], [105, 105, 105],
    [128, 128, 128], [160, 82, 45], [210, 105, 30], [85, 107, 47],
    [205, 133, 63], [119, 136, 153],
  ];

  const imgData = ctx.createImageData(width, height);
  const data = imgData.data;
  const halfY = Math.floor(height / 2);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      if (y < halfY) {
        // Top half: exact background color
        data[idx] = 173;
        data[idx + 1] = 216;
        data[idx + 2] = 230;
      } else {
        // Bottom half: terrain with high-frequency per-pixel noise
        const colorIdx = ((x * 7 + y * 13 + (x * y) % 700 + x % 3 + y % 5) % terrainColors.length);
        const base = terrainColors[colorIdx];
        const n1 = ((x * 31 + y * 17) % 25) - 12;
        const n2 = ((x * 17 + y * 23 + 7) % 19) - 9;
        data[idx] = Math.max(0, Math.min(255, base[0] + n1 + n2));
        data[idx + 1] = Math.max(0, Math.min(255, base[1] + n1 - n2));
        data[idx + 2] = Math.max(0, Math.min(255, base[2] + n2));
      }
      data[idx + 3] = 255;
    }
  }
  ctx.putImageData(imgData, 0, 0);

  return Buffer.from(canvas.toBuffer("image/png"));
}

async function createLowEntropyStoneViewPng(width: number, height: number): Promise<Buffer> {
  const { createCanvas } = await import("canvas");
  const canvas = createCanvas(width, height);
  const ctx = canvas.getContext("2d");
  const blockSize = 64;

  for (let y = 0; y < height; y += blockSize) {
    for (let x = 0; x < width; x += blockSize) {
      const shade = 115 + ((Math.floor(x / blockSize) * 13 + Math.floor(y / blockSize) * 17) % 45);
      ctx.fillStyle = `rgb(${shade},${shade},${shade})`;
      ctx.fillRect(x, y, blockSize, blockSize);
    }
  }

  return Buffer.from(canvas.toBuffer("image/png"));
}

// ---------------------------------------------------------------------------
// Tests: frame quality gate
// ---------------------------------------------------------------------------

describe("assessFrameQuality", () => {
  const TEST_WIDTH = 854;
  const TEST_HEIGHT = 480;

  it("rejects a solid lightblue (173,216,230) PNG as unusable", async () => {
    const png = await createSolidColorPng(173, 216, 230, TEST_WIDTH, TEST_HEIGHT);
    const result = await assessFrameQuality(png, TEST_WIDTH, TEST_HEIGHT);

    expect(result.usable).toBe(false);
    // Solid color PNGs are caught by pixel variation check (low distinct colors, low luminance range)
    expect(result.distinctColorCount).toBeLessThan(result.minimumDistinctColors);
  });

  it("rejects a near-lightblue PNG (within tolerance) as unusable", async () => {
    // Slight variation within tolerance (±10)
    const png = await createSolidColorPng(178, 220, 235, TEST_WIDTH, TEST_HEIGHT);
    const result = await assessFrameQuality(png, TEST_WIDTH, TEST_HEIGHT);

    expect(result.usable).toBe(false);
  });

  it("rejects a very small PNG", async () => {
    // 1x1 pixel PNG is tiny
    const tinyPng = await createSolidColorPng(173, 216, 230, 1, 1);
    const result = await assessFrameQuality(tinyPng, 1, 1);

    expect(result.usable).toBe(false);
    expect(result.byteSize).toBeLessThan(1_000);
  });

  it("accepts a full-size bright block view even when PNG compression is below byte threshold", async () => {
    const png = await createLowEntropyStoneViewPng(TEST_WIDTH, TEST_HEIGHT);
    const result = await assessFrameQuality(png, TEST_WIDTH, TEST_HEIGHT);

    // Low-entropy stone view has meaningful pixel variation (distinct colors, luminance range)
    // With the lowered byte-size threshold, it passes via the standard quality gate.
    expect(result.usable).toBe(true);
    expect(result.distinctColorCount).toBeGreaterThanOrEqual(result.minimumDistinctColors);
    expect(result.luminanceRange).toBeGreaterThanOrEqual(result.minimumLuminanceRange);
    expect(result.dominantColorFraction).toBeLessThanOrEqual(result.maximumDominantColorFraction);
  });

  it("accepts a terrain-like PNG with mixed colors and pixel noise", async () => {
    const png = await createTerrainPng(TEST_WIDTH, TEST_HEIGHT);
    const result = await assessFrameQuality(png, TEST_WIDTH, TEST_HEIGHT);

    expect(result.usable).toBe(true);
    expect(result.backgroundFraction).toBeLessThanOrEqual(0.95);
    expect(result.byteSize).toBeGreaterThan(0);
  });

  it("accepts a mostly-non-background PNG even with some sky pixels", async () => {
    const png = await createHalfSkyHalfTerrainPng(TEST_WIDTH, TEST_HEIGHT);
    const result = await assessFrameQuality(png, TEST_WIDTH, TEST_HEIGHT);

    // ~50% background is well under the 95% threshold
    expect(result.usable).toBe(true);
    expect(result.backgroundFraction).toBeGreaterThan(0.3);
    expect(result.backgroundFraction).toBeLessThan(0.6);
  });

  it("reports correct byte size in assessment", async () => {
    const png = await createSolidColorPng(173, 216, 230, TEST_WIDTH, TEST_HEIGHT);
    const result = await assessFrameQuality(png, TEST_WIDTH, TEST_HEIGHT);

    expect(result.byteSize).toBe(png.length);
  });

  it("reports background fraction as a value between 0 and 1", async () => {
    const png = await createTerrainPng(TEST_WIDTH, TEST_HEIGHT);
    const result = await assessFrameQuality(png, TEST_WIDTH, TEST_HEIGHT);

    expect(result.backgroundFraction).toBeGreaterThanOrEqual(0);
    expect(result.backgroundFraction).toBeLessThanOrEqual(1);
  });

  it("returns reviewable threshold evidence with each quality assessment", async () => {
    const png = await createTerrainPng(TEST_WIDTH, TEST_HEIGHT);
    const result = await assessFrameQuality(png, TEST_WIDTH, TEST_HEIGHT);

    expect(result).toMatchObject({
      usable: true,
      minimumByteSize: 1_000,
      maximumBackgroundFraction: 0.95,
      maximumDarkFraction: 0.995,
      minimumDistinctColors: 4,
      minimumLuminanceRange: 18,
      maximumDominantColorFraction: 0.85,
    });
    expect(result.darkFraction).toBeGreaterThanOrEqual(0);
    expect(result.darkFraction).toBeLessThanOrEqual(1);
    expect(result.distinctColorCount).toBeGreaterThan(0);
    expect(result.luminanceRange).toBeGreaterThanOrEqual(0);
    expect(result.dominantColorFraction).toBeGreaterThanOrEqual(0);
    expect(result.dominantColorFraction).toBeLessThanOrEqual(1);
  });
});

// ---------------------------------------------------------------------------
// Tests: module exports
// ---------------------------------------------------------------------------

describe("browserCapture module", () => {
  it("launches headless Brave with extensions enabled", () => {
    expect(BROWSER_EXTENSIONS_ENABLED).toBe(true);
    expect(BROWSER_LAUNCH_ARGUMENTS).toContain("--enable-extensions");
  });

  it("exports createBrowserFrameImageCapture as a function", async () => {
    const mod = await import("../browserCapture.js");
    expect(typeof mod.createBrowserFrameImageCapture).toBe("function");
  });

  it("exports assessFrameQuality as a function", async () => {
    const mod = await import("../browserCapture.js");
    expect(typeof mod.assessFrameQuality).toBe("function");
  });
});
