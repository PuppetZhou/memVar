from pathlib import Path

import duckdb
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2] / "data" / "generated" / "differential_expression"


def test_generated_de_assets_conserve_source_granularity() -> None:
    connection = duckdb.connect(str(ROOT / "memvar_de.duckdb"), read_only=True)
    try:
        assert connection.execute("SELECT count(*) FROM dataset").fetchone()[0] == 151
        assert connection.execute("SELECT count(DISTINCT dataset_id) FROM contrast").fetchone()[0] == 42
        assert connection.execute("SELECT count(*) FROM contrast").fetchone()[0] == 142
        assert connection.execute("SELECT count(*) FROM manifest").fetchone()[0] == 142
        assert connection.execute(
            "SELECT count(*) FROM manifest WHERE plotted_count + unplottable_count <> tested_count"
        ).fetchone()[0] == 0
    finally:
        connection.close()
    assert pq.read_table(ROOT / "manifest.parquet").num_rows == 142
    assert len(list((ROOT / "contrasts").glob("*.parquet"))) == 142


def test_exact_gene_symbol_mapping_preserves_one_to_many_accessions() -> None:
    connection = duckdb.connect(str(ROOT / "memvar_de.duckdb"), read_only=True)
    try:
        contrast_id = connection.execute(
            "SELECT contrast_id FROM protein_contrast WHERE gene_symbol = 'GNAS' LIMIT 1"
        ).fetchone()[0]
        accessions = connection.execute(
            "SELECT uniprot_accession FROM protein_contrast WHERE gene_symbol = 'GNAS' AND contrast_id = ? ORDER BY 1",
            [contrast_id],
        ).fetchall()
        assert accessions == [("P63092",), ("P84996",), ("Q5JWF2",)]
        assert connection.execute(
            "SELECT count(*) FROM protein_contrast WHERE is_significant_with_effect IS DISTINCT FROM TRUE"
        ).fetchone()[0] == 0
    finally:
        connection.close()


def test_same_accession_contrast_keeps_conflicting_ensembl_gene_rows() -> None:
    connection = duckdb.connect(str(ROOT / "memvar_de.duckdb"), read_only=True)
    try:
        rows = connection.execute(
            """
            SELECT ensembl_gene_id, de_direction
            FROM protein_contrast
            WHERE uniprot_accession = 'P19440'
              AND contrast_id = 'GEND000503_lusc_late_tumor_vs_adjacent'
            ORDER BY ensembl_gene_id
            """
        ).fetchall()
        assert rows == [("ENSG00000100031", "down"), ("ENSG00000286070", "up")]
    finally:
        connection.close()
