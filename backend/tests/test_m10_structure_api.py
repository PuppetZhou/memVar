import gzip
from pathlib import Path

import duckdb
from fastapi.testclient import TestClient
import pytest

from app import structure
from app.main import app


client = TestClient(app)
P00533_DOWNLOAD = "/api/v1/proteins/P00533/structures/1/pdb"


def test_p00533_structure_list_and_lowercase_accession_are_canonical() -> None:
    response = client.get("/api/v1/proteins/P00533/structures")
    lowercase = client.get("/api/v1/proteins/p00533/structures")
    assert response.status_code == lowercase.status_code == 200
    assert response.json() == lowercase.json()

    body = response.json()
    assert body == {
        "uniprot_accession": "P00533",
        "availability": "available",
        "source": "AlphaFold DB",
        "model_version": 6,
        "fragment_total": 1,
        "fragments": [
            {
                "fragment_number": 1,
                "fragment_label": "F1",
                "filename": "AF-P00533-F1-model_v6.pdb.gz",
                "compressed_bytes": 170008,
                "uncompressed_bytes": 772334,
                "canonical_start": 1,
                "canonical_end": 1210,
                "content_url": P00533_DOWNLOAD,
                "download_url": P00533_DOWNLOAD,
            }
        ],
    }
    assert response.headers["cache-control"] == "no-store"


def test_q8wxi7_fragments_are_complete_and_sorted_numerically() -> None:
    response = client.get("/api/v1/proteins/Q8WXI7/structures")
    assert response.status_code == 200
    body = response.json()
    assert body["availability"] == "available"
    assert body["fragment_total"] == len(body["fragments"]) == 67
    assert [item["fragment_number"] for item in body["fragments"]] == list(range(1, 68))
    assert [item["fragment_label"] for item in body["fragments"][:12]] == [
        f"F{number}" for number in range(1, 13)
    ]
    assert body["fragments"][0]["canonical_start"] == 1
    assert body["fragments"][0]["canonical_end"] == 1400


def test_missing_structure_is_an_explicit_available_protein_empty_state() -> None:
    response = client.get("/api/v1/proteins/O43687/structures")
    assert response.status_code == 200
    assert response.json() == {
        "uniprot_accession": "O43687",
        "availability": "unavailable",
        "source": "AlphaFold DB",
        "model_version": 6,
        "fragment_total": 0,
        "fragments": [],
    }
    assert client.get("/api/v1/proteins/O43687/structures/1/pdb").status_code == 404


def test_pdb_download_get_head_range_and_immutable_cache() -> None:
    response = client.get(P00533_DOWNLOAD)
    assert response.status_code == 200
    assert response.content[:2] == b"\x1f\x8b"
    assert response.headers["content-type"] == "application/gzip"
    assert response.headers["content-disposition"] == (
        'attachment; filename="AF-P00533-F1-model_v6.pdb.gz"'
    )
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert int(response.headers["content-length"]) == len(response.content) == 170008
    assert gzip.decompress(response.content).startswith(b"HEADER")

    head = client.head(P00533_DOWNLOAD)
    assert head.status_code == 200
    assert head.content == b""
    assert head.headers["content-length"] == "170008"
    assert head.headers["accept-ranges"] == "bytes"

    ranged = client.get(P00533_DOWNLOAD, headers={"Range": "bytes=0-99"})
    assert ranged.status_code == 206
    assert len(ranged.content) == 100
    assert ranged.content == response.content[:100]
    assert ranged.headers["content-range"] == "bytes 0-99/170008"
    assert ranged.headers["accept-ranges"] == "bytes"
    assert ranged.headers["cache-control"] == "public, max-age=31536000, immutable"


@pytest.mark.parametrize(
    ("url", "expected_status"),
    [
        ("/api/v1/proteins/NOT_A_PROTEIN/structures", 404),
        ("/api/v1/proteins/P00533/structures/0/pdb", 422),
        ("/api/v1/proteins/P00533/structures/-1/pdb", 422),
        ("/api/v1/proteins/P00533/structures/not-a-number/pdb", 422),
        ("/api/v1/proteins/P00533/structures/2/pdb", 404),
        ("/api/v1/proteins/%2E%2E%2Fetc%2Fpasswd/structures", 404),
    ],
)
def test_invalid_protein_and_fragment_paths_are_rejected(url: str, expected_status: int) -> None:
    assert client.get(url).status_code == expected_status


def write_manifest(path: Path, rows: list[tuple[object, ...]]) -> None:
    connection = duckdb.connect()
    try:
        connection.execute(
            """
            CREATE TABLE manifest (
                uniprot_accession VARCHAR, fragment_number INTEGER, fragment_label VARCHAR,
                filename VARCHAR, relative_path VARCHAR, compressed_bytes BIGINT,
                uncompressed_bytes BIGINT, gzip_sha256 VARCHAR, pdb_sha256 VARCHAR,
                canonical_start BIGINT, canonical_end BIGINT, model_version INTEGER,
                source VARCHAR
            )
            """
        )
        connection.executemany(
            "INSERT INTO manifest VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows
        )
        connection.execute("COPY manifest TO ? (FORMAT PARQUET)", [str(path)])
    finally:
        connection.close()


def test_manifest_symlink_is_never_served(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "v6"
    protein_dir = root / "P43627"
    protein_dir.mkdir(parents=True)
    target = root / "real.pdb.gz"
    target.write_bytes(gzip.compress(b"HEADER test\n"))
    filename = "AF-P43627-F1-model_v6.pdb.gz"
    (protein_dir / filename).symlink_to(target)
    manifest = root / "manifest.parquet"
    write_manifest(
        manifest,
        [
            (
                "P43627", 1, "F1", filename, f"P43627/{filename}", target.stat().st_size,
                len(b"HEADER test\n"), "0" * 64, "1" * 64, 1, 1, 6, "AlphaFold DB",
            )
        ],
    )
    monkeypatch.setattr(structure, "structure_root", lambda: root)

    response = client.get("/api/v1/proteins/P43627/structures/1/pdb")
    assert response.status_code == 500
    assert response.json()["detail"] == "Unsafe AlphaFold structure symlink"


def test_manifest_path_escape_is_never_served(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "v6"
    root.mkdir()
    escaped = tmp_path / "AF-P43627-F1-model_v6.pdb.gz"
    escaped.write_bytes(gzip.compress(b"HEADER outside root\n"))
    manifest = root / "manifest.parquet"
    write_manifest(
        manifest,
        [
            (
                "P43627", 1, "F1", escaped.name, f"../{escaped.name}", escaped.stat().st_size,
                len(b"HEADER outside root\n"), "0" * 64, "1" * 64, 1, 1, 6,
                "AlphaFold DB",
            )
        ],
    )
    monkeypatch.setattr(structure, "structure_root", lambda: root)

    response = client.get("/api/v1/proteins/P43627/structures/1/pdb")
    assert response.status_code == 500
    assert response.json()["detail"] == "Invalid AlphaFold structure manifest row"
