export const controlNames = ["forward", "back", "left", "right", "jump", "sneak", "sprint"] as const;

export type ControlName = (typeof controlNames)[number];
export type ControlStates = Partial<Record<ControlName, boolean>>;

export interface CommandControls {
  applyControlStates(controls: ControlStates): Promise<void> | void;
  clearPhysicalState(): Promise<void> | void;
}
