"""Compact prebuilt statistics, guarded against a different active data snapshot."""
from functools import lru_cache
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from .db import query

router = APIRouter(prefix='/api', tags=['catalog'])
STATISTICS = Path(__file__).resolve().parents[2] / 'data/catalog_statistics.json'
VERSION_SQL = """SELECT 'proteins' module,manifest->>'data_version' version FROM web._build_manifest
UNION ALL SELECT 'variants',data_version FROM web_variant._build_manifest
UNION ALL SELECT 'context',data_version FROM web_context._build_manifest
UNION ALL SELECT 'diseases',data_version FROM web_disease._build_manifest
UNION ALL SELECT 'interface',data_version FROM web_interface._build_manifest"""


@lru_cache(maxsize=1)
def load_statistics(modified_ns):
    return json.loads(STATISTICS.read_text())


@router.get('/catalog/statistics')
def catalog_statistics():
    try:
        result = load_statistics(STATISTICS.stat().st_mtime_ns)
    except (OSError, ValueError):
        raise HTTPException(503, 'Catalog statistics are not available for this snapshot.') from None
    expected = {v['module']: v['service_version'] for v in result['versions']}
    active = {v['module']: v['version'] for v in query(VERSION_SQL)}
    if active != expected:
        raise HTTPException(503, 'Catalog statistics need to be refreshed for the current data snapshot.')
    return result
