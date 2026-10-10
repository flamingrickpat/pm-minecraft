/** Check descent permission against captured real-server geometry and poses. */
import { readFileSync } from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { staircaseFloorHazard, staircaseStepReached } from '../dist/bot.js';

const captured = JSON.parse(readFileSync(new URL('./fixtures/a13-staircase-boundary.json', import.meta.url)));

test('actual solid stone permits support; actual air cannot supply a floor', () => {
  assert.equal(staircaseFloorHazard(captured.floor), null);
  assert.equal(staircaseFloorHazard(captured.air), 'unsupported_floor');
  assert.equal(staircaseFloorHazard(null), 'unknown_floor');
});

test('actual twenty-nine-block drop cannot count as one descent step', () => {
  assert.equal(staircaseStepReached(captured.start, captured.projected_target,
    captured.reported_end, true, captured.death_count_before, captured.death_count_before), false);
});

test('actual changed death counter rejects even a projected target arrival', () => {
  assert.equal(staircaseStepReached(captured.start, captured.projected_target,
    captured.projected_target, true, captured.death_count_before, captured.death_count_after), false);
});

test('one grounded step is permitted as a contract projection', () => {
  assert.equal(staircaseStepReached(captured.start, captured.projected_target,
    captured.projected_target, true, captured.death_count_before, captured.death_count_before), true);
  assert.equal(staircaseStepReached(captured.start, captured.projected_target,
    captured.projected_target, false, captured.death_count_before, captured.death_count_before), false);
});
