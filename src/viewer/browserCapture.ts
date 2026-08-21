import { existsSync } from "node:fs";
import type { CapturedPng, FrameQualityAssessment } from "../targeting/frameBundle.js";
export type { FrameQualityAssessment } from "../targeting/frameBundle.js";

/**
 * prismarine-viewer runs in a browser; drive an installed browser to capture its rendered page as PNG bytes.
 *
 * @remarks
 * archetype: service-provider
 * owns: launching a headless browser, opening the viewer URL, reading canvas dimensions,
 *       frame quality gating/metrics, and returning PNG bytes only when the image is usable.
 * not own: frame ids, bot pose metadata, world grounding, or target ray resolution.
 * fails when: no supported browser executable exists, the viewer page cannot load,
 *             screenshot capture throws, or the captured frame is unusable (solid background).
 * domain: this keeps screenshots tied to the real prismarine-viewer web surface instead of generated image data.
 * invariant: returned bytes come from browser screenshot capture of the supplied viewer URL
 *            and carry quality evidence proving the image is not tiny, black, or mostly viewer background.
 */
export interface BrowserFrameImageCaptureOptions {
  width?: number;
  height?: number;
  executablePath?: string;
  maxRetries?: number;
  retryDelayMs?: number;
  deviceScaleFactor?: number;
  fovDegrees?: number;
}

export interface BrowserFrameCaptureInput {
  url: string;
  /** HUD text lines rendered into the top-left of the captured frame (pose,
   *  biome, vitals). Omit to capture without the HUD strip. */
  hud?: string[];
}

export interface BrowserFrameCapture {
  /** Quality-gated capture: retries until the frame shows usable terrain. */
  capture(input: BrowserFrameCaptureInput): Promise<CapturedPng>;
  /** Single-shot capture without retries; returns the frame regardless of quality. */
  captureRaw(input: BrowserFrameCaptureInput): Promise<CapturedPng>;
  close(): Promise<void>;
}

// prismarine-viewer default background color (lightblue sky)
const DEFAULT_BG_R = 173;
const DEFAULT_BG_G = 216;
const DEFAULT_BG_B = 230;
const BG_COLOR_TOLERANCE = 15; // allow some variance for near-background pixels

// Minimum acceptable PNG size for 854x480 capture.
// Removed the 10_000-byte hard limit: cave scenes with bright rendering
// produce legitimate terrain that can compress below this threshold.
// Quality is now determined by pixel variation (distinct colors, luminance range,
// dominant color fraction) instead of compressed byte size.
const MIN_PNG_SIZE_BYTES = 1_000; // guard against truly empty/corrupt captures

// Maximum fraction of pixels that can be background-color before rejecting the frame
const MAX_BACKGROUND_FRACTION = 0.95;

// Maximum fraction of near-black pixels before rejecting a frame as a black/blank capture
const MAX_DARK_FRACTION = 0.995;
const DARK_COLOR_MAX = 8;

// Sample every Nth pixel for quality check (avoids full pixel scan for performance)
const PIXEL_SAMPLE_STEP = 4;

const MIN_DISTINCT_COLORS = 4;
const MIN_LUMINANCE_RANGE = 18;
const MAX_DOMINANT_COLOR_FRACTION = 0.85;

export const BROWSER_LAUNCH_ARGUMENTS = [
  "--no-sandbox",
  "--disable-dev-shm-usage",
  "--use-gl=angle",
  "--use-angle=d3d11",
  "--ignore-gpu-blocklist",
  "--use-cmd-decoder=passthrough",
  "--enable-gpu",
  "--enable-extensions",
] as const;
export const BROWSER_EXTENSIONS_ENABLED = true;

export function createBrowserFrameImageCapture(options: BrowserFrameImageCaptureOptions = {}): BrowserFrameCapture {
  const width = options.width ?? 640;
  const height = options.height ?? 640;
  const maxRetries = options.maxRetries ?? 3;
  const retryDelayMs = options.retryDelayMs ?? 2000;
  const deviceScaleFactor = options.deviceScaleFactor ?? 1;
  const fovDegrees = options.fovDegrees ?? 80;

  // One browser/page is kept alive across captures. A cold Chrome launch plus
  // viewer page load costs 5-10 seconds; reusing the page brings captures down
  // to a few hundred milliseconds and lets terrain accumulate between shots.
  let browser: import("puppeteer-core").Browser | null = null;
  let page: import("puppeteer-core").Page | null = null;
  let pageUrl: string | null = null;
  let queue: Promise<unknown> = Promise.resolve();
  let closed = false;

  const disposeBrowser = async (): Promise<void> => {
    const current = browser;
    browser = null;
    page = null;
    pageUrl = null;
    if (current) {
      try {
        await current.close();
      } catch {
        // Browser already gone
      }
    }
  };

  const ensurePage = async (url: string): Promise<import("puppeteer-core").Page> => {
    if (closed) {
      throw new Error("Frame capture has been closed.");
    }
    if (!browser) {
      const { default: puppeteer } = await import("puppeteer-core");
      const launched = await puppeteer.launch({
        executablePath: options.executablePath ?? browserExecutablePath(),
        headless: true,
        enableExtensions: BROWSER_EXTENSIONS_ENABLED,
        args: [...BROWSER_LAUNCH_ARGUMENTS],
      });
      launched.once("disconnected", () => {
        if (browser === launched) {
          browser = null;
          page = null;
          pageUrl = null;
        }
      });
      browser = launched;
      page = null;
      pageUrl = null;
    }
    if (!page || page.isClosed()) {
      page = await browser.newPage();
      await page.setViewport({ width, height, deviceScaleFactor });
      pageUrl = null;
    }
    if (pageUrl !== url) {
      await page.goto(url, { waitUntil: "networkidle2", timeout: 15000 });
      await page.waitForSelector("canvas", { timeout: 15000 }).catch(() => undefined);
      await page.waitForFunction(() => Boolean((window as any).viewer?.scene && (window as any).viewer?.camera), { timeout: 5000 }).catch(() => undefined);
      await injectBrightShading(page, fovDegrees);
      pageUrl = url;
    }
    return page;
  };

  const screenshotOnce = async (input: BrowserFrameCaptureInput): Promise<{ png: Buffer; width: number; height: number; quality: FrameQualityAssessment }> => {
    const attempt = async (): Promise<{ png: Buffer; width: number; height: number; quality: FrameQualityAssessment }> => {
      const currentPage = await ensurePage(input.url);
      // Crosshair (always, centered on the look direction) + optional HUD
      // strip, both drawn as DOM overlay so every captured PNG carries them.
      await injectOverlay(currentPage, input.hud);
      const dimensions = await currentPage.evaluate(() => {
        const canvas = document.querySelector("canvas");
        return {
          width: (canvas?.clientWidth || window.innerWidth) * window.devicePixelRatio,
          height: (canvas?.clientHeight || window.innerHeight) * window.devicePixelRatio,
        };
      });
      const png = Buffer.from(await currentPage.screenshot({ type: "png", fullPage: false }));
      const quality = await assessFrameQuality(png, dimensions.width, dimensions.height);
      return { png, width: dimensions.width, height: dimensions.height, quality };
    };

    try {
      return await attempt();
    } catch (error) {
      // The persistent browser may have died since the last capture; retry once
      // with a fresh instance before surfacing the error.
      if (closed) {
        throw error;
      }
      await disposeBrowser();
      return attempt();
    }
  };

  const toCapturedPng = (shot: { png: Buffer; width: number; height: number; quality: FrameQualityAssessment }): CapturedPng => ({
    png: shot.png,
    width: shot.width,
    height: shot.height,
    projection: {
      fovDegrees,
      near: 0.1,
      far: 1000,
      source: "prismarine-viewer browser capture",
    },
    quality: shot.quality,
  });

  // Captures share one page; serialize them so screenshots never interleave.
  const serialize = <T>(task: () => Promise<T>): Promise<T> => {
    const next = queue.then(task, task);
    queue = next.then(() => undefined, () => undefined);
    return next;
  };

  return {
    capture: ({ url, hud }) => serialize(async () => {
      let lastQuality: FrameQualityAssessment | null = null;
      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        if (attempt > 0) {
          // Wait for more terrain to render before retrying
          await new Promise((resolve) => setTimeout(resolve, retryDelayMs));
        }
        const shot = await screenshotOnce({ url, hud });
        lastQuality = shot.quality;
        if (shot.quality.usable) {
          return toCapturedPng(shot);
        }
      }
      throw new Error(
        `Frame capture produced unusable image after ${maxRetries + 1} attempts. ` +
        `Last reason: ${lastQuality?.reason}. ` +
        `Byte size: ${lastQuality?.byteSize}, BG fraction: ${(lastQuality?.backgroundFraction ?? 0).toFixed(2)}`
      );
    }),
    captureRaw: ({ url, hud }) => serialize(async () => toCapturedPng(await screenshotOnce({ url, hud }))),
    close: () => serialize(async () => {
      closed = true;
      await disposeBrowser();
    })
  };
}

/**
 * Draw the agent overlay into the viewer page: an X crosshair centered on the
 * canvas (the first-person camera follows the look direction, so dead center
 * is exactly what minecraft_raytrace resolves) and, when HUD lines are given,
 * a monospace strip in the top-left corner carrying pose/biome/vitals so the
 * image is self-describing. Idempotent: creates the overlay once, then only
 * updates the HUD text.
 */
async function injectOverlay(page: import("puppeteer-core").Page, hud?: string[]): Promise<void> {
  await page.evaluate((lines: string[]) => {
    try {
      const OVERLAY_ID = "agent-capture-overlay";
      const HUD_ID = "agent-capture-hud";
      let overlay = document.getElementById(OVERLAY_ID);
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = OVERLAY_ID;
        overlay.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:2147483647;";
        // Crosshair X: two stacked strokes (black outline under white) for
        // contrast on any background, centered on the viewport = canvas center.
        const cross = document.createElement("div");
        cross.style.cssText =
          "position:absolute;left:50%;top:50%;width:44px;height:44px;transform:translate(-50%,-50%);";
        for (const [color, width] of [["#000", 5], ["#fff", 2]] as const) {
          for (const angle of [45, -45]) {
            const line = document.createElement("div");
            line.style.cssText =
              `position:absolute;left:50%;top:50%;width:${width === 5 ? 46 : 42}px;height:${width}px;` +
              `background:${color};border-radius:${width / 2}px;transform:translate(-50%,-50%) rotate(${angle}deg);`;
            cross.appendChild(line);
          }
        }
        overlay.appendChild(cross);
        document.body.appendChild(overlay);
      }
      let hud = document.getElementById(HUD_ID);
      if (lines.length > 0) {
        if (!hud) {
          hud = document.createElement("div");
          hud.id = HUD_ID;
          hud.style.cssText =
            "position:absolute;left:8px;top:8px;font:13px/1.45 ui-monospace,Consolas,monospace;" +
            "color:#fff;background:rgba(0,0,0,0.55);padding:4px 8px;border-radius:4px;white-space:pre;";
          overlay.appendChild(hud);
        }
        hud.textContent = lines.join("\n");
        hud.style.display = "block";
      } else if (hud) {
        hud.style.display = "none";
      }
    } catch (err) {
      console.warn("Overlay injection failed (non-fatal): " + String(err));
    }
  }, hud ?? []);
}

/**
 * Keep caves readable without flattening adjacent faces. Ambient light lifts
 * shadows while a weaker directional light, Lambert materials, and AO retain
 * geometry cues. The modest FOV adds context without shrinking targets badly.
 */
async function injectBrightShading(page: import("puppeteer-core").Page, fovDegrees: number): Promise<void> {
  await page.evaluate((requestedFov) => {
    try {
      // viewer is the global prismarine-viewer instance
      const v = (window as any).viewer;
      if (v && v.scene) {
        if (v.camera) {
          v.camera.fov = requestedFov;
          v.camera.updateProjectionMatrix();
        }
        if (v.ambientLight) {
          v.ambientLight.intensity = 1.1;
          v.ambientLight.color.set(0xffffff);
        }
        if (v.directionalLight) {
          v.directionalLight.intensity = 0.55;
          v.directionalLight.color.set(0xffffff);
        }
        if (v.scene.fog) {
          v.scene.fog.color.set(0x8f9ba3);
          v.scene.fog.near = 100;
          v.scene.fog.far = 200;
        }
        if (v.scene.children) {
          for (const child of v.scene.children) {
            if ((child as any).isLight) {
              const light = child as any;
              if (light !== v.ambientLight && light !== v.directionalLight && light.intensity !== undefined) {
                light.intensity = Math.min(light.intensity, 0.55);
              }
            }
          }
        }
      }
    } catch (err) {
      console.warn("Bright shaded lighting injection failed (non-fatal): " + String(err));
    }
  }, fovDegrees);
}

/**
 * Assess whether a captured PNG frame contains usable terrain rendering
 * or is mostly the prismarine-viewer default lightblue background.
 */
export async function assessFrameQuality(
  png: Buffer,
  width: number,
  height: number
): Promise<FrameQualityAssessment> {
  const fractions = await samplePixelFractions(png, width, height);
  const bgFraction = fractions.backgroundFraction;

  if (bgFraction > MAX_BACKGROUND_FRACTION) {
    return qualityAssessment({
      usable: false,
      reason: (bgFraction * 100).toFixed(1) + "% of sampled pixels are background color (" + DEFAULT_BG_R + "," + DEFAULT_BG_G + "," + DEFAULT_BG_B + ")",
      byteSize: png.length,
      backgroundFraction: bgFraction,
      darkFraction: fractions.darkFraction,
      distinctColorCount: fractions.distinctColorCount,
      luminanceRange: fractions.luminanceRange,
      dominantColorFraction: fractions.dominantColorFraction,
    });
  }

  if (fractions.whiteFraction > MAX_BACKGROUND_FRACTION) {
    return qualityAssessment({
      usable: false,
      reason: (fractions.whiteFraction * 100).toFixed(1) + "% of sampled pixels are near-white; the viewer canvas has likely not rendered yet (e.g. WebGL context lost)",
      byteSize: png.length,
      backgroundFraction: fractions.backgroundFraction,
      darkFraction: fractions.darkFraction,
      distinctColorCount: fractions.distinctColorCount,
      luminanceRange: fractions.luminanceRange,
      dominantColorFraction: fractions.dominantColorFraction,
    });
  }

  if (fractions.darkFraction > MAX_DARK_FRACTION) {
    return qualityAssessment({
      usable: false,
      reason: (fractions.darkFraction * 100).toFixed(1) + "% of sampled pixels are near-black",
      byteSize: png.length,
      backgroundFraction: bgFraction,
      darkFraction: fractions.darkFraction,
      distinctColorCount: fractions.distinctColorCount,
      luminanceRange: fractions.luminanceRange,
      dominantColorFraction: fractions.dominantColorFraction,
    });
  }

  if (png.length < MIN_PNG_SIZE_BYTES && !hasMeaningfulPixelVariation(fractions)) {
    return qualityAssessment({
      usable: false,
      reason: "PNG byte size " + png.length + " is below minimum " + MIN_PNG_SIZE_BYTES + " and pixel variation is too low",
      byteSize: png.length,
      backgroundFraction: bgFraction,
      darkFraction: fractions.darkFraction,
      distinctColorCount: fractions.distinctColorCount,
      luminanceRange: fractions.luminanceRange,
      dominantColorFraction: fractions.dominantColorFraction,
    });
  }

  return qualityAssessment({
    usable: true,
    reason: png.length < MIN_PNG_SIZE_BYTES
      ? "Frame passes quality gate via pixel variation despite low PNG byte size"
      : "Frame passes quality gate",
    byteSize: png.length,
    backgroundFraction: bgFraction,
    darkFraction: fractions.darkFraction,
    distinctColorCount: fractions.distinctColorCount,
    luminanceRange: fractions.luminanceRange,
    dominantColorFraction: fractions.dominantColorFraction,
  });
}

interface PixelFractions {
  backgroundFraction: number;
  whiteFraction: number;
  darkFraction: number;
  distinctColorCount: number;
  luminanceRange: number;
  dominantColorFraction: number;
}

async function samplePixelFractions(png: Buffer, width: number, height: number): Promise<PixelFractions> {
  try {
    const { createCanvas, loadImage } = await import("canvas");
    const canvas = createCanvas(width, height);
    const ctx = canvas.getContext("2d");

    const img = await loadImage(png);
    ctx.drawImage(img, 0, 0, width, height);
    const data = ctx.getImageData(0, 0, width, height);

    let bgCount = 0;
    let whiteCount = 0;
    let darkCount = 0;
    let totalSampled = 0;
    let minLuminance = Number.POSITIVE_INFINITY;
    let maxLuminance = Number.NEGATIVE_INFINITY;
    const colorCounts = new Map<string, number>();
    const step = PIXEL_SAMPLE_STEP;

    for (let y = 0; y < height; y += step) {
      for (let x = 0; x < width; x += step) {
        const idx = (y * width + x) * 4;
        const r = data.data[idx];
        const g = data.data[idx + 1];
        const b = data.data[idx + 2];
        const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        const colorKey = `${r},${g},${b}`;

        totalSampled++;
        minLuminance = Math.min(minLuminance, luminance);
        maxLuminance = Math.max(maxLuminance, luminance);
        colorCounts.set(colorKey, (colorCounts.get(colorKey) ?? 0) + 1);
        if (isNearBackground(r, g, b)) {
          bgCount++;
        }
        if (isNearWhite(r, g, b)) {
          whiteCount++;
        }
        if (isNearBlack(r, g, b)) {
          darkCount++;
        }
      }
    }

    if (totalSampled === 0) {
      return blankPixelFractions();
    }

    const dominantCount = Math.max(...colorCounts.values());
    return {
      backgroundFraction: bgCount / totalSampled,
      whiteFraction: whiteCount / totalSampled,
      darkFraction: darkCount / totalSampled,
      distinctColorCount: colorCounts.size,
      luminanceRange: maxLuminance - minLuminance,
      dominantColorFraction: dominantCount / totalSampled,
    };
  } catch {
    // Fallback: byte-entropy heuristic if canvas is unavailable
    const byteSet = new Set<number>();
    const sampleSize = Math.min(png.length, 4096);
    for (let i = 0; i < sampleSize; i += 8) {
      byteSet.add(png[i]);
    }
    // Solid color PNGs typically have < 50 unique byte values
    return byteSet.size < 50
      ? blankPixelFractions()
      : {
        backgroundFraction: 0.0,
        whiteFraction: 0.0,
        darkFraction: 0.0,
        distinctColorCount: byteSet.size,
        luminanceRange: 255,
        dominantColorFraction: 0,
      };
  }
}

function qualityAssessment(
  input: Omit<
    FrameQualityAssessment,
    "minimumByteSize" |
    "maximumBackgroundFraction" |
    "maximumDarkFraction" |
    "minimumDistinctColors" |
    "minimumLuminanceRange" |
    "maximumDominantColorFraction"
  >
): FrameQualityAssessment {
  return {
    ...input,
    minimumByteSize: MIN_PNG_SIZE_BYTES,
    maximumBackgroundFraction: MAX_BACKGROUND_FRACTION,
    maximumDarkFraction: MAX_DARK_FRACTION,
    minimumDistinctColors: MIN_DISTINCT_COLORS,
    minimumLuminanceRange: MIN_LUMINANCE_RANGE,
    maximumDominantColorFraction: MAX_DOMINANT_COLOR_FRACTION,
  };
}

function hasMeaningfulPixelVariation(fractions: PixelFractions): boolean {
  return fractions.distinctColorCount >= MIN_DISTINCT_COLORS &&
    fractions.luminanceRange >= MIN_LUMINANCE_RANGE &&
    fractions.dominantColorFraction <= MAX_DOMINANT_COLOR_FRACTION;
}

function blankPixelFractions(): PixelFractions {
  return {
    backgroundFraction: 1.0,
    whiteFraction: 1.0,
    darkFraction: 1.0,
    distinctColorCount: 0,
    luminanceRange: 0,
    dominantColorFraction: 1.0,
  };
}

function isNearBackground(r: number, g: number, b: number): boolean {
  return (
    Math.abs(r - DEFAULT_BG_R) <= BG_COLOR_TOLERANCE &&
    Math.abs(g - DEFAULT_BG_G) <= BG_COLOR_TOLERANCE &&
    Math.abs(b - DEFAULT_BG_B) <= BG_COLOR_TOLERANCE
  );
}

function isNearWhite(r: number, g: number, b: number): boolean {
  return r >= 240 && g >= 240 && b >= 240;
}

function isNearBlack(r: number, g: number, b: number): boolean {
  return r <= DARK_COLOR_MAX && g <= DARK_COLOR_MAX && b <= DARK_COLOR_MAX;
}

function browserExecutablePath(): string {
  const candidates = [
    process.env.BROWSER_EXECUTABLE_PATH,
    "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].filter((value): value is string => typeof value === "string" && value.length > 0);

  const found = candidates.find((candidate) => existsSync(candidate));
  if (!found) {
    throw new Error("No supported browser executable found. Set BROWSER_EXECUTABLE_PATH.");
  }
  return found;
}
