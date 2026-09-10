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

  constructor(
    private readonly viewerPort: number,
    private readonly browserExecutable: string,
  ) {}

  start(bot: Bot): void {
    if (this.viewerStarted) {
      return;
    }
    startViewer(bot, { port: this.viewerPort, firstPerson: true, viewDistance: 12 });
    this.viewerStarted = true;
    this.warming = this.warm();
  }

  async capture(): Promise<CapturedFrame> {
    await this.warming;
    while (true) {
      try {
        const page = await this.ensurePage();
        const png = Buffer.from(await page.screenshot({ type: "png" }));
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
        waitUntil: "networkidle2",
        timeout: 15000,
      });
      await this.page.waitForSelector("canvas", { timeout: 15000 });
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
