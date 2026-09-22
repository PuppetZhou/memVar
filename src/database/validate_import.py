"""Validate imported source counts, nested details and full-scale indexed queries."""
import json,subprocess,sys
from pathlib import Path
import polars as pl
from import_tables import WEB,C,command,q
sys.path.insert(0,str(WEB/'src/build'))
from external_references import reference_fields,uniprot_xref_fields

def query(sql):
 return json.loads(command(f'SELECT coalesce(json_agg(t),\'[]\'::json) FROM ({sql}) t;',True))

def main():
 report=json.loads((WEB/'data/postgresql_import.json').read_text())
 manifest=json.loads((WEB/'data/tables/manifest.json').read_text())
 assert report['input_built_at']==manifest['built_at']
 assert query('SELECT built_at FROM web._build_manifest')[0]['built_at']==manifest['built_at']
 assert query("SELECT manifest->>'data_version' AS data_version FROM web._build_manifest")[0]['data_version']==manifest['data_version']
 assert report['data_version']==manifest['data_version']
 output={'status':'passed','data_version':manifest['data_version'],'input_built_at':manifest['built_at'],'mapping_counts':{},'jsonb_roundtrips':[],'query_plans':{}}
 # Revision-specific checks: removed storage remains reconstructible through ordinary views.
 columns={r['table_name']:set() for r in query("SELECT DISTINCT table_name FROM information_schema.columns WHERE table_schema='web'")}
 for row in query("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema='web'"):
  columns[row['table_name']].add(row['column_name'])
 for table,removed in manifest['rules']['deduplicated_columns'].items():
  assert not columns[table].intersection(removed),(table,removed)
 xref=query("SELECT count(*) AS total,count(DISTINCT reference_id) AS distinct_ids FROM web.protein_external_reference_all")[0]
 expected=report['tables']['protein_external_reference']+report['tables']['protein']+report['tables']['protein_gene']
 assert xref['total']==xref['distinct_ids']==expected
 assert query("SELECT count(*) AS n FROM web.protein_external_reference WHERE database_name IN ('UniProt','HGNC')")[0]['n']==0
 source=pl.read_parquet(WEB.parent/manifest['inputs']['identity']['path']/'protein_xref.parquet')
 for external_id in ['NP_005219.2','ENST00000275493.7','YP_003024031.1']:
  original=source.filter(pl.col('external_id')==external_id).to_dicts()[0]
  expected_fields=uniprot_xref_fields(original)
  actual=query(f"SELECT * FROM web.protein_external_reference_all WHERE accession='{original['accession']}' AND external_id='{external_id}'")[0]
  assert all(actual[k]==v for k,v in expected_fields.items()),external_id
 for database,external_id in [('HGNC','HGNC:3236'),('UniProt','P00533')]:
  actual=query(f"SELECT * FROM web.protein_external_reference_all WHERE accession='P00533' AND database_name='{database}'")[0]
  assert all(actual[k]==v for k,v in reference_fields(database,external_id).items())
 sites=pl.read_parquet(WEB/'data/tables/membrane/membrane_biodolphin_site.parquet',columns=['interaction_id','mapping_status'])
 expected_summary=sites.group_by('interaction_id').agg(pl.len().cast(pl.Int64).alias('source_site_rows'),(pl.col('mapping_status')=='mapped').sum().cast(pl.Int64).alias('mapped_site_rows'))
 actual_summary=pl.from_dicts(query('SELECT interaction_id,source_site_rows,mapped_site_rows,sequence_mapping_status FROM web.membrane_biodolphin_interaction_summary'),infer_schema_length=None)
 interactions=pl.read_parquet(WEB/'data/tables/membrane/membrane_biodolphin_interaction.parquet',columns=['interaction_id'])
 expected_summary=interactions.join(expected_summary,on='interaction_id',how='left').with_columns(
  pl.when(pl.col('source_site_rows').is_null()).then(pl.lit('source_sites_absent'))
  .when(pl.col('source_site_rows')==pl.col('mapped_site_rows')).then(pl.lit('all_source_sites_mapped'))
  .when(pl.col('mapped_site_rows')>0).then(pl.lit('partially_mapped')).otherwise(pl.lit('no_verified_mapping')).alias('sequence_mapping_status'))
 assert expected_summary.sort('interaction_id').equals(actual_summary.select(expected_summary.columns).sort('interaction_id'),null_equal=True)
 label=pl.read_parquet(WEB/'data/tables/membrane/protein_membrane_label.parquet')
 classification=pl.read_parquet(WEB/'data/tables/membrane/protein_membrane_classification.parquet')
 fids=set(pl.read_parquet(WEB/'data/tables'/next(t['path'] for t in manifest['tables'] if t['name'] in ['uniprot_sequence_feature','membrane_uniprot_feature']),columns=['feature_id'])['feature_id'])
 cids=set(pl.read_parquet(WEB/'data/tables/localization/protein_uniprot_location.parquet',columns=['annotation_id'])['annotation_id'])
 supports=0
 for row in label.iter_rows(named=True):
  assert row['supporting_records'] or row['label']=='membrane_related'
  for evidence in row['supporting_records']:
   assert evidence['source_record_id'] in (fids if evidence['source_table']=='membrane_uniprot_feature' else cids)
   supports+=1
 assert query("SELECT count(*) AS n FROM web.protein_membrane_label l JOIN web.protein p USING(accession) WHERE l.sequence_id<>p.default_sequence_id")[0]['n']==0
 assert classification.height==classification['accession'].n_unique()==7715
 assert query("SELECT count(*) AS n FROM web.protein_membrane_classification")[0]['n']==7715
 class_counts={r['primary_class']:r['n'] for r in query("SELECT primary_class,count(*) AS n FROM web.protein_membrane_classification GROUP BY primary_class")}
 assert class_counts=={'transmembrane':5213,'lipid_anchored':441,'peripheral_membrane':1015,'membrane_related':1046}
 assert query("SELECT count(*) AS n FROM web.protein_membrane_classification WHERE parent_class='integral_membrane'")[0]['n']==5654
 assert query("SELECT count(*) AS n FROM web.protein_membrane_classification WHERE transmembrane_subclass='single_pass'")[0]['n']==2380
 assert query("SELECT count(*) AS n FROM web.protein_membrane_classification WHERE transmembrane_subclass='multi_pass'")[0]['n']==2833
 assert query("SELECT count(*) AS n FROM web.go_slim_mapping m JOIN web.go_term t ON t.go_id=m.term_id JOIN web.go_term c ON c.go_id=m.category_id WHERE t.namespace<>c.namespace")[0]['n']==0
 assert query("SELECT count(*) AS n FROM web.protein_go_slim WHERE mapping_status='gpi_parent_context_only'")[0]['n']==0
 # The original row counts stay identical except normalized xrefs and the expanded GO dictionary.
 baseline=json.loads((WEB/'docs/record'/manifest['rules']['metadata'].get('baseline_audit',manifest['data_version']+'_audit.json')).read_text())
 for table,count in baseline['previous_table_rows'].items():
  if table not in ['protein_external_reference','go_term']:
   actual=report['tables'].get(table)
   if actual is None:actual=query(f'SELECT count(*) n FROM web.{q(table)}')[0]['n']
   assert actual==count,table
 output['optimization']={'removed_columns':manifest['rules']['deduplicated_columns'],
   'external_reference_storage_rows':report['tables']['protein_external_reference'],
   'external_reference_view_rows':xref['total'],'biodolphin_site_rows':sites.height,
   'biodolphin_summary_roundtrip_rows':actual_summary.height,'label_supports_checked':supports,
   'go_slim_mapping_rows':report['tables']['go_slim_mapping'],'protein_membrane_label_rows':label.height,
   'protein_membrane_classification_rows':classification.height,'primary_membrane_class_counts':class_counts,
   'ordinary_views':report['views']}
 for table in ['membrane_opm_observation','membrane_mplid_residue','membrane_biodolphin_site']:
  counts=query(f"SELECT mapping_status,count(*) AS rows FROM web.{q(table)} GROUP BY mapping_status")
  parquet=pl.scan_parquet(WEB/'data/tables/membrane'/(table+'.parquet')).group_by('mapping_status').len().collect()
  assert {x['mapping_status']:x['rows'] for x in counts}==dict(parquet.iter_rows())
  output['mapping_counts'][table]=counts
 for table,field,key in [('rhea_reaction','participants','rhea_id'),('gtopdb_ligand','peptide_records','ligand_id'),('protein_go_annotation','source_records','annotation_id')]:
  path=next(t['path'] for t in manifest['tables'] if t['name']==table)
  row=pl.scan_parquet(WEB/'data/tables'/path).filter(pl.col(field).is_not_null()).select(key,field).limit(1).collect().to_dicts()[0]
  value=str(row[key]).replace("'","''")
  actual=query(f"SELECT {q(field)} FROM web.{q(table)} WHERE {q(key)}='{value}' LIMIT 1")[0][field]
  assert actual==row[field],f'{table} JSONB differs'
  output['jsonb_roundtrips'].append(table+'.'+field)
 funcs=query('SELECT count(*) AS invalid FROM web.protein_function_overview o JOIN web.protein_function_annotation a ON a.annotation_id=o.default_annotation_id WHERE o.accession<>a.accession OR a.comment_type<>\'FUNCTION\'')
 assert funcs[0]['invalid']==0
 deep=query("SELECT count(*) AS n FROM web.deeptmhmm2_prediction WHERE protein_type='Globular' AND tm_helix_count=0 AND membrane_probabilities_json IS NULL")
 assert deep[0]['n']>0
 output['prediction_zero_and_not_applicable_preserved']=deep[0]['n']
 sqls={
 'external_reference_view':"SELECT database_name,external_id,url FROM web.protein_external_reference_all WHERE accession='P00533' ORDER BY reference_id LIMIT 50",
 'biodolphin_summary_view':"SELECT interaction_id,source_site_rows,mapped_site_rows FROM web.membrane_biodolphin_interaction_summary WHERE interaction_id='BioDolphin:9'",
 'canonical_membrane_labels':"SELECT label FROM web.protein_membrane_label WHERE accession='P00533'",
 'go_slim_categories':"SELECT category_id FROM web.protein_go_slim WHERE accession='P00533' AND subject_id='UniProtKB:P00533' LIMIT 50",
 'protein_GO_page':"SELECT annotation_id,go_id,evidence_code FROM web.protein_go_annotation WHERE accession='P00533' ORDER BY annotation_id LIMIT 50",
 'topology_site':"SELECT feature_id,start,\"end\" FROM web.membrane_topology_location WHERE sequence_id='P00533' AND start<=650 AND \"end\">=650 LIMIT 50",
 'prediction':"SELECT sequence_id,protein_type,tm_helix_count FROM web.deeptmhmm2_prediction WHERE sequence_id='P00533'",
 'biodolphin_site':"SELECT interaction_id,coordinate_system,target_position FROM web.membrane_biodolphin_site WHERE sequence_id='P06401' AND mapping_status='mapped' AND target_position=715 LIMIT 50",
 'opm_page':"SELECT source_observation_id,target_position FROM web.membrane_opm_observation WHERE sequence_id='P05023' AND mapping_status='mapped' ORDER BY target_position,source_observation_id LIMIT 50",
 'mplid_site':"SELECT source_member,source_row,target_position,is_contact FROM web.membrane_mplid_residue WHERE sequence_id='P05023' AND mapping_status='mapped' AND target_position=100 LIMIT 50"}
 for name,sql in sqls.items():
  plan=json.loads(command('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+sql+';',True))[0]
  output['query_plans'][name]={'execution_ms':plan['Execution Time'],'planning_ms':plan['Planning Time'],'rows':plan['Plan']['Actual Rows'],'plan':plan['Plan']}
  if name!='mplid_site':assert plan['Plan']['Actual Rows']>0,name+' empty'
 page1=query(sqls['opm_page']);last=page1[-1]
 page2=query(f"SELECT source_observation_id,target_position FROM web.membrane_opm_observation WHERE sequence_id='P05023' AND mapping_status='mapped' AND (target_position,source_observation_id)>({last['target_position']},{last['source_observation_id']}) ORDER BY target_position,source_observation_id LIMIT 50")
 assert len(page1)==len(page2)==50
 assert not ({r['source_observation_id'] for r in page1}&{r['source_observation_id'] for r in page2})
 output['pagination']={'table':'membrane_opm_observation','sequence_id':'P05023','page_sizes':[len(page1),len(page2)],'duplicate_rows':0,'cursor':['target_position','source_observation_id']}
 output['runtime_memory']=subprocess.run(['docker','stats','--no-stream','--format','{{.MemUsage}}',C['container']],capture_output=True,text=True,check=True).stdout.strip()
 output['limits']='Single local client, current complete tables. No API/browser or concurrent-load test.'
 (WEB/'data/postgresql_validation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v if k!='query_plans' else {n:{x:y for x,y in z.items() if x!='plan'} for n,z in v.items()} for k,v in output.items()},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
