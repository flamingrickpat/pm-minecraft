/** Compare activation labels with independently observed real door states. */
import { readFileSync } from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { confirmedToggleAction } from '../dist/bot.js';

const captured = JSON.parse(readFileSync(new URL('./fixtures/a13-block-activation.json', import.meta.url)));
test('confirmed activation agrees with the real server and rejects the old prediction', () => {
  const failed = captured.failed_activation.result;
  assert.equal(failed.action, 'door_opened');
  assert.equal(failed.window.kind, 'chest');
  assert.equal(failed.window.slots.length, 3);
  const oracle = captured.independent_closed_door.results;
  assert.equal(oracle[0].result, '');
  assert.notEqual(oracle[1].result, '');
  // The old label inferred a closed pre-state. The server still observed closed.
  assert.equal(confirmedToggleAction('door', false, false), null);
  const activations = captured.confirmed_probe.calls.filter(row => row.tool === 'minecraft_use_block' && row.result.open_before !== null);
  assert.equal(activations.length, 2);
  for (const {result} of activations) {
    assert.equal(confirmedToggleAction('door', result.open_before, result.open_after), result.action);
    assert.notEqual(result.open_before, result.open_after);
    assert.equal(result.window, null);
  }
  assert.equal(captured.confirmed_probe.checks.first_toggle_confirmed, true);
  assert.equal(captured.confirmed_probe.checks.second_toggle_confirmed, true);
});
