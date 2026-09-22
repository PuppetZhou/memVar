"""Import only web_context, leaving the concurrently maintained web schema intact."""
from pathlib import Path
import json, os, subprocess, time
import duckdb, pyarrow as pa, pyarrow.parquet as pq, yaml
from import_tables import command,q,C,start
WEB=Path(__file__).resolve().parents[2];DATA=WEB/'data/context_tables'
def lit(v):return "'"+str(v).replace("'","''")+"'"
def pgtype(f):
 t=f.type
 if f.name.endswith('_json') or pa.types.is_nested(t):return 'jsonb'
 if pa.types.is_integer(t):return 'bigint'
 if pa.types.is_float32(t):return 'real'
 if pa.types.is_floating(t):return 'double precision'
 if pa.types.is_boolean(t):return 'boolean'
 return 'text'
def main():
 start();manifest=json.loads((DATA/'manifest.json').read_text());stage='web_context_loading_'+str(os.getpid());begin=time.time()
 state_path=WEB/'data/postgresql_context_loading.json'
 counts={};checks=[]
 if state_path.exists():
  state=json.loads(state_path.read_text())
  if state['built_at']!=manifest['built_at']:raise ValueError('A different context import is pending')
  stage=state['stage'];counts=state['completed']
 else:
  command(f'CREATE SCHEMA {q(stage)};')
  state=dict(stage=stage,built_at=manifest['built_at'],completed={},status='loading')
  state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2))
 con=duckdb.connect();con.execute("SET threads=2; SET memory_limit='4GB'")
 try:
  for t in manifest['tables']:
   name=t['name']
   if name in counts:continue
   path=DATA/t['path'];fields=pq.ParquetFile(path).schema_arrow
   command(f'DROP TABLE IF EXISTS {q(stage)}.{q(name)} CASCADE;')
   command(f'CREATE TABLE {q(stage)}.{q(name)} ('+','.join(q(f.name)+' '+pgtype(f) for f in fields)+');')
   csv=DATA/('.copy_'+name+'.csv')
   projection=','.join(('to_json('+q(f.name)+') AS '+q(f.name)) if pa.types.is_nested(f.type) else q(f.name) for f in fields)
   con.execute(f"COPY (SELECT {projection} FROM read_parquet({lit(path)})) TO {lit(csv)} (FORMAT CSV, HEADER FALSE, NULL '\\N', FORCE_QUOTE *)")
   args=['docker','exec','-i',C['container'],'psql','-X','-v','ON_ERROR_STOP=1','-U',C['user'],'-d',C['database']]
   # Stream DuckDB's CSV unchanged, keeping empty strings, null and literal \N distinct.
   with (DATA/'.copy_stderr').open('wb') as err:
    proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=err)
    try:
     proc.stdin.write(f"COPY {q(stage)}.{q(name)} FROM STDIN WITH (FORMAT CSV, NULL '\\N');\n".encode())
     with csv.open('rb') as f:
      while block:=f.read(4*1024*1024):proc.stdin.write(block)
     proc.stdin.write(b'\\.\n');proc.stdin.close()
     if proc.wait():raise RuntimeError((DATA/'.copy_stderr').read_text())
    except BaseException:
     proc.kill();proc.wait();raise
   csv.unlink()
   if t['primary_key']:command(f'ALTER TABLE {q(stage)}.{q(name)} ADD PRIMARY KEY ('+','.join(q(c) for c in t['primary_key'])+');')
   for cols in t['indices']:command(f'CREATE INDEX ON {q(stage)}.{q(name)} ('+','.join(q(c) for c in cols)+');')
   command(f'ANALYZE {q(stage)}.{q(name)};')
   count=int(command(f'SELECT count(*) FROM {q(stage)}.{q(name)}',True))
   if count!=t['rows']:raise ValueError('Count mismatch '+name)
   counts[name]=count;state['completed']=counts;state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2));print(name,count,'loaded',flush=True)
  S=q(stage)
  relations=[('ppi_membership','record_id','ppi_interaction','record_id'),('ppi_membership','dataset_id','context_dataset','dataset_id'),('ppi_participant','record_id','ppi_interaction','record_id'),('ppi_protein_link','record_id','ppi_interaction','record_id'),('expression_gene','hgnc_id','context_gene','hgnc_id'),('expression_context','dataset_id','context_dataset','dataset_id')]
  for t in ['gtex_qtl_pair','gtex_qtl_summary','eqtlgen_cis','qtlbase_association']:
   relations += [(t,'hgnc_id','context_gene','hgnc_id'),(t,'dataset_id','context_dataset','dataset_id')]
  for t,c,p,pc in relations:command(f'ALTER TABLE {S}.{q(t)} ADD FOREIGN KEY ({q(c)}) REFERENCES {S}.{q(p)}({q(pc)});')
  # Reconstruct original observation without storing participant JSON twice.
  command(f'''CREATE OR REPLACE VIEW {S}.ppi_record AS SELECT i.record_id,i.provider,i.details_json || coalesce(p.fields,'{{}}'::jsonb) details_json FROM {S}.ppi_interaction i LEFT JOIN LATERAL (SELECT jsonb_object_agg(e.key,e.value) fields FROM {S}.ppi_participant p,jsonb_each(p.details_json) e WHERE p.record_id=i.record_id) p ON true''')
  views=['ppi_record']
  for t in manifest['tables']:
   if 'dataset_id' not in t or not t['name'].startswith('expression_'):continue
   name=t['name'];did=lit(t['dataset_id']);v=name+'_detail'
   command(f"CREATE OR REPLACE VIEW {S}.{q(v)} AS SELECT r.*,g.hgnc_id,{did}::text dataset_id,c.details_json context_json FROM {S}.{q(name)} r JOIN {S}.expression_gene g ON r.source_gene_id=g.source_gene_id AND g.dataset_id={did} JOIN {S}.expression_context c ON r.context_id=c.context_id AND c.dataset_id={did}")
   # Every projected observation must retain its gene and context links.
   lost=int(command(f"SELECT count(*) FROM {S}.{q(name)} r WHERE NOT EXISTS (SELECT 1 FROM {S}.expression_gene g WHERE r.source_gene_id=g.source_gene_id AND g.dataset_id={did}) OR NOT EXISTS (SELECT 1 FROM {S}.expression_context c WHERE r.context_id=c.context_id AND c.dataset_id={did})",True))
   if lost:raise ValueError('Expression relationships lost '+name)
   views.append(v)
  command(f'DROP TABLE IF EXISTS {S}._build_manifest; CREATE TABLE {S}._build_manifest (data_version text PRIMARY KEY,manifest jsonb); INSERT INTO {S}._build_manifest VALUES ({lit(manifest["data_version"])},{lit(json.dumps(manifest,ensure_ascii=False))}::jsonb)')
  # Real indexed gene and PPI lookups, bounded result sets.
  for table,key in [('qtlbase_association','hgnc_id'),('gtex_qtl_pair','hgnc_id'),('eqtlgen_cis','hgnc_id'),('ppi_protein_link','target_accession'),('expression_rna_cancer_sample','source_gene_id')]:
   val=command(f'SELECT {q(key)} FROM {S}.{q(table)} LIMIT 1',True).strip()
   plan=command(f'EXPLAIN (ANALYZE,BUFFERS) SELECT * FROM {S}.{q(table)} WHERE {q(key)}={lit(val)} LIMIT 30',True)
   checks.append(dict(table=table,key=val,plan=plan))
  exists=command("SELECT count(*) FROM pg_namespace WHERE nspname='web_context'",True).strip()=='1'
  sql='BEGIN; SELECT pg_advisory_xact_lock(20260921,3);'
  if exists:sql+='ALTER SCHEMA web_context RENAME TO '+q(stage+'_old')+';'
  sql+='ALTER SCHEMA '+S+' RENAME TO web_context;'
  if exists:sql+='DROP SCHEMA '+q(stage+'_old')+' CASCADE;'
  command(sql+'COMMIT;')
 except BaseException as exc:
  state.update(status='failed_staging_preserved',error=str(exc));state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2));raise
 state_path.unlink()
 report=dict(status='imported_validated',data_version=manifest['data_version'],schema='web_context',tables=counts,views=views,checks=checks,elapsed_seconds=round(time.time()-begin,2),deferred=manifest['deferred'])
 (WEB/'data/postgresql_context_import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['tables','checks']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
