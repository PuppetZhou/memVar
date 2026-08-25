"""M2 sequence, site, and protein-scoped variant endpoints.

Every Parquet query resolves a single deterministic accession bucket before
DuckDB is invoked.  This is an API safety boundary, not merely an optimisation.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from pathlib import Path
from typing import Literal

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from .store import get_connection, require_protein, row_dict
from .release_store import release_store
from .models import (
    ConservationBinSummary,
    CosmicEvidence,
    ExactTotal,
    SequenceResponse,
    SequenceOverviewBin,
    SequenceOverviewBounds,
    SequenceOverviewCovalentPair,
    SequenceOverviewFeatureInterval,
    SequenceOverviewPfamInterval,
    SequenceOverviewPtmSite,
    SequenceOverviewPtmType,
    SequenceOverviewResponse,
    SequenceOverviewSecondaryStructureInterval,
    SequenceOverviewTotals,
    StabilityOverviewBin,
    StabilityPrediction,
    StabilitySiteDetailResponse,
    StabilitySubstitutionItem,
    StabilityTotals,
    SequenceVariantSiteDensity,
    SequenceVariantSiteDensityResponse,
    SequenceTrackSummary,
    SequenceWindow,
    SiteResponse,
    VariantCatalogSummaryResponse,
    ClinvarAssertion,
    VariantClinvarEvidenceResponse,
    VariantCosmicEvidenceResponse,
    VariantEffectsEvidenceResponse,
    VariantFactsEvidenceResponse,
    VariantStabilityEvidenceResponse,
    VariantEffect,
    VariantFilterOption,
    VariantFilterOptionsResponse,
    VariantListResponse,
    VariantSummaryCount,
    VariantSummaryFacet,
    VariantSummaryTotal,
    PopulationFrequencyGroup,
    VariantPopulationFrequencyResponse,
    VariantSitePreviewItem,
    VariantSitePreviewResponse,
)
from .site_models import (
    CovalentEvidence,
    SiteConservation,
    SiteCovalentPair,
    SiteEvidenceSummaryResponse,
    SiteFeatureOverlap,
    SiteIdentity,
    SiteOverlaps,
    SitePfamOverlap,
    SitePtmOverlap,
    SiteStability,
    SiteStabilitySubstitution,
    SiteVariantPreview,
    SiteVariants,
)


router = APIRouter(prefix="/api/v1")

DEFAULT_WINDOW = 100
MAX_WINDOW = 500
DEFAULT_OVERVIEW_BINS = 400
MAX_OVERVIEW_BINS = 1000
MAX_OVERVIEW_SECONDARY_STRUCTURE_INTERVALS = 512
DEFAULT_VARIANT_PAGE_SIZE = 50
MAX_VARIANT_PAGE_SIZE = 200
DEFAULT_SITE_PREVIEW_LIMIT = 6
MAX_SITE_PREVIEW_LIMIT = 12
SITE_EVIDENCE_VARIANT_PREVIEW_LIMIT = 6
CLINVAR_PLP_PATTERN = (
    r"(pathogenic|likely pathogenic|pathogenic/likely pathogenic|"
    r"pathogenic/likely pathogenic/pathogenic, low penetrance|"
    r"pathogenic/pathogenic, low penetrance|"
    r"likely pathogenic/pathogenic, low penetrance|"
    r"pathogenic, low penetrance|likely pathogenic, low penetrance)(;.*)?"
)
ALLOWED_TRACKS = {"feature", "ptm", "pfam", "conservation", "covalent", "variant", "stability"}
DEFAULT_TRACKS = ("feature", "ptm", "pfam", "conservation", "covalent", "variant", "stability")
MAX_POPULATION_FREQUENCY_GROUPS = 16
POPULATION_LABELS = {
    "afr": "African / African American",
    "ami": "Amish",
    "amr": "Admixed American",
    "asj": "Ashkenazi Jewish",
    "eas": "East Asian",
    "fin": "Finnish",
    "mid": "Middle Eastern",
    "nfe": "Non-Finnish European",
    "sas": "South Asian",
    "remaining": "Remaining individuals",
}
POPULATIONS_BY_CALLSET = {
    "exome": ("afr", "amr", "asj", "eas", "fin", "mid", "nfe", "remaining", "sas"),
    "genome": ("afr", "ami", "amr", "asj", "eas", "fin", "mid", "nfe", "remaining", "sas"),
    "joint": ("afr", "ami", "amr", "asj", "eas", "fin", "mid", "nfe", "remaining", "sas"),
}
GNOMAD_UNAVAILABLE_FIELDS = ["ac", "an", "homozygote_count", "hemizygote_count"]
CLINVAR_PATHOGENICITY_CATEGORIES = (
    "benign", "pathogenic", "uncertain", "conflicting", "other", "unclassified",
)


def m2_root() -> Path:
    return release_store().path("facts")


def accession_bucket(accession: str) -> int:
    """Match the fixed polynomial hash used by ``etl/build_m2.py``."""
    return sum(
        (ord(accession[index - 1]) if index <= len(accession) else 0) * 31 ** (10 - index)
        for index in range(1, 11)
    ) % 128


def bucket_glob(accession: str, *parts: str) -> str:
    directory = m2_root().joinpath(*parts, f"accession_bucket={accession_bucket(accession)}")
    if not directory.is_dir() or not any(directory.glob("*.parquet")):
        raise HTTPException(status_code=503, detail=f"M2 data bucket is missing for: {accession}")
    return str(directory / "*.parquet")


def optional_bucket_glob(accession: str, *parts: str) -> str | None:
    directory = m2_root().joinpath(*parts, f"accession_bucket={accession_bucket(accession)}")
    if not directory.is_dir() or not any(directory.glob("*.parquet")):
        return None
    return str(directory / "*.parquet")


def population_frequency_root() -> Path:
    return release_store().variant_population_frequency


def variant_key_bucket(variant_key: str) -> int:
    return hashlib.md5(variant_key.encode("utf-8")).digest()[0]


def population_frequency_asset(variant_key: str) -> Path | None:
    path = population_frequency_root() / f"variant_bucket={variant_key_bucket(variant_key):03d}" / "data_0.parquet"
    return path if path.is_file() else None


def stability_direction(ddg: float) -> str:
    if ddg <= -0.5:
        return "predicted_stabilizing"
    if ddg >= 0.5:
        return "predicted_destabilizing"
    return "small_predicted_change"


def stability_prediction(row: tuple[object, ...] | None) -> StabilityPrediction | None:
    if row is None:
        return None
    ddg = float(row[0])
    return StabilityPrediction(
        ddg=ddg, direction=stability_direction(ddg), canonical_position=int(row[1]),
        ref_aa=str(row[2]), alt_aa=str(row[3]), pdb_name=str(row[4]),
        model_name=str(row[5]), unit=str(row[6]),
    )


def predictions_for_variants(
    connection: duckdb.DuckDBPyConnection, accession: str, variant_keys: list[str]
) -> dict[str, StabilityPrediction]:
    path = optional_bucket_glob(accession, "variant", "source", "thermompnn")
    if path is None or not variant_keys:
        return {}
    placeholders = ",".join("?" for _ in variant_keys)
    rows = connection.execute(
        f"""SELECT variant_key, ddg_pred, canonical_position, ref_aa, alt_aa,
                   pdb_name, model_name, unit
            FROM read_parquet(?)
            WHERE page_accession = ? AND variant_key IN ({placeholders})""",
        [path, accession, *variant_keys],
    ).fetchall()
    return {str(row[0]): stability_prediction(row[1:]) for row in rows}


def selected_tracks(raw: str | None) -> tuple[str, ...]:
    if raw is None or not raw.strip():
        return DEFAULT_TRACKS
    tracks = tuple(dict.fromkeys(part.strip().lower() for part in raw.split(",") if part.strip()))
    invalid = sorted(set(tracks) - ALLOWED_TRACKS)
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown track(s): {', '.join(invalid)}")
    if not tracks:
        raise HTTPException(status_code=400, detail="At least one track is required")
    return tracks


def canonical_sequence(connection: duckdb.DuckDBPyConnection, accession: str) -> dict[str, object]:
    sequence = row_dict(
        connection,
        """
        SELECT sequence_id, length, sequence, parent_canonical_sequence_version AS sequence_version
        FROM protein_sequence
        WHERE uniprot_accession = ? AND is_canonical = true
        """,
        [accession],
    )
    if sequence is None:
        raise HTTPException(status_code=500, detail=f"Canonical sequence missing for: {accession}")
    return sequence


def validated_region(length: int, start: int | None, end: int | None) -> tuple[int, int]:
    resolved_start = 1 if start is None else start
    resolved_end = min(length, resolved_start + DEFAULT_WINDOW - 1) if end is None else end
    if resolved_start < 1 or resolved_end < resolved_start or resolved_end > length:
        raise HTTPException(
            status_code=400,
            detail=f"Range must be a 1-based closed interval within 1-{length}",
        )
    if resolved_end - resolved_start + 1 > MAX_WINDOW:
        raise HTTPException(status_code=400, detail=f"Sequence window cannot exceed {MAX_WINDOW} residues")
    return resolved_start, resolved_end


def rows_as_dicts(result: duckdb.DuckDBPyConnection) -> list[dict[str, object]]:
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def source_list(value: object) -> list[str]:
    """Normalize a semicolon-delimited source list without inventing values."""
    if value is None:
        return []
    return list(dict.fromkeys(part.strip() for part in str(value).split(";") if part.strip()))


def cosmic_roles(value: object) -> list[str]:
    """Return known CGC gene roles in a stable biological display order."""
    if value is None:
        return []
    observed = {part.strip().lower() for part in str(value).split(",") if part.strip()}
    labels = (("oncogene", "oncogene"), ("tsg", "TSG"), ("fusion", "fusion"))
    return [label for key, label in labels if key in observed]


def cosmic_evidence(row: dict[str, object]) -> CosmicEvidence:
    return CosmicEvidence(
        genome_screen_sample_count=row.get("GENOME_SCREEN_SAMPLE_COUNT"),
        mondo_ids=source_list(row.get("mondo_ids")),
        disease_categories=source_list(row.get("disease_categories")),
        cgc_tier=row.get("CGC_TIER"),
        cgc_roles=cosmic_roles(row.get("ONC_TSG")),
    )


def build_scope() -> str | None:
    path = release_store().variant_catalog
    if not path.is_file():
        return None
    connection = duckdb.connect(str(path), read_only=True)
    try:
        row = connection.execute("SELECT scope FROM build_scope LIMIT 1").fetchone()
        return None if row is None else row[0]
    finally:
        connection.close()


def track_count(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    track: str,
) -> SequenceTrackSummary:
    if track == "stability":
        path = optional_bucket_glob(accession, "sequence", "stability_site")
        if path is None:
            return SequenceTrackSummary(track=track, count=0, drawable_count=0)
        count = connection.execute(
            "SELECT count(*) FROM read_parquet(?) WHERE uniprot_accession = ?",
            [path, accession],
        ).fetchone()[0]
        return SequenceTrackSummary(track=track, count=count, drawable_count=count)
    if track == "variant":
        path = bucket_glob(accession, "variant", "effect")
        count, drawable = connection.execute(
            """SELECT count(*), count(*) FILTER (WHERE is_drawable)
               FROM read_parquet(?) WHERE uniprot_accession = ?""",
            [path, accession],
        ).fetchone()
    else:
        dataset = {
            "feature": "feature_interval", "ptm": "ptm_site", "pfam": "pfam_interval",
            "conservation": "conservation_tile", "covalent": "covalent_pair",
        }[track]
        path = bucket_glob(accession, "sequence", dataset)
        if track == "feature":
            drawable_expression = "start_position IS NOT NULL AND end_position IS NOT NULL AND coordinate_basis = 'canonical'"
        elif track == "pfam":
            drawable_expression = "env_start IS NOT NULL AND env_end IS NOT NULL"
        elif track == "covalent":
            drawable_expression = "start_position IS NOT NULL AND end_position IS NOT NULL AND coordinate_basis = 'canonical'"
        else:
            drawable_expression = "position IS NOT NULL"
        count, drawable = connection.execute(
            f"SELECT count(*), count(*) FILTER (WHERE {drawable_expression}) "
            "FROM read_parquet(?) WHERE uniprot_accession = ?",
            [path, accession],
        ).fetchone()
    return SequenceTrackSummary(track=track, count=count, drawable_count=drawable)


def overview_feature_intervals(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    length: int,
    track_group: Literal["topology", "functional_site"],
) -> list[SequenceOverviewFeatureInterval]:
    path = bucket_glob(accession, "sequence", "feature_interval")
    rows = connection.execute(
        """
        SELECT feature_type, CAST(start_position AS BIGINT), CAST(end_position AS BIGINT),
               description, feature_id, start_modifier, end_modifier
        FROM read_parquet(?)
        WHERE uniprot_accession = ? AND coordinate_basis = 'canonical'
          AND track_group = ?
          AND start_position IS NOT NULL AND end_position IS NOT NULL
          AND start_position = trunc(start_position) AND end_position = trunc(end_position)
          AND start_position BETWEEN 1 AND ? AND end_position BETWEEN 1 AND ?
          AND start_position <= end_position
        ORDER BY start_position, end_position, feature_type, feature_id NULLS LAST
        """,
        [path, accession, track_group, length, length],
    ).fetchall()
    return [
        SequenceOverviewFeatureInterval(
            feature_type=row[0], start=row[1], end=row[2], description=row[3],
            feature_id=row[4], start_modifier=row[5], end_modifier=row[6],
        )
        for row in rows
    ]


def overview_secondary_structure_intervals(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    length: int,
) -> tuple[list[SequenceOverviewSecondaryStructureInterval], int]:
    """Return bounded canonical UniProt Helix, Beta strand, and Turn intervals.

    These are feature-table annotations, not structural predictions or PDB-derived
    assignments.  The exact total is retained separately so callers can disclose
    a future truncation without widening the overview payload.
    """
    path = bucket_glob(accession, "sequence", "feature_interval")
    rows = connection.execute(
        """
        SELECT feature_type, CAST(start_position AS BIGINT), CAST(end_position AS BIGINT),
               description, feature_id, start_modifier, end_modifier,
               count(*) OVER () AS total_intervals
        FROM read_parquet(?)
        WHERE uniprot_accession = ? AND coordinate_basis = 'canonical'
          AND track_group = 'secondary_structure'
          AND feature_type IN ('Helix', 'Beta strand', 'Turn')
          AND start_position IS NOT NULL AND end_position IS NOT NULL
          AND start_position = trunc(start_position) AND end_position = trunc(end_position)
          AND start_position BETWEEN 1 AND ? AND end_position BETWEEN 1 AND ?
          AND start_position <= end_position
        ORDER BY start_position, end_position, feature_type, feature_id NULLS LAST
        LIMIT ?
        """,
        [path, accession, length, length, MAX_OVERVIEW_SECONDARY_STRUCTURE_INTERVALS],
    ).fetchall()
    intervals = [
        SequenceOverviewSecondaryStructureInterval(
            feature_type=row[0], start=row[1], end=row[2], description=row[3],
            feature_id=row[4], start_modifier=row[5], end_modifier=row[6],
        )
        for row in rows
    ]
    return intervals, (int(rows[0][7]) if rows else 0)


def overview_pfam_intervals(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    length: int,
) -> list[SequenceOverviewPfamInterval]:
    path = bucket_glob(accession, "sequence", "pfam_interval")
    rows = connection.execute(
        """
        SELECT pfam_accession, pfam_id, pfam_description, pfam_type, clan_id, clan_name,
               env_start, env_end
        FROM read_parquet(?)
        WHERE uniprot_accession = ?
          AND env_start IS NOT NULL AND env_end IS NOT NULL
          AND env_start BETWEEN 1 AND ? AND env_end BETWEEN 1 AND ? AND env_start <= env_end
        ORDER BY env_start, env_end, pfam_accession
        """,
        [path, accession, length, length],
    ).fetchall()
    return [
        SequenceOverviewPfamInterval(
            pfam_accession=row[0], pfam_id=row[1], description=row[2], pfam_type=row[3],
            clan_id=row[4], clan_name=row[5], start=row[6], end=row[7],
        )
        for row in rows
    ]


def overview_variant_site_density(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    length: int,
) -> tuple[SequenceVariantSiteDensity, int]:
    effect_path = bucket_glob(accession, "variant", "effect")
    clinvar_path = bucket_glob(accession, "variant", "source", "clinvar")
    rows = connection.execute(
        """
        WITH canonical_source AS (
          SELECT variant_key, protein_start, is_drawable
          FROM read_parquet(?)
          WHERE uniprot_accession = ? AND effect_scope = 'canonical'
        ), anchors AS (
          SELECT variant_key, min(CAST(protein_start AS BIGINT)) AS anchor_position
          FROM canonical_source
          WHERE is_drawable AND protein_start BETWEEN 1 AND ?
          GROUP BY variant_key
        ), clinvar_flags AS (
          SELECT variant_key,
                 bool_or(regexp_full_match(
                   lower(trim(coalesce(ClinicalSignificance, ''))), ?
                 )) AS has_clinvar_plp_evidence
          FROM read_parquet(?)
          WHERE page_accession = ?
          GROUP BY variant_key
        ), site_counts AS (
          SELECT anchor_position,
                 count(*) AS total_count,
                 count(*) FILTER (
                   WHERE coalesce(has_clinvar_plp_evidence, false)
                 ) AS clinvar_plp_count
          FROM anchors
          LEFT JOIN clinvar_flags USING (variant_key)
          GROUP BY anchor_position
        ), positions AS (
          SELECT range AS position FROM range(1, ? + 1)
        )
        SELECT p.position, coalesce(s.total_count, 0), coalesce(s.clinvar_plp_count, 0),
               (SELECT count(DISTINCT variant_key) FROM canonical_source) AS canonical_total
        FROM positions p
        LEFT JOIN site_counts s ON s.anchor_position = p.position
        ORDER BY p.position
        """,
        [
            effect_path, accession, length, CLINVAR_PLP_PATTERN,
            clinvar_path, accession, length,
        ],
    ).fetchall()
    total_counts = [int(row[1]) for row in rows]
    clinvar_plp_counts = [int(row[2]) for row in rows]
    return (
        SequenceVariantSiteDensity(
            end=length,
            total_counts=total_counts,
            clinvar_plp_counts=clinvar_plp_counts,
        ),
        int(rows[0][3]),
    )


def overview_ptm_sites(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    length: int,
) -> tuple[list[SequenceOverviewPtmSite], list[SequenceOverviewPtmType], int]:
    path = bucket_glob(accession, "sequence", "ptm_site")
    record_total = int(connection.execute(
        "SELECT count(*) FROM read_parquet(?) WHERE uniprot_accession = ?",
        [path, accession],
    ).fetchone()[0])
    rows = connection.execute(
        """
        SELECT CAST(position AS BIGINT) AS position, residue, ptm_type, count(*) AS record_count
        FROM read_parquet(?)
        WHERE uniprot_accession = ? AND position BETWEEN 1 AND ?
          AND position = trunc(position) AND ptm_type IS NOT NULL AND trim(ptm_type) <> ''
        GROUP BY position, residue, ptm_type
        ORDER BY position, lower(ptm_type), ptm_type, residue NULLS LAST
        """,
        [path, accession, length],
    ).fetchall()
    grouped: dict[int, dict[str, object]] = {}
    type_counts: dict[str, int] = {}
    for position, residue, ptm_type, count in rows:
        site = grouped.setdefault(
            int(position),
            {"residue": residue, "total_count": 0, "types": []},
        )
        site["total_count"] = int(site["total_count"]) + int(count)
        site["types"].append(SequenceOverviewPtmType(ptm_type=ptm_type, count=count))
        type_counts[ptm_type] = type_counts.get(ptm_type, 0) + int(count)
    sites = [
        SequenceOverviewPtmSite(
            position=position,
            residue=values["residue"],
            total_count=values["total_count"],
            types=values["types"],
        )
        for position, values in grouped.items()
    ]
    counts = [
        SequenceOverviewPtmType(ptm_type=ptm_type, count=count)
        for ptm_type, count in sorted(
            type_counts.items(), key=lambda item: (-item[1], item[0].lower(), item[0])
        )
    ]
    return sites, counts, record_total


def overview_covalent_pairs(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    length: int,
) -> list[SequenceOverviewCovalentPair]:
    path = bucket_glob(accession, "sequence", "covalent_pair")
    rows = connection.execute(
        """
        SELECT feature_type, CAST(start_position AS BIGINT), CAST(end_position AS BIGINT),
               start_modifier, end_modifier, description, feature_id
        FROM read_parquet(?)
        WHERE uniprot_accession = ? AND coordinate_basis = 'canonical'
          AND start_position IS NOT NULL AND end_position IS NOT NULL
          AND start_position = trunc(start_position) AND end_position = trunc(end_position)
          AND start_position BETWEEN 1 AND ? AND end_position BETWEEN 1 AND ?
        ORDER BY start_position, end_position, feature_type, feature_id NULLS LAST
        """,
        [path, accession, length, length],
    ).fetchall()
    return [
        SequenceOverviewCovalentPair(
            feature_type=row[0], start_endpoint=row[1], end_endpoint=row[2],
            start_modifier=row[3], end_modifier=row[4], description=row[5], feature_id=row[6],
        )
        for row in rows
    ]


def overview_density_bins(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    length: int,
    bin_count: int,
    variant_site_counts: list[int],
    ptm_sites: list[SequenceOverviewPtmSite],
) -> tuple[list[SequenceOverviewBin], int]:
    conservation_path = bucket_glob(accession, "sequence", "conservation_tile")
    rows = connection.execute(
        """
        WITH conservation_source AS (
          SELECT *, CAST(floor((position * ? - 1) / ?) AS INTEGER) AS bin_index
          FROM read_parquet(?)
          WHERE uniprot_accession = ? AND position BETWEEN 1 AND ?
        ), conservation AS (
          SELECT bin_index, count(*) AS observation_count,
                 avg(jsd_conservation) AS jsd_mean,
                 min(jsd_conservation) AS jsd_min,
                 max(jsd_conservation) AS jsd_max,
                 count(*) FILTER (WHERE confidence IS NULL) AS confidence_missing_count
          FROM conservation_source
          GROUP BY bin_index
        ), confidence_category AS (
          SELECT bin_index, confidence, count(*) AS category_count
          FROM conservation_source WHERE confidence IS NOT NULL
          GROUP BY bin_index, confidence
        ), confidence AS (
          SELECT bin_index, json_group_object(confidence, category_count) AS confidence_counts_json
          FROM confidence_category GROUP BY bin_index
        ), indices AS (
          SELECT range AS bin_index FROM range(?)
        )
        SELECT i.bin_index, coalesce(c.observation_count, 0), c.jsd_mean, c.jsd_min, c.jsd_max,
               coalesce(cf.confidence_counts_json, '{}'), coalesce(c.confidence_missing_count, 0)
        FROM indices i
        LEFT JOIN conservation c USING (bin_index)
        LEFT JOIN confidence cf USING (bin_index)
        ORDER BY i.bin_index
        """,
        [
            bin_count, length, conservation_path, accession, length, bin_count,
        ],
    ).fetchall()

    bins: list[SequenceOverviewBin] = []
    for row in rows:
        index = int(row[0])
        bins.append(SequenceOverviewBin(
            index=index,
            start=index * length // bin_count + 1,
            end=(index + 1) * length // bin_count,
            conservation=ConservationBinSummary(
                observation_count=row[1], jsd_mean=row[2], jsd_min=row[3], jsd_max=row[4],
                confidence_counts=json.loads(row[5]), confidence_missing_count=row[6],
            ),
            ptm_count=sum(
                site.total_count for site in ptm_sites
                if index * length // bin_count < site.position <= (index + 1) * length // bin_count
            ),
            variant_count=sum(
                variant_site_counts[index * length // bin_count:(index + 1) * length // bin_count]
            ),
        ))
    return (
        bins,
        sum(item.conservation.observation_count for item in bins),
    )


def overview_stability_bins(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    length: int,
    bin_count: int,
) -> tuple[list[StabilityOverviewBin], StabilityTotals]:
    path = optional_bucket_glob(accession, "sequence", "stability_site")
    prediction_path = optional_bucket_glob(accession, "variant", "source", "thermompnn")
    effect_path = bucket_glob(accession, "variant", "effect")
    empty = [
        StabilityOverviewBin(
            index=index, start=index * length // bin_count + 1,
            end=(index + 1) * length // bin_count,
            observation_count=0, distinct_substitution_count=0,
        )
        for index in range(bin_count)
    ]
    if path is None or prediction_path is None:
        return empty, StabilityTotals(
            predicted_variants=0, canonical_sites=0, distinct_substitutions=0,
        )
    rows = connection.execute(
        """
        WITH drawable AS (
          SELECT DISTINCT variant_key, uniprot_accession,
                 CAST(protein_start AS BIGINT) AS canonical_position, ref_aa, alt_aa
          FROM read_parquet(?)
          WHERE uniprot_accession = ? AND effect_scope = 'canonical' AND is_drawable
        ), substitution AS (
          SELECT p.canonical_position, p.ref_aa, p.alt_aa, avg(p.ddg_pred) AS ddg_pred
          FROM read_parquet(?) p JOIN drawable d
            ON d.variant_key = p.variant_key
           AND d.uniprot_accession = p.page_accession
           AND d.canonical_position = p.canonical_position
           AND d.ref_aa = p.ref_aa AND d.alt_aa = p.alt_aa
          WHERE p.page_accession = ? AND p.canonical_position BETWEEN 1 AND ?
          GROUP BY p.canonical_position, p.ref_aa, p.alt_aa
        ), source AS (
          SELECT *, CAST(floor((canonical_position * ? - 1) / ?) AS INTEGER) AS bin_index
          FROM substitution
        ), grouped AS (
          SELECT bin_index, count(DISTINCT canonical_position) AS observation_count,
                 count(*) AS distinct_substitution_count,
                 min(ddg_pred) AS ddg_min,
                 quantile_cont(ddg_pred, 0.25) AS ddg_q25,
                 median(ddg_pred) AS ddg_median,
                 quantile_cont(ddg_pred, 0.75) AS ddg_q75,
                 max(ddg_pred) AS ddg_max
          FROM source GROUP BY bin_index
        ), indices AS (SELECT range AS bin_index FROM range(?))
        SELECT i.bin_index, coalesce(g.observation_count, 0),
               coalesce(g.distinct_substitution_count, 0),
               g.ddg_min, g.ddg_q25, g.ddg_median, g.ddg_q75, g.ddg_max
        FROM indices i LEFT JOIN grouped g USING (bin_index)
        ORDER BY i.bin_index
        """,
        [effect_path, accession, prediction_path, accession, length, bin_count, length, bin_count],
    ).fetchall()
    totals = connection.execute(
        """
        SELECT sum(genomic_variant_count), count(*), sum(distinct_substitution_count)
        FROM read_parquet(?) WHERE uniprot_accession = ?
        """,
        [path, accession],
    ).fetchone()
    return [
        StabilityOverviewBin(
            index=int(row[0]), start=int(row[0]) * length // bin_count + 1,
            end=(int(row[0]) + 1) * length // bin_count,
            observation_count=int(row[1]), distinct_substitution_count=int(row[2]),
            ddg_min=row[3], ddg_q25=row[4], ddg_median=row[5],
            ddg_q75=row[6], ddg_max=row[7],
        )
        for row in rows
    ], StabilityTotals(
        predicted_variants=int(totals[0] or 0), canonical_sites=int(totals[1] or 0),
        distinct_substitutions=int(totals[2] or 0),
    )


@router.get(
    "/proteins/{acc}/sequence/variant-site-density",
    response_model=SequenceVariantSiteDensityResponse,
)
def sequence_variant_site_density(
    acc: str,
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> SequenceVariantSiteDensityResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    sequence = row_dict(
        connection,
        """
        SELECT length, parent_canonical_sequence_version AS sequence_version
        FROM protein_sequence
        WHERE uniprot_accession = ? AND is_canonical = true
        """,
        [accession],
    )
    if sequence is None:
        raise HTTPException(status_code=500, detail=f"Canonical sequence missing for: {accession}")
    length = int(sequence["length"])
    density, _ = overview_variant_site_density(connection, accession, length)
    return SequenceVariantSiteDensityResponse(
        uniprot_accession=accession,
        canonical_length=length,
        sequence_version=sequence["sequence_version"],
        variant_site_density=density,
    )


@router.get("/proteins/{acc}/sequence/overview", response_model=SequenceOverviewResponse)
def sequence_overview(
    acc: str,
    bins: int = Query(default=DEFAULT_OVERVIEW_BINS, ge=1, le=MAX_OVERVIEW_BINS),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> SequenceOverviewResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    sequence = canonical_sequence(connection, accession)
    length = int(sequence["length"])
    returned_bins = min(bins, length)
    topology = overview_feature_intervals(connection, accession, length, "topology")
    functional = overview_feature_intervals(connection, accession, length, "functional_site")
    secondary_structure, secondary_structure_total = overview_secondary_structure_intervals(
        connection, accession, length
    )
    pfam = overview_pfam_intervals(connection, accession, length)
    variant_site_density, variant_total = overview_variant_site_density(
        connection, accession, length
    )
    ptm_sites, ptm_type_counts, ptm_total = overview_ptm_sites(connection, accession, length)
    covalent_pairs = overview_covalent_pairs(connection, accession, length)
    density, conservation_total = overview_density_bins(
        connection, accession, length, returned_bins,
        variant_site_density.total_counts, ptm_sites,
    )
    stability_bins, stability_totals = overview_stability_bins(
        connection, accession, length, returned_bins,
    )
    ptm_drawable_total = sum(site.total_count for site in ptm_sites)
    variant_drawable_total = sum(variant_site_density.total_counts)
    return SequenceOverviewResponse(
        uniprot_accession=accession,
        sequence_id=str(sequence["sequence_id"]),
        canonical_length=length,
        canonical_sequence=str(sequence["sequence"]),
        sequence_version=sequence["sequence_version"],
        topology_intervals=topology,
        pfam_intervals=pfam,
        functional_intervals=functional,
        secondary_structure_intervals=secondary_structure,
        density_bins=density,
        stability_bins=stability_bins,
        stability_totals=stability_totals,
        variant_site_density=variant_site_density,
        ptm_sites=ptm_sites,
        ptm_type_counts=ptm_type_counts,
        covalent_pairs=covalent_pairs,
        totals=SequenceOverviewTotals(
            topology_intervals=len(topology), pfam_intervals=len(pfam),
            functional_intervals=len(functional),
            secondary_structure_intervals=secondary_structure_total,
            conservation_positions=conservation_total,
            ptm_records=ptm_total, ptm_drawable_records=ptm_drawable_total,
            canonical_variants=variant_total, canonical_drawable_variants=variant_drawable_total,
        ),
        response_bounds=SequenceOverviewBounds(
            requested_bins=bins, returned_bins=returned_bins, max_bins=MAX_OVERVIEW_BINS,
            secondary_structure_intervals_returned=len(secondary_structure),
            max_secondary_structure_intervals=MAX_OVERVIEW_SECONDARY_STRUCTURE_INTERVALS,
            secondary_structure_intervals_complete=(
                secondary_structure_total <= MAX_OVERVIEW_SECONDARY_STRUCTURE_INTERVALS
            ),
        ),
    )


@router.get("/proteins/{acc}/sequence", response_model=SequenceResponse)
def sequence_window(
    acc: str,
    start: int | None = Query(default=None),
    end: int | None = Query(default=None),
    tracks: str | None = Query(default=None),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> SequenceResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    sequence = canonical_sequence(connection, accession)
    region_start, region_end = validated_region(int(sequence["length"]), start, end)
    requested = selected_tracks(tracks)
    return SequenceResponse(
        uniprot_accession=accession,
        sequence_id=str(sequence["sequence_id"]),
        length=int(sequence["length"]),
        sequence_version=sequence["sequence_version"],
        build_context={"milestone": "M2", "scope": build_scope()},
        window=SequenceWindow(
            start=region_start,
            end=region_end,
            sequence=str(sequence["sequence"])[region_start - 1:region_end],
        ),
        tracks=[track_count(connection, accession, track) for track in requested],
    )


def site_track_rows(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    track: str,
    start: int,
    end: int,
) -> list[dict[str, object]]:
    if track == "feature":
        path = bucket_glob(accession, "sequence", "feature_interval")
        return rows_as_dicts(connection.execute(
            """
            SELECT sequence_version, feature_category, feature_type,
                   CAST(start_position AS BIGINT) AS start, CAST(end_position AS BIGINT) AS end,
                   start_modifier, end_modifier, description, feature_id, evidence_json,
                   coordinate_basis, track_group, 'UniProt' AS source, 'drawable' AS status
            FROM read_parquet(?)
            WHERE uniprot_accession = ? AND coordinate_basis = 'canonical'
              AND start_position IS NOT NULL AND end_position IS NOT NULL
              AND start_position <= ? AND end_position >= ?
            ORDER BY start_position, end_position, feature_type
            """, [path, accession, end, start]))
    if track == "ptm":
        path = bucket_glob(accession, "sequence", "ptm_site")
        return rows_as_dicts(connection.execute(
            """
            SELECT sequence_version, CAST(position AS BIGINT) AS position, residue, ptm_type,
                   pmid, source_evidence_count, 'dbPTM' AS source,
                   'canonical_1_based' AS coordinate_basis, 'drawable' AS status
            FROM read_parquet(?) WHERE uniprot_accession = ? AND position BETWEEN ? AND ?
            ORDER BY position, ptm_type
            """, [path, accession, start, end]))
    if track == "pfam":
        path = bucket_glob(accession, "sequence", "pfam_interval")
        return rows_as_dicts(connection.execute(
            """
            SELECT pfam_accession, pfam_id, pfam_description, pfam_type, clan_id, clan_name,
                   env_start AS start, env_end AS end, ali_start, ali_end, hmm_start, hmm_end,
                   domain_i_evalue, domain_score, pfam_release, 'Pfam' AS source,
                   'canonical_1_based_closed' AS coordinate_basis, 'drawable' AS status
            FROM read_parquet(?) WHERE uniprot_accession = ?
              AND env_start IS NOT NULL AND env_end IS NOT NULL AND env_start <= ? AND env_end >= ?
            ORDER BY env_start, env_end, pfam_accession
            """, [path, accession, end, start]))
    if track == "conservation":
        path = bucket_glob(accession, "sequence", "conservation_tile")
        return rows_as_dicts(connection.execute(
            """
            SELECT sequence_version, position, residue, consensus_aa, wt_frequency,
                   entropy_conservation, jsd_conservation, gap_frequency, occupancy,
                   neff_site, neff_protein, alignment_scope, confidence,
                   'memVar conservation' AS source, 'canonical_1_based' AS coordinate_basis,
                   'drawable' AS status
            FROM read_parquet(?) WHERE uniprot_accession = ? AND position BETWEEN ? AND ?
            ORDER BY position
            """, [path, accession, start, end]))
    if track == "covalent":
        path = bucket_glob(accession, "sequence", "covalent_pair")
        return rows_as_dicts(connection.execute(
            """
            SELECT sequence_version, feature_category, feature_type,
                   CAST(start_position AS BIGINT) AS start_endpoint,
                   CAST(end_position AS BIGINT) AS end_endpoint,
                   start_modifier, end_modifier, description, feature_id, evidence_json,
                   coordinate_basis, 'UniProt' AS source, 'linked_endpoints' AS status
            FROM read_parquet(?)
            WHERE uniprot_accession = ? AND coordinate_basis = 'canonical'
              AND start_position IS NOT NULL AND end_position IS NOT NULL
              AND (start_position BETWEEN ? AND ? OR end_position BETWEEN ? AND ?)
            ORDER BY start_position, end_position
            """, [path, accession, start, end, start, end]))
    if track == "stability":
        path = optional_bucket_glob(accession, "sequence", "stability_site")
        if path is None:
            return []
        return rows_as_dicts(connection.execute(
            """
            SELECT canonical_position AS position, ref_aa,
                   distinct_substitution_count, genomic_variant_count,
                   ddg_min, ddg_q25, ddg_median, ddg_q75, ddg_max,
                   stabilizing_count, small_change_count, destabilizing_count,
                   'ThermoMPNN' AS source, 'kcal/mol' AS unit,
                   'canonical_1_based' AS coordinate_basis
            FROM read_parquet(?)
            WHERE uniprot_accession = ? AND canonical_position BETWEEN ? AND ?
            ORDER BY canonical_position
            """,
            [path, accession, start, end],
        ))
    path = bucket_glob(accession, "variant", "effect")
    return rows_as_dicts(connection.execute(
        """
        WITH ranked AS (
          SELECT variant_key, effect_scope, Consequence AS consequence, HGVSp AS hgvsp,
                 CAST(protein_start AS BIGINT) AS anchor_start,
                 CAST(protein_end AS BIGINT) AS anchor_end,
                 ref_aa, alt_aa, site_parse_status AS status, is_drawable,
                 row_number() OVER (
                   PARTITION BY variant_key
                   ORDER BY protein_start, protein_end, is_representative_effect DESC NULLS LAST,
                            HGVSp NULLS LAST, Consequence NULLS LAST
                 ) AS anchor_rank
          FROM read_parquet(?)
          WHERE uniprot_accession = ? AND is_drawable
            AND effect_scope = 'canonical' AND protein_start IS NOT NULL
        )
        SELECT variant_key, effect_scope, consequence, hgvsp,
               anchor_start AS start, anchor_end AS "end", ref_aa, alt_aa,
               status, is_drawable, 'variant_protein_effect' AS source,
               'canonical_1_based_closed' AS coordinate_basis
        FROM ranked
        WHERE anchor_rank = 1 AND anchor_start BETWEEN ? AND ?
        ORDER BY anchor_start, anchor_end, variant_key
        """, [path, accession, start, end]))


@router.get("/proteins/{acc}/sites", response_model=SiteResponse)
def sites(
    acc: str,
    start: int | None = Query(default=None),
    end: int | None = Query(default=None),
    tracks: str | None = Query(default=None),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> SiteResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    sequence = canonical_sequence(connection, accession)
    region_start, region_end = validated_region(int(sequence["length"]), start, end)
    requested = selected_tracks(tracks)
    grouped = {
        track: site_track_rows(connection, accession, track, region_start, region_end)
        for track in requested
    }
    bin_size = max(1, (region_end - region_start + 1 + 49) // 50)
    density: list[dict[str, object]] = []
    for bin_start in range(region_start, region_end + 1, bin_size):
        bin_end = min(region_end, bin_start + bin_size - 1)
        counts: dict[str, int] = {}
        for track, items in grouped.items():
            if track == "variant":
                counts[track] = sum(
                    item.get("start") is not None and bin_start <= int(item["start"]) <= bin_end
                    for item in items
                )
                continue

            def item_overlaps(item: dict[str, object]) -> bool:
                point = item.get("position")
                left = item.get("start", item.get("start_endpoint", point))
                right = item.get("end", item.get("end_endpoint", point))
                return left is not None and right is not None and int(left) <= bin_end and int(right) >= bin_start
            counts[track] = sum(item_overlaps(item) for item in items)
        density.append({"start": bin_start, "end": bin_end, "counts": counts})
    return SiteResponse(
        uniprot_accession=accession,
        sequence_version=sequence["sequence_version"],
        variant_density_semantics="one_per_canonical_drawable_variant_anchored_at_min_start",
        region={"start": region_start, "end": region_end},
        tracks=grouped,
        density=density,
        summary={track: len(items) for track, items in grouped.items()},
        applied_filters={"start": region_start, "end": region_end, "tracks": list(requested)},
    )


@router.get(
    "/proteins/{acc}/stability/sites/{position}",
    response_model=StabilitySiteDetailResponse,
)
def stability_site_detail(
    acc: str,
    position: int,
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> StabilitySiteDetailResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    sequence = canonical_sequence(connection, accession)
    length = int(sequence["length"])
    if position < 1 or position > length:
        raise HTTPException(status_code=422, detail=f"Position must be between 1 and {length}")
    prediction_path = optional_bucket_glob(accession, "variant", "source", "thermompnn")
    ref_aa = str(sequence["sequence"])[position - 1]
    if prediction_path is None:
        return StabilitySiteDetailResponse(
            uniprot_accession=accession, position=position, ref_aa=ref_aa,
            substitutions=[], response_bounds={"complete": True, "max_substitutions": 19},
        )
    effect_path = bucket_glob(accession, "variant", "effect")
    rows = connection.execute(
        """
        WITH drawable AS (
          SELECT DISTINCT variant_key, uniprot_accession,
                 CAST(protein_start AS BIGINT) AS canonical_position, ref_aa, alt_aa
          FROM read_parquet(?)
          WHERE uniprot_accession = ? AND effect_scope = 'canonical' AND is_drawable
            AND protein_start = ?
        )
        SELECT p.ref_aa, p.alt_aa, avg(p.ddg_pred) AS ddg,
               count(DISTINCT p.variant_key) AS genomic_variant_count,
               any_value(p.pdb_name) AS pdb_name
        FROM read_parquet(?) p JOIN drawable d
          ON d.variant_key = p.variant_key
         AND d.uniprot_accession = p.page_accession
         AND d.canonical_position = p.canonical_position
         AND d.ref_aa = p.ref_aa AND d.alt_aa = p.alt_aa
        WHERE p.page_accession = ? AND p.canonical_position = ?
        GROUP BY p.ref_aa, p.alt_aa
        ORDER BY ddg, p.alt_aa
        LIMIT 19
        """,
        [effect_path, accession, position, prediction_path, accession, position],
    ).fetchall()
    substitutions = [
        StabilitySubstitutionItem(
            substitution=f"{row[0]}{position}{row[1]}", ref_aa=str(row[0]),
            alt_aa=str(row[1]), ddg=float(row[2]),
            direction=stability_direction(float(row[2])),
            genomic_variant_count=int(row[3]), pdb_name=str(row[4]),
        )
        for row in rows
    ]
    return StabilitySiteDetailResponse(
        uniprot_accession=accession, position=position,
        ref_aa=(substitutions[0].ref_aa if substitutions else ref_aa),
        ddg_min=(min(item.ddg for item in substitutions) if substitutions else None),
        ddg_max=(max(item.ddg for item in substitutions) if substitutions else None),
        substitutions=substitutions,
        response_bounds={"complete": len(rows) <= 19, "max_substitutions": 19},
    )


def covalent_evidence(value: object) -> list[CovalentEvidence]:
    """Parse the compact UniProt evidence records without exposing raw JSON."""
    try:
        records = json.loads(str(value or "[]"))
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=500, detail="Invalid covalent evidence record") from error
    if not isinstance(records, list) or any(not isinstance(record, dict) for record in records):
        raise HTTPException(status_code=500, detail="Invalid covalent evidence record")
    return [
        CovalentEvidence(
            evidence_code=record.get("evidenceCode"), source=record.get("source"),
            identifier=record.get("id"),
        )
        for record in records
    ]


def covalent_pair_id(
    accession: str,
    feature_type: object,
    start_endpoint: object,
    end_endpoint: object,
    start_modifier: object,
    end_modifier: object,
    description: object,
    feature_id: object,
    evidence_json: object,
) -> str:
    """Create an endpoint-invariant covalent identity for a canonical pair."""
    if feature_id is not None:
        return f"{accession}:feature:{feature_id}"
    payload = json.dumps({
        "feature_type": feature_type,
        "start_endpoint": start_endpoint,
        "end_endpoint": end_endpoint,
        "start_modifier": start_modifier,
        "end_modifier": end_modifier,
        "description": description,
        "evidence_json": evidence_json,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"{accession}:pair:{digest}"


@router.get(
    "/proteins/{acc}/sites/{position}/summary",
    response_model=SiteEvidenceSummaryResponse,
)
def site_evidence_summary(
    acc: str,
    position: int,
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> SiteEvidenceSummaryResponse:
    """Return a bounded, canonical-site evidence dossier.

    Every data read remains scoped to the one deterministic accession bucket;
    the endpoint intentionally returns compact typed evidence, never feature or
    covalent raw JSON blobs and never an unbounded variant collection.
    """
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    sequence = canonical_sequence(connection, accession)
    sequence_text = str(sequence["sequence"])
    length = int(sequence["length"])
    if position < 1 or position > length:
        raise HTTPException(status_code=422, detail=f"Position must be between 1 and {length}")

    conservation_path = bucket_glob(accession, "sequence", "conservation_tile")
    conservation_row = connection.execute(
        """
        SELECT residue, consensus_aa, wt_frequency, entropy_conservation,
               jsd_conservation, gap_frequency, occupancy, neff_site,
               neff_protein, alignment_scope, confidence
        FROM read_parquet(?)
        WHERE uniprot_accession = ? AND position = ?
        """, [conservation_path, accession, position],
    ).fetchone()
    if conservation_row is not None and conservation_row[0] is not None and conservation_row[0] != sequence_text[position - 1]:
        raise HTTPException(status_code=500, detail="Conservation residue disagrees with canonical sequence")
    conservation = None if conservation_row is None else SiteConservation(
        residue=conservation_row[0], consensus_aa=conservation_row[1],
        wt_frequency=conservation_row[2], entropy_conservation=conservation_row[3],
        jsd_conservation=conservation_row[4], gap_frequency=conservation_row[5],
        occupancy=conservation_row[6], neff_site=conservation_row[7],
        neff_protein=conservation_row[8], alignment_scope=conservation_row[9],
        confidence=conservation_row[10],
    )

    feature_path = bucket_glob(accession, "sequence", "feature_interval")
    feature_rows = connection.execute(
        """
        SELECT track_group, feature_type, description,
               CAST(start_position AS BIGINT), CAST(end_position AS BIGINT)
        FROM read_parquet(?)
        WHERE uniprot_accession = ? AND coordinate_basis = 'canonical'
          AND track_group IN ('topology', 'functional_site')
          AND start_position IS NOT NULL AND end_position IS NOT NULL
          AND start_position <= ? AND end_position >= ?
        ORDER BY track_group, start_position, end_position, feature_type
        """, [feature_path, accession, position, position],
    ).fetchall()
    topology = [
        SiteFeatureOverlap(feature_type=row[1], description=row[2], start=row[3], end=row[4], source="UniProt")
        for row in feature_rows if row[0] == "topology"
    ]
    functional = [
        SiteFeatureOverlap(feature_type=row[1], description=row[2], start=row[3], end=row[4], source="UniProt")
        for row in feature_rows if row[0] == "functional_site"
    ]
    pfam_path = bucket_glob(accession, "sequence", "pfam_interval")
    pfam = [
        SitePfamOverlap(
            pfam_accession=row[0], pfam_id=row[1], description=row[2], pfam_type=row[3],
            start=row[4], end=row[5],
        )
        for row in connection.execute(
            """
            SELECT pfam_accession, pfam_id, pfam_description, pfam_type, env_start, env_end
            FROM read_parquet(?)
            WHERE uniprot_accession = ? AND env_start <= ? AND env_end >= ?
            ORDER BY env_start, env_end, pfam_accession
            """, [pfam_path, accession, position, position],
        ).fetchall()
    ]
    ptm_path = bucket_glob(accession, "sequence", "ptm_site")
    ptm = [
        SitePtmOverlap(
            ptm_type=row[0], residue=row[1], record_count=int(row[2]),
            pmids=[str(pmid) for pmid in (row[3] or []) if pmid is not None], evidence_count=row[4],
        )
        for row in connection.execute(
            """
            SELECT ptm_type, any_value(residue), count(*) AS record_count,
                   list_sort(list_distinct(list(pmid) FILTER (WHERE pmid IS NOT NULL))) AS pmids,
                   max(source_evidence_count) AS evidence_count
            FROM read_parquet(?)
            WHERE uniprot_accession = ? AND position = ?
            GROUP BY ptm_type
            ORDER BY lower(ptm_type), ptm_type
            """, [ptm_path, accession, position],
        ).fetchall()
    ]

    stability_path = optional_bucket_glob(accession, "sequence", "stability_site")
    stability_row = None if stability_path is None else connection.execute(
        """
        SELECT distinct_substitution_count, genomic_variant_count, ddg_min, ddg_q25,
               ddg_median, ddg_q75, ddg_max, stabilizing_count, small_change_count,
               destabilizing_count
        FROM read_parquet(?)
        WHERE uniprot_accession = ? AND canonical_position = ?
        """, [stability_path, accession, position],
    ).fetchone()
    substitutions: list[SiteStabilitySubstitution] = []
    model_name = None
    prediction_path = optional_bucket_glob(accession, "variant", "source", "thermompnn")
    if stability_row is not None and prediction_path is not None:
        effect_path = bucket_glob(accession, "variant", "effect")
        substitution_rows = connection.execute(
            """
            WITH drawable AS (
              SELECT DISTINCT variant_key, uniprot_accession,
                     CAST(protein_start AS BIGINT) AS canonical_position, ref_aa, alt_aa
              FROM read_parquet(?)
              WHERE uniprot_accession = ? AND effect_scope = 'canonical' AND is_drawable
                AND protein_start = ?
            )
            SELECT p.ref_aa, p.alt_aa, avg(p.ddg_pred), count(DISTINCT p.variant_key),
                   any_value(p.pdb_name), any_value(p.model_name)
            FROM read_parquet(?) p JOIN drawable d
              ON d.variant_key = p.variant_key AND d.uniprot_accession = p.page_accession
             AND d.canonical_position = p.canonical_position AND d.ref_aa = p.ref_aa
             AND d.alt_aa = p.alt_aa
            WHERE p.page_accession = ? AND p.canonical_position = ?
            GROUP BY p.ref_aa, p.alt_aa
            ORDER BY avg(p.ddg_pred), p.alt_aa
            LIMIT 19
            """, [effect_path, accession, position, prediction_path, accession, position],
        ).fetchall()
        substitutions = [
            SiteStabilitySubstitution(
                substitution=f"{row[0]}{position}{row[1]}", ref_aa=str(row[0]), alt_aa=str(row[1]),
                ddg=float(row[2]), direction=stability_direction(float(row[2])),
                genomic_variant_count=int(row[3]), pdb_name=str(row[4]),
            )
            for row in substitution_rows
        ]
        model_name = str(substitution_rows[0][5]) if substitution_rows else None
    stability = SiteStability(
        available=stability_row is not None, model_name=model_name,
        distinct_substitution_count=0 if stability_row is None else int(stability_row[0]),
        genomic_variant_count=0 if stability_row is None else int(stability_row[1]),
        ddg_min=None if stability_row is None else stability_row[2],
        ddg_q25=None if stability_row is None else stability_row[3],
        ddg_median=None if stability_row is None else stability_row[4],
        ddg_q75=None if stability_row is None else stability_row[5],
        ddg_max=None if stability_row is None else stability_row[6],
        stabilizing_count=0 if stability_row is None else int(stability_row[7]),
        small_change_count=0 if stability_row is None else int(stability_row[8]),
        destabilizing_count=0 if stability_row is None else int(stability_row[9]),
        substitutions=substitutions,
    )

    covalent_path = bucket_glob(accession, "sequence", "covalent_pair")
    covalent_pairs = [
        SiteCovalentPair(
            pair_id=covalent_pair_id(
                accession, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7],
            ),
            feature_type=row[0], start_endpoint=int(row[1]), end_endpoint=int(row[2]),
            start_modifier=row[3], end_modifier=row[4], description=row[5],
            evidence=covalent_evidence(row[7]),
        )
        for row in connection.execute(
            """
            SELECT feature_type, CAST(start_position AS BIGINT), CAST(end_position AS BIGINT),
                   start_modifier, end_modifier, description, feature_id, evidence_json
            FROM read_parquet(?)
            WHERE uniprot_accession = ? AND coordinate_basis = 'canonical'
              AND start_position IS NOT NULL AND end_position IS NOT NULL
              AND start_position BETWEEN 1 AND ? AND end_position BETWEEN 1 AND ?
              AND (start_position = ? OR end_position = ?)
            ORDER BY start_position, end_position, feature_type, feature_id NULLS LAST
            """, [covalent_path, accession, length, length, position, position],
        ).fetchall()
    ]

    effect_path = bucket_glob(accession, "variant", "effect")
    core_path = bucket_glob(accession, "variant", "core")
    clinvar_path = bucket_glob(accession, "variant", "source", "clinvar")
    variant_rows = connection.execute(
        """
        WITH ranked_effects AS (
          SELECT variant_key, HGVSp, Consequence, protein_start,
                 row_number() OVER (
                   PARTITION BY variant_key
                   ORDER BY protein_start, protein_end, is_representative_effect DESC NULLS LAST,
                            HGVSp NULLS LAST, Consequence NULLS LAST
                 ) AS anchor_rank
          FROM read_parquet(?)
          WHERE uniprot_accession = ? AND effect_scope = 'canonical'
            AND is_drawable AND protein_start IS NOT NULL
        ), anchors AS (
          SELECT variant_key, HGVSp, Consequence FROM ranked_effects
          WHERE anchor_rank = 1 AND protein_start = ?
        ), clinvar_flags AS (
          SELECT variant_key, bool_or(regexp_full_match(
                   lower(trim(coalesce(ClinicalSignificance, ''))), ?
                 )) AS has_clinvar_plp_evidence
          FROM read_parquet(?) WHERE page_accession = ? GROUP BY variant_key
        ), core AS (
          SELECT variant_key, database_source FROM read_parquet(?) WHERE page_accession = ?
          QUALIFY row_number() OVER (PARTITION BY variant_key ORDER BY variant_key) = 1
        ), matched AS (
          SELECT a.variant_key, a.HGVSp, a.Consequence, c.database_source,
                 coalesce(f.has_clinvar_plp_evidence, false) AS has_clinvar_plp_evidence
          FROM anchors a LEFT JOIN clinvar_flags f USING (variant_key)
          LEFT JOIN core c USING (variant_key)
        )
        SELECT *, count(*) OVER () AS exact_total,
               count(*) FILTER (WHERE has_clinvar_plp_evidence) OVER () AS clinvar_plp_total
        FROM matched ORDER BY has_clinvar_plp_evidence DESC, variant_key LIMIT ?
        """, [
            effect_path, accession, position, CLINVAR_PLP_PATTERN, clinvar_path, accession,
            core_path, accession, SITE_EVIDENCE_VARIANT_PREVIEW_LIMIT,
        ],
    ).fetchall()
    variant_total = int(variant_rows[0][5]) if variant_rows else 0
    clinvar_plp_total = int(variant_rows[0][6]) if variant_rows else 0
    source_rows = connection.execute(
        """
        WITH ranked_effects AS (
          SELECT variant_key, protein_start,
                 row_number() OVER (
                   PARTITION BY variant_key
                   ORDER BY protein_start, protein_end, is_representative_effect DESC NULLS LAST,
                            HGVSp NULLS LAST, Consequence NULLS LAST
                 ) AS anchor_rank
          FROM read_parquet(?)
          WHERE uniprot_accession = ? AND effect_scope = 'canonical'
            AND is_drawable AND protein_start IS NOT NULL
        ), anchors AS (
          SELECT variant_key FROM ranked_effects WHERE anchor_rank = 1 AND protein_start = ?
        ), core AS (
          SELECT variant_key, database_source FROM read_parquet(?) WHERE page_accession = ?
          QUALIFY row_number() OVER (PARTITION BY variant_key ORDER BY variant_key) = 1
        )
        SELECT trim(source_name), count(*)
        FROM anchors JOIN core USING (variant_key),
             UNNEST(string_split(coalesce(database_source, ''), ';')) AS source(source_name)
        WHERE trim(source_name) <> ''
        GROUP BY trim(source_name)
        ORDER BY lower(trim(source_name)), trim(source_name)
        """, [effect_path, accession, position, core_path, accession],
    ).fetchall()
    source_counts = {str(row[0]): int(row[1]) for row in source_rows}
    variant_preview = [
        SiteVariantPreview(
            variant_key=row[0], hgvsp=row[1], consequence=row[2], source_badges=source_list(row[3]),
            has_clinvar_plp_evidence=bool(row[4]),
        ) for row in variant_rows
    ]

    return SiteEvidenceSummaryResponse(
        identity=SiteIdentity(
            uniprot_accession=accession, sequence_id=str(sequence["sequence_id"]),
            sequence_version=sequence["sequence_version"], position=position,
            reference_residue=sequence_text[position - 1],
        ),
        conservation=conservation,
        overlaps=SiteOverlaps(topology=topology, functional=functional, pfam=pfam, ptm=ptm),
        stability=stability,
        covalent_pairs=covalent_pairs,
        variants=SiteVariants(
            total=variant_total, clinvar_plp_count=clinvar_plp_total,
            source_counts=dict(sorted(source_counts.items())), preview=variant_preview,
            preview_limit=SITE_EVIDENCE_VARIANT_PREVIEW_LIMIT, showing=len(variant_preview),
            has_more=variant_total > len(variant_preview),
        ),
        provenance={
            "coordinate_basis": "canonical UniProt sequence, 1-based position",
            "conservation": "memVar conservation alignment tile",
            "stability": "ThermoMPNN predicted stability change (kcal/mol); negative stabilizing, positive destabilizing",
            "variants": "Canonical drawable variants are anchored once at their minimum canonical protein start",
        },
        response_bounds={
            "variant_preview_limit": SITE_EVIDENCE_VARIANT_PREVIEW_LIMIT,
            "stability_substitution_limit": 19,
            "raw_evidence_json_returned": False,
            "accession_bucket_only": True,
        },
    )


def encode_variant_cursor(filters: dict[str, object], sort_key: list[object]) -> str:
    payload = json.dumps({"v": 1, "filters": filters, "after": sort_key}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_variant_cursor(cursor: str, filters: dict[str, object]) -> list[object]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        after = payload["after"]
        if payload.get("v") != 1 or payload.get("filters") != filters or not isinstance(after, list) or len(after) != 5:
            raise ValueError
        if not isinstance(after[0], int) or not isinstance(after[1], int) or not isinstance(after[3], int):
            raise ValueError
        if not isinstance(after[2], str) or not isinstance(after[4], str):
            raise ValueError
        return after
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, binascii.Error, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail="Invalid variant cursor") from error


def effect_dict(row: dict[str, object]) -> dict[str, object]:
    return {
        "uniprot_accession": row["uniprot_accession"],
        "uniprot_isoform_id": row["uniprot_isoform_id"],
        "canonical_flag": row["canonical_flag"],
        "effect_scope": row["effect_scope"],
        "consequence": row["Consequence"],
        "hgvsp": row["HGVSp"],
        "codons": row["Codons"],
        "transcript_ids": row["transcript_ids"],
        "protein_start": row["protein_start"],
        "protein_end": row["protein_end"],
        "ref_aa": row["ref_aa"],
        "alt_aa": row["alt_aa"],
        "site_parse_status": row["site_parse_status"],
        "is_drawable": row["is_drawable"],
        "is_representative_effect": row["is_representative_effect"],
    }


def core_dict(row: dict[str, object]) -> dict[str, object]:
    database_source = row["database_source"]
    return {
        "variant_key": row["variant_key"], "genome_build": "GRCh38",
        "chrom": row["chrom"], "pos": row["pos"], "ref": row["ref"], "alt": row["alt"],
        "variant_class": row["VARIANT_CLASS"], "existing_variation": row["Existing_variation"],
        "representative_consequence": row["Consequence"], "representative_hgvsp": row["HGVSp"],
        "impact": row["IMPACT"], "am_pathogenicity": row["am_pathogenicity"],
        "am_class": row["am_class"], "joint_ac": row["joint_ac"], "joint_an": row["joint_an"],
        "joint_af": row["joint_AF"], "exome_af": row["exome_AF"], "genome_af": row["genome_AF"],
        "database_source": database_source,
        "source_badges": [part.strip() for part in (database_source or "").split(";") if part.strip()],
        "database_id": row["database_id"], "n_sources": row["n_sources"],
        "gene_symbol": row["gene_symbol"], "hgnc_id": row["hgnc_id"],
    }


@router.get(
    "/proteins/{acc}/variants/options",
    response_model=VariantFilterOptionsResponse,
)
def variant_filter_options(
    acc: str,
    scope: Literal["canonical", "isoform", "all"] = Query(default="canonical"),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantFilterOptionsResponse:
    """Return complete controlled-filter values from one protein bucket.

    VEP can store several comma-separated consequences on one effect.  Options
    and counts therefore operate on individual consequence terms while the raw
    combined value remains unchanged in variant responses.
    """
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    core_path = bucket_glob(accession, "variant", "core")
    effect_path = bucket_glob(accession, "variant", "effect")
    scope_condition = "TRUE" if scope == "all" else "e.effect_scope = ?"
    scope_parameters: list[object] = [] if scope == "all" else [scope]

    consequence_rows = connection.execute(
        f"""
        SELECT trim(consequence_term) AS value, count(DISTINCT e.variant_key) AS variant_count
        FROM read_parquet(?) e,
             UNNEST(string_split(coalesce(e.Consequence, ''), ',')) AS terms(consequence_term)
        WHERE e.uniprot_accession = ? AND {scope_condition}
          AND trim(consequence_term) <> ''
        GROUP BY value
        ORDER BY variant_count DESC, lower(value), value
        """,
        [effect_path, accession, *scope_parameters],
    ).fetchall()
    source_rows = connection.execute(
        f"""
        WITH scoped_variants AS (
          SELECT DISTINCT e.variant_key
          FROM read_parquet(?) e
          WHERE e.uniprot_accession = ? AND {scope_condition}
        )
        SELECT trim(source_term) AS value, count(DISTINCT c.variant_key) AS variant_count
        FROM read_parquet(?) c
        JOIN scoped_variants s USING (variant_key),
             UNNEST(string_split(coalesce(c.database_source, ''), ';')) AS sources(source_term)
        WHERE c.page_accession = ? AND trim(source_term) <> ''
        GROUP BY value
        ORDER BY variant_count DESC, lower(value), value
        """,
        [effect_path, accession, *scope_parameters, core_path, accession],
    ).fetchall()
    return VariantFilterOptionsResponse(
        uniprot_accession=accession,
        scope=scope,
        consequences=[
            VariantFilterOption(value=row[0], variant_count=row[1])
            for row in consequence_rows
        ],
        sources=[
            VariantFilterOption(value=row[0], variant_count=row[1])
            for row in source_rows
        ],
        response_bounds={
            "strategy": "complete_accession_bucket_distinct_values",
            "fact_rows_returned": 0,
            "counts": "exact_distinct_variants",
            "consequence_semantics": "comma_separated_term_membership",
            "source_semantics": "semicolon_separated_badge_membership",
        },
    )


@router.get(
    "/proteins/{acc}/variants/site-preview",
    response_model=VariantSitePreviewResponse,
)
def variant_site_preview(
    acc: str,
    position: int = Query(..., ge=1),
    limit: int = Query(default=DEFAULT_SITE_PREVIEW_LIMIT, ge=1, le=MAX_SITE_PREVIEW_LIMIT),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantSitePreviewResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    length = int(overview["canonical_length"])
    if position > length:
        raise HTTPException(
            status_code=400,
            detail=f"Position must be within the canonical sequence 1-{length}",
        )
    effect_path = bucket_glob(accession, "variant", "effect")
    core_path = bucket_glob(accession, "variant", "core")
    clinvar_path = bucket_glob(accession, "variant", "source", "clinvar")
    rows = connection.execute(
        """
        WITH ranked_effects AS (
          SELECT variant_key, HGVSp, Consequence, protein_start,
                 row_number() OVER (
                   PARTITION BY variant_key
                   ORDER BY protein_start, protein_end,
                            is_representative_effect DESC NULLS LAST,
                            HGVSp NULLS LAST, Consequence NULLS LAST
                 ) AS anchor_rank
          FROM read_parquet(?)
          WHERE uniprot_accession = ? AND effect_scope = 'canonical'
            AND is_drawable AND protein_start IS NOT NULL
        ), anchors AS (
          SELECT variant_key, HGVSp, Consequence
          FROM ranked_effects
          WHERE anchor_rank = 1 AND protein_start = ?
        ), clinvar_flags AS (
          SELECT variant_key,
                 bool_or(regexp_full_match(
                   lower(trim(coalesce(ClinicalSignificance, ''))), ?
                 )) AS has_clinvar_plp_evidence
          FROM read_parquet(?)
          WHERE page_accession = ?
          GROUP BY variant_key
        ), core AS (
          SELECT variant_key, database_source
          FROM read_parquet(?)
          WHERE page_accession = ?
          QUALIFY row_number() OVER (PARTITION BY variant_key ORDER BY variant_key) = 1
        ), matched AS (
          SELECT a.variant_key, a.HGVSp, a.Consequence, c.database_source,
                 coalesce(f.has_clinvar_plp_evidence, false) AS has_clinvar_plp_evidence
          FROM anchors a
          LEFT JOIN clinvar_flags f USING (variant_key)
          LEFT JOIN core c USING (variant_key)
        )
        SELECT *, count(*) OVER () AS exact_total,
               count(*) FILTER (WHERE has_clinvar_plp_evidence) OVER () AS clinvar_plp_total
        FROM matched
        ORDER BY has_clinvar_plp_evidence DESC, variant_key
        LIMIT ?
        """,
        [
            effect_path, accession, position, CLINVAR_PLP_PATTERN,
            clinvar_path, accession, core_path, accession, limit,
        ],
    ).fetchall()
    total = int(rows[0][5]) if rows else 0
    clinvar_plp_count = int(rows[0][6]) if rows else 0
    items = [
        VariantSitePreviewItem(
            variant_key=row[0],
            hgvsp=row[1],
            consequence=row[2],
            source_badges=[
                badge.strip()
                for badge in (row[3] or "").split(";")
                if badge.strip()
            ],
            has_clinvar_plp_evidence=bool(row[4]),
        )
        for row in rows
    ]
    prediction_map = predictions_for_variants(
        connection, accession, [item.variant_key for item in items],
    )
    for item in items:
        item.stability_prediction = prediction_map.get(item.variant_key)
    return VariantSitePreviewResponse(
        uniprot_accession=accession,
        position=position,
        total=total,
        clinvar_plp_count=clinvar_plp_count,
        showing=len(items),
        limit=limit,
        has_more=total > len(items),
        items=items,
        variant_table_query={
            "scope": "canonical", "start": position, "end": position,
        },
    )


@router.get(
    "/proteins/{acc}/variants/summary",
    response_model=VariantCatalogSummaryResponse,
)
def variant_catalog_summary(
    acc: str,
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantCatalogSummaryResponse:
    """Return exact, protein-scoped variant catalog counts from one accession bucket."""
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    core_path = bucket_glob(accession, "variant", "core")
    effect_path = bucket_glob(accession, "variant", "effect")
    clinvar_path = bucket_glob(accession, "variant", "source", "clinvar")
    rows = connection.execute(
        """
        WITH core_variants AS (
          SELECT DISTINCT variant_key
          FROM read_parquet(?)
          WHERE page_accession = ?
        ), effects AS (
          SELECT DISTINCT e.variant_key, e.effect_scope, e.uniprot_isoform_id, e.Consequence
          FROM read_parquet(?) e
          JOIN core_variants USING (variant_key)
          WHERE e.uniprot_accession = ?
        ), clinvar_assertions AS (
          SELECT cv.variant_key,
                 CASE
                   WHEN c.variant_key IS NULL
                     OR lower(trim(coalesce(c.ClinicalSignificance, ''))) IN ('', 'not provided')
                     THEN 'unclassified'
                   WHEN lower(trim(c.ClinicalSignificance)) LIKE '%conflicting classification%'
                     THEN 'conflicting'
                   WHEN lower(trim(c.ClinicalSignificance)) LIKE '%uncertain significance%'
                     THEN 'uncertain'
                   WHEN lower(trim(c.ClinicalSignificance)) LIKE '%benign%'
                     THEN 'benign'
                   WHEN lower(trim(c.ClinicalSignificance)) LIKE '%pathogenic%'
                     THEN 'pathogenic'
                   ELSE 'other'
                 END AS category
          FROM core_variants cv
          LEFT JOIN read_parquet(?) c
            ON c.page_accession = ? AND c.variant_key = cv.variant_key
        )
        SELECT 'total' AS facet, 'total' AS category, CAST(NULL AS VARCHAR) AS isoform_id,
               count(*) AS variant_count
        FROM core_variants
        UNION ALL
        SELECT 'protein_forms' AS facet, effect_scope AS category, uniprot_isoform_id,
               count(DISTINCT variant_key) AS variant_count
        FROM effects
        GROUP BY effect_scope, uniprot_isoform_id
        UNION ALL
        SELECT 'consequences' AS facet, trim(term) AS category, CAST(NULL AS VARCHAR) AS isoform_id,
               count(DISTINCT variant_key) AS variant_count
        FROM effects,
             UNNEST(string_split(coalesce(Consequence, ''), ',')) AS terms(term)
        WHERE trim(term) <> ''
        GROUP BY trim(term)
        UNION ALL
        SELECT 'clinvar_pathogenicity' AS facet, category, CAST(NULL AS VARCHAR) AS isoform_id,
               count(DISTINCT variant_key) AS variant_count
        FROM clinvar_assertions
        GROUP BY category
        """,
        [core_path, accession, effect_path, accession, clinvar_path, accession],
    ).fetchall()
    total = 0
    forms: list[VariantSummaryCount] = []
    consequences: list[VariantSummaryCount] = []
    clinvar_counts = {category: 0 for category in CLINVAR_PATHOGENICITY_CATEGORIES}
    for facet, category, isoform_id, variant_count in rows:
        count = int(variant_count)
        if facet == "total":
            total = count
        elif facet == "protein_forms":
            forms.append(VariantSummaryCount(
                category=str(category), isoform_id=isoform_id, variant_count=count,
            ))
        elif facet == "consequences":
            consequences.append(VariantSummaryCount(category=str(category), variant_count=count))
        else:
            clinvar_counts[str(category)] = count
    if not any(item.category == "canonical" for item in forms):
        forms.append(VariantSummaryCount(category="canonical", variant_count=0))
    forms.sort(key=lambda item: (item.category != "canonical", item.isoform_id or ""))
    consequences.sort(key=lambda item: (-item.variant_count, item.category.lower(), item.category))
    return VariantCatalogSummaryResponse(
        uniprot_accession=accession,
        total=VariantSummaryTotal(value=total),
        protein_forms=VariantSummaryFacet(items=forms),
        consequences=VariantSummaryFacet(items=consequences),
        clinvar_pathogenicity=VariantSummaryFacet(items=[
            VariantSummaryCount(category=category, variant_count=clinvar_counts[category])
            for category in CLINVAR_PATHOGENICITY_CATEGORIES
        ]),
        response_bounds={
            "strategy": "one_accession_bucket_single_grouped_query",
            "runtime_external_requests": 0,
        },
    )


@router.get("/proteins/{acc}/variants", response_model=VariantListResponse)
def protein_variants(
    acc: str,
    scope: Literal["canonical", "isoform", "all"] = Query(default="canonical"),
    consequence: str | None = Query(default=None),
    source: str | None = Query(default=None),
    start: int | None = Query(default=None),
    end: int | None = Query(default=None),
    limit: int = Query(default=DEFAULT_VARIANT_PAGE_SIZE, ge=1, le=MAX_VARIANT_PAGE_SIZE),
    cursor: str | None = Query(default=None),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantListResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    if (start is None) != (end is None):
        raise HTTPException(status_code=400, detail="Variant site range requires both start and end")
    if start is not None:
        length = int(overview["canonical_length"])
        if start < 1 or end is None or end < start or end > length:
            raise HTTPException(
                status_code=400,
                detail=f"Range must be a 1-based closed interval within 1-{length}",
            )
    normalized_consequence = consequence.strip() if consequence and consequence.strip() else None
    normalized_source = source.strip() if source and source.strip() else None
    filters: dict[str, object] = {
        "accession": accession, "scope": scope, "consequence": normalized_consequence,
        "source": normalized_source, "start": start, "end": end,
    }
    after = decode_variant_cursor(cursor, filters) if cursor else None
    core_path = bucket_glob(accession, "variant", "core")
    effect_path = bucket_glob(accession, "variant", "effect")
    effect_conditions = ["e.uniprot_accession = ?"]
    effect_parameters: list[object] = [accession]
    if scope != "all":
        effect_conditions.append("e.effect_scope = ?")
        effect_parameters.append(scope)
    if normalized_consequence:
        effect_conditions.append(
            "list_contains("
            "list_transform(string_split(coalesce(e.Consequence, ''), ','), "
            "term -> lower(trim(term))), lower(?)"
            ")"
        )
        effect_parameters.append(normalized_consequence)
    if start is not None and end is not None:
        effect_conditions.extend(["e.protein_start IS NOT NULL", "e.protein_end IS NOT NULL", "e.protein_start <= ?", "e.protein_end >= ?"])
        effect_parameters.extend([end, start])
    effect_where = " AND ".join(effect_conditions)
    source_condition = "TRUE"
    source_parameters: list[object] = []
    if normalized_source:
        source_condition = """
            list_contains(
              list_transform(string_split(coalesce(c.database_source, ''), ';'), badge -> lower(trim(badge))),
              lower(?)
            )
        """
        source_parameters.append(normalized_source)
    after_sql = ""
    after_parameters: list[object] = []
    if after:
        after_sql = "WHERE (scope_rank, sort_start, sort_chrom, sort_pos, variant_key) > (?, ?, ?, ?, ?)"
        after_parameters = after
    query = f"""
        WITH effects AS (
          SELECT *, row_number() OVER (
            PARTITION BY variant_key ORDER BY
              CASE effect_scope WHEN 'canonical' THEN 0 WHEN 'isoform' THEN 1 ELSE 2 END,
              protein_start NULLS LAST, HGVSp NULLS LAST, uniprot_isoform_id NULLS LAST
          ) AS rn
          FROM read_parquet(?) e WHERE {effect_where}
        ), matched AS (
          SELECT DISTINCT c.variant_key
          FROM read_parquet(?) c
          JOIN effects e USING (variant_key)
          WHERE c.page_accession = ? AND {source_condition}
        ), ordered AS (
          SELECT c.*, e.uniprot_isoform_id AS primary_isoform_id,
            e.canonical_flag AS primary_canonical_flag, e.effect_scope AS primary_effect_scope,
            e.Consequence AS primary_consequence, e.HGVSp AS primary_hgvsp,
            e.protein_start AS primary_protein_start, e.protein_end AS primary_protein_end,
            e.site_parse_status AS primary_site_parse_status, e.is_drawable AS primary_is_drawable,
            CASE e.effect_scope WHEN 'canonical' THEN 0 WHEN 'isoform' THEN 1 ELSE 2 END AS scope_rank,
            coalesce(e.protein_start, 9223372036854775807) AS sort_start,
            coalesce(c.chrom, '') AS sort_chrom, coalesce(c.pos, 9223372036854775807) AS sort_pos
          FROM read_parquet(?) c JOIN matched m USING (variant_key)
          LEFT JOIN effects e ON c.variant_key = e.variant_key AND e.rn = 1
          WHERE c.page_accession = ?
        )
        SELECT * FROM ordered {after_sql}
        ORDER BY scope_rank, sort_start, sort_chrom, sort_pos, variant_key LIMIT ?
    """
    parameters: list[object] = [effect_path, *effect_parameters, core_path, accession]
    parameters.extend(source_parameters)
    parameters.extend([core_path, accession])
    parameters.extend(after_parameters)
    parameters.append(limit + 1)
    rows = rows_as_dicts(connection.execute(query, parameters))

    count_query = f"""
        WITH filtered_effects AS (
          SELECT variant_key FROM read_parquet(?) e WHERE {effect_where}
        )
        SELECT count(DISTINCT c.variant_key)
        FROM read_parquet(?) c JOIN filtered_effects e USING (variant_key)
        WHERE c.page_accession = ? AND {source_condition}
    """
    total = connection.execute(
        count_query, [effect_path, *effect_parameters, core_path, accession, *source_parameters]
    ).fetchone()[0]
    has_more = len(rows) > limit
    page = rows[:limit]
    items: list[dict[str, object]] = []
    prediction_map = predictions_for_variants(
        connection, accession, [str(row["variant_key"]) for row in page],
    )
    for row in page:
        item = core_dict(row)
        item["primary_effect"] = {
            "uniprot_isoform_id": row["primary_isoform_id"],
            "canonical_flag": row["primary_canonical_flag"],
            "effect_scope": row["primary_effect_scope"],
            "consequence": row["primary_consequence"],
            "hgvsp": row["primary_hgvsp"],
            "protein_start": row["primary_protein_start"],
            "protein_end": row["primary_protein_end"],
            "site_parse_status": row["primary_site_parse_status"],
            "is_drawable": row["primary_is_drawable"],
        }
        prediction = prediction_map.get(str(row["variant_key"]))
        item["stability_prediction"] = prediction.model_dump() if prediction else None
        items.append(item)
    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_variant_cursor(
            filters,
            [last["scope_rank"], last["sort_start"], last["sort_chrom"], last["sort_pos"], last["variant_key"]],
        )
    return VariantListResponse(
        uniprot_accession=accession, items=items, next_cursor=next_cursor,
        total_or_estimate=ExactTotal(value=total),
        applied_filters={**filters, "limit": limit},
    )


@router.get(
    "/variants/{variant_key:path}/population-frequency",
    response_model=VariantPopulationFrequencyResponse,
)
def variant_population_frequency(
    variant_key: str,
    protein_accession: str = Query(...),
    callset: Literal["exome", "genome", "joint"] = Query(default="joint"),
    limit: int = Query(default=12, ge=1, le=MAX_POPULATION_FREQUENCY_GROUPS),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantPopulationFrequencyResponse:
    """Return one AF-only gnomAD v4.1 callset for a protein member variant."""
    overview = require_protein(connection, protein_accession)
    accession = str(overview["uniprot_accession"])
    core_path = bucket_glob(accession, "variant", "core")
    belongs = connection.execute(
        "SELECT 1 FROM read_parquet(?) WHERE page_accession = ? AND variant_key = ? LIMIT 1",
        [core_path, accession, variant_key],
    ).fetchone()
    if belongs is None:
        raise HTTPException(status_code=404, detail=f"Variant is not a member of protein {accession}: {variant_key}")

    populations = POPULATIONS_BY_CALLSET[callset]
    bounds = {
        "strategy": "exact_variant_key_local_bucket",
        "variant_bucket": f"{variant_key_bucket(variant_key):03d}",
        "max_groups": limit,
        "runtime_external_requests": 0,
    }
    asset = population_frequency_asset(variant_key)
    row = None if asset is None else row_dict(
        connection,
        "SELECT * FROM read_parquet(?) WHERE variant_key = ? LIMIT 1",
        [str(asset), variant_key],
    )
    if row is None:
        return VariantPopulationFrequencyResponse(
            uniprot_accession=accession, variant_key=variant_key,
            callset=callset,
            available_callsets=["exome", "genome", "joint"],
            availability="not_found_in_gnomad",
            message="This GRCh38 variant has no gnomAD v4.1 ancestry frequency row; absence is not AF 0.",
            groups=[],
            unavailable_fields=GNOMAD_UNAVAILABLE_FIELDS,
            total_or_estimate=ExactTotal(value=0),
            response_bounds=bounds,
        )

    groups = [
        PopulationFrequencyGroup(
            ancestry_group=population,
            label=POPULATION_LABELS[population],
            allele_frequency=row.get(f"{callset}_{population}_af"),
        )
        for population in populations[:limit]
    ]
    available_count = sum(group.allele_frequency is not None for group in groups)
    return VariantPopulationFrequencyResponse(
        uniprot_accession=accession,
        variant_key=variant_key,
        availability="matched",
        callset=callset,
        available_callsets=["exome", "genome", "joint"],
        message=f"gnomAD v4.1 {callset} AF by genetic ancestry group; callsets remain independent.",
        groups=groups,
        unavailable_fields=GNOMAD_UNAVAILABLE_FIELDS,
        total_or_estimate=ExactTotal(value=len(populations)),
        response_bounds={
            **bounds,
            "returned_groups": len(groups),
            "available_groups": available_count,
            "fixed_af_scale": {"kind": "log10", "minimum_positive": 1e-6, "maximum": 1.0},
        },
    )


def require_variant_membership(
    connection: duckdb.DuckDBPyConnection, protein_accession: str, variant_key: str,
) -> tuple[str, dict[str, object]]:
    overview = require_protein(connection, protein_accession)
    accession = str(overview["uniprot_accession"])
    core_path = bucket_glob(accession, "variant", "core")
    core = row_dict(
        connection,
        "SELECT * FROM read_parquet(?) WHERE page_accession = ? AND variant_key = ? LIMIT 1",
        [core_path, accession, variant_key],
    )
    if core is None:
        raise HTTPException(status_code=404, detail=f"Variant is not a member of protein {accession}: {variant_key}")
    return accession, core


@router.get(
    "/variants/{variant_key:path}/evidence/facts",
    response_model=VariantFactsEvidenceResponse,
)
def variant_facts_evidence(
    variant_key: str,
    protein_accession: str = Query(...),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantFactsEvidenceResponse:
    accession, core = require_variant_membership(connection, protein_accession, variant_key)
    return VariantFactsEvidenceResponse(
        uniprot_accession=accession, variant_key=variant_key, core=core_dict(core),
    )


@router.get(
    "/variants/{variant_key:path}/evidence/effects",
    response_model=VariantEffectsEvidenceResponse,
)
def variant_effects_evidence(
    variant_key: str,
    protein_accession: str = Query(...),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantEffectsEvidenceResponse:
    accession, _ = require_variant_membership(connection, protein_accession, variant_key)
    effect_path = bucket_glob(accession, "variant", "effect")
    effects = rows_as_dicts(connection.execute(
        """
        SELECT * FROM read_parquet(?) WHERE uniprot_accession = ? AND variant_key = ?
        ORDER BY CASE effect_scope WHEN 'canonical' THEN 0 WHEN 'isoform' THEN 1 ELSE 2 END,
                 protein_start NULLS LAST, HGVSp NULLS LAST, uniprot_isoform_id NULLS LAST
        """, [effect_path, accession, variant_key]))
    return VariantEffectsEvidenceResponse(
        uniprot_accession=accession,
        variant_key=variant_key,
        effects=[VariantEffect(**effect_dict(effect)) for effect in effects],
    )


@router.get(
    "/variants/{variant_key:path}/evidence/clinvar",
    response_model=VariantClinvarEvidenceResponse,
)
def variant_clinvar_evidence(
    variant_key: str,
    protein_accession: str = Query(...),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantClinvarEvidenceResponse:
    accession, _ = require_variant_membership(connection, protein_accession, variant_key)
    path = bucket_glob(accession, "variant", "source", "clinvar")
    rows = rows_as_dicts(connection.execute(
        """
        SELECT * EXCLUDE (page_accession, accession_bucket)
        FROM read_parquet(?)
        WHERE page_accession = ? AND variant_key = ?
        ORDER BY RCVaccession NULLS LAST
        """,
        [path, accession, variant_key],
    ))
    return VariantClinvarEvidenceResponse(
        uniprot_accession=accession,
        variant_key=variant_key,
        assertions=[ClinvarAssertion(
            clinical_significance=row.get("ClinicalSignificance"),
            rcv_accession=row.get("RCVaccession"),
            phenotype_list=row.get("PhenotypeList"),
            phenotype_ids=row.get("PhenotypeIDs"),
            review_status=row.get("ReviewStatus"),
            origin=row.get("OriginSimple"),
            mondo_ids=source_list(row.get("mondo_ids")),
            disease_categories=source_list(row.get("disease_categories")),
            source_release=row.get("source_release"),
            evidence_grain=row.get("evidence_grain"),
        ) for row in rows],
    )


@router.get(
    "/variants/{variant_key:path}/evidence/cosmic",
    response_model=VariantCosmicEvidenceResponse,
)
def variant_cosmic_evidence(
    variant_key: str,
    protein_accession: str = Query(...),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantCosmicEvidenceResponse:
    accession, _ = require_variant_membership(connection, protein_accession, variant_key)
    path = bucket_glob(accession, "variant", "source", "cosmic")
    rows = rows_as_dicts(connection.execute(
        """
        SELECT GENOME_SCREEN_SAMPLE_COUNT, mondo_ids, disease_categories, CGC_TIER, ONC_TSG
        FROM read_parquet(?)
        WHERE page_accession = ? AND variant_key = ?
        ORDER BY GENOME_SCREEN_SAMPLE_COUNT NULLS LAST, mondo_ids NULLS LAST,
                 disease_categories NULLS LAST
        """,
        [path, accession, variant_key],
    ))
    return VariantCosmicEvidenceResponse(
        uniprot_accession=accession,
        variant_key=variant_key,
        records=[cosmic_evidence(row) for row in rows],
    )


@router.get(
    "/variants/{variant_key:path}/evidence/stability",
    response_model=VariantStabilityEvidenceResponse,
)
def variant_stability_evidence(
    variant_key: str,
    protein_accession: str = Query(...),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> VariantStabilityEvidenceResponse:
    accession, _ = require_variant_membership(connection, protein_accession, variant_key)
    prediction = predictions_for_variants(connection, accession, [variant_key]).get(variant_key)
    return VariantStabilityEvidenceResponse(
        uniprot_accession=accession, variant_key=variant_key, prediction=prediction,
    )
