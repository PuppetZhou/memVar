import assert from "node:assert/strict";
import test from "node:test";

import { clinicalClassification, clinicalClassificationTone } from "../lib/variant-classification.ts";

test("clinical tone is derived only from an explicit ClinVar classification field", () => {
  assert.equal(clinicalClassification({ ClinicalSignificance: "Likely pathogenic", am_class: "likely_benign" }), "Likely pathogenic");
  assert.equal(clinicalClassification({ clinical_significance: "Benign" }), "Benign");
  assert.equal(clinicalClassification({ classification: "Uncertain significance" }), "Uncertain significance");
  assert.equal(clinicalClassification({ am_class: "likely_pathogenic", ddg: 4.2, genome_screen_sample_count: 80 }), null);
});

test("clinical tones preserve conflict and uncertain states instead of voting", () => {
  assert.equal(clinicalClassificationTone("Conflicting classifications of pathogenicity"), "conflict");
  assert.equal(clinicalClassificationTone("Pathogenic/Likely pathogenic"), "pathogenic");
  assert.equal(clinicalClassificationTone("Likely benign"), "benign");
  assert.equal(clinicalClassificationTone("Uncertain significance"), "uncertain");
  assert.equal(clinicalClassificationTone("risk factor"), "neutral");
  assert.equal(clinicalClassificationTone(null), "neutral");
});
