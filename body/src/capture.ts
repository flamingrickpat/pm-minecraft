/**
 * Render the live Mineflayer view and capture real PNG bytes.
 *
 * A missing browser executable is a permanent setup error checked by Python.
 * Viewer or browser connection failures are external and transient, so capture
 * retries the same operation until the local renderer is available.
 */

import type { Bot } from "mineflayer";
import { mineflayer as startViewer } from "prismarine-viewer";
import puppeteer, { Browser, Page } from "puppeteer-core";

export type CapturedFrame = {
  png_base64: string;
  width: number;
  height: number;
};

export class ViewerCapture {
  private browser: Browser | null = null;
  private page: Page | null = null;
  private viewerStarted = false;
  private warming: Promise<void> | null = null;
  private bot: Bot | null = null;
  private pendingCapture: Promise<void> = Promise.resolve();

  constructor(
    private readonly viewerPort: number,
    private readonly browserExecutable: string,
  ) {}

  start(bot: Bot): void {
    this.bot = bot;
    if (this.viewerStarted) {
      return;
    }
    startViewer(bot, { port: this.viewerPort, firstPerson: true, viewDistance: 12 });
    this.viewerStarted = true;
    this.warming = this.warm();
  }

  capture(): Promise<CapturedFrame> {
    const frame = this.pendingCapture.then(() => this.captureFrame());
    this.pendingCapture = frame.then(() => {}, () => {});
    return frame;
  }

  private async captureFrame(): Promise<CapturedFrame> {
    await this.warming;
    while (true) {
      try {
        const page = await this.ensurePage();
        const bot = this.bot!;
        // bot.look(force=true) changes the pose before the viewer's next move
        // packet. Render this snapshot directly, then wait for browser frames.
        const state = {
          position: { x: bot.entity.position.x, y: bot.entity.position.y + 1.62, z: bot.entity.position.z },
          yaw: bot.entity.yaw, pitch: bot.entity.pitch,
          timeOfDay: bot.time.timeOfDay, isRaining: bot.isRaining,
          dimension: bot.game.dimension,
        };
        await page.evaluate(async (snapshot) => {
          const bridge = (globalThis as any).mcmcpViewer;
          await bridge.viewer.waitForChunksToRender();
          bridge.capturing = true;
          await new Promise(resolve => setTimeout(resolve, 75));
          await new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
          // Flush the viewer's position tween before setting the exact pose.
          bridge.viewer.update();
          bridge.viewer.camera.rotation.set(snapshot.pitch, snapshot.yaw, 0, 'ZYX');
          bridge.viewer.camera.position.set(snapshot.position.x, snapshot.position.y, snapshot.position.z);
          (globalThis as any).mcmcpUpdateEnvironment(bridge.viewer, snapshot);
          bridge.renderer.render(bridge.viewer.scene, bridge.viewer.camera);
        }, state);
        const png = Buffer.from(await page.screenshot({ type: "png" }));
        await page.evaluate(() => { (globalThis as any).mcmcpViewer.capturing = false; });
        return { png_base64: png.toString("base64"), width: 640, height: 480 };
      } catch (error) {
        console.error(`Viewer capture failed: ${String(error)}. Trying again.`);
        await this.disposeBrowser();
        await delay(500);
      }
    }
  }

  private async warm(): Promise<void> {
    while (true) {
      try {
        await this.ensurePage();
        return;
      } catch (error) {
        console.error(`Viewer warmup failed: ${String(error)}. Trying again.`);
        await this.disposeBrowser();
        await delay(500);
      }
    }
  }

  async close(): Promise<void> {
    await this.disposeBrowser();
  }

  private async ensurePage(): Promise<Page> {
    if (this.browser === null) {
      this.browser = await puppeteer.launch({
        executablePath: this.browserExecutable,
        headless: true,
        args: ["--no-sandbox", "--disable-dev-shm-usage", "--use-gl=angle"],
      });
    }
    if (this.page === null || this.page.isClosed()) {
      this.page = await this.browser.newPage();
      await this.page.setViewport({ width: 640, height: 480, deviceScaleFactor: 1 });
      await this.page.goto(`http://127.0.0.1:${this.viewerPort}`, {
        waitUntil: "domcontentloaded",
        timeout: 15000,
      });
      await this.page.waitForSelector("canvas", { timeout: 15000 });
      await this.page.waitForFunction(() => (globalThis as any).mcmcpViewer?.viewer.version !== undefined, { timeout: 15000 });
      await this.page.evaluate(() => {
        const bridge = (globalThis as any).mcmcpViewer;
        const setCamera = bridge.viewer.setFirstPersonCamera.bind(bridge.viewer);
        bridge.viewer.setFirstPersonCamera = (...args: unknown[]) => {
          if (!bridge.capturing) setCamera(...args);
        };
      });
      await delay(500);
    }
    return this.page;
  }

  private async disposeBrowser(): Promise<void> {
    const browser = this.browser;
    this.browser = null;
    this.page = null;
    if (browser !== null) {
      await browser.close();
    }
  }
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
