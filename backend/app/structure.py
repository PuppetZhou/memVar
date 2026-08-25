"""Read-only access to website-owned AlphaFold v6 structure assets."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Path as PathParameter
from starlette.responses import FileResponse

from .store import get_connection, require_protein
from .release_store import release_store
from .models import ProteinStructuresResponse, StructureFragment


router = APIRouter(prefix="/api/v1")

MANIFEST_COLUMNS = {
    "uniprot_accession",
    "fragment_number",
    "fragment_label",
    "filename",
    "relative_path",
    "compressed_bytes",
    "uncompressed_bytes",
    "gzip_sha256",
    "pdb_sha256",
    "canonical_start",
    "canonical_end",
    "model_version",
    "source",
}
IMMUTABLE_CACHE_CONTROL = "public, max-age=31536000, immutable"


def structure_root() -> Path:
    return release_store().structure_assets


def structure_manifest_path() -> Path:
    return structure_root() / "manifest.parquet"


def manifest_rows(accession: str) -> list[dict[str, object]]:
    root = structure_root()
    manifest = structure_manifest_path()
    if root.is_symlink() or not root.is_dir() or not manifest.is_file() or manifest.is_symlink():
        raise HTTPException(status_code=503, detail="AlphaFold structure manifest is unavailable")

    connection = duckdb.connect()
    try:
        actual_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE SELECT * FROM read_parquet(?)", [str(manifest)]
            ).fetchall()
        }
        missing_columns = sorted(MANIFEST_COLUMNS - actual_columns)
        if missing_columns:
            raise HTTPException(
                status_code=500,
                detail=f"AlphaFold structure manifest is missing columns: {', '.join(missing_columns)}",
            )
        result = connection.execute(
            """
            SELECT uniprot_accession, fragment_number, fragment_label, filename,
                   relative_path, compressed_bytes, uncompressed_bytes,
                   canonical_start, canonical_end, model_version, source
            FROM read_parquet(?)
            WHERE uniprot_accession = ?
            ORDER BY fragment_number
            """,
            [str(manifest), accession],
        )
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
    except HTTPException:
        raise
    except (duckdb.Error, OSError) as error:
        raise HTTPException(status_code=500, detail="AlphaFold structure manifest cannot be read") from error
    finally:
        connection.close()


def expected_filename(accession: str, fragment_number: int) -> str:
    return f"AF-{accession}-F{fragment_number}-model_v6.pdb.gz"


def validate_manifest_row(row: dict[str, object], accession: str) -> None:
    try:
        fragment_number = int(row["fragment_number"])
        fragment_label = str(row["fragment_label"])
        filename = str(row["filename"])
        relative_path = str(row["relative_path"])
        compressed_bytes = int(row["compressed_bytes"])
        uncompressed_bytes = int(row["uncompressed_bytes"])
        model_version = int(row["model_version"])
        source = str(row["source"])
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Invalid AlphaFold structure manifest row") from error

    expected = expected_filename(accession, fragment_number)
    expected_relative = PurePosixPath(accession, expected).as_posix()
    if (
        row["uniprot_accession"] != accession
        or fragment_number < 1
        or fragment_label != f"F{fragment_number}"
        or filename != expected
        or relative_path != expected_relative
        or compressed_bytes < 1
        or uncompressed_bytes < 1
        or model_version != 6
        or source != "AlphaFold DB"
    ):
        raise HTTPException(status_code=500, detail="Invalid AlphaFold structure manifest row")

    canonical_start = row["canonical_start"]
    canonical_end = row["canonical_end"]
    if (canonical_start is None) != (canonical_end is None):
        raise HTTPException(status_code=500, detail="Invalid AlphaFold canonical range")
    if canonical_start is not None:
        try:
            start, end = int(canonical_start), int(canonical_end)
        except (TypeError, ValueError) as error:
            raise HTTPException(status_code=500, detail="Invalid AlphaFold canonical range") from error
        if start < 1 or end < start:
            raise HTTPException(status_code=500, detail="Invalid AlphaFold canonical range")


def safe_structure_file(row: dict[str, object], accession: str) -> Path:
    validate_manifest_row(row, accession)
    root = structure_root()
    if root.is_symlink():
        raise HTTPException(status_code=500, detail="Unsafe AlphaFold structure root symlink")
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as error:
        raise HTTPException(status_code=503, detail="AlphaFold structure assets are unavailable") from error
    if not resolved_root.is_dir():
        raise HTTPException(status_code=503, detail="AlphaFold structure assets are unavailable")

    relative = PurePosixPath(str(row["relative_path"]))
    if relative.is_absolute() or ".." in relative.parts:
        raise HTTPException(status_code=500, detail="Unsafe AlphaFold structure path")
    candidate = root.joinpath(*relative.parts)

    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise HTTPException(status_code=500, detail="Unsafe AlphaFold structure symlink")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=404, detail="AlphaFold structure file not found") from error
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="AlphaFold structure file not found")
    if resolved.stat().st_size != int(row["compressed_bytes"]):
        raise HTTPException(status_code=500, detail="AlphaFold structure file size does not match manifest")
    return resolved


def validate_rows(rows: list[dict[str, object]], accession: str) -> None:
    seen_fragments: set[int] = set()
    for row in rows:
        validate_manifest_row(row, accession)
        fragment_number = int(row["fragment_number"])
        if fragment_number in seen_fragments:
            raise HTTPException(status_code=500, detail="Duplicate AlphaFold structure fragment")
        seen_fragments.add(fragment_number)


def fragment_url(accession: str, fragment_number: int) -> str:
    return f"/api/v1/proteins/{accession}/structures/{fragment_number}/pdb"


@router.get("/proteins/{acc}/structures", response_model=ProteinStructuresResponse)
def protein_structures(
    acc: str,
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> ProteinStructuresResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    rows = manifest_rows(accession)
    validate_rows(rows, accession)
    fragments = [
        StructureFragment(
            fragment_number=int(row["fragment_number"]),
            fragment_label=str(row["fragment_label"]),
            filename=str(row["filename"]),
            compressed_bytes=int(row["compressed_bytes"]),
            uncompressed_bytes=int(row["uncompressed_bytes"]),
            canonical_start=(int(row["canonical_start"]) if row["canonical_start"] is not None else None),
            canonical_end=(int(row["canonical_end"]) if row["canonical_end"] is not None else None),
            content_url=fragment_url(accession, int(row["fragment_number"])),
            download_url=fragment_url(accession, int(row["fragment_number"])),
        )
        for row in rows
    ]
    return ProteinStructuresResponse(
        uniprot_accession=accession,
        availability="available" if fragments else "unavailable",
        fragment_total=len(fragments),
        fragments=fragments,
    )


@router.api_route(
    "/proteins/{acc}/structures/{fragment}/pdb",
    methods=["GET", "HEAD"],
    response_class=FileResponse,
)
def protein_structure_pdb(
    acc: str,
    fragment: int = PathParameter(ge=1, le=999),
    connection: duckdb.DuckDBPyConnection = Depends(get_connection),
) -> FileResponse:
    overview = require_protein(connection, acc)
    accession = str(overview["uniprot_accession"])
    rows = manifest_rows(accession)
    matches = [row for row in rows if int(row["fragment_number"]) == fragment]
    if not matches:
        raise HTTPException(status_code=404, detail=f"AlphaFold structure fragment not found: F{fragment}")
    if len(matches) != 1:
        raise HTTPException(status_code=500, detail="Duplicate AlphaFold structure fragment")
    row = matches[0]
    path = safe_structure_file(row, accession)
    return FileResponse(
        path,
        media_type="application/gzip",
        filename=str(row["filename"]),
        headers={"Cache-Control": IMMUTABLE_CACHE_CONTROL},
        stat_result=path.stat(),
    )
