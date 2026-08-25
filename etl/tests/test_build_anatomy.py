from __future__ import annotations

import json
from pathlib import Path
import re

import duckdb


ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "data" / "generated"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold().replace("_", " ").replace("-", " ")).strip()


def test_current_release_tissue_terms_are_explicitly_routed() -> None:
    payload = json.loads((ROOT / "config" / "anatomy_crosswalk.json").read_text())
    aliases: dict[str, str] = {}
    for mapping in payload["mappings"]:
        for alias in mapping["aliases"]:
            key = normalize(alias)
            assert key not in aliases or aliases[key] == mapping["body_region_id"]
            aliases[key] = mapping["body_region_id"]

    connection = duckdb.connect()
    connection.execute(f"ATTACH '{GENERATED / 'memvar_m3.duckdb'}' AS m3 (READ_ONLY)")
    connection.execute(
        f"ATTACH '{GENERATED / 'differential_expression' / 'memvar_de.duckdb'}' AS de (READ_ONLY)"
    )
    rows = connection.execute(
        """
        SELECT DISTINCT raw_term FROM (
          SELECT tissue AS raw_term FROM m3.expression_hpa_rna
          UNION ALL SELECT tissue FROM m3.expression_hpa_ms
          UNION ALL SELECT tissue FROM m3.expression_hpa_ihc
          UNION ALL SELECT organ FROM m3.expression_paxdb
          UNION ALL SELECT tissue_or_context FROM m3.qtl_summary
          UNION ALL SELECT c.tissue
            FROM de.protein_contrast p JOIN de.contrast c USING (dataset_id, contrast_id)
            WHERE p.is_significant_with_effect = TRUE
        ) WHERE raw_term IS NOT NULL
        """
    ).fetchall()
    missing = sorted(row[0] for row in rows if normalize(row[0]) not in aliases)
    assert missing == []


def test_generated_anatomy_keeps_gen_as_an_independent_layer() -> None:
    connection = duckdb.connect()
    path = GENERATED / "anatomy" / "anatomy_summary.parquet"
    rows = connection.execute(
        """
        SELECT body_region_id, raw_filter_terms
        FROM read_parquet(?)
        WHERE uniprot_accession = 'P00533' AND layer = 'gen'
        ORDER BY body_region_id
        """,
        [str(path)],
    ).fetchall()
    assert rows
    assert {row[0] for row in rows} >= {"blood", "heart", "kidney", "skin"}
    assert all(row[1] for row in rows)
