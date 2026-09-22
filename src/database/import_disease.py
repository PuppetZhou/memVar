"""Stage and publish web_disease without replacing web or web_context."""
import json,os,time
from pathlib import Path
import import_tables as base
from import_tables import command,q,WEB
from disease_views import statements
from validate_disease import validate
DATA=WEB/'data/disease_tables'
def lit(v):return "'"+str(v).replace("'","''")+"'"
def main():
 base.start();m=json.loads((DATA/'manifest.json').read_text());stage='web_disease_loading_'+str(os.getpid());s=q(stage);begin=time.monotonic();counts={}
 command(f'CREATE SCHEMA {s}');base.TABLES=DATA
 try:
  for t in m['tables']:
   counts[t['name']]=base.import_table(stage,t)
   for cols in t['indices']:
    if cols==['accession']:continue # shared loader already creates this index
    command(f'CREATE INDEX ON {s}.{q(t["name"])} ('+','.join(q(c) for c in cols)+');')
  relations=[('disease_entry','primary_definition_id','disease_definition','definition_id'),('disease_definition_link','definition_id','disease_definition','definition_id'),('disease_label_origin','label_id','disease_label','label_id'),('disease_phenotype','label_occurrence_id','disease_label_origin','label_occurrence_id'),('disease_phenotype','resolved_hpo_id','ontology_term','term_id'),('evidence_identifier_check','evidence_id','gene_disease_evidence','evidence_id'),('shared_report_candidates','evidence_a','gene_disease_evidence','evidence_id'),('shared_report_candidates','evidence_b','gene_disease_evidence','evidence_id'),('ontology_term','definition_id','disease_definition','definition_id'),('ontology_parent','child_id','ontology_term','term_id'),('ontology_alias','term_id','ontology_term','term_id'),('ontology_synonym','term_id','ontology_term','term_id'),('ontology_xref','term_id','ontology_term','term_id'),('disease_mondo_link','mondo_id','ontology_term','term_id')]
  for t in m['tables']:
   if 'disease_id' in t['columns'] and t['name']!='disease_entry':relations.append((t['name'],'disease_id','disease_entry','disease_id'))
   if 'dataset_id' in t['columns'] and t['name']!='disease_dataset':relations.append((t['name'],'dataset_id','disease_dataset','dataset_id'))
  for t,c,p,pc in relations:command(f'ALTER TABLE {s}.{q(t)} ADD FOREIGN KEY ({q(c)}) REFERENCES {s}.{q(p)}({q(pc)});')
  views=[]
  for name,sql in statements(stage):command(sql);views.append(name)
  validation=validate(stage,m)
  command(f'CREATE TABLE {s}._build_manifest(data_version text PRIMARY KEY,manifest jsonb NOT NULL); INSERT INTO {s}._build_manifest VALUES ({lit(m["data_version"])},{lit(json.dumps(m,ensure_ascii=False))}::jsonb);')
  current=m['schema'];exists=command(f"SELECT count(*) FROM pg_namespace WHERE nspname={lit(current)}",True).strip()=='1'
  sql='BEGIN; SELECT pg_advisory_xact_lock(20260921,4);'
  if exists:sql+=f'ALTER SCHEMA {q(current)} RENAME TO {q(stage+"_old")};'
  sql+=f'ALTER SCHEMA {s} RENAME TO {q(current)};'
  if exists:sql+=f'DROP SCHEMA {q(stage+"_old")} CASCADE;'
  command(sql+'COMMIT;')
 except BaseException:
  command(f'DROP SCHEMA IF EXISTS {s} CASCADE');raise
 report=dict(status='imported_validated',data_version=m['data_version'],input_built_at=m['built_at'],database=base.C['database'],schema=current,table_count=len(counts),tables=counts,views=views,validation=validation,elapsed_seconds=round(time.monotonic()-begin,2))
 (WEB/'data/postgresql_disease_import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['tables','validation']},indent=2))
if __name__=='__main__':main()
