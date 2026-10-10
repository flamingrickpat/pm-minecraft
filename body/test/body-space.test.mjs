/** Check support boundaries using the actual M3-34 player pose. */
import { readFileSync } from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { underPlayerSupport } from '../dist/bot.js';

const captured = JSON.parse(readFileSync(new URL('./fixtures/a13-body-space.json', import.meta.url)));
test('actual below-body dig is refused; a projected adjacent side remains available', () => {
  assert.equal(underPlayerSupport(captured.feet, captured.dug_below), true);
  assert.equal(underPlayerSupport(captured.feet, { ...captured.dug_below, x: captured.dug_below.x + 2 }), false);
  assert.equal(underPlayerSupport(captured.feet, { ...captured.dug_below, y: captured.feet.y }), false);
});
test('a projected edge protects both touched support columns', () => {
  const edge = { ...captured.feet, x: -20.05 };
  assert.equal(underPlayerSupport(edge, { ...captured.dug_below, x: -20 }), true);
  assert.equal(underPlayerSupport(edge, { ...captured.dug_below, x: -21 }), true);
});
