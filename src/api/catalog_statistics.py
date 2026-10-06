"""Compact prebuilt statistics, guarded against a different active data snapshot."""
from functools import lru_cache
import json
from copy import deepcopy
from collections import Counter
from pathlib import Path
from fastapi import APIRouter, HTTPException
from .db import engine, query
from ..runtime import catalog_path, statistics_path

router = APIRouter(prefix='/api', tags=['catalog'])
STATISTICS = statistics_path(catalog_path())
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
    path = statistics_path(engine().path)
    try:
        result = load_statistics(str(path), path.stat().st_mtime_ns)
    except (OSError, ValueError):
        raise HTTPException(503, 'Catalog statistics are not available for this snapshot.') from None
    expected = {v['module']: v['service_version'] for v in result['versions']}
    active = {v['module']: v['version'] for v in query(VERSION_SQL)}
    if active != expected:
        raise HTTPException(503, 'Catalog statistics need to be refreshed for the current data snapshot.')
    # Selector definitions are an API projection; keep their counts current without
    # rewriting or rescanning the immutable scientific data snapshot.
    from .evidence import prediction_dictionary, prediction_group
    definitions = prediction_dictionary()
    result = deepcopy(result)
    for section in result['sections']:
        if section['id'] != 'predictors':
            continue
        counts = {'tools':len({p['tool'] for p in definitions}), 'fields':len(definitions)}
        for metric in section['metrics']:
            if metric['key'] in counts:
                metric['value'] = counts[metric['key']]
        distributions = {
            'groups':Counter(prediction_group(p['field']) for p in definitions),
            'tools':Counter(p['tool'] for p in definitions),
            'scope':Counter(p['scope'].replace('_',' ') for p in definitions),
        }
        for breakdown in section['breakdowns']:
            if breakdown['key'] in distributions:
                breakdown['rows'] = [dict(label=label,value=value) for label,value in distributions[breakdown['key']].items()]
            if breakdown['key'] == 'scope':
                breakdown['note'] = 'Variant, transcript-consequence and protein-substitution scores retain their original association level.'
        section['notes'] = [note for note in section['notes'] if not note.startswith('ThermoMPNN ddG')]
        section['notes'].append('ThermoMPNN ΔΔG is selectable under Protein stability; linked substitution records retain their identities. Protein-interface predictions remain separate.')
    return result
