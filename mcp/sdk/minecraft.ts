export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface InventoryItem {
  name: string;
  count: number;
}

export interface MinecraftObservation {
  capturedAt: string;
  player: {
    username: string;
    position: Vector3;
    blockPosition: Vector3;
    yawDegrees: number;
    pitchDegrees: number;
    facing: string;
    health: number;
    food: number;
    oxygenLevel: number;
    [key: string]: unknown;
  };
  world: {
    dimension: string;
    biome: string | null;
    timeOfDay: number;
    isDay: boolean;
    isRaining: boolean;
    [key: string]: unknown;
  };
  inventory: {
    selectedHotbarSlot: number;
    heldItem: InventoryItem | null;
    items: InventoryItem[];
    emptySlots: number;
    [key: string]: unknown;
  };
  surroundings: {
    nearbyBlocks: Array<{
      name: string;
      count: number;
      nearest: Vector3;
      distance: number;
    }>;
    nearbyEntities: Array<{
      name: string;
      kind: string;
      position: Vector3;
      distance: number;
    }>;
    [key: string]: unknown;
  };
}

export interface MinecraftResponse {
  ok?: boolean;
  status?: string;
  reason?: string;
  message?: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface MinecraftContext {
  username: string;
  bodyUrl: string;
  agentHome: string;
  executionId: string;
  call(action: string, parameters?: Record<string, unknown>, timeoutSeconds?: number): Promise<MinecraftResponse>;
  observe(): Promise<MinecraftObservation>;
  findBlock(blockName: string, maxDistance?: number): Promise<MinecraftResponse>;
  walkTo(target: Vector3, tolerance?: number, timeoutSeconds?: number): Promise<MinecraftResponse>;
  mineBlock(block: Vector3, walkIntoRange?: boolean, timeoutSeconds?: number): Promise<MinecraftResponse>;
  placeBlock(referenceBlock: Vector3, face: Vector3, walkIntoRange?: boolean, timeoutSeconds?: number): Promise<MinecraftResponse>;
  useBlock(block: Vector3, walkIntoRange?: boolean, timeoutSeconds?: number): Promise<MinecraftResponse>;
  equip(itemName: string): Promise<MinecraftResponse>;
  craft(itemName: string, repetitions?: number): Promise<MinecraftResponse>;
  smelt(inputItemName: string, inputCount: number, fuelItemName: string, fuelCount?: number, timeoutSeconds?: number): Promise<MinecraftResponse>;
  rotate(yaw: number, pitch?: number): Promise<MinecraftResponse>;
  stop(): Promise<MinecraftResponse>;
  /** Send ordinary chat. Only communication and informational slash commands are accepted. */
  chat(text: string): Promise<MinecraftResponse>;
  sleep(milliseconds: number): Promise<void>;
}

export type SkillEntrypoint = (context: MinecraftContext, input: unknown) => Promise<unknown>;

export interface SkillResult {
  ok: boolean;
  startedAt: string;
  finishedAt: string;
  value?: unknown;
  error?: { name: string; message: string; stack: string };
}

export function itemCount(observation: MinecraftObservation, itemName: string): number {
  return observation.inventory.items.find((item) => item.name === itemName)?.count ?? 0;
}

export function requireSuccessful(response: MinecraftResponse, operation: string): MinecraftResponse {
  if (response.ok !== true) {
    throw new Error(`${operation} failed: ${response.reason ?? response.status ?? "unknown"}: ${response.message ?? JSON.stringify(response)}`);
  }
  return response;
}

export function responseBlock(response: MinecraftResponse): Vector3 {
  const block = response.data?.block;
  if (!block || typeof block !== "object") {
    throw new Error(`Find-block response has no data.block: ${JSON.stringify(response)}`);
  }
  const value = block as Record<string, unknown>;
  if (typeof value.x !== "number" || typeof value.y !== "number" || typeof value.z !== "number") {
    throw new Error(`Find-block response contains an invalid position: ${JSON.stringify(block)}`);
  }
  return { x: value.x, y: value.y, z: value.z };
}
