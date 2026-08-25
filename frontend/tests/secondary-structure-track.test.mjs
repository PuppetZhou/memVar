import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const explorer = readFileSync(new URL("../components/sequence-explorer.tsx", import.meta.url), "utf8");
const api = readFileSync(new URL("../lib/api.ts", import.meta.url), "utf8");
const css = readFileSync(new URL("../app/styles/sequence.css", import.meta.url), "utf8");

test("secondary structure uses the typed UniProt canonical interval contract", () => {
  assert.match(api, /SequenceOverviewSecondaryStructureInterval = SequenceOverviewFeatureInterval/);
  assert.match(api, /feature_type: "Helix" \| "Beta strand" \| "Turn"/);
  assert.match(explorer, /secondary_structure_intervals\.map\(secondaryStructureInterval\)/);
  assert.match(explorer, /secondary_structure_intervals_complete/);
  assert.match(explorer, /secondary_structure_intervals_returned/);
  assert.match(api, /secondary_structure_intervals: number/);
  assert.doesNotMatch(explorer, /pLDDT|plddt/i);
});

test("secondary structure has distinct named shapes and accessible range selection", () => {
  assert.match(explorer, /key: "secondaryStructure", label: "Secondary structure"/);
  assert.match(explorer, /secondary-helix-shape/);
  assert.match(explorer, /secondary-beta-shape/);
  assert.match(explorer, /secondary-turn-shape/);
  assert.match(explorer, /Helix · capsule/);
  assert.match(explorer, /Beta strand · C-terminal arrow/);
  assert.match(explorer, /Turn · loop segment/);
  assert.match(explorer, /UniProt secondary-structure annotation/);
  assert.match(explorer, /function selectItem\(item: SecondaryStructureVisual\)/);
  assert.match(explorer, /onClick=\{\(\) => selectItem\(item\)\}/);
  assert.match(css, /\.secondary-structure-mark \.secondary-helix-shape/);
  assert.match(css, /\.secondary-structure-mark \.secondary-beta-shape/);
  assert.match(css, /\.secondary-structure-mark \.secondary-turn-shape/);
});
