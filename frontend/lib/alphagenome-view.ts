import type { AlphaGenomeGeneCandidate, AlphaGenomeSummaryResponse, AlphaGenomeTrack } from "./api";

export const ALPHAGENOME_MODALITIES = ["rna_seq", "cage", "procap", "atac", "chip_histone", "splice_sites", "splice_site_usage", "splice_junctions", "contact_maps"] as const;

export const ALPHAGENOME_MODALITY_LABELS: Record<string, string> = {
  rna_seq: "RNA-seq",
  cage: "CAGE",
  procap: "PRO-cap",
  atac: "ATAC-seq",
  chip_histone: "Histone ChIP",
  splice_sites: "Splice sites",
  splice_site_usage: "Splice usage",
  splice_junctions: "Junctions",
  contact_maps: "3D contact",
};

const modalityIndex: Map<string, number> = new Map(ALPHAGENOME_MODALITIES.map((modality, index) => [modality, index]));

export function biosampleLabel(track: AlphaGenomeTrack) {
  return track.biosample_name || track.gtex_tissue || track.ontology_curie || "Unspecified biosample";
}

export function trackDisplayLabel(track: AlphaGenomeTrack) {
  const details = [track.assay_title || track.name, track.histone_mark, track.strand && track.strand !== "." ? `${track.strand} strand` : null].filter(Boolean);
  return details.length ? details.join(" · ") : track.track_id;
}

export function signalRowDescriptor(track: AlphaGenomeTrack) {
  return {
    modality: ALPHAGENOME_MODALITY_LABELS[track.modality] ?? track.modality,
    biosample: biosampleLabel(track),
    track: trackDisplayLabel(track),
    unit: track.display_unit,
  };
}

/** The M14 response currently permits only reference-sequence track wording. */
export function predictionContext(predictionKind: AlphaGenomeSummaryResponse["prediction_kind"], hasVariantEffectScores: boolean) {
  if (predictionKind !== "reference_sequence_tracks") {
    return {
      title: "Model prediction",
      caveat: "Prediction type is not described by this response.",
    };
  }
  return {
    title: "Reference-sequence model prediction",
    caveat: hasVariantEffectScores
      ? "This response includes model scores; interpret each source-defined score in its own context."
      : "Predictions are calculated on the GRCh38 reference sequence. No REF/ALT comparison or variant-effect score is available.",
  };
}

export function mappingStatus(candidate: AlphaGenomeGeneCandidate) {
  switch (candidate.mapping_status) {
    case "exact":
      return { title: "Exact Ensembl mapping", detail: "One stable Ensembl gene mapping is available for this canonical protein." };
    case "ambiguous":
      return { title: "Multiple Ensembl mappings", detail: `${candidate.mapping_count} stable Ensembl gene candidates are retained. Choose a gene before comparing tracks.` };
    case "no_prediction":
      return { title: "Mapped, without local prediction", detail: "A stable Ensembl mapping is available, but no local AlphaGenome prediction was generated for it." };
    case "no_ensembl":
      return { title: "No Ensembl mapping", detail: "No stable Ensembl gene mapping is available for this canonical protein." };
  }
}

export function preferredCandidate(candidates: AlphaGenomeGeneCandidate[]) {
  return [...candidates].sort((left, right) => {
    const leftRank = left.mapping_status === "exact" ? 0 : left.mapping_status === "ambiguous" ? 1 : 2;
    const rightRank = right.mapping_status === "exact" ? 0 : right.mapping_status === "ambiguous" ? 1 : 2;
    return leftRank - rightRank || Number(right.display_ready) - Number(left.display_ready) || (left.ensembl_gene_id ?? "").localeCompare(right.ensembl_gene_id ?? "");
  })[0];
}

export function catalogCoverage(summary: AlphaGenomeSummaryResponse) {
  return ALPHAGENOME_MODALITIES
    .map((modality) => ({ modality, label: ALPHAGENOME_MODALITY_LABELS[modality], count: summary.modality_track_counts[modality] ?? 0 }))
    .filter((item) => item.count > 0);
}

/**
 * This is a navigation default, not a biological ranking. It has no signal,
 * tissue, expression, or gene-specific priority input: only stable catalogue
 * metadata are used to make repeated visits reproducible.
 */
export function chooseOverviewPreset(tracks: AlphaGenomeTrack[]) {
  return [...tracks].sort((left, right) => {
    const modalityOrder = (modalityIndex.get(left.modality) ?? Number.MAX_SAFE_INTEGER) - (modalityIndex.get(right.modality) ?? Number.MAX_SAFE_INTEGER);
    return modalityOrder || biosampleLabel(left).localeCompare(biosampleLabel(right)) || left.track_id.localeCompare(right.track_id);
  })[0] ?? null;
}

export function formatLocus(candidate: AlphaGenomeGeneCandidate) {
  if (!candidate.chromosome || candidate.gene_start_1based === null || candidate.gene_end_1based_inclusive === null) return "GRCh38 locus unavailable";
  return `${candidate.chromosome}:${candidate.gene_start_1based.toLocaleString()}–${candidate.gene_end_1based_inclusive.toLocaleString()} · ${candidate.gene_strand ?? "?"} strand`;
}
