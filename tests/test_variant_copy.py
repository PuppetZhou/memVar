"""Regression for lossless CSV/JSON and Float32 transfer through libpq COPY."""
import json,os,sys,tempfile,unittest
from pathlib import Path
import pyarrow as pa,pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/database'))
import import_variant as importer

@unittest.skipUnless(os.environ.get('MEMVAR_TEST_POSTGRES')=='1','requires local PostgreSQL')
class VariantCopyTests(unittest.TestCase):
 def test_source_text_json_and_exact_float32(self):
  schema='variant_copy_test_'+str(os.getpid());original=importer.DATA
  importer.command('CREATE SCHEMA '+schema)
  try:
   with tempfile.TemporaryDirectory() as directory:
    importer.DATA=Path(directory)
    table=pa.table({'id':[1,2,3], 'text':['',None,'\\N\n\\.\n"quoted"'],
      'score':pa.array([0.0851297378540039,-23.408439,None],type=pa.float32()),
      'details_json':pa.array(['{"text":"中文\\nquote\\\"","zero":0}',None,'{}'],type=pa.json_())})
    pq.write_table(table,importer.DATA/'test.parquet')
    importer.load(schema,dict(name='test',path='test.parquet',primary_key=['id'],indices=[],rows=3))
    actual=json.loads(importer.command('SELECT json_agg(t ORDER BY id) FROM '+schema+'.test t',True))
    expected=table.to_pylist()
    for r in expected:
     if r['details_json'] is not None:r['details_json']=json.loads(r['details_json'])
    self.assertEqual(actual,expected)
  finally:
   importer.DATA=original;importer.command('DROP SCHEMA '+schema+' CASCADE')
if __name__=='__main__':unittest.main()
