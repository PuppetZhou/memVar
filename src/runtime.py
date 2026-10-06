"""Resolve the read-only website data package and its external resources."""
from __future__ import annotations

import os
import json
from pathlib import Path
import re
import sys

import yaml

WEB = Path(__file__).resolve().parents[1]


class RuntimeConfigurationError(RuntimeError):
    """The selected website data package is unavailable or inconsistent."""


def data_root() -> Path | None:
    value = os.environ.get('MEMVAR_DATA_ROOT') or yaml_config('duckdb.yaml').get('data_root')
    return configured_path(value) if value else None


def configured_path(value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else WEB / path).resolve()


def yaml_config(name: str) -> dict:
    try:
        result = yaml.safe_load((WEB / 'config' / name).read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeConfigurationError(f'Website runtime configuration {name} is unavailable.') from exc
    if not isinstance(result, dict):
        raise RuntimeConfigurationError(f'Website runtime configuration {name} is invalid.')
    return result


def catalog_path() -> Path:
    root = data_root()
    if root is not None:
        return root / 'catalog.duckdb'
    value = os.environ.get('MEMVAR_DUCKDB_PATH') or yaml_config('duckdb.yaml').get('catalog')
    if not value:
        raise RuntimeConfigurationError('The DuckDB service snapshot is not configured.')
    return configured_path(value)


def structure_root() -> Path:
    root = data_root()
    if root is not None:
        return root / 'structures'
    value = os.environ.get('MEMVAR_STRUCTURE_ROOT') or yaml_config('resources.yaml').get('structure_root')
    if not value:
        raise RuntimeConfigurationError('The structure resource is not configured.')
    return configured_path(value)


def alphagenome_root() -> Path:
    root = data_root()
    if root is not None:
        return root / 'alphagenome' / 'assets'
    value = os.environ.get('MEMVAR_ALPHAGENOME_REFERENCE_ROOT') or yaml_config('alphagenome.yaml').get('reference_root')
    if not value:
        raise RuntimeConfigurationError('The AlphaGenome reference resource is not configured.')
    return configured_path(value)


def statistics_path(catalog: Path) -> Path:
    root = data_root()
    if root is not None:
        return root / 'catalog_statistics.json'
    value = os.environ.get('MEMVAR_CATALOG_STATISTICS')
    return configured_path(value) if value else catalog.parent / 'catalog_statistics.json'


def check() -> None:
    """Check package entry files without scanning large Parquet or HDF5 data."""
    root = data_root()
    if root is None:
        required = [catalog_path(), statistics_path(catalog_path()),
                    structure_root() / 'manifest.parquet', alphagenome_root() / 'tiles']
    else:
        required = [root / name for name in (
            'package.json', 'catalog.duckdb', 'manifest.json', 'catalog_statistics.json',
            'source-record-files.json', 'structures/manifest.parquet',
            'alphagenome/manifest.json', 'alphagenome/genes.parquet',
            'alphagenome/protein_gene.parquet', 'alphagenome/tracks.parquet',
            'alphagenome/windows.parquet', 'alphagenome/assets/tiles')]
        for path in required:
            if not path.resolve().is_relative_to(root):
                raise RuntimeConfigurationError(f'Website data package path escapes MEMVAR_DATA_ROOT: {path}')
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeConfigurationError('Website data package entries are missing: ' + ', '.join(missing))
    if root is not None:
        try:
            marker = json.loads((root / 'package.json').read_text())
        except (OSError, ValueError) as exc:
            raise RuntimeConfigurationError('Website data package completion marker is invalid.') from exc
        if marker.get('status') != 'complete':
            raise RuntimeConfigurationError('Website data package is not complete.')
        import duckdb
        try:
            with duckdb.connect(str(root / 'catalog.duckdb'), read_only=True) as database:
                views = database.execute('SELECT sql FROM duckdb_views()').fetchall()
                paths = [match.replace("''", "'") for (sql,) in views
                         for match in re.findall(r"read_parquet\(\s*'((?:''|[^'])*)'", sql, re.IGNORECASE)]
                if not paths:
                    raise RuntimeConfigurationError('Website catalog has no Parquet view paths.')
                if any(not Path(path).resolve().is_relative_to(root) for path in paths):
                    raise RuntimeConfigurationError('Website catalog has Parquet view paths outside MEMVAR_DATA_ROOT; rebind it offline.')
                database.execute('SELECT accession FROM web.protein LIMIT 1').fetchone()
        except duckdb.Error as exc:
            raise RuntimeConfigurationError('Website catalog cannot read its Parquet data.') from exc


if __name__ == '__main__':
    if sys.argv[1:] != ['check']:
        raise SystemExit('Usage: python -m src.runtime check')
    try:
        check()
    except RuntimeConfigurationError as error:
        raise SystemExit(str(error)) from None
    print('Website data package entry files are available.')
