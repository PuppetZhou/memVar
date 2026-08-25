import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  BODY_REGION_VISUAL_IDS,
  TISSUE_ICON_ASSETS,
  TISSUE_SYSTEMS,
  groupRegionsByTissueSystem,
  tissueIconAssetForKey,
  tissueVisualForRegion,
} from "../lib/tissue-visuals.ts";

const crosswalk = JSON.parse(await readFile(new URL("../../config/anatomy_crosswalk.json", import.meta.url), "utf8"));
const CROSSWALK_IDS = crosswalk.regions.map((region) => region.id);

test("every explicit anatomy crosswalk region has one explicit tissue visual", () => {
  assert.equal(CROSSWALK_IDS.length, 47);
  assert.equal(new Set(TISSUE_SYSTEMS.map((system) => system.id)).size, 12);
  assert.deepEqual([...BODY_REGION_VISUAL_IDS].sort(), [...CROSSWALK_IDS].sort());

  for (const bodyRegionId of CROSSWALK_IDS) {
    const visual = tissueVisualForRegion(bodyRegionId);
    assert.equal(visual.bodyRegionId, bodyRegionId);
    assert.ok(TISSUE_SYSTEMS.some((system) => system.id === visual.id));
  }
});

test("non-anatomical contexts retain their explicit other system and index-only target", () => {
  const other = tissueVisualForRegion("other");
  assert.equal(other.id, "other_non_anatomical");
  assert.equal(other.iconSpecificity, "non_anatomical");
  assert.equal(other.anatomogramTarget, "index_only");
  assert.equal(tissueIconAssetForKey(other.iconKey), null);
});

test("all anatomical display systems use the locally shipped Healthicons outline and filled pair", async () => {
  const manifest = JSON.parse(await readFile(new URL("../public/assets/healthicons/manifest.json", import.meta.url), "utf8"));
  assert.equal(manifest.upstream.repository, "https://github.com/resolvetosavelives/healthicons");
  assert.equal(manifest.upstream.commit, "36887b268d2cb61f8d91622ad459bdf07910c2b0");
  assert.equal(manifest.assets.length, 22);

  for (const system of TISSUE_SYSTEMS) {
    const asset = tissueIconAssetForKey(system.iconKey);
    if (system.id === "other_non_anatomical") {
      assert.equal(asset, null);
      continue;
    }
    assert.ok(asset, `${system.id} has a controlled Healthicons asset`);
    assert.equal(TISSUE_ICON_ASSETS[system.iconKey], asset);
    await Promise.all([asset.outlinePath, asset.filledPath].map(async (assetPath) => {
      const localPath = new URL(`../public${assetPath}`, import.meta.url);
      const svg = await readFile(localPath, "utf8");
      assert.match(svg, /<svg\b/);
      assert.match(svg, /currentColor/);
    }));
  }
});

test("region index groups in stable system order without changing region identity", () => {
  const sample = [
    { body_region_id: "lung" },
    { body_region_id: "heart" },
    { body_region_id: "brain" },
    { body_region_id: "other" },
  ];
  const groups = groupRegionsByTissueSystem(sample);
  assert.deepEqual(groups.map(({ system }) => system.id), ["nervous_sensory", "cardiovascular", "respiratory", "other_non_anatomical"]);
  assert.deepEqual(groups.flatMap(({ regions }) => regions.map((region) => region.body_region_id)).sort(), sample.map((region) => region.body_region_id).sort());
});
