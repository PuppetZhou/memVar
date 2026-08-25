import assert from "node:assert/strict";
import test from "node:test";

import {
  compareContrasts,
  contrastDirection,
  differentialExpressionCounts,
  formatDeNumber,
  representativeTargetResult,
  sortContrasts,
} from "../lib/differential-expression-view.ts";

function contrast(id, results) {
  return {
    contrast_id: id,
    disease_category: "disease",
    disease_condition: "disease",
    tissue: "tissue",
    case_definition: "case",
    control_definition: "control",
    case_n: 10,
    control_n: 10,
    paired: false,
    target_result_total: results.length,
    mapping_status: results.length > 1 ? "multiple_gene_rows_same_symbol" : "unique_gene_row",
    target_results: results,
  };
}

function result(direction, fdr, log2fc, ensembl = "ENSG000001") {
  return { direction, fdr, log2fc, mean_expression: null, ensembl_gene_id: ensembl };
}

test("keeps multiple Ensembl rows as mixed when source directions disagree", () => {
  const mixed = contrast("mixed", [result("up", .002, 2, "ENSG1"), result("down", .001, -3, "ENSG2")]);
  assert.equal(contrastDirection(mixed), "mixed");
});

test("summary counts group source directions without collapsing contrasts", () => {
  const counts = differentialExpressionCounts([
    contrast("up-1", [result("up", .01, 2)]),
    contrast("up-2", [result("up", .02, 1.5)]),
    contrast("down", [result("down", .03, -2)]),
    contrast("mixed", [result("up", .01, 2), result("down", .02, -2)]),
  ]);
  assert.deepEqual(counts, { total: 4, up: 2, down: 1, mixed: 1, notSignificant: 0 });
});

test("NULL statistics remain unavailable and sort after finite source values", () => {
  assert.equal(formatDeNumber(null), "Not available");
  const ordered = sortContrasts([
    contrast("null", [result("up", null, null)]),
    contrast("finite", [result("up", .02, 1.2)]),
  ]);
  assert.deepEqual(ordered.map((item) => item.contrast_id), ["finite", "null"]);
});

test("representative result uses finite |log2FC| before NULL when FDR is tied", () => {
  const selected = representativeTargetResult(contrast("same-fdr", [
    result("up", .01, null, "ENSG_NULL"),
    result("up", .01, 1.5, "ENSG_FINITE"),
  ]));
  assert.equal(selected?.ensembl_gene_id, "ENSG_FINITE");
});

test("sorting uses FDR, absolute effect, then contrast ID as the stable tie-break", () => {
  const ordered = sortContrasts([
    contrast("contrast-c", [result("up", .01, 1.5)]),
    contrast("contrast-b", [result("up", .01, 2)]),
    contrast("contrast-a", [result("up", .01, 2)]),
    contrast("later-fdr", [result("down", .02, -4)]),
  ]);
  assert.deepEqual(ordered.map((item) => item.contrast_id), ["contrast-a", "contrast-b", "contrast-c", "later-fdr"]);
  assert.ok(compareContrasts(ordered[0], ordered[1]) < 0);
});

test("a defined source direction is displayed before a mixed mapping", () => {
  const ordered = sortContrasts([
    contrast("mixed", [result("up", .0001, 4, "ENSG1"), result("down", .0002, -4, "ENSG2")]),
    contrast("defined", [result("down", .02, -1.2)]),
  ]);
  assert.deepEqual(ordered.map((item) => item.contrast_id), ["defined", "mixed"]);
});
