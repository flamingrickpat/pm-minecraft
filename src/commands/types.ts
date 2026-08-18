export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface WalkToInput {
  target: Vector3;
  tolerance: number;
  /** Search-region size in chunks (default 3). Validated against the server's max. */
  chunkLimit?: number;
}

export interface BlockCommandOptions {
  walkIntoRange: boolean;
}

export interface MineBlockInput extends BlockCommandOptions {
  block: Vector3;
}

export interface FindBlockInput {
  blockName: string;
  maxDistance: number;
  requireVisible?: boolean;
}

export interface PlaceBlockInput extends BlockCommandOptions {
  referenceBlock: Vector3;
  face: Vector3;
}

export interface JumpPlaceBlockInput extends PlaceBlockInput {}

export interface UseBlockInput extends BlockCommandOptions {
  block: Vector3;
}

export interface AttackEntityInput extends BlockCommandOptions {
  entityId: number;
  /** How many times to re-walk to the entity's current position when it moves out of range (default 3). */
  renavigationCount?: number;
  /** Maximum swings before giving up (default 25). The bot hits until the target is dead/gone. */
  maxHits?: number;
}

export interface ChestInput {
  itemName: string;
  /** Amount to move; defaults to every matching item. */
  count?: number;
}
