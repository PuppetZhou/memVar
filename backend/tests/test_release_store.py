import json
from pathlib import Path

import pytest

from app.release_store import ReleaseStore, release_store
from app.store import database_path


def write_release(root: Path, *, required_assets: list[str] | None = None) -> None:
    (root / "catalog").mkdir(parents=True, exist_ok=True)
    (root / "catalog" / "core.duckdb").touch()
    (root / "catalog" / "m3.duckdb").touch()
    (root / "catalog" / "m4.duckdb").touch()
    (root / "facts" / "sequence").mkdir(parents=True, exist_ok=True)
    (root / "facts" / "qtl").mkdir(parents=True, exist_ok=True)
    (root / "facts" / "interaction").mkdir(parents=True, exist_ok=True)
    (root / "facts" / "interaction_mutation").mkdir(parents=True, exist_ok=True)
    (root / "facts" / "differential_expression").mkdir(parents=True, exist_ok=True)
    (root / "facts" / "differential_expression" / "memvar_de.duckdb").touch()
    (root / "assets" / "alphagenome").mkdir(parents=True, exist_ok=True)
    (root / "assets" / "alphagenome" / "alphagenome_catalog.duckdb").touch()
    (root / "assets" / "alphagenome" / "build_manifest.json").write_text("{}", encoding="utf-8")
    (root / "assets" / "structure").mkdir(parents=True, exist_ok=True)
    (root / "assets" / "structure" / "manifest.parquet").touch()
    (root / "assets" / "anatomy").mkdir(parents=True, exist_ok=True)
    (root / "assets" / "anatomy" / "anatomy_summary.parquet").touch()
    (root / "RELEASE.json").write_text(
        json.dumps(
            {
                "release_id": root.name,
                "schema_version": 1,
                "required_assets": required_assets or [
                    "catalog/core.duckdb", "catalog/m3.duckdb", "catalog/m4.duckdb",
                    "facts/sequence", "facts/qtl", "facts/interaction", "facts/interaction_mutation",
                    "facts/differential_expression/memvar_de.duckdb", "assets/structure/manifest.parquet",
                    "assets/alphagenome/alphagenome_catalog.duckdb", "assets/alphagenome/build_manifest.json",
                    "assets/anatomy/anatomy_summary.parquet",
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "_READY").touch()


def test_open_exposes_release_relative_typed_paths(tmp_path: Path) -> None:
    root = tmp_path / "serve-v1.0.0"
    write_release(root)

    store = ReleaseStore.open(root)

    assert store.release_id == "serve-v1.0.0"
    assert store.schema_version == 1
    assert store.core_database == root / "catalog" / "core.duckdb"
    assert store.m3_database == root / "catalog" / "m3.duckdb"
    assert store.m4_database == root / "catalog" / "m4.duckdb"
    assert store.sequence_projection == root / "facts" / "sequence"
    assert store.qtl_facts == root / "facts" / "qtl"
    assert store.interaction_facts == root / "facts" / "interaction"
    assert store.interaction_mutation_facts == root / "facts" / "interaction_mutation"
    assert store.differential_expression_assets == root / "facts" / "differential_expression"
    assert store.alphagenome_assets == root / "assets" / "alphagenome"
    assert store.structure_assets == root / "assets" / "structure"
    assert store.anatomy_assets == root / "assets" / "anatomy"
    assert store.anatomy_summary == root / "assets" / "anatomy" / "anatomy_summary.parquet"


@pytest.mark.parametrize("missing", ["_READY", "RELEASE.json"])
def test_open_rejects_an_unpublished_release(tmp_path: Path, missing: str) -> None:
    root = tmp_path / "serve-v1.0.0"
    write_release(root)
    (root / missing).unlink()

    with pytest.raises(RuntimeError, match="published|manifest"):
        ReleaseStore.open(root)


def test_open_rejects_a_missing_or_unsafe_required_asset(tmp_path: Path) -> None:
    root = tmp_path / "serve-v1.0.0"
    write_release(root, required_assets=["facts/variant"])
    with pytest.raises(RuntimeError, match="required asset is missing"):
        ReleaseStore.open(root)

    write_release(root, required_assets=["../outside"])
    with pytest.raises(RuntimeError, match="unsafe"):
        ReleaseStore.open(root)


def test_environment_store_validates_the_configured_mount_uuid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "serve-v1.0.0"
    write_release(root)
    monkeypatch.setenv("MEMVAR_DATA_ROOT", str(root))
    monkeypatch.setenv("MEMVAR_DATA_UUID", "expected-uuid")
    monkeypatch.setattr("app.release_store.mounted_uuid", lambda path: "expected-uuid")
    release_store.cache_clear()

    assert release_store().root == root
    monkeypatch.setenv("MEMVAR_CORE_DB", str(tmp_path / "ignored.duckdb"))
    assert database_path() == root / "catalog" / "core.duckdb"

    release_store.cache_clear()
    monkeypatch.setattr("app.release_store.mounted_uuid", lambda path: "other-uuid")
    with pytest.raises(RuntimeError, match="UUID"):
        release_store()


def test_runtime_data_adapters_resolve_only_from_the_configured_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.alphagenome import alphagenome_root
    from app.de import de_database_path, de_root
    from app.m3 import m3_database_path, m3_root
    from app.m4 import m4_database_path
    from app.structure import structure_root

    root = tmp_path / "serve-v1.0.0"
    write_release(root)
    monkeypatch.setenv("MEMVAR_DATA_ROOT", str(root))
    monkeypatch.setenv("MEMVAR_DATA_UUID", "expected-uuid")
    monkeypatch.setattr("app.release_store.mounted_uuid", lambda path: "expected-uuid")
    release_store.cache_clear()
    try:
        assert m3_database_path() == root / "catalog" / "m3.duckdb"
        assert m3_root() == root / "facts" / "qtl"
        assert m4_database_path() == root / "catalog" / "m4.duckdb"
        assert de_root() == root / "facts" / "differential_expression"
        assert de_database_path() == root / "facts" / "differential_expression" / "memvar_de.duckdb"
        assert structure_root() == root / "assets" / "structure"
        assert alphagenome_root() == root / "assets" / "alphagenome"
    finally:
        release_store.cache_clear()
