"""Targeted disease reconstruction checks against immutable source Parquet."""
import json
from pathlib import Path
import polars as pl
from import_tables import command,q,WEB

def validate(schema,manifest):
 s=q(schema);src=WEB.parent/manifest['inputs']['disease']['path'];checked=[]
 def query(sql):return json.loads(command("SELECT coalesce(json_agg(t),'[]'::json) FROM ("+sql+") t;",True))
 def equal(source,view,keys):
  expected=pl.read_parquet(src/(source+'.parquet'))
  columns=','.join(q(c) for c in expected.columns)
  data=query(f'SELECT {columns} FROM {s}.{q(view)}')
  actual=pl.from_dicts(data,schema=expected.schema,infer_schema_length=None)
  if not expected.sort(keys).equals(actual.sort(keys),null_equal=True):raise ValueError(source+' roundtrip differs')
  checked.append(dict(source=source,view=view,rows=expected.height))
 for a,b,k in [
  ('disease_entry','disease_entry_detail',['disease_id']),
  ('disease_description','disease_description',['disease_id','definition_source','source_record','definition','via','display_eligible']),
  ('disease_source_label','disease_source_label',['disease_id','source','source_record','label']),
  ('gene_disease_evidence','gene_disease_evidence_detail',['evidence_id']),
  ('gene_protein_link','gene_protein_link',['gene_id','accession']),
  ('gene_dosage','gene_dosage_detail',['gene_id']),
  ('disease_phenotype','disease_phenotype_detail',['annotation_id']),
  ('evidence_identifier_consistency','evidence_identifier_check',['evidence_id','source_field']),
  ('disease_mondo_link','disease_mondo_link_detail',['disease_id','mondo_id']),
  ('disease_medgen_link','disease_medgen_link_detail',['disease_id','cui','source_id_raw','source_namespace']),
  ('medgen_names','medgen_names',['resolved_cui','CUI','source','name','SUPPRESS']),
  ('medgen_definitions','medgen_definitions',['resolved_cui','CUI','source','DEF','SUPPRESS']),
  ('shared_report_candidates','shared_report_candidates',['evidence_a','evidence_b'])]:equal(a,b,k)
 # Native GenCC notes, criteria, CURIEs and ClinGen supplementary fields must remain available.
 native_root=WEB.parent/manifest['inputs']['disease_native']['path']
 all_evidence=query(f'SELECT * FROM {s}.gene_disease_evidence_detail')
 native_cache={};native_count=0
 for row in all_evidence:
  aliases=manifest['native_field_aliases'].get(row['source_table'],manifest['native_field_aliases'].get(row['source']))
  if aliases is None:continue
  table=row['source_table']
  if table not in native_cache:native_cache[table]=pl.read_parquet(native_root/table).to_dicts()
  original=native_cache[table][int(row['native_record_ordinal'])-1];details=row['source_details_json'] or {}
  restored={k:(details[k] if k in details else row[aliases[k]]) for k in original}
  if restored!=original:raise ValueError('Native source details lost '+row['evidence_id'])
  native_count+=1
 checked.append(dict(source='GenCC_and_ClinGen_native_nonredundant_fields',rows=native_count))
 # OMIM extension must be reconstructible even though duplicate title/number aren't stored.
 expected=pl.read_parquet(src/'omim_entry.parquet')
 rows=query(f'''SELECT disease_id,split_part(disease_id,':',2) AS mim_number,name AS title,alternative_titles,included_titles,
 omim_prefix AS prefix,omim_entry_type AS entry_type,(SELECT source_version FROM {s}.disease_dataset WHERE source='OMIM') AS source_version
 FROM {s}.disease_entry WHERE disease_id LIKE 'OMIM:%' AND disease_id NOT LIKE 'OMIM:PS%' ''')
 actual=pl.from_dicts(rows,schema=expected.schema,infer_schema_length=None)
 if not expected.sort('disease_id').equals(actual.sort('disease_id'),null_equal=True):raise ValueError('OMIM extension differs')
 checked.append(dict(source='omim_entry',rows=expected.height))
 missing=query(f'''SELECT count(*) AS n FROM {s}.gene_protein_link g LEFT JOIN web.protein p USING(accession) WHERE p.accession IS NULL''')[0]['n']
 if missing:raise ValueError('Protein identities missing')
 # Each nested MedGen definition references an existing dictionary entry.
 missing=query(f'''SELECT count(*) n FROM {s}.medgen_concept c CROSS JOIN LATERAL jsonb_array_elements(c.definitions) x
LEFT JOIN {s}.disease_definition d ON d.definition_id=x->>'definition_id' WHERE d.definition_id IS NULL''')[0]['n']
 if missing:raise ValueError('MedGen definition link broken')
 queries={
 'protein_disease':f"SELECT evidence_id,disease_id,classification FROM {s}.protein_disease_evidence WHERE accession='P13569' LIMIT 50",
 'disease_phenotype':f"SELECT annotation_id,resolved_hpo_id,qualifier,frequency FROM {s}.disease_phenotype WHERE disease_id='OMIM:219700' LIMIT 50",
 'definition':f"SELECT definition,definition_source FROM {s}.disease_description WHERE disease_id='OMIM:219700'",
 'gene_dosage':f"SELECT * FROM {s}.gene_dosage WHERE gene_id='HGNC:1884'"}
 plans={}
 for name,sql in queries.items():
  plan=json.loads(command('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+sql,True))[0];plans[name]={'execution_ms':plan['Execution Time'],'rows':plan['Plan']['Actual Rows']}
 return dict(status='passed',roundtrips=checked,checks=['existing_gene_protein_links_exact','all_source_assertions_and_classifications','all_HPO_NOT_and_aspect_annotations','all_definitions_and_primary_definition_exceptions','MedGen_names_suppression_and_links','GenCC_conflicts','shared_report_candidates'],queries=plans)
