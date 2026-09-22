"""Lossless service projections for context; isolated from concurrent Web builds."""
from pathlib import Path
import json, os, shutil, time, gzip, csv, sys
from datetime import datetime, timezone
import duckdb, yaml, pyarrow as pa, pyarrow.parquet as pq
WEB=Path(__file__).resolve().parents[2]; ROOT=WEB.parent
CFG=yaml.safe_load((WEB/'config/context.yaml').read_text())
I={k:ROOT/v for k,v in CFG['inputs'].items()}
def q(s): return '"'+s.replace('"','""')+'"'
def lit(s): return "'"+str(s).replace("'","''")+"'"
def read(p): return f'read_parquet({lit(p)},union_by_name=true)'
class Build:
 def __init__(self):
  self.out=Path(sys.argv[2]) if len(sys.argv)>2 and sys.argv[1]=='--resume' else WEB/'data'/f'.context_build_{os.getpid()}'; self.out.mkdir(exist_ok=True)
  self.con=duckdb.connect(str(self.out/'work.duckdb'));self.con.execute("SET memory_limit='8GB'; SET threads=4")
  self.tables=[];self.datasets=[];self.checks=[]
 def put(self,name,sql,keys=(),indices=()):
  path=self.out/(name+'.parquet')
  if not path.exists():self.con.execute(f'COPY ({sql}) TO {lit(path)} (FORMAT PARQUET, COMPRESSION ZSTD)')
  pf=pq.ParquetFile(path)
  self.tables.append(dict(name=name,path=path.name,rows=pf.metadata.num_rows,primary_key=list(keys),indices=list(indices),columns={f.name:str(f.type) for f in pf.schema_arrow}))
  self.con.execute(f'CREATE OR REPLACE VIEW {q(name)} AS SELECT * FROM {read(path)}')
  print(name,pf.metadata.num_rows,flush=True)
 def dataset(self,id,provider,type,details):
  row=dict(dataset_id=id,provider=provider,kind=type,details_json=json.dumps(details,ensure_ascii=False))
  existing=next((r for r in self.datasets if r['dataset_id']==id),None)
  if existing and existing!=row:raise ValueError('Dataset definition conflict '+id)
  if not existing:self.datasets.append(row)
 def qtl(self):
  root=I['qtl']; pairs=[];summary=[]
  for f in sorted((root/'gtex').glob('*.parquet')):
   kind,role=f.stem.split('_',1); src=read(f)
   tissues=[r[0] for r in self.con.execute(f'SELECT DISTINCT tissue FROM {src}').fetchall()]
   for tissue in tissues:self.dataset('gtex:'+kind+':'+tissue,'GTEx',kind,dict(tissue=tissue,version='v11',assembly='GRCh38'))
   # Keep all source measurements; gene names belong to source contexts, not global aliases.
   sql=f"SELECT 'gtex:{kind}:'||tissue AS dataset_id, * EXCLUDE(tissue), row_number() OVER () AS source_row FROM {src}"
   (pairs if role=='pairs' else summary).append(sql)
  self.put('gtex_qtl_pair',' UNION ALL BY NAME '.join(pairs),indices=[['hgnc_id','dataset_id']])
  self.put('gtex_qtl_summary',' UNION ALL BY NAME '.join(summary),indices=[['hgnc_id','dataset_id']])
  self.dataset('eqtlgen:cis','eQTLGen','cis',dict(version='2019-12',assembly='GRCh37',background='study-level blood/PBMC'))
  self.put('eqtlgen_cis',f"SELECT 'eqtlgen:cis' dataset_id,* FROM {read(root/'eqtlgen/cis_eqtl.parquet')}",indices=[['hgnc_id']])
  ds=pq.read_table(root/'qtlbase/datasets.parquet').to_pylist()
  for r in ds:self.dataset('qtlbase:'+r['Sourceid'],'QTLbase',r['xQTL'],dict(r,version='2',assembly='source hg19 and hg38'))
  union=[]
  for f in sorted((root/'qtlbase').glob('*.parquet')):
   if f.stem=='datasets':continue
   union.append(f"SELECT 'qtlbase:'||Sourceid dataset_id,{lit(f.stem)} qtl_type,* EXCLUDE(Sourceid) FROM {read(f)}")
  self.put('qtlbase_association',' UNION ALL BY NAME '.join(union),indices=[['hgnc_id','dataset_id']])
  self.put('qtl_context_count'," UNION ALL ".join(f"SELECT {lit(t)} table_name,hgnc_id,dataset_id,count(*) record_count FROM {q(t)} GROUP BY hgnc_id,dataset_id" for t in ['gtex_qtl_pair','eqtlgen_cis','qtlbase_association']),['table_name','hgnc_id','dataset_id'])
 def ppi(self):
  root=I['ppi'];records=[];members=[]
  for d in pq.read_table(root/'ppi_dataset.parquet').to_pylist():
   f=ROOT/d['cleaned_file']; mf=ROOT/d['mapping_file'];cols=pq.ParquetFile(f).schema_arrow.names
   self.dataset(d['dataset_id'],d['source'],d['kind'],{k:d[k] for k in ['context_raw','source_release']})
   rawcols=[c for c in cols if not c.startswith('ppi_') and 'Checksum' not in c]
   # Struct equality verifies complete source content; never pair-name deduplication.
   payload='to_json(struct_pack('+','.join(q(c)+':='+q(c) for c in rawcols)+'))'
   records.append(f"SELECT r.ppi_record_id source_record_id,r.ppi_dataset_id dataset_id,{lit(d['source'])} provider,{payload} details_json, m.endpoint_a_status,m.endpoint_b_status,m.mutation_coordinate_status FROM {read(f)} r JOIN {read(mf)} m ON r.ppi_record_id=m.record_id WHERE m.project_related")
  self.con.execute('CREATE TABLE IF NOT EXISTS ppi_raw AS '+' UNION ALL BY NAME '.join(records))
  self.con.execute('CREATE TABLE IF NOT EXISTS ppi_unique AS SELECT provider,details_json,min(source_record_id) record_id FROM ppi_raw GROUP BY provider,details_json')
  self.put('ppi_record','SELECT record_id,provider,details_json FROM ppi_unique',['record_id'])
  self.put('ppi_membership','SELECT u.record_id,r.* EXCLUDE(provider,details_json) FROM ppi_raw r JOIN ppi_unique u USING(provider,details_json)',['source_record_id'],[['record_id'],['dataset_id']])
  self.put('ppi_protein_link',f"SELECT DISTINCT m.record_id,l.* EXCLUDE(record_id) FROM {read(root/'endpoint_link/**/*.parquet')} l JOIN ppi_membership m ON l.record_id=m.source_record_id",indices=[['target_accession','record_id'],['record_id']])
  # Participant data are original fields from each record, not inferred protein entities.
  pairs="list_zip(json_keys(details_json),json_extract(details_json,'$.*'))"
  def fields(pattern,invert=False):
   test=f"regexp_matches(x[1], {lit(pattern)})"
   if invert:test='NOT '+test
   return "to_json(map_from_entries(list_transform(list_filter("+pairs+", x -> "+test+"), x -> struct_pack(key := x[1], value := x[2]))))"
  a_fields=fields('(?i)(interactor|participant) A');b_fields=fields('(?i)(interactor|participant) B')
  sql=f"SELECT record_id,'A' endpoint,{a_fields} details_json FROM ppi_unique UNION ALL SELECT record_id,'B' endpoint,{b_fields} details_json FROM ppi_unique"
  self.put('ppi_participant',f"SELECT * FROM ({sql}) WHERE details_json!='{{}}'",['record_id','endpoint'])
  other=fields('(?i)(interactor|participant) [AB]',True)
  self.put('ppi_interaction',f'SELECT record_id,provider,{other} details_json FROM ppi_unique',['record_id'])
  self.tables=[t for t in self.tables if t['name']!='ppi_record'];(self.out/'ppi_record.parquet').unlink()
  self.checks.append(dict(ppi_source_rows=self.con.execute('SELECT count(*) FROM ppi_raw').fetchone()[0],ppi_content_records=self.con.execute('SELECT count(*) FROM ppi_unique').fetchone()[0]))
 def expression(self):
  gene=read(I['gene_ensembl']); backgrounds=[];genenames=[]
  for f in sorted(I['hpa'].glob('*.parquet')):
   n=f.stem
   if n=='subcellular_location':continue
   did='hpa:'+n;cols=pq.ParquetFile(f).schema_arrow.names;src=read(f)
   provider='FANTOM' if 'fantom' in n else 'CPTAC' if n=='cancer_cptac' else 'HPA'
   self.dataset(did,provider,n,dict(provider_portal='HPA',version='25.1',unit_policy='original column names',source=f.name))
   gc='ensgid' if 'ensgid' in cols else 'Gene'
   genenames.append(f"SELECT DISTINCT {lit(did)} dataset_id,{q(gc)} source_gene_id,"+(q('Gene name') if 'Gene name' in cols else 'NULL::VARCHAR')+f' source_gene_name FROM {src}')
   if n=='transcript_rna_tissue':
    self.con.execute(f'CREATE VIEW hpa_tx AS SELECT * FROM {src}')
    # Paired measures stay together in each sample; all original text values retained.
    samples=[c[4:] for c in cols if c.startswith('TPM.')]
    parts=[f"SELECT {lit(did)} dataset_id,ensgid source_gene_id,enstid transcript_id,{lit(s)} sample_id,{q('TPM.'+s)} TPM,{q('est_counts.'+s)} est_counts FROM hpa_tx" for s in samples]
    self.put('expression_hpa_transcript',' UNION ALL '.join(parts),indices=[['source_gene_id']])
    continue
   dims=[c for c in cols if c in ['Cancer','Sample','sample_name','Tissue','IHC tissue name','Cell type','Cell type name','Cell line','Cluster','Source tissue','replicate_nr']]
   ctx='to_json(struct_pack('+','.join(q(c)+':='+q(c) for c in dims)+'))'
   self.con.execute(f'CREATE OR REPLACE TABLE expr_background AS SELECT row_number() OVER (ORDER BY details_json) context_id,* FROM (SELECT DISTINCT {ctx} details_json FROM {src})')
   backgrounds.append(self.con.execute(f'SELECT {lit(did)} dataset_id,context_id,details_json FROM expr_background').fetch_arrow_table())
   measurements=[c for c in cols if c not in dims+[gc,'Gene name']]
   sql=f'SELECT r.{q(gc)} source_gene_id,b.context_id,'+','.join('r.'+q(c) for c in measurements)+f' FROM {src} r JOIN expr_background b ON {ctx}=b.details_json'
   self.put('expression_'+n,sql,indices=[['source_gene_id','context_id']])
   self.tables[-1]['dataset_id']=did
  self.con.register('background_data',pa.concat_tables(backgrounds))
  self.put('expression_context','SELECT * FROM background_data',['dataset_id','context_id'])
  self.put('expression_gene',f"SELECT n.*,g.hgnc_id FROM ({' UNION ALL '.join(genenames)}) n LEFT JOIN {gene} g ON split_part(n.source_gene_id,'.',1)=g.ensembl_gene_id",['dataset_id','source_gene_id'])
  bad=self.con.execute('SELECT count(*) FROM expression_gene WHERE hgnc_id IS NULL').fetchone()[0]
  if bad:raise ValueError(f'Unknown HPA gene links: {bad}')
 def finish(self):
  self.con.register('datasets_data',pa.Table.from_pylist(self.datasets))
  self.put('context_dataset','SELECT * FROM datasets_data',['dataset_id'])
  self.put('context_gene',f'SELECT * FROM {read(I["gene_ensembl"])}',['hgnc_id'])
  # Lightweight all-table key/count checks; raw strings are not cast or rounded.
  for t in self.tables:
   if t['name']=='context_dataset':
    self.con.register('dedup_datasets',pa.Table.from_pylist(self.datasets))
    self.con.execute(f'COPY (SELECT * FROM dedup_datasets) TO {lit(self.out/t["path"])} (FORMAT PARQUET, COMPRESSION ZSTD)')
    t['rows']=len(self.datasets)
   if t['primary_key']:
    key=','.join(q(c) for c in t['primary_key']);bad=self.con.execute(f'SELECT count(*) FROM (SELECT {key},count(*) n FROM {q(t["name"])} GROUP BY ALL HAVING n>1)').fetchone()[0]
    if bad:raise ValueError('Duplicate key '+t['name'])
  manifest=dict(data_version=CFG['data_version'],built_at=datetime.now(timezone.utc).isoformat(),tables=self.tables,inputs=CFG['inputs'],deferred=CFG['deferred'],checks=self.checks,status='built_validated')
  (self.out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
  self.con.close();(self.out/'work.duckdb').unlink()
  dest=WEB/'data/context_tables'
  previous=WEB/'data/.context_previous'
  if previous.exists():raise ValueError('Interrupted context replacement requires inspection')
  if dest.exists():dest.rename(previous)
  try:self.out.rename(dest)
  except BaseException:
   if previous.exists():previous.rename(dest)
   raise
  if previous.exists():shutil.rmtree(previous)
if __name__=='__main__':
 b=Build();b.qtl();b.ppi();b.expression();b.finish()
