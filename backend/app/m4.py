"""M4 interaction, disease, and source-description endpoints.

Interaction detail queries resolve exactly one source/accession bucket. Disease
assertions remain source-specific and MONDO mappings are limited to the
offline exact/eligible bridge.
"""

from __future__ import annotations

import base64
import binascii
from contextlib import contextmanager
import json
import os
from pathlib import Path
from typing import Iterator, Literal

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query
import yaml

from .store import get_connection, require_protein
from .release_store import release_store
from .models import (
    DataSourceDescription,
    DataSourcesResponse,
    DiseaseAssertionItem,
    DiseaseResponse,
    DiseaseSection,
    ExactTotal,
    HpoEvidenceItem,
    HpoEvidenceResponse,
    InteractionDetailItem,
    InteractionDetailResponse,
    InteractionMutationEffect,
    InteractionMutationResponse,
    InteractionSourceSemantics,
    InteractionSummaryItem,
    InteractionSummaryResponse,
)


router = APIRouter(prefix="/api/v1")

DEFAULT_SOURCE_REGISTRY = Path(__file__).resolve().parents[2] / "config" / "source_registry.yaml"
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
INTERACTION_SOURCES = {"biogrid": "BioGRID", "intact": "IntAct"}
DISEASE_TABLES = {
    "clingen_validity": "disease_clingen_validity",
    "clingen_dosage": "disease_clingen_dosage",
    "gencc": "disease_gencc_assertion",
    "omim": "disease_omim_gene_disease",
    "hpo": "disease_hpo_gene",
}
HPO_TABLES = {
    "observed": "disease_hpo_observed",
    "explicitly_absent": "disease_hpo_explicitly_absent",
    "inheritance": "disease_hpo_inheritance",
}

def m4_database_path() -> Path:
    return release_store().m4_database


def source_registry_path() -> Path:
    return Path(os.environ.get("MEMVAR_SOURCE_REGISTRY", DEFAULT_SOURCE_REGISTRY)).resolve()


def load_source_descriptions() -> list[DataSourceDescription]:
    path = source_registry_path()
    if not path.is_file():
        raise RuntimeError(f"Source registry is missing: {path}")
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise RuntimeError(f"Source registry cannot be read: {path}") from error
    if not isinstance(document, dict) or not isinstance(document.get("sources"), dict):
        raise RuntimeError("Source registry must contain a sources mapping")
    descriptions: list[DataSourceDescription] = []
    for source_id, raw in document["sources"].items():
        if not isinstance(source_id, str) or not isinstance(raw, dict):
            raise RuntimeError("Every source registry entry must be a named mapping")
        if "quarantine" in source_id.casefold():
            raise RuntimeError("Quarantine sources must never enter the public source registry")
        missing = [
            field for field in ("display_name", "layer", "record_grain")
            if not isinstance(raw.get(field), str) or not raw[field].strip()
        ]
        if missing:
            raise RuntimeError(
                f"Source registry entry {source_id} is missing: {', '.join(missing)}"
            )
        release = raw.get("source_release")
        caveat = raw.get("caveat")
        if release is not None and not isinstance(release, str):
            raise RuntimeError(f"Source release must be text or null: {source_id}")
        if caveat is not None and not isinstance(caveat, str):
            raise RuntimeError(f"Source caveat must be text or null: {source_id}")
        descriptions.append(DataSourceDescription(
            source_id=source_id,
            display_name=raw["display_name"],
            layer=raw["layer"],
            source_release=release,
            record_grain=raw["record_grain"],
            caveat=caveat,
        ))
    if not descriptions:
        raise RuntimeError("Source registry cannot be empty")
    return descriptions


@contextmanager
def read_m4_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    path = m4_database_path()
    if not path.is_file():
        raise RuntimeError(f"M4 database is missing: {path}")
    connection = duckdb.connect(str(path), read_only=True)
    try:
        yield connection
    finally:
        connection.close()


def get_m4_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    with read_m4_connection() as connection:
        yield connection


def rows_as_dicts(result: duckdb.DuckDBPyConnection) -> list[dict[str, object]]:
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def accession_bucket(accession: str) -> int:
    return sum(
        (ord(accession[index - 1]) if index <= len(accession) else 0) * 31 ** (10 - index)
        for index in range(1, 11)
    ) % 128


def canonical_interaction_source(source: str) -> str:
    canonical = INTERACTION_SOURCES.get(source.strip().casefold())
    if canonical is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown interaction source: {source}. Allowed sources: BioGRID, IntAct",
        )
    return canonical


def interaction_bucket_glob(source: str, accession: str) -> str | None:
    directory = (
        release_store().interaction_facts / f"source={source}"
        / f"accession_bucket={accession_bucket(accession)}"
    )
    if not directory.is_dir() or not any(directory.glob("*.parquet")):
        return None
    return str(directory / "*.parquet")


def interaction_mutation_bucket_glob(accession: str) -> str | None:
    directory = (
        release_store().interaction_mutation_facts / "source=IntAct"
        / f"accession_bucket={accession_bucket(accession)}"
    )
    if not directory.is_dir() or not any(directory.glob("*.parquet")):
        return None
    return str(directory / "*.parquet")


def encode_cursor(kind: str, filters: dict[str, object], token: str, ordinal: int) -> str:
    payload = json.dumps(
        {"v": 1, "kind": kind, "filters": filters, "after": [token, ordinal]},
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(
    cursor: str, kind: str, filters: dict[str, object]
) -> tuple[str, int]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        after = payload["after"]
        if (
            payload.get("v") != 1 or payload.get("kind") != kind
            or payload.get("filters") != filters or not isinstance(after, list)
            or len(after) != 2 or not isinstance(after[0], str)
            or not isinstance(after[1], int) or after[1] < 1
        ):
            raise ValueError
        return after[0], after[1]
    except (
        KeyError, TypeError, ValueError, UnicodeDecodeError, binascii.Error,
        json.JSONDecodeError,
    ) as error:
        raise HTTPException(status_code=400, detail=f"Invalid {kind} cursor") from error


@router.get("/data-sources", response_model=DataSourcesResponse)
def data_sources() -> DataSourcesResponse:
    descriptions = load_source_descriptions()
    return DataSourcesResponse(
        items=descriptions,
        total_or_estimate=ExactTotal(value=len(descriptions)),
    )


def interaction_semantics(
    connection: duckdb.DuckDBPyConnection, sources: list[str]
) -> list[InteractionSourceSemantics]:
    placeholders = ",".join("?" for _ in sources)
    rows = connection.execute(
        f"""SELECT source_database, evidence_grain, caveat
            FROM interaction_source_semantics
            WHERE source_database IN ({placeholders}) ORDER BY source_database""",
        sources,
    ).fetchall()
    found = {row[0] for row in rows}
    missing = sorted(set(sources) - found)
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Interaction source metadata missing: {', '.join(missing)}",
        )
    return [InteractionSourceSemantics(
        source_database=row[0], evidence_grain=row[1], caveat=row[2]
    ) for row in rows]


@router.get(
    "/proteins/{acc}/interactions/summary",
    response_model=InteractionSummaryResponse,
)
def interaction_summary(
    acc: str,
    source: str | None = Query(default=None),
    category: str | None = Query(default=None),
    core_connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    connection: duckdb.DuckDBPyConnection = Depends(get_m4_connection),
) -> InteractionSummaryResponse:
    overview = require_protein(core_connection, acc)
    accession = str(overview["uniprot_accession"])
    normalized_source = canonical_interaction_source(source) if source else None
    category = category.strip() if category and category.strip() else None
    conditions = ["uniprot_accession = ?"]
    parameters: list[object] = [accession]
    if normalized_source:
        conditions.append("source_database = ?")
        parameters.append(normalized_source)
    if category:
        conditions.append("interaction_category = ?")
        parameters.append(category)
    rows = connection.execute(
        f"""SELECT source_database, context_class, context, interaction_category,
                   evidence_record_count, distinct_native_interaction_count
            FROM interaction_summary WHERE {' AND '.join(conditions)}
            ORDER BY source_database, context_class NULLS LAST, context NULLS LAST,
                     interaction_category NULLS LAST""",
        parameters,
    ).fetchall()
    sources = [normalized_source] if normalized_source else list(INTERACTION_SOURCES.values())
    return InteractionSummaryResponse(
        uniprot_accession=accession,
        items=[InteractionSummaryItem(
            source_database=row[0], context_class=row[1], context=row[2],
            interaction_category=row[3], evidence_record_count=row[4],
            distinct_native_interaction_count=row[5],
        ) for row in rows],
        source_semantics=interaction_semantics(connection, sources),
        total_or_estimate=ExactTotal(value=len(rows)),
        applied_filters={"source": normalized_source, "category": category},
    )


def biogrid_interaction_item(row: dict[str, object]) -> InteractionDetailItem:
    return InteractionDetailItem(
        source_database="BioGRID", native_interaction_id=row["native_interaction_id"],
        page_role=row["page_role"], interaction_category=row["interaction_category"],
        context_class=row["context_class"], context=row["context"],
        partner={
            "gene_id": row["partner_gene_id"], "symbol": row["partner_symbol"],
            "swissprot_accessions": row["partner_swissprot_accessions"],
            "taxid": row["partner_taxid"],
        },
        publication=row["publication"],
        source_specific={"biogrid": {
            key: row[key] for key in (
                "source_release", "evidence_grain", "interactor_a_gene_id",
                "interactor_b_gene_id", "interactor_a_symbol", "interactor_b_symbol",
                "interactor_a_swissprot_accessions", "interactor_b_swissprot_accessions",
                "interactor_a_taxid", "interactor_b_taxid",
                "mapped_membrane_gene_id_a", "mapped_membrane_gene_id_b",
                "experimental_system", "throughput", "score", "modification",
                "qualifications", "tags", "ontology_term_ids", "ontology_term_names",
                "ontology_term_categories", "ontology_term_qualifier_ids",
                "ontology_term_qualifier_names", "ontology_term_types",
            )
        }},
    )


def intact_interaction_item(row: dict[str, object]) -> InteractionDetailItem:
    return InteractionDetailItem(
        source_database="IntAct", native_interaction_id=row["native_interaction_id"],
        page_role=row["page_role"], interaction_category=row["interaction_category"],
        context_class=row["context_class"], context=row["context"],
        partner={
            "raw_id": row["partner_raw_id"], "alias": row["partner_alias"],
            "taxid": row["partner_taxid"], "type": row["partner_type"],
        },
        publication=row["publication"],
        source_specific={"intact": {
            key: row[key] for key in (
                "source_release", "evidence_grain", "interactor_a_raw_id",
                "interactor_b_raw_id", "interactor_a_alt_id", "interactor_b_alt_id",
                "interactor_a_alias", "interactor_b_alias", "interactor_a_taxid",
                "interactor_b_taxid", "interactor_a_type", "interactor_b_type",
                "source_uniprot_accession_a", "source_uniprot_accession_b",
                "mapped_membrane_accession_a", "mapped_membrane_accession_b",
                "detection_method", "interaction_type", "publication_first_author",
                "source_database_raw", "confidence", "expansion_method", "biological_role_a",
                "biological_role_b", "experimental_role_a", "experimental_role_b",
                "annotation_a", "annotation_b", "interaction_annotation", "host_organism",
                "interaction_parameters", "creation_date", "update_date", "is_negative",
                "features_a", "features_b", "stoichiometry_a", "stoichiometry_b",
                "identification_method_a", "identification_method_b",
            )
        }},
    )


@router.get("/proteins/{acc}/interactions", response_model=InteractionDetailResponse)
def interactions(
    acc: str,
    source: str = Query(...),
    context_class: str | None = Query(default=None),
    context: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(default=None),
    core_connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    connection: duckdb.DuckDBPyConnection = Depends(get_m4_connection),
) -> InteractionDetailResponse:
    overview = require_protein(core_connection, acc)
    accession = str(overview["uniprot_accession"])
    normalized_source = canonical_interaction_source(source)
    context_class = context_class.strip() if context_class and context_class.strip() else None
    context = context.strip() if context and context.strip() else None
    category = category.strip() if category and category.strip() else None
    filters: dict[str, object] = {
        "accession": accession, "source": normalized_source,
        "context_class": context_class, "context": context, "category": category,
    }
    after = decode_cursor(cursor, "interaction", filters) if cursor else None
    metadata = interaction_semantics(connection, [normalized_source])[0]
    path = interaction_bucket_glob(normalized_source, accession)
    if path is None:
        return InteractionDetailResponse(
            uniprot_accession=accession, source_database=normalized_source,
            items=[], source_semantics=metadata, total_or_estimate=ExactTotal(value=0),
            applied_filters={**filters, "limit": limit},
        )
    conditions = ["x.uniprot_accession = ?"]
    filter_parameters: list[object] = [accession]
    for column, value in (
        ("context_class", context_class), ("context", context),
        ("interaction_category", category),
    ):
        if value:
            conditions.append(f"x.{column} = ?")
            filter_parameters.append(value)
    after_sql = ""
    after_parameters: list[object] = []
    if after:
        after_sql = "WHERE (sort_token, duplicate_ordinal) > (?, ?)"
        after_parameters = [after[0], after[1]]
    where = " AND ".join(conditions)
    rows = rows_as_dicts(connection.execute(
        f"""
        WITH base AS (
          SELECT x.*, to_json(x) AS row_json FROM read_parquet(?) x WHERE {where}
        ), keyed AS (
          SELECT *, coalesce(context, '') || chr(31) ||
            coalesce(native_interaction_id, '') || chr(31) || row_json AS sort_token,
            row_number() OVER (PARTITION BY row_json ORDER BY row_json) AS duplicate_ordinal
          FROM base
        )
        SELECT * FROM keyed {after_sql}
        ORDER BY sort_token, duplicate_ordinal LIMIT ?
        """,
        [path, *filter_parameters, *after_parameters, limit + 1],
    ))
    total = connection.execute(
        f"SELECT count(*) FROM read_parquet(?) x WHERE {where}",
        [path, *filter_parameters],
    ).fetchone()[0]
    has_more = len(rows) > limit
    page = rows[:limit]
    adapter = biogrid_interaction_item if normalized_source == "BioGRID" else intact_interaction_item
    items = [adapter(row) for row in page]
    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_cursor(
            "interaction", filters, str(last["sort_token"]),
            int(last["duplicate_ordinal"]),
        )
    return InteractionDetailResponse(
        uniprot_accession=accession, source_database=normalized_source,
        items=items, source_semantics=metadata, next_cursor=next_cursor,
        total_or_estimate=ExactTotal(value=total),
        applied_filters={**filters, "limit": limit},
    )


@router.get(
    "/proteins/{acc}/interactions/mutation-effects",
    response_model=InteractionMutationResponse,
)
def interaction_mutation_effects(
    acc: str,
    feature_type: str | None = Query(default=None),
    interaction_accession: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(default=None),
    core_connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    connection: duckdb.DuckDBPyConnection = Depends(get_m4_connection),
) -> InteractionMutationResponse:
    overview = require_protein(core_connection, acc)
    accession = str(overview["uniprot_accession"])
    feature_type = feature_type.strip() if feature_type and feature_type.strip() else None
    interaction_accession = (
        interaction_accession.strip()
        if interaction_accession and interaction_accession.strip() else None
    )
    filters: dict[str, object] = {
        "accession": accession, "feature_type": feature_type,
        "interaction_accession": interaction_accession,
    }
    after = decode_cursor(cursor, "interaction mutation", filters) if cursor else None
    path = interaction_mutation_bucket_glob(accession)
    if path is None:
        return InteractionMutationResponse(
            uniprot_accession=accession, items=[], total_or_estimate=ExactTotal(value=0),
            applied_filters={**filters, "limit": limit},
        )
    conditions = ["x.uniprot_accession = ?"]
    filter_parameters: list[object] = [accession]
    if feature_type:
        conditions.append("x.feature_type = ?")
        filter_parameters.append(feature_type)
    if interaction_accession:
        conditions.append("x.interaction_ac = ?")
        filter_parameters.append(interaction_accession)
    after_sql = ""
    after_parameters: list[object] = []
    if after:
        after_sql = "WHERE (sort_token, duplicate_ordinal) > (?, ?)"
        after_parameters = [after[0], after[1]]
    where = " AND ".join(conditions)
    rows = rows_as_dicts(connection.execute(
        f"""
        WITH base AS (
          SELECT x.*, to_json(x) AS row_json FROM read_parquet(?) x WHERE {where}
        ), keyed AS (
          SELECT *, coalesce(feature_ac, '') || chr(31) ||
            coalesce(interaction_ac, '') || chr(31) || row_json AS sort_token,
            row_number() OVER (PARTITION BY row_json ORDER BY row_json) AS duplicate_ordinal
          FROM base
        )
        SELECT * FROM keyed {after_sql}
        ORDER BY sort_token, duplicate_ordinal LIMIT ?
        """,
        [path, *filter_parameters, *after_parameters, limit + 1],
    ))
    total = connection.execute(
        f"SELECT count(*) FROM read_parquet(?) x WHERE {where}",
        [path, *filter_parameters],
    ).fetchone()[0]
    has_more = len(rows) > limit
    page = rows[:limit]
    items = [InteractionMutationEffect(
        source_release=row["source_release"], evidence_grain=row["evidence_grain"],
        feature_accession=row["feature_ac"], feature_short_label=row["feature_short_label"],
        feature_ranges=row["feature_ranges"], original_sequence=row["original_sequence"],
        resulting_sequence=row["resulting_sequence"], feature_type=row["feature_type"],
        feature_annotation=row["feature_annotation"],
        affected_protein={
            "accession": row["affected_protein_ac"],
            "symbol": row["affected_protein_symbol"],
            "full_name": row["affected_protein_full_name"],
            "organism": row["affected_protein_organism"],
        },
        interaction_participants=row["interaction_participants"],
        pubmed_id=row["pubmed_id"], figure_legend=row["figure_legend"],
        interaction_accession=row["interaction_ac"],
    ) for row in page]
    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_cursor(
            "interaction mutation", filters, str(last["sort_token"]),
            int(last["duplicate_ordinal"]),
        )
    return InteractionMutationResponse(
        uniprot_accession=accession, items=items, next_cursor=next_cursor,
        total_or_estimate=ExactTotal(value=total),
        applied_filters={**filters, "limit": limit},
    )


def exact_mondo_mappings(
    connection: duckdb.DuckDBPyConnection,
    disease_id: str | None,
) -> list[dict[str, object]]:
    if disease_id is None:
        return []
    mappings = rows_as_dicts(connection.execute(
        """SELECT * FROM disease_mondo_exact
           WHERE source_disease_id = ?
           ORDER BY mondo_id""",
        [disease_id],
    ))
    for mapping in mappings:
        categories = connection.execute(
            """SELECT category_mondo_id, category_name, category_axis,
                      is_hereditary, is_neoplastic
               FROM disease_mondo_category
               WHERE source_disease_id = ? AND mondo_id = ?
               ORDER BY category_axis, category_name, category_mondo_id""",
            [disease_id, mapping["mondo_id"]],
        )
        mapping["categories"] = rows_as_dicts(categories)
    return mappings


def disease_section(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    source: str,
    limit: int,
    cursor: str | None,
) -> DiseaseSection:
    table = DISEASE_TABLES[source]
    filters: dict[str, object] = {"accession": accession, "source": source}
    after = decode_cursor(cursor, "disease", filters) if cursor else None
    after_sql = ""
    parameters: list[object] = [accession]
    if after:
        after_sql = "WHERE (sort_token, duplicate_ordinal) > (?, ?)"
        parameters.extend(after)
    result = connection.execute(
        f"""
        WITH base AS (
          SELECT x.*, to_json(x) AS row_json FROM {table} x
          WHERE x.uniprot_accession = ?
        ), keyed AS (
          SELECT *, row_json AS sort_token,
            row_number() OVER (PARTITION BY row_json ORDER BY row_json) AS duplicate_ordinal
          FROM base
        )
        SELECT * FROM keyed {after_sql}
        ORDER BY sort_token, duplicate_ordinal LIMIT ?
        """,
        [*parameters, limit + 1],
    )
    rows = rows_as_dicts(result)
    total = connection.execute(
        f"SELECT count(*) FROM {table} WHERE uniprot_accession = ?", [accession]
    ).fetchone()[0]
    has_more = len(rows) > limit
    page = rows[:limit]
    items: list[DiseaseAssertionItem] = []
    for row in page:
        disease_id = row.get("disease_id")
        disease_name = row.get("disease_name")
        assertion = {
            key: value for key, value in row.items()
            if key not in {
                "uniprot_accession", "accession_bucket", "row_json", "sort_token",
                "duplicate_ordinal", "disease_id", "disease_name",
            }
        }
        items.append(DiseaseAssertionItem(
            source=source, disease_id=disease_id, disease_name=disease_name,
            assertion=assertion,
            exact_mondo_mappings=exact_mondo_mappings(
                connection, disease_id if isinstance(disease_id, str) else None
            ),
        ))
    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_cursor(
            "disease", filters, str(last["sort_token"]), int(last["duplicate_ordinal"])
        )
    return DiseaseSection(
        source=source, items=items, next_cursor=next_cursor,
        total_or_estimate=ExactTotal(value=total),
    )


@router.get("/proteins/{acc}/diseases", response_model=DiseaseResponse)
def diseases(
    acc: str,
    source: Literal[
        "clingen_validity", "clingen_dosage", "gencc", "omim", "hpo"
    ] | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(default=None),
    core_connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    connection: duckdb.DuckDBPyConnection = Depends(get_m4_connection),
) -> DiseaseResponse:
    overview = require_protein(core_connection, acc)
    accession = str(overview["uniprot_accession"])
    if cursor and source is None:
        raise HTTPException(
            status_code=400, detail="A disease cursor requires an explicit source"
        )
    requested = [source] if source else list(DISEASE_TABLES)
    sections = {
        item_source: disease_section(
            connection, accession, item_source, limit,
            cursor if source == item_source else None,
        )
        for item_source in requested
    }
    return DiseaseResponse(
        uniprot_accession=accession,
        sections=sections,
        applied_filters={"source": source, "limit": limit},
    )


@router.get("/proteins/{acc}/diseases/hpo", response_model=HpoEvidenceResponse)
def hpo_evidence(
    acc: str,
    category: Literal["observed", "explicitly_absent", "inheritance"] = Query(...),
    disease_id: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(default=None),
    core_connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    connection: duckdb.DuckDBPyConnection = Depends(get_m4_connection),
) -> HpoEvidenceResponse:
    overview = require_protein(core_connection, acc)
    accession = str(overview["uniprot_accession"])
    disease_id = disease_id.strip() if disease_id and disease_id.strip() else None
    filters: dict[str, object] = {
        "accession": accession, "category": category, "disease_id": disease_id,
    }
    after = decode_cursor(cursor, "HPO evidence", filters) if cursor else None
    conditions = ["x.uniprot_accession = ?"]
    filter_parameters: list[object] = [accession]
    if disease_id:
        conditions.append("x.disease_id = ?")
        filter_parameters.append(disease_id)
    after_sql = ""
    after_parameters: list[object] = []
    if after:
        after_sql = "WHERE (sort_token, duplicate_ordinal) > (?, ?)"
        after_parameters = [after[0], after[1]]
    table = HPO_TABLES[category]
    rows = rows_as_dicts(connection.execute(
        f"""
        WITH base AS (
          SELECT x.*, to_json(x) AS row_json FROM {table} x
          WHERE {' AND '.join(conditions)}
        ), keyed AS (
          SELECT *, row_json AS sort_token,
            row_number() OVER (PARTITION BY row_json ORDER BY row_json) AS duplicate_ordinal
          FROM base
        )
        SELECT * FROM keyed {after_sql}
        ORDER BY sort_token, duplicate_ordinal LIMIT ?
        """,
        [*filter_parameters, *after_parameters, limit + 1],
    ))
    total = connection.execute(
        f"SELECT count(*) FROM {table} x WHERE {' AND '.join(conditions)}",
        filter_parameters,
    ).fetchone()[0]
    has_more = len(rows) > limit
    page = rows[:limit]
    items = []
    for row in page:
        evidence = {
            key: value for key, value in row.items()
            if key not in {
                "uniprot_accession", "accession_bucket", "row_json", "sort_token",
                "duplicate_ordinal", "disease_id", "disease_name", "hpo_id",
                "hpo_name", "qualifier", "aspect", "phenotype_status",
            }
        }
        items.append(HpoEvidenceItem(
            disease_id=row.get("disease_id"), disease_name=row.get("disease_name"),
            hpo_id=row.get("hpo_id"), hpo_name=row.get("hpo_name"),
            qualifier=row.get("qualifier"), aspect=row.get("aspect"),
            phenotype_status=row.get("phenotype_status"), evidence=evidence,
        ))
    next_cursor = None
    if has_more and page:
        last = page[-1]
        next_cursor = encode_cursor(
            "HPO evidence", filters, str(last["sort_token"]),
            int(last["duplicate_ordinal"]),
        )
    return HpoEvidenceResponse(
        uniprot_accession=accession, category=category, items=items,
        next_cursor=next_cursor, total_or_estimate=ExactTotal(value=total),
        applied_filters={**filters, "limit": limit},
    )
