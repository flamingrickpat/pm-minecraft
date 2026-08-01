import { mkdir, writeFile, appendFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import Database from "better-sqlite3";

/**
 * Evidence records need SQLite persistence and disk files; own schema creation, writes, and queries at the shared command/evidence boundary.
 *
 * @remarks
 * archetype: information-holder
 * owns: SQLite schema, command logs, inventory snapshots, world changes, screenshot blobs + disk paths, CLI transcripts, and disk-only error logs.
 * not own: command execution, screenshot capture, or CLI process management.
 * fails when: SQLite DB path is invalid, write fails, or disk path is inaccessible.
 * domain: evidence rows are produced at the shared command/evidence boundary where real commands execute; tests alone do not create evidence.
 * invariant: SQLite rows and disk files are written atomically for the same command; error logs are disk-only.
 */
export interface EvidenceStore {
  close(): Promise<void>;
  recordCommand(cmd: CommandRecord): Promise<void>;
  recordInventorySnapshot(runId: string, commandId: string, snapshot: InventorySnapshot): Promise<void>;
  recordWorldChange(runId: string, commandId: string, change: WorldChange): Promise<void>;
  recordScreenshot(runId: string, metadata: ScreenshotMetadata, pngBlob: Buffer): Promise<void>;
  recordCliTranscript(runId: string, channel: string, text: string): Promise<void>;
  logError(message: string): void;
  getEvidence<T extends EvidenceRecord>(table: EvidenceTable, filters: QueryFilters): Promise<T[]>;
  get(sql: string, params: unknown[], columns?: string[]): Promise<any[]>;
}

export type EvidenceTable = "commands" | "inventory_snapshots" | "world_changes" | "screenshots" | "cli_transcripts" | "evidence_records";

export interface QueryFilters {
  runId?: string;
}

export interface CommandRecord extends EvidenceRecord {
  commandId: string;
  command: string;
  status: "succeeded" | "failed" | "cancelled" | "timed_out";
  input: unknown;
  acceptedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  durationMs: number;
  ok: boolean;
  reason: string | null;
  message: string;
  data: unknown;
}

export interface InventorySnapshot {
  totalSlots: number;
  usedSlots: number;
  items: InventoryItem[];
}

export interface InventoryItem {
  slot: number | null;
  name: string;
  count: number;
}

export interface WorldChange {
  position: { x: number; y: number; z: number };
  oldBlock: string;
  newBlock: string;
  source: string;
}

export interface ScreenshotMetadata {
  frameId: string;
  capturedAt: string;
  pngPath: string;
  width: number;
  height: number;
}

export interface EvidenceRecord {
  id: number | null;
  runId: string;
  evidenceType: string | null;
  commandId: string | null;
  data: unknown;
  recordedAt: string;
}

/**
 * Creates an evidence store backed by SQLite and disk files.
 *
 * @param dbPath - Path to the SQLite database file
 * @returns An EvidenceStore instance
 */
export function createEvidenceStore(dbPath: string): EvidenceStore {
  const dbDir = dirname(dbPath);
  const errorLogDir = join(dbDir, "errors");
  let db: InstanceType<typeof Database> | null = null;
  let cliCounter = 0;

  async function initDatabase(): Promise<InstanceType<typeof Database>> {
    if (db) {
      return db;
    }
    await mkdir(dbDir, { recursive: true });
    db = new Database(dbPath);
    db.pragma("journal_mode = WAL");
    createTables(db);
    return db;
  }

  function createTables(db: InstanceType<typeof Database>): void {
    db.exec(`
      CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        command_id TEXT NOT NULL,
        command TEXT NOT NULL,
        status TEXT NOT NULL,
        input TEXT NOT NULL,
        accepted_at TEXT NOT NULL,
        started_at TEXT,
        finished_at TEXT,
        duration_ms INTEGER NOT NULL,
        ok INTEGER NOT NULL,
        reason TEXT,
        message TEXT NOT NULL,
        data TEXT,
        recorded_at TEXT NOT NULL,
        UNIQUE(run_id, command_id)
      );

      CREATE TABLE IF NOT EXISTS inventory_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        command_id TEXT NOT NULL,
        total_slots INTEGER NOT NULL,
        used_slots INTEGER NOT NULL,
        items_json TEXT NOT NULL,
        recorded_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS world_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        command_id TEXT NOT NULL,
        position_x INTEGER NOT NULL,
        position_y INTEGER NOT NULL,
        position_z INTEGER NOT NULL,
        old_block TEXT NOT NULL,
        new_block TEXT NOT NULL,
        source TEXT NOT NULL,
        recorded_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        frame_id TEXT NOT NULL,
        captured_at TEXT NOT NULL,
        png_path TEXT NOT NULL,
        width INTEGER NOT NULL,
        height INTEGER NOT NULL,
        blob_size INTEGER NOT NULL,
        png_blob BLOB,
        recorded_at TEXT NOT NULL,
        UNIQUE(run_id, frame_id)
      );

      CREATE TABLE IF NOT EXISTS cli_transcripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        channel TEXT NOT NULL,
        text TEXT NOT NULL,
        line_number INTEGER NOT NULL,
        recorded_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS evidence_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        evidence_type TEXT NOT NULL,
        command_id TEXT,
        data_json TEXT NOT NULL,
        recorded_at TEXT NOT NULL
      );

      CREATE INDEX IF NOT EXISTS idx_commands_run_id ON commands(run_id);
      CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_run_id ON inventory_snapshots(run_id);
      CREATE INDEX IF NOT EXISTS idx_world_changes_run_id ON world_changes(run_id);
      CREATE INDEX IF NOT EXISTS idx_screenshots_run_id ON screenshots(run_id);
      CREATE INDEX IF NOT EXISTS idx_cli_transcripts_run_id ON cli_transcripts(run_id);
    `);
  }

  async function ensureRun(runId: string): Promise<void> {
    const database = await initDatabase();
    try {
      database.prepare("INSERT INTO runs (run_id, created_at) VALUES (?, ?)").run(runId, new Date().toISOString());
    } catch {
      // Run already exists, ignore
    }
  }

  async function recordCommand(cmd: CommandRecord): Promise<void> {
    const database = await initDatabase();
    await ensureRun(cmd.runId);
    database.prepare(`
      INSERT OR REPLACE INTO commands (run_id, command_id, command, status, input, accepted_at, started_at, finished_at, duration_ms, ok, reason, message, data, recorded_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      cmd.runId,
      cmd.commandId,
      cmd.command,
      cmd.status,
      JSON.stringify(cmd.input),
      cmd.acceptedAt,
      cmd.startedAt,
      cmd.finishedAt,
      cmd.durationMs,
      cmd.ok ? 1 : 0,
      cmd.reason,
      cmd.message,
      JSON.stringify(cmd.data),
      new Date().toISOString()
    );

    // Also record in evidence_records for generic querying
    database.prepare(`
      INSERT INTO evidence_records (run_id, evidence_type, command_id, data_json, recorded_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(
      cmd.runId,
      "command",
      cmd.commandId,
      JSON.stringify(cmd),
      new Date().toISOString()
    );
  }

  async function recordInventorySnapshot(runId: string, commandId: string, snapshot: InventorySnapshot): Promise<void> {
    const database = await initDatabase();
    await ensureRun(runId);
    database.prepare(`
      INSERT INTO inventory_snapshots (run_id, command_id, total_slots, used_slots, items_json, recorded_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(
      runId,
      commandId,
      snapshot.totalSlots,
      snapshot.usedSlots,
      JSON.stringify(snapshot.items),
      new Date().toISOString()
    );

    database.prepare(`
      INSERT INTO evidence_records (run_id, evidence_type, command_id, data_json, recorded_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(
      runId,
      "inventory_snapshot",
      commandId,
      JSON.stringify(snapshot),
      new Date().toISOString()
    );
  }

  async function recordWorldChange(runId: string, commandId: string, change: WorldChange): Promise<void> {
    const database = await initDatabase();
    await ensureRun(runId);
    database.prepare(`
      INSERT INTO world_changes (run_id, command_id, position_x, position_y, position_z, old_block, new_block, source, recorded_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      runId,
      commandId,
      change.position.x,
      change.position.y,
      change.position.z,
      change.oldBlock,
      change.newBlock,
      change.source,
      new Date().toISOString()
    );

    database.prepare(`
      INSERT INTO evidence_records (run_id, evidence_type, command_id, data_json, recorded_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(
      runId,
      "world_change",
      commandId,
      JSON.stringify(change),
      new Date().toISOString()
    );
  }

  async function recordScreenshot(runId: string, metadata: ScreenshotMetadata, pngBlob: Buffer): Promise<void> {
    const database = await initDatabase();
    await ensureRun(runId);

    // Write to disk first
    await mkdir(dirname(metadata.pngPath), { recursive: true });
    await writeFile(metadata.pngPath, pngBlob);

    database.prepare(`
      INSERT OR REPLACE INTO screenshots (run_id, frame_id, captured_at, png_path, width, height, blob_size, png_blob, recorded_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      runId,
      metadata.frameId,
      metadata.capturedAt,
      metadata.pngPath,
      metadata.width,
      metadata.height,
      pngBlob.length,
      pngBlob,
      new Date().toISOString()
    );

    database.prepare(`
      INSERT INTO evidence_records (run_id, evidence_type, command_id, data_json, recorded_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(
      runId,
      "screenshot",
      null,
      JSON.stringify({ ...metadata, blobSize: pngBlob.length }),
      new Date().toISOString()
    );
  }

  async function recordCliTranscript(runId: string, channel: string, text: string): Promise<void> {
    const database = await initDatabase();
    await ensureRun(runId);
    cliCounter += 1;
    database.prepare(`
      INSERT INTO cli_transcripts (run_id, channel, text, line_number, recorded_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(
      runId,
      channel,
      text,
      cliCounter,
      new Date().toISOString()
    );

    database.prepare(`
      INSERT INTO evidence_records (run_id, evidence_type, command_id, data_json, recorded_at)
      VALUES (?, ?, ?, ?, ?)
    `).run(
      runId,
      "cli_transcript",
      null,
      JSON.stringify({ channel, text, line_number: cliCounter }),
      new Date().toISOString()
    );
  }

  function logError(message: string): void {
    const timestamp = new Date().toISOString();
    const logPath = join(errorLogDir, `${timestamp.replace(/[:.]/g, "-")}.log`);
    void mkdir(errorLogDir, { recursive: true }).then(() => appendFile(logPath, message + "\n", "utf8")).catch(() => {
      // Silently fail on disk write errors for error logging
    });
  }

  async function getEvidence<T extends EvidenceRecord>(table: EvidenceTable, filters: QueryFilters): Promise<T[]> {
    const database = await initDatabase();

    let sql: string;
    const params: unknown[] = [];

    switch (table) {
      case "commands":
        sql = "SELECT id, run_id as runId, command_id as commandId, command, status, input, accepted_at as acceptedAt, started_at as startedAt, finished_at as finishedAt, duration_ms as durationMs, ok, reason, message, data, recorded_at as recordedAt FROM commands WHERE run_id = ? ORDER BY accepted_at";
        params.push(filters.runId);
        break;
      case "inventory_snapshots":
        sql = "SELECT id, run_id, command_id, total_slots as totalSlots, used_slots as usedSlots, items_json as items, recorded_at FROM inventory_snapshots WHERE run_id = ? ORDER BY recorded_at";
        params.push(filters.runId);
        break;
      case "world_changes":
        sql = "SELECT id, run_id, command_id, position_x as x, position_y as y, position_z as z, old_block as oldBlock, new_block as newBlock, source, recorded_at FROM world_changes WHERE run_id = ? ORDER BY recorded_at";
        params.push(filters.runId);
        break;
      case "screenshots":
        sql = "SELECT id, run_id, frame_id, captured_at, png_path as pngPath, width, height, blob_size as blobSize, recorded_at FROM screenshots WHERE run_id = ? ORDER BY captured_at";
        params.push(filters.runId);
        break;
      case "cli_transcripts":
        sql = "SELECT id, run_id, channel, text, line_number as lineNumber, recorded_at FROM cli_transcripts WHERE run_id = ? ORDER BY line_number";
        params.push(filters.runId);
        break;
      case "evidence_records":
        sql = "SELECT id, run_id, evidence_type, command_id, data_json as data, recorded_at FROM evidence_records WHERE run_id = ? ORDER BY recorded_at";
        params.push(filters.runId);
        break;
      default:
        throw new Error(`Unknown evidence table: ${table}`);
    }

    return database.prepare(sql).all(...params) as T[];
  }

  async function get(sql: string, params: unknown[], _columns?: string[]): Promise<any[]> {
    const database = await initDatabase();
    const statement = database.prepare(sql);
    const result = statement.all(...params);
    return result;
  }

  async function close(): Promise<void> {
    if (db) {
      db.close();
      db = null;
    }
  }

  return {
    close,
    recordCommand,
    recordInventorySnapshot,
    recordWorldChange,
    recordScreenshot,
    recordCliTranscript,
    logError,
    getEvidence,
    get
  };
}
