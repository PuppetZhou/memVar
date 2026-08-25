#!/usr/bin/env python3
"""Build the M1 read-only protein core mart from immutable View Parquet files.

Only the generated DuckDB file is written, and its output root must stay under
website/data/generated.  The build is intentionally limited to M1 search,
overview, canonical sequence, and compact basic annotation data.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import uuid

import duckdb


WEBSITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WEBSITE_ROOT.parent
DEFAULT_VIEW_ROOT = PROJECT_ROOT / "View"
DEFAULT_OUTPUT_ROOT = WEBSITE_ROOT / "data" / "generated"

SOURCE_COLUMNS: dict[str, set[str]] = {
    "Basic_info/protein_basic.parquet": {
        "uniprot_accession", "entry_name", "protein_name", "gene_symbol",
        "canonical_length", "protein_existence", "annotation_score",
        "membrane_class", "all_class_labels", "transmembrane_count",
        "intramembrane_count", "lipidation_count", "lipidation_anchor_match_count",
    },
    "Basic_info/protein_gene_name.parquet": {
        "uniprot_accession", "gene_name", "gene_name_type",
    },
    "Basic_info/gene_identifier_bridge.parquet": {
        "uniprot_accession", "identifier_database", "identifier_full",
        "identifier_base", "identifier_version",
    },
    "Basic_info/transcript_identifier_bridge.parquet": {
        "uniprot_accession", "isoform_id", "database", "transcript_id_full",
        "transcript_id_base", "transcript_id_version", "protein_id_full",
        "protein_id_base", "protein_id_version", "gene_id_full", "gene_id_base",
        "gene_id_version",
    },
    "Basic_info/protein_isoform.parquet": {
        "uniprot_accession", "isoform_id", "isoform_id_aliases", "isoform_name",
        "isoform_synonyms", "is_canonical",
    },
    "Basic_info/protein_sequence.parquet": {
        "sequence_id", "uniprot_accession", "is_canonical", "length", "sequence",
        "parent_canonical_sequence_version",
    },
    "Annotation/go_mf_bp_cc_membrane.parquet": {
        "uniprot_accession", "MF (Molecular Function)", "BP (Biological Process)",
        "CC (Cellular Component)",
    },
    "Annotation/go_annotation.parquet": {
        "uniprot_accession", "go_id", "go_term_name", "go_aspect", "go_namespace",
        "relation_qualifier", "is_negated", "evidence_code", "reference_id", "with_from",
        "assigned_by", "annotation_extension", "annotation_date",
    },
    "Annotation/reactome_pathway_membership.parquet": {
        "uniprot_accession", "pathway_id", "pathway_name", "pathway_url",
        "evidence_codes", "evidence_count",
    },
    "Annotation/reactome_pathway_hierarchy.parquet": {
        "parent_pathway_id", "child_pathway_id",
    },
    "Annotation/uniprot_subcellular_location.parquet": {
        "uniprot_accession", "sequence_version", "location_id", "location_name",
        "topology_id", "topology_name", "orientation_id", "orientation_name",
    },
}


def path_is_within(path: Path, parent: Path) -> bool:
    """Return whether path is parent itself or one of its descendants."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def fail(message: str) -> None:
    raise RuntimeError(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--view-root",
        type=Path,
        default=DEFAULT_VIEW_ROOT,
        help=f"Immutable source directory (default: {DEFAULT_VIEW_ROOT})",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=f"Generated-data directory (default: {DEFAULT_OUTPUT_ROOT})",
    )
    return parser.parse_args()


def validate_paths(view_root: Path, output_root: Path) -> tuple[Path, Path]:
    view_root = view_root.resolve()
    output_root = output_root.resolve()
    allowed_output_root = DEFAULT_OUTPUT_ROOT.resolve()

    if not view_root.is_dir():
        fail(f"View root does not exist or is not a directory: {view_root}")
    if output_root == view_root or path_is_within(output_root, view_root):
        fail(f"Refusing output in immutable View tree: {output_root}")
    if not path_is_within(output_root, allowed_output_root):
        fail(
            "Output root must be website/data/generated or one of its descendants: "
            f"{output_root}"
        )
    return view_root, output_root


def validate_source_schema(connection: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    for relative_path, expected_columns in SOURCE_COLUMNS.items():
        source_path = view_root / relative_path
        if not source_path.is_file():
            fail(f"Required source file is missing: {source_path}")
        columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE SELECT * FROM read_parquet(?)", [str(source_path)]
            ).fetchall()
        }
        missing = sorted(expected_columns - columns)
        if missing:
            fail(f"{source_path} is missing required columns: {', '.join(missing)}")


def parquet_path(view_root: Path, relative_path: str) -> str:
    """Return a SQL-safe parameter value for a validated source path."""
    return str(view_root / relative_path)


def create_go_evidence(connection: duckdb.DuckDBPyConnection, source_path: str) -> None:
    """Materialise source-grain GO annotations for bounded term drill-down."""
    connection.execute(
        """
        CREATE TABLE go_evidence AS
        SELECT
            row_number() OVER (
                ORDER BY g.uniprot_accession, g.go_aspect, g.go_id, g.go_term_name,
                         g.relation_qualifier NULLS FIRST, g.is_negated NULLS FIRST,
                         g.evidence_code NULLS FIRST, g.reference_id NULLS FIRST,
                         g.with_from NULLS FIRST, g.assigned_by NULLS FIRST,
                         g.annotation_extension NULLS FIRST, g.annotation_date NULLS FIRST
            ) AS go_evidence_id,
            g.uniprot_accession,
            g.go_id,
            g.go_term_name,
            g.go_aspect,
            g.go_namespace,
            g.relation_qualifier AS qualifier,
            g.is_negated,
            g.evidence_code,
            g.reference_id,
            g.with_from,
            g.assigned_by,
            g.annotation_extension,
            g.annotation_date
        FROM read_parquet(?) g
        JOIN protein_overview o USING (uniprot_accession)
        """,
        [source_path],
    )


def create_tables(connection: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    basic = parquet_path(view_root, "Basic_info/protein_basic.parquet")
    gene_names = parquet_path(view_root, "Basic_info/protein_gene_name.parquet")
    gene_bridge = parquet_path(view_root, "Basic_info/gene_identifier_bridge.parquet")
    transcript_bridge = parquet_path(view_root, "Basic_info/transcript_identifier_bridge.parquet")
    isoforms = parquet_path(view_root, "Basic_info/protein_isoform.parquet")
    sequences = parquet_path(view_root, "Basic_info/protein_sequence.parquet")
    go_compact = parquet_path(view_root, "Annotation/go_mf_bp_cc_membrane.parquet")
    go_annotation = parquet_path(view_root, "Annotation/go_annotation.parquet")
    reactome = parquet_path(view_root, "Annotation/reactome_pathway_membership.parquet")
    reactome_hierarchy = parquet_path(view_root, "Annotation/reactome_pathway_hierarchy.parquet")
    locations = parquet_path(view_root, "Annotation/uniprot_subcellular_location.parquet")

    connection.execute(
        """
        CREATE TABLE protein_overview AS
        SELECT
            uniprot_accession,
            entry_name,
            protein_name,
            gene_symbol,
            canonical_length,
            protein_existence,
            annotation_score,
            membrane_class,
            all_class_labels,
            transmembrane_count,
            intramembrane_count,
            lipidation_count,
            lipidation_anchor_match_count
        FROM read_parquet(?)
        """,
        [basic],
    )

    connection.execute(
        """
        CREATE TEMP TABLE search_raw AS
        WITH overview_labels AS (
            SELECT
                uniprot_accession,
                concat_ws(' · ', gene_symbol, protein_name, uniprot_accession) AS display_label
            FROM protein_overview
        )
        SELECT
            o.uniprot_accession AS uniprot_accession,
            o.uniprot_accession AS search_text,
            'uniprot_accession' AS identifier_type,
            'UniProt' AS identifier_database,
            o.display_label AS display_label,
            100 AS match_priority
        FROM overview_labels o

        UNION ALL

        SELECT
            o.uniprot_accession,
            p.entry_name,
            'entry_name',
            'UniProt',
            o.display_label,
            80
        FROM read_parquet(?) p
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            p.protein_name,
            'protein_name',
            'UniProt',
            o.display_label,
            20
        FROM read_parquet(?) p
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            g.gene_name,
            CASE WHEN lower(g.gene_name_type) = 'primary' THEN 'gene_primary' ELSE 'gene_synonym' END,
            'UniProt',
            o.display_label,
            CASE WHEN lower(g.gene_name_type) = 'primary' THEN 80 ELSE 70 END
        FROM read_parquet(?) g
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            g.identifier_full,
            'gene_stable_id',
            g.identifier_database,
            o.display_label,
            90
        FROM read_parquet(?) g
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            g.identifier_base,
            'gene_stable_id',
            g.identifier_database,
            o.display_label,
            90
        FROM read_parquet(?) g
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            t.transcript_id_full,
            'transcript_id',
            t.database,
            o.display_label,
            90
        FROM read_parquet(?) t
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            t.transcript_id_base,
            'transcript_id',
            t.database,
            o.display_label,
            90
        FROM read_parquet(?) t
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            t.protein_id_full,
            'protein_id',
            t.database,
            o.display_label,
            90
        FROM read_parquet(?) t
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            t.protein_id_base,
            'protein_id',
            t.database,
            o.display_label,
            90
        FROM read_parquet(?) t
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            t.gene_id_full,
            'gene_stable_id',
            t.database,
            o.display_label,
            90
        FROM read_parquet(?) t
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            t.gene_id_base,
            'gene_stable_id',
            t.database,
            o.display_label,
            90
        FROM read_parquet(?) t
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            i.isoform_id,
            'isoform_id',
            'UniProt',
            o.display_label,
            95
        FROM read_parquet(?) i
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            i.isoform_id_aliases,
            'isoform_alias',
            'UniProt',
            o.display_label,
            95
        FROM read_parquet(?) i
        JOIN overview_labels o USING (uniprot_accession)

        UNION ALL

        SELECT
            o.uniprot_accession,
            trim(synonym),
            'isoform_synonym',
            'UniProt',
            o.display_label,
            65
        FROM read_parquet(?) i
        CROSS JOIN UNNEST(string_split(i.isoform_synonyms, '|')) AS t(synonym)
        JOIN overview_labels o USING (uniprot_accession)
        """,
        [basic, basic, gene_names, gene_bridge, gene_bridge, transcript_bridge,
         transcript_bridge, transcript_bridge, transcript_bridge, transcript_bridge,
         transcript_bridge, isoforms, isoforms, isoforms],
    )

    connection.execute(
        """
        CREATE TABLE protein_search_index AS
        WITH normalized AS (
            SELECT
                search_text,
                upper(trim(search_text)) AS normalized_text,
                identifier_type,
                identifier_database,
                uniprot_accession,
                display_label,
                match_priority
            FROM search_raw
            WHERE search_text IS NOT NULL AND trim(search_text) <> ''
        ),
        ranked AS (
            SELECT *,
                row_number() OVER (
                    PARTITION BY normalized_text, uniprot_accession
                    ORDER BY match_priority DESC, identifier_type, identifier_database, search_text
                ) AS match_rank
            FROM normalized
        )
        SELECT
            search_text,
            normalized_text,
            identifier_type,
            identifier_database,
            uniprot_accession,
            display_label,
            match_priority
        FROM ranked
        WHERE match_rank = 1
        """
    )

    connection.execute(
        """
        CREATE TABLE protein_identifier AS
        SELECT
            o.uniprot_accession,
            NULL::VARCHAR AS isoform_id,
            'uniprot_accession' AS identifier_type,
            'UniProt' AS identifier_database,
            o.uniprot_accession AS identifier_full,
            o.uniprot_accession AS identifier_base,
            NULL::BIGINT AS identifier_version,
            NULL::VARCHAR AS alias_type,
            NULL::VARCHAR AS identifier_label
        FROM protein_overview o

        UNION ALL

        SELECT
            o.uniprot_accession,
            NULL::VARCHAR,
            'entry_name',
            'UniProt',
            o.entry_name,
            o.entry_name,
            NULL::BIGINT,
            NULL::VARCHAR,
            NULL::VARCHAR
        FROM protein_overview o

        UNION ALL

        SELECT
            g.uniprot_accession,
            NULL::VARCHAR,
            CASE WHEN lower(g.gene_name_type) = 'primary' THEN 'gene_primary' ELSE 'gene_synonym' END,
            'UniProt',
            g.gene_name,
            g.gene_name,
            NULL::BIGINT,
            g.gene_name_type,
            NULL::VARCHAR
        FROM read_parquet(?) g
        JOIN protein_overview o USING (uniprot_accession)

        UNION ALL

        SELECT
            g.uniprot_accession,
            NULL::VARCHAR,
            'gene_stable_id',
            g.identifier_database,
            g.identifier_full,
            g.identifier_base,
            CAST(g.identifier_version AS BIGINT),
            NULL::VARCHAR,
            NULL::VARCHAR
        FROM read_parquet(?) g
        JOIN protein_overview o USING (uniprot_accession)

        UNION ALL

        SELECT
            t.uniprot_accession,
            t.isoform_id,
            'transcript_id',
            t.database,
            t.transcript_id_full,
            t.transcript_id_base,
            t.transcript_id_version,
            NULL::VARCHAR,
            NULL::VARCHAR
        FROM read_parquet(?) t
        JOIN protein_overview o USING (uniprot_accession)
        WHERE t.transcript_id_full IS NOT NULL

        UNION ALL

        SELECT
            t.uniprot_accession,
            t.isoform_id,
            'protein_id',
            t.database,
            t.protein_id_full,
            t.protein_id_base,
            t.protein_id_version,
            NULL::VARCHAR,
            NULL::VARCHAR
        FROM read_parquet(?) t
        JOIN protein_overview o USING (uniprot_accession)
        WHERE t.protein_id_full IS NOT NULL

        UNION ALL

        SELECT
            t.uniprot_accession,
            t.isoform_id,
            'gene_stable_id',
            t.database,
            t.gene_id_full,
            t.gene_id_base,
            CAST(t.gene_id_version AS BIGINT),
            NULL::VARCHAR,
            NULL::VARCHAR
        FROM read_parquet(?) t
        JOIN protein_overview o USING (uniprot_accession)
        WHERE t.gene_id_full IS NOT NULL

        UNION ALL

        SELECT
            i.uniprot_accession,
            i.isoform_id,
            'isoform_id',
            'UniProt',
            i.isoform_id,
            i.isoform_id,
            NULL::BIGINT,
            NULL::VARCHAR,
            i.isoform_name
        FROM read_parquet(?) i
        JOIN protein_overview o USING (uniprot_accession)

        UNION ALL

        SELECT
            i.uniprot_accession,
            i.isoform_id,
            'isoform_alias',
            'UniProt',
            i.isoform_id_aliases,
            i.isoform_id_aliases,
            NULL::BIGINT,
            'isoform_id_alias',
            NULL::VARCHAR
        FROM read_parquet(?) i
        JOIN protein_overview o USING (uniprot_accession)
        WHERE i.isoform_id_aliases IS NOT NULL

        UNION ALL

        SELECT
            i.uniprot_accession,
            i.isoform_id,
            'isoform_synonym',
            'UniProt',
            trim(synonym),
            trim(synonym),
            NULL::BIGINT,
            'isoform_synonym',
            NULL::VARCHAR
        FROM read_parquet(?) i
        CROSS JOIN UNNEST(string_split(i.isoform_synonyms, '|')) AS t(synonym)
        JOIN protein_overview o USING (uniprot_accession)
        WHERE trim(synonym) <> ''
        """,
        [gene_names, gene_bridge, transcript_bridge, transcript_bridge, transcript_bridge,
         isoforms, isoforms, isoforms],
    )

    connection.execute(
        """
        CREATE TABLE protein_sequence AS
        SELECT
            s.sequence_id,
            s.uniprot_accession,
            s.is_canonical,
            s.length,
            s.sequence,
            s.parent_canonical_sequence_version
        FROM read_parquet(?) s
        JOIN protein_overview o USING (uniprot_accession)
        WHERE s.is_canonical = true
        """,
        [sequences],
    )

    connection.execute(
        """
        CREATE TABLE go_summary AS
        SELECT
            g.uniprot_accession,
            g."MF (Molecular Function)" AS go_molecular_function,
            g."BP (Biological Process)" AS go_biological_process,
            g."CC (Cellular Component)" AS go_cellular_component
        FROM read_parquet(?) g
        JOIN protein_overview o USING (uniprot_accession)
        """,
        [go_compact],
    )

    create_go_evidence(connection, go_annotation)

    connection.execute(
        """
        CREATE TABLE reactome_membership AS
        SELECT
            r.uniprot_accession,
            r.pathway_id,
            r.pathway_name,
            r.pathway_url,
            r.evidence_codes,
            r.evidence_count
        FROM read_parquet(?) r
        JOIN protein_overview o USING (uniprot_accession)
        """,
        [reactome],
    )

    connection.execute(
        """
        CREATE TABLE reactome_hierarchy_edge AS
        SELECT parent_pathway_id, child_pathway_id
        FROM read_parquet(?)
        """,
        [reactome_hierarchy],
    )

    connection.execute(
        """
        CREATE TABLE subcellular_location AS
        SELECT
            l.uniprot_accession,
            l.sequence_version,
            l.location_id,
            l.location_name,
            l.topology_id,
            l.topology_name,
            l.orientation_id,
            l.orientation_name
        FROM read_parquet(?) l
        JOIN protein_overview o USING (uniprot_accession)
        """,
        [locations],
    )


def scalar(connection: duckdb.DuckDBPyConnection, query: str) -> int:
    return int(connection.execute(query).fetchone()[0])


def validate_output(connection: duckdb.DuckDBPyConnection) -> None:
    expected_tables = {
        "protein_search_index",
        "protein_overview",
        "protein_identifier",
        "protein_sequence",
        "go_evidence",
        "go_summary",
        "reactome_hierarchy_edge",
        "reactome_membership",
        "subcellular_location",
    }
    actual_tables = {row[0] for row in connection.execute("SHOW TABLES").fetchall()}
    missing_tables = expected_tables - actual_tables
    if missing_tables:
        fail(f"Generated core is missing tables: {', '.join(sorted(missing_tables))}")

    overview_count = scalar(connection, "SELECT count(*) FROM protein_overview")
    overview_distinct = scalar(
        connection, "SELECT count(DISTINCT uniprot_accession) FROM protein_overview"
    )
    if overview_count == 0 or overview_count != overview_distinct:
        fail("protein_overview must contain one non-empty row per canonical accession")

    invalid_sequences = scalar(
        connection,
        """
        SELECT count(*)
        FROM (
            SELECT uniprot_accession
            FROM protein_sequence
            GROUP BY uniprot_accession
            HAVING count(*) <> 1 OR bool_and(is_canonical) = false
        )
        """,
    )
    if invalid_sequences:
        fail("Each overview protein must have exactly one canonical protein_sequence row")
    if scalar(connection, "SELECT count(*) FROM protein_sequence") != overview_count:
        fail("Canonical protein_sequence coverage does not match protein_overview")

    go_evidence_count = scalar(connection, "SELECT count(*) FROM go_evidence")
    if go_evidence_count == 0:
        fail("go_evidence must not be empty")
    invalid_go_identity = scalar(
        connection,
        """
        SELECT count(*) FROM go_evidence
        WHERE go_id IS NULL OR NOT regexp_full_match(go_id, 'GO:[0-9]{7}')
           OR go_term_name IS NULL OR trim(go_term_name) = ''
           OR go_aspect NOT IN ('MF', 'BP', 'CC')
        """,
    )
    if invalid_go_identity:
        fail("go_evidence contains an invalid GO ID, term name, or aspect")
    orphan_go_evidence = scalar(
        connection,
        """
        SELECT count(*) FROM go_evidence e
        LEFT JOIN protein_overview o USING (uniprot_accession)
        WHERE o.uniprot_accession IS NULL
        """,
    )
    if orphan_go_evidence:
        fail("go_evidence contains accessions outside protein_overview")

    unmapped_search_rows = scalar(
        connection,
        """
        SELECT count(*)
        FROM protein_search_index s
        LEFT JOIN protein_overview o USING (uniprot_accession)
        WHERE o.uniprot_accession IS NULL
        """,
    )
    if unmapped_search_rows:
        fail("protein_search_index contains accessions outside protein_overview")

    cardinality_changes = scalar(
        connection,
        """
        WITH raw_counts AS (
            SELECT upper(trim(search_text)) AS normalized_text,
                   count(DISTINCT uniprot_accession) AS accession_count
            FROM search_raw
            WHERE search_text IS NOT NULL AND trim(search_text) <> ''
            GROUP BY 1
        ), output_counts AS (
            SELECT normalized_text, count(DISTINCT uniprot_accession) AS accession_count
            FROM protein_search_index
            GROUP BY 1
        )
        SELECT count(*)
        FROM raw_counts r
        LEFT JOIN output_counts o USING (normalized_text)
        WHERE o.accession_count IS NULL OR r.accession_count <> o.accession_count
        """,
    )
    if cardinality_changes:
        fail("Search build collapsed or changed one-to-many accession mappings")

    hierarchy_edge_count = scalar(connection, "SELECT count(*) FROM reactome_hierarchy_edge")
    if hierarchy_edge_count == 0:
        fail("reactome_hierarchy_edge must not be empty")
    invalid_hierarchy_edges = scalar(
        connection,
        """
        SELECT count(*)
        FROM reactome_hierarchy_edge
        WHERE parent_pathway_id IS NULL
           OR child_pathway_id IS NULL
           OR parent_pathway_id = child_pathway_id
        """,
    )
    if invalid_hierarchy_edges:
        fail("Reactome hierarchy edges must have non-null, distinct parent and child IDs")
    distinct_hierarchy_edges = scalar(
        connection,
        """
        SELECT count(*)
        FROM (
            SELECT parent_pathway_id, child_pathway_id
            FROM reactome_hierarchy_edge
            GROUP BY parent_pathway_id, child_pathway_id
        )
        """,
    )
    if hierarchy_edge_count != distinct_hierarchy_edges:
        fail("reactome_hierarchy_edge must contain unique direct parent-child edges")


def build(view_root: Path, output_root: Path) -> Path:
    view_root, output_root = validate_paths(view_root, output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / "memvar_core.duckdb"
    temporary = output_root / f".memvar_core.{uuid.uuid4().hex}.duckdb"

    connection = duckdb.connect(str(temporary))
    try:
        validate_source_schema(connection, view_root)
        create_tables(connection, view_root)
        validate_output(connection)
        connection.execute("CHECKPOINT")
    except Exception:
        connection.close()
        temporary.unlink(missing_ok=True)
        raise
    else:
        connection.close()

    os.replace(temporary, target)
    return target


def main() -> int:
    args = parse_args()
    try:
        target = build(args.view_root, args.output_root)
    except (RuntimeError, duckdb.Error, OSError) as error:
        print(f"build_core failed: {error}", file=sys.stderr)
        return 1
    print(f"Built M1 core data mart: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
