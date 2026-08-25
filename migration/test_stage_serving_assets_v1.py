from pathlib import Path

import pytest

from migration.stage_serving_assets_v1 import checksum_equivalent, tree_inventory


def test_checksum_equivalent_detects_same_size_content_change(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (source / "asset.bin").write_bytes(b"abcd")
    (target / "asset.bin").write_bytes(b"abce")

    assert tree_inventory(source) == tree_inventory(target)
    with pytest.raises(RuntimeError, match="Checksum verification failed"):
        checksum_equivalent(source, target)


def test_checksum_equivalent_accepts_identical_tree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (source / "asset.bin").write_bytes(b"content")
    (target / "asset.bin").write_bytes(b"content")

    checksum_equivalent(source, target)
