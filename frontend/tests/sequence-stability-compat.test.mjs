import assert from "node:assert/strict";
import test from "node:test";

import { smoothWavePath, stabilityColor, stabilityOverviewFrom } from "../lib/sequence-stability.ts";

test("stability palette preserves blue neutral red semantics", () => {
  assert.equal(stabilityColor(-0.5), "#1B75BC");
  assert.equal(stabilityColor(0), "#7A838C");
  assert.equal(stabilityColor(0.5), "#D94949");
});

test("stability path is continuous cubic geometry without point glyphs", () => {
  assert.equal(
    smoothWavePath([{ x: 0, y: 50 }, { x: 100, y: 25 }, { x: 200, y: 75 }]),
    "M 0 50 C 50 50, 50 25, 100 25 C 150 25, 150 75, 200 75",
  );
});

test("legacy sequence overview without M15 fields degrades as unavailable", () => {
  const stability = stabilityOverviewFrom({});

  assert.equal(stability.available, false);
  assert.deepEqual(stability.bins, []);
  assert.deepEqual(stability.totals, {
    predicted_variants: 0,
    canonical_sites: 0,
    distinct_substitutions: 0,
  });
});

test("M15 sequence overview preserves an empty but available stability branch", () => {
  const stability = stabilityOverviewFrom({
    stability_bins: [],
    stability_totals: {
      predicted_variants: 0,
      canonical_sites: 0,
      distinct_substitutions: 0,
    },
  });

  assert.equal(stability.available, true);
  assert.deepEqual(stability.bins, []);
  assert.equal(stability.totals.distinct_substitutions, 0);
});
