from __future__ import annotations

from pathlib import Path
import sys

import duckdb


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_thermompnn as MODULE  # noqa: E402


def write_parquet(connection: duckdb.DuckDBPyConnection, path: Path, query: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection.execute(f"COPY ({query}) TO ? (FORMAT PARQUET)", [str(path)])


def test_build_preserves_variant_grain_and_deduplicates_site_substitutions(tmp_path: Path) -> None:
    source = tmp_path / "source"
    membership = tmp_path / "membership"
    staging = tmp_path / "staging"
    source.mkdir()
    staging.mkdir()
    connection = duckdb.connect()
    write_parquet(
        connection,
        source / MODULE.PREDICTIONS,
        """
        SELECT * FROM (VALUES
          ('v1', 'P00533', 'AF-P00533-F1-model_v6.pdb.gz', -0.25::FLOAT),
          ('v2', 'P00533', 'AF-P00533-F1-model_v6.pdb.gz', -0.25::FLOAT),
          ('v3', 'P00533', 'AF-P00533-F1-model_v6.pdb.gz', 1.5::FLOAT)
        ) t(variant_key, uniprot_accession, pdb_name, ddg_pred)
        """,
    )
    write_parquet(
        connection,
        source / MODULE.TARGETS,
        """
        SELECT * FROM (VALUES
          ('v1', 'P00533', 338, 'N', 'H', 'AF-P00533-F1-model_v6.pdb.gz'),
          ('v2', 'P00533', 338, 'N', 'H', 'AF-P00533-F1-model_v6.pdb.gz'),
          ('v3', 'P00533', 338, 'N', 'K', 'AF-P00533-F1-model_v6.pdb.gz')
        ) t(variant_key, uniprot_accession, canonical_position, ref_aa, alt_aa, pdb_name)
        """,
    )
    write_parquet(
        connection,
        membership / "variant" / "effect" / "accession_bucket=0" / "part.parquet",
        """
        SELECT * FROM (VALUES
          ('v1', 'P00533', 'canonical', 338, 'N', 'H', true),
          ('v2', 'P00533', 'canonical', 338, 'N', 'H', true),
          ('v3', 'P00533', 'canonical', 338, 'N', 'K', true)
        ) t(variant_key, uniprot_accession, effect_scope, protein_start, ref_aa, alt_aa, is_drawable)
        """,
    )

    counts = MODULE.build(connection, source, staging, membership, ["P00533"])
    assert counts == {"predictions": 3, "sequence_sites": 1, "non_drawable_predictions": 0}
    branch = connection.execute(
        "SELECT variant_key, page_accession, unit, model_name FROM read_parquet(?, hive_partitioning=true) ORDER BY variant_key",
        [str(staging / "variant/source/thermompnn/**/*.parquet")],
    ).fetchall()
    assert branch == [
        ("v1", "P00533", "kcal/mol", "ThermoMPNN"),
        ("v2", "P00533", "kcal/mol", "ThermoMPNN"),
        ("v3", "P00533", "kcal/mol", "ThermoMPNN"),
    ]
    site = connection.execute(
        """
        SELECT distinct_substitution_count, genomic_variant_count,
               ddg_min, ddg_median, ddg_max,
               stabilizing_count, small_change_count, destabilizing_count
        FROM read_parquet(?, hive_partitioning=true)
        """,
        [str(staging / "sequence/stability_site/**/*.parquet")],
    ).fetchone()
    assert site == (2, 3, -0.25, 0.625, 1.5, 0, 1, 1)


def test_non_drawable_membership_stays_in_variant_branch_but_not_sequence(tmp_path: Path) -> None:
    source = tmp_path / "source"
    membership = tmp_path / "membership"
    staging = tmp_path / "staging"
    source.mkdir()
    staging.mkdir()
    connection = duckdb.connect()
    write_parquet(
        connection, source / MODULE.PREDICTIONS,
        "SELECT 'v1' variant_key, 'P1' uniprot_accession, 'AF-P1-F1-model_v6.pdb.gz' pdb_name, 0.2::FLOAT ddg_pred",
    )
    write_parquet(
        connection, source / MODULE.TARGETS,
        "SELECT 'v1' variant_key, 'P1' uniprot_accession, 2 canonical_position, 'V' ref_aa, 'I' alt_aa, 'AF-P1-F1-model_v6.pdb.gz' pdb_name",
    )
    write_parquet(
        connection,
        membership / "variant/effect/accession_bucket=0/part.parquet",
        "SELECT 'v1' variant_key, 'P1' uniprot_accession, 'canonical' effect_scope, 2 protein_start, 'V' ref_aa, 'I' alt_aa, false is_drawable",
    )
    counts = MODULE.build(connection, source, staging, membership, ["P1"])
    assert counts == {"predictions": 1, "sequence_sites": 0, "non_drawable_predictions": 1}
