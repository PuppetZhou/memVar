#!/usr/bin/env python3
"""Build M3 expression and protein-scoped QTL data from immutable View.

Expression is stored as four source-specific tables in ``memvar_m3.duckdb``.
QTL summaries are stored in the same database, while source-specific detail
records are written as ZSTD Parquet under source/type/accession buckets.  Use
one or more ``--accession`` options for a staged build, or omit them for the
full reviewed-protein set.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import time
import uuid

import duckdb

from build_core import DEFAULT_OUTPUT_ROOT, DEFAULT_VIEW_ROOT, fail, path_is_within
from build_m2 import bucket_sql


QTLBASE_TYPES = (
    "apaQTL", "bQTL", "caQTL", "cerQTL", "circQTL", "eQTL", "eaQTL",
    "edQTL", "hQTL", "lncRNAQTL", "m6AQTL", "mQTL", "metaQTL", "miQTL",
    "pQTL", "pieQTL", "puQTL", "riboQTL", "sQTL", "stQTL", "tuQTL",
    "vQTL",
)

SOURCES: dict[str, set[str]] = {
    "Basic_info/protein_basic.parquet": {"uniprot_accession"},
    "Basic_info/gene_identifier_bridge.parquet": {
        "uniprot_accession", "identifier_database", "identifier_base",
    },
    "Expression/hpa_rna_tissue.parquet": {
        "ensembl_gene_id", "gene_symbol", "tissue", "normalized_expression_ntpm",
    },
    "Expression/hpa_ms.parquet": {
        "ensembl_gene_id", "gene_symbol", "tissue", "protein_intensity",
    },
    "Expression/hpa_ihc.parquet": {
        "ensembl_gene_id", "gene_symbol", "tissue", "ihc_tissue_name",
        "cell_type", "staining_level", "reliability",
    },
    "Expression/paxdb_protein_abundance.parquet": {
        "paxdb_dataset_id", "paxdb_dataset_name", "organ", "string_external_id",
        "source_gene_name", "uniprot_accession", "abundance_ppm",
    },
    "QTLs/gtex_gene_protein_bridge.parquet": {
        "source_ensembl_gene_id", "gene_symbol", "uniprot_accession",
        "release_ensembl_gene_id",
    },
    "QTLs/qtlbase_gene_protein_bridge.parquet": {
        "gene_symbol", "uniprot_accession", "ensembl_gene_id", "gene_name_type",
    },
    "QTLs/eqtlgen_cis_eqtl.parquet": {
        "qtl_type", "ensembl_gene_id", "gene_symbol", "variant_rs_id",
        "variant_chromosome", "variant_position", "genome_build",
        "assessed_allele", "other_allele", "p_value", "z_score", "fdr",
        "bonferroni_p_value", "sample_size", "cohort_count",
    },
}

GTEX_COLUMNS = {
    "qtl_type", "ensembl_gene_id", "gene_symbol", "phenotype_id", "group_id",
    "variant_id", "genome_build", "distance_to_phenotype_start_bp",
    "alt_allele_frequency", "minor_allele_sample_count", "minor_allele_count",
    "p_value_nominal", "effect_slope", "effect_standard_error",
    "p_value_nominal_threshold", "tissue",
}

QTLBASE_COLUMNS = {
    "qtl_type", "gene_symbol", "variant_chromosome", "variant_position_grch38",
    "genome_build", "tissue", "population", "p_value", "trait_chromosome",
    "trait_start_grch38", "trait_end_grch38", "sample_size_raw",
    "sample_size_numeric", "publication_id", "source_id", "source_genome_build",
    "assay_context",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view-root", type=Path, default=DEFAULT_VIEW_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--accession", action="append", default=[],
        help="Build only this accession; repeat for a multi-protein staged build.",
    )
    parser.add_argument("--threads", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    return parser.parse_args()


def validate_paths(view_root: Path, output_root: Path) -> tuple[Path, Path]:
    view_root = view_root.resolve()
    output_root = output_root.resolve()
    allowed = DEFAULT_OUTPUT_ROOT.resolve()
    if not view_root.is_dir():
        fail(f"View root does not exist: {view_root}")
    if output_root == view_root or path_is_within(output_root, view_root):
        fail(f"Refusing output in immutable View tree: {output_root}")
    if not path_is_within(output_root, allowed):
        fail(f"Output must stay under {allowed}: {output_root}")
    return view_root, output_root


def sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def source(view_root: Path, relative: str) -> str:
    return sql_path(view_root / relative)


def actual_columns(con: duckdb.DuckDBPyConnection, path: Path) -> set[str]:
    return {
        row[0]
        for row in con.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]
        ).fetchall()
    }


def validate_sources(con: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    expected_qtlbase = {f"qtlbase_{name}.parquet" for name in QTLBASE_TYPES}
    actual_qtlbase = {path.name for path in (view_root / "QTLs" / "qtlbase").glob("*.parquet")}
    if actual_qtlbase != expected_qtlbase:
        missing = sorted(expected_qtlbase - actual_qtlbase)
        extra = sorted(actual_qtlbase - expected_qtlbase)
        fail(f"QTLbase type contract changed; missing={missing}, extra={extra}")

    for relative, required in SOURCES.items():
        path = view_root / relative
        if not path.is_file():
            fail(f"Required source file is missing: {path}")
        missing = sorted(required - actual_columns(con, path))
        if missing:
            fail(f"{path} is missing required columns: {', '.join(missing)}")

    for kind in ("eqtl", "sqtl", "apaqtl"):
        path = view_root / "QTLs" / "gtex" / f"gtex_v11_{kind}_significant_pairs.parquet"
        if not path.is_file():
            fail(f"Required GTEx source is missing: {path}")
        missing = sorted(GTEX_COLUMNS - actual_columns(con, path))
        if missing:
            fail(f"{path} is missing required columns: {', '.join(missing)}")

    for qtl_type in QTLBASE_TYPES:
        path = view_root / "QTLs" / "qtlbase" / f"qtlbase_{qtl_type}.parquet"
        missing = sorted(QTLBASE_COLUMNS - actual_columns(con, path))
        if missing:
            fail(f"{path} is missing required columns: {', '.join(missing)}")


def accession_predicate(accessions: list[str], alias: str = "") -> str:
    if not accessions:
        return "TRUE"
    prefix = f"{alias}." if alias else ""
    values = ", ".join("'" + value.replace("'", "''") + "'" for value in accessions)
    return f"{prefix}uniprot_accession IN ({values})"


def create_scope(
    con: duckdb.DuckDBPyConnection, view_root: Path, accessions: list[str]
) -> None:
    basic = source(view_root, "Basic_info/protein_basic.parquet")
    con.execute(
        f"CREATE TEMP TABLE protein_scope AS "
        f"SELECT uniprot_accession FROM read_parquet('{basic}') "
        f"WHERE {accession_predicate(accessions)}"
    )
    found = {row[0] for row in con.execute("SELECT uniprot_accession FROM protein_scope").fetchall()}
    if not found:
        fail("No requested accession exists in protein_basic")
    missing = sorted(set(accessions) - found)
    if missing:
        fail(f"Unknown accession(s): {', '.join(missing)}")


def create_bridges(con: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    gene = source(view_root, "Basic_info/gene_identifier_bridge.parquet")
    gtex = source(view_root, "QTLs/gtex_gene_protein_bridge.parquet")
    qtlbase = source(view_root, "QTLs/qtlbase_gene_protein_bridge.parquet")
    con.execute(f"""
        CREATE TEMP TABLE ensembl_protein_bridge AS
        SELECT DISTINCT g.identifier_base AS ensembl_gene_id, g.uniprot_accession
        FROM read_parquet('{gene}') g
        JOIN protein_scope s USING (uniprot_accession)
        WHERE lower(g.identifier_database) = 'ensembl'
          AND g.identifier_base IS NOT NULL;

        CREATE TEMP TABLE gtex_protein_bridge AS
        SELECT g.source_ensembl_gene_id, g.gene_symbol, g.uniprot_accession,
          list(DISTINCT g.release_ensembl_gene_id ORDER BY g.release_ensembl_gene_id)
            FILTER (WHERE g.release_ensembl_gene_id IS NOT NULL)
            AS release_ensembl_gene_ids
        FROM read_parquet('{gtex}') g
        JOIN protein_scope s USING (uniprot_accession)
        GROUP BY g.source_ensembl_gene_id, g.gene_symbol, g.uniprot_accession;

        CREATE TEMP TABLE qtlbase_protein_bridge AS
        SELECT q.gene_symbol, q.uniprot_accession,
          list(DISTINCT q.ensembl_gene_id ORDER BY q.ensembl_gene_id)
            FILTER (WHERE q.ensembl_gene_id IS NOT NULL) AS ensembl_gene_ids,
          list(DISTINCT q.gene_name_type ORDER BY q.gene_name_type)
            FILTER (WHERE q.gene_name_type IS NOT NULL) AS gene_name_types
        FROM read_parquet('{qtlbase}') q
        JOIN protein_scope s USING (uniprot_accession)
        GROUP BY q.gene_symbol, q.uniprot_accession;
    """)


def assert_complete_mapping(con: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    """Fail if a source stable ID has no legal release accession mapping."""
    hpa_sources = (
        "Expression/hpa_rna_tissue.parquet",
        "Expression/hpa_ms.parquet",
        "Expression/hpa_ihc.parquet",
    )
    if con.execute("SELECT count(*) FROM protein_scope").fetchone()[0] == 7728:
        for relative in hpa_sources:
            path = source(view_root, relative)
            missing = con.execute(f"""
                SELECT count(*) FROM read_parquet('{path}') x
                WHERE NOT EXISTS (
                  SELECT 1 FROM ensembl_protein_bridge b
                  WHERE b.ensembl_gene_id = x.ensembl_gene_id
                )
            """).fetchone()[0]
            if missing:
                fail(f"{relative} contains {missing:,} rows without an accession mapping")

        eqtlgen = source(view_root, "QTLs/eqtlgen_cis_eqtl.parquet")
        missing = con.execute(f"""
            SELECT count(*) FROM read_parquet('{eqtlgen}') x
            WHERE NOT EXISTS (
              SELECT 1 FROM ensembl_protein_bridge b
              WHERE b.ensembl_gene_id = x.ensembl_gene_id
            )
        """).fetchone()[0]
        if missing:
            fail(f"eQTLGen contains {missing:,} rows without an accession mapping")

        paxdb = source(view_root, "Expression/paxdb_protein_abundance.parquet")
        missing = con.execute(f"""
            SELECT count(*) FROM read_parquet('{paxdb}') x
            WHERE NOT EXISTS (
              SELECT 1 FROM protein_scope s
              WHERE s.uniprot_accession = x.uniprot_accession
            )
        """).fetchone()[0]
        if missing:
            fail(f"PaxDB contains {missing:,} rows without a reviewed accession mapping")

        for kind in ("eqtl", "sqtl", "apaqtl"):
            path = source(
                view_root,
                f"QTLs/gtex/gtex_v11_{kind}_significant_pairs.parquet",
            )
            missing = con.execute(f"""
                SELECT count(*) FROM read_parquet('{path}') x
                WHERE NOT EXISTS (
                  SELECT 1 FROM gtex_protein_bridge b
                  WHERE b.source_ensembl_gene_id = x.ensembl_gene_id
                    AND b.gene_symbol = x.gene_symbol
                )
            """).fetchone()[0]
            if missing:
                fail(f"GTEx {kind} contains {missing:,} rows without a bridge mapping")

        for qtl_type in QTLBASE_TYPES:
            path = source(
                view_root, f"QTLs/qtlbase/qtlbase_{qtl_type}.parquet"
            )
            missing = con.execute(f"""
                SELECT count(*) FROM read_parquet('{path}') x
                WHERE NOT EXISTS (
                  SELECT 1 FROM qtlbase_protein_bridge b
                  WHERE b.gene_symbol = x.gene_symbol
                )
            """).fetchone()[0]
            if missing:
                fail(
                    f"QTLbase {qtl_type} contains {missing:,} rows without a bridge mapping"
                )


def build_expression(con: duckdb.DuckDBPyConnection, view_root: Path) -> None:
    rna = source(view_root, "Expression/hpa_rna_tissue.parquet")
    ms = source(view_root, "Expression/hpa_ms.parquet")
    ihc = source(view_root, "Expression/hpa_ihc.parquet")
    paxdb = source(view_root, "Expression/paxdb_protein_abundance.parquet")

    con.execute(f"""
        CREATE TABLE expression_hpa_rna AS
        SELECT b.uniprot_accession, x.*, 'HPA RNA'::VARCHAR AS modality,
          'nTPM'::VARCHAR AS unit, 'HPA'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release
        FROM read_parquet('{rna}') x
        JOIN ensembl_protein_bridge b USING (ensembl_gene_id)
        ORDER BY b.uniprot_accession, x.tissue, x.ensembl_gene_id;

        CREATE TABLE expression_hpa_ms AS
        SELECT b.uniprot_accession, x.*, 'HPA MS'::VARCHAR AS modality,
          'source intensity'::VARCHAR AS unit, 'HPA'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release
        FROM read_parquet('{ms}') x
        JOIN ensembl_protein_bridge b USING (ensembl_gene_id)
        ORDER BY b.uniprot_accession, x.tissue, x.ensembl_gene_id;

        CREATE TABLE expression_hpa_ihc AS
        SELECT b.uniprot_accession, x.*, 'HPA IHC'::VARCHAR AS modality,
          'categorical staining'::VARCHAR AS unit, 'HPA'::VARCHAR AS source_database,
          'not_recorded'::VARCHAR AS source_release
        FROM read_parquet('{ihc}') x
        JOIN ensembl_protein_bridge b USING (ensembl_gene_id)
        ORDER BY b.uniprot_accession, x.tissue, x.ihc_tissue_name,
          x.cell_type, x.ensembl_gene_id;

        CREATE TABLE expression_paxdb AS
        SELECT x.*, 'PaxDB protein abundance'::VARCHAR AS modality,
          'ppm'::VARCHAR AS unit, 'PaxDB'::VARCHAR AS source_database,
          'v6.1'::VARCHAR AS source_release
        FROM read_parquet('{paxdb}') x
        JOIN protein_scope s USING (uniprot_accession)
        ORDER BY x.uniprot_accession, x.organ, x.paxdb_dataset_id,
          x.string_external_id;
    """)


def copy_partitioned(
    con: duckdb.DuckDBPyConnection, query: str, target: Path
) -> None:
    target.mkdir(parents=True, exist_ok=False)
    con.execute(
        f"COPY ({query}) TO '{sql_path(target)}' "
        "(FORMAT PARQUET, PARTITION_BY (accession_bucket), COMPRESSION ZSTD, "
        "ROW_GROUP_SIZE 100000)"
    )


def create_summary_staging(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("""
        CREATE TEMP TABLE qtl_summary_staging (
          uniprot_accession VARCHAR,
          source_database VARCHAR,
          qtl_type VARCHAR,
          tissue_or_context VARCHAR,
          population VARCHAR,
          record_count BIGINT,
          distinct_variant_or_locus_count BIGINT
        )
    """)


def build_gtex(
    con: duckdb.DuckDBPyConnection, view_root: Path, root: Path
) -> None:
    kinds = (("eqtl", "eQTL"), ("sqtl", "sQTL"), ("apaqtl", "apaQTL"))
    for filename_kind, qtl_type in kinds:
        path = source(
            view_root,
            f"QTLs/gtex/gtex_v11_{filename_kind}_significant_pairs.parquet",
        )
        relation = f"""
            SELECT b.uniprot_accession, b.release_ensembl_gene_ids, x.*,
              'GTEx'::VARCHAR AS source_database,
              'v11'::VARCHAR AS source_release,
              'official significant pair'::VARCHAR AS evidence_semantics,
              {bucket_sql('b.uniprot_accession')} AS accession_bucket
            FROM read_parquet('{path}') x
            JOIN gtex_protein_bridge b
              ON x.ensembl_gene_id = b.source_ensembl_gene_id
             AND x.gene_symbol = b.gene_symbol
        """
        copy_partitioned(
            con,
            relation + " ORDER BY accession_bucket, b.uniprot_accession, "
            "x.tissue, x.variant_id, x.phenotype_id",
            root / "qtl" / "source=GTEx" / f"type={qtl_type}",
        )
        con.execute(f"""
            INSERT INTO qtl_summary_staging
            SELECT b.uniprot_accession, 'GTEx', x.qtl_type, x.tissue, NULL,
              count(*), count(DISTINCT x.variant_id)
            FROM read_parquet('{path}') x
            JOIN gtex_protein_bridge b
              ON x.ensembl_gene_id = b.source_ensembl_gene_id
             AND x.gene_symbol = b.gene_symbol
            GROUP BY b.uniprot_accession, x.qtl_type, x.tissue
        """)


def build_eqtlgen(
    con: duckdb.DuckDBPyConnection, view_root: Path, root: Path
) -> None:
    path = source(view_root, "QTLs/eqtlgen_cis_eqtl.parquet")
    relation = f"""
        SELECT b.uniprot_accession, x.*,
          'blood meta-analysis'::VARCHAR AS tissue_or_context,
          'eQTLGen'::VARCHAR AS source_database,
          '2019-12-11'::VARCHAR AS source_release,
          'official FDR < 0.05 cis-eQTL association'::VARCHAR AS evidence_semantics,
          {bucket_sql('b.uniprot_accession')} AS accession_bucket
        FROM read_parquet('{path}') x
        JOIN ensembl_protein_bridge b USING (ensembl_gene_id)
    """
    copy_partitioned(
        con,
        relation + " ORDER BY accession_bucket, b.uniprot_accession, "
        "x.variant_chromosome, x.variant_position, x.variant_rs_id",
        root / "qtl" / "source=eQTLGen" / "type=cis_eQTL",
    )
    con.execute(f"""
        INSERT INTO qtl_summary_staging
        SELECT b.uniprot_accession, 'eQTLGen', x.qtl_type,
          'blood meta-analysis', NULL, count(*), count(DISTINCT x.variant_rs_id)
        FROM read_parquet('{path}') x
        JOIN ensembl_protein_bridge b USING (ensembl_gene_id)
        GROUP BY b.uniprot_accession, x.qtl_type
    """)


def build_qtlbase(
    con: duckdb.DuckDBPyConnection, view_root: Path, root: Path
) -> None:
    for qtl_type in QTLBASE_TYPES:
        path = source(
            view_root, f"QTLs/qtlbase/qtlbase_{qtl_type}.parquet"
        )
        relation = f"""
            SELECT b.uniprot_accession, b.ensembl_gene_ids,
              b.gene_name_types, x.*,
              'QTLbase'::VARCHAR AS source_database,
              'v2'::VARCHAR AS source_release,
              'association'::VARCHAR AS evidence_semantics,
              {bucket_sql('b.uniprot_accession')} AS accession_bucket
            FROM read_parquet('{path}') x
            JOIN qtlbase_protein_bridge b USING (gene_symbol)
        """
        copy_partitioned(
            con,
            relation + " ORDER BY accession_bucket, b.uniprot_accession, "
            "x.tissue, x.population, x.variant_chromosome, "
            "x.variant_position_grch38, x.p_value NULLS LAST",
            root / "qtl" / "source=QTLbase" / f"type={qtl_type}",
        )
        con.execute(f"""
            INSERT INTO qtl_summary_staging
            SELECT b.uniprot_accession, 'QTLbase', x.qtl_type,
              coalesce(x.tissue, x.assay_context), x.population,
              count(*), count(DISTINCT (x.variant_chromosome, x.variant_position_grch38))
            FROM read_parquet('{path}') x
            JOIN qtlbase_protein_bridge b USING (gene_symbol)
            GROUP BY b.uniprot_accession, x.qtl_type,
              coalesce(x.tissue, x.assay_context), x.population
        """)


def finalize_database(
    con: duckdb.DuckDBPyConnection, accessions: list[str]
) -> None:
    scope = ",".join(accessions) if accessions else "all"
    con.execute(f"""
        CREATE TABLE qtl_summary AS
        SELECT uniprot_accession, source_database, qtl_type,
          tissue_or_context, population, sum(record_count)::BIGINT AS record_count,
          sum(distinct_variant_or_locus_count)::BIGINT AS distinct_variant_or_locus_count
        FROM qtl_summary_staging
        GROUP BY uniprot_accession, source_database, qtl_type,
          tissue_or_context, population
        ORDER BY uniprot_accession, source_database, qtl_type,
          tissue_or_context NULLS LAST, population NULLS LAST;

        CREATE TABLE qtl_source_semantics AS
        SELECT * FROM (VALUES
          ('GTEx', 'official significant pairs', 'GRCh38'),
          ('QTLbase', 'associations; not a uniform significant set', 'GRCh38'),
          ('eQTLGen', 'official FDR < 0.05 cis-eQTL associations', 'GRCh37')
        ) AS t(source_database, evidence_semantics, genome_build);

        CREATE TABLE build_scope AS
        SELECT '{scope.replace(chr(39), chr(39) * 2)}'::VARCHAR AS scope,
          128::INTEGER AS accession_bucket_count;
    """)
    con.execute("CHECKPOINT")


def parquet_glob(root: Path, source_name: str) -> str:
    return sql_path(root / "qtl" / f"source={source_name}" / "**" / "*.parquet")


def source_parquet_files(root: Path, source_name: str) -> list[Path]:
    return list((root / "qtl" / f"source={source_name}").glob("**/*.parquet"))


def validate_build(
    con: duckdb.DuckDBPyConnection, view_root: Path, root: Path
) -> dict[str, int]:
    expression_tables = (
        "expression_hpa_rna", "expression_hpa_ms", "expression_hpa_ihc",
        "expression_paxdb",
    )
    counts = {
        table: int(con.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        for table in expression_tables
    }
    if any(count == 0 for count in counts.values()):
        fail(f"Expression output is unexpectedly empty: {counts}")

    ms_path = sql_path(view_root / "Expression" / "hpa_ms.parquet")
    source_ms_null = con.execute(f"""
        SELECT count(*) FROM read_parquet('{ms_path}') x
        JOIN ensembl_protein_bridge b USING (ensembl_gene_id)
        WHERE x.protein_intensity IS NULL
    """).fetchone()[0]
    mapped_ms_null = con.execute(
        "SELECT count(*) FROM expression_hpa_ms WHERE protein_intensity IS NULL"
    ).fetchone()[0]
    if source_ms_null != mapped_ms_null:
        fail(
            "HPA MS NULL intensities were lost or converted: "
            f"expected {source_ms_null:,}, found {mapped_ms_null:,}"
        )

    expected_builds = {"GTEx": "GRCh38", "QTLbase": "GRCh38", "eQTLGen": "GRCh37"}
    expected_semantics = {
        "GTEx": "official significant pair",
        "QTLbase": "association",
        "eQTLGen": "official FDR < 0.05 cis-eQTL association",
    }
    full_scope = con.execute("SELECT count(*) FROM protein_scope").fetchone()[0] == 7728
    for name in ("GTEx", "QTLbase", "eQTLGen"):
        glob = parquet_glob(root, name)
        files = source_parquet_files(root, name)
        count = int(con.execute(
            f"SELECT count(*) FROM read_parquet('{glob}', hive_partitioning=true)"
        ).fetchone()[0]) if files else 0
        counts[f"qtl_{name}"] = count
        if full_scope and not count:
            fail(f"{name} QTL detail output is unexpectedly empty")
        if not files:
            continue
        bad = con.execute(f"""
            SELECT count(*) FROM read_parquet('{glob}', hive_partitioning=true)
            WHERE genome_build IS DISTINCT FROM ?
               OR evidence_semantics IS DISTINCT FROM ?
               OR accession_bucket < 0 OR accession_bucket >= 128
        """, [expected_builds[name], expected_semantics[name]]).fetchone()[0]
        if bad:
            fail(f"{name} output violates build, semantics, or bucket contract ({bad:,} rows)")

    eqtlgen_glob = parquet_glob(root, "eQTLGen")
    bad_fdr = con.execute(f"""
        SELECT count(*) FROM read_parquet('{eqtlgen_glob}', hive_partitioning=true)
        WHERE fdr IS NULL OR fdr >= 0.05
    """).fetchone()[0] if source_parquet_files(root, "eQTLGen") else 0
    if bad_fdr:
        fail(f"eQTLGen output violates official FDR < 0.05 selection ({bad_fdr:,} rows)")

    summary_total = {
        row[0]: int(row[1])
        for row in con.execute(
            "SELECT source_database, sum(record_count) FROM qtl_summary GROUP BY source_database"
        ).fetchall()
    }
    for name in ("GTEx", "QTLbase", "eQTLGen"):
        if summary_total.get(name, 0) != counts[f"qtl_{name}"]:
            fail(
                f"{name} summary/detail mismatch: "
                f"{summary_total.get(name, 0):,} vs {counts[f'qtl_{name}']:,}"
            )
    counts["qtl_summary"] = int(con.execute("SELECT count(*) FROM qtl_summary").fetchone()[0])
    return counts


def install_build(temp: Path, output_root: Path) -> None:
    """Install both M3 targets with rollback if either rename fails."""
    names = ("qtl", "memvar_m3.duckdb")
    backup = output_root / f".m3-backup-{uuid.uuid4().hex}"
    backup.mkdir()
    installed: list[str] = []
    moved_old: list[str] = []
    try:
        for name in names:
            destination = output_root / name
            if destination.exists():
                os.replace(destination, backup / name)
                moved_old.append(name)
        for name in names:
            os.replace(temp / name, output_root / name)
            installed.append(name)
    except OSError:
        for name in reversed(installed):
            destination = output_root / name
            if destination.is_dir():
                shutil.rmtree(destination)
            elif destination.exists():
                destination.unlink()
        for name in moved_old:
            if (backup / name).exists():
                os.replace(backup / name, output_root / name)
        raise
    finally:
        if backup.exists():
            shutil.rmtree(backup)
    temp.rmdir()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    con: duckdb.DuckDBPyConnection | None = None
    temp: Path | None = None
    try:
        view_root, output_root = validate_paths(args.view_root, args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        accessions = sorted(set(value.strip().upper() for value in args.accession if value.strip()))
        temp = output_root / f".m3-build-{uuid.uuid4().hex}"
        temp.mkdir()
        con = duckdb.connect(str(temp / "memvar_m3.duckdb"))
        con.execute(f"SET threads={args.threads}")
        con.execute(f"SET temp_directory='{sql_path(temp / 'duckdb-tmp')}'")
        validate_sources(con, view_root)
        create_scope(con, view_root, accessions)
        create_bridges(con, view_root)
        assert_complete_mapping(con, view_root)
        build_expression(con, view_root)
        create_summary_staging(con)
        build_gtex(con, view_root, temp)
        build_eqtlgen(con, view_root, temp)
        build_qtlbase(con, view_root, temp)
        finalize_database(con, accessions)
        counts = validate_build(con, view_root, temp)
        scope = ",".join(accessions) if accessions else "all"
        con.close()
        con = None
        install_build(temp, output_root)
        temp = None
    except (RuntimeError, OSError, ValueError, duckdb.Error) as error:
        print(f"build_m3 failed: {error}", file=sys.stderr)
        return 1
    finally:
        if con is not None:
            con.close()
        if temp is not None and temp.exists():
            shutil.rmtree(temp)

    elapsed = time.monotonic() - started
    print(f"Built M3 scope: {scope}")
    for name, count in counts.items():
        print(f"{name}: {count:,}")
    print(f"elapsed_seconds: {elapsed:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
