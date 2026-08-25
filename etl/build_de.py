#!/usr/bin/env python3
"""Build immutable, website-owned GEN differential-expression assets."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import uuid

import duckdb
import pyarrow.parquet as pq


ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
DATASET_COLUMNS = {
    "dataset_id", "dataset_name", "project_id", "bioproject_id", "source_page",
    "strategy", "tissues", "disease_conditions", "sample_count_reported",
    "sample_count_metadata", "matrix_sample_count", "sample_join_valid",
}
CONTRAST_COLUMNS = {
    "dataset_id", "contrast_id", "disease_category", "disease_condition", "tissue",
    "case_definition", "control_definition", "case_n", "control_n", "paired",
    "design_formula", "eligible_for_de",
}
DE_COLUMNS = {
    "dataset_id", "contrast_id", "ensembl_gene_id", "gene_symbol", "mean_expression",
    "log2fc", "fdr", "de_direction", "passes_expression_filter", "is_fdr_significant",
    "passes_log2fc_threshold", "is_significant_with_effect", "is_membrane_mapped",
}


def parquet_columns(path: Path) -> set[str]:
    return set(pq.read_schema(path).names)


def require_columns(path: Path, required: set[str]) -> None:
    missing = sorted(required - parquet_columns(path))
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def quoted(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def discover(source_root: Path) -> tuple[list[Path], list[tuple[str, str, Path, Path]]]:
    datasets = sorted(source_root.glob("*/dataset_metadata.parquet"))
    contrasts: list[tuple[str, str, Path, Path]] = []
    seen: set[str] = set()
    for dataset_path in datasets:
        dataset_id = dataset_path.parent.name
        if not ID_PATTERN.fullmatch(dataset_id):
            raise ValueError(f"Unsafe dataset identifier: {dataset_id}")
        require_columns(dataset_path, DATASET_COLUMNS)
        table = pq.read_table(dataset_path, columns=["dataset_id"])
        if table.num_rows != 1 or table.column("dataset_id")[0].as_py() != dataset_id:
            raise ValueError(f"Dataset metadata identity mismatch: {dataset_path}")
        for de_path in sorted((dataset_path.parent / "contrasts").glob("*/differential_expression.parquet")):
            contrast_id = de_path.parent.name
            metadata_path = de_path.parent / "contrast_metadata.parquet"
            if not ID_PATTERN.fullmatch(contrast_id) or contrast_id in seen:
                raise ValueError(f"Unsafe or duplicate contrast identifier: {contrast_id}")
            if not metadata_path.is_file():
                raise ValueError(f"Missing contrast metadata: {metadata_path}")
            require_columns(metadata_path, CONTRAST_COLUMNS)
            require_columns(de_path, DE_COLUMNS)
            metadata = pq.read_table(metadata_path, columns=["dataset_id", "contrast_id"])
            if metadata.num_rows != 1 or metadata.column("dataset_id")[0].as_py() != dataset_id or metadata.column("contrast_id")[0].as_py() != contrast_id:
                raise ValueError(f"Contrast metadata identity mismatch: {metadata_path}")
            identities = pq.read_table(de_path, columns=["dataset_id", "contrast_id"])
            if identities.num_rows and (
                set(identities.column("dataset_id").to_pylist()) != {dataset_id}
                or set(identities.column("contrast_id").to_pylist()) != {contrast_id}
            ):
                raise ValueError(f"Differential-expression identity mismatch: {de_path}")
            seen.add(contrast_id)
            contrasts.append((dataset_id, contrast_id, metadata_path, de_path))
    if not datasets or not contrasts:
        raise ValueError("GEN source contains no dataset metadata or DE contrasts")
    return datasets, contrasts


def build(source_root: Path, protein_basic: Path, output_root: Path) -> None:
    require_columns(protein_basic, {"uniprot_accession", "gene_symbol"})
    datasets, contrasts = discover(source_root)
    if (len(datasets), len({item[0] for item in contrasts}), len(contrasts)) != (151, 42, 142):
        raise ValueError("GEN conservation failure: expected 151 metadata / 42 DE datasets / 142 contrasts")

    temporary = output_root.with_name(f"{output_root.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}")
    backup = output_root.with_name(f"{output_root.name}.old-{uuid.uuid4().hex}")
    temporary.mkdir(parents=True)
    (temporary / "contrasts").mkdir()
    database = temporary / "memvar_de.duckdb"
    connection = duckdb.connect(str(database))
    try:
        dataset_glob = quoted(source_root / "*" / "dataset_metadata.parquet")
        metadata_glob = quoted(source_root / "*" / "contrasts" / "*" / "contrast_metadata.parquet")
        de_glob = quoted(source_root / "*" / "contrasts" / "*" / "differential_expression.parquet")
        protein_path = quoted(protein_basic)
        connection.execute(f"""
            CREATE TABLE dataset AS
            SELECT dataset_id, dataset_name, project_id, bioproject_id, source_page, strategy,
                   CAST(tissues AS VARCHAR[]) AS tissues,
                   CAST(disease_conditions AS VARCHAR[]) AS disease_conditions,
                   sample_count_reported, sample_count_metadata, matrix_sample_count, sample_join_valid
            FROM read_parquet('{dataset_glob}', union_by_name=true)
            ORDER BY dataset_id
        """)
        connection.execute(f"""
            CREATE TABLE contrast AS
            SELECT dataset_id, contrast_id, disease_category, disease_condition, tissue,
                   case_definition, control_definition, case_n, control_n, paired,
                   design_formula, eligible_for_de
            FROM read_parquet('{metadata_glob}', union_by_name=true)
            ORDER BY dataset_id, contrast_id
        """)
        connection.execute(f"""
            CREATE TABLE protein_contrast AS
            SELECT DISTINCT p.uniprot_accession, p.gene_symbol, d.ensembl_gene_id,
                   d.dataset_id, d.contrast_id, d.mean_expression, d.log2fc, d.fdr,
                   d.de_direction, d.is_fdr_significant, d.passes_log2fc_threshold,
                   d.is_significant_with_effect
            FROM read_parquet('{de_glob}', union_by_name=true) d
            JOIN read_parquet('{protein_path}') p
              ON lower(trim(d.gene_symbol)) = lower(trim(p.gene_symbol))
            WHERE d.is_significant_with_effect = TRUE
            ORDER BY p.uniprot_accession, d.dataset_id, d.contrast_id
        """)
        connection.execute("CREATE TABLE manifest(contrast_id VARCHAR PRIMARY KEY, relative_path VARCHAR UNIQUE, tested_count BIGINT, plotted_count BIGINT, unplottable_count BIGINT, fdr_zero_count BIGINT)")

        for _, contrast_id, _, de_path in contrasts:
            output = temporary / "contrasts" / f"{contrast_id}.parquet"
            source = quoted(de_path)
            destination = quoted(output)
            counts = connection.execute(f"""
                SELECT count(*),
                       count(*) FILTER (WHERE isfinite(log2fc) AND isfinite(fdr) AND fdr >= 0),
                       count(*) FILTER (WHERE isfinite(log2fc) AND isfinite(fdr) AND fdr = 0)
                FROM read_parquet('{source}')
            """).fetchone()
            tested, plotted, fdr_zero = (int(value) for value in counts)
            connection.execute(f"""
                COPY (
                    SELECT gene_symbol, ensembl_gene_id, mean_expression, log2fc, fdr,
                           CASE WHEN fdr = 0 THEN 300.0 ELSE -log10(fdr) END AS neg_log10_fdr,
                           de_direction, passes_expression_filter, is_fdr_significant,
                           passes_log2fc_threshold, is_significant_with_effect, is_membrane_mapped
                    FROM read_parquet('{source}')
                    WHERE isfinite(log2fc) AND isfinite(fdr) AND fdr >= 0
                    ORDER BY gene_symbol NULLS LAST, ensembl_gene_id NULLS LAST
                ) TO '{destination}' (FORMAT PARQUET, COMPRESSION ZSTD)
            """)
            connection.execute(
                "INSERT INTO manifest VALUES (?, ?, ?, ?, ?, ?)",
                [contrast_id, f"contrasts/{contrast_id}.parquet", tested, plotted, tested - plotted, fdr_zero],
            )
        connection.execute("CREATE INDEX protein_contrast_accession ON protein_contrast(uniprot_accession)")
        connection.execute("CREATE INDEX contrast_identity ON contrast(contrast_id)")
        connection.execute("CHECKPOINT")
    finally:
        connection.close()

    manifest_path = temporary / "manifest.parquet"
    connection = duckdb.connect(str(database), read_only=True)
    try:
        connection.execute("COPY manifest TO ? (FORMAT PARQUET, COMPRESSION ZSTD)", [str(manifest_path)])
    finally:
        connection.close()

    replaced = False
    try:
        if output_root.exists():
            os.replace(output_root, backup)
            replaced = True
        os.replace(temporary, output_root)
        if replaced:
            shutil.rmtree(backup)
    except Exception:
        if replaced and not output_root.exists() and backup.exists():
            os.replace(backup, output_root)
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=root / "Mapping-data/GEN/results/by_dataset")
    parser.add_argument("--protein-basic", type=Path, default=root / "View/Basic_info/protein_basic.parquet")
    parser.add_argument("--output-root", type=Path, default=root / "website/data/generated/differential_expression")
    args = parser.parse_args()
    build(args.source_root.resolve(), args.protein_basic.resolve(), args.output_root.resolve())


if __name__ == "__main__":
    main()
