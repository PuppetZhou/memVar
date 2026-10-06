"""Capture and compare a bounded, full-value HTTP baseline for a portable site.

Run capture against the current read-only service before replacing its data.
The baseline and comparison report belong in ignored data/, not in Git.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


DEFAULT_PATHS = (
    '/api/health',
    '/api/catalog/statistics',
    '/api/proteins?query=EGFR&limit=5',
    '/api/proteins?limit=5&offset=5',
    '/api/proteins/P00533/overview',
    '/api/proteins/P00533/sequence',
    '/api/proteins/P00533/variants?limit=3&source=ClinVar',
    '/api/proteins/P00533/variants?limit=3&source=ClinVar&offset=3',
    '/api/proteins/P00533/variants/summary',
    '/api/proteins/P00533/structure/predictor-extrema?field=AlphaMissense_score',
    '/api/proteins/P00533/structure/predictor-records?field=AlphaMissense_score&limit=3',
    '/api/proteins/P00533/qtl?limit=3&source=QTLbase',
    '/api/proteins/P00533/diseases/summary',
    '/api/proteins/P00533/expression?limit=3&category=all',
    '/api/proteins/P00533/structures',
    '/api/proteins/P00533/expression/alphagenome',
)


def fetch(base: str, path: str, timeout: int) -> dict:
    started = perf_counter()
    try:
        with urlopen(base.rstrip('/') + path, timeout=timeout) as response:
            status = response.status
            raw = response.read()
            content_type = response.headers.get('Content-Type', '')
    except HTTPError as error:
        status = error.code
        raw = error.read()
        content_type = error.headers.get('Content-Type', '')
    except Exception as error:
        return {'status': 0, 'body': f'{type(error).__name__}: {error}',
                'seconds': perf_counter() - started}
    try:
        body = json.loads(raw) if 'json' in content_type else raw.decode('utf-8')
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return {'status': 0, 'body': f'Invalid response: {error}',
                'seconds': perf_counter() - started}
    return {'status': status, 'body': body, 'seconds': perf_counter() - started}


def discovered_paths(records: dict) -> list[str]:
    paths = []
    prefix = '/api/proteins/P00533'
    def body(path):
        record = records.get(path, {})
        value = record.get('body')
        return value if record.get('status') == 200 and isinstance(value, dict) else {}

    variants = body(prefix + '/variants?limit=3&source=ClinVar')
    if variants.get('items') and variants['items'][0].get('variant_id'):
        paths.append('/api/variants/' + str(variants['items'][0]['variant_id']) + '?accession=P00533')
    qtl = body(prefix + '/qtl?limit=3&source=QTLbase')
    if qtl.get('next_cursor'):
        paths.append(prefix + '/qtl?' + urlencode({'limit': 3, 'source': 'QTLbase',
                                                   'cursor': qtl['next_cursor']}))
    structures = body(prefix + '/structures')
    if structures.get('items'):
        paths.append(prefix + '/structures/' + str(structures['items'][0]['id']) + '/model.pdb')
    ag = body(prefix + '/expression/alphagenome')
    genes = [item for item in ag.get('genes', []) if item.get('tiles')]
    if genes:
        gene = genes[0]
        tile = gene['tiles'][0]
        paths.append(prefix + '/qtl/tracks?' + urlencode({'gene': gene['ensembl_gene_id']}))
        common = {'gene': gene['ensembl_gene_id'], 'tile': tile['tile_id'], 'bins': 16,
                  'limit': 3}
        for modality in ('rna_seq', 'contact_maps'):
            track = next((item for item in ag.get('tracks', [])
                          if item.get('modality') == modality), None)
            if track:
                path = prefix + '/expression/alphagenome/track?'
                paths.append(path + urlencode({**common, 'track_id': track['track_id']}))
                if modality == 'rna_seq':
                    paths.append(path + urlencode({**common, 'track_id': track['track_id'],
                        'start': tile['retention_start_0based'] - 1,
                        'end': tile['retention_end_0based']}))
    return paths


def differences(expected, actual, path='$', limit=20):
    if type(expected) is not type(actual):
        return [f'{path}: type {type(expected).__name__} != {type(actual).__name__}']
    if isinstance(expected, dict):
        result = ([f'{path}: keys differ {sorted(set(expected) ^ set(actual))}']
                  if set(expected) != set(actual) else [])
        for key in expected.keys() & actual.keys():
            result.extend(differences(expected[key], actual[key], path + '.' + key, limit))
            if len(result) >= limit:
                break
        return result[:limit]
    if isinstance(expected, list):
        result = ([f'{path}: length {len(expected)} != {len(actual)}']
                  if len(expected) != len(actual) else [])
        for index, (left, right) in enumerate(zip(expected, actual)):
            result.extend(differences(left, right, f'{path}[{index}]', limit))
            if len(result) >= limit:
                break
        return result[:limit]
    return [] if expected == actual else [f'{path}: {str(expected)[:100]} != {str(actual)[:100]}']


def write_json(path: Path, payload: dict, *, replace: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise FileExistsError(f'Output exists: {path}; pass --replace to overwrite it')
    temporary = path.with_name(path.name + '.writing')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    capture = sub.add_parser('capture', help='Record current read-only HTTP responses')
    capture.add_argument('--source-url', required=True)
    capture.add_argument('--baseline', type=Path, required=True)
    capture.add_argument('--paths-from', type=Path,
                         help='Capture exactly the paths in an earlier baseline')
    capture.add_argument('--replace', action='store_true')
    compare = sub.add_parser('compare', help='Compare a candidate with a saved baseline')
    compare.add_argument('--candidate-url', required=True)
    compare.add_argument('--baseline', type=Path, required=True)
    compare.add_argument('--report', type=Path, required=True)
    compare.add_argument('--replace', action='store_true')
    for command in (capture, compare):
        command.add_argument('--workers', type=int, default=4)
        command.add_argument('--timeout', type=int, default=60)
    args = parser.parse_args()
    if args.workers < 1 or args.timeout < 1:
        parser.error('--workers and --timeout must be positive')
    now = datetime.now(timezone.utc).isoformat()
    if args.command == 'capture':
        if args.baseline.exists() and not args.replace:
            parser.error('Baseline exists; pass --replace only when recapturing is intended')
        if args.paths_from:
            old_responses = json.loads(args.paths_from.read_text())['responses']
            paths = list(old_responses)
            expected_status = {path: old_responses[path]['status'] for path in paths}
        else:
            paths = list(DEFAULT_PATHS)
            expected_status = {path: 200 for path in paths}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            records = dict(zip(paths, pool.map(lambda path: fetch(args.source_url, path, args.timeout), paths)))
        if not args.paths_from:
            extra = [path for path in discovered_paths(records) if path not in records]
            expected_status.update({path: 422 if '/expression/alphagenome/track?' in path
                                    and '&start=' in path else 200 for path in extra})
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                records.update(zip(extra, pool.map(lambda path: fetch(args.source_url, path, args.timeout), extra)))
        failed = [f"{path}: expected {expected_status[path]}, got {record['status']}"
                  for path, record in records.items()
                  if record['status'] != expected_status[path]]
        if failed:
            print('Capture failed:', *failed, sep='\n  ')
            return 1
        write_json(args.baseline, {'captured_at': now, 'base': args.source_url,
                                   'responses': records}, replace=args.replace)
        print(f'Captured {len(records)} cases: {args.baseline}')
        return 0
    baseline = json.loads(args.baseline.read_text())
    if not isinstance(baseline.get('responses'), dict) or not baseline['responses']:
        parser.error('Baseline has no HTTP responses')
    paths = list(baseline['responses'])
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch, args.candidate_url, path, args.timeout): path for path in paths}
        actual = {futures[future]: future.result() for future in as_completed(futures)}
    results = {}
    for path in paths:
        old, new = baseline['responses'][path], actual[path]
        delta = differences(old['body'], new['body'])
        if old['status'] != new['status']:
            delta.insert(0, f"HTTP status {old['status']} != {new['status']}")
        if new['status'] == 0 and not delta:
            delta.append('No HTTP response from candidate')
        results[path] = {'status': new['status'], 'seconds': new['seconds'],
                         'differences': delta}
        print(('FAIL' if delta else 'PASS'), path, flush=True)
    report = {'compared_at': now, 'baseline': str(args.baseline),
              'candidate': args.candidate_url, 'cases': len(results),
              'failed': sum(bool(item['differences']) for item in results.values()),
              'results': results}
    write_json(args.report, report, replace=args.replace)
    print(f"{report['cases']} cases, {report['failed']} failed: {args.report}")
    return bool(report['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
