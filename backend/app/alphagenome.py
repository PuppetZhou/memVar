"""Read-only AlphaGenome catalog and bounded display endpoints."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path, PurePosixPath
from typing import Iterator

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query
import numpy as np

from .alphagenome_models import (
    AlphaGenomeContactMapResponse,
    AlphaGenomeGeneCandidate,
    AlphaGenomeJunction,
    AlphaGenomeJunctionResponse,
    AlphaGenomeSignalResponse,
    AlphaGenomeSummaryResponse,
    AlphaGenomeTile,
    AlphaGenomeTrack,
    AlphaGenomeTrackCatalogResponse,
)
from .store import get_connection, require_protein
from .release_store import release_store


router = APIRouter(prefix="/api/v1")
ALLOWED_BINS = {256, 1024, 4096}
MODALITIES = {
    "rna_seq", "cage", "procap", "atac", "chip_histone", "splice_sites",
    "splice_site_usage", "splice_junctions", "contact_maps",
}


def alphagenome_root() -> Path:
    return release_store().alphagenome_assets


def catalog_path() -> Path:
    return alphagenome_root() / "alphagenome_catalog.duckdb"


@contextmanager
def read_catalog() -> Iterator[duckdb.DuckDBPyConnection]:
    root, path = alphagenome_root(), catalog_path()
    if root.is_symlink() or not root.is_dir() or path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=503, detail="AlphaGenome display catalog is unavailable")
    connection = duckdb.connect(str(path), read_only=True)
    try:
        yield connection
    finally:
        connection.close()


def get_catalog() -> Iterator[duckdb.DuckDBPyConnection]:
    with read_catalog() as connection:
        yield connection


def dictionaries(result: duckdb.DuckDBPyConnection) -> list[dict[str, object]]:
    names = [column[0] for column in result.description]
    return [dict(zip(names, row, strict=True)) for row in result.fetchall()]


def manifest() -> dict[str, object]:
    path = alphagenome_root() / "build_manifest.json"
    if path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=503, detail="AlphaGenome build manifest is unavailable")
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail="AlphaGenome build manifest cannot be read") from error
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise HTTPException(status_code=500, detail="Invalid AlphaGenome build manifest")
    return value


def canonical_accession(core: duckdb.DuckDBPyConnection, accession: str) -> str:
    return str(require_protein(core, accession)["uniprot_accession"])


def track_from_row(row: dict[str, object]) -> AlphaGenomeTrack:
    return AlphaGenomeTrack(**{
        key: row.get(key) for key in AlphaGenomeTrack.model_fields
    })


def require_mapped_gene(
    catalog: duckdb.DuckDBPyConnection,
    accession: str,
    gene_id: str,
    *,
    ready: bool,
) -> None:
    row = catalog.execute(
        """
        SELECT has_prediction, display_ready
        FROM protein_gene_coverage
        WHERE uniprot_accession = ? AND ensembl_gene_id = ?
        """,
        [accession, gene_id],
    ).fetchone()
    if row is None or not bool(row[0]):
        raise HTTPException(status_code=404, detail="AlphaGenome gene is not mapped to this protein")
    if ready and not bool(row[1]):
        raise HTTPException(status_code=409, detail="AlphaGenome display bundle is still being prepared")


def require_track(
    catalog: duckdb.DuckDBPyConnection,
    track_id: str,
    modality: str | None = None,
) -> AlphaGenomeTrack:
    result = catalog.execute(
        "SELECT * FROM track WHERE track_id = ?", [track_id]
    )
    rows = dictionaries(result)
    if len(rows) != 1 or (modality is not None and rows[0]["modality"] != modality):
        raise HTTPException(status_code=404, detail=f"AlphaGenome track not found: {track_id}")
    return track_from_row(rows[0])


def prepared_row(
    catalog: duckdb.DuckDBPyConnection,
    gene_id: str,
    tile_id: str,
) -> dict[str, object]:
    rows = dictionaries(catalog.execute(
        "SELECT * FROM prepared_tile WHERE ensembl_gene_id = ? AND tile_id = ?",
        [gene_id, tile_id],
    ))
    if len(rows) != 1:
        raise HTTPException(status_code=404, detail=f"AlphaGenome tile is not display-ready: {tile_id}")
    return rows[0]


def safe_asset(relative_path: object, expected_root: str) -> Path:
    relative = PurePosixPath(str(relative_path))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != expected_root:
        raise HTTPException(status_code=500, detail="Unsafe AlphaGenome display asset path")
    root = alphagenome_root()
    candidate = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise HTTPException(status_code=500, detail="Unsafe AlphaGenome display asset symlink")
    try:
        candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="AlphaGenome display asset is unavailable") from error
    if not candidate.is_file():
        raise HTTPException(status_code=500, detail="AlphaGenome display asset is unavailable")
    return candidate


@router.get("/proteins/{acc}/alphagenome/summary", response_model=AlphaGenomeSummaryResponse)
def protein_alphagenome_summary(
    acc: str,
    core: duckdb.DuckDBPyConnection = Depends(get_connection),
    catalog: duckdb.DuckDBPyConnection = Depends(get_catalog),
) -> AlphaGenomeSummaryResponse:
    accession = canonical_accession(core, acc)
    rows = dictionaries(catalog.execute(
        """
        SELECT c.*, g.gene_symbol, g.hgnc_id, g.chromosome, g.gene_start_1based,
               g.gene_end_1based_inclusive, g.gene_strand
        FROM protein_gene_coverage c
        LEFT JOIN gene g USING (ensembl_gene_id)
        WHERE c.uniprot_accession = ?
        ORDER BY c.ensembl_gene_id NULLS LAST
        """,
        [accession],
    ))
    if not rows:
        raise HTTPException(status_code=500, detail="AlphaGenome protein coverage is missing")
    candidates: list[AlphaGenomeGeneCandidate] = []
    for row in rows:
        gene_id = row.get("ensembl_gene_id")
        tile_rows = [] if gene_id is None else dictionaries(catalog.execute(
            """
            SELECT t.*, p.tile_id IS NOT NULL AS display_ready
            FROM tile t
            LEFT JOIN prepared_tile p USING (ensembl_gene_id, tile_id)
            WHERE t.ensembl_gene_id = ? ORDER BY t.tile_index
            """,
            [gene_id],
        ))
        candidates.append(AlphaGenomeGeneCandidate(
            **{key: row.get(key) for key in (
                "ensembl_gene_id", "gene_symbol", "hgnc_id", "chromosome",
                "gene_start_1based", "gene_end_1based_inclusive", "gene_strand",
                "mapping_status", "mapping_count", "has_prediction", "display_ready",
            )},
            tiles=[AlphaGenomeTile(**{key: tile[key] for key in AlphaGenomeTile.model_fields}) for tile in tile_rows],
        ))
    ready = any(candidate.display_ready for candidate in candidates)
    predicted = any(candidate.has_prediction for candidate in candidates)
    counts = dict(catalog.execute(
        "SELECT modality, count(*) FROM track GROUP BY modality ORDER BY modality"
    ).fetchall()) if predicted else {}
    build = manifest()
    return AlphaGenomeSummaryResponse(
        uniprot_accession=accession,
        availability="available" if ready else "preparing" if predicted else "unavailable",
        missing_official_modalities=list(build.get("missing_official_modalities", [])),
        modality_track_counts={str(key): int(value) for key, value in counts.items()},
        candidates=candidates,
        notice="Reference-sequence model prediction; not an experimental measurement or variant-effect score.",
    )


@router.get("/proteins/{acc}/alphagenome/tracks", response_model=AlphaGenomeTrackCatalogResponse)
def protein_alphagenome_tracks(
    acc: str,
    ensembl_gene_id: str = Query(pattern=r"^ENSG[0-9]{11}$"),
    modality: str = Query(),
    core: duckdb.DuckDBPyConnection = Depends(get_connection),
    catalog: duckdb.DuckDBPyConnection = Depends(get_catalog),
) -> AlphaGenomeTrackCatalogResponse:
    accession = canonical_accession(core, acc)
    if modality not in MODALITIES:
        raise HTTPException(status_code=422, detail=f"Unsupported AlphaGenome modality: {modality}")
    require_mapped_gene(catalog, accession, ensembl_gene_id, ready=False)
    rows = dictionaries(catalog.execute(
        "SELECT * FROM track WHERE modality = ? ORDER BY source_column_index", [modality]
    ))
    return AlphaGenomeTrackCatalogResponse(
        uniprot_accession=accession, ensembl_gene_id=ensembl_gene_id,
        modality=modality, tracks=[track_from_row(row) for row in rows], total=len(rows),
    )


@router.get("/proteins/{acc}/alphagenome/signals", response_model=AlphaGenomeSignalResponse)
def protein_alphagenome_signal(
    acc: str,
    ensembl_gene_id: str = Query(pattern=r"^ENSG[0-9]{11}$"),
    tile_id: str = Query(pattern=r"^tile_[0-9]{3}$"),
    track_id: str = Query(min_length=1, max_length=80),
    bins: int = Query(default=1024, ge=256, le=4096),
    start: int | None = Query(default=None, ge=0),
    end: int | None = Query(default=None, ge=1),
    core: duckdb.DuckDBPyConnection = Depends(get_connection),
    catalog: duckdb.DuckDBPyConnection = Depends(get_catalog),
) -> AlphaGenomeSignalResponse:
    accession = canonical_accession(core, acc)
    if bins not in ALLOWED_BINS:
        raise HTTPException(status_code=422, detail="AlphaGenome bins must be 256, 1024, or 4096")
    require_mapped_gene(catalog, accession, ensembl_gene_id, ready=True)
    track = require_track(catalog, track_id)
    if track.modality not in MODALITIES - {"splice_junctions", "contact_maps"}:
        raise HTTPException(status_code=422, detail="Track is not a one-dimensional AlphaGenome signal")
    prepared = prepared_row(catalog, ensembl_gene_id, tile_id)
    asset = safe_asset(prepared["signal_relative_path"], "tracks")
    row = catalog.execute(
        """
        SELECT window_start_0based, window_end_0based, source_resolution_bp,
               value_count, mean_float16_le, max_float16_le
        FROM read_parquet(?) WHERE track_id = ? AND level_bins = ?
        """,
        [str(asset), track_id, bins],
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="AlphaGenome signal level is unavailable")
    window_start, window_end, resolution, count = (int(row[index]) for index in range(4))
    means = np.frombuffer(row[4], dtype="<f2")
    maxima = np.frombuffer(row[5], dtype="<f2")
    if means.size != count or maxima.size != count or count != bins:
        raise HTTPException(status_code=500, detail="Invalid AlphaGenome signal bundle")
    requested_start = window_start if start is None else start
    requested_end = window_end if end is None else end
    if requested_start < window_start or requested_end > window_end or requested_start >= requested_end:
        raise HTTPException(status_code=422, detail="Signal window must lie inside the selected model tile")
    width = window_end - window_start
    first = max(0, int(np.floor((requested_start - window_start) * count / width)))
    last = min(count, int(np.ceil((requested_end - window_start) * count / width)))
    values = [(float(mean), float(maximum)) for mean, maximum in zip(means[first:last], maxima[first:last], strict=True)]
    return AlphaGenomeSignalResponse(
        uniprot_accession=accession, ensembl_gene_id=ensembl_gene_id, tile_id=tile_id,
        track=track, level_bins=bins, returned_bin_start=first, returned_bin_end=last,
        window_start_0based=window_start, window_end_0based=window_end,
        source_resolution_bp=resolution, values=values,
    )


@router.get("/proteins/{acc}/alphagenome/junctions", response_model=AlphaGenomeJunctionResponse)
def protein_alphagenome_junctions(
    acc: str,
    ensembl_gene_id: str = Query(pattern=r"^ENSG[0-9]{11}$"),
    tile_id: str = Query(pattern=r"^tile_[0-9]{3}$"),
    track_id: str = Query(pattern=r"^splice_junctions:[0-9]{3}$"),
    start: int | None = Query(default=None, ge=0),
    end: int | None = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=200),
    core: duckdb.DuckDBPyConnection = Depends(get_connection),
    catalog: duckdb.DuckDBPyConnection = Depends(get_catalog),
) -> AlphaGenomeJunctionResponse:
    accession = canonical_accession(core, acc)
    require_mapped_gene(catalog, accession, ensembl_gene_id, ready=True)
    track = require_track(catalog, track_id, "splice_junctions")
    prepared = prepared_row(catalog, ensembl_gene_id, tile_id)
    asset = safe_asset(prepared["junction_relative_path"], "junctions")
    filters, parameters = ["track_id = ?"], [track_id]
    if start is not None:
        filters.append("end_0based > ?")
        parameters.append(start)
    if end is not None:
        filters.append("start_0based < ?")
        parameters.append(end)
    where = " AND ".join(filters)
    available = int(catalog.execute(
        f"SELECT count(*) FROM read_parquet(?) WHERE {where}", [str(asset), *parameters]
    ).fetchone()[0])
    rows = catalog.execute(
        f"""
        SELECT rank, chromosome, start_0based, end_0based, strand, value
        FROM read_parquet(?) WHERE {where} ORDER BY value DESC, start_0based, end_0based LIMIT ?
        """,
        [str(asset), *parameters, limit],
    ).fetchall()
    items = [AlphaGenomeJunction(
        rank=int(row[0]), chromosome=str(row[1]), start_0based=int(row[2]),
        end_0based=int(row[3]), strand=str(row[4]), value=float(row[5]),
    ) for row in rows]
    return AlphaGenomeJunctionResponse(
        uniprot_accession=accession, ensembl_gene_id=ensembl_gene_id, tile_id=tile_id,
        track=track, items=items, available_count=available, returned_count=len(items),
        truncated=available > len(items),
    )


@router.get("/proteins/{acc}/alphagenome/contact-map", response_model=AlphaGenomeContactMapResponse)
def protein_alphagenome_contact_map(
    acc: str,
    ensembl_gene_id: str = Query(pattern=r"^ENSG[0-9]{11}$"),
    tile_id: str = Query(pattern=r"^tile_[0-9]{3}$"),
    track_id: str = Query(pattern=r"^contact_maps:[0-9]{3}$"),
    size: int = Query(default=128, ge=128, le=128),
    start: int | None = Query(default=None, ge=0),
    end: int | None = Query(default=None, ge=1),
    core: duckdb.DuckDBPyConnection = Depends(get_connection),
    catalog: duckdb.DuckDBPyConnection = Depends(get_catalog),
) -> AlphaGenomeContactMapResponse:
    accession = canonical_accession(core, acc)
    require_mapped_gene(catalog, accession, ensembl_gene_id, ready=True)
    track = require_track(catalog, track_id, "contact_maps")
    prepared = prepared_row(catalog, ensembl_gene_id, tile_id)
    asset = safe_asset(prepared["contact_relative_path"], "contacts")
    row = catalog.execute(
        """
        SELECT matrix_size, window_start_0based, window_end_0based,
               source_resolution_bp, mean_float16_le
        FROM read_parquet(?) WHERE track_id = ? AND matrix_size = ?
        """,
        [str(asset), track_id, size],
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="AlphaGenome contact map is unavailable")
    matrix_size, window_start, window_end, resolution = (int(row[index]) for index in range(4))
    values = np.frombuffer(row[4], dtype="<f2")
    if values.size != matrix_size * matrix_size:
        raise HTTPException(status_code=500, detail="Invalid AlphaGenome contact-map bundle")
    requested_start = window_start if start is None else start
    requested_end = window_end if end is None else end
    if requested_start < window_start or requested_end > window_end or requested_start >= requested_end:
        raise HTTPException(status_code=422, detail="Contact-map window must lie inside the selected model tile")
    width = window_end - window_start
    first = max(0, int(np.floor((requested_start - window_start) * matrix_size / width)))
    last = min(matrix_size, int(np.ceil((requested_end - window_start) * matrix_size / width)))
    matrix = values.reshape(matrix_size, matrix_size)[first:last, first:last]
    cropped_start = window_start + int(np.floor(first * width / matrix_size))
    cropped_end = window_start + int(np.ceil(last * width / matrix_size))
    return AlphaGenomeContactMapResponse(
        uniprot_accession=accession, ensembl_gene_id=ensembl_gene_id, tile_id=tile_id,
        track=track, matrix_size=last - first, window_start_0based=cropped_start,
        window_end_0based=cropped_end, source_resolution_bp=resolution,
        values=[float(value) for value in matrix.ravel()],
    )
