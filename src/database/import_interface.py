"""Add the published PeSTo/SPPIDER dataset without replacing existing Web schemas.

Run: python -m Web.src.database.import_interface
Resumable per table. Native real[] keeps both partner-conditioned Float32 vectors.
"""
from pathlib import Path
import json, time, os
from datetime import datetime, timezone
import pyarrow as pa
import pyarrow.parquet as pq
import psycopg
from psycopg import sql
import yaml
from Web.src.api.db import read_env

WEB=Path(__file__).resolve().parents[2]
PROJECT=WEB.parent
STATE=WEB/'data/postgresql_interface_loading.json'
REPORT=WEB/'data/postgresql_interface_import.json'
PK={'pesto_sequence':['sequence_id'],'pesto_structure':['structure_id'],
 'pesto_prediction':['structure_id','chain','structure_residue_id','insertion_code'],
 'sppider_prediction':['query_sequence_key','partner_sequence_key'],
 'sequence_content':['sequence_key'],'canonical_reference':['canonical_accession'],
 'sppider_foundation_link':['canonical_accession'],'direction_manifest':['query_sequence_key','partner_sequence_key']}
INDEX={'pesto_prediction':[['sequence_id','canonical_position']],
 'pesto_structure':[['sequence_id']], 'canonical_reference':[['sequence_key']],
 'sppider_foundation_link':[['foundation_sequence_id'],['sequence_key']],
 'direction_evidence':[['query_sequence_key','partner_sequence_key']],
 'endpoint_canonical_candidate':[['endpoint_key']]}
def pgtype(t):
 if pa.types.is_list(t):return pgtype(t.value_type)+'[]'
 if pa.types.is_boolean(t):return 'boolean'
 if pa.types.is_int32(t):return 'integer'
 if pa.types.is_integer(t):return 'bigint'
 if pa.types.is_float32(t):return 'real'
 if pa.types.is_floating(t):return 'double precision'
 return 'text'
def main():
 cfg=yaml.safe_load((WEB/'config/interface.yaml').read_text());source=PROJECT/cfg['source_path']
 manifest=json.loads((source/cfg['source_manifest']).read_text());assert manifest['status']=='published'
 assert manifest['data_version']==cfg['data_version']
 db=yaml.safe_load((WEB/'config/database.yaml').read_text());secret=read_env(WEB/db['credentials_file'])
 conn=psycopg.connect(host=db['host'],port=db['port'],dbname=db['database'],user=secret['POSTGRES_USER'],password=secret['POSTGRES_PASSWORD'],autocommit=True,application_name='memvar_interface_import')
 if conn.execute("SELECT 1 FROM pg_namespace WHERE nspname=%s",(cfg['schema'],)).fetchone():
  raise RuntimeError('web_interface already exists; do not overwrite a published dataset implicitly')
 state=json.loads(STATE.read_text()) if STATE.exists() else {'stage':'web_interface_loading_'+str(os.getpid()),'data_version':cfg['data_version'],'completed':{},'status':'loading','started_at':datetime.now(timezone.utc).isoformat()}
 assert state['data_version']==cfg['data_version'];stage=state['stage'];begin=time.monotonic()
 def save():STATE.write_text(json.dumps(state,indent=2)+'\n')
 conn.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(stage)));save()
 tables=sorted(set(f['path'].split('/')[0].removesuffix('.parquet') for f in manifest['files']))
 try:
  for name in tables:
   if name in state['completed']:continue
   files=sorted((source/name).glob('*.parquet')) if (source/name).is_dir() else [source/(name+'.parquet')]
   schema=pq.ParquetFile(files[0]).schema_arrow;types=[pgtype(f.type) for f in schema];columns=schema.names
   expected=sum(pq.ParquetFile(f).metadata.num_rows for f in files)
   table=sql.Identifier(stage,name)
   conn.execute(sql.SQL('DROP TABLE IF EXISTS {}').format(table))
   conn.execute(sql.SQL('CREATE TABLE {} ({})').format(table,sql.SQL(',').join(sql.SQL('{} {}').format(sql.Identifier(f.name),sql.SQL(t)) for f,t in zip(schema,types))))
   count=0;print(name,'loading',expected,flush=True)
   with conn.cursor().copy(sql.SQL('COPY {} FROM STDIN (FORMAT BINARY)').format(table)) as copy:
    copy.set_types(types)
    for file_index,path in enumerate(files):
     for batch in pq.ParquetFile(path).iter_batches(batch_size=4096,use_threads=False):
      values=[col.to_pylist() for col in batch.columns]
      for row in zip(*values):copy.write_row(row)
      count+=batch.num_rows
     if len(files)>100 and (file_index+1)%250==0:print(name,'files',file_index+1,'/',len(files),flush=True)
   assert count==expected,(name,count,expected)
   if name in PK:conn.execute(sql.SQL('ALTER TABLE {} ADD PRIMARY KEY ({})').format(table,sql.SQL(',').join(map(sql.Identifier,PK[name]))))
   for cols in INDEX.get(name,[]):
    if all(c in columns for c in cols):conn.execute(sql.SQL('CREATE INDEX ON {} ({})').format(table,sql.SQL(',').join(map(sql.Identifier,cols))))
   conn.execute(sql.SQL('ANALYZE {}').format(table))
   actual=conn.execute(sql.SQL('SELECT count(*) FROM {}').format(table)).fetchone()[0];assert actual==expected
   state['completed'][name]=actual;save();print(name,'complete',actual,flush=True)
  S=sql.Identifier(stage)
  conn.execute(sql.SQL('DROP TABLE IF EXISTS {}.web_sequence_link').format(S))
  conn.execute(sql.SQL('''CREATE TABLE {}.web_sequence_link AS
   SELECT 'PeSTo'::text method,s.accession canonical_accession,s.sequence_id source_sequence_id,
     s.sequence_id source_key,p.default_sequence_id web_sequence_id,
     CASE WHEN w.sequence=s.sequence THEN 'exact' WHEN w.sequence IS NULL THEN 'outside_web' ELSE 'sequence_mismatch' END mapping_status
   FROM {}.pesto_sequence s LEFT JOIN web.protein p ON p.accession=s.accession
   LEFT JOIN web.protein_sequence w ON w.sequence_id=p.default_sequence_id
   UNION ALL
   SELECT 'SPPIDER-seq',l.canonical_accession,l.foundation_sequence_id,l.sequence_key,p.default_sequence_id,
     CASE WHEN l.mapping_status='exact' AND c.sequence=w.sequence THEN 'exact'
       WHEN l.mapping_status<>'exact' THEN l.mapping_status WHEN w.sequence IS NULL THEN 'outside_web' ELSE 'sequence_mismatch' END
   FROM {}.sppider_foundation_link l LEFT JOIN {}.sequence_content c USING(sequence_key)
   LEFT JOIN web.protein p ON p.accession=l.canonical_accession LEFT JOIN web.protein_sequence w ON w.sequence_id=p.default_sequence_id
  ''').format(S,S,S,S))
  conn.execute(sql.SQL('CREATE INDEX ON {}.web_sequence_link(canonical_accession,method,mapping_status)').format(S))
  conn.execute(sql.SQL('CREATE INDEX ON {}.web_sequence_link(web_sequence_id,method)').format(S))
  # Necessary relationship/array shape checks; source-wide score QC already passed upstream.
  checks={}
  for name,statement in {
   'pesto_structure_missing':'SELECT count(*) FROM {s}.pesto_structure x LEFT JOIN {s}.pesto_sequence s USING(sequence_id) WHERE s.sequence_id IS NULL',
   'sppider_vector_length':'SELECT count(*) FROM {s}.sppider_prediction WHERE cardinality(receptor_probability)<>length OR cardinality(peptide_probability)<>length',
   'sppider_query_missing':'SELECT count(*) FROM {s}.sppider_prediction p LEFT JOIN {s}.sequence_content s ON s.sequence_key=p.query_sequence_key WHERE s.sequence_key IS NULL',
   'sppider_partner_missing':'SELECT count(*) FROM {s}.sppider_prediction p LEFT JOIN {s}.sequence_content s ON s.sequence_key=p.partner_sequence_key WHERE s.sequence_key IS NULL',
  }.items():
   checks[name]=conn.execute(sql.SQL(statement).format(s=S)).fetchone()[0];assert checks[name]==0,(name,checks[name])
  mappings=conn.execute(sql.SQL('SELECT method,mapping_status,count(*) FROM {}.web_sequence_link GROUP BY 1,2').format(S)).fetchall()
  report={'status':'imported_validated','data_version':cfg['data_version'],'schema':cfg['schema'],'tables':state['completed'],'mapping_counts':mappings,'checks':checks,'source_manifest':str(source/cfg['source_manifest']),'vector_storage':'real[]; query position i selects array element i; no partner or fragment averaging','finished_at':datetime.now(timezone.utc).isoformat(),'elapsed_this_process_seconds':round(time.monotonic()-begin,2)}
  conn.execute(sql.SQL('CREATE TABLE IF NOT EXISTS {}._build_manifest(data_version text PRIMARY KEY,manifest jsonb)').format(S))
  conn.execute(sql.SQL('INSERT INTO {}._build_manifest VALUES (%s,%s::jsonb)').format(S),(cfg['data_version'],json.dumps(report)))
  with conn.transaction():
   conn.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO memvar_api').format(S))
   conn.execute(sql.SQL('GRANT SELECT ON ALL TABLES IN SCHEMA {} TO memvar_api').format(S))
   conn.execute(sql.SQL('ALTER SCHEMA {} RENAME TO {}').format(S,sql.Identifier(cfg['schema'])))
  REPORT.write_text(json.dumps(report,indent=2)+'\n');STATE.unlink();print(json.dumps(report),flush=True)
 except BaseException as exc:
  state.update(status='failed_staging_preserved',error=type(exc).__name__+': '+str(exc));save();raise
 finally:conn.close()
if __name__=='__main__':main()
