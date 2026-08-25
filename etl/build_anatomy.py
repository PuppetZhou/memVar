#!/usr/bin/env python3
"""Build protein-scoped anatomy availability summaries from website marts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

import duckdb

from build_core import DEFAULT_OUTPUT_ROOT, fail, path_is_within


WEBSITE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = WEBSITE_ROOT / "config" / "anatomy_crosswalk.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser.parse_args()


def normalize_sql(column: str) -> str:
    return f"trim(regexp_replace(lower(replace(replace({column}, '_', ' '), '-', ' ')), '\\s+', ' ', 'g'))"


def sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def build(input_root: Path, target: Path, config_path: Path) -> int:
    m3 = input_root / "memvar_m3.duckdb"
    de = input_root / "differential_expression" / "memvar_de.duckdb"
    if not m3.is_file() or not de.is_file():
        fail("M3 and differential-expression marts are required before anatomy build")
    payload = json.loads(config_path.read_text())
    rows = []
    for mapping in payload["mappings"]:
        for alias in mapping["aliases"]:
            rows.append((str(alias), str(mapping["body_region_id"]), mapping.get("ontology_id")))
    connection = duckdb.connect()
    try:
        connection.execute(f"ATTACH '{sql_path(m3)}' AS m3 (READ_ONLY)")
        connection.execute(f"ATTACH '{sql_path(de)}' AS de (READ_ONLY)")
        connection.execute("CREATE TEMP TABLE crosswalk(raw_alias VARCHAR, body_region_id VARCHAR, ontology_id VARCHAR)")
        connection.executemany("INSERT INTO crosswalk VALUES (?, ?, ?)", rows)
        connection.execute(f"""
            CREATE TEMP TABLE normalized_crosswalk AS
            SELECT DISTINCT {normalize_sql('raw_alias')} AS normalized_term,
                   body_region_id, ontology_id
            FROM crosswalk
        """)
        conflicts = connection.execute(
            "SELECT count(*) FROM (SELECT normalized_term FROM normalized_crosswalk GROUP BY normalized_term HAVING count(*) > 1)"
        ).fetchone()[0]
        if conflicts:
            fail("Anatomy crosswalk has conflicting normalized aliases")
        connection.execute("""
            CREATE TEMP TABLE evidence AS
            SELECT uniprot_accession, 'expression' AS layer, source_database,
                   modality_or_type, raw_term, count(*)::BIGINT AS record_count
            FROM (
              SELECT uniprot_accession, source_database, 'hpa_rna' AS modality_or_type, tissue AS raw_term FROM m3.expression_hpa_rna
              UNION ALL SELECT uniprot_accession, source_database, 'hpa_ms', tissue FROM m3.expression_hpa_ms
              UNION ALL SELECT uniprot_accession, source_database, 'hpa_ihc', tissue FROM m3.expression_hpa_ihc
              UNION ALL SELECT uniprot_accession, source_database, 'paxdb', organ FROM m3.expression_paxdb
            ) GROUP BY uniprot_accession, source_database, modality_or_type, raw_term;

            INSERT INTO evidence
            SELECT uniprot_accession, 'qtl', source_database, qtl_type,
                   tissue_or_context, sum(record_count)::BIGINT
            FROM m3.qtl_summary
            GROUP BY uniprot_accession, source_database, qtl_type, tissue_or_context;

            INSERT INTO evidence
            SELECT p.uniprot_accession, 'gen', 'GEN', 'qualifying_contrast', c.tissue,
                   count(DISTINCT c.contrast_id)::BIGINT
            FROM de.protein_contrast p JOIN de.contrast c USING (dataset_id, contrast_id)
            WHERE p.is_significant_with_effect = TRUE
            GROUP BY p.uniprot_accession, c.tissue;
        """)
        target.parent.mkdir(parents=True, exist_ok=True)
        connection.execute(f"""
            COPY (
              WITH mapped AS (
                SELECT e.*, coalesce(c.body_region_id, 'other') AS body_region_id,
                       c.ontology_id,
                       c.body_region_id IS NOT NULL AS is_explicit
                FROM evidence e LEFT JOIN normalized_crosswalk c
                  ON c.normalized_term = {normalize_sql('e.raw_term')}
              )
              SELECT uniprot_accession, body_region_id, any_value(ontology_id) AS ontology_id,
                     layer, source_database, modality_or_type,
                     sum(record_count)::BIGINT AS record_count,
                     count(DISTINCT raw_term)::BIGINT AS distinct_context_count,
                     list(DISTINCT raw_term ORDER BY lower(raw_term), raw_term)
                       FILTER (WHERE raw_term IS NOT NULL) AS raw_filter_terms,
                     CASE WHEN bool_and(is_explicit) THEN 'explicit' ELSE 'unmapped_other' END AS mapping_status
              FROM mapped
              GROUP BY uniprot_accession, body_region_id, layer, source_database, modality_or_type
              ORDER BY uniprot_accession, body_region_id, layer, source_database, modality_or_type
            ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 50000)
        """, [str(target)])
        return int(connection.execute("SELECT count(*) FROM read_parquet(?)", [str(target)]).fetchone()[0])
    finally:
        connection.close()


def main() -> int:
    args = parse_args()
    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    allowed = DEFAULT_OUTPUT_ROOT.resolve()
    if not input_root.is_dir():
        fail(f"Generated input root is missing: {input_root}")
    if not path_is_within(output_root, allowed):
        fail(f"Output must stay under {allowed}: {output_root}")
    temporary = output_root / f".anatomy-build-{uuid.uuid4().hex}"
    temporary.mkdir()
    try:
        count = build(input_root, temporary / "anatomy_summary.parquet", args.config.resolve())
        destination = output_root / "anatomy"
        if destination.exists():
            shutil.rmtree(destination)
        os.replace(temporary, destination)
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError, duckdb.Error) as error:
        if temporary.exists():
            shutil.rmtree(temporary)
        print(f"build_anatomy failed: {error}", file=sys.stderr)
        return 1
    print(f"anatomy_summary_rows: {count:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
