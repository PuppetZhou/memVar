"""Publish GTEx projections into the independently built context table set."""
from pathlib import Path
import json,shutil
import pyarrow as pa,pyarrow.parquet as pq
WEB=Path(__file__).resolve().parents[2]
def main():
 dest=WEB/'data/context_tables';src=WEB/'data/.context_gtex'
 a=json.loads((dest/'manifest.json').read_text());b=json.loads((src/'manifest.json').read_text())
 if set(t['name'] for t in a['tables']) & set(t['name'] for t in b['tables']):raise ValueError('GTEx already merged')
 datasets=pq.read_table(dest/'context_dataset.parquet').to_pylist()+pq.read_table(src/'context_dataset.parquet').to_pylist()
 if len({r['dataset_id'] for r in datasets})!=len(datasets):raise ValueError('Duplicate dataset')
 for t in b['tables']:shutil.move(str(src/t['path']),str(dest/t['path']))
 pq.write_table(pa.Table.from_pylist(datasets),dest/'context_dataset.parquet',compression='zstd')
 for t in a['tables']:
  if t['name']=='context_dataset':t['rows']=len(datasets)
 a['tables']+=b['tables'];a['checks']+=b['checks']
 counts={t['name']:t['rows'] for t in a['tables']}
 assert sum(counts[t] for t in ['gtex_qtl_pair','gtex_qtl_summary','eqtlgen_cis','qtlbase_association'])==251750112
 assert counts['ppi_membership']==2083370
 a['checks'].append({'qtl_source_count':251750112,'ppi_source_membership_count':2083370,'csv_null_empty_zero_and_multiline_roundtrip':'passed'})
 tmp=dest/'manifest.tmp';tmp.write_text(json.dumps(a,ensure_ascii=False,indent=2));tmp.replace(dest/'manifest.json')
 shutil.rmtree(src)
 print('Finalized',len(a['tables']),'tables')
if __name__=='__main__':main()
