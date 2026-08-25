"""FastAPI application serving only the website-owned DuckDB core mart."""

from __future__ import annotations

import base64
import binascii
import json
from time import perf_counter
from typing import Literal

import duckdb
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import Response

from .models import (
    AnnotationResponse,
    CanonicalSequenceMetadata,
    CompactAnnotationSummary,
    DataSourceDescription,
    ExactTotal,
    GoAspectCount,
    GoEvidenceCodeCount,
    GoEvidenceItem,
    GoEvidenceResponse,
    GoSummary,
    GoTermsResponse,
    GoTermSummary,
    Identifier,
    ProteinOverviewResponse,
    ReactomeHierarchyNode,
    ReactomeHierarchyResponse,
    ReactomePathway,
    SearchCandidate,
    SearchMatch,
    SearchResponse,
    SubcellularLocation,
)
from .store import get_connection, require_protein, row_dict
from .release_store import release_store
from .http_policy import (
    NO_STORE_CACHE_CONTROL,
    REVALIDATE_CACHE_CONTROL,
    application_release,
    if_none_match_matches,
    normalized_route,
    release_etag,
)
from .de import router as de_router
from .m2 import router as m2_router
from .m3 import router as m3_router
from .m4 import load_source_descriptions, router as m4_router
from .structure import router as structure_router
from .alphagenome import router as alphagenome_router
from .anatomy import router as anatomy_router


ANNOTATION_PAGE_SIZE = 50
OVERVIEW_ANNOTATION_LIMIT = 10
ANNOTATION_SECTIONS = {"go", "reactome", "location"}


def split_compact(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def as_identifier(row: tuple[object, ...]) -> Identifier:
    return Identifier(
        isoform_id=row[0],
        identifier_type=row[1],
        identifier_database=row[2],
        identifier_full=row[3],
        identifier_base=row[4],
        identifier_version=row[5],
        alias_type=row[6],
        identifier_label=row[7],
    )


def get_go_summary(connection: duckdb.DuckDBPyConnection, accession: str) -> GoSummary | None:
    row = connection.execute(
        """
        SELECT go_molecular_function, go_biological_process, go_cellular_component
        FROM go_summary WHERE uniprot_accession = ?
        """,
        [accession],
    ).fetchone()
    if row is None:
        return None
    return GoSummary(
        molecular_function=split_compact(row[0]),
        biological_process=split_compact(row[1]),
        cellular_component=split_compact(row[2]),
    )


def reactome_rows(connection: duckdb.DuckDBPyConnection, accession: str, limit: int | None = None) -> list[ReactomePathway]:
    query = """
        SELECT pathway_id, pathway_name, pathway_url, evidence_codes, evidence_count
        FROM reactome_membership
        WHERE uniprot_accession = ?
        ORDER BY pathway_name NULLS LAST, pathway_id NULLS LAST
    """
    parameters: list[object] = [accession]
    if limit is not None:
        query += " LIMIT ?"
        parameters.append(limit)
    return [
        ReactomePathway(
            pathway_id=row[0], pathway_name=row[1], pathway_url=row[2],
            evidence_codes=split_compact(row[3]), evidence_count=row[4],
        )
        for row in connection.execute(query, parameters).fetchall()
    ]


def reactome_hierarchy(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
) -> ReactomeHierarchyResponse:
    pathways = reactome_rows(connection, accession)
    pathways_by_id: dict[str, ReactomePathway] = {}
    for pathway in pathways:
        pathway_id = pathway.pathway_id
        if pathway_id is None or pathway_id in pathways_by_id:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid Reactome membership identity for: {accession}",
            )
        pathways_by_id[pathway_id] = pathway

    edge_rows = connection.execute(
        """
        WITH membership AS (
            SELECT pathway_id
            FROM reactome_membership
            WHERE uniprot_accession = ?
        )
        SELECT edge.parent_pathway_id, edge.child_pathway_id
        FROM reactome_hierarchy_edge edge
        JOIN membership parent ON parent.pathway_id = edge.parent_pathway_id
        JOIN membership child ON child.pathway_id = edge.child_pathway_id
        ORDER BY edge.parent_pathway_id, edge.child_pathway_id
        """,
        [accession],
    ).fetchall()
    edges = [(str(parent_id), str(child_id)) for parent_id, child_id in edge_rows]
    if len(edges) != len(set(edges)):
        raise HTTPException(status_code=500, detail="Reactome hierarchy contains duplicate direct edges")
    if any(parent_id not in pathways_by_id or child_id not in pathways_by_id for parent_id, child_id in edges):
        raise HTTPException(status_code=500, detail="Reactome hierarchy edge endpoint is not a membership node")

    def pathway_sort_key(pathway_id: str) -> tuple[bool, str, str]:
        pathway_name = pathways_by_id[pathway_id].pathway_name
        return pathway_name is None, pathway_name or "", pathway_id

    parent_ids: dict[str, set[str]] = {pathway_id: set() for pathway_id in pathways_by_id}
    child_ids: dict[str, set[str]] = {pathway_id: set() for pathway_id in pathways_by_id}
    for parent_id, child_id in edges:
        child_ids[parent_id].add(child_id)
        parent_ids[child_id].add(parent_id)

    ordered_ids = sorted(pathways_by_id, key=pathway_sort_key)
    nodes = [
        ReactomeHierarchyNode(
            **pathways_by_id[pathway_id].model_dump(exclude={"pathway_id"}),
            pathway_id=pathway_id,
            parent_ids=sorted(parent_ids[pathway_id], key=pathway_sort_key),
            child_ids=sorted(child_ids[pathway_id], key=pathway_sort_key),
        )
        for pathway_id in ordered_ids
    ]
    roots = sorted(
        (pathway_id for pathway_id in ordered_ids if not parent_ids[pathway_id]),
        key=pathway_sort_key,
    )
    return ReactomeHierarchyResponse(
        uniprot_accession=accession,
        nodes=nodes,
        roots=roots,
        node_total=len(nodes),
        edge_total=len(edges),
        root_total=len(roots),
        shared_node_total=sum(len(parents) > 1 for parents in parent_ids.values()),
    )


def location_rows(connection: duckdb.DuckDBPyConnection, accession: str, limit: int | None = None) -> list[SubcellularLocation]:
    query = """
        SELECT sequence_version, location_id, location_name, topology_id, topology_name,
               orientation_id, orientation_name
        FROM subcellular_location
        WHERE uniprot_accession = ?
        ORDER BY location_name NULLS LAST, topology_name NULLS LAST, orientation_name NULLS LAST,
                 location_id NULLS LAST
    """
    parameters: list[object] = [accession]
    if limit is not None:
        query += " LIMIT ?"
        parameters.append(limit)
    return [
        SubcellularLocation(
            sequence_version=row[0], location_id=row[1], location_name=row[2],
            topology_id=row[3], topology_name=row[4], orientation_id=row[5], orientation_name=row[6],
        )
        for row in connection.execute(query, parameters).fetchall()
    ]


def compact_annotations(connection: duckdb.DuckDBPyConnection, accession: str) -> CompactAnnotationSummary:
    reactome_total = connection.execute(
        "SELECT count(*) FROM reactome_membership WHERE uniprot_accession = ?", [accession]
    ).fetchone()[0]
    locations_total = connection.execute(
        "SELECT count(*) FROM subcellular_location WHERE uniprot_accession = ?", [accession]
    ).fetchone()[0]
    return CompactAnnotationSummary(
        go=get_go_summary(connection, accession),
        reactome=reactome_rows(connection, accession, OVERVIEW_ANNOTATION_LIMIT),
        reactome_total=reactome_total,
        locations=location_rows(connection, accession, OVERVIEW_ANNOTATION_LIMIT),
        locations_total=locations_total,
        item_limit=OVERVIEW_ANNOTATION_LIMIT,
    )


def encode_cursor(section: str | None, offset: int) -> str:
    payload = json.dumps({"section": section, "offset": offset}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: str, section: str | None) -> int:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        offset = payload["offset"]
        if payload.get("section") != section or not isinstance(offset, int) or offset < 0:
            raise ValueError
        return offset
    except (
        KeyError, TypeError, ValueError, UnicodeDecodeError, binascii.Error,
        json.JSONDecodeError,
    ) as error:
        raise HTTPException(status_code=400, detail="Invalid annotation cursor") from error


def encode_go_cursor(kind: str, filters: dict[str, object], after: list[object]) -> str:
    payload = json.dumps({"v": 1, "kind": kind, "filters": filters, "after": after}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_go_cursor(cursor: str, kind: str, filters: dict[str, object]) -> list[object]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        after = payload["after"]
        if payload.get("v") != 1 or payload.get("kind") != kind or payload.get("filters") != filters:
            raise ValueError
        if not isinstance(after, list):
            raise ValueError
        return after
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, binascii.Error, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail="Invalid GO evidence cursor") from error


def go_filters(
    accession: str,
    aspect: Literal["MF", "BP", "CC"] | None,
    evidence_code: str | None,
    query: str | None,
    include_negated: bool,
    *,
    include_aspect: bool = True,
) -> tuple[str, list[object]]:
    clauses = ["e.uniprot_accession = ?"]
    parameters: list[object] = [accession]
    if not include_negated:
        clauses.append("coalesce(e.is_negated, false) = false")
    if include_aspect and aspect is not None:
        clauses.append("e.go_aspect = ?")
        parameters.append(aspect)
    if evidence_code is not None:
        clauses.append("e.evidence_code = ?")
        parameters.append(evidence_code)
    if query is not None:
        clauses.append("(contains(lower(e.go_id), ?) OR contains(lower(e.go_term_name), ?))")
        parameters.extend([query, query])
    return " AND ".join(clauses), parameters


def goa_provenance() -> DataSourceDescription:
    matches = [item for item in load_source_descriptions() if item.source_id == "goa_annotation"]
    if len(matches) != 1:
        raise RuntimeError("Source registry must contain exactly one goa_annotation entry")
    return matches[0]


def annotation_items(
    connection: duckdb.DuckDBPyConnection,
    accession: str,
    section: Literal["go", "reactome", "location"] | None,
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    if section in (None, "go"):
        go = get_go_summary(connection, accession)
        if go is not None:
            items.append({"section": "go", **go.model_dump()})
    if section in (None, "reactome"):
        items.extend({"section": "reactome", **row.model_dump()} for row in reactome_rows(connection, accession))
    if section in (None, "location"):
        items.extend({"section": "location", **row.model_dump()} for row in location_rows(connection, accession))
    return items


def create_app() -> FastAPI:
    app = FastAPI(title="memVar API", version="0.4.0")
    @app.middleware("http")
    async def release_aware_api_response_policy(request: Request, call_next):
        started = perf_counter()
        response = await call_next(request)
        if not request.url.path.startswith("/api/"):
            return response

        duration_ms = (perf_counter() - started) * 1000
        route = normalized_route(request)
        response.headers["Server-Timing"] = (
            f'app;dur={duration_ms:.1f};desc="{route}"'
        )
        is_structure_asset = (
            request.url.path.startswith("/api/v1/proteins/")
            and "/structures/" in request.url.path
            and request.url.path.endswith("/pdb")
        )
        release_id = release_store().release_id
        response.headers["X-MemVar-Release"] = release_id
        if not 200 <= response.status_code < 300:
            response.headers["Cache-Control"] = NO_STORE_CACHE_CONTROL
            return response

        if is_structure_asset:
            return response

        is_revalidatable_json = (
            request.method in {"GET", "HEAD"}
            and response.headers.get("content-type", "").startswith("application/json")
        )
        if not is_revalidatable_json:
            response.headers["Cache-Control"] = NO_STORE_CACHE_CONTROL
            return response

        app_release = application_release()
        if app_release is None:
            response.headers["Cache-Control"] = NO_STORE_CACHE_CONTROL
            return response

        etag = release_etag(release_id, app_release, request)
        response.headers["Cache-Control"] = REVALIDATE_CACHE_CONTROL
        response.headers["ETag"] = etag
        if if_none_match_matches(request.headers.get("if-none-match"), etag):
            return Response(
                status_code=304,
                headers={
                    "Cache-Control": REVALIDATE_CACHE_CONTROL,
                    "ETag": etag,
                    "Server-Timing": response.headers["Server-Timing"],
                    "X-MemVar-Release": release_id,
                },
            )
        return response
    app.include_router(m2_router)
    app.include_router(m3_router)
    app.include_router(m4_router)
    app.include_router(structure_router)
    app.include_router(de_router)
    app.include_router(alphagenome_router)
    app.include_router(anatomy_router)

    @app.get("/api/v1/search", response_model=SearchResponse)
    def search(
        q: str = Query(default=""),
        limit: int = Query(default=20, ge=1, le=50),
        connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    ) -> SearchResponse:
        query = q.strip()
        if not query:
            return SearchResponse(
                query=query, items=[], total_or_estimate=ExactTotal(value=0),
                applied_filters={"limit": limit}, ambiguity=False, resolution="no_match",
            )

        normalized = query.upper()
        rows = connection.execute(
            """
            WITH matches AS (
                SELECT
                    s.uniprot_accession,
                    s.search_text,
                    s.identifier_type,
                    s.identifier_database,
                    s.match_priority,
                    CASE
                        WHEN s.normalized_text = ? THEN 'exact'
                        WHEN starts_with(s.normalized_text, ?) THEN 'prefix'
                        ELSE 'token'
                    END AS match_kind,
                    CASE
                        WHEN s.normalized_text = ? THEN 3
                        WHEN starts_with(s.normalized_text, ?) THEN 2
                        ELSE 1
                    END AS kind_priority
                FROM protein_search_index s
                WHERE s.normalized_text = ?
                   OR starts_with(s.normalized_text, ?)
                   OR (
                       length(?) >= 3
                       AND s.identifier_type = 'protein_name'
                       AND contains(s.normalized_text, ?)
                   )
            ), ranked AS (
                SELECT *, row_number() OVER (
                    PARTITION BY uniprot_accession
                    ORDER BY kind_priority DESC, match_priority DESC, identifier_type,
                             identifier_database, search_text
                ) AS match_rank
                FROM matches
            ), best_kind AS (
                SELECT max(kind_priority) AS kind_priority FROM ranked
            ), preferred AS (
                SELECT r.*
                FROM ranked r
                CROSS JOIN best_kind b
                WHERE r.kind_priority = b.kind_priority
            )
            SELECT r.uniprot_accession, o.gene_symbol, o.protein_name, o.entry_name,
                   o.membrane_class, o.canonical_length, r.search_text, r.identifier_type,
                   r.identifier_database, r.match_kind, r.kind_priority, r.match_priority
            FROM preferred r
            JOIN protein_overview o USING (uniprot_accession)
            WHERE r.match_rank = 1
            ORDER BY r.kind_priority DESC, r.match_priority DESC, o.gene_symbol NULLS LAST,
                     r.uniprot_accession
            """,
            [normalized, normalized, normalized, normalized, normalized, normalized, normalized, normalized],
        ).fetchall()
        total = len(rows)
        # ``limit`` bounds prefix/token suggestions. An exact biological
        # identifier or alias must return its complete one-to-many candidate
        # set so the browser can never hide a valid protein choice.
        exact_candidate_set = bool(rows) and rows[0][9] == "exact"
        selected_rows = rows if exact_candidate_set else rows[:limit]
        candidates = [
            SearchCandidate(
                uniprot_accession=row[0], gene_symbol=row[1], protein_name=row[2], entry_name=row[3],
                membrane_class=row[4], canonical_length=row[5],
                match=SearchMatch(text=row[6], identifier_type=row[7], identifier_database=row[8], kind=row[9]),
            )
            for row in selected_rows
        ]
        resolution: Literal["no_match", "direct_candidate", "candidate_selection"]
        if total == 0:
            resolution = "no_match"
        elif total == 1:
            resolution = "direct_candidate"
        else:
            resolution = "candidate_selection"
        return SearchResponse(
            query=query, items=candidates, total_or_estimate=ExactTotal(value=total),
            applied_filters={
                "limit": limit,
                "limit_applies_to": "prefix_and_token_suggestions",
                "exact_candidate_set_complete": exact_candidate_set,
            },
            ambiguity=total > 1, resolution=resolution,
        )

    @app.get("/api/v1/proteins/{acc}", response_model=ProteinOverviewResponse)
    def protein_overview(
        acc: str,
        connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    ) -> ProteinOverviewResponse:
        overview = require_protein(connection, acc)
        accession = str(overview["uniprot_accession"])
        sequence = row_dict(
            connection,
            """
            SELECT sequence_id, length, parent_canonical_sequence_version
            FROM protein_sequence WHERE uniprot_accession = ?
            """,
            [accession],
        )
        if sequence is None:
            raise HTTPException(status_code=500, detail=f"Canonical sequence metadata missing for: {accession}")
        identifiers = [
            as_identifier(row)
            for row in connection.execute(
                """
                SELECT isoform_id, identifier_type, identifier_database, identifier_full,
                       identifier_base, identifier_version, alias_type, identifier_label
                FROM protein_identifier
                WHERE uniprot_accession = ?
                ORDER BY identifier_type, identifier_database NULLS LAST, identifier_full NULLS LAST,
                         isoform_id NULLS LAST
                """,
                [accession],
            ).fetchall()
        ]
        return ProteinOverviewResponse(
            **{key: value for key, value in overview.items() if key != "all_class_labels"},
            all_class_labels=split_compact(overview["all_class_labels"]),
            canonical_sequence=CanonicalSequenceMetadata(
                sequence_id=str(sequence["sequence_id"]), length=int(sequence["length"]),
                sequence_version=sequence["parent_canonical_sequence_version"],
            ),
            identifiers=identifiers,
            annotation_summary=compact_annotations(connection, accession),
        )

    @app.get(
        "/api/v1/proteins/{acc}/reactome-hierarchy",
        response_model=ReactomeHierarchyResponse,
    )
    def protein_reactome_hierarchy(
        acc: str,
        connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    ) -> ReactomeHierarchyResponse:
        overview = require_protein(connection, acc)
        accession = str(overview["uniprot_accession"])
        return reactome_hierarchy(connection, accession)

    @app.get("/api/v1/proteins/{acc}/go/terms", response_model=GoTermsResponse)
    def go_terms(
        acc: str,
        aspect: Literal["MF", "BP", "CC"] | None = Query(default=None),
        evidence_code: str | None = Query(default=None, max_length=40),
        q: str | None = Query(default=None, max_length=120),
        include_negated: bool = Query(default=False),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None),
        connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    ) -> GoTermsResponse:
        """Return bounded, grouped GO terms; raw annotation rows stay behind term drill-down."""
        overview = require_protein(connection, acc)
        accession = str(overview["uniprot_accession"])
        normalized_code = evidence_code.strip().upper() if evidence_code and evidence_code.strip() else None
        normalized_query = q.strip().lower() if q and q.strip() else None
        filters: dict[str, object] = {
            "aspect": aspect,
            "evidence_code": normalized_code,
            "q": normalized_query,
            "include_negated": include_negated,
            "limit": limit,
        }
        after: list[object] | None = None
        if cursor is not None:
            after = decode_go_cursor(cursor, "terms", filters)
            if len(after) != 3 or not all(isinstance(value, str) for value in after):
                raise HTTPException(status_code=400, detail="Invalid GO evidence cursor")
        where_all, all_parameters = go_filters(
            accession, aspect, normalized_code, normalized_query, include_negated, include_aspect=False,
        )
        where_terms, term_parameters = go_filters(
            accession, aspect, normalized_code, normalized_query, include_negated,
        )
        total_row = connection.execute(
            f"""
            WITH filtered AS (SELECT e.* FROM go_evidence e WHERE {where_terms}),
                 terms AS (
                   SELECT go_id, go_term_name, go_aspect
                   FROM filtered GROUP BY go_id, go_term_name, go_aspect
                 )
            SELECT count(*) AS term_count, (SELECT count(*) FROM filtered) AS annotation_count
            FROM terms
            """, term_parameters,
        ).fetchone()
        aspect_rows = connection.execute(
            f"""
            WITH filtered AS (SELECT e.* FROM go_evidence e WHERE {where_all})
            SELECT go_aspect, count(DISTINCT (go_id, go_term_name)), count(*),
                   count(DISTINCT nullif(reference_id, ''))
            FROM filtered GROUP BY go_aspect ORDER BY go_aspect
            """, all_parameters,
        ).fetchall()
        keyset = "" if after is None else "WHERE (go_aspect, lower(go_term_name), go_id) > (?, ?, ?)"
        rows = connection.execute(
            f"""
            WITH filtered AS (SELECT e.* FROM go_evidence e WHERE {where_terms}),
                 term_counts AS (
                   SELECT go_id, go_term_name, go_aspect, any_value(go_namespace) AS go_namespace,
                          count(*) AS annotation_count,
                          count(DISTINCT nullif(reference_id, '')) AS reference_count
                   FROM filtered GROUP BY go_id, go_term_name, go_aspect
                 ), code_counts AS (
                   SELECT go_id, go_term_name, go_aspect, evidence_code, count(*) AS annotation_count
                   FROM filtered WHERE evidence_code IS NOT NULL AND trim(evidence_code) <> ''
                   GROUP BY go_id, go_term_name, go_aspect, evidence_code
                 ), terms AS (
                   SELECT t.go_id, t.go_term_name, t.go_aspect, t.go_namespace,
                          t.annotation_count, t.reference_count,
                          coalesce(
                            list(struct_pack(evidence_code := c.evidence_code, annotation_count := c.annotation_count)
                              ORDER BY c.evidence_code) FILTER (WHERE c.evidence_code IS NOT NULL),
                            []
                          ) AS evidence_codes
                   FROM term_counts t
                   LEFT JOIN code_counts c USING (go_id, go_term_name, go_aspect)
                   GROUP BY t.go_id, t.go_term_name, t.go_aspect, t.go_namespace,
                            t.annotation_count, t.reference_count
                 )
            SELECT * FROM terms {keyset}
            ORDER BY go_aspect, lower(go_term_name), go_id
            LIMIT ?
            """, [*term_parameters, *(after or []), limit + 1],
        ).fetchall()
        page = rows[:limit]
        items = [
            GoTermSummary(
                go_id=row[0], go_term_name=row[1], aspect=row[2], go_namespace=row[3],
                annotation_count=int(row[4]), reference_count=int(row[5]),
                evidence_codes=[GoEvidenceCodeCount(**item) for item in row[6]],
            )
            for row in page
        ]
        next_cursor = None
        if len(rows) > limit and page:
            last = page[-1]
            next_cursor = encode_go_cursor(
                "terms", filters, [str(last[2]), str(last[1]).lower(), str(last[0])],
            )
        aspect_map = {
            str(row[0]): (int(row[1]), int(row[2]), int(row[3]))
            for row in aspect_rows
        }
        return GoTermsResponse(
            uniprot_accession=accession,
            provenance=goa_provenance(),
            items=items,
            next_cursor=next_cursor,
            total_or_estimate=ExactTotal(value=int(total_row[0])),
            annotation_count=int(total_row[1]),
            aspect_counts=[
                GoAspectCount(
                    aspect=aspect_key,
                    term_count=aspect_map.get(aspect_key, (0, 0, 0))[0],
                    annotation_count=aspect_map.get(aspect_key, (0, 0, 0))[1],
                    reference_count=aspect_map.get(aspect_key, (0, 0, 0))[2],
                )
                for aspect_key in ("MF", "BP", "CC")
            ],
            applied_filters={**filters, "default_excludes_negated": not include_negated},
        )

    @app.get(
        "/api/v1/proteins/{acc}/go/terms/{go_id}/evidence",
        response_model=GoEvidenceResponse,
    )
    def go_term_evidence(
        acc: str,
        go_id: str,
        evidence_code: str | None = Query(default=None, max_length=40),
        include_negated: bool = Query(default=False),
        limit: int = Query(default=20, ge=1, le=50),
        cursor: str | None = Query(default=None),
        connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    ) -> GoEvidenceResponse:
        overview = require_protein(connection, acc)
        accession = str(overview["uniprot_accession"])
        normalized_go_id = go_id.strip().upper()
        normalized_code = evidence_code.strip().upper() if evidence_code and evidence_code.strip() else None
        filters: dict[str, object] = {
            "go_id": normalized_go_id,
            "evidence_code": normalized_code,
            "include_negated": include_negated,
            "limit": limit,
        }
        after_id: int | None = None
        if cursor is not None:
            after = decode_go_cursor(cursor, "evidence", filters)
            if len(after) != 1 or not isinstance(after[0], int) or after[0] < 0:
                raise HTTPException(status_code=400, detail="Invalid GO evidence cursor")
            after_id = after[0]
        where = "e.uniprot_accession = ? AND e.go_id = ?"
        parameters: list[object] = [accession, normalized_go_id]
        if not include_negated:
            where += " AND coalesce(e.is_negated, false) = false"
        if normalized_code is not None:
            where += " AND e.evidence_code = ?"
            parameters.append(normalized_code)
        total = int(connection.execute(
            f"SELECT count(*) FROM go_evidence e WHERE {where}", parameters,
        ).fetchone()[0])
        if after_id is not None:
            where += " AND e.go_evidence_id > ?"
            parameters.append(after_id)
        rows = connection.execute(
            f"""
            SELECT go_evidence_id, go_id, go_term_name, go_aspect, go_namespace, qualifier,
                   is_negated, evidence_code, reference_id, with_from, assigned_by,
                   annotation_extension, annotation_date
            FROM go_evidence e WHERE {where}
            ORDER BY go_evidence_id LIMIT ?
            """, [*parameters, limit + 1],
        ).fetchall()
        page = rows[:limit]
        items = [
            GoEvidenceItem(
                go_evidence_id=int(row[0]), go_id=row[1], go_term_name=row[2], aspect=row[3],
                go_namespace=row[4], qualifier=row[5], is_negated=row[6], evidence_code=row[7],
                reference_id=row[8], with_from=row[9], assigned_by=row[10],
                annotation_extension=row[11], annotation_date=row[12],
            )
            for row in page
        ]
        next_cursor = (
            encode_go_cursor("evidence", filters, [int(page[-1][0])])
            if len(rows) > limit and page else None
        )
        return GoEvidenceResponse(
            uniprot_accession=accession, go_id=normalized_go_id, items=items,
            next_cursor=next_cursor, total_or_estimate=ExactTotal(value=total),
            applied_filters={**filters, "default_excludes_negated": not include_negated},
        )

    @app.get("/api/v1/proteins/{acc}/annotations", response_model=AnnotationResponse)
    def annotations(
        acc: str,
        section: Literal["go", "reactome", "location"] | None = Query(default=None),
        cursor: str | None = Query(default=None),
        connection: duckdb.DuckDBPyConnection = Depends(get_connection),
    ) -> AnnotationResponse:
        overview = require_protein(connection, acc)
        accession = str(overview["uniprot_accession"])
        offset = decode_cursor(cursor, section) if cursor else 0
        items = annotation_items(connection, accession, section)
        page = items[offset: offset + ANNOTATION_PAGE_SIZE]
        next_cursor = (
            encode_cursor(section, offset + ANNOTATION_PAGE_SIZE)
            if offset + ANNOTATION_PAGE_SIZE < len(items)
            else None
        )
        return AnnotationResponse(
            uniprot_accession=accession, section=section, items=page, next_cursor=next_cursor,
            total_or_estimate=ExactTotal(value=len(items)),
            applied_filters={"section": section, "page_size": ANNOTATION_PAGE_SIZE},
        )

    return app


app = create_app()
