"""Validated paths for one immutable serving release."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import os
from pathlib import Path
import subprocess


def mounted_uuid(path: Path) -> str:
    """Return the UUID of the filesystem containing ``path``."""
    result = subprocess.run(
        ["findmnt", "--noheadings", "--output", "UUID", "--target", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    uuid = result.stdout.strip()
    if result.returncode != 0 or not uuid:
        raise RuntimeError(f"Cannot determine the filesystem UUID for data root: {path}")
    return uuid


@dataclass(frozen=True)
class ReleaseStore:
    """The read-only asset paths exposed by one published serving release."""

    root: Path
    release_id: str
    schema_version: int

    @classmethod
    def open(cls, root: Path, *, expected_uuid: str | None = None) -> "ReleaseStore":
        """Open a published release, optionally checking its mount identity.

        ``expected_uuid`` is omitted only by tests that construct a temporary
        release directory. Normal application startup always supplies it.
        """
        resolved_root = root.resolve()
        if not resolved_root.is_dir():
            raise RuntimeError(f"Serving release root is missing: {resolved_root}")
        if expected_uuid is not None and mounted_uuid(resolved_root) != expected_uuid:
            raise RuntimeError(f"Data mount UUID does not match MEMVAR_DATA_UUID: {resolved_root}")

        ready = resolved_root / "_READY"
        if not ready.is_file():
            raise RuntimeError(f"Serving release is not published (_READY is missing): {resolved_root}")

        manifest_path = resolved_root / "RELEASE.json"
        if not manifest_path.is_file():
            raise RuntimeError(f"Serving release manifest is missing: {manifest_path}")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Serving release manifest is invalid JSON: {manifest_path}") from error

        release_id = manifest.get("release_id")
        schema_version = manifest.get("schema_version")
        if not isinstance(release_id, str) or not release_id:
            raise RuntimeError(f"Serving release manifest has no release_id: {manifest_path}")
        if release_id != resolved_root.name:
            raise RuntimeError(f"Serving release ID does not match its directory: {resolved_root}")
        if not isinstance(schema_version, int):
            raise RuntimeError(f"Serving release manifest has no integer schema_version: {manifest_path}")

        store = cls(root=resolved_root, release_id=release_id, schema_version=schema_version)
        required_assets = manifest.get("required_assets", [])
        if not isinstance(required_assets, list) or not all(isinstance(asset, str) for asset in required_assets):
            raise RuntimeError(f"Serving release manifest has invalid required_assets: {manifest_path}")
        for asset in required_assets:
            if not store.path(asset).exists():
                raise RuntimeError(f"Serving release required asset is missing: {asset}")
        return store

    def path(self, relative_path: str) -> Path:
        """Return one release-relative path without allowing traversal."""
        relative = Path(relative_path)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise RuntimeError(f"Release asset path is unsafe: {relative_path}")
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise RuntimeError(f"Release asset path escapes the release root: {relative_path}")
        return path

    @property
    def core_database(self) -> Path:
        return self.path("catalog/core.duckdb")

    @property
    def variant_catalog(self) -> Path:
        return self.path("catalog/variant.duckdb")

    @property
    def m3_database(self) -> Path:
        return self.path("catalog/m3.duckdb")

    @property
    def m4_database(self) -> Path:
        return self.path("catalog/m4.duckdb")

    @property
    def sequence_projection(self) -> Path:
        return self.path("facts/sequence")

    @property
    def variant_facts(self) -> Path:
        return self.path("facts/variant")

    @property
    def variant_population_frequency(self) -> Path:
        return self.path("facts/variant-population-frequency")

    @property
    def qtl_facts(self) -> Path:
        return self.path("facts/qtl")

    @property
    def interaction_facts(self) -> Path:
        return self.path("facts/interaction")

    @property
    def interaction_mutation_facts(self) -> Path:
        return self.path("facts/interaction_mutation")

    @property
    def differential_expression_assets(self) -> Path:
        return self.path("facts/differential_expression")

    @property
    def structure_assets(self) -> Path:
        return self.path("assets/structure")

    @property
    def alphagenome_assets(self) -> Path:
        return self.path("assets/alphagenome")

    @property
    def anatomy_assets(self) -> Path:
        return self.path("assets/anatomy")

    @property
    def anatomy_summary(self) -> Path:
        return self.path("assets/anatomy/anatomy_summary.parquet")


@lru_cache
def release_store() -> ReleaseStore:
    """Resolve the configured release once for the lifetime of the process."""
    root = os.environ.get("MEMVAR_DATA_ROOT")
    expected_uuid = os.environ.get("MEMVAR_DATA_UUID")
    if not root:
        raise RuntimeError("MEMVAR_DATA_ROOT must name the exact serving release root")
    if not expected_uuid:
        raise RuntimeError("MEMVAR_DATA_UUID must name the data mount UUID")
    return ReleaseStore.open(Path(root), expected_uuid=expected_uuid)
