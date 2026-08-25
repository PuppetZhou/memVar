#!/usr/bin/env python3
"""Build the AlphaFold v6 membrane-protein PDB release.

The source archive and View registry are immutable inputs.  The current source
archive has a damaged prefix, so recovery is opt-in with ``--recover-prefix``;
normal operation deliberately rejects it.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import gzip
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import uuid

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq


WEBSITE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WEBSITE_ROOT.parent
DEFAULT_ARCHIVE = PROJECT_ROOT / "structure" / "UP000005640_9606_HUMAN_v6.tar"
DEFAULT_REGISTRY = PROJECT_ROOT / "View" / "Basic_info" / "protein_basic.parquet"
GENERATED_ROOT = WEBSITE_ROOT / "data" / "generated"
DEFAULT_OUTPUT = GENERATED_ROOT / "structure" / "alphafold" / "v6"
AUDITED_RECOVERY_OFFSET = 5_696_512
BLOCK_SIZE = 512
MODEL_VERSION = 6
SOURCE_LABEL = "AlphaFold DB"

MEMBER_RE = re.compile(
    r"^AF-([A-Z0-9]+)-F([1-9][0-9]*)-model_v6\.(pdb|cif)\.gz$"
)
PDB_DBREF_RE = re.compile(
    rb"^DBREF\s+\S+\s+\S+\s+\d+\s+\d+\s+UNP\s+"
    rb"([A-Z0-9]+)\s+\S+\s+(\d+)\s+(\d+)\s*$"
)


class BuildError(RuntimeError):
    """A source or generated-data contract violation."""


@dataclass(frozen=True)
class ArchiveMember:
    name: str
    accession: str
    fragment_number: int
    extension: str
    data_offset: int
    compressed_bytes: int


@dataclass(frozen=True)
class ExpectedCounts:
    proteins: int
    available: int
    fragments: int
    missing: int


PRODUCTION_COUNTS = ExpectedCounts(7728, 7624, 8837, 104)


def fail(message: str) -> None:
    raise BuildError(message)


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def parse_octal(field: bytes, label: str, offset: int) -> int:
    value = field.rstrip(b"\0 ").lstrip(b" ")
    if not value:
        return 0
    if not re.fullmatch(rb"[0-7]+", value):
        fail(f"Invalid tar {label} at byte offset {offset}")
    return int(value, 8)


def parse_header(header: bytes, offset: int) -> ArchiveMember:
    if len(header) != BLOCK_SIZE:
        fail(f"Truncated tar header at byte offset {offset}")
    if header[257:262] != b"ustar":
        fail(f"Missing ustar header at byte offset {offset}")

    stored_checksum = parse_octal(header[148:156], "checksum", offset)
    calculated_checksum = sum(header[:148]) + (8 * ord(" ")) + sum(header[156:])
    if stored_checksum != calculated_checksum:
        fail(f"Tar header checksum mismatch at byte offset {offset}")

    type_flag = header[156:157]
    if type_flag not in (b"\0", b"0"):
        fail(f"Archive member at byte offset {offset} is not a regular file")
    if header[157:257].rstrip(b"\0"):
        fail(f"Archive member at byte offset {offset} has a link target")
    if header[345:500].rstrip(b"\0"):
        fail(f"Archive member at byte offset {offset} has an unexpected path prefix")

    raw_name = header[:100].split(b"\0", 1)[0]
    try:
        name = raw_name.decode("ascii")
    except UnicodeDecodeError as error:
        raise BuildError(f"Non-ASCII tar member at byte offset {offset}") from error
    if not name or PurePosixPath(name).name != name:
        fail(f"Unsafe tar member path at byte offset {offset}: {name!r}")
    match = MEMBER_RE.fullmatch(name)
    if not match:
        fail(f"Unexpected AlphaFold archive member name: {name!r}")

    size = parse_octal(header[124:136], "size", offset)
    return ArchiveMember(
        name=name,
        accession=match.group(1),
        fragment_number=int(match.group(2)),
        extension=match.group(3),
        data_offset=offset + BLOCK_SIZE,
        compressed_bytes=size,
    )


def validate_archive_from(archive: Path, start_offset: int) -> list[ArchiveMember]:
    archive_size = archive.stat().st_size
    if start_offset % BLOCK_SIZE:
        fail(f"Tar start is not 512-byte aligned: {start_offset}")
    members: list[ArchiveMember] = []
    seen_names: set[str] = set()
    position = start_offset

    with archive.open("rb") as stream:
        while True:
            if position + BLOCK_SIZE > archive_size:
                fail("Archive ended before the two required zero blocks")
            stream.seek(position)
            header = stream.read(BLOCK_SIZE)
            if header == bytes(BLOCK_SIZE):
                second = stream.read(BLOCK_SIZE)
                if second != bytes(BLOCK_SIZE):
                    fail(f"Tar has only one zero terminator block at byte offset {position}")
                trailing = stream.read()
                if trailing.strip(b"\0"):
                    fail("Non-zero data follows the tar terminator")
                break

            member = parse_header(header, position)
            if member.name in seen_names:
                fail(f"Duplicate archive member: {member.name}")
            seen_names.add(member.name)
            data_blocks = (member.compressed_bytes + BLOCK_SIZE - 1) // BLOCK_SIZE
            next_position = member.data_offset + data_blocks * BLOCK_SIZE
            if next_position > archive_size:
                fail(f"Archive member extends beyond end of file: {member.name}")
            members.append(member)
            position = next_position

    if not members:
        fail("Archive contains no AlphaFold members")
    validate_archive_inventory(members)
    return members


def validate_archive_inventory(members: list[ArchiveMember]) -> None:
    inventory: dict[tuple[str, int], set[str]] = {}
    for member in members:
        key = (member.accession, member.fragment_number)
        inventory.setdefault(key, set()).add(member.extension)
    unpaired = sorted(key for key, extensions in inventory.items() if extensions != {"pdb", "cif"})
    if unpaired:
        fail(f"PDB/CIF pairing is incomplete for {len(unpaired)} fragments")


def find_archive_start(
    archive: Path,
    recover_prefix: bool,
    *,
    audited_recovery_offset: int = AUDITED_RECOVERY_OFFSET,
) -> tuple[int, list[ArchiveMember]]:
    try:
        return 0, validate_archive_from(archive, 0)
    except BuildError as normal_error:
        if not recover_prefix:
            raise BuildError(
                "Source is not a standard tar archive; refusing implicit recovery. "
                "Use --recover-prefix only for an audited damaged prefix. "
                f"Initial error: {normal_error}"
            ) from normal_error

    archive_size = archive.stat().st_size
    with archive.open("rb") as stream:
        for offset in range(BLOCK_SIZE, archive_size - BLOCK_SIZE + 1, BLOCK_SIZE):
            stream.seek(offset + 257)
            if stream.read(5) != b"ustar":
                continue
            try:
                members = validate_archive_from(archive, offset)
            except BuildError:
                continue
            if offset != audited_recovery_offset:
                fail(
                    "Recovered tar start differs from the audited source contract: "
                    f"expected {audited_recovery_offset}, observed {offset}"
                )
            return offset, members
    fail("No complete, aligned tar stream with a valid terminator was found")


def load_allowlist(registry: Path) -> dict[str, int]:
    if not registry.is_file():
        fail(f"Protein registry does not exist: {registry}")
    connection = duckdb.connect()
    try:
        description = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)", [str(registry)]
        ).fetchall()
        columns = {row[0] for row in description}
        required = {"uniprot_accession", "canonical_length"}
        if not required <= columns:
            fail(f"Protein registry is missing columns: {', '.join(sorted(required - columns))}")
        rows = connection.execute(
            "SELECT uniprot_accession, canonical_length FROM read_parquet(?) ORDER BY 1",
            [str(registry)],
        ).fetchall()
    finally:
        connection.close()

    allowlist: dict[str, int] = {}
    for accession, canonical_length in rows:
        if not isinstance(accession, str) or not re.fullmatch(r"[A-Z0-9]+", accession):
            fail(f"Invalid canonical accession in protein registry: {accession!r}")
        if accession in allowlist:
            fail(f"Duplicate canonical accession in protein registry: {accession}")
        if not isinstance(canonical_length, int) or canonical_length <= 0:
            fail(f"Invalid canonical length for {accession}: {canonical_length!r}")
        allowlist[accession] = canonical_length
    if not allowlist:
        fail("Protein registry is empty")
    return allowlist


def parse_dbref(pdb: bytes, accession: str) -> tuple[int, int]:
    ranges: set[tuple[int, int]] = set()
    for line in pdb.splitlines():
        if not line.startswith(b"DBREF"):
            continue
        match = PDB_DBREF_RE.fullmatch(line.rstrip())
        if match and match.group(1).decode("ascii") == accession:
            ranges.add((int(match.group(2)), int(match.group(3))))
    if len(ranges) != 1:
        fail(f"Expected one unambiguous UniProt DBREF range for {accession}, found {sorted(ranges)}")
    start, end = next(iter(ranges))
    if start < 1 or end < start:
        fail(f"Invalid DBREF range for {accession}: {start}-{end}")
    return start, end


MANIFEST_SCHEMA = pa.schema(
    [
        ("uniprot_accession", pa.string()),
        ("fragment_number", pa.int32()),
        ("fragment_label", pa.string()),
        ("filename", pa.string()),
        ("relative_path", pa.string()),
        ("compressed_bytes", pa.int64()),
        ("uncompressed_bytes", pa.int64()),
        ("gzip_sha256", pa.string()),
        ("pdb_sha256", pa.string()),
        ("canonical_start", pa.int64()),
        ("canonical_end", pa.int64()),
        ("model_version", pa.int32()),
        ("source", pa.string()),
    ]
)
MISSING_SCHEMA = pa.schema([("uniprot_accession", pa.string())])


def write_parquet(rows: list[dict[str, object]], schema: pa.Schema, path: Path) -> None:
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, path, compression="zstd")


def extract_selected(
    archive: Path,
    members: list[ArchiveMember],
    allowlist: dict[str, int],
    temporary: Path,
) -> tuple[list[dict[str, object]], list[str]]:
    selected = sorted(
        (
            member
            for member in members
            if member.extension == "pdb" and member.accession in allowlist
        ),
        key=lambda member: (member.accession, member.fragment_number),
    )
    seen: set[tuple[str, int]] = set()
    selected_fragments: dict[str, set[int]] = {}
    manifest: list[dict[str, object]] = []

    with archive.open("rb") as stream:
        for index, member in enumerate(selected, 1):
            key = (member.accession, member.fragment_number)
            if key in seen:
                fail(f"Duplicate selected PDB fragment: {member.accession} F{member.fragment_number}")
            seen.add(key)
            selected_fragments.setdefault(member.accession, set()).add(member.fragment_number)

            stream.seek(member.data_offset)
            compressed = stream.read(member.compressed_bytes)
            if len(compressed) != member.compressed_bytes:
                fail(f"Truncated compressed member: {member.name}")
            try:
                pdb = gzip.decompress(compressed)
            except (gzip.BadGzipFile, EOFError, OSError) as error:
                raise BuildError(f"gzip CRC/decompression failed for {member.name}: {error}") from error
            canonical_start, canonical_end = parse_dbref(pdb, member.accession)

            accession_dir = temporary / member.accession
            accession_dir.mkdir(mode=0o755, exist_ok=True)
            destination = accession_dir / member.name
            with destination.open("xb") as output:
                output.write(compressed)

            relative_path = PurePosixPath(member.accession, member.name).as_posix()
            manifest.append(
                {
                    "uniprot_accession": member.accession,
                    "fragment_number": member.fragment_number,
                    "fragment_label": f"F{member.fragment_number}",
                    "filename": member.name,
                    "relative_path": relative_path,
                    "compressed_bytes": len(compressed),
                    "uncompressed_bytes": len(pdb),
                    "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
                    "pdb_sha256": hashlib.sha256(pdb).hexdigest(),
                    "canonical_start": canonical_start,
                    "canonical_end": canonical_end,
                    "model_version": MODEL_VERSION,
                    "source": SOURCE_LABEL,
                }
            )
            if index % 500 == 0 or index == len(selected):
                print(f"Validated and copied {index:,}/{len(selected):,} PDB fragments", file=sys.stderr)

    for accession, numbers in selected_fragments.items():
        if numbers != set(range(1, max(numbers) + 1)):
            fail(f"Selected PDB fragments are not contiguous for {accession}")
    missing = sorted(set(allowlist) - set(selected_fragments))
    return manifest, missing


def validate_generated(
    temporary: Path,
    manifest: list[dict[str, object]],
    missing: list[str],
    allowlist: dict[str, int],
    expected: ExpectedCounts | None,
) -> None:
    available = {str(row["uniprot_accession"]) for row in manifest}
    if available & set(missing):
        fail("Available and missing accession sets overlap")
    if available | set(missing) != set(allowlist):
        fail("Available and missing accession sets do not partition the canonical registry")
    if expected is not None:
        observed = ExpectedCounts(len(allowlist), len(available), len(manifest), len(missing))
        if observed != expected:
            fail(f"Production structure counts differ: expected {expected}, observed {observed}")

    expected_files = {str(row["relative_path"]) for row in manifest}
    actual_files = {
        path.relative_to(temporary).as_posix()
        for path in temporary.glob("*/*.pdb.gz")
        if path.is_file() and not path.is_symlink()
    }
    if actual_files != expected_files:
        fail("Generated PDB files do not exactly match the manifest")
    for row in manifest:
        path = temporary / str(row["relative_path"])
        if path.is_symlink() or not path.is_file():
            fail(f"Generated structure is not a regular file: {path}")
        if path.stat().st_size != row["compressed_bytes"]:
            fail(f"Generated structure size mismatch: {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != row["gzip_sha256"]:
            fail(f"Generated structure SHA-256 mismatch: {path}")


def publish(temporary: Path, target: Path) -> None:
    if not target.exists():
        os.replace(temporary, target)
        return
    backup = target.parent / f".{target.name}.previous.{uuid.uuid4().hex}"
    os.replace(target, backup)
    try:
        os.replace(temporary, target)
    except Exception:
        os.replace(backup, target)
        raise
    shutil.rmtree(backup)


def validate_paths(archive: Path, registry: Path, output: Path) -> tuple[Path, Path, Path]:
    archive = archive.resolve()
    registry = registry.resolve()
    output = output.resolve()
    generated_root = GENERATED_ROOT.resolve()
    view_root = (PROJECT_ROOT / "View").resolve()
    structure_root = (PROJECT_ROOT / "structure").resolve()
    if not archive.is_file():
        fail(f"Source archive does not exist: {archive}")
    if not registry.is_file():
        fail(f"Protein registry does not exist: {registry}")
    if not path_is_within(registry, view_root):
        fail(f"Protein registry must be inside immutable View: {registry}")
    if not path_is_within(archive, structure_root):
        fail(f"Source archive must be inside structure/: {archive}")
    if not path_is_within(output, generated_root):
        fail(f"Output must be inside website/data/generated: {output}")
    if path_is_within(output, view_root) or path_is_within(output, structure_root):
        fail(f"Refusing output in an immutable source tree: {output}")
    return archive, registry, output


def build(
    archive: Path,
    registry: Path,
    output: Path,
    *,
    recover_prefix: bool,
    expected: ExpectedCounts | None = PRODUCTION_COUNTS,
) -> Path:
    archive, registry, output = validate_paths(archive, registry, output)
    allowlist = load_allowlist(registry)
    start_offset, members = find_archive_start(archive, recover_prefix)
    recovered = start_offset != 0
    print(
        f"Archive validated: {len(members):,} members; start={start_offset:,}; "
        f"recovered_prefix={str(recovered).lower()}",
        file=sys.stderr,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.parent / f".{output.name}.building.{uuid.uuid4().hex}"
    temporary.mkdir(mode=0o755)
    try:
        manifest, missing = extract_selected(archive, members, allowlist, temporary)
        validate_generated(temporary, manifest, missing, allowlist, expected)
        write_parquet(manifest, MANIFEST_SCHEMA, temporary / "manifest.parquet")
        write_parquet(
            [{"uniprot_accession": accession} for accession in missing],
            MISSING_SCHEMA,
            temporary / "missing_accessions.parquet",
        )
        publish(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    print(
        f"Published AlphaFold v6 structures: {len(manifest):,} fragments for "
        f"{len({row['uniprot_accession'] for row in manifest}):,} proteins; "
        f"missing={len(missing):,}; "
        f"DBREF ranges beyond current registry length="
        f"{sum(int(row['canonical_end']) > allowlist[str(row['uniprot_accession'])] for row in manifest):,}; "
        f"recovered_prefix={str(recovered).lower()}",
        file=sys.stderr,
    )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--recover-prefix",
        action="store_true",
        help="Explicitly recover a complete aligned tar stream after an audited damaged prefix",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        target = build(
            args.archive,
            args.registry,
            args.output,
            recover_prefix=args.recover_prefix,
        )
    except (BuildError, duckdb.Error, OSError, pa.ArrowException) as error:
        print(f"build_structure failed: {error}", file=sys.stderr)
        return 1
    print(f"Built M10.1 AlphaFold structure release: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
