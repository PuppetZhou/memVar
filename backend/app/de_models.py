"""Public response models for GEN differential expression."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DeMappingSemantics(BaseModel):
    method: Literal["trim_casefold_exact_gene_symbol"] = "trim_casefold_exact_gene_symbol"
    summary_membership: Literal["source_is_significant_with_effect"] = "source_is_significant_with_effect"
    fdr_threshold: float = 0.05
    absolute_log2fc_threshold: float = 1.0


class DeTargetResult(BaseModel):
    ensembl_gene_id: str | None
    mean_expression: float | None
    log2fc: float
    fdr: float
    direction: Literal["up", "down", "not_significant"]


class DeContrastSummary(BaseModel):
    contrast_id: str
    disease_category: str
    disease_condition: str
    tissue: str
    case_definition: str
    control_definition: str
    case_n: int
    control_n: int
    paired: bool
    target_result_total: int
    mapping_status: Literal["unique_gene_row", "multiple_gene_rows_same_symbol"]
    target_results: list[DeTargetResult]


class DeDatasetSummary(BaseModel):
    dataset_id: str
    dataset_name: str
    project_id: str
    bioproject_id: str
    source_page: str
    strategy: str
    tissues: list[str]
    disease_conditions: list[str]
    sample_count_reported: int
    sample_count_metadata: int
    matrix_sample_count: int
    sample_join_valid: bool
    qualifying_contrast_total: int
    contrasts: list[DeContrastSummary]


class ProteinDifferentialExpressionSummary(BaseModel):
    uniprot_accession: str
    gene_symbol: str
    mapping: DeMappingSemantics = Field(default_factory=DeMappingSemantics)
    dataset_total: int
    contrast_total: int
    datasets: list[DeDatasetSummary]


class VolcanoContrastMetadata(BaseModel):
    dataset_id: str
    contrast_id: str
    disease_category: str
    disease_condition: str
    tissue: str
    case_definition: str
    control_definition: str
    case_n: int
    control_n: int
    paired: bool
    design_formula: str


class VolcanoThresholds(BaseModel):
    fdr: float = 0.05
    absolute_log2fc: float = 1.0
    fdr_zero_y_clamp: float = 300.0


class VolcanoCounts(BaseModel):
    tested: int
    plotted: int
    unplottable: int
    fdr_zero: int


VolcanoPoint = tuple[
    float, float, str | None, str | None, float | None, float,
    str, bool, bool, bool, bool, bool, bool,
]


class DifferentialExpressionVolcano(BaseModel):
    uniprot_accession: str
    gene_symbol: str
    contrast: VolcanoContrastMetadata
    thresholds: VolcanoThresholds = Field(default_factory=VolcanoThresholds)
    counts: VolcanoCounts
    point_columns: list[str]
    points: list[VolcanoPoint]
