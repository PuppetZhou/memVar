import assert from "node:assert/strict";
import test from "node:test";

import {
  fullLengthPosition,
  navigatorGeometry,
  panViewport,
  resizeViewport,
} from "../lib/sequence-navigator.ts";

test("full rail retains canonical endpoints after narrowing", () => {
  assert.equal(fullLengthPosition(100, 100, 800, 1210), 1);
  assert.equal(fullLengthPosition(900, 100, 800, 1210), 1210);
  assert.equal(fullLengthPosition(500, 100, 800, 1210), 606);
});

test("EGFR 300-500 thumb uses the full 1210-residue geometry", () => {
  const geometry = navigatorGeometry({ start: 300, end: 500 }, 1210);
  assert.ok(Math.abs(geometry.leftPercent - 24.71) < 0.02);
  assert.ok(Math.abs(geometry.widthPercent - 16.61) < 0.02);
});

test("handles can restore a narrowed viewport to full length", () => {
  const left = resizeViewport({ start: 300, end: 500 }, "start", 1, 1210, 2);
  assert.deepEqual(left, { start: 1, end: 500 });
  const full = resizeViewport(left, "end", 1210, 1210, 2);
  assert.deepEqual(full, { start: 1, end: 1210 });
});

test("window pan preserves span and clamps to full-sequence bounds", () => {
  assert.deepEqual(panViewport({ start: 300, end: 500 }, -1000, 1210), { start: 1, end: 201 });
  assert.deepEqual(panViewport({ start: 300, end: 500 }, 1000, 1210), { start: 1010, end: 1210 });
});
