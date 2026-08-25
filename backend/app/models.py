"""Pydantic response models for the read-only M1-M3 API."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ExactTotal(BaseModel):
    value: int
    kind: Literal["exact"] = "exact"


class SearchMatch(BaseModel):
    text: str
    identifier_type: str
    identifier_database: str | None = None
    kind: Literal["exact", "prefix", "token"]


class SearchCandidate(BaseModel):
    uniprot_accession: str
    gene_symbol: str | None = None
    protein_name: str | None = None
    entry_name: str | None = None
    membrane_class: str | None = None
    canonical_length: int | None = None
    match: SearchMatch


class SearchResponse(BaseModel):
    query: str
    items: list[SearchCandidate]
    next_cursor: None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]
    ambiguity: bool
    resolution: Literal["no_match", "direct_candidate", "candidate_selection"]


class Identifier(BaseModel):
    isoform_id: str | None = None
    identifier_type: str
    identifier_database: str | None = None
    identifier_full: str | None = None
    identifier_base: str | None = None
    identifier_version: int | None = None
    alias_type: str | None = None
    identifier_label: str | None = None


class CanonicalSequenceMetadata(BaseModel):
    sequence_id: str
    length: int
    sequence_version: int | None = None


class GoSummary(BaseModel):
    molecular_function: list[str]
    biological_process: list[str]
    cellular_component: list[str]


class GoEvidenceCodeCount(BaseModel):
    evidence_code: str
    annotation_count: int


class GoAspectCount(BaseModel):
    aspect: Literal["MF", "BP", "CC"]
    term_count: int
    annotation_count: int
    reference_count: int


class GoTermSummary(BaseModel):
    go_id: str
    go_term_name: str
    aspect: Literal["MF", "BP", "CC"]
    go_namespace: str | None = None
    annotation_count: int
    reference_count: int
    evidence_codes: list[GoEvidenceCodeCount]


class GoTermsResponse(BaseModel):
    uniprot_accession: str
    provenance: "DataSourceDescription"
    items: list[GoTermSummary]
    next_cursor: str | None = None
    total_or_estimate: ExactTotal
    annotation_count: int
    aspect_counts: list[GoAspectCount]
    applied_filters: dict[str, object]


class GoEvidenceItem(BaseModel):
    go_evidence_id: int
    go_id: str
    go_term_name: str
    aspect: Literal["MF", "BP", "CC"]
    go_namespace: str | None = None
    qualifier: str | None = None
    is_negated: bool | None = None
    evidence_code: str | None = None
    reference_id: str | None = None
    with_from: str | None = None
    assigned_by: str | None = None
    annotation_extension: str | None = None
    annotation_date: str | None = None


class GoEvidenceResponse(BaseModel):
    uniprot_accession: str
    go_id: str
    items: list[GoEvidenceItem]
    next_cursor: str | None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


class ReactomePathway(BaseModel):
    pathway_id: str | None = None
    pathway_name: str | None = None
    pathway_url: str | None = None
    evidence_codes: list[str]
    evidence_count: int | None = None


class ReactomeHierarchyNode(BaseModel):
    pathway_id: str
    pathway_name: str | None = None
    pathway_url: str | None = None
    evidence_codes: list[str]
    evidence_count: int | None = None
    parent_ids: list[str]
    child_ids: list[str]


class ReactomeHierarchyResponse(BaseModel):
    uniprot_accession: str
    nodes: list[ReactomeHierarchyNode]
    roots: list[str]
    node_total: int
    edge_total: int
    root_total: int
    shared_node_total: int
    edge_semantics: Literal["direct_parent_child"] = "direct_parent_child"
    node_semantics: Literal["protein_pathway_membership"] = "protein_pathway_membership"


class SubcellularLocation(BaseModel):
    sequence_version: int | None = None
    location_id: str | None = None
    location_name: str | None = None
    topology_id: str | None = None
    topology_name: str | None = None
    orientation_id: str | None = None
    orientation_name: str | None = None


class CompactAnnotationSummary(BaseModel):
    go: GoSummary | None = None
    reactome: list[ReactomePathway]
    reactome_total: int
    locations: list[SubcellularLocation]
    locations_total: int
    item_limit: int


class ProteinOverviewResponse(BaseModel):
    uniprot_accession: str
    entry_name: str | None = None
    protein_name: str | None = None
    gene_symbol: str | None = None
    canonical_length: int | None = None
    protein_existence: str | None = None
    annotation_score: float | None = None
    membrane_class: str | None = None
    all_class_labels: list[str]
    transmembrane_count: int | None = None
    intramembrane_count: int | None = None
    lipidation_count: int | None = None
    lipidation_anchor_match_count: int | None = None
    canonical_sequence: CanonicalSequenceMetadata
    identifiers: list[Identifier]
    annotation_summary: CompactAnnotationSummary


class GoAnnotation(BaseModel):
    section: Literal["go"]
    molecular_function: list[str]
    biological_process: list[str]
    cellular_component: list[str]


class ReactomeAnnotation(BaseModel):
    section: Literal["reactome"]
    pathway_id: str | None = None
    pathway_name: str | None = None
    pathway_url: str | None = None
    evidence_codes: list[str]
    evidence_count: int | None = None


class LocationAnnotation(BaseModel):
    section: Literal["location"]
    sequence_version: int | None = None
    location_id: str | None = None
    location_name: str | None = None
    topology_id: str | None = None
    topology_name: str | None = None
    orientation_id: str | None = None
    orientation_name: str | None = None


AnnotationItem = Annotated[
    GoAnnotation | ReactomeAnnotation | LocationAnnotation,
    Field(discriminator="section"),
]


class AnnotationResponse(BaseModel):
    uniprot_accession: str
    section: Literal["go", "reactome", "location"] | None = None
    items: list[AnnotationItem]
    next_cursor: str | None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


class SequenceWindow(BaseModel):
    start: int
    end: int
    sequence: str


class SequenceTrackSummary(BaseModel):
    track: str
    count: int
    drawable_count: int


class SequenceResponse(BaseModel):
    uniprot_accession: str
    sequence_id: str
    length: int
    sequence_version: int | None = None
    coordinate_basis: Literal["canonical_1_based_closed"] = "canonical_1_based_closed"
    build_context: dict[str, object]
    window: SequenceWindow
    tracks: list[SequenceTrackSummary]


class SequenceOverviewFeatureInterval(BaseModel):
    feature_type: str
    start: int
    end: int
    description: str | None = None
    feature_id: str | None = None
    start_modifier: str | None = None
    end_modifier: str | None = None
    source: Literal["UniProt"] = "UniProt"


class SequenceOverviewSecondaryStructureInterval(SequenceOverviewFeatureInterval):
    """A canonical UniProt secondary-structure interval for the overview rail."""

    feature_type: Literal["Helix", "Beta strand", "Turn"]


class SequenceOverviewPfamInterval(BaseModel):
    pfam_accession: str
    pfam_id: str | None = None
    description: str | None = None
    pfam_type: str | None = None
    clan_id: str | None = None
    clan_name: str | None = None
    start: int
    end: int
    source: Literal["Pfam"] = "Pfam"


class ConservationBinSummary(BaseModel):
    observation_count: int
    jsd_mean: float | None = None
    jsd_min: float | None = None
    jsd_max: float | None = None
    confidence_counts: dict[str, int]
    confidence_missing_count: int


class SequenceOverviewBin(BaseModel):
    index: int
    start: int
    end: int
    conservation: ConservationBinSummary
    ptm_count: int
    variant_count: int


class StabilityOverviewBin(BaseModel):
    index: int
    start: int
    end: int
    observation_count: int
    distinct_substitution_count: int
    ddg_min: float | None = None
    ddg_q25: float | None = None
    ddg_median: float | None = None
    ddg_q75: float | None = None
    ddg_max: float | None = None
    unit: Literal["kcal/mol"] = "kcal/mol"


class StabilityTotals(BaseModel):
    predicted_variants: int
    canonical_sites: int
    distinct_substitutions: int


class SequenceVariantSiteDensity(BaseModel):
    start: Literal[1] = 1
    end: int
    total_counts: list[int]
    clinvar_plp_counts: list[int]
    anchor_semantics: Literal["one_per_canonical_drawable_variant_anchored_at_min_start"] = (
        "one_per_canonical_drawable_variant_anchored_at_min_start"
    )
    clinvar_plp_semantics: Literal["strict_clinvar_classification_presence_not_consensus"] = (
        "strict_clinvar_classification_presence_not_consensus"
    )


class SequenceOverviewPtmType(BaseModel):
    ptm_type: str
    count: int


class SequenceOverviewPtmSite(BaseModel):
    position: int
    residue: str | None = None
    total_count: int
    types: list[SequenceOverviewPtmType]


class SequenceOverviewCovalentPair(BaseModel):
    feature_type: str
    start_endpoint: int
    end_endpoint: int
    start_modifier: str | None = None
    end_modifier: str | None = None
    description: str | None = None
    feature_id: int | None = None
    source: Literal["UniProt"] = "UniProt"
    coordinate_basis: Literal["canonical_1_based_linked_endpoints"] = (
        "canonical_1_based_linked_endpoints"
    )


class SequenceOverviewTotals(BaseModel):
    topology_intervals: int
    pfam_intervals: int
    functional_intervals: int
    secondary_structure_intervals: int
    conservation_positions: int
    ptm_records: int
    ptm_drawable_records: int
    canonical_variants: int
    canonical_drawable_variants: int


class SequenceOverviewBounds(BaseModel):
    requested_bins: int
    returned_bins: int
    max_bins: int
    interval_sets_complete: Literal[True] = True
    variant_fact_rows_returned: Literal[0] = 0
    variant_bin_semantics: Literal["one_per_canonical_drawable_variant_anchored_at_min_start"] = (
        "one_per_canonical_drawable_variant_anchored_at_min_start"
    )
    secondary_structure_intervals_returned: int
    max_secondary_structure_intervals: int
    secondary_structure_intervals_complete: bool


class SequenceOverviewResponse(BaseModel):
    uniprot_accession: str
    sequence_id: str
    canonical_length: int
    canonical_sequence: str
    sequence_version: int | None = None
    coordinate_basis: Literal["canonical_1_based_closed"] = "canonical_1_based_closed"
    topology_intervals: list[SequenceOverviewFeatureInterval]
    pfam_intervals: list[SequenceOverviewPfamInterval]
    functional_intervals: list[SequenceOverviewFeatureInterval]
    secondary_structure_intervals: list[SequenceOverviewSecondaryStructureInterval]
    density_bins: list[SequenceOverviewBin]
    stability_bins: list[StabilityOverviewBin]
    stability_totals: StabilityTotals
    variant_site_density: SequenceVariantSiteDensity
    ptm_sites: list[SequenceOverviewPtmSite]
    ptm_type_counts: list[SequenceOverviewPtmType]
    covalent_pairs: list[SequenceOverviewCovalentPair]
    totals: SequenceOverviewTotals
    response_bounds: SequenceOverviewBounds


class SiteResponse(BaseModel):
    uniprot_accession: str
    sequence_version: int | None = None
    coordinate_basis: Literal["canonical_1_based_closed"] = "canonical_1_based_closed"
    variant_density_semantics: Literal["one_per_canonical_drawable_variant_anchored_at_min_start"] = (
        "one_per_canonical_drawable_variant_anchored_at_min_start"
    )
    region: dict[str, int]
    tracks: dict[str, list[dict[str, object]]]
    density: list[dict[str, object]]
    summary: dict[str, int]
    applied_filters: dict[str, object]


class VariantEffect(BaseModel):
    uniprot_accession: str
    uniprot_isoform_id: str | None = None
    canonical_flag: bool | None = None
    effect_scope: Literal["canonical", "isoform"] | None = None
    consequence: str | None = None
    hgvsp: str | None = None
    codons: str | None = None
    transcript_ids: str | None = None
    protein_start: int | None = None
    protein_end: int | None = None
    ref_aa: str | None = None
    alt_aa: str | None = None
    site_parse_status: str
    is_drawable: bool
    is_representative_effect: bool


class StabilityPrediction(BaseModel):
    source: Literal["ThermoMPNN"] = "ThermoMPNN"
    ddg: float
    unit: Literal["kcal/mol"] = "kcal/mol"
    direction: Literal[
        "predicted_stabilizing", "small_predicted_change", "predicted_destabilizing"
    ]
    model_name: Literal["ThermoMPNN"] = "ThermoMPNN"
    canonical_position: int
    ref_aa: str
    alt_aa: str
    pdb_name: str


class StabilitySubstitutionItem(BaseModel):
    substitution: str
    ref_aa: str
    alt_aa: str
    ddg: float
    direction: Literal[
        "predicted_stabilizing", "small_predicted_change", "predicted_destabilizing"
    ]
    genomic_variant_count: int
    pdb_name: str


class StabilitySiteDetailResponse(BaseModel):
    uniprot_accession: str
    position: int
    ref_aa: str
    source: Literal["ThermoMPNN"] = "ThermoMPNN"
    unit: Literal["kcal/mol"] = "kcal/mol"
    ddg_min: float | None = None
    ddg_max: float | None = None
    substitutions: list[StabilitySubstitutionItem]
    response_bounds: dict[str, object]


class VariantListResponse(BaseModel):
    uniprot_accession: str
    items: list[dict[str, object]]
    next_cursor: str | None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


class VariantSummaryTotal(BaseModel):
    value: int
    record_grain: Literal["distinct_variant_key"] = "distinct_variant_key"
    categories_overlap: Literal[False] = False


class VariantSummaryCount(BaseModel):
    category: str
    variant_count: int
    isoform_id: str | None = None


class VariantSummaryFacet(BaseModel):
    record_grain: Literal["distinct_variant_key"] = "distinct_variant_key"
    categories_overlap: Literal[True] = True
    items: list[VariantSummaryCount]


class VariantCatalogSummaryResponse(BaseModel):
    uniprot_accession: str
    total: VariantSummaryTotal
    protein_forms: VariantSummaryFacet
    consequences: VariantSummaryFacet
    clinvar_pathogenicity: VariantSummaryFacet
    response_bounds: dict[str, object]


class VariantSitePreviewItem(BaseModel):
    variant_key: str
    hgvsp: str | None = None
    consequence: str | None = None
    source_badges: list[str]
    has_clinvar_plp_evidence: bool
    stability_prediction: StabilityPrediction | None = None


class VariantSitePreviewResponse(BaseModel):
    uniprot_accession: str
    position: int
    coordinate_basis: Literal["canonical_1_based"] = "canonical_1_based"
    total: int
    clinvar_plp_count: int
    showing: int
    limit: int
    has_more: bool
    items: list[VariantSitePreviewItem]
    variant_table_query: dict[str, object]


class VariantFilterOption(BaseModel):
    value: str
    variant_count: int


class VariantFilterOptionsResponse(BaseModel):
    uniprot_accession: str
    scope: Literal["canonical", "isoform", "all"]
    consequences: list[VariantFilterOption]
    sources: list[VariantFilterOption]
    complete: Literal[True] = True
    response_bounds: dict[str, object]


class PopulationFrequencyGroup(BaseModel):
    ancestry_group: str
    label: str
    allele_frequency: float | None


class VariantPopulationFrequencyResponse(BaseModel):
    uniprot_accession: str
    variant_key: str
    source: Literal["gnomAD"] = "gnomAD"
    dataset: Literal["gnomad_r4"] = "gnomad_r4"
    source_release: Literal["v4.1"] = "v4.1"
    genome_build: Literal["GRCh38"] = "GRCh38"
    population_scope: Literal["genetic_ancestry_group"] = "genetic_ancestry_group"
    callset: Literal["exome", "genome", "joint"]
    available_callsets: list[Literal["exome", "genome", "joint"]]
    availability: Literal["matched", "not_found_in_gnomad"]
    message: str
    groups: list[PopulationFrequencyGroup]
    unavailable_fields: list[str]
    total_or_estimate: ExactTotal
    response_bounds: dict[str, object]


class CosmicEvidence(BaseModel):
    genome_screen_sample_count: int | None = None
    mondo_ids: list[str]
    disease_categories: list[str]
    cgc_tier: int | None = None
    cgc_roles: list[str]


class VariantFactsEvidenceResponse(BaseModel):
    uniprot_accession: str
    variant_key: str
    branch: Literal["facts"] = "facts"
    core: dict[str, object]


class VariantEffectsEvidenceResponse(BaseModel):
    uniprot_accession: str
    variant_key: str
    branch: Literal["effects"] = "effects"
    effects: list[VariantEffect]


class ClinvarAssertion(BaseModel):
    clinical_significance: str | None = None
    rcv_accession: str | None = None
    phenotype_list: str | None = None
    phenotype_ids: str | None = None
    review_status: str | None = None
    origin: str | None = None
    mondo_ids: list[str]
    disease_categories: list[str]
    source_release: str | None = None
    evidence_grain: str | None = None


class VariantClinvarEvidenceResponse(BaseModel):
    uniprot_accession: str
    variant_key: str
    branch: Literal["clinvar"] = "clinvar"
    assertions: list[ClinvarAssertion]


class VariantCosmicEvidenceResponse(BaseModel):
    uniprot_accession: str
    variant_key: str
    branch: Literal["cosmic"] = "cosmic"
    records: list[CosmicEvidence]


class VariantStabilityEvidenceResponse(BaseModel):
    uniprot_accession: str
    variant_key: str
    branch: Literal["stability"] = "stability"
    prediction: StabilityPrediction | None = None


ExpressionModality = Literal["hpa_rna", "hpa_ms", "hpa_ihc", "paxdb"]


class ExpressionItem(BaseModel):
    source_tissue: str | None = None
    source_organ: str | None = None
    raw_value: float | str | None = None
    unit: str
    source_database: str
    source_release: str
    details: dict[str, object]


class ExpressionGroup(BaseModel):
    modality: ExpressionModality
    display_name: str
    items: list[ExpressionItem]
    total_or_estimate: ExactTotal
    complete: Literal[True] = True


class ExpressionResponse(BaseModel):
    uniprot_accession: str
    groups: dict[ExpressionModality, ExpressionGroup]
    next_cursor: None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]
    response_bounds: dict[str, object]


class AnatomyEvidenceSummary(BaseModel):
    layer: Literal["expression", "gen", "qtl"]
    source_database: str
    modality_or_type: str
    record_count: int
    distinct_context_count: int
    raw_filter_terms: list[str]


class AnatomyRegionSummary(BaseModel):
    body_region_id: str
    display_label: str
    ontology_id: str | None = None
    has_data: bool
    mapping_status: Literal["explicit", "unmapped_other"]
    evidence: list[AnatomyEvidenceSummary]


class AnatomySummaryResponse(BaseModel):
    uniprot_accession: str
    regions: list[AnatomyRegionSummary]
    coordinate_semantics: Literal["display_filter_crosswalk"] = "display_filter_crosswalk"
    fill_semantics: Literal["availability_or_selection_only"] = "availability_or_selection_only"
    cross_modality_score: Literal[False] = False


class QtlSourceSemantics(BaseModel):
    source_database: Literal["GTEx", "QTLbase", "eQTLGen"]
    evidence_semantics: str
    genome_build: Literal["GRCh37", "GRCh38"]


class QtlSummaryItem(BaseModel):
    source_database: Literal["GTEx", "QTLbase", "eQTLGen"]
    qtl_type: str
    tissue_or_context: str | None = None
    population: str | None = None
    record_count: int
    distinct_variant_or_locus_count: int


class QtlSummaryResponse(BaseModel):
    uniprot_accession: str
    items: list[QtlSummaryItem]
    source_semantics: list[QtlSourceSemantics]
    next_cursor: None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


class QtlDetailItem(BaseModel):
    source_database: Literal["GTEx", "QTLbase", "eQTLGen"]
    qtl_type: str
    tissue: str | None = None
    context: str | None = None
    population: str | None = None
    gene: dict[str, object]
    phenotype: dict[str, object] | None = None
    variant_or_locus: dict[str, object]
    genome_build: Literal["GRCh37", "GRCh38"]
    p_value: float | None = None
    evidence_semantics: str
    source_release: str
    source_specific: dict[str, dict[str, object]]


class QtlDetailResponse(BaseModel):
    uniprot_accession: str
    source_database: Literal["GTEx", "QTLbase", "eQTLGen"]
    qtl_type: str
    items: list[QtlDetailItem]
    source_semantics: QtlSourceSemantics
    next_cursor: str | None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


class InteractionSourceSemantics(BaseModel):
    source_database: Literal["BioGRID", "IntAct"]
    evidence_grain: str
    caveat: str


class InteractionSummaryItem(BaseModel):
    source_database: Literal["BioGRID", "IntAct"]
    context_class: str | None = None
    context: str | None = None
    interaction_category: str | None = None
    evidence_record_count: int
    distinct_native_interaction_count: int


class InteractionSummaryResponse(BaseModel):
    uniprot_accession: str
    items: list[InteractionSummaryItem]
    source_semantics: list[InteractionSourceSemantics]
    next_cursor: None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


class InteractionDetailItem(BaseModel):
    source_database: Literal["BioGRID", "IntAct"]
    native_interaction_id: str | None = None
    page_role: str | None = None
    interaction_category: str | None = None
    context_class: str | None = None
    context: str | None = None
    partner: dict[str, object]
    publication: str | None = None
    source_specific: dict[str, dict[str, object]]


class InteractionDetailResponse(BaseModel):
    uniprot_accession: str
    source_database: Literal["BioGRID", "IntAct"]
    items: list[InteractionDetailItem]
    source_semantics: InteractionSourceSemantics
    next_cursor: str | None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


class InteractionMutationEffect(BaseModel):
    source_database: Literal["IntAct"] = "IntAct"
    source_release: str
    evidence_grain: str
    feature_accession: str | None = None
    feature_short_label: str | None = None
    feature_ranges: str | None = None
    original_sequence: str | None = None
    resulting_sequence: str | None = None
    feature_type: str | None = None
    feature_annotation: str | None = None
    affected_protein: dict[str, object]
    interaction_participants: str | None = None
    pubmed_id: str | None = None
    figure_legend: str | None = None
    interaction_accession: str | None = None


class InteractionMutationResponse(BaseModel):
    uniprot_accession: str
    items: list[InteractionMutationEffect]
    next_cursor: str | None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


DiseaseSource = Literal[
    "clingen_validity", "clingen_dosage", "gencc", "omim", "hpo"
]


class DiseaseAssertionItem(BaseModel):
    source: DiseaseSource
    disease_id: str | None = None
    disease_name: str | None = None
    assertion: dict[str, object]
    exact_mondo_mappings: list[dict[str, object]]


class DiseaseSection(BaseModel):
    source: DiseaseSource
    items: list[DiseaseAssertionItem]
    next_cursor: str | None = None
    total_or_estimate: ExactTotal


class DiseaseResponse(BaseModel):
    uniprot_accession: str
    sections: dict[DiseaseSource, DiseaseSection]
    applied_filters: dict[str, object]
    interpretation: Literal["source_specific_no_cross_source_voting"] = (
        "source_specific_no_cross_source_voting"
    )


class HpoEvidenceItem(BaseModel):
    disease_id: str | None = None
    disease_name: str | None = None
    hpo_id: str | None = None
    hpo_name: str | None = None
    qualifier: str | None = None
    aspect: str | None = None
    phenotype_status: str | None = None
    evidence: dict[str, object]


class HpoEvidenceResponse(BaseModel):
    uniprot_accession: str
    category: Literal["observed", "explicitly_absent", "inheritance"]
    items: list[HpoEvidenceItem]
    next_cursor: str | None = None
    total_or_estimate: ExactTotal
    applied_filters: dict[str, object]


class DataSourceDescription(BaseModel):
    source_id: str
    display_name: str
    layer: str
    source_release: str | None = None
    record_grain: str
    caveat: str | None = None


class DataSourcesResponse(BaseModel):
    items: list[DataSourceDescription]
    total_or_estimate: ExactTotal


class StructureFragment(BaseModel):
    fragment_number: int
    fragment_label: str
    filename: str
    compressed_bytes: int
    uncompressed_bytes: int
    canonical_start: int | None = None
    canonical_end: int | None = None
    content_url: str
    download_url: str


class ProteinStructuresResponse(BaseModel):
    uniprot_accession: str
    availability: Literal["available", "unavailable"]
    source: Literal["AlphaFold DB"] = "AlphaFold DB"
    model_version: Literal[6] = 6
    fragment_total: int
    fragments: list[StructureFragment]
