"""Transactional PaxDB-only import, with indexed accession and dataset links."""
from pathlib import Path
import json,os,time
import psycopg
from psycopg import sql
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from Web.src.api.db import read_env
WEB=Path(__file__).resolve().parents[2]
def main():
 cfg=yaml.safe_load((WEB/'config/database.yaml').read_text());secret=read_env(WEB/cfg['credentials_file'])
 source=WEB/'data/tables/paxdb';manifest=json.loads((source/'manifest.json').read_text())
 stage='web_paxdb_loading_'+str(os.getpid());counts={};begin=time.monotonic()
 with psycopg.connect(host=cfg['host'],port=cfg['port'],dbname=cfg['database'],user=secret['POSTGRES_USER'],password=secret['POSTGRES_PASSWORD']) as conn:
  conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(stage)))
  for name,file in [('datasets','datasets'),('observations','mapped_observations'),('protein_mapping','protein_mapping')]:
   p=pq.ParquetFile(source/(file+'.parquet'));fields=p.schema_arrow
   types=['boolean' if pa.types.is_boolean(f.type) else 'bigint' if pa.types.is_integer(f.type) else 'text' for f in fields]
   table=sql.Identifier(stage,name)
   conn.execute(sql.SQL('CREATE TABLE {} ({})').format(table,sql.SQL(',').join(sql.SQL('{} {}').format(sql.Identifier(f.name),sql.SQL(t)) for f,t in zip(fields,types))))
   with conn.cursor().copy(sql.SQL('COPY {} FROM STDIN').format(table)) as copy:
    for batch in p.iter_batches(batch_size=8192):
     for row in zip(*(col.to_pylist() for col in batch.columns)):copy.write_row(row)
   actual=conn.execute(sql.SQL('SELECT count(*) FROM {}').format(table)).fetchone()[0]
   assert actual==p.metadata.num_rows;counts[name]=actual;print(name,actual,flush=True)
  S=sql.Identifier(stage)
  for statement in [
   'ALTER TABLE {}.datasets ADD PRIMARY KEY(id)',
   'ALTER TABLE {}.observations ADD PRIMARY KEY(dataset_id,source_row)',
   'ALTER TABLE {}.protein_mapping ADD PRIMARY KEY(string_external_id,accession)',
   'ALTER TABLE {}.observations ADD FOREIGN KEY(dataset_id) REFERENCES '+stage+'.datasets(id)',
   'CREATE INDEX ON {}.observations(string_external_id,dataset_id)',
   'CREATE INDEX ON {}.protein_mapping(accession,string_external_id)',
   'CREATE INDEX ON {}.datasets(integrated,context_type,organ)',
  ]:conn.execute(sql.SQL(statement).format(S))
  lost=conn.execute(sql.SQL('SELECT count(*) FROM {}.observations o WHERE NOT EXISTS (SELECT 1 FROM {}.protein_mapping m WHERE m.string_external_id=o.string_external_id)').format(S,S)).fetchone()[0]
  assert lost==0
  reader=read_env(WEB/'data/.api.env')['PGUSER']
  conn.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(S,sql.Identifier(reader)))
  conn.execute(sql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}').format(S,sql.Identifier(reader)))
  for table in counts:conn.execute(sql.SQL('ANALYZE {}.{}').format(S,sql.Identifier(table)))
  conn.execute('SELECT pg_advisory_xact_lock(20260928,1)')
  if conn.execute("SELECT 1 FROM pg_namespace WHERE nspname='web_paxdb'").fetchone():
   conn.execute(sql.SQL('ALTER SCHEMA web_paxdb RENAME TO {}').format(sql.Identifier(stage+'_old')))
  conn.execute(sql.SQL('ALTER SCHEMA {} RENAME TO web_paxdb').format(S))
  conn.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(stage+'_old')))
 (WEB/'data/postgresql_paxdb_import.json').write_text(json.dumps(dict(status='imported_validated',counts=counts,data_version=manifest['data_version'],elapsed_seconds=time.monotonic()-begin),indent=2))
if __name__=='__main__':main()
