"""Local PostgreSQL bootstrap and transactional service-schema replacement."""
from __future__ import annotations
import argparse,json,math,os,secrets,subprocess,time
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from service_views import statements
WEB=Path(__file__).resolve().parents[2]
C=yaml.safe_load((WEB/'config/database.yaml').read_text())
TABLES=WEB/'data/tables'
def q(s):return '"'+s.replace('"','""')+'"'
def command(sql,tuples=False):
 args=['docker','exec','-i',C['container'],'psql','-X','-v','ON_ERROR_STOP=1','-U',C['user'],'-d',C['database']]
 if tuples:args+=['-At']
 return subprocess.run(args,input=sql,text=True,check=True,capture_output=True).stdout

def start():
 env=WEB/C['credentials_file']
 if not env.exists():
  fd=os.open(env,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'w') as f:f.write(f"POSTGRES_USER={C['user']}\nPOSTGRES_DB={C['database']}\nPOSTGRES_PASSWORD={secrets.token_urlsafe(32)}\n")
 inspect=subprocess.run(['docker','container','inspect',C['container']],capture_output=True,text=True)
 if inspect.returncode:
  storage=WEB/C['storage'];storage.mkdir(exist_ok=True)
  subprocess.run(['docker','run','-d','--name',C['container'],'--restart','unless-stopped','--env-file',str(env),
   '-p',f"{C['host']}:{C['port']}:5432",'-v',f'{storage}:/var/lib/postgresql/data',C['image']],check=True,capture_output=True)
 else:
  actual=json.loads(inspect.stdout)[0]
  mounts=[m for m in actual['Mounts'] if m['Destination']=='/var/lib/postgresql/data']
  if not mounts or Path(mounts[0]['Source'])!=(WEB/C['storage']).resolve():raise ValueError('Container storage differs; refusing reuse')
  if not actual['State']['Running']:subprocess.run(['docker','start',C['container']],check=True,capture_output=True)
 for attempt in range(30):
  r=subprocess.run(['docker','exec',C['container'],'pg_isready','-U',C['user'],'-d',C['database']],capture_output=True)
  if not r.returncode:return
  time.sleep(1)
 raise RuntimeError('PostgreSQL did not become ready')

def sqltype(field):
 t=field.type
 if pa.types.is_boolean(t):return 'boolean'
 if pa.types.is_integer(t):return 'bigint'
 if pa.types.is_floating(t):return 'double precision'
 if pa.types.is_list(t) or pa.types.is_large_list(t) or pa.types.is_struct(t):return 'jsonb'
 if field.name.endswith('_json') or field.name in ['raw_attributes']:return 'jsonb'
 return 'text'

def encode(value,kind):
 if value is None:return '\\N'
 if kind=='jsonb':
  value=json.dumps(json.loads(value) if isinstance(value,str) else value,ensure_ascii=False,separators=(',',':'),allow_nan=False)
 elif isinstance(value,bool):value='true' if value else 'false'
 else:value=str(value)
 if '\x00' in value:raise ValueError('PostgreSQL cannot store NUL; source requires explicit repair')
 return '"'+value.replace('"','""')+'"'

def import_table(stage,t):
 path=TABLES/t['path'];file=pq.ParquetFile(path);schema=file.schema_arrow
 types=[sqltype(f) for f in schema]
 if any(len(f.name.encode())>63 for f in schema):raise ValueError('PostgreSQL identifier too long')
 command(f'CREATE TABLE {q(stage)}.{q(t["name"])} ('+', '.join(q(f.name)+' '+typ for f,typ in zip(schema,types))+');')
 args=['docker','exec','-i',C['container'],'psql','-X','-v','ON_ERROR_STOP=1','-U',C['user'],'-d',C['database']]
 proc=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  proc.stdin.write(f"COPY {q(stage)}.{q(t['name'])} FROM STDIN WITH (FORMAT CSV, NULL '\\N');\n")
  for batch in file.iter_batches(batch_size=8192):
   cols=[x.to_pylist() for x in batch.columns]
   text=''.join(','.join(encode(v,k) for v,k in zip(row,types))+'\n' for row in zip(*cols))
   proc.stdin.write(text)
  proc.stdin.write('\\.\n');proc.stdin.close()
  out=proc.stdout.read();err=proc.stderr.read();code=proc.wait()
  if code:raise RuntimeError(f'{t["name"]}: COPY failed: {err}')
 except BaseException:
  proc.kill();proc.wait();raise
 if t['primary_key']:
  command(f'ALTER TABLE {q(stage)}.{q(t["name"])} ADD PRIMARY KEY ('+', '.join(q(x) for x in t['primary_key'])+');')
 # Index the current protein/sequence entrypoints and site/region pagination.
 names=schema.names
 if 'accession' in names and (not t['primary_key'] or t['primary_key'][0]!='accession'):
  command(f'CREATE INDEX ON {q(stage)}.{q(t["name"])} (accession);')
 if 'sequence_id' in names:
  tail='target_position' if 'target_position' in names else 'position' if 'position' in names else 'ali_start' if 'ali_start' in names else 'start' if 'start' in names else None
  if tail:command(f'CREATE INDEX ON {q(stage)}.{q(t["name"])} (sequence_id, {q(tail)});')
 elif 'mapped_sequence_id' in names and 'start' in names:command(f'CREATE INDEX ON {q(stage)}.{q(t["name"])} (mapped_sequence_id, start);')
 if 'mapping_status' in names and 'target_position' in names:
  command(f'CREATE INDEX ON {q(stage)}.{q(t["name"])} (sequence_id, target_position) WHERE mapping_status=\'mapped\';')
 for col in ['record_id','site_id','uniprot_feature_id']:
  if col in names and (not t['primary_key'] or t['primary_key'][0]!=col):
   command(f'CREATE INDEX ON {q(stage)}.{q(t["name"])} ({q(col)});')
 command(f'ANALYZE {q(stage)}.{q(t["name"])};')
 count=int(command(f'SELECT count(*) FROM {q(stage)}.{q(t["name"])};',True).strip())
 if count!=t['rows']:raise ValueError(f'{t["name"]}: {count} != {t["rows"]}')
 print(t['name'],count,'loaded',flush=True)
 return count

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--start-only',action='store_true');args=parser.parse_args()
 start()
 if args.start_only:print('PostgreSQL ready on loopback port',C['port']);return
 manifest=json.loads((TABLES/'manifest.json').read_text());stage='web_loading_'+str(os.getpid())
 command(f'CREATE SCHEMA {q(stage)};')
 starttime=time.perf_counter();counts={}
 try:
  for table in manifest['tables']:counts[table['name']]=import_table(stage,table)
  # Scalar foreign keys; nested source arrays are validated before Parquet publication.
  relations=[('protein','default_sequence_id','protein_sequence','sequence_id'),('protein_function_overview','default_annotation_id','protein_function_annotation','annotation_id'),('protein_go_annotation','go_id','go_term','go_id'),('protein_pathway','pathway_id','pathway','pathway_id'),('protein_rhea_reaction','rhea_id','rhea_reaction','rhea_id'),('gtopdb_record','target_id','gtopdb_target','target_id'),('gtopdb_record','ligand_id','gtopdb_ligand','ligand_id')]
  # pathway has a composite source key; create a unique ID index for this Reactome-only snapshot.
  command(f'CREATE UNIQUE INDEX ON {q(stage)}.pathway (pathway_id);')
  for t,c,p,pc in relations:
   command(f'ALTER TABLE {q(stage)}.{q(t)} ADD FOREIGN KEY ({q(c)}) REFERENCES {q(stage)}.{q(p)} ({q(pc)});')
  for table in manifest['tables']:
   names=table['columns'];t=table['name']
   if 'accession' in names and t!='protein':command(f'ALTER TABLE {q(stage)}.{q(t)} ADD FOREIGN KEY (accession) REFERENCES {q(stage)}.protein (accession);')
   if 'sequence_id' in names and t!='protein_sequence':command(f'ALTER TABLE {q(stage)}.{q(t)} ADD FOREIGN KEY (sequence_id) REFERENCES {q(stage)}.protein_sequence (sequence_id);')
  for t,c,p,pc in [('membrane_biodolphin_site','interaction_id','membrane_biodolphin_interaction','interaction_id'),
                   ('go_slim_mapping','term_id','go_term','go_id'),('go_slim_mapping','category_id','go_term','go_id')]:
   command(f'ALTER TABLE {q(stage)}.{q(t)} ADD FOREIGN KEY ({q(c)}) REFERENCES {q(stage)}.{q(p)} ({q(pc)});')
  if 'ptm_record' in counts:
   for t,c,p,pc in [('ptm_record','uniprot_feature_id','uniprot_sequence_feature','feature_id'),('ptm_record_site','record_id','ptm_record','record_id'),('ptm_record_site','site_id','sequence_site','site_id'),('ptm_evidence','record_id','ptm_record','record_id'),('pfam_hit','pfam_accession','pfam_entry','pfam_accession')]:
    command(f'ALTER TABLE {q(stage)}.{q(t)} ADD FOREIGN KEY ({q(c)}) REFERENCES {q(stage)}.{q(p)} ({q(pc)});')
   for table in manifest['tables']:
    if 'dataset_id' in table['columns'] and table['category']=='sequence' and table['name']!='sequence_dataset':
     command(f'ALTER TABLE {q(stage)}.{q(table["name"])} ADD FOREIGN KEY (dataset_id) REFERENCES {q(stage)}.sequence_dataset(dataset_id);')
   command(f'ALTER TABLE {q(stage)}.residue_conservation ADD FOREIGN KEY (sequence_id,dataset_id) REFERENCES {q(stage)}.conservation_sequence(sequence_id,dataset_id);')
   command(f'CREATE INDEX ptm_record_candidate_accessions_gin ON {q(stage)}.ptm_record USING gin(candidate_accessions) WHERE accession IS NULL;')
  views=[]
  for name,sql in statements(stage,manifest):
   command(sql);views.append(name)
  if 'ptm_record' in counts:
   from validate_sequence import validate_sequence
   sequence_validation=validate_sequence(stage,manifest)
  # Check reconstructed relationships before publishing the replacement schema.
  expected=counts['protein_external_reference']+counts['protein']+counts['protein_gene']
  actual=int(command(f'SELECT count(*) FROM {q(stage)}.protein_external_reference_all;',True))
  if actual!=expected:raise ValueError('Unified external references lost rows')
  missing=int(command(f"""SELECT count(*) FROM {q(stage)}.protein_external_reference_all
   WHERE database_name='RefSeq' AND (
    (identifier_type='protein' AND (url IS NULL OR url NOT LIKE '%/protein/%')) OR
    (nucleotide_id_full ~ '^(NM|XM|NR|XR|NC|NG|NT|NW|NZ)_[A-Za-z0-9]+([.][0-9]+)?$' AND nucleotide_url IS NULL) OR
    (nucleotide_id_full IS NULL AND nucleotide_url IS NOT NULL));""",True))
  if missing:raise ValueError('RefSeq view links invalid')
  command(f'CREATE TABLE {q(stage)}._build_manifest (built_at text PRIMARY KEY, manifest jsonb NOT NULL);')
  literal=json.dumps(manifest,ensure_ascii=False).replace("'","''")
  command(f"INSERT INTO {q(stage)}._build_manifest VALUES ('{manifest['built_at']}', '{literal}'::jsonb);")
  current=C['schema'];exists=command(f"SELECT count(*) FROM pg_namespace WHERE nspname='{current}';",True).strip()=='1'
  old=stage+'_old'
  sql='BEGIN;\n'
  if exists:sql+=f'ALTER SCHEMA {q(current)} RENAME TO {q(old)};\n'
  sql+=f'ALTER SCHEMA {q(stage)} RENAME TO {q(current)};\n'
  if exists:sql+=f'DROP SCHEMA {q(old)} CASCADE;\n'
  sql+='COMMIT;'
  command(sql)
  # A schema rename replaces the objects that were granted to the read-only API
  # role. Restore least-privilege access before the service can observe the new
  # schema; the role itself and its password are managed by api.db setup_reader.
  reader='memvar_api'
  if command(f"SELECT count(*) FROM pg_roles WHERE rolname='{reader}';",True).strip()=='1':
   command(f'GRANT USAGE ON SCHEMA {q(current)} TO {q(reader)};\n'
           f'GRANT SELECT ON ALL TABLES IN SCHEMA {q(current)} TO {q(reader)};\n'
           f'ALTER DEFAULT PRIVILEGES IN SCHEMA {q(current)} GRANT SELECT ON TABLES TO {q(reader)};')
  # Rebind cross-schema projections after replacing the shared protein schema.
  if command("SELECT count(*) FROM pg_namespace WHERE nspname='web_variant';",True).strip()=='1':
   from variant_views import statements as variant_statements
   for _,view_sql in variant_statements('web_variant'):command(view_sql)
  if command("SELECT count(*) FROM pg_namespace WHERE nspname='web_disease';",True).strip()=='1':
   from disease_views import statements as disease_statements
   for name,view_sql in disease_statements('web_disease'):
    command(f'DROP VIEW IF EXISTS web_disease.{q(name)} CASCADE;')
    command(view_sql)
   if command(f"SELECT count(*) FROM pg_roles WHERE rolname='{reader}';",True).strip()=='1':
    command(f'GRANT SELECT ON ALL TABLES IN SCHEMA web_disease TO {q(reader)};')
 except BaseException:
  command(f'DROP SCHEMA IF EXISTS {q(stage)} CASCADE;');raise
 report={'status':'imported','data_version':manifest['data_version'],'database':C['database'],'schema':C['schema'],'container':C['container'],'host':C['host'],'port':C['port'],'input_built_at':manifest['built_at'],'tables':counts,'table_count':len(counts),'views':views,'elapsed_seconds':round(time.perf_counter()-starttime,2),'storage':C['storage'],'validated':['all_row_counts','primary_keys','scalar_foreign_keys','nested_fields_JSONB','unified_reference_view','transactional_schema_swap']}
 if 'ptm_record' in counts:report['sequence_validation']=sequence_validation
 report['database_size_bytes']=int(command('SELECT pg_database_size(current_database());',True))
 (WEB/'data/postgresql_import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='tables'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
