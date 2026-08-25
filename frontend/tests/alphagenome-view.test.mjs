import assert from "node:assert/strict";
import test from "node:test";

import { catalogCoverage, chooseOverviewPreset, mappingStatus, predictionContext, signalRowDescriptor } from "../lib/alphagenome-view.ts";

const candidate = (mapping_status, extra = {}) => ({
  ensembl_gene_id: "ENSG00000146648", gene_symbol: "EGFR", hgnc_id: null, chromosome: "chr7",
  gene_start_1based: 1, gene_end_1based_inclusive: 2, gene_strand: "+", mapping_status,
  mapping_count: mapping_status === "ambiguous" ? 2 : 1, has_prediction: true, display_ready: true, tiles: [], ...extra,
});

const track = (track_id, modality, biosample_name) => ({
  track_id, modality, name: null, assay_title: null, ontology_curie: null, biosample_name,
  biosample_type: null, biosample_life_stage: null, gtex_tissue: null, strand: null,
  histone_mark: null, data_source: "local", display_unit: "prediction",
});

test("mapping states retain exact, ambiguous, and unavailable distinctions", () => {
  assert.match(mappingStatus(candidate("exact")).title, /Exact/);
  assert.match(mappingStatus(candidate("ambiguous")).detail, /Choose a gene/);
  assert.match(mappingStatus(candidate("no_prediction")).title, /without local prediction/);
  assert.match(mappingStatus(candidate("no_ensembl")).title, /No Ensembl/);
});

test("coverage labels describe the local catalog rather than a gene-specific count", () => {
  const coverage = catalogCoverage({ modality_track_counts: { rna_seq: 113, contact_maps: 2 } });
  assert.deepEqual(coverage, [
    { modality: "rna_seq", label: "RNA-seq", count: 113 },
    { modality: "contact_maps", label: "3D contact", count: 2 },
  ]);
});

test("overview preset is deterministic metadata ordering, not biological significance", () => {
  const tracks = [track("atac:001", "atac", "Zebra"), track("rna_seq:010", "rna_seq", "Zulu"), track("rna_seq:002", "rna_seq", "Alpha")];
  assert.equal(chooseOverviewPreset(tracks)?.track_id, "rna_seq:002");
  assert.equal(chooseOverviewPreset([...tracks].reverse())?.track_id, "rna_seq:002");
});

test("signal row descriptor persists assay context and unit outside a tooltip", () => {
  assert.deepEqual(signalRowDescriptor({ ...track("rna_seq:002", "rna_seq", "Alpha"), assay_title: "RNA profiling", display_unit: "predicted signal" }), {
    modality: "RNA-seq", biosample: "Alpha", track: "RNA profiling", unit: "predicted signal",
  });
});

test("reference-sequence context cannot be presented as a variant effect", () => {
  const context = predictionContext("reference_sequence_tracks", false);
  assert.equal(context.title, "Reference-sequence model prediction");
  assert.match(context.caveat, /GRCh38 reference sequence/);
  assert.match(context.caveat, /No REF\/ALT comparison or variant-effect score/);
});
