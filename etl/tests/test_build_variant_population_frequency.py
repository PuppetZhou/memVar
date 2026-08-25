from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from etl.build_variant_population_frequency import AF_COLUMNS, DEFAULT_INPUT, build, main, variant_bucket


def fixture_rows() -> list[dict[str, float | str | None]]:
    rows: list[dict[str, float | str | None]] = []
    for index, variant_key in enumerate(("1-9-A-C", "1-1-A-C", "7-55198724-T-C", "X-101-G-A")):
        row: dict[str, float | str | None] = {"variant_id": variant_key}
        row.update({column: (index + 1) / 100 if column.endswith("afr_af") else None for column in AF_COLUMNS})
        rows.append(row)
    return rows


def test_variant_bucket_is_the_first_byte_of_md5() -> None:
    key = "7-55198724-T-C"
    assert variant_bucket(key) == hashlib.md5(key.encode("utf-8")).digest()[0]
    assert 0 <= variant_bucket(key) < 256


def test_build_writes_sorted_zstd_partitions_with_only_variant_key_and_af_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "gnomad.parquet"
    output_path = tmp_path / "variant-population-frequency"
    pq.write_table(pa.Table.from_pylist(fixture_rows()), input_path)

    build(input_path, output_path)

    files = sorted(output_path.glob("variant_bucket=*/data_*.parquet"))
    assert files
    expected_columns = ["variant_key", *AF_COLUMNS]
    records: list[dict[str, float | str | None]] = []
    for path in files:
        assert pq.ParquetFile(path).schema_arrow.names == expected_columns
        assert pq.ParquetFile(path).metadata.row_group(0).column(0).compression == "ZSTD"
        rows = pq.ParquetFile(path).read().to_pylist()
        assert [row["variant_key"] for row in rows] == sorted(row["variant_key"] for row in rows)
        bucket = int(path.parent.name.removeprefix("variant_bucket="))
        assert all(variant_bucket(str(row["variant_key"])) == bucket for row in rows)
        records.extend(rows)

    assert {row["variant_key"] for row in records} == {row["variant_id"] for row in fixture_rows()}
    assert all(set(row) == set(expected_columns) for row in records)


def test_cli_requires_an_explicit_output_path() -> None:
    assert DEFAULT_INPUT == Path("/home/xuyzh/memVar/View/Variant/gnomad_v41_population_frequencies.parquet")
    with pytest.raises(SystemExit):
        main([])
