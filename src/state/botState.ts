import type { BotStateSnapshot, InventoryItemSummary } from "../server/state.js";

interface SnapshotStatus {
  connected: boolean;
  username: string;
}

interface BotLike {
  username?: string;
  entity?: { position?: { x: number; y: number; z: number }; yaw?: number; pitch?: number };
  game?: { dimension?: unknown };
  health?: unknown;
  food?: unknown;
  quickBarSlot?: unknown;
  heldItem?: ItemLike | null;
  inventory?: { slots?: Array<ItemLike | null | undefined> };
}

interface ItemLike {
  slot?: unknown;
  name?: unknown;
  displayName?: unknown;
  count?: unknown;
}

export function createBotStateSnapshot(bot: BotLike, status: SnapshotStatus): BotStateSnapshot {
  const connected = status.connected;
  const slots = Array.isArray(bot.inventory?.slots) ? bot.inventory.slots : [];
  const items = slots
    .map((item, index) => itemSummary(item, index))
    .filter((item): item is InventoryItemSummary => item !== null);

  const yaw = connected && typeof bot.entity?.yaw === "number" ? bot.entity.yaw : null;
  const pitch = connected && typeof bot.entity?.pitch === "number" ? bot.entity.pitch : null;
  const yawDegrees = yaw !== null ? normalizeYawDegrees(yaw * 180 / Math.PI) : null;

  return {
    connected,
    username: connected ? String(bot.username ?? status.username) : status.username,
    position: connected && bot.entity?.position ? vector(bot.entity.position) : null,
    yaw,
    pitch,
    yawDegrees,
    pitchDegrees: pitch !== null ? round1(pitch * 180 / Math.PI) : null,
    facing: yawDegrees !== null ? compassFacing(yawDegrees) : null,
    dimension: connected && bot.game?.dimension !== undefined ? String(bot.game.dimension) : null,
    health: connected && typeof bot.health === "number" ? bot.health : null,
    food: connected && typeof bot.food === "number" ? bot.food : null,
    selectedHotbarSlot: connected && typeof bot.quickBarSlot === "number" ? bot.quickBarSlot : null,
    heldItem: connected ? itemSummary(bot.heldItem, null) : null,
    inventory: {
      totalSlots: slots.length,
      usedSlots: items.length,
      items
    },
    crosshairBlock: null
  };
}

function vector(position: { x: number; y: number; z: number }): { x: number; y: number; z: number } {
  return { x: position.x, y: position.y, z: position.z };
}

function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

function normalizeYawDegrees(degrees: number): number {
  // The trailing modulo keeps values that round up to 360.0 at 0.
  return round1(((degrees % 360) + 360) % 360) % 360;
}

// Mineflayer yaw frame: 0 = north (-z), increasing counterclockwise (90 = west).
export function compassFacing(yawDegrees: number): string {
  const directions = ["north", "northwest", "west", "southwest", "south", "southeast", "east", "northeast"];
  return directions[Math.round(normalizeYawDegrees(yawDegrees) / 45) % 8];
}

function itemSummary(item: ItemLike | null | undefined, fallbackSlot: number | null): InventoryItemSummary | null {
  if (!item || typeof item.name !== "string" || typeof item.count !== "number") {
    return null;
  }

  return {
    slot: typeof item.slot === "number" ? item.slot : fallbackSlot,
    name: item.name,
    displayName: typeof item.displayName === "string" ? item.displayName : null,
    count: item.count
  };
}
