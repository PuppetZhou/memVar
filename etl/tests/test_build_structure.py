from __future__ import annotations

import gzip
import io
from pathlib import Path
import sys
import tarfile

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_structure as structure  # noqa: E402


def pdb_bytes(accession: str, canonical_start: int, canonical_end: int) -> bytes:
    fragment_length = canonical_end - canonical_start + 1
    return (
        "HEADER    SYNTHETIC ALPHAFOLD MODEL\n"
        f"DBREF  XXXX A    1  {fragment_length:4d}  UNP    {accession:<8} TEST_HUMAN   "
        f"{canonical_start:4d}  {canonical_end:4d}\n"
        "END\n"
    ).encode("ascii")


def make_archive(path: Path, fragments: list[tuple[str, int, int, int]]) -> None:
    with tarfile.open(path, "w", format=tarfile.USTAR_FORMAT) as archive:
        for accession, fragment, start, end in fragments:
            for extension in ("cif", "pdb"):
                raw = pdb_bytes(accession, start, end) if extension == "pdb" else b"data_test\n"
                compressed = gzip.compress(raw, mtime=0)
                name = f"AF-{accession}-F{fragment}-model_v6.{extension}.gz"
                info = tarfile.TarInfo(name)
                info.size = len(compressed)
                info.type = tarfile.REGTYPE
                archive.addfile(info, io.BytesIO(compressed))


def test_standard_archive_and_selected_extraction(tmp_path: Path) -> None:
    archive = tmp_path / "models.tar"
    make_archive(archive, [("P00533", 1, 1, 1210), ("Q8WXI7", 1, 1, 1400), ("Q8WXI7", 2, 201, 1600)])

    start, members = structure.find_archive_start(archive, recover_prefix=False)
    assert start == 0
    assert len(members) == 6

    output = tmp_path / "selected"
    output.mkdir()
    manifest, missing = structure.extract_selected(
        archive,
        members,
        {"P00533": 1210, "Q8WXI7": 14507, "O43687": 100},
        output,
    )
    structure.validate_generated(
        output,
        manifest,
        missing,
        {"P00533": 1210, "Q8WXI7": 14507, "O43687": 100},
        expected=None,
    )

    assert [(row["uniprot_accession"], row["fragment_label"]) for row in manifest] == [
        ("P00533", "F1"),
        ("Q8WXI7", "F1"),
        ("Q8WXI7", "F2"),
    ]
    assert [(row["canonical_start"], row["canonical_end"]) for row in manifest] == [
        (1, 1210),
        (1, 1400),
        (201, 1600),
    ]
    assert missing == ["O43687"]
    assert all(len(str(row["gzip_sha256"])) == 64 for row in manifest)
    assert all(len(str(row["pdb_sha256"])) == 64 for row in manifest)


def test_prefix_recovery_is_explicit_and_audited(tmp_path: Path) -> None:
    normal = tmp_path / "normal.tar"
    make_archive(normal, [("P00533", 1, 1, 1210)])
    damaged = tmp_path / "damaged-prefix.tar"
    damaged.write_bytes((b"damaged" + bytes(505)) + normal.read_bytes())

    with pytest.raises(structure.BuildError, match="refusing implicit recovery"):
        structure.find_archive_start(damaged, recover_prefix=False)

    start, members = structure.find_archive_start(
        damaged,
        recover_prefix=True,
        audited_recovery_offset=512,
    )
    assert start == 512
    assert len(members) == 2

    with pytest.raises(structure.BuildError, match="differs from the audited"):
        structure.find_archive_start(
            damaged,
            recover_prefix=True,
            audited_recovery_offset=1024,
        )


def test_inventory_rejects_fragment_gap_and_unpaired_member(tmp_path: Path) -> None:
    gap = tmp_path / "gap.tar"
    make_archive(gap, [("Q8WXI7", 1, 1, 1400), ("Q8WXI7", 3, 401, 1800)])
    gap_members = structure.validate_archive_from(gap, 0)
    gap_output = tmp_path / "gap-output"
    gap_output.mkdir()
    with pytest.raises(structure.BuildError, match="not contiguous"):
        structure.extract_selected(gap, gap_members, {"Q8WXI7": 2000}, gap_output)

    unpaired = tmp_path / "unpaired.tar"
    with tarfile.open(unpaired, "w", format=tarfile.USTAR_FORMAT) as archive:
        compressed = gzip.compress(pdb_bytes("P00533", 1, 1210), mtime=0)
        info = tarfile.TarInfo("AF-P00533-F1-model_v6.pdb.gz")
        info.size = len(compressed)
        archive.addfile(info, io.BytesIO(compressed))
    with pytest.raises(structure.BuildError, match="pairing is incomplete"):
        structure.validate_archive_from(unpaired, 0)


def test_selected_pdb_requires_valid_gzip_and_dbref(tmp_path: Path) -> None:
    archive = tmp_path / "bad.tar"
    with tarfile.open(archive, "w", format=tarfile.USTAR_FORMAT) as tar:
        for extension, payload in (("cif", gzip.compress(b"data_test\n", mtime=0)), ("pdb", b"bad gzip")):
            info = tarfile.TarInfo(f"AF-P00533-F1-model_v6.{extension}.gz")
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
    members = structure.validate_archive_from(archive, 0)
    output = tmp_path / "out"
    output.mkdir()
    with pytest.raises(structure.BuildError, match="gzip CRC/decompression failed"):
        structure.extract_selected(archive, members, {"P00533": 1210}, output)


def test_header_checksum_and_unsafe_names_are_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "models.tar"
    make_archive(archive, [("P00533", 1, 1, 1210)])
    content = bytearray(archive.read_bytes())
    content[0] ^= 1
    corrupt = tmp_path / "checksum.tar"
    corrupt.write_bytes(content)
    with pytest.raises(structure.BuildError, match="checksum mismatch"):
        structure.validate_archive_from(corrupt, 0)

    unsafe = tmp_path / "unsafe.tar"
    with tarfile.open(unsafe, "w", format=tarfile.USTAR_FORMAT) as tar:
        payload = gzip.compress(pdb_bytes("P00533", 1, 1210), mtime=0)
        info = tarfile.TarInfo("../AF-P00533-F1-model_v6.pdb.gz")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    with pytest.raises(structure.BuildError, match="Unsafe tar member path"):
        structure.validate_archive_from(unsafe, 0)

    symlink = tmp_path / "symlink.tar"
    with tarfile.open(symlink, "w", format=tarfile.USTAR_FORMAT) as tar:
        info = tarfile.TarInfo("AF-P00533-F1-model_v6.pdb.gz")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        tar.addfile(info)
    with pytest.raises(structure.BuildError, match="not a regular file"):
        structure.validate_archive_from(symlink, 0)
