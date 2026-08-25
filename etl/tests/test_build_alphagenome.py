import json
from pathlib import Path
import sys

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build_alphagenome import (  # noqa: E402
    CONTACT_SCHEMA,
    JUNCTION_SCHEMA,
    SIGNAL_SCHEMA,
    resume_bundle_counts,
)


ROOT = Path(__file__).resolve().parents[2] / "data" / "generated" / "alphagenome"


def test_catalog_conserves_source_and_protein_coverage() -> None:
    connection = duckdb.connect(str(ROOT / "alphagenome_catalog.duckdb"), read_only=True)
    try:
        assert connection.execute("SELECT count(*) FROM gene").fetchone()[0] == 7637
        assert connection.execute("SELECT count(*) FROM tile").fetchone()[0] == 7746
        assert connection.execute("SELECT count(*) FROM track").fetchone()[0] == 492
        assert connection.execute(
            "SELECT count(DISTINCT uniprot_accession) FROM protein_gene_coverage"
        ).fetchone()[0] == 7728
        assert connection.execute(
            "SELECT count(DISTINCT uniprot_accession) FROM protein_gene_coverage WHERE has_prediction"
        ).fetchone()[0] == 7430
        assert connection.execute(
            "SELECT count(DISTINCT uniprot_accession) FROM protein_gene_coverage WHERE mapping_status = 'ambiguous'"
        ).fetchone()[0] == 28
        assert connection.execute("SELECT count(*) FROM prepared_tile").fetchone()[0] >= 1
    finally:
        connection.close()


def test_egfr_display_bundles_are_bounded_and_complete() -> None:
    connection = duckdb.connect(str(ROOT / "alphagenome_catalog.duckdb"), read_only=True)
    try:
        row = connection.execute(
            "SELECT signal_relative_path, junction_relative_path, contact_relative_path FROM prepared_tile WHERE ensembl_gene_id = 'ENSG00000146648' AND tile_id = 'tile_000'"
        ).fetchone()
        assert row is not None
        signal = ROOT / row[0]
        levels = connection.execute(
            "SELECT level_bins, count(*), min(value_count), max(value_count) FROM read_parquet(?) GROUP BY 1 ORDER BY 1",
            [str(signal)],
        ).fetchall()
        assert levels == [(256, 429, 256, 256), (1024, 429, 1024, 1024), (4096, 429, 4096, 4096)]
        sample = connection.execute(
            "SELECT value_count, octet_length(mean_float16_le), octet_length(max_float16_le) FROM read_parquet(?) WHERE track_id = 'rna_seq:000' AND level_bins = 1024",
            [str(signal)],
        ).fetchone()
        assert sample == (1024, 2048, 2048)
        assert connection.execute("SELECT count(*) FROM read_parquet(?)", [str(ROOT / row[1])]).fetchone()[0] <= 61 * 200
        assert connection.execute("SELECT count(*), min(matrix_size), max(matrix_size) FROM read_parquet(?)", [str(ROOT / row[2])]).fetchone() == (2, 128, 128)
    finally:
        connection.close()


def test_build_manifest_never_exposes_source_path() -> None:
    manifest = json.loads((ROOT / "build_manifest.json").read_text())
    assert manifest["prediction_kind"] == "reference_sequence_tracks"
    assert manifest["local_output_subset"] is True
    assert manifest["missing_official_modalities"] == ["dnase", "chip_tf"]
    assert manifest["pyramid_bins"] == [256, 1024, 4096]
    assert "/media/" not in json.dumps(manifest)


def test_resume_requires_three_valid_parquet_bundles(tmp_path: Path) -> None:
    relative_paths = [Path("tracks/G/tile.parquet"), Path("junctions/G/tile.parquet"), Path("contacts/G/tile.parquet")]
    for relative_path, schema in zip(relative_paths, (SIGNAL_SCHEMA, JUNCTION_SCHEMA, CONTACT_SCHEMA), strict=True):
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(pa.Table.from_pylist([], schema=schema), path)

    assert resume_bundle_counts(
        tmp_path, *relative_paths, expected_signal_rows=0, expected_contact_rows=0,
    ) == (0, 0, 0)

    (tmp_path / relative_paths[2]).write_text("interrupted")
    assert resume_bundle_counts(
        tmp_path, *relative_paths, expected_signal_rows=0, expected_contact_rows=0,
    ) is None
