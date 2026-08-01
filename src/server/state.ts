/**
 * Browser state needs live bot fields; serialize the minimal state shape without static placeholders.
 *
 * @remarks
 * archetype: service-provider
 * owns: the public `/api/state` minimal response shape for WI-01.
 * not own: Mineflayer state collection, command execution, or richer inventory summaries.
 * fails when: callers provide malformed live state objects.
 * domain: later work enriches this route, but this slice proves state comes from a bot-derived snapshot.
 * invariant: `currentCommand` is present and null until the command queue exists.
 */
export interface BotStateSnapshot {
  connected: boolean;
  username: string | null;
  position: { x: number; y: number; z: number } | null;
  yaw: number | null;
  pitch: number | null;
  yawDegrees: number | null;
  pitchDegrees: number | null;
  facing: string | null;
  dimension: string | null;
  health: number | null;
  food: number | null;
  selectedHotbarSlot: number | null;
  heldItem: InventoryItemSummary | null;
  inventory: InventorySummary;
  crosshairBlock: null;
}

export interface StateResponse extends BotStateSnapshot {
  currentCommand: CommandStateResponse | null;
}

export interface CommandStateResponse {
  commandId: string;
  command: string;
  status: string;
  input: unknown;
  acceptedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
}

export interface InventoryItemSummary {
  slot: number | null;
  name: string;
  displayName: string | null;
  count: number;
}

export interface InventorySummary {
  totalSlots: number;
  usedSlots: number;
  items: InventoryItemSummary[];
}

export function serializeState(snapshot: BotStateSnapshot, currentCommand: CommandStateResponse | null = null): StateResponse {
  return {
    ...snapshot,
    currentCommand
  };
}
