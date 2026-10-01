"""Focused migration edge cases; creates temporary local files, never PostgreSQL tables."""
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from Web.src.database import migrate_duckdb as migration

class MigrationStorageRegression(unittest.TestCase):
    def test_existing_output_manifest_is_not_mutated(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest=root/'manifest.json';original='{"status":"validated_physical_tables","proof":"keep"}\n';manifest.write_text(original)
            with patch('sys.argv',['migration','build','--output',str(root)]):
                with self.assertRaises(FileExistsError):migration.main()
            self.assertEqual(manifest.read_text(),original)

    def test_float_precision_and_signed_zero(self):
        restored=pa.array([0.1,-0.0],type=pa.float32()).to_pylist()
        self.assertNotEqual(0.1,restored[0])
        self.assertTrue(migration.same_typed_value(0.1,restored[0],pa.float32()))
        self.assertFalse(migration.same_typed_value(0.1,restored[0],pa.float64()))
        self.assertTrue(migration.same_typed_value(-0.0,restored[1],pa.float32()))
        self.assertFalse(migration.same_typed_value(-0.0,0.0,pa.float32()))

    def test_null_empty_nan_arrays_and_json_roundtrip(self):
        table=pa.table({'values':pa.array([None,[],[0.1,None,float('nan'),-0.0]],type=pa.list_(pa.float32())), 'json':pa.array(['null','{}','{"n":9223372036854775807,"zero":0,"nested":[null,[]]}'])})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'values.parquet';pq.write_table(table,path);restored=pq.read_table(path)
            for column in range(table.num_columns):
                for a,b in zip(table.column(column).to_pylist(),restored.column(column).to_pylist()):self.assertTrue(migration.same_typed_value(a,b,table.schema[column].type))
            self.assertIsNone(restored['values'][0].as_py());self.assertEqual(restored['values'][1].as_py(),[])
            self.assertTrue(math.isnan(restored['values'][2].as_py()[2]));self.assertEqual(restored['json'][2].as_py(),table['json'][2].as_py())

    def test_catalog_rebuild_relocates_without_postgres(self):
        with tempfile.TemporaryDirectory() as folder:
            original=Path(folder)/'first';directory=original/'data/web/example';directory.mkdir(parents=True)
            pq.write_table(pa.table({'id':pa.array([1],type=pa.int64()),'payload':['{"v":0}']}),directory/'part-000000.parquet')
            objects=[{'schema':'web','name':'example','storage':'parquet','files':['data/web/example/part-000000.parquet'],'columns':[{'name':'id','pg_type':'int8'},{'name':'payload','pg_type':'jsonb'}]}, {'schema':'web','name':'empty','storage':'parquet','files':[],'columns':[{'name':'id','pg_type':'int8'}]}]
            (original/'data/web/empty').mkdir(parents=True)
            (original/'manifest.json').write_text(json.dumps({'objects':objects}))
            with patch.object(migration,'connect',side_effect=AssertionError('PostgreSQL must not be accessed')):
                migration.catalog(original);moved=Path(folder)/'moved';shutil.move(original,moved);migration.catalog(moved)
            with duckdb.connect(str(moved/'catalog.duckdb'),read_only=True) as db:
                self.assertEqual(db.execute('SELECT * FROM web.example').fetchall(),[(1,'{"v":0}')])
                self.assertEqual(db.execute('SELECT count(*) FROM web.empty').fetchone(),(0,))
                self.assertEqual(db.execute('SELECT id FROM web.empty').description[0][1],duckdb.sqltype('BIGINT'))

if __name__=='__main__':unittest.main()
