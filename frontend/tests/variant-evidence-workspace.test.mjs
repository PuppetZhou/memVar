import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { clinvarRecordUrl, normalizedSource, VARIANT_EVIDENCE_BRANCHES } from "../lib/variant-evidence.ts";
import { columnsForPreset, toggleVariantColumn, VARIANT_OPTIONAL_COLUMNS, variantTableColumnCount } from "../lib/variant-table-view.ts";

const component = () => readFile(new URL("../components/variant-table.tsx", import.meta.url), "utf8");
const api = () => readFile(new URL("../lib/api.ts", import.meta.url), "utf8");

test("variant evidence branches stay source-specific and complete", () => {
  assert.deepEqual(VARIANT_EVIDENCE_BRANCHES.map((branch) => branch.key), ["facts", "effects", "clinvar", "cosmic", "stability", "population"]);
  assert.equal(normalizedSource("ClinVar"), "clinvar");
  assert.equal(normalizedSource("Cosmic"), "cosmic");
  assert.equal(normalizedSource("gnomAD"), "population");
  assert.equal(normalizedSource("AlphaMissense"), "other");
});

test("ClinVar links accept only a stored stable RCV accession", () => {
  assert.equal(clinvarRecordUrl({ RCVaccession: "RCV001937606" }), "https://www.ncbi.nlm.nih.gov/clinvar/RCV001937606/");
  assert.equal(clinvarRecordUrl({ RCVaccession: "not-an-accession" }), null);
  assert.equal(clinvarRecordUrl({ variation_id: "123" }), null);
});

test("column presets preserve two required columns and support custom choices", () => {
  assert.deepEqual(columnsForPreset("balanced"), ["evidence", "predictions", "population"]);
  assert.deepEqual(columnsForPreset("clinical"), ["evidence", "population"]);
  assert.deepEqual(columnsForPreset("protein"), ["evidence", "predictions"]);
  assert.equal(variantTableColumnCount([]), 2);
  assert.equal(variantTableColumnCount(columnsForPreset("balanced")), 5);
  assert.deepEqual(toggleVariantColumn(["evidence", "predictions"], "predictions"), ["evidence"]);
  assert.equal(VARIANT_OPTIONAL_COLUMNS.length, 3);
});

test("summary rows expose direct evidence actions and compact/full limits", async () => {
  const source = await component();
  assert.match(source, /function EvidenceAction/);
  assert.match(source, /branch="stability"/);
  assert.match(source, /normalizedSource\(source\)/);
  assert.match(source, /role="tablist"/);
  assert.match(source, /role="tabpanel"/);
  assert.match(source, /aria-expanded=\{active\}/);
  assert.match(source, /colSpan=\{variantTableColumnCount\(visibleColumns\)\}/);
  assert.match(source, /limit: compact \? "12" : "50"/);
  assert.match(source, /View all variants in the full browser/);
  assert.match(source, /document\.addEventListener\("keydown", closeOnEscape\)/);
  assert.doesNotMatch(source, /tabIndex=\{branch === item\.key \? 0 : -1\}/);
});

test("active evidence branch requests only its own endpoint and caches successful responses", async () => {
  const source = await component();
  assert.match(source, /\/evidence\/\$\{branch\}\?protein_accession=/);
  assert.match(source, /\[accession, variantKey, branch, requestVersion\]/);
  assert.match(source, /evidenceCache\.current\.get\(cacheKey\)/);
  assert.match(source, /evidenceCache\.current\.set\(cacheKey, evidence\)/);
  assert.match(source, /evidenceCache\.current\.clear\(\)/);
  assert.match(source, /branchStateIsCurrent = state\.branch === branch/);
  assert.doesNotMatch(source, /requestVersion === 0 \? evidenceCache/);
  assert.doesNotMatch(source, /VariantDetailResponse/);
  assert.doesNotMatch(source, /\/variants\/\$\{encodeURIComponent\(variantKey\)\}\?protein_accession=/);
});

test("gnomAD action loads a distinct local ancestry chart with explicit unavailable states", async () => {
  const source = await component();
  assert.match(source, /population-frequency/);
  assert.match(source, /gnomAD v4\.1 genetic ancestry frequency/);
  assert.match(source, /Exome, genome, and joint callsets remain independent/);
  assert.match(source, /population-callset-tabs/);
  assert.match(source, /params\.set\("callset", requestedCallset\)/);
  assert.match(source, /group\.label/);
  assert.match(source, /value === null \|\| value === 0/);
  assert.match(source, /missing row is not represented as AF 0/i);
  assert.match(source, /Math\.log10/);
  assert.match(source, /data\.unavailable_fields/);
  assert.match(source, /population-frequency-bars/);
  assert.doesNotMatch(source, /AF = AC \/ AN/);
  assert.doesNotMatch(source, /group\.allele_count|group\.allele_number/);
});

test("summary-first catalog panel preserves distinct-variant and overlap semantics", async () => {
  const [source, apiSource] = await Promise.all([component(), api()]);
  assert.match(apiSource, /export type VariantCatalogSummaryResponse/);
  assert.match(apiSource, /record_grain: "distinct_variant_key"/);
  assert.match(apiSource, /categories_overlap: true/);
  assert.match(source, /function VariantSummaryPanel/);
  assert.match(source, /variants\/summary/);
  assert.match(source, /Protein-scoped variant catalog/);
  assert.match(source, /Protein forms and isoforms/);
  assert.match(source, /summary\.protein_forms\.items\.length\} forms/);
  assert.match(source, /Canonical protein form/);
  assert.match(source, /Consequence terms/);
  assert.match(source, /ClinVar pathogenicity categories/);
  assert.match(source, /categories may overlap; do not add category counts together/);
  assert.match(source, /do not represent a vote, rank, or consensus/);
  assert.match(source, /Variant summary unavailable\. The browser table remains available\./);
  assert.ok(source.indexOf("<VariantSummaryPanel accession={accession} />") < source.indexOf("<form className=\"variant-filters\""));
});
