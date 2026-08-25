#!/usr/bin/env python3
"""Build the M15 ThermoMPNN variant branch and canonical site summaries.

The immutable prediction release is copied into accession buckets without
changing its record grain.  Sequence summaries are restricted to predictions
whose Ref/Alt/position identity also has a drawable canonical M2 effect.
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

from build_core import DEFAULT_OUTPUT_ROOT, fail, path_is_within
from build_m2 import bucket_sql


DEFAULT_SOURCE_ROOT = Path("/home/xuyzh/memVar/MPNN-predict/result")
PREDICTIONS = "thermompnn_variant_predictions.parquet"
TARGETS = "variant_targets.parquet"
STANDARD_AA = tuple("ACDEFGHIKLMNPQRSTVWY")
MODEL_NAME = "ThermoMPNN"
UNIT = "kcal/mol"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--accession", action="append", default=[],
        help="Build only this accession; repeat for a staged slice.",
    )
    parser.add_argument("--threads", type=int, default=max(1, min(8, os.cpu_count() or 1)))
    return parser.parse_args()


def validate_paths(source_root: Path, output_root: Path) -> tuple[Path, Path]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    allowed = DEFAULT_OUTPUT_ROOT.resolve()
    if not source_root.is_dir():
        fail(f"ThermoMPNN source root does not exist: {source_root}")
    if output_root == source_root or path_is_within(output_root, source_root):
        fail(f"Refusing output in immutable ThermoMPNN tree: {output_root}")
    if not path_is_within(output_root, allowed):
        fail(f"Output must stay under {allowed}: {output_root}")
    return source_root, output_root


def required_columns(
    con: duckdb.DuckDBPyConnection, path: Path, required: set[str]
) -> None:
    if not path.is_file():
        fail(f"Required ThermoMPNN source is missing: {path}")
    actual = {
        row[0]
        for row in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]).fetchall()
    }
    missing = sorted(required - actual)
    if missing:
        fail(f"{path} is missing required columns: {', '.join(missing)}")


def sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def accession_clause(accessions: list[str], alias: str) -> str:
    if not accessions:
        return "TRUE"
    values = ", ".join("'" + item.replace("'", "''") + "'" for item in accessions)
    return f"{alias}.uniprot_accession IN ({values})"


def copy_partitioned(con: duckdb.DuckDBPyConnection, query: str, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    con.execute(
        f"COPY ({query}) TO '{sql_path(target)}' "
        "(FORMAT PARQUET, PARTITION_BY (accession_bucket), COMPRESSION ZSTD, "
        "ROW_GROUP_SIZE 100000)"
    )


def parquet_count(con: duckdb.DuckDBPyConnection, root: Path) -> int:
    if not list(root.glob("accession_bucket=*/*.parquet")):
        return 0
    return int(con.execute(
        "SELECT count(*) FROM read_parquet(?, hive_partitioning=true)",
        [str(root / "**" / "*.parquet")],
    ).fetchone()[0])


def build(
    con: duckdb.DuckDBPyConnection,
    source_root: Path,
    staging_root: Path,
    membership_root: Path,
    accessions: list[str],
) -> dict[str, int]:
    prediction_path = source_root / PREDICTIONS
    target_path = source_root / TARGETS
    required_columns(
        con, prediction_path,
        {"variant_key", "uniprot_accession", "pdb_name", "ddg_pred"},
    )
    required_columns(
        con, target_path,
        {"variant_key", "uniprot_accession", "canonical_position", "ref_aa", "alt_aa", "pdb_name"},
    )
    prediction = sql_path(prediction_path)
    target = sql_path(target_path)
    scope = accession_clause(accessions, "p")
    con.execute(f"""
        CREATE TEMP TABLE thermompnn_joined AS
        SELECT p.variant_key, p.uniprot_accession, p.pdb_name,
               CAST(p.ddg_pred AS DOUBLE) AS ddg_pred,
               CAST(t.canonical_position AS BIGINT) AS canonical_position,
               t.ref_aa, t.alt_aa
        FROM read_parquet('{prediction}') p
        JOIN read_parquet('{target}') t
          ON p.variant_key = t.variant_key
         AND p.uniprot_accession = t.uniprot_accession
         AND p.pdb_name = t.pdb_name
        WHERE {scope}
    """)
    prediction_count = int(con.execute(
        f"SELECT count(*) FROM read_parquet('{prediction}') p WHERE {scope}"
    ).fetchone()[0])
    joined_count = int(con.execute("SELECT count(*) FROM thermompnn_joined").fetchone()[0])
    if joined_count != prediction_count:
        fail(
            "ThermoMPNN predictions do not join one-to-one to variant targets: "
            f"predictions={prediction_count:,}, joined={joined_count:,}"
        )
    invalid = con.execute(
        """
        SELECT
          count(*) FILTER (WHERE variant_key IS NULL OR trim(variant_key) = ''),
          count(*) FILTER (WHERE uniprot_accession IS NULL OR trim(uniprot_accession) = ''),
          count(*) FILTER (WHERE pdb_name IS NULL OR trim(pdb_name) = ''),
          count(*) FILTER (WHERE ddg_pred IS NULL OR NOT isfinite(ddg_pred)),
          count(*) FILTER (WHERE canonical_position < 1 OR canonical_position IS NULL),
          count(*) FILTER (WHERE ref_aa NOT IN (SELECT unnest(?)) OR alt_aa NOT IN (SELECT unnest(?)) OR ref_aa = alt_aa)
        FROM thermompnn_joined
        """,
        [list(STANDARD_AA), list(STANDARD_AA)],
    ).fetchone()
    if any(invalid):
        fail(f"ThermoMPNN input contract failed: invalid_counts={tuple(int(x) for x in invalid)}")
    duplicates = int(con.execute(
        """
        SELECT count(*) FROM (
          SELECT variant_key, uniprot_accession, count(*) AS n
          FROM thermompnn_joined GROUP BY variant_key, uniprot_accession HAVING n <> 1
        )
        """
    ).fetchone()[0])
    if duplicates:
        fail("ThermoMPNN variant_key + uniprot_accession identity is not unique")

    effect_glob = membership_root / "variant" / "effect" / "**" / "*.parquet"
    if not list((membership_root / "variant" / "effect").glob("accession_bucket=*/*.parquet")):
        fail("M2 variant-effect data is required before the M15 build")
    effect = sql_path(effect_glob)
    con.execute(f"""
        CREATE TEMP TABLE canonical_membership AS
        SELECT DISTINCT variant_key, uniprot_accession,
          CAST(protein_start AS BIGINT) AS canonical_position, ref_aa, alt_aa,
          bool_or(is_drawable) AS is_sequence_drawable
        FROM read_parquet('{effect}', hive_partitioning=true)
        WHERE effect_scope = 'canonical'
        GROUP BY variant_key, uniprot_accession, protein_start, ref_aa, alt_aa
    """)
    missing_membership = int(con.execute(
        """
        SELECT count(*) FROM thermompnn_joined t
        WHERE NOT EXISTS (
          SELECT 1 FROM canonical_membership m
          WHERE m.variant_key = t.variant_key
            AND m.uniprot_accession = t.uniprot_accession
        )
        """
    ).fetchone()[0])
    if missing_membership:
        fail(f"ThermoMPNN rows without same-accession canonical membership: {missing_membership:,}")

    branch_query = f"""
        SELECT t.uniprot_accession AS page_accession,
          {bucket_sql('t.uniprot_accession')} AS accession_bucket,
          t.variant_key, t.canonical_position, t.ref_aa, t.alt_aa,
          CAST(t.ddg_pred AS FLOAT) AS ddg_pred,
          '{UNIT}'::VARCHAR AS unit, t.pdb_name,
          '{MODEL_NAME}'::VARCHAR AS model_name
        FROM thermompnn_joined t
        ORDER BY accession_bucket, page_accession, variant_key
    """
    copy_partitioned(
        con, branch_query,
        staging_root / "variant" / "source" / "thermompnn",
    )

    site_query = f"""
        WITH drawable AS (
          SELECT t.*
          FROM thermompnn_joined t
          JOIN canonical_membership m
            ON m.variant_key = t.variant_key
           AND m.uniprot_accession = t.uniprot_accession
           AND m.canonical_position = t.canonical_position
           AND m.ref_aa = t.ref_aa AND m.alt_aa = t.alt_aa
          WHERE m.is_sequence_drawable
        ), substitution AS (
          SELECT uniprot_accession, canonical_position, ref_aa, alt_aa,
                 avg(ddg_pred) AS ddg_pred,
                 count(*) AS genomic_variant_count
          FROM drawable
          GROUP BY uniprot_accession, canonical_position, ref_aa, alt_aa
        )
        SELECT uniprot_accession,
          {bucket_sql('uniprot_accession')} AS accession_bucket,
          canonical_position, any_value(ref_aa) AS ref_aa,
          count(*) AS distinct_substitution_count,
          sum(genomic_variant_count)::BIGINT AS genomic_variant_count,
          min(ddg_pred) AS ddg_min,
          quantile_cont(ddg_pred, 0.25) AS ddg_q25,
          median(ddg_pred) AS ddg_median,
          quantile_cont(ddg_pred, 0.75) AS ddg_q75,
          max(ddg_pred) AS ddg_max,
          count(*) FILTER (WHERE ddg_pred <= -0.5) AS stabilizing_count,
          count(*) FILTER (WHERE ddg_pred > -0.5 AND ddg_pred < 0.5) AS small_change_count,
          count(*) FILTER (WHERE ddg_pred >= 0.5) AS destabilizing_count
        FROM substitution
        GROUP BY uniprot_accession, canonical_position
        ORDER BY accession_bucket, uniprot_accession, canonical_position
    """
    copy_partitioned(con, site_query, staging_root / "sequence" / "stability_site")

    branch_count = parquet_count(con, staging_root / "variant" / "source" / "thermompnn")
    site_count = parquet_count(con, staging_root / "sequence" / "stability_site")
    if branch_count != prediction_count:
        fail(f"ThermoMPNN branch count changed: {branch_count:,} != {prediction_count:,}")
    return {
        "predictions": branch_count,
        "sequence_sites": site_count,
        "non_drawable_predictions": branch_count - int(con.execute(
            """
            SELECT count(*) FROM thermompnn_joined t
            WHERE EXISTS (
              SELECT 1 FROM canonical_membership m
              WHERE m.variant_key=t.variant_key AND m.uniprot_accession=t.uniprot_accession
                AND m.canonical_position=t.canonical_position
                AND m.ref_aa=t.ref_aa AND m.alt_aa=t.alt_aa AND m.is_sequence_drawable
            )
            """
        ).fetchone()[0]),
    }


def install(temp: Path, output_root: Path) -> None:
    targets = (
        (temp / "variant" / "source" / "thermompnn", output_root / "variant" / "source" / "thermompnn"),
        (temp / "sequence" / "stability_site", output_root / "sequence" / "stability_site"),
    )
    for source, destination in targets:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        os.replace(source, destination)


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    temporary: Path | None = None
    con: duckdb.DuckDBPyConnection | None = None
    try:
        source_root, output_root = validate_paths(args.source_root, args.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        accessions = sorted({item.strip().upper() for item in args.accession if item.strip()})
        temporary = output_root / f".m15-build-{uuid.uuid4().hex}"
        temporary.mkdir()
        con = duckdb.connect()
        con.execute(f"SET threads={args.threads}")
        counts = build(con, source_root, temporary, output_root, accessions)
        # Membership is website-owned M2 data and is deliberately not copied.
        install(temporary, output_root)
        shutil.rmtree(temporary)
        temporary = None
    except (RuntimeError, OSError, ValueError, duckdb.Error) as error:
        print(f"build_thermompnn failed: {error}", file=sys.stderr)
        return 1
    finally:
        if con is not None:
            con.close()
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)
    print(f"Built ThermoMPNN scope: {','.join(accessions) if accessions else 'all'}")
    for name, count in counts.items():
        print(f"{name}: {count:,}")
    print(f"elapsed_seconds: {time.monotonic() - started:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
