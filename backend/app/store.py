"""Read-only access to the website-owned core protein store."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb
from fastapi import HTTPException

from .release_store import release_store


def database_path() -> Path:
    """Resolve the core catalog from the configured immutable release."""
    return release_store().core_database


@contextmanager
def read_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    path = database_path()
    if not path.is_file():
        raise RuntimeError(f"M1 core database is missing: {path}")
    connection = duckdb.connect(str(path), read_only=True)
    try:
        yield connection
    finally:
        connection.close()


def get_connection() -> Iterator[duckdb.DuckDBPyConnection]:
    with read_connection() as connection:
        yield connection


def row_dict(
    cursor: duckdb.DuckDBPyConnection,
    query: str,
    parameters: list[object],
) -> dict[str, object] | None:
    result = cursor.execute(query, parameters)
    row = result.fetchone()
    if row is None:
        return None
    return dict(zip((column[0] for column in result.description), row, strict=True))


def require_protein(connection: duckdb.DuckDBPyConnection, accession: str) -> dict[str, object]:
    overview = row_dict(
        connection,
        "SELECT * FROM protein_overview WHERE uniprot_accession = ?",
        [accession.upper()],
    )
    if overview is None:
        raise HTTPException(status_code=404, detail=f"Canonical protein accession not found: {accession}")
    return overview
