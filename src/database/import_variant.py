"""Import the independently built variant schema without replacing other Web data."""
import argparse,glob,json,os,subprocess,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import psycopg
import pyarrow as pa,pyarrow.csv as pcsv,pyarrow.parquet as pq
from import_tables import WEB,C,start,command,q,sqltype
from variant_views import statements
DATA=WEB/'data/tables/variant'
def lit(s):return "'"+str(s).replace("'","''")+"'"
def copy_files(table,name,files,schema):
 credentials=dict(line.split('=',1) for line in (WEB/C['credentials_file']).read_text().splitlines() if '=' in line)
 with psycopg.connect(host=C['host'],port=C['port'],dbname=C['database'],user=C['user'],password=credentials['POSTGRES_PASSWORD']) as connection:
  with connection.cursor().copy(f"COPY {table} FROM STDIN WITH (FORMAT CSV, NULL '')") as copy:
   copied=0;next_report=1000000
   for file in files:
    if pq.ParquetFile(file).schema_arrow!=schema:raise ValueError('Partition schema mismatch '+name)
    for batch in pq.ParquetFile(file).iter_batches(batch_size=4096):
     arrays=[a.storage if isinstance(a,pa.ExtensionArray) else a for a in batch.columns]
     # Emit the exact widened Float32 value when the target column is double precision.
     arrays=[a.cast(pa.float64()) if pa.types.is_float32(a.type) else a for a in arrays]
     batch=pa.RecordBatch.from_arrays(arrays,names=batch.schema.names)
     sink=pa.BufferOutputStream();pcsv.write_csv(batch,sink,write_options=pcsv.WriteOptions(include_header=False))
     copy.write(sink.getvalue().to_pybytes())
     copied+=batch.num_rows
     if copied>=next_report:
      print(name,copied,'rows streamed',flush=True);next_report+=1000000
 return copied

def load(stage,t):
 begin=time.monotonic();files=sorted(glob.glob(str(DATA/t['path'])));schema=pq.ParquetFile(files[0]).schema_arrow
 if any(pa.types.is_nested(f.type) for f in schema):raise ValueError('Explicit JSON projection required')
 if any(len(f.name.encode())>63 for f in schema):raise ValueError('Column exceeds PostgreSQL limit')
 table=q(stage)+'.'+q(t['name'])
 command(f'DROP TABLE IF EXISTS {table}; CREATE TABLE {table} ('+','.join(q(f.name)+' '+sqltype(f) for f in schema)+');')
 if t['name']=='variant_source_record' and len(files)>1:
  with ThreadPoolExecutor(max_workers=4) as pool:
   futures=[pool.submit(copy_files,table,t['name'],files[i::4],schema) for i in range(4)]
   for f in as_completed(futures):f.result()
 else:copy_files(table,t['name'],files,schema)
 if t['primary_key']:command("SET maintenance_work_mem='512MB'; ALTER TABLE "+table+' ADD PRIMARY KEY ('+','.join(map(q,t['primary_key']))+');')
 for idx in t['indices']:command("SET maintenance_work_mem='512MB'; CREATE INDEX ON "+table+' ('+','.join(map(q,idx))+');')
 command(f'ANALYZE {table};')
 count=int(command(f'SELECT count(*) FROM {table}',True))
 if count!=t['rows']:raise ValueError('Count changed '+t['name'])
 print(t['name'],count,'loaded',round(time.monotonic()-begin,2),'seconds',flush=True)
 return t['name'],count

def validate(stage,manifest):
 s=q(stage);checks={}
 # The database enforces links in addition to prior Parquet checks.
 relations=[('variant_consequence',['variant_id'],'variant',['variant_id']),('variant_frequency',['variant_id'],'variant',['variant_id']),('variant_source_record',['dataset_id'],'variant_dataset',['dataset_id']),('variant_source_link',['variant_id'],'variant',['variant_id']),('variant_source_link',['record_id'],'variant_source_record',['record_id']),('variant_dbsnp',['variant_id'],'variant',['variant_id']),('variant_ddg_link',['prediction_id'],'ddg_prediction',['prediction_id']),('variant_ddg_link',['annotation_id','gene_id'],'variant_consequence',['annotation_id','gene_id']),('variant_ddg_status',['annotation_id','gene_id'],'variant_consequence',['annotation_id','gene_id'])]
 for i,(t,cols,p,pc) in enumerate(relations):
  key='variant_fk_'+str(i)
  exists=command(f"SELECT count(*) FROM pg_constraint WHERE conname={lit(key)} AND connamespace={lit(stage)}::regnamespace",True).strip()=='1'
  if not exists:command("SET work_mem='256MB'; "+f'ALTER TABLE {s}.{q(t)} ADD CONSTRAINT {q(key)} FOREIGN KEY ('+','.join(map(q,cols))+f') REFERENCES {s}.{q(p)} ('+','.join(map(q,pc))+');')
 checks['foreign_keys']=len(relations)
 print('foreign keys validated',flush=True)
 views=[]
 for name,sql in statements(stage):command(sql);views.append(name)
 for label,sql in {
  'canonical_ddg':f'SELECT count(*) FROM {s}.ddg_prediction d LEFT JOIN web.protein p ON d.accession=p.accession WHERE d.sequence_id IS DISTINCT FROM p.default_sequence_id',
  'ddg_ref_residue':f"SELECT count(*) FROM {s}.ddg_prediction d JOIN web.protein_sequence p USING(sequence_id) WHERE d.position<1 OR d.position>p.length OR substring(p.sequence FROM d.position::integer FOR 1)<>d.ref_aa",
  'ddg_variant_identity':f'SELECT count(*) FROM {s}.variant_ddg_link l JOIN {s}.variant_consequence c USING(annotation_id,gene_id) WHERE l.variant_id<>c.variant_id',
  'gene_identity':f'SELECT count(*) FROM {s}.variant_consequence c WHERE NOT EXISTS(SELECT 1 FROM web.protein_gene g WHERE g.hgnc_id=c.gene_id)',
 }.items():
  count=int(command(sql,True));checks[label]=count;print(label,count,flush=True)
  if count:raise ValueError(label+' failed '+str(count))
 # Compare actual stored values and structured annotations against bounded real rows.
 samples={}
 for t in manifest['tables']:
  path=sorted(glob.glob(str(DATA/t['path'])))[0]
  expected=next(pq.ParquetFile(path).iter_batches(batch_size=3)).to_pylist()
  for row in expected:
   where=' AND '.join(q(k)+'='+lit(row[k]) for k in t['primary_key'])
   actual=json.loads(command(f'SELECT row_to_json(x) FROM (SELECT * FROM {s}.{q(t["name"])} WHERE {where}) x',True))
   for f,v in row.items():
    if f.endswith('_json') and v is not None:v=json.loads(v)
    if actual[f]!=v:raise ValueError('Roundtrip '+t['name']+'.'+f)
  samples[t['name']]=len(expected)
 checks['sample_roundtrips']=samples
 frequency=json.loads(command(f"SELECT json_build_object('rows',count(*),'available',count(*) FILTER(WHERE frequency_status='available'),'source_af_missing',count(*) FILTER(WHERE frequency_status='source_af_missing'),'no_local_source',count(*) FILTER(WHERE frequency_status='no_local_source'),'zero_af',count(*) FILTER(WHERE \"AF_exomes\"=0)) FROM {s}.variant_frequency",True))
 source=json.loads((WEB.parent/manifest['inputs']['frequency']/'manifest.json').read_text())
 assert frequency['rows']==source['rows'] and frequency['zero_af']==source['zero_af']
 for k,n in source['frequency_status'].items():assert frequency[k]==n
 checks['frequency']=frequency
 checks['queries']={}
 queries={
  'protein_variant_page':f"SELECT c.annotation_id,c.variant_id,c.\"HGVSp\",f.\"AF_exomes\" FROM web.protein_gene g JOIN {s}.variant_consequence c ON c.gene_id=g.hgnc_id JOIN {s}.variant_frequency f USING(variant_id) WHERE g.accession='P00533' ORDER BY c.variant_id,c.annotation_id LIMIT 30",
  'canonical_site_ddg':f"SELECT * FROM {s}.canonical_ddg_site WHERE sequence_id='P00533' AND position=858",
  'variant_sources':f"SELECT * FROM {s}.variant_source_detail WHERE variant_id=(SELECT variant_id FROM {s}.variant_consequence WHERE gene_id='HGNC:3236' LIMIT 1)",
 }
 for name,sql in queries.items():checks['queries'][name]=command('EXPLAIN (ANALYZE,BUFFERS) '+sql,True)
 return checks,views

def main():
 p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=3);p.add_argument('--resume',action='store_true');args=p.parse_args()
 start();manifest=json.loads((DATA/'manifest.json').read_text());progress=WEB/'data/variant_import_progress.json';begin=time.monotonic()
 if args.resume:
  state=json.loads(progress.read_text());assert state['built_at']==manifest['built_at'];stage=state['stage']
  if state['status']=='imported_validated':
   print('This build is already imported and validated:',manifest['data_version']);return
 else:
  stage='web_variant_loading_'+str(os.getpid());command('CREATE SCHEMA '+q(stage));state=dict(status='loading',stage=stage,built_at=manifest['built_at'],tables={})
 state['status']='loading';state.pop('error',None)
 def save():progress.write_text(json.dumps(state,indent=2)+'\n')
 save()
 try:
  with ThreadPoolExecutor(max_workers=args.workers) as pool:
   fs=[pool.submit(load,stage,t) for t in manifest['tables'] if t['name'] not in state['tables']]
   errors=[]
   for f in as_completed(fs):
    try:
     name,count=f.result();state['tables'][name]=count;save()
    except Exception as e:errors.append(e);print('table load failed:',str(e),flush=True)
   if errors:raise errors[0]
  state['status']='validating';save();checks,views=validate(stage,manifest)
  command(f'CREATE TABLE IF NOT EXISTS {q(stage)}._build_manifest (data_version text PRIMARY KEY,manifest jsonb); DELETE FROM {q(stage)}._build_manifest; INSERT INTO {q(stage)}._build_manifest VALUES ({lit(manifest["data_version"])},{lit(json.dumps(manifest,ensure_ascii=False))}::jsonb);')
  target=manifest['schema'];exists=command('SELECT count(*) FROM pg_namespace WHERE nspname='+lit(target),True).strip()=='1';sql='BEGIN; SELECT pg_advisory_xact_lock(20260921,4);'
  if exists:sql+='ALTER SCHEMA '+q(target)+' RENAME TO '+q(stage+'_old')+';'
  sql+='ALTER SCHEMA '+q(stage)+' RENAME TO '+q(target)+';'
  if exists:sql+='DROP SCHEMA '+q(stage+'_old')+' CASCADE;'
  command(sql+'COMMIT;');state['status']='imported_validated';save()
  report=dict(status='imported_validated',resumed=args.resume,timing_scope='current invocation; previous successful copies retained on resume',data_version=manifest['data_version'],schema=target,input_built_at=manifest['built_at'],tables=state['tables'],views=views,checks=checks,elapsed_seconds=round(time.monotonic()-begin,2))
  report['schema_size_bytes']=int(command("SELECT coalesce(sum(pg_total_relation_size(c.oid)),0) FROM pg_class c JOIN pg_namespace n ON c.relnamespace=n.oid WHERE n.nspname="+lit(target)+" AND c.relkind='r'",True))
  (WEB/'data/postgresql_variant_import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False),flush=True)
 except BaseException as e:state.update(status='failed',error=str(e));save();raise
if __name__=='__main__':main()
