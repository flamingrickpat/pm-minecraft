import { test, expect } from "@playwright/test";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000";

/**
 * WI-12: Playwright smoke test for browser UI.
 *
 * Verifies that the browser UI loads, shows core controls, and has no critical
 * console errors. This test runs against a live backend (npm run dev) or
 * a local HTTP server with the product runtime.
 */
test.describe("Browser smoke flow", () => {
  test("loads the app and shows UI controls", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Verify page loaded
    await expect(page).toHaveTitle(/turnbased/i);

    // Verify core UI elements are present
    await expect(page.locator("#toolbar")).toBeVisible();
    await expect(page.locator("#mode-group")).toBeVisible();
    await expect(page.locator("#stop-btn")).toBeVisible();
    await expect(page.locator("#viewer-area")).toBeVisible();
    await expect(page.locator("#target-preview")).toBeVisible();
    await expect(page.locator("#sidebar")).toBeVisible();
    await expect(page.locator("#panel-state")).toBeVisible();
    await expect(page.locator("#panel-inventory")).toBeVisible();
    await expect(page.locator("#panel-crafting")).toBeVisible();
    await expect(page.locator("#panel-chat")).toBeVisible();
    await expect(page.locator("#panel-log")).toBeVisible();
    await expect(page.locator("#panel-fine")).toBeVisible();
  });

  test("shows all mode buttons", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Verify all 7 mode buttons exist
    const modes = ["Look", "Walk", "Mine", "Place", "Use", "Inspect", "Fine Ctrl"];
    for (const mode of modes) {
      await expect(page.locator(`button[data-mode]`).and(page.locator(`:text("${mode}")`))).toBeVisible();
    }

    // Verify stop button is always visible
    await expect(page.locator("#stop-btn")).toBeVisible();
  });

  test("shows viewer iframe and target preview", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Viewer iframe should be present (may not load if viewer port is not available)
    await expect(page.locator("#viewer-frame")).toBeVisible();

    // Target preview should show initial placeholder values
    await expect(page.locator("#tp-block")).toBeVisible();
    await expect(page.locator("#tp-pos")).toBeVisible();
    await expect(page.locator("#tp-face")).toBeVisible();
    await expect(page.locator("#tp-dist")).toBeVisible();
  });

  test("shows state panel fields", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // State panel fields should be present
    await expect(page.locator("#st-pos")).toBeVisible();
    await expect(page.locator("#st-angles")).toBeVisible();
    await expect(page.locator("#st-health")).toBeVisible();
    await expect(page.locator("#st-food")).toBeVisible();
    await expect(page.locator("#st-held")).toBeVisible();
    await expect(page.locator("#st-dim")).toBeVisible();
  });

  test("shows command status indicator", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Command status should be visible and show initial state
    await expect(page.locator("#cmd-status")).toBeVisible();
    const cmdStatus = page.locator("#cmd-status");
    await expect(cmdStatus).toHaveClass(/idle/);
  });

  test("shows inventory panel structure", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Hotbar grid should be present
    await expect(page.locator("#hotbar-grid")).toBeVisible();

    // Inventory list should exist in DOM (may be empty initially)
    expect(await page.locator("#inventory-list").count()).toBe(1);
    // Verify it's not collapsed (panel-body without collapsed class)
    const invBody = page.locator("#inventory-body");
    expect(await invBody.getAttribute("class")).not.toContain("collapsed");
  });

  test("shows crafting panel controls", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Crafting grid should be present
    await expect(page.locator("#crafting-grid")).toBeVisible();

    // Crafting output slot
    await expect(page.locator("#craft-output")).toBeVisible();

    // Crafting action buttons
    const craftingActions = ["Open Inv", "Open Table", "Set Grid", "Take Output", "Clear Grid", "Close"];
    for (const action of craftingActions) {
      await expect(page.locator(`:text("${action}")`)).toBeVisible();
    }
  });

  test("shows chat panel with input", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Chat panel body should be present and not collapsed
    const chatBody = page.locator("#chat-body");
    expect(await chatBody.getAttribute("class")).not.toContain("collapsed");

    // Chat input should be visible
    await expect(page.locator("#chat-input")).toBeVisible();
  });

  test("shows action log panel", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    await expect(page.locator("#action-log")).toBeVisible();
  });

  test("shows fine control panel buttons", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Fine control panel and its buttons exist in the DOM
    expect(await page.locator("#fine-control-panel").count()).toBe(1);
    expect(await page.locator("#fc-duration").count()).toBe(1);

    // Verify fine control buttons are in the DOM (Fwd, Jump, Stop, etc.)
    const fcButtons = page.locator("#fine-control-panel button");
    expect(await fcButtons.count()).toBeGreaterThan(5);

    // Verify the panel can be toggled open by removing collapsed class via JS
    await page.evaluate(() => {
      const body = document.querySelector("#fine-control-panel");
      if (body) body.classList.remove("collapsed");
    });

    // After removing collapsed, panel should be visible
    await expect(page.locator("#fine-control-panel")).toBeVisible();
  });

  test("captures full UI screenshot for evidence", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Wait briefly for any WebSocket state updates
    await page.waitForTimeout(2000);

    // Take a full-page screenshot for evidence
    await page.screenshot({
      path: "evidence/browser-smoke-full-ui.png",
      fullPage: false
    });

    // Screenshot should have been captured successfully
    const fs = await import("node:fs");
    expect(fs.existsSync("evidence/browser-smoke-full-ui.png")).toBe(true);
  });

  test("has no critical JavaScript console errors", async ({ page }) => {
    const errors: string[] = [];

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        errors.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/`);
    await page.waitForTimeout(3000);

    // Filter out expected WebSocket reconnection errors (viewer may not be available)
    const criticalErrors = errors.filter((err) => {
      // Ignore expected errors from viewer iframe and WebSocket reconnection
      return !err.includes("WebSocket")
        && !err.includes("prismarine-viewer")
        && !err.includes("Failed to load")
        && !err.includes("net::ERR")
        && !err.includes("frame");
    });

    expect(criticalErrors.length).toBe(0);
  });

  test("health API is reachable from browser context", async ({ page, request }) => {
    const health = await request.get(`${BASE_URL}/api/health`);
    expect(health.status()).toBe(200);
    const body = await health.json();
    expect(body).toHaveProperty("ready");
    expect(body).toHaveProperty("config");
    expect(body).toHaveProperty("mineflayer");
    expect(body).toHaveProperty("paper");
    expect(body).toHaveProperty("http");
    expect(body).toHaveProperty("viewer");
  });

  test("state API is reachable from browser context", async ({ page, request }) => {
    const state = await request.get(`${BASE_URL}/api/state`);
    expect(state.status()).toBe(200);
    const body = await state.json();
    expect(body).toHaveProperty("connected");
    expect(body).toHaveProperty("username");
  });

  test("confirm dialog overlay exists for destructive actions", async ({ page }) => {
    await page.goto(`${BASE_URL}/`);

    // Confirm overlay should exist but be hidden
    const overlay = page.locator("#confirm-overlay");
    await expect(overlay).toBeVisible({ visible: false });
    // Or check that it's in the DOM but not displayed
    expect(await overlay.count()).toBeGreaterThan(0);
  });
});
