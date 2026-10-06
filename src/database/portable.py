"""Prepare a relocatable, read-only website data package from the live snapshot.

This tool reads source files only. It never connects to PostgreSQL or changes
the catalog currently used by the API. Run ``plan`` before ``build``.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import duckdb
import pyarrow.parquet as pq
import yaml

from ..api.duckdb_sql import translate


WEB = Path(__file__).resolve().parents[2]
TYPE = {
    'text': 'VARCHAR', 'jsonb': 'JSON', 'int4': 'INTEGER', 'int8': 'BIGINT',
    'float4': 'FLOAT', 'float8': 'DOUBLE', 'bool': 'BOOLEAN',
    '_text': 'VARCHAR[]', '_float4': 'FLOAT[]',
}
ALPHAGENOME_TABLES = ('genes', 'protein_gene', 'tracks', 'windows')
SIDECARS = ('manifest.json', 'source-metadata.json', 'source-record-files.json', 'catalog_statistics.json')


def identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def literal(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def preparation_version() -> dict:
    """Best-effort code provenance; package preparation also works without Git."""
    try:
        commit = subprocess.run(['git', '-C', str(WEB), 'rev-parse', 'HEAD'],
                                capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(['git', '-C', str(WEB), 'status', '--porcelain', '--untracked-files=no'],
                                    capture_output=True, text=True, check=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return {'git_commit': None, 'working_tree_dirty': None}
    return {'git_commit': commit, 'working_tree_dirty': dirty}


def source_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else WEB / path).resolve()


def package_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError(f'Package path escapes its root: {relative}')
    return path


def sources(config_path: Path) -> dict[str, Path]:
    config = yaml.safe_load(config_path.read_text())
    return {key: source_path(config[key]) for key in
            ('snapshot', 'catalog', 'alphagenome', 'assets', 'structures')}


def inventory(config_path: Path) -> dict:
    source = sources(config_path)
    snapshot, alpha, assets, structures = (source[key] for key in ('snapshot', 'alphagenome', 'assets', 'structures'))
    if source['catalog'].parent != snapshot or not source['catalog'].is_file():
        raise ValueError('Configured runtime catalog does not belong to the configured snapshot')
    manifest = json.loads((snapshot / 'manifest.json').read_text())
    alpha_manifest = json.loads((alpha / 'manifest.json').read_text())
    if alpha_manifest.get('schema_version') != 2 or alpha_manifest.get('crop_status') != 'complete':
        raise ValueError('AlphaGenome retained catalog is incomplete')
    with duckdb.connect(str(source['catalog']), read_only=True) as current:
        for schema, name, sql in current.execute(
                'SELECT schema_name, view_name, sql FROM duckdb_views() WHERE NOT internal').fetchall():
            if schema != 'web_alphagenome' and 'read_parquet(' in sql.lower() and str(snapshot) not in sql:
                raise ValueError(f'Runtime snapshot view points elsewhere: {schema}.{name}')
        current_manifest = json.loads(current.execute(
            'SELECT data FROM web_alphagenome.manifest WHERE id').fetchone()[0])
        for field in ('source_run_id', 'checkpoint_revision', 'backend',
                      'model_version', 'crop_run_id', 'retention_flank_bp'):
            if current_manifest.get(field) != alpha_manifest.get(field):
                raise ValueError(f'AlphaGenome runtime identity differs: {field}')
        for name in ALPHAGENOME_TABLES:
            if current_manifest['counts'][name] != alpha_manifest['counts'][name]:
                raise ValueError(f'AlphaGenome runtime scope differs: {name}')
            actual_rows = current.execute(
                'SELECT count(*) FROM web_alphagenome.' + identifier(name)).fetchone()[0]
            if actual_rows != alpha_manifest['counts'][name]:
                raise ValueError(f'AlphaGenome current catalog rows differ: {name}')
            current_columns = [(row[0], row[1]) for row in current.execute(
                'DESCRIBE SELECT * FROM web_alphagenome.' + identifier(name)).fetchall()]
            new_columns = [(row[0], row[1]) for row in current.execute(
                'DESCRIBE SELECT * FROM read_parquet(' + literal(alpha / (name + '.parquet')) + ')').fetchall()]
            if current_columns != new_columns:
                raise ValueError(f'AlphaGenome runtime fields differ: {name}')
    windows = pq.read_table(alpha / 'windows.parquet', columns=['relative_path']).column(0).to_pylist()
    window_contract = pq.read_table(alpha / 'windows.parquet', columns=[
        'retention_start', 'retention_end', 'window_start', 'window_end',
        'source_run_id', 'crop_run_id']).to_pylist()
    if any(row['retention_start'] is None or row['retention_end'] is None or
           row['retention_start'] < row['window_start'] or
           row['retention_end'] > row['window_end'] or
           row['retention_start'] >= row['retention_end'] or
           row['source_run_id'] != alpha_manifest['source_run_id'] or
           row['crop_run_id'] != alpha_manifest['crop_run_id']
           for row in window_contract):
        raise ValueError('AlphaGenome retained window contract is invalid')
    models = pq.read_table(structures / 'manifest.parquet', columns=['relative_path']).column(0).to_pylist()
    if len(windows) != alpha_manifest['counts']['windows']:
        raise ValueError('AlphaGenome window count differs from its manifest')
    files: list[tuple[Path, str]] = []
    for name in SIDECARS:
        files.append((snapshot / name, name))
    for obj in manifest['objects']:
        if obj['storage'] == 'logical_view':
            relative = f"view-baseline/{obj['schema']}.{obj['name']}.json"
            files.append((snapshot / relative, relative))
    for obj in manifest['objects']:
        if obj['storage'] == 'parquet':
            if not obj['files']:
                raise ValueError(f"No Parquet files for {obj['schema']}.{obj['name']}")
            for relative in obj['files']:
                expected = f"data/{obj['schema']}/{obj['name']}/"
                if not relative.startswith(expected) or not re.fullmatch(r'part-[A-Za-z0-9_-]+\.parquet', relative[len(expected):]):
                    raise ValueError(f'Unexpected Parquet filename: {relative}')
                files.append((package_path(snapshot, relative), relative))
    for name in ALPHAGENOME_TABLES:
        files.append((alpha / (name + '.parquet'), 'alphagenome/' + name + '.parquet'))
    files.append((alpha / 'manifest.json', 'alphagenome/manifest.json'))
    for relative in windows:
        if not isinstance(relative, str) or not relative.startswith('tiles/'):
            raise ValueError(f'Unexpected AlphaGenome tile path: {relative}')
        files.append((package_path(assets, relative), 'alphagenome/assets/' + relative))
    files.append((structures / 'manifest.parquet', 'structures/manifest.parquet'))
    for relative in models:
        if not isinstance(relative, str) or not relative.endswith('.pdb.gz'):
            raise ValueError(f'Unexpected structure model path: {relative}')
        files.append((package_path(structures, relative), 'structures/' + relative))
    unique = set()
    count, bytes_total = Counter(), Counter()
    file_details = []
    for original, relative in files:
        if relative in unique:
            raise ValueError(f'Duplicate package path: {relative}')
        unique.add(relative)
        if not original.is_file():
            raise FileNotFoundError(original)
        group = relative.split('/', 1)[0] if '/' in relative else 'sidecars'
        count[group] += 1
        size = original.stat().st_size
        bytes_total[group] += size
        file_details.append({'path': relative, 'bytes': size})
    return dict(source=source, manifest=manifest, alpha_manifest=alpha_manifest,
                files=files, file_details=file_details,
                counts=dict(count), bytes=dict(bytes_total))


def build_catalog(root: Path, name: str = 'catalog.duckdb') -> Path:
    """Recreate all active views from the frozen manifest and retained crop catalog."""
    root = root.resolve()
    manifest = json.loads((root / 'manifest.json').read_text())
    alpha = json.loads((root / 'alphagenome/manifest.json').read_text())
    if Path(name).name != name or not name.endswith('.duckdb'):
        raise ValueError('Catalog name must be a local .duckdb filename')
    destination = root / name
    if destination.exists():
        raise FileExistsError(destination)
    temporary = root / (name + '.building')
    if temporary.exists():
        raise FileExistsError(temporary)
    try:
        with duckdb.connect(str(temporary)) as db:
            for schema in sorted({obj['schema'] for obj in manifest['objects']}):
                db.execute('CREATE SCHEMA ' + identifier(schema))
            for obj in manifest['objects']:
                if obj['storage'] != 'parquet' or obj['schema'] == 'web_alphagenome':
                    continue
                relation = identifier(obj['schema']) + '.' + identifier(obj['name'])
                projection = ','.join(
                    f"CAST({identifier(col['name'])} AS {TYPE[col['pg_type']]}) AS {identifier(col['name'])}"
                    for col in obj['columns']
                )
                pattern = root / 'data' / obj['schema'] / obj['name'] / 'part-*.parquet'
                db.execute(f'CREATE VIEW {relation} AS SELECT {projection} FROM read_parquet({literal(pattern)})')
            pending = [obj for obj in manifest['objects'] if obj['storage'] == 'logical_view']
            while pending:
                failures = []
                for obj in pending:
                    relation = identifier(obj['schema']) + '.' + identifier(obj['name'])
                    # Retain the migrated view definition and its dependency order.
                    definition = obj['definition'].replace('::jsonb', '::JSON')
                    try:
                        db.execute(f'CREATE VIEW {relation} AS {definition}')
                    except duckdb.Error:
                        try:
                            db.execute(f'CREATE VIEW {relation} AS {translate(obj["definition"])}')
                        except Exception as error:
                            failures.append((obj, str(error)))
                if len(failures) == len(pending):
                    raise RuntimeError('Unresolved logical views: ' + str([(o['schema'], o['name'], e) for o, e in failures]))
                pending = [obj for obj, _ in failures]
            for name in ALPHAGENOME_TABLES:
                path = root / 'alphagenome' / (name + '.parquet')
                db.execute(f'CREATE VIEW web_alphagenome.{identifier(name)} AS SELECT * FROM read_parquet({literal(path)})')
            # The JSON is a source fact: its historical absolute locations stay intact.
            db.execute('CREATE VIEW web_alphagenome.manifest AS SELECT true AS id, CAST('
                       + literal(json.dumps(alpha)) + ' AS JSON) AS data')
            db.execute('CHECKPOINT')
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def effective_catalog(root: Path, catalog_name: str = 'catalog.duckdb') -> dict:
    """Record current view contracts without scanning large relations."""
    root = root.resolve()
    manifest = json.loads((root / 'manifest.json').read_text())
    alpha = json.loads((root / 'alphagenome/manifest.json').read_text())
    view_rows = {}
    with duckdb.connect(str(root / catalog_name), read_only=True) as db:
        for obj in manifest['objects']:
            schema, name = obj['schema'], obj['name']
            relation = identifier(schema) + '.' + identifier(name)
            columns = [{'name': row[0], 'duckdb_type': row[1]}
                       for row in db.execute('DESCRIBE SELECT * FROM ' + relation).fetchall()]
            if schema == 'web_alphagenome':
                source = 'retained_alphagenome_catalog'
                rows = 1 if name == 'manifest' else alpha['counts'][name]
            elif obj['storage'] == 'logical_view':
                source = 'snapshot_logical_view'
                baseline = root / 'view-baseline' / (schema + '.' + name + '.json')
                rows = json.loads(baseline.read_text())['rows'] if baseline.is_file() else None
            else:
                source = 'snapshot_parquet'
                rows = obj.get('rows')
            view_rows[relation] = {'source': source, 'rows': rows, 'columns': columns,
                                   'primary_key': obj.get('primary_key', [])}
    return {'schema_version': 1, 'snapshot_id': manifest.get('snapshot_id'),
            'alphagenome_crop_run_id': alpha['crop_run_id'],
            'historical_manifest_note': 'manifest.json preserves source snapshot records; web_alphagenome views use the retained crop catalog',
            'effective_views': view_rows}


def finalize(config_path: Path, root: Path) -> dict:
    """Validate a copied package and publish its completion marker, without copying."""
    root = root.resolve()
    if not root.is_dir() or not (root / 'catalog.duckdb').is_file():
        raise FileNotFoundError('Package catalog is absent')
    listing = inventory(config_path)
    for entry in listing['file_details']:
        target = package_path(root, entry['path'])
        if not target.is_file() or target.stat().st_size != entry['bytes']:
            raise ValueError(f"Package file missing or size differs: {entry['path']}")
    with duckdb.connect(str(root / 'catalog.duckdb'), read_only=True) as db:
        views = db.execute('SELECT schema_name, view_name, sql FROM duckdb_views() WHERE NOT internal').fetchall()
        if len(views) != len(listing['manifest']['objects']):
            raise ValueError('Package view count differs')
        for schema, name, sql in views:
            if 'read_parquet(' in sql.lower() and str(root) not in sql:
                raise ValueError(f'External Parquet path in {schema}.{name}')
        for table in ALPHAGENOME_TABLES:
            actual = db.execute(f'SELECT count(*) FROM web_alphagenome.{identifier(table)}').fetchone()[0]
            if actual != listing['alpha_manifest']['counts'][table]:
                raise ValueError(f'AlphaGenome {table} count differs')
    report = effective_catalog(root)
    report.update(status='complete', source={key: str(value) for key, value in listing['source'].items()},
                  prepared_at=datetime.now(timezone.utc).isoformat(),
                  source_code_version=listing['manifest'].get('code_version'),
                  preparation_code_version=preparation_version(),
                  file_counts=listing['counts'], file_bytes=listing['bytes'],
                  files=listing['file_details'])
    writing = root / 'package.json.writing'
    writing.write_text(json.dumps(report, indent=2) + '\n')
    writing.replace(root / 'package.json')
    return {'destination': str(root), 'status': 'complete', 'views': len(views),
            'file_counts': listing['counts'], 'file_bytes': listing['bytes']}


def build(config_path: Path, destination: Path) -> dict:
    listing = inventory(config_path)
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(destination)
    temporary = destination.with_name(destination.name + '.building')
    if temporary.exists():
        raise FileExistsError(temporary)
    temporary.mkdir(parents=True)
    try:
        for original, relative in listing['files']:
            target = package_path(temporary, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, target)
            if target.stat().st_size != original.stat().st_size:
                raise IOError(f'Copy size differs: {relative}')
        temporary.rename(destination)
        # Bind only after the final path exists. Until then there is no catalog
        # in the destination, so an interrupted package cannot serve requests.
        build_catalog(destination)
        finalize(config_path, destination)
    except BaseException:
        # Preserve a failed stage for inspection; never touch the active source.
        raise
    return {'destination': str(destination), 'views': len(listing['manifest']['objects']),
            'file_counts': listing['counts'], 'file_bytes': listing['bytes']}


def rebind(root: Path, name: str = 'catalog.rebound.duckdb', replace_offline: bool = False) -> Path:
    """Recreate views after a package move; replacement requires explicit offline mode."""
    root = root.resolve()
    if not (root / 'manifest.json').is_file() or not (root / 'alphagenome/manifest.json').is_file():
        raise FileNotFoundError('Package metadata is incomplete')
    if replace_offline:
        if name != 'catalog.rebound.duckdb':
            raise ValueError('--replace-offline uses the default rebound catalog name')
        rebound = build_catalog(root, name)
        os.replace(rebound, root / 'catalog.duckdb')
        return root / 'catalog.duckdb'
    return build_catalog(root, name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan', 'build', 'rebind', 'finalize'))
    parser.add_argument('--config', type=Path, default=WEB / 'config/packaging.yaml')
    parser.add_argument('--output', type=Path, help='New package directory; required for build')
    parser.add_argument('--catalog-name', default='catalog.rebound.duckdb',
                        help='New catalog filename for rebind; never overwrites an existing file')
    parser.add_argument('--replace-offline', action='store_true',
                        help='Explicitly replace catalog.duckdb after rebind; stop all readers first')
    args = parser.parse_args()
    config = source_path(args.config)
    if args.command == 'plan':
        listing = inventory(config)
        print(json.dumps({'source': {k: str(v) for k, v in listing['source'].items()},
                          'file_counts': listing['counts'], 'file_bytes': listing['bytes'],
                          'total_bytes': sum(listing['bytes'].values()),
                          'views': len(listing['manifest']['objects'])}, indent=2))
    elif args.command == 'build':
        if args.output is None:
            parser.error('--output is required for build')
        print(json.dumps(build(config, args.output), indent=2))
    elif args.command == 'finalize':
        if args.output is None:
            parser.error('--output is required for finalize')
        print(json.dumps(finalize(config, args.output), indent=2))
    else:
        if args.output is None:
            parser.error('--output is required for rebind')
        print(rebind(args.output, args.catalog_name, args.replace_offline))


if __name__ == '__main__':
    main()
