import assert from "node:assert/strict";
import test from "node:test";

import { allCovalentPairsAreDisulfide, covalentBondLabel, routeCovalentPairLanes } from "../lib/covalent-bonds.ts";

test("explicit UniProt disulfide bond is displayed with its S—S notation", () => {
  assert.equal(covalentBondLabel("Disulfide bond"), "Disulfide bond (S—S)");
});

test("other supplied types and missing types are not guessed", () => {
  assert.equal(covalentBondLabel("Thioether bond"), "Thioether bond");
  assert.equal(covalentBondLabel(null), "Covalent bond (type not specified)");
});

test("disulfide pairs may share one collection label only when every type is explicit", () => {
  assert.equal(allCovalentPairsAreDisulfide([
    { start_endpoint: 25, end_endpoint: 80, feature_type: "Disulfide bond" },
    { start_endpoint: 40, end_endpoint: 64, feature_type: " disulfide bond " },
  ]), true);
  assert.equal(allCovalentPairsAreDisulfide([
    { start_endpoint: 25, end_endpoint: 80, feature_type: "Disulfide bond" },
    { start_endpoint: 40, end_endpoint: 64, feature_type: null },
  ]), false);
  assert.equal(allCovalentPairsAreDisulfide([]), false);
});

test("overlapping covalent intervals are routed into staggered lanes", () => {
  assert.deepEqual(routeCovalentPairLanes([
    { start_endpoint: 10, end_endpoint: 90 },
    { start_endpoint: 20, end_endpoint: 80 },
    { start_endpoint: 100, end_endpoint: 120 },
  ]), [0, 1, 0]);
});

test("covalent lane routing is deterministic and bounded", () => {
  assert.deepEqual(routeCovalentPairLanes([
    { start_endpoint: 1, end_endpoint: 100 },
    { start_endpoint: 2, end_endpoint: 99 },
    { start_endpoint: 3, end_endpoint: 98 },
  ], 2), [0, 1, 1]);
  assert.throws(() => routeCovalentPairLanes([], 0), /positive integer/);
});
