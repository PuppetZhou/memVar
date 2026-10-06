"""Small, real-format checks for portable catalog paths and frozen values."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

try:
    from src.database.portable import build_catalog, rebind
except ModuleNotFoundError:
    from Web.src.database.portable import build_catalog, rebind


class PortableCatalogTest(unittest.TestCase):
    def test_views_rebind_after_move_without_changing_values(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'first'
            table = root / 'data/web/protein'
            table.mkdir(parents=True)
            pq.write_table(pa.table({'id': pa.array([1, 2], type=pa.int64()),
                                     'score': pa.array([0.0, None], type=pa.float32()),
                                     'details': ['{"zero":0}', None]}), table / 'part-000000.parquet')
            alpha_dir = root / 'alphagenome'
            alpha_dir.mkdir()
            for name in ('genes', 'protein_gene', 'tracks', 'windows'):
                pq.write_table(pa.table({'id': [1]}), alpha_dir / (name + '.parquet'))
            (alpha_dir / 'manifest.json').write_text(json.dumps({'schema_version': 2,
                                                                 'source_root': '/historical/source'}))
            (root / 'manifest.json').write_text(json.dumps({'objects': [
                {'schema': 'web', 'name': 'protein', 'storage': 'parquet',
                 'columns': [{'name': 'id', 'pg_type': 'int8'},
                             {'name': 'score', 'pg_type': 'float4'},
                             {'name': 'details', 'pg_type': 'jsonb'}]},
                {'schema': 'web', 'name': 'protein_count', 'storage': 'logical_view',
                 'definition': 'SELECT count(*)::bigint AS n FROM web.protein'},
                *[{'schema': 'web_alphagenome', 'name': name, 'storage': 'parquet'}
                  for name in ('genes', 'protein_gene', 'tracks', 'windows')],
                {'schema': 'web_alphagenome', 'name': 'manifest', 'storage': 'parquet'},
            ]}))
            build_catalog(root)
            moved = Path(folder) / 'moved'
            shutil.move(root, moved)
            # Rebinding creates a separate catalog; the copied catalog remains intact.
            original_catalog = (moved / 'catalog.duckdb').read_bytes()
            rebound = rebind(moved)
            self.assertEqual((moved / 'catalog.duckdb').read_bytes(), original_catalog)
            with self.assertRaises(FileExistsError):
                rebind(moved)
            with duckdb.connect(str(rebound), read_only=True) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM web.protein').fetchone(), (2,))
                self.assertEqual(db.execute('SELECT * FROM web.protein_count').fetchone(), (2,))
                self.assertEqual(db.execute('SELECT score, details FROM web.protein ORDER BY id').fetchall(),
                                 [(0.0, '{"zero":0}'), (None, None)])
                source = json.loads(db.execute('SELECT data FROM web_alphagenome.manifest').fetchone()[0])
                self.assertEqual(source['source_root'], '/historical/source')
                sql = db.execute("SELECT sql FROM duckdb_views() WHERE schema_name='web' AND view_name='protein'").fetchone()[0]
                self.assertIn(str(moved), sql)
                self.assertNotIn(str(root), sql)


if __name__ == '__main__':
    unittest.main()
