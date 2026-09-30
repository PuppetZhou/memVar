"""Publish the small curated AlphaGenome reference catalog to PostgreSQL atomically."""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import time
import psycopg
from psycopg import sql
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from Web.src.api.db import read_env
WEB = Path(__file__).resolve().parents[2]


def main():
    begin = time.monotonic()
    config = yaml.safe_load((WEB / 'config/alphagenome.yaml').read_text())
    source = (WEB / config['catalog_path']).resolve()
    manifest = json.loads((source / 'manifest.json').read_text())
    if manifest['schema_version'] != 2:
        raise ValueError('Unsupported curated reference catalog')
    stage_files = WEB / 'data/tables' / f'.alphagenome_reference_{os.getpid()}'
    stage_files.mkdir(parents=True)
    for name in ['genes', 'windows', 'protein_gene', 'tracks']:
        shutil.copy2(source / f'{name}.parquet', stage_files / f'{name}.parquet')
    shutil.copy2(source / 'manifest.json', stage_files / 'manifest.json')
    cfg = yaml.safe_load((WEB / 'config/database.yaml').read_text())
    secret = read_env(WEB / cfg['credentials_file'])
    reader = read_env(WEB / 'data/.api.env')['PGUSER']
    stage = f'web_alphagenome_loading_{os.getpid()}'
    counts = {}
    with psycopg.connect(host=cfg['host'], port=cfg['port'], dbname=cfg['database'],
                        user=secret['POSTGRES_USER'], password=secret['POSTGRES_PASSWORD']) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(stage)))
        for name in ['genes', 'windows', 'protein_gene', 'tracks']:
            parquet = pq.ParquetFile(stage_files / f'{name}.parquet')
            fields = parquet.schema_arrow
            types = ['boolean' if pa.types.is_boolean(f.type) else 'bigint' if pa.types.is_integer(f.type)
                     else 'double precision' if pa.types.is_floating(f.type) else 'text' for f in fields]
            table = sql.Identifier(stage, name)
            conn.execute(sql.SQL('CREATE TABLE {} ({})').format(table, sql.SQL(',').join(
                sql.SQL('{} {}').format(sql.Identifier(f.name), sql.SQL(t)) for f, t in zip(fields, types))))
            with conn.cursor().copy(sql.SQL('COPY {} FROM STDIN').format(table)) as copy:
                for batch in parquet.iter_batches(batch_size=8192):
                    for row in zip(*(col.to_pylist() for col in batch.columns)):
                        copy.write_row(row)
            actual = conn.execute(sql.SQL('SELECT count(*) FROM {}').format(table)).fetchone()[0]
            if actual != parquet.metadata.num_rows:
                raise ValueError('Imported row count differs')
            counts[name] = actual
        schema = sql.Identifier(stage)
        for statement in [
            'ALTER TABLE {}.genes ADD PRIMARY KEY(hgnc_id)',
            'CREATE INDEX ON {}.genes(ensembl_gene_id)',
            'ALTER TABLE {}.windows ADD PRIMARY KEY(tile_id)',
            'CREATE INDEX ON {}.windows(hgnc_id,tile_index)',
            'ALTER TABLE {}.tracks ADD PRIMARY KEY(track_id)',
            'CREATE INDEX ON {}.tracks(biosample_key,modality)',
            'ALTER TABLE {}.protein_gene ADD PRIMARY KEY(accession,hgnc_id)',
            f'ALTER TABLE {{}}.windows ADD FOREIGN KEY(hgnc_id) REFERENCES {stage}.genes(hgnc_id)',
            f'ALTER TABLE {{}}.protein_gene ADD FOREIGN KEY(hgnc_id) REFERENCES {stage}.genes(hgnc_id)',
        ]:
            conn.execute(sql.SQL(statement).format(schema))
        conn.execute(sql.SQL('CREATE TABLE {}.manifest (id boolean PRIMARY KEY DEFAULT true CHECK(id), data jsonb NOT NULL)').format(schema))
        conn.execute(sql.SQL('INSERT INTO {}.manifest(data) VALUES(%s::jsonb)').format(schema), (json.dumps(manifest),))
        conn.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(schema, sql.Identifier(reader)))
        conn.execute(sql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}').format(schema, sql.Identifier(reader)))
        for name in counts:
            conn.execute(sql.SQL('ANALYZE {}.{}').format(schema, sql.Identifier(name)))
        conn.execute('SELECT pg_advisory_xact_lock(20260929,2)')
        if conn.execute("SELECT 1 FROM pg_namespace WHERE nspname='web_alphagenome'").fetchone():
            conn.execute(sql.SQL('ALTER SCHEMA web_alphagenome RENAME TO {}').format(sql.Identifier(stage + '_old')))
        conn.execute(sql.SQL('ALTER SCHEMA {} RENAME TO web_alphagenome').format(schema))
        conn.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(stage + '_old')))
    current = WEB / 'data/tables/alphagenome_reference'
    old = current.with_name('.alphagenome_reference_previous')
    if old.exists():
        shutil.rmtree(old)
    if current.exists():
        current.rename(old)
    stage_files.rename(current)
    if old.exists():
        shutil.rmtree(old)
    result = dict(status='imported_validated', checked_at=datetime.now(timezone.utc).isoformat(),
                  counts=counts, catalog_run_id=manifest['catalog_run_id'],
                  source_run_id=manifest['source_run_id'], elapsed_seconds=time.monotonic() - begin)
    (WEB / 'data/postgresql_alphagenome_reference_import.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
