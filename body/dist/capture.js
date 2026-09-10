/**
 * Render the live Mineflayer view and capture real PNG bytes.
 *
 * A missing browser executable is a permanent setup error checked by Python.
 * Viewer or browser connection failures are external and transient, so capture
 * retries the same operation until the local renderer is available.
 */
import { mineflayer as startViewer } from "prismarine-viewer";
import puppeteer from "puppeteer-core";
export class ViewerCapture {
    viewerPort;
    browserExecutable;
    browser = null;
    page = null;
    viewerStarted = false;
    warming = null;
    constructor(viewerPort, browserExecutable) {
        this.viewerPort = viewerPort;
        this.browserExecutable = browserExecutable;
    }
    start(bot) {
        if (this.viewerStarted) {
            return;
        }
        startViewer(bot, { port: this.viewerPort, firstPerson: true, viewDistance: 12 });
        this.viewerStarted = true;
        this.warming = this.warm();
    }
    async capture() {
        await this.warming;
        while (true) {
            try {
                const page = await this.ensurePage();
                const png = Buffer.from(await page.screenshot({ type: "png" }));
                return { png_base64: png.toString("base64"), width: 640, height: 480 };
            }
            catch (error) {
                console.error(`Viewer capture failed: ${String(error)}. Trying again.`);
                await this.disposeBrowser();
                await delay(500);
            }
        }
    }
    async warm() {
        while (true) {
            try {
                await this.ensurePage();
                return;
            }
            catch (error) {
                console.error(`Viewer warmup failed: ${String(error)}. Trying again.`);
                await this.disposeBrowser();
                await delay(500);
            }
        }
    }
    async close() {
        await this.disposeBrowser();
    }
    async ensurePage() {
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
    async disposeBrowser() {
        const browser = this.browser;
        this.browser = null;
        this.page = null;
        if (browser !== null) {
            await browser.close();
        }
    }
}
function delay(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
