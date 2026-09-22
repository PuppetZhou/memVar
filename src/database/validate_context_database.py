"""Bounded real-data round trips and cross-schema navigation after context publish."""
from pathlib import Path
import sys,json
import pyarrow.parquet as pq, pyarrow as pa
from import_tables import command,q
WEB=Path(__file__).resolve().parents[2];DATA=WEB/'data/context_tables'
def lit(x):return "'"+str(x).replace("'","''")+"'"
def main():
 checks=[]
 for table,keys in [('gtex_qtl_pair',['hgnc_id','dataset_id','source_row']),('eqtlgen_cis',['hgnc_id','SNP']),('qtlbase_association',['hgnc_id','dataset_id','SNP_chr','SNP_pos_hg19','SNP_pos_hg38']),('expression_rna_cancer_sample',['source_gene_id','context_id']),('expression_hpa_transcript',['source_gene_id','transcript_id','sample_id'])]:
  row=next(pq.ParquetFile(DATA/(table+'.parquet')).iter_batches(batch_size=1)).to_pylist()[0]
  pred=' AND '.join(q(k)+' IS NOT DISTINCT FROM '+('NULL' if row[k] is None else lit(row[k])) for k in keys)
  schema=pq.ParquetFile(DATA/(table+'.parquet')).schema_arrow
  projection=','.join(q(f.name)+'::double precision AS '+q(f.name) if pa.types.is_float32(f.type) else q(f.name) for f in schema)
  raw=command(f'SELECT row_to_json(t) FROM (SELECT {projection} FROM web_context.{q(table)} WHERE {pred} LIMIT 100) t',True)
  candidates=[json.loads(r) for r in raw.splitlines() if r]
  assert row in candidates,table
  checks.append(dict(table=table,result='source row values roundtrip'))
 for name in ['gtex_gene_tpm','gtex_gene_median_tpm','gtex_transcript_tpm']:
  table='expression_'+name;row=next(pq.ParquetFile(DATA/(table+'.parquet')).iter_batches(batch_size=1)).to_pylist()[0];key='transcript_id' if 'transcript_id' in row else 'source_gene_id'
  values=json.loads(command(f'SELECT {q("values")} FROM web_context.{q(table)} WHERE {q(key)}={lit(row[key])}',True))
  assert values==row['values'],table
  count=int(command(f"SELECT count(*) FROM web_context.expression_gtex_sample WHERE dataset_id={lit('gtex_expression:'+name)}",True))
  assert count==len(values),table
  checks.append(dict(table=table,result='full sample vector and sample index length roundtrip',values=count))
 gene=command("SELECT hgnc_id FROM web.protein_gene WHERE accession='P00533' LIMIT 1",True).strip()
 qtl=json.loads(command(f"SELECT coalesce(json_agg(t),'[]') FROM (SELECT table_name,record_count FROM web_context.qtl_context_count WHERE hgnc_id={lit(gene)} LIMIT 10) t",True))
 ppi=int(command("SELECT count(*) FROM (SELECT record_id FROM web_context.ppi_protein_link WHERE target_accession='P00533' LIMIT 10) t",True))
 expr=int(command(f"SELECT count(*) FROM (SELECT * FROM web_context.expression_rna_tissue_hpa_detail WHERE hgnc_id={lit(gene)} LIMIT 10) t",True))
 assert qtl and ppi and expr
 report=dict(status='passed',checks=checks,protein_example=dict(accession='P00533',hgnc_id=gene,qtl=qtl,ppi_sample_rows=ppi,expression_sample_rows=expr),scope='bounded source-value checks and current web protein/gene navigation; not API or concurrent load testing')
 (WEB/'data/postgresql_context_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('PASS',len(checks),'source-value checks; P00533 QTL/PPI/Expression navigation')
if __name__=='__main__':main()
