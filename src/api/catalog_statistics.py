"""Compact prebuilt statistics, guarded against a different active data snapshot."""
from functools import lru_cache
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from .db import backend, engine, query
from .resources import resource_path

router = APIRouter(prefix='/api', tags=['catalog'])
STATISTICS = resource_path('catalog_statistics', 'MEMVAR_CATALOG_STATISTICS', 'data/catalog_statistics.json')
VERSION_SQL = """SELECT 'proteins' module,manifest->>'data_version' version FROM web._build_manifest
UNION ALL SELECT 'variants',data_version FROM web_variant._build_manifest
UNION ALL SELECT 'context',data_version FROM web_context._build_manifest
UNION ALL SELECT 'diseases',data_version FROM web_disease._build_manifest
UNION ALL SELECT 'interface',data_version FROM web_interface._build_manifest"""


@lru_cache(maxsize=1)
def load_statistics(path: str, modified_ns: int):
    return json.loads(Path(path).read_text())


@router.get('/catalog/statistics')
def catalog_statistics():
    path = (resource_path('catalog_statistics', 'MEMVAR_CATALOG_STATISTICS',
                          str(engine().path.parent / 'catalog_statistics.json'))
            if backend() == 'duckdb' else STATISTICS)
    try:
        result = load_statistics(str(path), path.stat().st_mtime_ns)
    except (OSError, ValueError):
        raise HTTPException(503, 'Catalog statistics are not available for this snapshot.') from None
    expected = {v['module']: v['service_version'] for v in result['versions']}
    active = {v['module']: v['version'] for v in query(VERSION_SQL)}
    if active != expected:
        raise HTTPException(503, 'Catalog statistics need to be refreshed for the current data snapshot.')
    return result
