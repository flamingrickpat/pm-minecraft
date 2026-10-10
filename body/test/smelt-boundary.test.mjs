/** Exercise the wait boundary exposed by the native M3-37 fuel shortage. */
import { readFileSync } from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { smeltStopReason } from '../dist/bot.js';

const captured = JSON.parse(readFileSync(new URL('./fixtures/a13-smelt-timeout.json', import.meta.url)));
test('captured batch uses one log for three input; projected exhausted fuel stops', () => {
  const row = captured.rows.find(row => row.event === 'uncertain');
  assert.equal(row.arguments.input_count, 3);
  assert.equal(row.arguments.fuel, 'birch_log');
  assert.equal(row.arguments.fuel_count, undefined);
  assert.equal(smeltStopReason(16000, 0, 0, 2), 'fuel_exhausted');
  assert.equal(smeltStopReason(1000, 0, 0, 3), null);
  assert.equal(smeltStopReason(16000, 0.5, 0, 2), null);
  assert.equal(smeltStopReason(16000, 0, 1, 2), null);
  assert.equal(smeltStopReason(90000, null, 1, 2), 'smelt_timeout');
});
