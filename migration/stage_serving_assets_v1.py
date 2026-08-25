#!/home/xuyzh/miniconda3/bin/python
"""Resume and validate the v1.0 serving-asset copy after the raw AlphaGenome copy."""

from __future__ import annotations

import argparse
import filecmp
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import duckdb
import pyarrow.parquet as parquet


EXPECTED_UUID = "9894627C94625D2E"
MOUNT = Path("/media/xuyzh/Newsmy")
SOURCE = Path("/home/xuyzh/memVar/website/data/generated")
STAGING = MOUNT / "memvar-data/.staging/serve-v1.0.0-foundation"
RAW_UNIT = "memvar-alphagenome-source-v1.service"
RAW_SOURCE = Path("/media/xuyzh/Newsmy1/alpha-predict/alphagenome_1mb_by_gene")
RAW_PARTIAL = MOUNT / "memvar-data/.staging/source-v1.0.0/alphagenome/alphagenome_1mb_by_gene.partial"
RAW_FINAL = MOUNT / "memvar-data/.staging/source-v1.0.0/alphagenome/alphagenome_1mb_by_gene"
RAW_EXPECTED_FILES = 46_285
RAW_EXPECTED_BYTES = 2_764_008_820_308

ASSETS = (
    (SOURCE / "memvar_m3.duckdb", STAGING / "catalog/m3.duckdb"),
    (SOURCE / "memvar_m4.duckdb", STAGING / "catalog/m4.duckdb"),
    (SOURCE / "qtl", STAGING / "facts/qtl"),
    (SOURCE / "interaction", STAGING / "facts/interaction"),
    (SOURCE / "interaction_mutation", STAGING / "facts/interaction_mutation"),
    (SOURCE / "differential_expression", STAGING / "facts/differential_expression"),
    (SOURCE / "structure/alphafold/v6", STAGING / "assets/structure"),
    (SOURCE / "anatomy", STAGING / "assets/anatomy"),
    (SOURCE / "alphagenome", STAGING / "assets/alphagenome"),
)


def log(message: str) -> None:
    print(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {message}", flush=True)


def command(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, text=True, capture_output=capture)


def mounted_identity() -> tuple[str, str]:
    result = command(
        "findmnt", "--noheadings", "--output", "UUID,FSTYPE", "--target", str(MOUNT), capture=True
    )
    fields = result.stdout.split()
    if len(fields) != 2:
        raise RuntimeError(f"Cannot determine target mount identity: {MOUNT}")
    return fields[0], fields[1]


def tree_inventory(root: Path) -> dict[str, int]:
    inventory: dict[str, int] = {}
    for directory, _, names in os.walk(root):
        base = Path(directory)
        for name in names:
            path = base / name
            if path.is_symlink():
                raise RuntimeError(f"Symlink is not allowed in a frozen asset: {path}")
            inventory[path.relative_to(root).as_posix()] = path.stat().st_size
    return inventory


def inventory_summary(root: Path) -> tuple[int, int]:
    inventory = tree_inventory(root)
    return len(inventory), sum(inventory.values())


def require_unpublished() -> None:
    if (STAGING / "_READY").exists():
        raise RuntimeError("Refusing to mutate a staging tree containing _READY")


def checksum_equivalent(source: Path, target: Path) -> None:
    log(f"checksum verification started: {source} -> {target}")
    source_arg = f"{source}/" if source.is_dir() else str(source)
    target_arg = f"{target}/" if target.is_dir() else str(target)
    result = subprocess.run(
        ["rsync", "-rcn", "--delete", "--itemize-changes", source_arg, target_arg],
        check=False,
        capture_output=True,
        text=True,
    )
    differences = result.stdout.strip()
    if result.returncode != 0 or differences:
        preview = "\n".join(differences.splitlines()[:20])
        raise RuntimeError(
            f"Checksum verification failed: {source} -> {target}; "
            f"rsync_status={result.returncode}; differences={preview}"
        )
    log(f"checksum verification passed: {source} -> {target}")


def validate_equivalent(source: Path, target: Path) -> None:
    if not target.exists() or source.is_dir() != target.is_dir():
        raise RuntimeError(f"Target type conflicts with source: {target}")
    if source.is_dir():
        if tree_inventory(source) != tree_inventory(target):
            raise RuntimeError(f"Target differs by relative path or size: {target}")
    elif not filecmp.cmp(source, target, shallow=False):
        raise RuntimeError(f"Target file differs from source: {target}")
    checksum_equivalent(source, target)


def require_layout() -> int:
    uuid, filesystem = mounted_identity()
    if uuid != EXPECTED_UUID or filesystem != "ntfs3":
        raise RuntimeError(f"Wrong target filesystem for {MOUNT}: UUID={uuid} FSTYPE={filesystem}")
    if not SOURCE.is_dir() or not STAGING.is_dir():
        raise RuntimeError("Generated source or serving staging root is missing")
    require_unpublished()

    total = 0
    if len({target for _, target in ASSETS}) != len(ASSETS):
        raise RuntimeError("Serving asset plan contains duplicate targets")
    for source, target in ASSETS:
        if not source.exists():
            raise RuntimeError(f"Required source is missing: {source}")
        files, size = (
            inventory_summary(source) if source.is_dir() else (1, source.stat().st_size)
        )
        partial = target.with_name(target.name + ".partial")
        if target.exists() and partial.exists():
            raise RuntimeError(f"Both final and partial staging assets exist: {target}")
        if target.exists():
            log(f"existing target will be checksum-verified after the raw copy: {target}")
        else:
            total += size
            log(f"planned {source} -> {target}: files={files} bytes={size}")

    available = shutil.disk_usage(MOUNT).free
    if available < total + 10 * 1024**3:
        raise RuntimeError(f"Insufficient target capacity: need={total} available={available}")
    log(f"target UUID={EXPECTED_UUID} available_bytes={available} planned_bytes={total}")
    return total


def unit_properties() -> dict[str, str]:
    result = subprocess.run(
        [
            "systemctl", "--user", "show", RAW_UNIT,
            "--property=LoadState", "--property=ActiveState", "--property=Result",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )


def wait_for_raw_copy() -> None:
    next_report = 0.0
    while unit_properties().get("ActiveState") in {"active", "activating", "deactivating"}:
        now = time.monotonic()
        if now >= next_report:
            log(f"waiting for {RAW_UNIT}; no serving assets are being read or written")
            next_report = now + 600
        time.sleep(30)

    properties = unit_properties()
    if properties.get("LoadState") == "loaded" and properties.get("Result") not in {"", "success"}:
        raise RuntimeError(f"Raw copy unit did not succeed: {properties}")

    if RAW_FINAL.exists() and RAW_PARTIAL.exists():
        raise RuntimeError("Both final and partial raw AlphaGenome staging directories exist")
    raw_target = RAW_FINAL if RAW_FINAL.exists() else RAW_PARTIAL
    if not raw_target.is_dir():
        raise RuntimeError(f"Raw AlphaGenome staging directory is missing: {raw_target}")

    log(f"raw copy is inactive; validating relative paths and sizes: {raw_target}")
    source_inventory = tree_inventory(RAW_SOURCE)
    target_inventory = tree_inventory(raw_target)
    if len(source_inventory) != RAW_EXPECTED_FILES or sum(source_inventory.values()) != RAW_EXPECTED_BYTES:
        raise RuntimeError("Raw AlphaGenome source no longer matches the audited v1.0 inventory")
    if target_inventory != source_inventory:
        raise RuntimeError("Raw AlphaGenome destination does not match source paths and sizes")
    checksum_equivalent(RAW_SOURCE, raw_target)
    log(f"raw copy validated: files={RAW_EXPECTED_FILES} bytes={RAW_EXPECTED_BYTES}")
    if raw_target == RAW_PARTIAL:
        if mounted_identity() != (EXPECTED_UUID, "ntfs3"):
            raise RuntimeError("Target mount identity changed during raw checksum verification")
        ready = RAW_PARTIAL.parents[1] / "_READY"
        if ready.exists():
            raise RuntimeError(f"Refusing staging rename because source _READY exists: {ready}")
        RAW_PARTIAL.rename(RAW_FINAL)
        log(f"raw staging directory renamed atomically: {RAW_PARTIAL} -> {RAW_FINAL}")
    else:
        log(f"raw staging directory already has its stable name: {RAW_FINAL}")


def validate_duckdb(path: Path) -> None:
    connection = duckdb.connect(str(path), read_only=True)
    try:
        connection.execute("SELECT count(*) FROM information_schema.tables").fetchone()
    finally:
        connection.close()


def validate_formats(root: Path, *, source_suffix: str | None = None) -> None:
    if root.is_file():
        if source_suffix == ".duckdb" or root.suffix == ".duckdb":
            validate_duckdb(root)
        return

    parquet_count = 0
    for path in sorted(root.rglob("*.parquet")):
        parquet.ParquetFile(path).metadata
        parquet_count += 1
    for path in sorted(root.rglob("*.duckdb")):
        validate_duckdb(path)
    for path in sorted(root.rglob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
    gzip_files = sorted(root.rglob("*.gz"))
    samples = gzip_files[:5] + gzip_files[-5:]
    for path in dict.fromkeys(samples):
        with gzip.open(path, "rb") as stream:
            if not stream.read():
                raise RuntimeError(f"Empty gzip payload: {path}")
    log(f"format validation passed for {root}: parquet_files={parquet_count} gzip_samples={len(set(samples))}")


def copy_file(source: Path, target: Path) -> None:
    partial = target.with_name(target.name + ".partial")
    target.parent.mkdir(parents=True, exist_ok=True)
    command(
        "rsync", "-t", "--partial", "--append-verify", "--info=stats2",
        str(source), str(partial),
    )
    validate_equivalent(source, partial)
    validate_formats(partial, source_suffix=source.suffix)
    require_unpublished()
    partial.rename(target)
    log(f"installed staging asset {target}: files=1 bytes={target.stat().st_size}")


def copy_tree(source: Path, target: Path) -> None:
    partial = target.with_name(target.name + ".partial")
    partial.mkdir(parents=True, exist_ok=True)
    command(
        "rsync", "-rt", "--partial", "--append-verify", "--info=stats2",
        f"{source}/", f"{partial}/",
    )
    source_inventory = tree_inventory(source)
    target_inventory = tree_inventory(partial)
    validate_equivalent(source, partial)
    validate_formats(partial)
    require_unpublished()
    partial.rename(target)
    log(
        f"installed staging asset {target}: files={len(target_inventory)} "
        f"bytes={sum(target_inventory.values())}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="validate source, target, UUID and capacity without writing"
    )
    args = parser.parse_args()
    require_layout()
    if args.check:
        log("preflight passed; no files were written")
        return

    wait_for_raw_copy()
    require_layout()
    for source, target in ASSETS:
        require_unpublished()
        if target.exists():
            validate_equivalent(source, target)
            validate_formats(target, source_suffix=source.suffix)
            log(f"validated existing staging asset {target}; skipping copy")
            continue
        log(f"copying {source} -> {target}")
        copy_tree(source, target) if source.is_dir() else copy_file(source, target)
    log("all requested serving assets are staged and validated; _READY was not created")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        log(f"FAILED: {error}")
        raise
