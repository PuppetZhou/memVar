"""Narrow, site-scoped evidence response models.

These models deliberately describe the scientific concepts shown in the site
dossier rather than exposing the generated Parquet rows or their raw evidence
JSON blobs.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SiteIdentity(BaseModel):
    uniprot_accession: str
    sequence_id: str
    sequence_version: int | None = None
    position: int
    reference_residue: str
    coordinate_basis: Literal["canonical_1_based"] = "canonical_1_based"


class SiteConservation(BaseModel):
    residue: str | None = None
    consensus_aa: str | None = None
    wt_frequency: float | None = None
    entropy_conservation: float | None = None
    jsd_conservation: float | None = None
    gap_frequency: float | None = None
    occupancy: float | None = None
    neff_site: float | None = None
    neff_protein: float | None = None
    alignment_scope: str | None = None
    confidence: str | None = None
    source: Literal["memVar conservation"] = "memVar conservation"


class SiteFeatureOverlap(BaseModel):
    feature_type: str
    description: str | None = None
    start: int
    end: int
    source: str


class SitePfamOverlap(BaseModel):
    pfam_accession: str
    pfam_id: str | None = None
    description: str | None = None
    pfam_type: str | None = None
    start: int
    end: int
    source: Literal["Pfam"] = "Pfam"


class SitePtmOverlap(BaseModel):
    ptm_type: str
    residue: str | None = None
    record_count: int
    pmids: list[str]
    evidence_count: int | None = None
    source: Literal["dbPTM"] = "dbPTM"


class SiteOverlaps(BaseModel):
    topology: list[SiteFeatureOverlap]
    functional: list[SiteFeatureOverlap]
    pfam: list[SitePfamOverlap]
    ptm: list[SitePtmOverlap]


class SiteStabilitySubstitution(BaseModel):
    substitution: str
    ref_aa: str
    alt_aa: str
    ddg: float
    direction: Literal[
        "predicted_stabilizing", "small_predicted_change", "predicted_destabilizing"
    ]
    genomic_variant_count: int
    pdb_name: str


class SiteStability(BaseModel):
    available: bool
    source: Literal["ThermoMPNN"] = "ThermoMPNN"
    model_name: str | None = None
    unit: Literal["kcal/mol"] = "kcal/mol"
    distinct_substitution_count: int = 0
    genomic_variant_count: int = 0
    ddg_min: float | None = None
    ddg_q25: float | None = None
    ddg_median: float | None = None
    ddg_q75: float | None = None
    ddg_max: float | None = None
    stabilizing_count: int = 0
    small_change_count: int = 0
    destabilizing_count: int = 0
    substitutions: list[SiteStabilitySubstitution]
    interpretation: str = "Predicted stability change; not functional or clinical evidence."


class CovalentEvidence(BaseModel):
    evidence_code: str | None = None
    source: str | None = None
    identifier: str | None = None


class SiteCovalentPair(BaseModel):
    pair_id: str
    feature_type: str
    start_endpoint: int
    end_endpoint: int
    start_modifier: str | None = None
    end_modifier: str | None = None
    description: str | None = None
    evidence: list[CovalentEvidence]
    source: Literal["UniProt"] = "UniProt"
    coordinate_basis: Literal["canonical_1_based_linked_endpoints"] = "canonical_1_based_linked_endpoints"


class SiteVariantPreview(BaseModel):
    variant_key: str
    hgvsp: str | None = None
    consequence: str | None = None
    source_badges: list[str]
    has_clinvar_plp_evidence: bool


class SiteVariants(BaseModel):
    total: int
    clinvar_plp_count: int
    source_counts: dict[str, int]
    preview: list[SiteVariantPreview]
    preview_limit: int
    showing: int
    has_more: bool
    anchor_semantics: Literal["one_per_canonical_drawable_variant_anchored_at_min_start"] = (
        "one_per_canonical_drawable_variant_anchored_at_min_start"
    )
    clinvar_plp_semantics: Literal["strict_clinvar_classification_presence_not_consensus"] = (
        "strict_clinvar_classification_presence_not_consensus"
    )


class SiteEvidenceSummaryResponse(BaseModel):
    identity: SiteIdentity
    conservation: SiteConservation | None = None
    overlaps: SiteOverlaps
    stability: SiteStability
    covalent_pairs: list[SiteCovalentPair]
    variants: SiteVariants
    provenance: dict[str, str]
    response_bounds: dict[str, object]
