"""Narrow API models for AlphaGenome reference-sequence predictions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AlphaGenomeAvailability = Literal["available", "preparing", "unavailable"]
AlphaGenomeMappingStatus = Literal["exact", "ambiguous", "no_prediction", "no_ensembl"]


class AlphaGenomeTile(BaseModel):
    tile_id: str
    tile_index: int
    chromosome: str
    window_start_0based: int
    window_end_0based: int
    core_start_0based: int
    core_end_0based: int
    display_ready: bool


class AlphaGenomeGeneCandidate(BaseModel):
    ensembl_gene_id: str | None = None
    gene_symbol: str | None = None
    hgnc_id: str | None = None
    chromosome: str | None = None
    gene_start_1based: int | None = None
    gene_end_1based_inclusive: int | None = None
    gene_strand: str | None = None
    mapping_status: AlphaGenomeMappingStatus
    mapping_count: int
    has_prediction: bool
    display_ready: bool
    tiles: list[AlphaGenomeTile]


class AlphaGenomeSummaryResponse(BaseModel):
    uniprot_accession: str
    availability: AlphaGenomeAvailability
    source: Literal["AlphaGenome"] = "AlphaGenome"
    prediction_kind: Literal["reference_sequence_tracks"] = "reference_sequence_tracks"
    genome_build: Literal["GRCh38"] = "GRCh38"
    coordinate_convention: Literal["model_window_0_based_half_open"] = "model_window_0_based_half_open"
    local_output_subset: Literal[True] = True
    missing_official_modalities: list[str]
    has_variant_effect_scores: Literal[False] = False
    modality_track_counts: dict[str, int]
    candidates: list[AlphaGenomeGeneCandidate]
    notice: str


class AlphaGenomeTrack(BaseModel):
    track_id: str
    modality: str
    name: str | None = None
    assay_title: str | None = None
    ontology_curie: str | None = None
    biosample_name: str | None = None
    biosample_type: str | None = None
    biosample_life_stage: str | None = None
    gtex_tissue: str | None = None
    strand: str | None = None
    histone_mark: str | None = None
    data_source: str | None = None
    display_unit: str


class AlphaGenomeTrackCatalogResponse(BaseModel):
    uniprot_accession: str
    ensembl_gene_id: str
    modality: str
    tracks: list[AlphaGenomeTrack]
    total: int


class AlphaGenomeSignalResponse(BaseModel):
    uniprot_accession: str
    ensembl_gene_id: str
    tile_id: str
    track: AlphaGenomeTrack
    genome_build: Literal["GRCh38"] = "GRCh38"
    coordinate_convention: Literal["0_based_half_open"] = "0_based_half_open"
    aggregation: Literal["mean_and_max"] = "mean_and_max"
    level_bins: int
    returned_bin_start: int
    returned_bin_end: int
    window_start_0based: int
    window_end_0based: int
    source_resolution_bp: int
    point_columns: list[str] = Field(default_factory=lambda: ["mean", "max"])
    values: list[tuple[float, float]]


class AlphaGenomeJunction(BaseModel):
    rank: int
    chromosome: str
    start_0based: int
    end_0based: int
    strand: str
    value: float


class AlphaGenomeJunctionResponse(BaseModel):
    uniprot_accession: str
    ensembl_gene_id: str
    tile_id: str
    track: AlphaGenomeTrack
    genome_build: Literal["GRCh38"] = "GRCh38"
    coordinate_convention: Literal["0_based_half_open"] = "0_based_half_open"
    items: list[AlphaGenomeJunction]
    available_count: int
    returned_count: int
    truncated: bool


class AlphaGenomeContactMapResponse(BaseModel):
    uniprot_accession: str
    ensembl_gene_id: str
    tile_id: str
    track: AlphaGenomeTrack
    genome_build: Literal["GRCh38"] = "GRCh38"
    coordinate_convention: Literal["0_based_half_open"] = "0_based_half_open"
    matrix_size: int
    window_start_0based: int
    window_end_0based: int
    source_resolution_bp: int
    values: list[float]
