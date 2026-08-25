"""Read-only GEN differential-expression summary and volcano endpoints."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterator

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query

from .de_models import (
    DeContrastSummary,
    DeDatasetSummary,
    DeTargetResult,
    DifferentialExpressionVolcano,
    ProteinDifferentialExpressionSummary,
    VolcanoContrastMetadata,
    VolcanoCounts,
)
from .store import get_connection, require_protein
from .release_store import release_store


router = APIRouter(prefix="/api/v1")
POINT_COLUMNS = [
    "log2fc", "neg_log10_fdr", "gene_symbol", "ensembl_gene_id", "mean_expression",
    "raw_fdr", "direction", "passes_expression_filter", "is_fdr_significant",
    "passes_log2fc_threshold", "is_significant_with_effect", "is_membrane_mapped",
    "is_current_target",
]


def de_root() -> Path:
    return release_store().differential_expression_assets


def de_database_path() -> Path:
    return de_root() / "memvar_de.duckdb"


@contextmanager
def read_de_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    path = de_database_path()
    if not path.is_file():
        raise RuntimeError(f"Differential-expression database is missing: {path}")
    connection = duckdb.connect(str(path), read_only=True)
    try:
        yield connection
    finally:
        connection.close()


def get_de_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    with read_de_connection() as connection:
        yield connection


def dictionaries(result: duckdb.DuckDBPyConnection) -> list[dict[str, object]]:
    names = [column[0] for column in result.description]
    return [dict(zip(names, row, strict=True)) for row in result.fetchall()]


def canonical_protein(connection: duckdb.DuckDBPyConnection, accession: str) -> tuple[str, str]:
    overview = require_protein(connection, accession)
    gene_symbol = overview.get("gene_symbol")
    if not isinstance(gene_symbol, str) or not gene_symbol.strip():
        raise HTTPException(status_code=404, detail="Protein has no gene symbol for differential-expression mapping")
    return str(overview["uniprot_accession"]), gene_symbol


@router.get(
    "/proteins/{acc}/differential-expression/summary",
    response_model=ProteinDifferentialExpressionSummary,
)
def protein_de_summary(
    acc: str,
    core: duckdb.DuckDBPyConnection = Depends(get_connection),
    de: duckdb.DuckDBPyConnection = Depends(get_de_connection),
) -> ProteinDifferentialExpressionSummary:
    accession, gene_symbol = canonical_protein(core, acc)
    rows = dictionaries(de.execute(
        """
        SELECT d.dataset_id, d.dataset_name, d.project_id, d.bioproject_id, d.source_page,
               d.strategy, d.tissues, d.disease_conditions, d.sample_count_reported,
               d.sample_count_metadata, d.matrix_sample_count, d.sample_join_valid,
               c.contrast_id, c.disease_category, c.disease_condition, c.tissue,
               c.case_definition, c.control_definition, c.case_n, c.control_n, c.paired,
               p.ensembl_gene_id, p.mean_expression, p.log2fc, p.fdr, p.de_direction
        FROM protein_contrast p
        JOIN contrast c USING (dataset_id, contrast_id)
        JOIN dataset d USING (dataset_id)
        WHERE p.uniprot_accession = ? AND p.is_significant_with_effect = TRUE
        ORDER BY d.dataset_id, c.contrast_id
        """,
        [accession],
    ))
    contrast_rows: dict[tuple[str, str], tuple[dict[str, object], list[DeTargetResult]]] = {}
    for row in rows:
        key = str(row["dataset_id"]), str(row["contrast_id"])
        if key not in contrast_rows:
            contrast_rows[key] = (row, [])
        contrast_rows[key][1].append(DeTargetResult(
            ensembl_gene_id=(str(row["ensembl_gene_id"]) if row["ensembl_gene_id"] is not None else None),
            mean_expression=(float(row["mean_expression"]) if row["mean_expression"] is not None else None),
            log2fc=float(row["log2fc"]), fdr=float(row["fdr"]), direction=str(row["de_direction"]),
        ))
    grouped: dict[str, tuple[dict[str, object], list[DeContrastSummary]]] = {}
    for (dataset_id, _), (row, target_results) in contrast_rows.items():
        if dataset_id not in grouped:
            grouped[dataset_id] = (row, [])
        grouped[dataset_id][1].append(DeContrastSummary(
            contrast_id=str(row["contrast_id"]),
            disease_category=str(row["disease_category"]), disease_condition=str(row["disease_condition"]),
            tissue=str(row["tissue"]), case_definition=str(row["case_definition"]),
            control_definition=str(row["control_definition"]), case_n=int(row["case_n"]),
            control_n=int(row["control_n"]), paired=bool(row["paired"]),
            target_result_total=len(target_results),
            mapping_status=("unique_gene_row" if len(target_results) == 1 else "multiple_gene_rows_same_symbol"),
            target_results=target_results,
        ))
    datasets = []
    for row, contrasts in grouped.values():
        datasets.append(DeDatasetSummary(
            dataset_id=str(row["dataset_id"]), dataset_name=str(row["dataset_name"] or ""),
            project_id=str(row["project_id"] or ""), bioproject_id=str(row["bioproject_id"] or ""),
            source_page=str(row["source_page"] or ""), strategy=str(row["strategy"] or ""),
            tissues=list(row["tissues"] or []), disease_conditions=list(row["disease_conditions"] or []),
            sample_count_reported=int(row["sample_count_reported"] or 0),
            sample_count_metadata=int(row["sample_count_metadata"] or 0),
            matrix_sample_count=int(row["matrix_sample_count"] or 0),
            sample_join_valid=bool(row["sample_join_valid"]),
            qualifying_contrast_total=len(contrasts), contrasts=contrasts,
        ))
    return ProteinDifferentialExpressionSummary(
        uniprot_accession=accession, gene_symbol=gene_symbol,
        dataset_total=len(datasets), contrast_total=sum(len(item.contrasts) for item in datasets),
        datasets=datasets,
    )


def safe_detail_path(relative_path: str) -> Path:
    relative = PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 2 or relative.parts[0] != "contrasts":
        raise HTTPException(status_code=500, detail="Unsafe differential-expression manifest path")
    root = de_root()
    path = root.joinpath(*relative.parts)
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Differential-expression detail asset is unavailable") from error
    if path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=500, detail="Differential-expression detail asset is unavailable")
    return path


@router.get(
    "/differential-expression/contrasts/{contrast_id}/volcano",
    response_model=DifferentialExpressionVolcano,
)
def contrast_volcano(
    contrast_id: str,
    accession: str = Query(min_length=1),
    core: duckdb.DuckDBPyConnection = Depends(get_connection),
    de: duckdb.DuckDBPyConnection = Depends(get_de_connection),
) -> DifferentialExpressionVolcano:
    canonical_accession, gene_symbol = canonical_protein(core, accession)
    manifest_result = de.execute(
        "SELECT relative_path, tested_count, plotted_count, unplottable_count, fdr_zero_count FROM manifest WHERE contrast_id = ?",
        [contrast_id],
    ).fetchone()
    metadata_result = de.execute(
        """
        SELECT dataset_id, contrast_id, disease_category, disease_condition, tissue,
               case_definition, control_definition, case_n, control_n, paired, design_formula
        FROM contrast WHERE contrast_id = ?
        """,
        [contrast_id],
    ).fetchone()
    if manifest_result is None or metadata_result is None:
        raise HTTPException(status_code=404, detail=f"Differential-expression contrast not found: {contrast_id}")
    detail = safe_detail_path(str(manifest_result[0]))
    points = de.execute(
        """
        SELECT log2fc, neg_log10_fdr, gene_symbol, ensembl_gene_id, mean_expression, fdr,
               de_direction, passes_expression_filter, is_fdr_significant,
               passes_log2fc_threshold, is_significant_with_effect, is_membrane_mapped,
               lower(trim(gene_symbol)) = lower(trim(?)) AS is_current_target
        FROM read_parquet(?)
        """,
        [gene_symbol, str(detail)],
    ).fetchall()
    tested, plotted, unplottable, fdr_zero = (int(value) for value in manifest_result[1:])
    if len(points) != plotted or plotted + unplottable != tested:
        raise HTTPException(status_code=500, detail="Differential-expression point-count conservation failure")
    return DifferentialExpressionVolcano(
        uniprot_accession=canonical_accession, gene_symbol=gene_symbol,
        contrast=VolcanoContrastMetadata(**dict(zip(
            ["dataset_id", "contrast_id", "disease_category", "disease_condition", "tissue",
             "case_definition", "control_definition", "case_n", "control_n", "paired", "design_formula"],
            metadata_result, strict=True,
        ))),
        counts=VolcanoCounts(tested=tested, plotted=plotted, unplottable=unplottable, fdr_zero=fdr_zero),
        point_columns=POINT_COLUMNS,
        points=points,
    )
