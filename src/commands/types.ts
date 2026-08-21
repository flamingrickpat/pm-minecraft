export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

/** walk_to_visible: approximate target, snapped to the nearest standable cell within a small sphere. */
export interface WalkToVisibleInput {
  target: Vector3;
  tolerance?: number;
  /** Search-region size in chunks. Defaults to the server's maximum; validated against it. */
  chunkLimit?: number;
}

/** walk_to_surface: sky-scan the surface at (x, z), spiralling outward when the exact column is not standable, then walk there over any number of internal hops. */
export interface WalkToSurfaceInput {
  x: number;
  z: number;
  /** Success radius around the requested point (default 1.5). */
  tolerance?: number;
}

/** walk_to_exact: precise coordinates known (or saved) to be standable; exact cell first, snap only within 3 blocks. */
export interface WalkToExactInput {
  target: Vector3;
  /** 3D success radius around the target cell (default 1). */
  tolerance?: number;
}

export interface BlockCommandOptions {
  /** Defaults to true: the body walks adjacent before acting. */
  walkIntoRange?: boolean;
}

export interface MineBlockInput extends BlockCommandOptions {
  block: Vector3;
}

export interface FindBlockInput {
  /** Exact registry name, or a glob pattern like "*log*" matching any wood. */
  blockName: string;
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
}

export interface ChestInput {
  itemName: string;
  /** Amount to move; defaults to every matching item. */
  count?: number;
}
