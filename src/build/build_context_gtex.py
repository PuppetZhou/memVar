"""Extract frozen GTEx target rows; no new expression statistics or normalization."""
from pathlib import Path
import gzip,json,time
import numpy as np
import pyarrow as pa,pyarrow.parquet as pq
import yaml
WEB=Path(__file__).resolve().parents[2];ROOT=WEB.parent
CFG=yaml.safe_load((WEB/'config/context.yaml').read_text());I={k:ROOT/v for k,v in CFG['inputs'].items()}
OUT=WEB/'data/.context_gtex';SNAP=json.loads(I['expression_snapshot'].read_text())

def register(tables,name,keys,indices=[]):
 f=OUT/(name+'.parquet');p=pq.ParquetFile(f)
 tables.append(dict(name=name,path=f.name,rows=p.metadata.num_rows,primary_key=keys,indices=indices,columns={x.name:str(x.type) for x in p.schema_arrow}))
 print(name,p.metadata.num_rows,flush=True)
def main():
 OUT.mkdir(exist_ok=False);manifest={'tables':[],'checks':[]};tables=manifest['tables'];datasets=[];samples=[]
 for name in ['gtex_gene_tpm','gtex_gene_median_tpm','gtex_transcript_tpm']:
  did='gtex_expression:'+name;spec=SNAP['sources'][name];source=Path(spec['file']);st=source.stat()
  if st.st_size!=spec['bytes'] or st.st_mtime_ns!=spec['mtime_ns']:raise ValueError('Frozen matrix changed '+name)
  idx=pq.read_table(I['expression_indexes']/(name+'.parquet'));rows=idx.to_pylist();byindex={r['source_index']:r for r in rows}
  datasets.append(dict(dataset_id=did,provider='GTEx',kind=name,details_json=json.dumps(dict(version='v11',source_file=source.name,unit='TPM',cohort='source-specific; no recomputed summary'))))
  dest=OUT/('expression_'+name+'.parquet')
  if name=='gtex_gene_tpm':
   pf=pq.ParquetFile(source);names=[x for x in pf.schema_arrow.names if x not in ['Name','Description']]
   ids=pf.read(columns=['Name']).take(idx['source_index'])['Name'].to_pylist()
   if ids!=idx['ensembl_gene_id'].to_pylist():raise ValueError('GTEx gene row mismatch')
   values=np.empty((len(rows),len(names)),dtype=np.float64)
   for a in range(0,len(names),256):
    cols=names[a:a+256];block=pf.read(columns=cols).take(idx['source_index'])
    for j,c in enumerate(block.columns):values[:,a+j]=c.to_numpy()
   if not np.isfinite(values).all() or (values<0).any():raise ValueError('Invalid GTEx TPM')
   vectors=pa.ListArray.from_arrays(pa.array(np.arange(len(rows)+1,dtype=np.int64)*len(names)),pa.array(values.ravel()))
   table=pa.table({'source_gene_id':idx['ensembl_gene_id'],'hgnc_id':idx['hgnc_id'],'values':vectors})
   pq.write_table(table,dest,compression='zstd',row_group_size=32)
   del table,values,vectors
  else:
   schema=pa.schema([('source_gene_id',pa.string()),('hgnc_id',pa.string())]+([('transcript_id',pa.string())] if name=='gtex_transcript_tpm' else [])+[('values',pa.list_(pa.string()))])
   with gzip.open(source,'rt') as f,pq.ParquetWriter(dest,schema,compression='zstd') as writer:
    if name=='gtex_gene_median_tpm':next(f);next(f)
    header=next(f).rstrip('\r\n').split('\t');names=header[2:];batch=[];seen=0
    for i,line in enumerate(f):
     if i not in byindex:continue
     fields=line.rstrip('\r\n').split('\t');r=byindex[i]
     gene=fields[0] if name=='gtex_gene_median_tpm' else fields[1]
     if gene!=r['ensembl_gene_id'] or len(fields)!=len(header):raise ValueError('GTEx index/width mismatch')
     out=dict(source_gene_id=gene,hgnc_id=r['hgnc_id'],values=fields[2:])
     if name=='gtex_transcript_tpm':
      if fields[0]!=r['transcript_id']:raise ValueError('Transcript index mismatch')
      out['transcript_id']=fields[0]
     batch.append(out);seen+=1
     if len(batch)==64:writer.write_table(pa.Table.from_pylist(batch,schema));batch=[]
    if batch:writer.write_table(pa.Table.from_pylist(batch,schema))
    if seen!=len(rows):raise ValueError('GTEx selected rows missing')
  samples += [dict(dataset_id=did,sample_index=j,sample_id=x) for j,x in enumerate(names)]
  register(tables,'expression_'+name,['transcript_id'] if name=='gtex_transcript_tpm' else ['source_gene_id'],[['hgnc_id']])
 pq.write_table(pa.Table.from_pylist(samples),OUT/'expression_gtex_sample.parquet',compression='zstd');register(tables,'expression_gtex_sample',['dataset_id','sample_index'])
 # Metadata describe gene TPM samples only, not the independently dated median/transcript cohorts.
 pq.write_table(pq.read_table(I['expression_indexes']/'gtex_gene_tpm_sample_metadata.parquet'),OUT/'expression_gtex_sample_metadata.parquet',compression='zstd');register(tables,'expression_gtex_sample_metadata',['SAMPID'])
 pq.write_table(pa.Table.from_pylist(datasets),OUT/'context_dataset.parquet',compression='zstd')
 for t in tables:
  if t['name']=='context_dataset':t['rows']=len(datasets)
 manifest['checks'].append(dict(gtex='selected row identity and complete vector width verified; source values preserved',cohort='official median and sample/transcript cohorts remain separate'))
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
