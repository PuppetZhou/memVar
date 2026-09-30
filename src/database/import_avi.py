"""Stream AVI contributions into an independent, atomically published schema."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq
import yaml

from Web.src.api.db import read_env

WEB = Path(__file__).resolve().parents[2]


def main():
    cfg = yaml.safe_load((WEB / 'config/database.yaml').read_text())
    avi = yaml.safe_load((WEB / 'config/avi.yaml').read_text())
    secret = read_env(WEB / cfg['credentials_file'])
    source = WEB / avi['service_directory']
    manifest = json.loads((source / 'manifest.json').read_text())
    file = pq.ParquetFile(source / 'attribution.parquet')
    fields = file.schema_arrow
    if any(not (pa.types.is_string(f.type) or pa.types.is_float64(f.type)) for f in fields):
        raise ValueError('Unexpected contribution service field types.')
    target = avi['schema']
    stage = target + '_loading_' + str(os.getpid())
    table = sql.Identifier(stage, 'attribution')
    started = time.monotonic()
    samples = []
    with psycopg.connect(host=cfg['host'], port=cfg['port'], dbname=cfg['database'],
                         user=secret['POSTGRES_USER'], password=secret['POSTGRES_PASSWORD']) as conn:
        conn.execute("SET maintenance_work_mem='512MB'")
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(stage)))
        conn.execute(sql.SQL('CREATE TABLE {} ({})').format(table, sql.SQL(',').join(
            sql.SQL('{} {}').format(sql.Identifier(f.name), sql.SQL(
                'double precision' if pa.types.is_float64(f.type) else 'text')) for f in fields)))
        copied = 0
        with conn.cursor().copy(sql.SQL("COPY {} FROM STDIN WITH (FORMAT CSV, NULL '')").format(table)) as copy:
            for batch in file.iter_batches(batch_size=16384):
                if copied == 0 or copied // 1000000 != (copied + batch.num_rows) // 1000000:
                    samples.append(batch.slice(0, 1).to_pylist()[0])
                    print('streaming', copied, 'rows', flush=True)
                sink = pa.BufferOutputStream()
                pcsv.write_csv(batch, sink, write_options=pcsv.WriteOptions(include_header=False))
                copy.write(sink.getvalue().to_pybytes())
                copied += batch.num_rows
        conn.execute(sql.SQL('ALTER TABLE {} ADD PRIMARY KEY(variant_id)').format(table))
        actual = conn.execute(sql.SQL('SELECT count(*) FROM {}').format(table)).fetchone()[0]
        if actual != manifest['tables'][0]['rows'] or actual != copied:
            raise ValueError('Database row count differs from published service projection.')
        missing = conn.execute(sql.SQL('SELECT a.variant_id FROM {} a WHERE NOT EXISTS '
            '(SELECT 1 FROM web_variant.variant v WHERE v.variant_id=a.variant_id) LIMIT 1').format(table)).fetchone()
        if missing:
            raise ValueError('Contribution variant is absent from the current variant database.')
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cursor:
            for expected in samples:
                actual_row = cursor.execute(sql.SQL('SELECT * FROM {} WHERE variant_id=%s').format(table),
                                            (expected['variant_id'],)).fetchone()
                if actual_row != expected:
                    raise ValueError('Contribution value roundtrip mismatch.')
        conn.execute(sql.SQL('CREATE TABLE {}._build_manifest(data_version text PRIMARY KEY,manifest jsonb)').format(sql.Identifier(stage)))
        conn.execute(sql.SQL('INSERT INTO {}._build_manifest VALUES (%s,%s)').format(sql.Identifier(stage)),
                     (manifest['data_version'], Jsonb(manifest)))
        reader = read_env(WEB / 'data/.api.env')['PGUSER']
        conn.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(sql.Identifier(stage), sql.Identifier(reader)))
        conn.execute(sql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}').format(sql.Identifier(stage), sql.Identifier(reader)))
        conn.execute(sql.SQL('ANALYZE {}').format(table))
        size = conn.execute('SELECT pg_total_relation_size(%s)', (stage+'.attribution',)).fetchone()[0]
        conn.execute('SELECT pg_advisory_xact_lock(20260929,2)')
        old = stage+'_old'
        if conn.execute('SELECT 1 FROM pg_namespace WHERE nspname=%s', (target,)).fetchone():
            conn.execute(sql.SQL('ALTER SCHEMA {} RENAME TO {}').format(sql.Identifier(target), sql.Identifier(old)))
        conn.execute(sql.SQL('ALTER SCHEMA {} RENAME TO {}').format(sql.Identifier(stage), sql.Identifier(target)))
        conn.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(old)))
    report = dict(status='imported_validated', data_version=manifest['data_version'],
                  checked_at=datetime.now(timezone.utc).isoformat(), rows=copied,
                  sample_roundtrips=len(samples), orphan_variants=0, schema=target,
                  table_size_bytes=size, elapsed_seconds=round(time.monotonic()-started, 3))
    (WEB / 'data/postgresql_avi_import.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
