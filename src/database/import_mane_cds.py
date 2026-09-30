"""Project the published MANE structures and atomically install a small Web catalog."""
from collections import defaultdict
import json
from pathlib import Path
import shutil

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
import pyarrow.parquet as pq
import yaml
from Web.src.api.db import read_env

WEB=Path(__file__).resolve().parents[2]

def main():
    cfg=yaml.safe_load((WEB/'config/mane_cds.yaml').read_text()); source=WEB.parent/cfg['source_directory']
    manifest=json.loads((source/'manifest.json').read_text())
    if manifest['state']!='published': raise ValueError('Source must be published')
    genes=pq.read_table(source/'gene_mane_cds.parquet').to_pylist(); blocks=defaultdict(list)
    for b in pq.read_table(source/'mane_cds_segments.parquet').to_pylist(): blocks[b['gene_id']].append(b)
    models=[{**g,'segments':blocks[g['gene_id']],'snapshot':manifest['run_id']} for g in genes]
    target=WEB/cfg['service_directory'];stage=target.with_name(target.name+'.building');stage.mkdir(parents=True,exist_ok=False)
    for name in ['gene_mane_cds.parquet','mane_cds_segments.parquet','manifest.json']:shutil.copy2(source/name,stage/name)
    db=yaml.safe_load((WEB/'config/database.yaml').read_text()); secret=read_env(WEB/db['credentials_file']);reader=read_env(WEB/'data/.api.env')['PGUSER']
    with psycopg.connect(host=db['host'],port=db['port'],dbname=db['database'],user=secret['POSTGRES_USER'],password=secret['POSTGRES_PASSWORD']) as conn:
        conn.execute('CREATE SCHEMA IF NOT EXISTS web_mane')
        conn.execute('CREATE TABLE web_mane.gene_cds_loading(gene_id text PRIMARY KEY,ensembl_gene_id text,model jsonb NOT NULL)')
        with conn.cursor().copy('COPY web_mane.gene_cds_loading FROM STDIN') as copy:
            for m in models:copy.write_row((m['gene_id'],m['ensembl_gene_id'],Jsonb(m)))
        actual=conn.execute('SELECT count(*) FROM web_mane.gene_cds_loading').fetchone()[0]
        if actual!=len(models):raise ValueError('Row count mismatch')
        for m in [models[0],next(m for m in models if m['gene_id']=='HGNC:3236'),next(m for m in models if m['status']=='no_mane_select')]:
            row=conn.execute('SELECT model FROM web_mane.gene_cds_loading WHERE gene_id=%s',(m['gene_id'],)).fetchone()[0]
            if row!=m:raise ValueError('Model JSON roundtrip mismatch')
        conn.execute('DROP TABLE IF EXISTS web_mane.gene_cds')
        conn.execute('ALTER TABLE web_mane.gene_cds_loading RENAME TO gene_cds')
        conn.execute(sql.SQL('GRANT USAGE ON SCHEMA web_mane TO {}').format(sql.Identifier(reader)))
        conn.execute(sql.SQL('GRANT SELECT ON web_mane.gene_cds TO {}').format(sql.Identifier(reader)))
        conn.execute('ANALYZE web_mane.gene_cds')
    old=target.with_name(target.name+'.previous')
    if target.exists():target.rename(old)
    stage.rename(target)
    if old.exists():shutil.rmtree(old)
    report=dict(state='imported_validated',rows=len(models),segments=sum(map(len,blocks.values())),source=cfg['source_directory'])
    (WEB/'data/postgresql_mane_cds_import.json').write_text(json.dumps(report,indent=2)+'\n');print(report)

if __name__=='__main__':main()
