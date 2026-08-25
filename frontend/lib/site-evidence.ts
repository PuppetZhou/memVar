export type SiteEvidenceSummary = {
  identity: {
    uniprot_accession: string;
    sequence_id: string;
    sequence_version: number | null;
    position: number;
    reference_residue: string;
    coordinate_basis: "canonical_1_based";
  };
  conservation: {
    residue: string | null;
    consensus_aa: string | null;
    wt_frequency: number | null;
    entropy_conservation: number | null;
    jsd_conservation: number | null;
    gap_frequency: number | null;
    occupancy: number | null;
    neff_site: number | null;
    neff_protein: number | null;
    alignment_scope: string | null;
    confidence: string | null;
  } | null;
  overlaps: {
    topology: SiteFeatureOverlap[];
    functional: SiteFeatureOverlap[];
    pfam: SitePfamOverlap[];
    ptm: SitePtmOverlap[];
  };
  stability: SiteStability;
  covalent_pairs: SiteCovalentPair[];
  variants: SiteVariants;
  provenance: Record<string, string>;
};

export type SiteFeatureOverlap = { feature_type: string; description: string | null; start: number; end: number; source: string };
export type SitePfamOverlap = { pfam_accession: string; pfam_id: string | null; description: string | null; pfam_type: string | null; start: number; end: number };
export type SitePtmOverlap = { ptm_type: string; residue: string | null; record_count: number; pmids: string[]; evidence_count: number | null };
export type StabilityDirection = "predicted_stabilizing" | "small_predicted_change" | "predicted_destabilizing";
export type SiteStability = {
  available: boolean;
  source: "ThermoMPNN";
  model_name: string | null;
  unit: "kcal/mol";
  distinct_substitution_count: number;
  genomic_variant_count: number;
  ddg_min: number | null;
  ddg_q25: number | null;
  ddg_median: number | null;
  ddg_q75: number | null;
  ddg_max: number | null;
  stabilizing_count: number;
  small_change_count: number;
  destabilizing_count: number;
  substitutions: { substitution: string; ddg: number; direction: StabilityDirection; genomic_variant_count: number; pdb_name: string }[];
  interpretation: string;
};
export type SiteCovalentPair = {
  pair_id: string;
  feature_type: string;
  start_endpoint: number;
  end_endpoint: number;
  description: string | null;
  evidence: { evidence_code: string | null; source: string | null; identifier: string | null }[];
};
export type SiteVariants = {
  total: number;
  clinvar_plp_count: number;
  source_counts: Record<string, number>;
  preview: { variant_key: string; hgvsp: string | null; consequence: string | null; source_badges: string[]; has_clinvar_plp_evidence: boolean }[];
  preview_limit: number;
  showing: number;
  has_more: boolean;
  anchor_semantics: string;
  clinvar_plp_semantics: string;
};

export function formatDdg(value: number | null, digits = 2): string {
  return value === null || !Number.isFinite(value) ? "Not predicted" : `${value >= 0 ? "+" : ""}${value.toFixed(digits)} kcal/mol`;
}

export function stabilityDirectionLabel(direction: StabilityDirection): string {
  if (direction === "predicted_stabilizing") return "Predicted stabilizing";
  if (direction === "predicted_destabilizing") return "Predicted destabilizing";
  return "Small predicted change";
}

export function percentage(value: number | null): string {
  return value === null || !Number.isFinite(value) ? "—" : `${(value * 100).toFixed(1)}%`;
}

export function partnerFor(pair: Pick<SiteCovalentPair, "start_endpoint" | "end_endpoint">, position: number): number {
  return pair.start_endpoint === position ? pair.end_endpoint : pair.start_endpoint;
}
