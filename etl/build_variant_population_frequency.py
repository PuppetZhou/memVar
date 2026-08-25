#!/usr/bin/env python3
"""Build the offline gnomAD v4.1 population-frequency serving partitions."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import duckdb


WEBSITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WEBSITE_ROOT.parent
DEFAULT_INPUT = PROJECT_ROOT / "View" / "Variant" / "gnomad_v41_population_frequencies.parquet"
AF_COLUMNS = (
    "exome_afr_af", "exome_amr_af", "exome_asj_af", "exome_eas_af", "exome_fin_af",
    "exome_mid_af", "exome_nfe_af", "exome_remaining_af", "exome_sas_af",
    "genome_afr_af", "genome_ami_af", "genome_amr_af", "genome_asj_af", "genome_eas_af",
    "genome_fin_af", "genome_mid_af", "genome_nfe_af", "genome_remaining_af", "genome_sas_af",
    "joint_afr_af", "joint_ami_af", "joint_amr_af", "joint_asj_af", "joint_eas_af",
    "joint_fin_af", "joint_mid_af", "joint_nfe_af", "joint_remaining_af", "joint_sas_af",
)


class BuildError(RuntimeError):
    pass


def variant_bucket(variant_key: str) -> int:
    """Return the stable 256-way bucket for one gnomAD variant key."""
    return hashlib.md5(variant_key.encode("utf-8")).digest()[0]


def build(input_path: Path, output_path: Path) -> None:
    if not input_path.is_file():
        raise BuildError(f"Input parquet is missing: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    af_columns = ",\n        ".join(AF_COLUMNS)
    connection = duckdb.connect()
    try:
        connection.execute("SET threads = 1")
        connection.execute(
            f"""
            COPY (
                WITH source AS (
                    SELECT
                        variant_id AS variant_key,
                        {af_columns},
                        lpad(
                            CAST(CAST('0x' || substr(md5(variant_id), 1, 2) AS INTEGER) AS VARCHAR),
                            3,
                            '0'
                        ) AS variant_bucket
                    FROM read_parquet(?)
                )
                SELECT variant_key, {", ".join(AF_COLUMNS)}, variant_bucket
                FROM source
                ORDER BY variant_bucket, variant_key
            ) TO ? (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (variant_bucket))
            """,
            [str(output_path), str(input_path)],
        )
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args(argv)
    build(arguments.input, arguments.output)
    print(arguments.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as error:
        print(f"error: {error}")
        raise SystemExit(2)
