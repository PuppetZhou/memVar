"""Lossless variant service projections from the confirmed published snapshots."""
import argparse,csv,json,os,shutil,time
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
import duckdb,pyarrow.parquet as pq,yaml
WEB=Path(__file__).resolve().parents[2];ROOT=WEB.parent
CFG=yaml.safe_load((WEB/'config/variant.yaml').read_text())
I={k:ROOT/v for k,v in CFG['inputs'].items()}
def q(s):return '"'+s.replace('"','""')+'"'
def lit(s):return "'"+str(s).replace("'","''")+"'"
def read(p):return 'read_parquet('+lit(p)+')'
def cols(p):return pq.ParquetFile(p).schema_arrow.names
def payload(alias,names):return 'to_json(struct_pack('+','.join(q(n)+':='+alias+'.'+q(n) for n in names)+'))'
def conn(out):
 c=duckdb.connect();c.execute("SET threads=2; SET memory_limit='6GB'");c.execute('SET temp_directory='+lit(out/'tmp'));return c

def put(c,out,name,sql,keys,indices=()):
 path=out/(name+'.parquet')
 c.execute('COPY ('+sql+') TO '+lit(path)+' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 122880)')
 c.execute('CREATE OR REPLACE VIEW '+q(name)+' AS SELECT * FROM '+read(path))
 if keys:
  invalid=' OR '.join(q(k)+' IS NULL' for k in keys)
  if c.execute('SELECT count(*) FROM '+q(name)+' WHERE '+invalid).fetchone()[0]:raise ValueError(name+' null key')
  if c.execute('SELECT count(*) FROM (SELECT '+','.join(map(q,keys))+' FROM '+q(name)+' GROUP BY ALL HAVING count(*)>1)').fetchone()[0]:raise ValueError(name+' duplicate key')
 pf=pq.ParquetFile(path)
 return dict(name=name,path=name+'.parquet',rows=pf.metadata.num_rows,primary_key=list(keys),indices=list(indices),columns={f.name:str(f.type) for f in pf.schema_arrow})

def partition(part,out):
 out=Path(out);out.mkdir(parents=True);src=I['variant']/'partitions'/part;c=conn(out);tables=[];checks=[]
 for name in ['variant','prediction_variant','dbnsfp_status','dbsnp_status','representative_annotation','variant_vep','prediction_annotation','prediction_match','aloft_selected_evidence','dbnsfp_record','variant_source','dbsnp_evidence']:
  c.execute('CREATE VIEW '+q('s_'+name)+' AS SELECT * FROM '+read(src/(name+'.parquet')))
 # AlphaGenome projection is partitioned once before workers start.
 c.execute('CREATE VIEW ag AS SELECT * FROM '+read(out.parent.parent/'alphagenome'/ (part+'.parquet')))
 tables.append(put(c,out,'variant',"SELECT v.*,p.* EXCLUDE(variant_id),d.status AS dbnsfp_status,s.status AS dbsnp_status,a.* EXCLUDE(variant_id) FROM s_variant v JOIN s_prediction_variant p USING(variant_id) JOIN s_dbnsfp_status d USING(variant_id) JOIN s_dbsnp_status s USING(variant_id) JOIN ag a USING(variant_id)",['variant_id'],[['chrom','pos']]))
 # Identity duplicates are removed only after equality checks.
 repcols=cols(src/'representative_annotation.parquet');vepcols=cols(src/'variant_vep.parquet')
 common=set(repcols)&set(vepcols)-{'annotation_id'}
 if c.execute('SELECT count(*) FROM s_representative_annotation r JOIN s_variant_vep v USING(annotation_id) WHERE '+' OR '.join('r.'+q(n)+' IS DISTINCT FROM v.'+q(n) for n in sorted(common))).fetchone()[0]:raise ValueError('VEP duplicate values differ')
 for a,b in [('variant_id','variant_id'),('gene_id','gene_id'),('selection_method','selection_method'),('Feature','transcript_id'),('ENSP','protein_id')]:
  if c.execute(f'SELECT count(*) FROM s_representative_annotation r JOIN s_prediction_annotation p USING(annotation_id,gene_id) WHERE r.{q(a)} IS DISTINCT FROM p.{q(b)}').fetchone()[0]:raise ValueError('Prediction identity differs: '+a)
 # Preserve prediction match rows and selected ALoFT slots with their actual context.
 mc=[n for n in cols(src/'prediction_match.parquet') if n not in ['variant_id','annotation_id','gene_id']]
 ac=[n for n in cols(src/'aloft_selected_evidence.parquet') if n not in ['variant_id','annotation_id','gene_id']]
 c.execute('CREATE TABLE match_detail AS SELECT annotation_id,gene_id,to_json(list(struct_pack('+','.join(q(n)+':=m.'+q(n) for n in mc)+'))) AS matches_json FROM s_prediction_match m GROUP BY annotation_id,gene_id')
 c.execute('CREATE TABLE aloft_detail AS SELECT annotation_id,gene_id,to_json(list(struct_pack('+','.join(q(n)+':=m.'+q(n) for n in ac)+'))) AS aloft_json FROM s_aloft_selected_evidence m GROUP BY annotation_id,gene_id')
 rc=[n for n in repcols if n not in ['chrom','pos','ref','alt']]
 vc=[n for n in vepcols if n not in repcols]
 pc=[n for n in cols(src/'prediction_annotation.parquet') if n not in ['annotation_id','variant_id','gene_id','transcript_id','protein_id','selection_method']]
 projection=[ 'r.'+q(n) for n in rc]+['v.'+q(n) for n in vc]+['p.'+q(n) for n in pc]+['m.matches_json','a.aloft_json']
 sql='SELECT '+','.join(projection)+' FROM s_representative_annotation r JOIN s_variant_vep v USING(annotation_id) JOIN s_prediction_annotation p USING(annotation_id,gene_id) LEFT JOIN match_detail m USING(annotation_id,gene_id) LEFT JOIN aloft_detail a USING(annotation_id,gene_id)'
 tables.append(put(c,out,'variant_consequence',sql,['annotation_id','gene_id'],[['gene_id','variant_id','annotation_id'],['variant_id']]))
 # Scientific source annotations remain intact; common metadata are stored once.
 sources=[]
 for source,dataset,idcol in [('clinvar','clinvar_20260906','VariationID'),('cosmic','cosmic_v104','ID'),('gnomad','gnomad_exomes_4.1','ID')]:
  f=src/(source+'_record.parquet')
  if not f.exists():continue
  ns=[n for n in cols(f) if n!='source_row_id']
  sources.append('SELECT r.source_row_id AS record_id,'+lit(dataset)+' AS dataset_id,CAST(r.'+q(idcol)+' AS VARCHAR) AS native_id,'+payload('r',ns)+' AS details_json FROM '+read(f)+' r')
 ns=[n for n in cols(src/'dbnsfp_record.parquet') if n not in ['variant_id','dbnsfp_row_id']]
 sources.append("SELECT dbnsfp_row_id AS record_id,'dbnsfp_5.4a' AS dataset_id,dbnsfp_row_id AS native_id,"+payload('r',ns)+' AS details_json FROM s_dbnsfp_record r')
 tables.append(put(c,out,'variant_source_record',' UNION ALL '.join(sources),['record_id'],[['dataset_id','native_id']]))
 tables.append(put(c,out,'variant_source_link',"SELECT variant_id,source_row_id AS record_id,alt_index FROM s_variant_source UNION ALL SELECT variant_id,dbnsfp_row_id,1::BIGINT FROM s_dbnsfp_record",['variant_id','record_id','alt_index'],[['record_id']]))
 tables.append(put(c,out,'variant_dbsnp','SELECT DISTINCT * FROM s_dbsnp_evidence',['variant_id','rsid','source_contig','source_pos','source_ref','source_alt','source_alt_index'],[['rsid']]))
 fq=I['frequency']/'partitions'/part/'variant_frequency.parquet'
 fs=[n for n in cols(fq) if n!='filters']
 tables.append(put(c,out,'variant_frequency','SELECT '+','.join(map(q,fs))+',to_json(filters) AS filters_json FROM '+read(fq),['variant_id']))
 # Numeric/state fidelity uses null-safe exact equality, not rounded exports.
 for outname,source,key,names in [('variant','s_prediction_variant','variant_id',cols(src/'prediction_variant.parquet')[1:]),('variant_consequence','s_prediction_annotation','annotation_id,gene_id',pc)]:
  condition=' OR '.join('o.'+q(n)+' IS DISTINCT FROM i.'+q(n) for n in names)
  if c.execute(f'SELECT count(*) FROM {q(outname)} o JOIN {source} i USING({key}) WHERE {condition}').fetchone()[0]:raise ValueError('Score/state changed')
 for output,input_name,key in [('variant','s_variant','variant_id'),('variant_consequence','s_representative_annotation','annotation_id,gene_id')]:
  if c.execute(f'SELECT count(*) FROM {output}').fetchone()!=c.execute(f'SELECT count(*) FROM {input_name}').fetchone():raise ValueError('Record coverage changed')
 if c.execute('SELECT count(*) FROM variant_source_link l ANTI JOIN variant_source_record r USING(record_id)').fetchone()[0]:raise ValueError('Lost source record')
 if c.execute('SELECT count(*) FROM variant_source_link l ANTI JOIN variant v USING(variant_id)').fetchone()[0]:raise ValueError('Lost variant')
 if c.execute('SELECT count(*) FROM variant_frequency f ANTI JOIN variant v USING(variant_id)').fetchone()[0]:raise ValueError('Frequency identity')
 for source,dataset in [('clinvar','clinvar_20260906'),('cosmic','cosmic_v104'),('gnomad','gnomad_exomes_4.1')]:
  f=src/(source+'_record.parquet')
  if not f.exists():continue
  ns=[n for n in cols(f) if n!='source_row_id']
  if c.execute('SELECT count(*) FROM '+read(f)+' r JOIN variant_source_record o ON r.source_row_id=o.record_id WHERE o.details_json IS DISTINCT FROM '+payload('r',ns)).fetchone()[0]:raise ValueError('Source annotations changed')
 c.close();shutil.rmtree(out/'tmp',ignore_errors=True)
 result=dict(partition=part,tables=tables,checks=['keys','source_links','VEP_duplicate_equality','prediction_identity','all_dbNSFP_values_and_states','source_annotation_JSON_roundtrip','coverage'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=4);p.add_argument('--resume');args=p.parse_args()
 out=Path(args.resume) if args.resume else WEB/'data'/('.variant_build_'+str(os.getpid()));out.mkdir(exist_ok=bool(args.resume));begin=time.monotonic()
 status={'status':'building','temporary_directory':str(out),'data_version':CFG['data_version']}
 def state():(out/'status.json').write_text(json.dumps(status,indent=2)+'\n')
 state();c=conn(out)
 try:
  parts=sorted(p.name for p in (I['variant']/'partitions').iterdir())
  ag=out/'alphagenome';ag.mkdir(exist_ok=True)
  if not all((ag/(p+'.parquet')).exists() for p in parts):
   c.execute('CREATE TABLE ag AS SELECT a.*,s.* EXCLUDE(variant_id) FROM '+read(I['alphagenome']/'variant_alphagenome.parquet')+' a JOIN '+read(I['alphagenome']/'variant_alphagenome_status.parquet')+' s USING(variant_id)')
   for part in parts:
    c.execute('COPY (SELECT * FROM ag WHERE split_part(variant_id,\':\',2)='+lit(part)+') TO '+lit(ag/(part+'.parquet'))+' (FORMAT PARQUET, COMPRESSION ZSTD)')
   c.execute('DROP TABLE ag')
  results=[]
  with ProcessPoolExecutor(max_workers=args.workers) as pool:
   futures=[]
   for part in parts:
    dest=out/'partitions'/part
    if (dest/'result.json').exists():results.append(json.loads((dest/'result.json').read_text()));continue
    if dest.exists():shutil.rmtree(dest)
    futures.append(pool.submit(partition,part,str(dest)))
   for f in as_completed(futures):
    r=f.result();results.append(r);status['completed_partitions']=len(results);state();print(r['partition'],[(t['name'],t['rows']) for t in r['tables']],flush=True)
  tables=[]
  for t in results[0]['tables']:
   t=dict(t);t['path']='partitions/*/'+t['name']+'.parquet';t['rows']=sum(next(x['rows'] for x in r['tables'] if x['name']==t['name']) for r in results);tables.append(t)
  shared=out/'shared';shared.mkdir(exist_ok=True)
  canonical=WEB/'data/tables/identity/protein.parquet'
  pred=I['ddg']/'prediction.parquet';link=I['ddg']/'variant_prediction.parquet'
  tables.append(put(c,shared,'ddg_prediction','SELECT d.* FROM '+read(pred)+' d JOIN '+read(canonical)+' p ON p.accession=d.accession AND p.default_sequence_id=d.sequence_id',['prediction_id'],[['sequence_id','position','ref_aa','alt_aa']]))
  tables.append(put(c,shared,'variant_ddg_link','SELECT l.* EXCLUDE(reference_protein_id,reference_position,ref_aa,alt_aa) FROM '+read(link)+' l JOIN ddg_prediction d USING(prediction_id)',['annotation_id','gene_id','prediction_id'],[['variant_id'],['prediction_id']]))
  tables.append(put(c,shared,'variant_ddg_status','SELECT * FROM '+read(I['ddg']/'variant_prediction_status.parquet'),['annotation_id','gene_id'],[['variant_id']]))
  # Removed link columns must remain exactly reconstructible from the source status.
  ddg_status=I['ddg']/'variant_prediction_status.parquet'
  mismatch=c.execute('SELECT count(*) FROM '+read(link)+' l JOIN '+read(ddg_status)+' s USING(annotation_id,gene_id) JOIN '+read(pred)+' p USING(prediction_id) WHERE l.reference_protein_id IS DISTINCT FROM s.reference_protein_id OR l.reference_position IS DISTINCT FROM s.aa_position OR l.ref_aa IS DISTINCT FROM s.ref_aa OR l.alt_aa IS DISTINCT FROM s.alt_aa OR l.ref_aa IS DISTINCT FROM p.ref_aa OR l.alt_aa IS DISTINCT FROM p.alt_aa').fetchone()[0]
  if mismatch:raise ValueError('ddG link fields cannot be reconstructed')
  rows=[dict(dataset_id=did,source=source,version=version,details_json=json.dumps(details,ensure_ascii=False)) for did,source,version,details in [
   ('clinvar_20260906','ClinVar','2026-09-06',{'input':str(I['variant'].relative_to(ROOT))}),('cosmic_v104','COSMIC','104',{'callset':'GenomeScreens Normal GRCh38'}),('gnomad_exomes_4.1','gnomAD','4.1',{'dataset':'exomes','frequency_input':CFG['inputs']['frequency']}),('dbnsfp_5.4a','dbNSFP','5.4a',{'raw_arrays':'preserved in source record','scores':58}),('dbsnp_157','dbSNP','157',{'allele_evidence':'variant_dbsnp'}),('vep_116','VEP','116',{'input':CFG['inputs']['variant']}),('alphagenome_atlas','AlphaGenome',None,{'input':CFG['inputs']['alphagenome'],'scope':'variant'}),('ddg_20260917','ThermoMPNN','20260917_ddg_thermompnn_01',{'input':CFG['inputs']['ddg'],'scope':'canonical substitution'})]]
  import pyarrow as pa
  c.register('dataset_rows',pa.Table.from_pylist(rows));tables.append(put(c,shared,'variant_dataset','SELECT * FROM dataset_rows',['dataset_id']))
  dictionary=[]
  pv=cols(I['variant']/'partitions'/'1'/'prediction_variant.parquet')
  for row in csv.DictReader(I['field_dictionary'].open(),delimiter='\t'):
   dictionary.append(dict(field=row['field'],source='dbNSFP',scope='variant' if row['field'] in pv else 'transcript_consequence',tool=row['tool'],details_json=json.dumps(row,ensure_ascii=False)))
  c.register('dictionary_rows',pa.Table.from_pylist(dictionary));tables.append(put(c,shared,'variant_prediction_field','SELECT * FROM dictionary_rows',['field']))
  for t in tables:
   if not t['path'].startswith('partitions/'):t['path']='shared/'+t['path']
  expected=json.loads((I['variant']/'manifest.json').read_text())['rounds']['hgvsp']
  assert next(t['rows'] for t in tables if t['name']=='variant')==expected['variants']
  assert next(t['rows'] for t in tables if t['name']=='variant_consequence')==expected['rows']
  manifest=dict(data_version=CFG['data_version'],built_at=datetime.now(timezone.utc).isoformat(),schema=CFG['schema'],inputs=CFG['inputs'],tables=tables,validation={'status':'passed','partitions':len(results),'checks':results[0]['checks']},elapsed_seconds=round(time.monotonic()-begin,2))
  (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  c.close();shutil.rmtree(ag);shutil.rmtree(out/'tmp',ignore_errors=True)
  status['status']='built_validated';state()
  dest=WEB/'data/tables/variant';previous=dest.with_name('.variant_previous')
  if previous.exists():raise RuntimeError('Inspect previous interrupted publication')
  if dest.exists():os.replace(dest,previous)
  try:os.replace(out,dest)
  except BaseException:
   if previous.exists():os.replace(previous,dest)
   raise
  if previous.exists():shutil.rmtree(previous)
  print(json.dumps({'status':'built_validated','tables':len(tables),'path':str(dest)}),flush=True)
 except BaseException as e:status.update(status='failed',error=str(e));state();raise
if __name__=='__main__':main()
