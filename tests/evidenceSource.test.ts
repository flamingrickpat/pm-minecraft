import { mkdir, rm } from "node:fs/promises";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createEvidenceStore, type EvidenceStore, type CommandRecord } from "../src/evidence/evidenceStore.js";

/**
 * WI-12: Backend evidence-source test.
 *
 * Verifies that command records can be distinguished by source (browser/API vs CLI transcript)
 * without changing command semantics. Both sources record to the same evidence store.
 */
describe("Evidence source distinction", () => {
  const testDir = join("evidence", "__tests__", "evidence-source");
  const dbPath = join(testDir, "evidence-source.db");
  let store: EvidenceStore;
  let runId: string;

  beforeEach(async () => {
    await mkdir(testDir, { recursive: true });
    store = createEvidenceStore(dbPath);
    runId = `source_test_${Date.now()}`;
  });

  afterEach(async () => {
    await store.close();
    await rm(testDir, { recursive: true, force: true });
  });

  it("records browser-sourced commands with source=browser", async () => {
    const cmd: CommandRecord = {
      id: null,
      runId,
      evidenceType: "command",
      commandId: "cmd_browser_1",
      command: "look_at",
      status: "succeeded",
      input: { target: { x: 100, y: 64, z: -50 }, source: "browser" },
      acceptedAt: "2026-06-19T00:00:00Z",
      startedAt: "2026-06-19T00:00:01Z",
      finishedAt: "2026-06-19T00:00:02Z",
      durationMs: 1000,
      ok: true,
      reason: null,
      message: "Looked at target.",
      data: null,
      recordedAt: new Date().toISOString()
    };
    await store.recordCommand(cmd);

    const rows = await store.getEvidence("commands", { runId }) as unknown as Array<{ input: unknown }>;
    expect(rows.length).toBe(1);
    // The source should be queryable from the stored command record
    const input = JSON.parse(rows[0].input as string);
    expect(input.source).toBe("browser");
  });

  it("records cli-sourced commands with source=cli", async () => {
    const cmd: CommandRecord = {
      id: null,
      runId,
      evidenceType: "command",
      commandId: "cmd_cli_1",
      command: "mine_block",
      status: "succeeded",
      input: { block: { x: 1, y: 64, z: 2 }, source: "cli" },
      acceptedAt: "2026-06-19T00:00:00Z",
      startedAt: "2026-06-19T00:00:01Z",
      finishedAt: "2026-06-19T00:00:02Z",
      durationMs: 1000,
      ok: true,
      reason: null,
      message: "Mined block.",
      data: null,
      recordedAt: new Date().toISOString()
    };
    await store.recordCommand(cmd);

    const rows = await store.getEvidence("commands", { runId }) as unknown as Array<{ input: unknown }>;
    expect(rows.length).toBe(1);
    const input = JSON.parse(rows[0].input as string);
    expect(input.source).toBe("cli");
  });

  it("can filter browser commands from CLI commands in the same run", async () => {
    // Record a browser command
    await store.recordCommand({
      id: null,
      runId,
      evidenceType: "command",
      commandId: "cmd_browser_1",
      command: "look_at",
      status: "succeeded",
      input: { target: { x: 100, y: 64, z: -50 }, source: "browser" },
      acceptedAt: "2026-06-19T00:00:00Z",
      startedAt: "2026-06-19T00:00:01Z",
      finishedAt: "2026-06-19T00:00:02Z",
      durationMs: 1000,
      ok: true,
      reason: null,
      message: "Looked at target.",
      data: null,
      recordedAt: new Date().toISOString()
    });

    // Record a CLI command
    await store.recordCommand({
      id: null,
      runId,
      evidenceType: "command",
      commandId: "cmd_cli_1",
      command: "mine_block",
      status: "succeeded",
      input: { block: { x: 1, y: 64, z: 2 }, source: "cli" },
      acceptedAt: "2026-06-19T00:00:03Z",
      startedAt: "2026-06-19T00:00:04Z",
      finishedAt: "2026-06-19T00:00:05Z",
      durationMs: 1000,
      ok: true,
      reason: null,
      message: "Mined block.",
      data: null,
      recordedAt: new Date().toISOString()
    });

    // Query all commands for the run
    const allRows = await store.getEvidence("commands", { runId }) as CommandRecord[];
    expect(allRows.length).toBe(2);

    // Verify source distinction via raw SQL query
    const browserRows = await store.get(
      "SELECT command_id, command, input FROM commands WHERE run_id = ? AND json_extract(input, '$.source') = 'browser'",
      [runId]
    );
    expect(browserRows.length).toBe(1);
    expect(browserRows[0].command_id).toBe("cmd_browser_1");

    const cliRows = await store.get(
      "SELECT command_id, command, input FROM commands WHERE run_id = ? AND json_extract(input, '$.source') = 'cli'",
      [runId]
    );
    expect(cliRows.length).toBe(1);
    expect(cliRows[0].command_id).toBe("cmd_cli_1");
  });

  it("browser and CLI commands use identical command semantics (same schema)", async () => {
    const browserCmd: CommandRecord = {
      id: null,
      runId,
      evidenceType: "command",
      commandId: "cmd_browser_mine",
      command: "mine_block",
      status: "succeeded",
      input: { block: { x: 50, y: 65, z: -10 }, walkIntoRange: true, source: "browser" },
      acceptedAt: "2026-06-19T00:00:00Z",
      startedAt: "2026-06-19T00:00:01Z",
      finishedAt: "2026-06-19T00:00:02Z",
      durationMs: 2000,
      ok: true,
      reason: null,
      message: "Mined block.",
      data: { blockName: "oak_log" },
      recordedAt: new Date().toISOString()
    };

    const cliCmd: CommandRecord = {
      id: null,
      runId,
      evidenceType: "command",
      commandId: "cmd_cli_mine",
      command: "mine_block",
      status: "succeeded",
      input: { block: { x: 51, y: 65, z: -10 }, walkIntoRange: true, source: "cli" },
      acceptedAt: "2026-06-19T00:00:03Z",
      startedAt: "2026-06-19T00:00:04Z",
      finishedAt: "2026-06-19T00:00:05Z",
      durationMs: 2500,
      ok: true,
      reason: null,
      message: "Mined block.",
      data: { blockName: "oak_log" },
      recordedAt: new Date().toISOString()
    };

    await store.recordCommand(browserCmd);
    await store.recordCommand(cliCmd);

    // Both commands have identical schema fields (command, status, input structure minus source)
    const rows = await store.getEvidence("commands", { runId }) as CommandRecord[];
    expect(rows.length).toBe(2);

    // Both are "mine_block" with "succeeded" status
    for (const row of rows) {
      expect(row.command).toBe("mine_block");
      expect(row.status).toBe("succeeded");
      const input = JSON.parse(row.input as string);
      expect(input).toHaveProperty("block");
      expect(input).toHaveProperty("walkIntoRange");
      expect(input).toHaveProperty("source");
    }
  });

  it("evidence_records table also stores source-distinguishable command evidence", async () => {
    await store.recordCommand({
      id: null,
      runId,
      evidenceType: "command",
      commandId: "cmd_browser_1",
      command: "walk_to",
      status: "succeeded",
      input: { target: { x: 10, y: 64, z: 10 }, source: "browser" },
      acceptedAt: "2026-06-19T00:00:00Z",
      startedAt: "2026-06-19T00:00:01Z",
      finishedAt: "2026-06-19T00:00:02Z",
      durationMs: 500,
      ok: true,
      reason: null,
      message: "Reached target.",
      data: null,
      recordedAt: new Date().toISOString()
    });

    // Check evidence_records table has the command evidence
    const evidenceRows = await store.get(
      "SELECT evidence_type, data_json FROM evidence_records WHERE run_id = ? AND evidence_type = 'command'",
      [runId]
    );
    expect(evidenceRows.length).toBe(1);
    const data = JSON.parse(evidenceRows[0].data_json as string);
    expect(data.commandId).toBe("cmd_browser_1");
    // Source is embedded in the input and thus in the evidence_records data
    expect(data.input.source).toBe("browser");
  });
});
