"""Disease service projection using existing mappings, with lossless detail reconstruction."""
import argparse,json,os,shutil,tempfile
from pathlib import Path
from datetime import datetime,timezone
import polars as pl
import yaml
WEB=Path(__file__).resolve().parents[2];ROOT=WEB.parent
CFG=yaml.safe_load((WEB/'config/disease.yaml').read_text());SRC=ROOT/CFG['inputs']['disease']['path']
def read(name):return pl.read_parquet(SRC/(name+'.parquet'))
def require(value,message):
 if not value:raise ValueError(message)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--replace',action='store_true');args=ap.parse_args()
 out=Path(tempfile.mkdtemp(prefix='.disease-',dir=WEB/'data'));catalog=[];checks=[];tables={}
 def put(name,df,key,meaning,indices=()):
  require(df.height>0,name+' empty')
  if key:
   require(df.select(pl.struct(key).n_unique()).item()==df.height,name+' duplicate key')
   require(not any(df[c].null_count() for c in key),name+' null key')
  df.write_parquet(out/(name+'.parquet'),compression='zstd');tables[name]=df
  catalog.append(dict(name=name,path=name+'.parquet',rows=df.height,primary_key=key,indices=list(indices),columns={k:str(v) for k,v in df.schema.items()},grain=meaning))
  print(name,df.height,flush=True)
 try:
  source=json.loads((SRC/'source_manifest.json').read_text())['sources']
  versions={k:str(v['version']) for k,v in source.items()};ds={k:'disease:'+k+':'+v for k,v in versions.items()}
  put('disease_dataset',pl.from_dicts([dict(dataset_id=ds[k],source=k,source_version=v,reference_url=source[k].get('reference_url'),snapshot=CFG['inputs']['disease']['version']) for k,v in versions.items()]),['dataset_id'],'来源版本最小字典')
  def dataset(df,source_name):
   if 'source_version' in df.columns:require(set(df['source_version'].drop_nulls())=={versions[source_name]},source_name+' version mismatch');df=df.drop('source_version')
   return df.with_columns(pl.lit(ds[source_name]).alias('dataset_id'))
  # Definitions are stored once per provider/version/text, all relationship provenance stays separate.
  definitions=[];lookup={}
  def define(text,provider,source_name):
   if text is None:return None
   key=(text,provider,ds[source_name])
   if key not in lookup:
    i='definition:'+str(len(lookup)+1);lookup[key]=i;definitions.append(dict(definition_id=i,definition=text,definition_source=provider,dataset_id=ds[source_name]))
   return lookup[key]
  entries=read('disease_entry');desc=read('disease_description');links=[]
  for n,r in enumerate(desc.iter_rows(named=True),1):
   base='MedGen' if r['definition_source'].startswith('MedGen/') else r['definition_source']
   require(r['source_version']==versions[base],'definition version')
   links.append(dict(definition_link_id=n,disease_id=r['disease_id'],definition_id=define(r['definition'],r['definition_source'],base),source_record=r['source_record'],via=r['via'],display_eligible=r['display_eligible']))
  entry_rows=[]
  for r in entries.iter_rows(named=True):
   text=r.pop('definition');provider=r.pop('definition_source');r['primary_definition_id']=define(text,provider,provider) if text is not None else None;entry_rows.append(r)
  entry=pl.from_dicts(entry_rows,infer_schema_length=None)
  om=read('omim_entry');joined=om.join(entries,on='disease_id')
  require(joined.filter(~pl.col('title').eq_missing(pl.col('name'))).height==0,'OMIM title differs')
  require(om.filter(pl.col('disease_id')!=(pl.lit('OMIM:')+pl.col('mim_number'))).height==0,'OMIM ID mismatch')
  om=om.drop('title','mim_number','source_version').rename({'entry_type':'omim_entry_type','prefix':'omim_prefix'})
  entry=entry.join(om,on='disease_id',how='left').join(read('disease_mapping_status'),on='disease_id',how='left')
  put('disease_entry',entry,['disease_id'],'来源疾病条目、OMIM专有属性和MONDO映射状态；定义为引用')
  # Full HPO/MONDO term and relationship dictionaries support existing hierarchy navigation.
  term_rows=[];parents=[];aliases=[];synonyms=[];xrefs=[]
  for ns in ['HPO','MONDO']:
   for r in read('reference/'+ns+'/terms').iter_rows(named=True):
    text=r.pop('definition');r['definition_id']=define(text,ns,ns);r.pop('stanza_json');r['dataset_id']=ds[ns];term_rows.append(r)
   for name,acc in [('parents',parents),('aliases',aliases),('synonyms',synonyms),('xrefs',xrefs)]:acc.append(dataset(read('reference/'+ns+'/'+name),ns))
  terms=pl.from_dicts(term_rows,infer_schema_length=None)
  # Keep raw definition qualifiers/citations and replacement suggestions; do not copy whole stanza.
  put('ontology_term',terms,['term_id'],'HPO/MONDO术语；定义引用、废弃替换和原定义限定保留')
  for name,parts,key,idx in [('ontology_parent',parents,['child_id','parent_id'],[['parent_id']]),('ontology_alias',aliases,['alt_id','term_id'],[['term_id']]),('ontology_synonym',synonyms,[],[['term_id']]),('ontology_xref',xrefs,[],[['term_id'],['external_id']])]:
   put(name,pl.concat(parts,how='diagonal_relaxed'),key,'原生本体关系，不用于新增疾病归类',idx)
  # MedGen names/definitions preserve raw CUI, suppression and display policy in compact concept records.
  concepts={}
  for r in read('medgen_names').iter_rows(named=True):
   cui=r.pop('resolved_cui');concepts.setdefault(cui,dict(resolved_cui=cui,names=[],definitions=[]))['names'].append(r)
  for r in read('medgen_definitions').iter_rows(named=True):
   cui=r.pop('resolved_cui');text=r.pop('DEF');r['definition_id']=define(text,'MedGen/'+r['source'],'MedGen');concepts.setdefault(cui,dict(resolved_cui=cui,names=[],definitions=[]))['definitions'].append(r)
  put('medgen_concept',pl.from_dicts(list(concepts.values()),infer_schema_length=None),['resolved_cui'],'相关MedGen CUI的来源名称及定义引用；保留原CUI/SUPPRESS')
  put('disease_definition',pl.from_dicts(definitions),['definition_id'],'按文本、提供者、版本保存一次的定义')
  put('disease_definition_link',pl.from_dicts(links),['definition_link_id'],'原疾病定义关联和展示状态', [['disease_id'],['definition_id']])
  labels=read('disease_source_label').with_row_index('label_occurrence_id',offset=1)
  unique=labels.select('disease_id','label','source').unique(maintain_order=True).with_row_index('label_id',offset=1)
  origins=labels.join(unique,on=['disease_id','label','source'],how='left',nulls_equal=True).select('label_occurrence_id','label_id','source_record')
  require(origins['label_id'].null_count()==0 and origins.height==labels.height,'label occurrences lost')
  put('disease_label',unique,['label_id'],'来源疾病名称文本；相同疾病/来源/文本只保存一次',[['disease_id']])
  put('disease_label_origin',origins,['label_occurrence_id'],'逐次来源名称出处，保留原有重复出现',[['label_id'],['source_record']])
  evidence=read('gene_disease_evidence');parts=[]
  native_dir=ROOT/CFG['inputs']['disease_native']['path'];native_cache={};extra=[]
  for r in evidence.iter_rows(named=True):
   aliases=CFG['native_field_aliases'].get(r['source_table'],CFG['native_field_aliases'].get(r['source']))
   detail=None
   if aliases is not None:
    key=r['source_table']
    if key not in native_cache:native_cache[key]=pl.read_parquet(native_dir/key).to_dicts()
    original=native_cache[key][int(r['native_record_ordinal'])-1]
    remainder={k:v for k,v in original.items() if k not in aliases or v!=r[aliases[k]]}
    restored={k:(remainder[k] if k in remainder else r[aliases[k]]) for k in original}
    require(restored==original,'native evidence details lost')
    detail=json.dumps(remainder,ensure_ascii=False,separators=(',',':'))
   extra.append(detail)
  evidence=evidence.with_columns(pl.Series('source_details_json',extra,dtype=pl.String))
  for s in evidence['source'].unique():parts.append(dataset(evidence.filter(pl.col('source')==s),s).drop('source'))
  put('gene_disease_evidence',pl.concat(parts),['evidence_id'],'逐来源基因—疾病关系；断言/导航/活动粒度独立',[['gene_id'],['disease_id']])
  ident=read('evidence_source_identifiers');cons=read('evidence_identifier_consistency');key=['evidence_id','source_field']
  require(ident.sort(key).equals(cons.select(ident.columns).sort(key),null_equal=True),'GenCC shared fields differ')
  put('evidence_identifier_check',cons,key,'GenCC补充编号与一致性核对合并保存')
  put('gene_dosage',dataset(read('gene_dosage'),'ClinGen'),['gene_id'],'ClinGen HI/TS独立基因级信息，保留来源symbol')
  gl=read('gene_protein_link');pg=pl.read_parquet(ROOT/CFG['inputs']['protein_gene']['path']).select(pl.col('hgnc_id').alias('gene_id'),'accession')
  h=gl.filter(pl.col('gene_id').str.starts_with('HGNC:'));reuse=pg.join(h.select('gene_id').unique(),on='gene_id',how='semi')
  require(h.sort(h.columns).equals(reuse.sort(h.columns)),'HGNC reuse differs')
  put('gene_protein_ncbi',gl.filter(pl.col('gene_id').str.starts_with('NCBIGene:')),['gene_id','accession'],'已确认NCBIGene—蛋白关系，HGNC部分复用web.protein_gene',[['accession']])
  ml=read('disease_mondo_link');test=ml.join(read('disease_mapping_status'),on='disease_id')
  require(test.filter(pl.col('mapping_status')!=pl.col('mondo_mapping_status')).height==0,'MONDO status differs')
  put('disease_mondo_link',ml.drop('mapping_status'),['disease_id','mondo_id'],'已有明确等价候选关系；状态从疾病条目读取',[['mondo_id']])
  mg=read('disease_medgen_link');require(mg['identity_merge_allowed'].unique().to_list()==[False],'MedGen merge rule changed')
  put('disease_medgen_link',mg.drop('identity_merge_allowed').with_row_index('link_id',offset=1),['link_id'],'已有MedGen辅助关联，不合并疾病身份',[['disease_id'],['resolved_cui']])
  put('shared_report_candidates',read('shared_report_candidates'),['evidence_a','evidence_b'],'共享报告候选；不去重、不投票')
  ph=read('disease_phenotype');require(ph.filter(pl.col('database_id')!=pl.col('disease_id')).height==0,'HPO disease identifier differs')
  phcheck=ph.join(terms.select(pl.col('term_id').alias('resolved_hpo_id'),pl.col('name').alias('term_name')),on='resolved_hpo_id',how='left')
  require(phcheck.filter(~pl.col('hpo_name').eq_missing(pl.col('term_name'))).height==0,'HPO term name differs')
  hlabels=labels.filter(pl.col('source')=='HPO').select(pl.col('source_record').alias('annotation_id'),'disease_id','label_occurrence_id','label')
  ph=ph.join(hlabels,on=['annotation_id','disease_id'],how='left')
  require(ph.height==98944 and ph.filter(~pl.col('disease_name').eq_missing(pl.col('label'))).height==0,'HPO source name recovery differs')
  ph=dataset(ph,'HPO').drop('database_id','disease_name','hpo_name','label')
  put('disease_phenotype',ph,['annotation_id'],'原HPOA逐条注释；NOT/频率/起病及来源条件保留',[['disease_id'],['resolved_hpo_id']])
  # Verify the principal definition losslessness, including the 19 absent from description links.
  recovered=entry.join(tables['disease_definition'].select(pl.col('definition_id').alias('primary_definition_id'),'definition','definition_source'),on='primary_definition_id',how='left')
  k=['disease_id','definition','definition_source'];require(recovered.select(k).sort('disease_id').equals(entries.select(k).sort('disease_id'),null_equal=True),'primary definitions lost')
  checks=['all_table_keys','GenCC_26006_shared_fields_equal','HGNC_links_exact_reuse','primary_definitions_including_19_preserved','HPO_identifier_and_names_recoverable','source_label_occurrences_preserved','MedGen_no_merge_constant','source_versions_preserved']
  manifest=dict(data_version=CFG['data_version'],schema=CFG['schema'],built_at=datetime.now(timezone.utc).isoformat(),tables=catalog,inputs=CFG['inputs'],rules=CFG['rules'],native_field_aliases=CFG['native_field_aliases'],checks=checks,status='built_validated')
  (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  destination=WEB/'data/disease_tables';previous=WEB/'data/.disease_previous'
  require(not previous.exists(),'Interrupted disease replacement requires inspection')
  if destination.exists():
   require(args.replace,'Use --replace for authorized disease service rebuild')
   os.replace(destination,previous)
  try:os.replace(out,destination)
  except BaseException:
   if previous.exists():os.replace(previous,destination)
   raise
  if previous.exists():shutil.rmtree(previous)
 finally:
  if out.exists():shutil.rmtree(out)
if __name__=='__main__':main()
