export type SearchCandidate = {
  uniprot_accession: string;
  gene_symbol: string | null;
  protein_name: string | null;
  entry_name: string | null;
  membrane_class: string | null;
  canonical_length: number | null;
  match: { text: string; identifier_type: string; identifier_database: string | null; kind: "exact" | "prefix" | "token" };
};

export type SearchResponse = {
  query: string;
  items: SearchCandidate[];
  next_cursor: null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: Record<string, unknown>;
  ambiguity: boolean;
  resolution: "no_match" | "direct_candidate" | "candidate_selection";
};

export type Identifier = {
  isoform_id: string | null;
  identifier_type: string;
  identifier_database: string | null;
  identifier_full: string | null;
  identifier_base: string | null;
  identifier_version: number | null;
  alias_type: string | null;
  identifier_label: string | null;
};

export type ProteinOverviewResponse = {
  uniprot_accession: string;
  entry_name: string | null;
  protein_name: string | null;
  gene_symbol: string | null;
  canonical_length: number | null;
  protein_existence: string | null;
  annotation_score: number | null;
  membrane_class: string | null;
  all_class_labels: string[];
  transmembrane_count: number | null;
  intramembrane_count: number | null;
  lipidation_count: number | null;
  lipidation_anchor_match_count: number | null;
  canonical_sequence: { sequence_id: string; length: number; sequence_version: number | null };
  identifiers: Identifier[];
  annotation_summary: {
    go: { molecular_function: string[]; biological_process: string[]; cellular_component: string[] } | null;
    reactome: { pathway_id: string | null; pathway_name: string | null; pathway_url: string | null; evidence_codes: string[]; evidence_count: number | null }[];
    reactome_total: number;
    locations: { sequence_version: number | null; location_id: string | null; location_name: string | null; topology_id: string | null; topology_name: string | null; orientation_id: string | null; orientation_name: string | null }[];
    locations_total: number;
    item_limit: number;
  };
};

export type GoAspect = "MF" | "BP" | "CC";

export type GoEvidenceCodeCount = {
  evidence_code: string;
  annotation_count: number;
};

export type GoAspectCount = {
  aspect: GoAspect;
  term_count: number;
  annotation_count: number;
  reference_count: number;
};

export type GoTermSummary = {
  go_id: string;
  go_term_name: string;
  aspect: GoAspect;
  go_namespace: string | null;
  annotation_count: number;
  reference_count: number;
  evidence_codes: GoEvidenceCodeCount[];
};

export type GoTermsResponse = {
  uniprot_accession: string;
  provenance: {
    source_id: "goa_annotation";
    display_name: string;
    layer: string;
    source_release: string | null;
    record_grain: string;
    caveat: string | null;
  };
  items: GoTermSummary[];
  next_cursor: string | null;
  total_or_estimate: { value: number; kind: "exact" };
  annotation_count: number;
  aspect_counts: GoAspectCount[];
  applied_filters: {
    aspect: GoAspect | null;
    evidence_code: string | null;
    q: string | null;
    include_negated: boolean;
    limit: number;
    default_excludes_negated: boolean;
  };
};

export type GoEvidenceItem = {
  go_evidence_id: number;
  go_id: string;
  go_term_name: string;
  aspect: GoAspect;
  go_namespace: string | null;
  qualifier: string | null;
  is_negated: boolean | null;
  evidence_code: string | null;
  reference_id: string | null;
  with_from: string | null;
  assigned_by: string | null;
  annotation_extension: string | null;
  annotation_date: string | null;
};

export type GoEvidenceResponse = {
  uniprot_accession: string;
  go_id: string;
  items: GoEvidenceItem[];
  next_cursor: string | null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: {
    go_id: string;
    include_negated: boolean;
    limit: number;
    default_excludes_negated: boolean;
  };
};

export type AlphaFoldStructureFragment = {
  fragment_number: number;
  fragment_label: string;
  filename: string;
  canonical_start: number | null;
  canonical_end: number | null;
  compressed_bytes: number;
  uncompressed_bytes: number;
  content_url: string;
  download_url: string;
};

export type AlphaFoldStructuresResponse = {
  uniprot_accession: string;
  availability: "available" | "unavailable";
  source: "AlphaFold DB";
  model_version: number;
  fragment_total: number;
  fragments: AlphaFoldStructureFragment[];
};

export type AlphaGenomeTile = {
  tile_id: string;
  tile_index: number;
  chromosome: string;
  window_start_0based: number;
  window_end_0based: number;
  core_start_0based: number;
  core_end_0based: number;
  display_ready: boolean;
};

export type AlphaGenomeGeneCandidate = {
  ensembl_gene_id: string | null;
  gene_symbol: string | null;
  hgnc_id: string | null;
  chromosome: string | null;
  gene_start_1based: number | null;
  gene_end_1based_inclusive: number | null;
  gene_strand: string | null;
  mapping_status: "exact" | "ambiguous" | "no_prediction" | "no_ensembl";
  mapping_count: number;
  has_prediction: boolean;
  display_ready: boolean;
  tiles: AlphaGenomeTile[];
};

export type AlphaGenomeSummaryResponse = {
  uniprot_accession: string;
  availability: "available" | "preparing" | "unavailable";
  source: "AlphaGenome";
  prediction_kind: "reference_sequence_tracks";
  genome_build: "GRCh38";
  coordinate_convention: "model_window_0_based_half_open";
  local_output_subset: true;
  missing_official_modalities: string[];
  has_variant_effect_scores: false;
  modality_track_counts: Record<string, number>;
  candidates: AlphaGenomeGeneCandidate[];
  notice: string;
};

export type AlphaGenomeTrack = {
  track_id: string;
  modality: string;
  name: string | null;
  assay_title: string | null;
  ontology_curie: string | null;
  biosample_name: string | null;
  biosample_type: string | null;
  biosample_life_stage: string | null;
  gtex_tissue: string | null;
  strand: string | null;
  histone_mark: string | null;
  data_source: string | null;
  display_unit: string;
};

export type AlphaGenomeTrackCatalogResponse = {
  uniprot_accession: string;
  ensembl_gene_id: string;
  modality: string;
  tracks: AlphaGenomeTrack[];
  total: number;
};

export type AlphaGenomeSignalResponse = {
  uniprot_accession: string;
  ensembl_gene_id: string;
  tile_id: string;
  track: AlphaGenomeTrack;
  genome_build: "GRCh38";
  coordinate_convention: "0_based_half_open";
  aggregation: "mean_and_max";
  level_bins: number;
  returned_bin_start: number;
  returned_bin_end: number;
  window_start_0based: number;
  window_end_0based: number;
  source_resolution_bp: number;
  point_columns: ["mean", "max"];
  values: [number, number][];
};

export type AlphaGenomeJunctionResponse = {
  uniprot_accession: string;
  ensembl_gene_id: string;
  tile_id: string;
  track: AlphaGenomeTrack;
  genome_build: "GRCh38";
  coordinate_convention: "0_based_half_open";
  items: { rank: number; chromosome: string; start_0based: number; end_0based: number; strand: string; value: number }[];
  available_count: number;
  returned_count: number;
  truncated: boolean;
};

export type AlphaGenomeContactMapResponse = {
  uniprot_accession: string;
  ensembl_gene_id: string;
  tile_id: string;
  track: AlphaGenomeTrack;
  genome_build: "GRCh38";
  coordinate_convention: "0_based_half_open";
  matrix_size: number;
  window_start_0based: number;
  window_end_0based: number;
  source_resolution_bp: number;
  values: number[];
};

export type ReactomeHierarchyNode = {
  pathway_id: string;
  pathway_name: string | null;
  pathway_url: string | null;
  evidence_codes: string[];
  evidence_count: number | null;
  parent_ids: string[];
  child_ids: string[];
};

export type ReactomeHierarchyResponse = {
  uniprot_accession: string;
  nodes: ReactomeHierarchyNode[];
  roots: string[];
  node_total: number;
  edge_total: number;
  root_total: number;
  shared_node_total: number;
  edge_semantics: "direct_parent_child";
  node_semantics: "protein_pathway_membership";
};

export type TrackName = "feature" | "ptm" | "pfam" | "conservation" | "covalent" | "variant" | "stability";

export type SequenceResponse = {
  uniprot_accession: string;
  sequence_id: string;
  length: number;
  sequence_version: number | null;
  coordinate_basis: "canonical_1_based_closed";
  build_context: { milestone?: string; scope?: string | null };
  window: { start: number; end: number; sequence: string };
  tracks: { track: TrackName; count: number; drawable_count: number }[];
};

export type SequenceOverviewFeatureInterval = {
  feature_type: string;
  start: number;
  end: number;
  description: string | null;
  feature_id: string | null;
  start_modifier: string | null;
  end_modifier: string | null;
  source: "UniProt";
};

export type SequenceOverviewSecondaryStructureInterval = SequenceOverviewFeatureInterval & {
  feature_type: "Helix" | "Beta strand" | "Turn";
};

export type SequenceOverviewPfamInterval = {
  pfam_accession: string;
  pfam_id: string | null;
  description: string | null;
  pfam_type: string | null;
  clan_id: string | null;
  clan_name: string | null;
  start: number;
  end: number;
  source: "Pfam";
};

export type SequenceOverviewPtmTypeCount = {
  ptm_type: string;
  count: number;
};

export type SequenceOverviewPtmSite = {
  position: number;
  residue: string | null;
  total_count: number;
  types: SequenceOverviewPtmTypeCount[];
};

export type SequenceOverviewCovalentPair = {
  feature_type: string;
  start_endpoint: number;
  end_endpoint: number;
  start_modifier: string | null;
  end_modifier: string | null;
  description: string | null;
  feature_id: number | null;
  source: "UniProt";
  coordinate_basis: "canonical_1_based_linked_endpoints";
};

export type SequenceVariantSiteDensity = {
  start: number;
  end: number;
  total_counts: number[];
  clinvar_plp_counts: number[];
  anchor_semantics: "one_per_canonical_drawable_variant_anchored_at_min_start";
  clinvar_plp_semantics: "strict_clinvar_classification_presence_not_consensus";
};

export type SequenceVariantSiteDensityResponse = {
  uniprot_accession: string;
  canonical_length: number;
  sequence_version: number | null;
  coordinate_basis: "canonical_1_based_closed";
  variant_site_density: SequenceVariantSiteDensity;
};

export type SequenceOverviewBin = {
  index: number;
  start: number;
  end: number;
  conservation: {
    observation_count: number;
    jsd_mean: number | null;
    jsd_min: number | null;
    jsd_max: number | null;
    confidence_counts: Record<string, number>;
    confidence_missing_count: number;
  };
  ptm_count: number;
  variant_count: number;
};

export type StabilityOverviewBin = {
  index: number;
  start: number;
  end: number;
  observation_count: number;
  distinct_substitution_count: number;
  ddg_min: number | null;
  ddg_q25: number | null;
  ddg_median: number | null;
  ddg_q75: number | null;
  ddg_max: number | null;
  unit: "kcal/mol";
};

export type StabilityPrediction = {
  source: "ThermoMPNN";
  ddg: number;
  unit: "kcal/mol";
  direction: "predicted_stabilizing" | "small_predicted_change" | "predicted_destabilizing";
  model_name: "ThermoMPNN";
  canonical_position: number;
  ref_aa: string;
  alt_aa: string;
  pdb_name: string;
};

export type StabilitySubstitutionItem = {
  substitution: string;
  ref_aa: string;
  alt_aa: string;
  ddg: number;
  direction: "predicted_stabilizing" | "small_predicted_change" | "predicted_destabilizing";
  genomic_variant_count: number;
  pdb_name: string;
};

export type StabilitySiteDetailResponse = {
  uniprot_accession: string;
  position: number;
  ref_aa: string;
  source: "ThermoMPNN";
  unit: "kcal/mol";
  ddg_min: number | null;
  ddg_max: number | null;
  substitutions: StabilitySubstitutionItem[];
  response_bounds: { complete: boolean; max_substitutions: number };
};

export type SequenceOverviewResponse = {
  uniprot_accession: string;
  sequence_id: string;
  canonical_length: number;
  sequence_version: number | null;
  coordinate_basis: "canonical_1_based_closed";
  canonical_sequence: string;
  topology_intervals: SequenceOverviewFeatureInterval[];
  pfam_intervals: SequenceOverviewPfamInterval[];
  functional_intervals: SequenceOverviewFeatureInterval[];
  secondary_structure_intervals: SequenceOverviewSecondaryStructureInterval[];
  ptm_sites: SequenceOverviewPtmSite[];
  ptm_type_counts: SequenceOverviewPtmTypeCount[];
  covalent_pairs: SequenceOverviewCovalentPair[];
  variant_site_density: SequenceVariantSiteDensity;
  density_bins: SequenceOverviewBin[];
  stability_bins?: StabilityOverviewBin[];
  stability_totals?: {
    predicted_variants: number;
    canonical_sites: number;
    distinct_substitutions: number;
  };
  totals: {
    topology_intervals: number;
    pfam_intervals: number;
    functional_intervals: number;
    secondary_structure_intervals: number;
    conservation_positions: number;
    ptm_records: number;
    ptm_drawable_records: number;
    canonical_variants: number;
    canonical_drawable_variants: number;
  };
  response_bounds: {
    requested_bins: number;
    returned_bins: number;
    max_bins: number;
    interval_sets_complete: true;
    variant_fact_rows_returned: 0;
    variant_bin_semantics: "one_per_canonical_drawable_variant_anchored_at_min_start";
    secondary_structure_intervals_returned: number;
    max_secondary_structure_intervals: number;
    secondary_structure_intervals_complete: boolean;
  };
};

export type VariantSitePreviewItem = {
  variant_key: string;
  hgvsp: string | null;
  consequence: string | null;
  source_badges: string[];
  has_clinvar_plp_evidence: boolean;
  stability_prediction: StabilityPrediction | null;
};

export type VariantSitePreviewResponse = {
  uniprot_accession: string;
  position: number;
  coordinate_basis: "canonical_1_based";
  total: number;
  clinvar_plp_count: number;
  items: VariantSitePreviewItem[];
  showing: number;
  limit: number;
  has_more: boolean;
  variant_table_query: { scope: "canonical"; start: number; end: number };
};

export type SiteItem = Record<string, unknown>;

export type SiteResponse = {
  uniprot_accession: string;
  sequence_version: number | null;
  coordinate_basis: "canonical_1_based_closed";
  region: { start: number; end: number };
  tracks: Partial<Record<TrackName, SiteItem[]>>;
  density: { start: number; end: number; counts: Partial<Record<TrackName, number>> }[];
  summary: Partial<Record<TrackName, number>>;
  applied_filters: Record<string, unknown>;
};

export type VariantEffect = {
  uniprot_accession: string;
  uniprot_isoform_id: string | null;
  canonical_flag: boolean | null;
  effect_scope: "canonical" | "isoform" | null;
  consequence: string | null;
  hgvsp: string | null;
  codons: string | null;
  transcript_ids: string | null;
  protein_start: number | null;
  protein_end: number | null;
  ref_aa: string | null;
  alt_aa: string | null;
  site_parse_status: string;
  is_drawable: boolean;
  is_representative_effect: boolean;
};

export type VariantItem = {
  variant_key: string;
  genome_build: string;
  chrom: string | null;
  pos: number | null;
  ref: string | null;
  alt: string | null;
  variant_class: string | null;
  existing_variation: string | null;
  representative_consequence: string | null;
  representative_hgvsp: string | null;
  impact: string | null;
  am_pathogenicity: number | null;
  am_class: string | null;
  joint_ac: number | null;
  joint_an: number | null;
  joint_af: number | null;
  exome_af: number | null;
  genome_af: number | null;
  database_source: string | null;
  source_badges: string[];
  database_id: string | null;
  n_sources: number | null;
  gene_symbol: string | null;
  hgnc_id: string | null;
  primary_effect: {
    uniprot_isoform_id: string | null;
    canonical_flag: boolean | null;
    effect_scope: "canonical" | "isoform" | null;
    consequence: string | null;
    hgvsp: string | null;
    protein_start: number | null;
    protein_end: number | null;
    site_parse_status: string;
    is_drawable: boolean;
  };
  stability_prediction: StabilityPrediction | null;
};

export type VariantListResponse = {
  uniprot_accession: string;
  items: VariantItem[];
  next_cursor: string | null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: Record<string, unknown>;
};

export type VariantSummaryTotal = {
  value: number;
  record_grain: "distinct_variant_key";
  categories_overlap: false;
};

export type VariantSummaryCount = {
  category: string;
  isoform_id: string | null;
  variant_count: number;
};

export type VariantSummaryFacet = {
  record_grain: "distinct_variant_key";
  categories_overlap: true;
  items: VariantSummaryCount[];
};

export type VariantCatalogSummaryResponse = {
  uniprot_accession: string;
  total: VariantSummaryTotal;
  protein_forms: VariantSummaryFacet;
  consequences: VariantSummaryFacet;
  clinvar_pathogenicity: VariantSummaryFacet;
  response_bounds: {
    strategy: "one_accession_bucket_single_grouped_query";
    runtime_external_requests: 0;
  };
};

export type VariantFilterOption = {
  value: string;
  variant_count: number;
};

export type VariantFilterOptionsResponse = {
  uniprot_accession: string;
  scope: "canonical" | "isoform" | "all";
  consequences: VariantFilterOption[];
  sources: VariantFilterOption[];
  complete: true;
  response_bounds: {
    strategy: "complete_accession_bucket_distinct_values";
    fact_rows_returned: 0;
    counts: "exact_distinct_variants";
    consequence_semantics: "comma_separated_term_membership";
    source_semantics: "semicolon_separated_badge_membership";
  };
};

export type VariantFactsEvidenceResponse = {
  uniprot_accession: string;
  variant_key: string;
  branch: "facts";
  core: Record<string, unknown>;
};

export type VariantEffectsEvidenceResponse = {
  uniprot_accession: string;
  variant_key: string;
  branch: "effects";
  effects: VariantEffect[];
};

export type ClinvarAssertion = {
  clinical_significance: string | null;
  rcv_accession: string | null;
  phenotype_list: string | null;
  phenotype_ids: string | null;
  review_status: string | null;
  origin: string | null;
  mondo_ids: string[];
  disease_categories: string[];
  source_release: string | null;
  evidence_grain: string | null;
};

export type VariantClinvarEvidenceResponse = {
  uniprot_accession: string;
  variant_key: string;
  branch: "clinvar";
  assertions: ClinvarAssertion[];
};

export type VariantCosmicEvidenceResponse = {
  uniprot_accession: string;
  variant_key: string;
  branch: "cosmic";
  records: CosmicEvidence[];
};

export type VariantStabilityEvidenceResponse = {
  uniprot_accession: string;
  variant_key: string;
  branch: "stability";
  prediction: StabilityPrediction | null;
};

export type VariantEvidenceResponse = VariantFactsEvidenceResponse
  | VariantEffectsEvidenceResponse
  | VariantClinvarEvidenceResponse
  | VariantCosmicEvidenceResponse
  | VariantStabilityEvidenceResponse;

export type PopulationFrequencyGroup = {
  ancestry_group: string;
  label: string;
  allele_frequency: number | null;
};

export type VariantPopulationFrequencyResponse = {
  uniprot_accession: string;
  variant_key: string;
  source: "gnomAD";
  dataset: "gnomad_r4";
  source_release: "v4.1";
  genome_build: "GRCh38";
  population_scope: "genetic_ancestry_group";
  callset: "exome" | "genome" | "joint";
  available_callsets: ("exome" | "genome" | "joint")[];
  availability: "matched" | "not_found_in_gnomad";
  message: string;
  groups: PopulationFrequencyGroup[];
  unavailable_fields: string[];
  total_or_estimate: { value: number; kind: "exact" };
  response_bounds: Record<string, unknown>;
};

export type CosmicEvidence = {
  genome_screen_sample_count: number | null;
  mondo_ids: string[];
  disease_categories: string[];
  cgc_tier: number | null;
  cgc_roles: ("oncogene" | "TSG" | "fusion")[];
};

export type ExpressionModality = "hpa_rna" | "hpa_ms" | "hpa_ihc" | "paxdb";

export type ExpressionDetails = {
  ensembl_gene_id?: string | null;
  gene_symbol?: string | null;
  ihc_tissue_name?: string | null;
  cell_type?: string | null;
  reliability?: string | null;
  paxdb_dataset_id?: string | null;
  paxdb_dataset_name?: string | null;
  string_external_id?: string | null;
  source_gene_name?: string | null;
  [key: string]: unknown;
};

export type ExpressionItem = {
  source_tissue: string | null;
  source_organ: string | null;
  raw_value: number | string | null;
  unit: string;
  source_database: string;
  source_release: string;
  details: ExpressionDetails;
};

export type ExpressionGroup = {
  modality: ExpressionModality;
  display_name: string;
  items: ExpressionItem[];
  total_or_estimate: { value: number; kind: "exact" };
  complete: true;
};

export type ExpressionResponse = {
  uniprot_accession: string;
  groups: Partial<Record<ExpressionModality, ExpressionGroup>>;
  next_cursor: null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: Record<string, unknown>;
  response_bounds: Record<string, unknown>;
};

export type AnatomyEvidenceSummary = {
  layer: "expression" | "gen" | "qtl";
  source_database: string;
  modality_or_type: string;
  record_count: number;
  distinct_context_count: number;
  raw_filter_terms: string[];
};

export type AnatomyRegionSummary = {
  body_region_id: string;
  display_label: string;
  ontology_id: string | null;
  has_data: boolean;
  mapping_status: "explicit" | "unmapped_other";
  evidence: AnatomyEvidenceSummary[];
};

export type AnatomySummaryResponse = {
  uniprot_accession: string;
  regions: AnatomyRegionSummary[];
  coordinate_semantics: "display_filter_crosswalk";
  fill_semantics: "availability_or_selection_only";
  cross_modality_score: false;
};

export type DifferentialExpressionContrast = {
  contrast_id: string;
  disease_category: string;
  tissue: string;
  disease_condition: string;
  case_definition: string;
  control_definition: string;
  case_n: number;
  control_n: number;
  paired: boolean;
  target_result_total: number;
  mapping_status: "unique_gene_row" | "multiple_gene_rows_same_symbol";
  target_results: DifferentialExpressionTargetResult[];
};

export type DifferentialExpressionTargetResult = {
  ensembl_gene_id: string | null;
  mean_expression: number | null;
  log2fc: number;
  fdr: number;
  direction: "up" | "down" | "not_significant";
};

export type DifferentialExpressionDataset = {
  dataset_id: string;
  dataset_name: string;
  project_id: string | null;
  bioproject_id: string | null;
  source_page: string | null;
  strategy: string | null;
  tissues: string[];
  disease_conditions: string[];
  sample_count_reported: number | null;
  sample_count_metadata: number | null;
  matrix_sample_count: number | null;
  sample_join_valid: boolean;
  qualifying_contrast_total: number;
  contrasts: DifferentialExpressionContrast[];
};

export type DifferentialExpressionSummaryResponse = {
  uniprot_accession: string;
  gene_symbol: string;
  mapping: {
    method: string;
    summary_membership: string;
    fdr_threshold: number;
    absolute_log2fc_threshold: number;
  };
  datasets: DifferentialExpressionDataset[];
  dataset_total: number;
  contrast_total: number;
};

export type VolcanoPoint = [
  log2fc: number,
  negLog10Fdr: number,
  geneSymbol: string | null,
  ensemblGeneId: string | null,
  meanExpression: number | null,
  rawFdr: number,
  direction: "up" | "down" | "not_significant",
  passesExpressionFilter: boolean,
  isFdrSignificant: boolean,
  passesLog2fcThreshold: boolean,
  isSignificantWithEffect: boolean,
  isMembraneMapped: boolean,
  isTarget: boolean,
];

export type DifferentialExpressionVolcanoResponse = {
  uniprot_accession: string;
  gene_symbol: string;
  contrast: {
    dataset_id: string;
    contrast_id: string;
    disease_category: string;
    disease_condition: string;
    tissue: string;
    case_definition: string;
    control_definition: string;
    case_n: number;
    control_n: number;
    paired: boolean;
    design_formula: string;
  };
  thresholds: { absolute_log2fc: number; fdr: number; fdr_zero_y_clamp: number };
  counts: { tested: number; plotted: number; unplottable: number; fdr_zero: number };
  point_columns: string[];
  points: VolcanoPoint[];
};

export type QtlSource = "GTEx" | "eQTLGen" | "QTLbase";

export type QtlSourceSemantics = {
  source_database: QtlSource;
  evidence_semantics: string;
  genome_build: "GRCh37" | "GRCh38";
};

export type QtlSummaryItem = {
  source_database: QtlSource;
  qtl_type: string;
  tissue_or_context: string | null;
  population: string | null;
  record_count: number;
  distinct_variant_or_locus_count: number;
};

export type QtlSummaryResponse = {
  uniprot_accession: string;
  items: QtlSummaryItem[];
  source_semantics: QtlSourceSemantics[];
  next_cursor: null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: Record<string, unknown>;
};

export type QtlDetailItem = {
  source_database: QtlSource;
  qtl_type: string;
  tissue: string | null;
  context: string | null;
  population: string | null;
  gene: Record<string, unknown>;
  phenotype: Record<string, unknown> | null;
  variant_or_locus: Record<string, unknown>;
  genome_build: "GRCh37" | "GRCh38";
  p_value: number | null;
  evidence_semantics: string;
  source_release: string;
  source_specific: Record<string, Record<string, unknown>>;
};

export type QtlDetailResponse = {
  uniprot_accession: string;
  source_database: QtlSource;
  qtl_type: string;
  items: QtlDetailItem[];
  source_semantics: QtlSourceSemantics;
  next_cursor: string | null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: Record<string, unknown>;
};

export type InteractionSource = "BioGRID" | "IntAct";

export type InteractionSummaryItem = {
  source_database: InteractionSource;
  context_class: string | null;
  context: string | null;
  interaction_category: string | null;
  evidence_record_count: number;
  distinct_native_interaction_count: number;
};

export type InteractionSummaryResponse = {
  uniprot_accession: string;
  items: InteractionSummaryItem[];
  source_semantics: { source_database: InteractionSource; evidence_grain: string; caveat: string }[];
  next_cursor: null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: Record<string, unknown>;
};

export type InteractionDetailItem = {
  source_database: InteractionSource;
  native_interaction_id: string | null;
  page_role: string | null;
  interaction_category: string | null;
  context_class: string | null;
  context: string | null;
  partner: Record<string, unknown>;
  publication: string | null;
  source_specific: Record<string, Record<string, unknown>>;
};

export type InteractionDetailResponse = {
  uniprot_accession: string;
  source_database: InteractionSource;
  items: InteractionDetailItem[];
  next_cursor: string | null;
  total_or_estimate: { value: number; kind: "exact" };
  source_semantics: { source_database: InteractionSource; evidence_grain: string; caveat: string };
  applied_filters: Record<string, unknown>;
};

export type MutationEffect = {
  source_database: "IntAct";
  source_release: string;
  evidence_grain: string;
  feature_accession: string | null;
  feature_short_label: string | null;
  feature_ranges: string | null;
  original_sequence: string | null;
  resulting_sequence: string | null;
  feature_type: string | null;
  feature_annotation: string | null;
  affected_protein: { accession: string | null; symbol: string | null; full_name: string | null; organism: string | null };
  interaction_participants: string | null;
  pubmed_id: string | null;
  figure_legend: string | null;
  interaction_accession: string | null;
};

export type MutationEffectResponse = {
  uniprot_accession: string;
  items: MutationEffect[];
  next_cursor: string | null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: Record<string, unknown>;
};

export type DiseaseItem = {
  source: "clingen_validity" | "clingen_dosage" | "gencc" | "omim" | "hpo";
  disease_id: string | null;
  disease_name: string | null;
  assertion: Record<string, unknown>;
  exact_mondo_mappings: Record<string, unknown>[];
};

export type DiseaseSection = {
  items: DiseaseItem[];
  next_cursor: string | null;
  total_or_estimate: { value: number; kind: "exact" };
};

export type DiseaseResponse = {
  uniprot_accession: string;
  sections: Partial<Record<DiseaseItem["source"], DiseaseSection>>;
  applied_filters: Record<string, unknown>;
  interpretation: string;
};

export type HpoEvidenceItem = {
  disease_id: string | null;
  disease_name: string | null;
  hpo_id: string | null;
  hpo_name: string | null;
  qualifier: string | null;
  aspect: string | null;
  phenotype_status: string | null;
  evidence: Record<string, unknown>;
};

export type HpoResponse = {
  uniprot_accession: string;
  category: "observed" | "explicitly_absent" | "inheritance";
  items: HpoEvidenceItem[];
  next_cursor: string | null;
  total_or_estimate: { value: number; kind: "exact" };
  applied_filters: Record<string, unknown>;
};

export type DataSourceItem = {
  source_id: string;
  display_name: string;
  layer: string;
  source_release: string | null;
  record_grain: string | null;
  caveat: string | null;
};

export type DataSourcesResponse = { items: DataSourceItem[]; total_or_estimate: { value: number; kind: "exact" } };
