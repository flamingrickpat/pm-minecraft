export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface WalkToInput {
  target: Vector3;
  tolerance: number;
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
