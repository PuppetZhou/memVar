"""M3 expression and protein-scoped QTL endpoints.

QTL detail requests resolve one explicit source/type/accession bucket before
DuckDB is invoked.  No detail query may broaden that path to a source, type,
or full-QTL glob.
"""

from __future__ import annotations

import base64
import binascii
from contextlib import contextmanager
import json
from pathlib import Path
from typing import Iterator, Literal

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from .store import get_connection, require_protein
from .release_store import release_store
from .models import (
    ExactTotal,
    ExpressionGroup,
    ExpressionItem,
    ExpressionResponse,
    QtlDetailItem,
    QtlDetailResponse,
    QtlSourceSemantics,
    QtlSummaryItem,
    QtlSummaryResponse,
)


router = APIRouter(prefix="/api/v1")

DEFAULT_QTL_PAGE_SIZE = 50
MAX_QTL_PAGE_SIZE = 200

SOURCE_TYPES: dict[str, tuple[str, ...]] = {
    "GTEx": ("apaQTL", "eQTL", "sQTL"),
    "QTLbase": (
        "apaQTL", "bQTL", "caQTL", "cerQTL", "circQTL", "eQTL",
        "eaQTL", "edQTL", "hQTL", "lncRNAQTL", "m6AQTL", "mQTL",
        "metaQTL", "miQTL", "pQTL", "pieQTL", "puQTL", "riboQTL",
        "sQTL", "stQTL", "tuQTL", "vQTL",
    ),
    "eQTLGen": ("cis_eQTL",),
}

EXPRESSION_SPECS = {
    "hpa_rna": {
        "table": "expression_hpa_rna", "display_name": "HPA RNA",
        "value": "normalized_expression_ntpm", "tissue": "tissue",
        "order": "tissue, ensembl_gene_id", "cap": 200,
        "details": ("ensembl_gene_id", "gene_symbol"),
    },
    "hpa_ms": {
        "table": "expression_hpa_ms", "display_name": "HPA MS",
        "value": "protein_intensity", "tissue": "tissue",
        "order": "tissue, ensembl_gene_id", "cap": 100,
        "details": ("ensembl_gene_id", "gene_symbol"),
    },
    "hpa_ihc": {
        "table": "expression_hpa_ihc", "display_name": "HPA IHC",
        "value": "staining_level", "tissue": "tissue",
        "order": "tissue, ihc_tissue_name, cell_type, ensembl_gene_id", "cap": 500,
        "details": (
            "ensembl_gene_id", "gene_symbol", "ihc_tissue_name", "cell_type",
            "reliability",
        ),
    },
    "paxdb": {
        "table": "expression_paxdb", "display_name": "PaxDB protein abundance",
        "value": "abundance_ppm", "organ": "organ",
        "order": "organ, paxdb_dataset_id, string_external_id", "cap": 100,
        "details": (
            "paxdb_dataset_id", "paxdb_dataset_name", "string_external_id",
            "source_gene_name",
        ),
    },
}


def m3_root() -> Path:
    return release_store().qtl_facts


def m3_database_path() -> Path:
    return release_store().m3_database


@contextmanager
def read_m3_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    path = m3_database_path()
    if not path.is_file():
        raise RuntimeError(f"M3 database is missing: {path}")
    connection = duckdb.connect(str(path), read_only=True)
    try:
        yield connection
    finally:
        connection.close()


def get_m3_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    with read_m3_connection() as connection:
        yield connection


def rows_as_dicts(result: duckdb.DuckDBPyConnection) -> list[dict[str, object]]:
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def accession_bucket(accession: str) -> int:
    """Match the fixed 128-way polynomial hash used by the M3 builder."""
    return sum(
        (ord(accession[index - 1]) if index <= len(accession) else 0) * 31 ** (10 - index)
        for index in range(1, 11)
    ) % 128


def canonical_source(source: str) -> str:
    normalized = source.strip().casefold()
    for candidate in SOURCE_TYPES:
        if candidate.casefold() == normalized:
            return candidate
    raise HTTPException(
        status_code=400,
        detail=f"Unknown QTL source: {source}. Allowed sources: {', '.join(SOURCE_TYPES)}",
    )


def canonical_qtl_type(qtl_type: str, source: str | None = None) -> str:
    candidates = SOURCE_TYPES[source] if source else tuple(
        dict.fromkeys(kind for kinds in SOURCE_TYPES.values() for kind in kinds)
    )
    normalized = qtl_type.strip().casefold()
    for candidate in candidates:
        if candidate.casefold() == normalized:
            return candidate
    scope = f" for {source}" if source else ""
    raise HTTPException(status_code=400, detail=f"Unknown QTL type{scope}: {qtl_type}")


def qtl_bucket_glob(source: str, qtl_type: str, accession: str) -> str | None:
    """Return only the requested accession bucket, or None for a valid empty bucket."""
    bucket = accession_bucket(accession)
    directory = (
        m3_root() / f"source={source}" / f"type={qtl_type}"
        / f"accession_bucket={bucket}"
    )
    if not directory.is_dir() or not any(directory.glob("*.parquet")):
        return None
    return str(directory / "*.parquet")


def source_semantics(
    connection: duckdb.DuckDBPyConnection, sources: list[str]
) -> list[QtlSourceSemantics]:
    if not sources:
        return []
    placeholders = ",".join("?" for _ in sources)
    rows = connection.execute(
        f"""SELECT source_database, evidence_semantics, genome_build
            FROM qtl_source_semantics WHERE source_database IN ({placeholders})
            ORDER BY source_database""",
        sources,
    ).fetchall()
    found = {row[0] for row in rows}
    missing = sorted(set(sources) - found)
    if missing:
        raise HTTPException(status_code=500, detail=f"QTL source metadata missing: {', '.join(missing)}")
    return [
        QtlSourceSemantics(
            source_database=row[0], evidence_semantics=row[1], genome_build=row[2]
        )
        for row in rows
    ]


def expression_group(
    connection: duckdb.DuckDBPyConnection, accession: str, modality: str
) -> ExpressionGroup:
    spec = EXPRESSION_SPECS[modality]
    detail_columns = list(spec["details"])
    tissue_column = spec.get("tissue")
    organ_column = spec.get("organ")
    selected = [
        spec["value"],
        tissue_column or "NULL AS source_tissue",
        organ_column or "NULL AS source_organ",
        "unit", "source_database", "source_release",
        *detail_columns,
    ]
    cap = int(spec["cap"])
    result = connection.execute(
        f"""SELECT {', '.join(selected)} FROM {spec['table']}
            WHERE uniprot_accession = ? ORDER BY {spec['order']} LIMIT ?""",
        [accession, cap + 1],
    )
    rows = rows_as_dicts(result)
    if len(rows) > cap:
        raise HTTPException(
            status_code=500,
            detail=f"Expression modality {modality} exceeds its bounded response contract",
        )
    items = []
    for row in rows:
        items.append(ExpressionItem(
            source_tissue=row.get(tissue_column) if tissue_column else None,
            source_organ=row.get(organ_column) if organ_column else None,
            raw_value=row[spec["value"]],
            unit=row["unit"],
            source_database=row["source_database"],
            source_release=row["source_release"],
            details={column: row[column] for column in detail_columns},
        ))
    return ExpressionGroup(
        modality=modality,
        display_name=spec["display_name"],
        items=items,
        total_or_estimate=ExactTotal(value=len(items)),
    )


@router.get("/proteins/{acc}/expression", response_model=ExpressionResponse)
def expression(
    acc: str,
    modality: Literal["hpa_rna", "hpa_ms", "hpa_ihc", "paxdb", "all"] = Query(...),
    core_connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    connection: duckdb.DuckDBPyConnection = Depends(get_m3_connection),
) -> ExpressionResponse:
    overview = require_protein(core_connection, acc)
    accession = str(overview["uniprot_accession"])
    requested = list(EXPRESSION_SPECS) if modality == "all" else [modality]
    groups = {
        name: expression_group(connection, accession, name)
        for name in requested
    }
    return ExpressionResponse(
        uniprot_accession=accession,
        groups=groups,
        total_or_estimate=ExactTotal(
            value=sum(group.total_or_estimate.value for group in groups.values())
        ),
        applied_filters={"modality": modality},
        response_bounds={
            "strategy": "complete_bounded_modality",
            "maximum_records_per_modality": {
                name: int(spec["cap"]) for name, spec in EXPRESSION_SPECS.items()
            },
        },
    )


@router.get("/proteins/{acc}/qtl/summary", response_model=QtlSummaryResponse)
def qtl_summary(
    acc: str,
    source: str | None = Query(default=None),
    qtl_type: str | None = Query(default=None),
    core_connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    connection: duckdb.DuckDBPyConnection = Depends(get_m3_connection),
) -> QtlSummaryResponse:
    overview = require_protein(core_connection, acc)
    accession = str(overview["uniprot_accession"])
    normalized_source = canonical_source(source) if source is not None else None
    normalized_type = (
        canonical_qtl_type(qtl_type, normalized_source) if qtl_type is not None else None
    )
    conditions = ["uniprot_accession = ?"]
    parameters: list[object] = [accession]
    if normalized_source:
        conditions.append("source_database = ?")
        parameters.append(normalized_source)
    if normalized_type:
        conditions.append("qtl_type = ?")
        parameters.append(normalized_type)
    rows = connection.execute(
        f"""SELECT source_database, qtl_type, tissue_or_context, population,
                   record_count, distinct_variant_or_locus_count
            FROM qtl_summary WHERE {' AND '.join(conditions)}
            ORDER BY source_database, qtl_type, tissue_or_context NULLS LAST,
                     population NULLS LAST""",
        parameters,
    ).fetchall()
    metadata_sources = [normalized_source] if normalized_source else list(SOURCE_TYPES)
    return QtlSummaryResponse(
        uniprot_accession=accession,
        items=[QtlSummaryItem(
            source_database=row[0], qtl_type=row[1], tissue_or_context=row[2],
            population=row[3], record_count=row[4],
            distinct_variant_or_locus_count=row[5],
        ) for row in rows],
        source_semantics=source_semantics(connection, metadata_sources),
        total_or_estimate=ExactTotal(value=len(rows)),
        applied_filters={"source": normalized_source, "qtl_type": normalized_type},
    )


def encode_qtl_cursor(filters: dict[str, object], token: str, duplicate_ordinal: int) -> str:
    payload = json.dumps(
        {"v": 1, "filters": filters, "after": [token, duplicate_ordinal]},
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_qtl_cursor(cursor: str, filters: dict[str, object]) -> tuple[str, int]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        after = payload["after"]
        if (
            payload.get("v") != 1 or payload.get("filters") != filters
            or not isinstance(after, list) or len(after) != 2
            or not isinstance(after[0], str) or not isinstance(after[1], int)
            or after[1] < 1
        ):
            raise ValueError
        return after[0], after[1]
    except (
        KeyError, TypeError, ValueError, UnicodeDecodeError, binascii.Error,
        json.JSONDecodeError,
    ) as error:
        raise HTTPException(status_code=400, detail="Invalid QTL cursor") from error


def validate_source_filters(
    source: str, tissue: str | None, context: str | None, population: str | None
) -> None:
    incompatible = []
    if source == "GTEx":
        incompatible = [name for name, value in (("context", context), ("population", population)) if value]
    elif source == "eQTLGen":
        incompatible = [name for name, value in (("tissue", tissue), ("population", population)) if value]
    if incompatible:
        raise HTTPException(
            status_code=400,
            detail=f"Filter(s) not supported for {source}: {', '.join(incompatible)}",
        )


def detail_query_parts(
    source: str, tissue: str | None, context: str | None, population: str | None
) -> tuple[list[str], list[object], str]:
    conditions = ["x.uniprot_accession = ?"]
    parameters: list[object] = []
    if source in ("GTEx", "QTLbase") and tissue:
        conditions.append("x.tissue = ?")
        parameters.append(tissue)
    if source == "QTLbase" and context:
        conditions.append("nullif(x.assay_context, '') = ?")
        parameters.append(context)
    if source == "eQTLGen" and context:
        conditions.append("x.tissue_or_context = ?")
        parameters.append(context)
    if source == "QTLbase" and population:
        conditions.append("x.population = ?")
        parameters.append(population)
    sort_prefix = {
        "GTEx": "coalesce(tissue, '') || chr(31) || coalesce(variant_id, '') || chr(31) || coalesce(phenotype_id, '')",
        "QTLbase": "coalesce(tissue, '') || chr(31) || coalesce(population, '') || chr(31) || coalesce(variant_chromosome, '') || chr(31) || lpad(coalesce(variant_position_grch38, 0)::VARCHAR, 12, '0')",
        "eQTLGen": "coalesce(variant_chromosome, '') || chr(31) || lpad(coalesce(variant_position, 0)::VARCHAR, 12, '0') || chr(31) || coalesce(variant_rs_id, '')",
    }[source]
    return conditions, parameters, sort_prefix


def gtex_item(row: dict[str, object]) -> QtlDetailItem:
    return QtlDetailItem(
        source_database="GTEx", qtl_type=row["qtl_type"], tissue=row["tissue"],
        gene={
            "gene_symbol": row["gene_symbol"], "ensembl_gene_id": row["ensembl_gene_id"],
            "release_ensembl_gene_ids": row["release_ensembl_gene_ids"],
        },
        phenotype={"phenotype_id": row["phenotype_id"], "group_id": row["group_id"]},
        variant_or_locus={"kind": "exact_variant", "identifier": row["variant_id"]},
        genome_build=row["genome_build"], p_value=row["p_value_nominal"],
        evidence_semantics=row["evidence_semantics"], source_release=row["source_release"],
        source_specific={"gtex": {
            "distance_to_phenotype_start_bp": row["distance_to_phenotype_start_bp"],
            "alt_allele_frequency": row["alt_allele_frequency"],
            "minor_allele_sample_count": row["minor_allele_sample_count"],
            "minor_allele_count": row["minor_allele_count"],
            "effect_slope": row["effect_slope"],
            "effect_standard_error": row["effect_standard_error"],
            "p_value_nominal_threshold": row["p_value_nominal_threshold"],
        }},
    )


def qtlbase_item(row: dict[str, object]) -> QtlDetailItem:
    context = row["assay_context"] or None
    return QtlDetailItem(
        source_database="QTLbase", qtl_type=row["qtl_type"], tissue=row["tissue"],
        context=context, population=row["population"],
        gene={
            "gene_symbol": row["gene_symbol"], "ensembl_gene_ids": row["ensembl_gene_ids"],
            "gene_name_types": row["gene_name_types"],
        },
        phenotype={
            "trait_chromosome": row["trait_chromosome"],
            "trait_start_grch38": row["trait_start_grch38"],
            "trait_end_grch38": row["trait_end_grch38"],
        },
        variant_or_locus={
            "kind": "chromosome_position_locus",
            "chromosome": row["variant_chromosome"],
            "position": row["variant_position_grch38"],
            "has_ref_alt_or_rsid": False,
        },
        genome_build=row["genome_build"], p_value=row["p_value"],
        evidence_semantics=row["evidence_semantics"], source_release=row["source_release"],
        source_specific={"qtlbase": {
            "sample_size_raw": row["sample_size_raw"],
            "sample_size_numeric": row["sample_size_numeric"],
            "publication_id": row["publication_id"], "source_id": row["source_id"],
            "source_genome_build": row["source_genome_build"],
        }},
    )


def eqtlgen_item(row: dict[str, object]) -> QtlDetailItem:
    return QtlDetailItem(
        source_database="eQTLGen", qtl_type=row["qtl_type"],
        context=row["tissue_or_context"],
        gene={"gene_symbol": row["gene_symbol"], "ensembl_gene_id": row["ensembl_gene_id"]},
        variant_or_locus={
            "kind": "variant_with_rsid", "identifier": row["variant_rs_id"],
            "chromosome": row["variant_chromosome"], "position": row["variant_position"],
            "assessed_allele": row["assessed_allele"], "other_allele": row["other_allele"],
        },
        genome_build=row["genome_build"], p_value=row["p_value"],
        evidence_semantics=row["evidence_semantics"], source_release=row["source_release"],
        source_specific={"eqtlgen": {
            "z_score": row["z_score"], "fdr": row["fdr"],
            "bonferroni_p_value": row["bonferroni_p_value"],
            "sample_size": row["sample_size"], "cohort_count": row["cohort_count"],
        }},
    )


@router.get("/proteins/{acc}/qtl", response_model=QtlDetailResponse)
def qtl_detail(
    acc: str,
    source: str = Query(...),
    qtl_type: str = Query(...),
    tissue: str | None = Query(default=None),
    context: str | None = Query(default=None),
    population: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_QTL_PAGE_SIZE, ge=1, le=MAX_QTL_PAGE_SIZE),
    cursor: str | None = Query(default=None),
    core_connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    connection: duckdb.DuckDBPyConnection = Depends(get_m3_connection),
) -> QtlDetailResponse:
    overview = require_protein(core_connection, acc)
    accession = str(overview["uniprot_accession"])
    normalized_source = canonical_source(source)
    normalized_type = canonical_qtl_type(qtl_type, normalized_source)
    tissue = tissue.strip() if tissue and tissue.strip() else None
    context = context.strip() if context and context.strip() else None
    population = population.strip() if population and population.strip() else None
    validate_source_filters(normalized_source, tissue, context, population)
    filters: dict[str, object] = {
        "accession": accession, "source": normalized_source, "qtl_type": normalized_type,
        "tissue": tissue, "context": context, "population": population,
    }
    after = decode_qtl_cursor(cursor, filters) if cursor else None
    metadata = source_semantics(connection, [normalized_source])[0]
    path = qtl_bucket_glob(normalized_source, normalized_type, accession)
    if path is None:
        return QtlDetailResponse(
            uniprot_accession=accession, source_database=normalized_source,
            qtl_type=normalized_type, items=[], source_semantics=metadata,
            total_or_estimate=ExactTotal(value=0),
            applied_filters={**filters, "limit": limit},
        )

    conditions, filter_parameters, sort_prefix = detail_query_parts(
        normalized_source, tissue, context, population
    )
    where = " AND ".join(conditions)
    cursor_condition = ""
    cursor_parameters: list[object] = []
    if after:
        cursor_condition = "WHERE (sort_token, duplicate_ordinal) > (?, ?)"
        cursor_parameters = [after[0], after[1]]
    query = f"""
        WITH base AS (
          SELECT x.*, to_json(x) AS row_json
          FROM read_parquet(?) x WHERE {where}
        ), keyed AS (
          SELECT *, {sort_prefix} || chr(31) || row_json AS sort_token,
            row_number() OVER (PARTITION BY row_json ORDER BY row_json) AS duplicate_ordinal
          FROM base
        )
        SELECT * FROM keyed {cursor_condition}
        ORDER BY sort_token, duplicate_ordinal LIMIT ?
    """
    parameters: list[object] = [path, accession, *filter_parameters, *cursor_parameters, limit + 1]
    rows = rows_as_dicts(connection.execute(query, parameters))
    total = connection.execute(
        f"SELECT count(*) FROM read_parquet(?) x WHERE {where}",
        [path, accession, *filter_parameters],
    ).fetchone()[0]
    has_more = len(rows) > limit
    page = rows[:limit]
    adapter = {"GTEx": gtex_item, "QTLbase": qtlbase_item, "eQTLGen": eqtlgen_item}[normalized_source]
    items = [adapter(row) for row in page]
    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_qtl_cursor(
            filters, str(last["sort_token"]), int(last["duplicate_ordinal"])
        )
    return QtlDetailResponse(
        uniprot_accession=accession, source_database=normalized_source,
        qtl_type=normalized_type, items=items, source_semantics=metadata,
        next_cursor=next_cursor, total_or_estimate=ExactTotal(value=total),
        applied_filters={**filters, "limit": limit},
    )
