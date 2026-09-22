"""Targeted source reconstruction checks, without rerunning scientific mapping."""
from pathlib import Path
import json,duckdb,pyarrow.parquet as pq
WEB=Path(__file__).resolve().parents[2];ROOT=WEB.parent
from build_context import I,read,lit,q

def main():
 data=WEB/'data/context_tables';c=duckdb.connect();c.execute("SET threads=2; SET memory_limit='4GB'")
 for t in ['ppi_membership','ppi_interaction','ppi_participant']:c.execute(f'CREATE VIEW {t} AS SELECT * FROM {read(data/(t+".parquet"))}')
 result=[]
 # At least one record from each original file/context, including mutation.
 for d in pq.read_table(I['ppi']/'ppi_dataset.parquet').to_pylist():
  row=c.execute(f"SELECT record_id,source_record_id FROM ppi_membership WHERE dataset_id={lit(d['dataset_id'])} LIMIT 1").fetchone()
  if not row:continue
  record,source=row
  original=c.execute(f'SELECT * FROM {read(ROOT/d["cleaned_file"])} WHERE ppi_record_id={lit(source)}').fetch_arrow_table().to_pylist()[0]
  expected={k:v for k,v in original.items() if not k.startswith('ppi_') and 'Checksum' not in k}
  actual=json.loads(c.execute('SELECT details_json FROM ppi_interaction WHERE record_id=?',[record]).fetchone()[0])
  for p in c.execute('SELECT details_json FROM ppi_participant WHERE record_id=?',[record]).fetchall():actual.update(json.loads(p[0]))
  assert actual==expected,source
  result.append(dict(dataset_id=d['dataset_id'],source_record_id=source,fields=len(expected)))
 report=dict(status='passed',ppi_reconstruction=result,scope='one real record per original full/context/mutation file; all retained fields compared',note='source checksums and engineering fields intentionally omitted')
 (WEB/'data/context_projection_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('PASS',len(result),'PPI source-file reconstructions')
if __name__=='__main__':main()
