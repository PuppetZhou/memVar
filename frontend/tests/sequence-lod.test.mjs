import assert from "node:assert/strict";
import test from "node:test";

import {
  aggregatePtmMarks,
  aggregateStabilityMarks,
  aggregateVariantMarks,
  sequenceMarkBudget,
  splitCanonicalRange,
} from "../lib/sequence-lod.ts";

test("overview budgets stay within the 48–96 screen-space contract", () => {
  assert.equal(sequenceMarkBudget(240), 48);
  assert.equal(sequenceMarkBudget(1280), 64);
  assert.equal(sequenceMarkBudget(3000), 96);
});

test("canonical bins are contiguous, 1-based, and cover the exact range", () => {
  const marks = splitCanonicalRange({ start: 7, end: 25 }, 6);
  assert.equal(marks[0].start, 7);
  assert.equal(marks.at(-1)?.end, 25);
  assert.ok(marks.every((mark, index) => index === 0 || marks[index - 1].end + 1 === mark.start));
});

test("variant aggregation preserves counts and strict ClinVar P/LP presence counts", () => {
  const marks = aggregateVariantMarks([2, 0, 4, 1, 0, 3], [1, 0, 9, 0, 0, 2], { start: 1, end: 6 }, 3);
  assert.equal(marks.reduce((total, mark) => total + mark.totalCount, 0), 10);
  assert.equal(marks.reduce((total, mark) => total + mark.clinvarPlpCount, 0), 7);
  assert.equal(marks.reduce((total, mark) => total + mark.occupiedSiteCount, 0), 4);
  assert.ok(marks.every((mark) => mark.clinvarPlpCount <= mark.totalCount));
});

test("PTM aggregation preserves record counts, occupied sites, and raw types", () => {
  const marks = aggregatePtmMarks([
    { position: 2, totalCount: 3, types: [{ ptmType: "Phosphorylation", count: 2 }, { ptmType: "Glycosylation", count: 1 }] },
    { position: 6, totalCount: 2, types: [{ ptmType: "Phosphorylation", count: 2 }] },
  ], { start: 1, end: 8 }, 2);
  assert.equal(marks.reduce((total, mark) => total + mark.totalCount, 0), 5);
  assert.equal(marks.reduce((total, mark) => total + mark.occupiedSiteCount, 0), 2);
  assert.deepEqual(marks.flatMap((mark) => mark.types).reduce((values, item) => ({ ...values, [item.ptmType]: (values[item.ptmType] ?? 0) + item.count }), {}), { Phosphorylation: 4, Glycosylation: 1 });
});

test("stability summaries preserve observation/substitution counts and leave missing marks null", () => {
  const marks = aggregateStabilityMarks([
    { start: 1, end: 2, observationCount: 2, distinctSubstitutionCount: 2, min: -2, q25: -1, median: -.5, q75: 0, max: .5 },
    { start: 7, end: 8, observationCount: 3, distinctSubstitutionCount: 3, min: .1, q25: .2, median: .4, q75: .8, max: 1.1 },
  ], { start: 1, end: 8 }, 4);
  assert.equal(marks.reduce((total, mark) => total + mark.observationCount, 0), 5);
  assert.equal(marks.reduce((total, mark) => total + mark.distinctSubstitutionCount, 0), 5);
  assert.equal(marks[1].median, null);
  assert.equal(marks[3].median, .4);
});
