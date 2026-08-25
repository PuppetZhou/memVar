import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const component = (name) => readFile(new URL(`../components/${name}`, import.meta.url), "utf8");

test("structure viewer keeps a Mol* molecular surface and offers a separate pLDDT mode", async () => {
  const source = await component("structure-viewer.tsx");
  assert.match(source, /import\("molstar\/lib\/mol-plugin-ui"\)/);
  assert.match(source, /createPluginUI/);
  assert.match(source, /representationPreset:\s*"coarse-surface"/);
  assert.match(source, /globalName:\s*"plddt-confidence"/);
  assert.match(source, /sequence-variant-density/);
  assert.match(source, /pLDDT molecular surface/);
  assert.match(source, /managers\.structure\.focus\.setFromLoci\(loci\)/);
  assert.match(source, /ungzip\(SyncRuntimeContext, compressed\)/);
  assert.doesNotMatch(source, /3dmol|cartoon:/i);
});

test("anatomy illustration has no tissue marker overlay", async () => {
  const source = await component("anatomy-navigator.tsx");
  assert.doesNotMatch(source, /ANATOMY_LANDMARK/);
  assert.doesNotMatch(source, /anatomy-tissue-point/);
  assert.match(source, /orientation background only/i);
  assert.match(source, /tissue index/i);
});

test("anatomy region index uses the explicit tissue visual system rather than map markers", async () => {
  const source = await component("anatomy-navigator.tsx");
  assert.match(source, /groupRegionsByTissueSystem/);
  assert.match(source, /TissueSystemIcon/);
  assert.match(source, /grouped by body system/);
});
