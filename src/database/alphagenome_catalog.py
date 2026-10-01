"""Bind a curated AlphaGenome catalog into a separate DuckDB runtime catalog.

Only five small AlphaGenome relations change. Existing Parquet views, source
record locator, and all other runtime metadata remain attached to their snapshot.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

import duckdb
import yaml


TABLES = ('genes', 'protein_gene', 'tracks', 'windows')


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def bind_catalog(source: Path, curated: Path, destination: Path, *, pilot=False):
    source, curated, destination = (p.resolve() for p in (source, curated, destination))
    if destination == source or destination.parent != source.parent:
        raise ValueError('Use a separate catalog beside the original runtime snapshot and sidecars.')
    if destination.exists():
        raise FileExistsError(destination)
    manifest = json.loads((curated / 'manifest.json').read_text())
    if manifest.get('schema_version') != 2 or not manifest.get('crop_run_id'):
        raise ValueError('A version 2 retained-storage catalog is required.')
    if not pilot and manifest.get('crop_status') != 'complete':
        raise ValueError('A full validated crop catalog is required outside pilot mode.')
    temporary = destination.with_name(destination.name + '.building')
    if temporary.exists():
        raise FileExistsError(temporary)
    shutil.copyfile(source, temporary)
    try:
        with duckdb.connect(str(temporary)) as db:
            original = json.loads(db.execute('SELECT data FROM web_alphagenome.manifest WHERE id').fetchone()[0])
            for field in ('source_run_id', 'checkpoint_revision', 'backend', 'model_version'):
                if manifest[field] != original[field]:
                    raise ValueError(f'The original prediction identity differs: {field}')
            old_views = db.execute("SELECT schema_name,view_name,sql FROM duckdb_views() WHERE NOT internal AND schema_name<>'web_alphagenome' ORDER BY schema_name,view_name").fetchall()
            counts = {}
            db.execute('BEGIN')
            for table in TABLES:
                path = curated / f'{table}.parquet'
                old_count = db.execute(f'SELECT count(*) FROM web_alphagenome.{table}').fetchone()[0]
                db.execute(f'CREATE OR REPLACE VIEW web_alphagenome.{table} AS SELECT * FROM read_parquet({literal(path)})')
                counts[table] = db.execute(f'SELECT count(*) FROM web_alphagenome.{table}').fetchone()[0]
                if counts[table] != manifest['counts'][table]:
                    raise ValueError(f'Curated manifest count differs: {table}')
                if counts[table] != old_count and not (pilot and table == 'windows'):
                    raise ValueError(f'Existing catalog scope changed: {table}')
            invalid = db.execute('''SELECT count(*) FROM web_alphagenome.windows WHERE
                retention_start < window_start OR retention_end > window_end OR
                retention_start >= retention_end OR source_run_id <> ? OR crop_run_id <> ?
                OR retention_start IS NULL OR retention_end IS NULL
                OR source_run_id IS NULL OR crop_run_id IS NULL''',
                [manifest['source_run_id'], manifest['crop_run_id']]).fetchone()[0]
            if invalid:
                raise ValueError('Invalid retained windows or prediction identity')
            db.execute('CREATE OR REPLACE VIEW web_alphagenome.manifest AS SELECT true AS id, CAST(' + literal(json.dumps(manifest)) + ' AS JSON) AS data')
            if old_views != db.execute("SELECT schema_name,view_name,sql FROM duckdb_views() WHERE NOT internal AND schema_name<>'web_alphagenome' ORDER BY schema_name,view_name").fetchall():
                raise ValueError('An unrelated runtime view changed')
            db.execute('COMMIT')
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    binding = dict(source_catalog=str(source), curated_catalog=str(curated),
                   crop_run_id=manifest['crop_run_id'], source_run_id=manifest['source_run_id'],
                   checkpoint_revision=manifest['checkpoint_revision'], counts=counts,
                   pilot=pilot, unchanged_other_views=True)
    destination.with_suffix('.binding.json').write_text(json.dumps(binding, indent=2) + '\n')
    return binding


def write_configuration(curated: Path, destination: Path):
    """Write a new configuration file; never overwrite a running deployment."""
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(destination)
    manifest = json.loads((curated / 'manifest.json').read_text())
    config = dict(catalog_path=str(curated.resolve()), reference_root=manifest['source_root'],
                  source_run_id=manifest['source_run_id'], checkpoint_revision=manifest['checkpoint_revision'],
                  crop_run_id=manifest['crop_run_id'], retention_flank_bp=manifest['retention_flank_bp'])
    with destination.open('x') as output:
        yaml.safe_dump(config, output)
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('curated', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--pilot', action='store_true', help='Allow fewer windows for local pilot validation only.')
    parser.add_argument('--config', type=Path, help='Write a separate API config, refusing any existing file.')
    args = parser.parse_args()
    try:
        if args.config and args.config.exists():
            raise FileExistsError(args.config)
        result=dict(status='passed',binding=bind_catalog(args.source, args.curated, args.destination, pilot=args.pilot))
        if args.config:
            result['configuration']=write_configuration(args.curated, args.config)
    except Exception as error:
        result=dict(status='failed',error_type=type(error).__name__,error=str(error))
    print(json.dumps(result, indent=2))
    return 0 if result['status']=='passed' else 1


if __name__ == '__main__':
    sys.exit(main())
