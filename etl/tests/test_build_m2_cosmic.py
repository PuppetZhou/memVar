from __future__ import annotations

from pathlib import Path
import sys

import duckdb


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_m2  # noqa: E402


def test_cosmic_fact_selection_deduplicates_only_complete_six_column_rows(
    tmp_path: Path,
) -> None:
    source = tmp_path / "cosmic.parquet"
    connection = duckdb.connect()
    connection.execute(
        """
        CREATE TABLE cosmic (
          variant_key VARCHAR, GENOME_SCREEN_SAMPLE_COUNT BIGINT,
          mondo_ids VARCHAR, disease_categories VARCHAR,
          CGC_TIER INTEGER, ONC_TSG VARCHAR
        )
        """
    )
    rows = [
        ("same", 2, "MONDO:1", "cancer", 1, "oncogene"),
        ("same", 2, "MONDO:1", "cancer", 1, "oncogene"),
        ("counts-differ", 1, "MONDO:1", "cancer", 2, "TSG, fusion"),
        ("counts-differ", 4, "MONDO:1", "cancer", 2, "TSG, fusion"),
    ]
    connection.executemany("INSERT INTO cosmic VALUES (?, ?, ?, ?, ?, ?)", rows)
    connection.execute(f"COPY cosmic TO '{source}' (FORMAT PARQUET)")

    facts = connection.execute(
        build_m2.cosmic_facts_sql(build_m2.sql_path(source))
        + " ORDER BY variant_key, GENOME_SCREEN_SAMPLE_COUNT"
    ).fetchall()

    assert facts == [
        ("counts-differ", 1, "MONDO:1", "cancer", 2, "TSG, fusion"),
        ("counts-differ", 4, "MONDO:1", "cancer", 2, "TSG, fusion"),
        ("same", 2, "MONDO:1", "cancer", 1, "oncogene"),
    ]
    assert {"CGC_TIER", "ONC_TSG"} <= build_m2.SOURCES[
        "Variant/cosmic_branch.parquet"
    ]
    connection.close()
