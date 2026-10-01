"""The small catalog rebind must preserve unrelated views and fail atomically."""
import json
from pathlib import Path
import tempfile
import unittest

import duckdb

from Web.src.database.alphagenome_catalog import bind_catalog, write_configuration


class CatalogBindingTests(unittest.TestCase):
    def test_pilot_count_exception_is_explicit_and_source_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/'catalog.duckdb'
            curated=root/'curated'
            curated.mkdir()
            original=dict(source_run_id='model',checkpoint_revision='checkpoint',backend='local',model_version='all')
            manifest=dict(original,schema_version=2,crop_run_id='crop',crop_status='complete',
                          source_root=str(root/'assets'),retention_flank_bp=10000,
                          counts={'genes':1,'protein_gene':1,'tracks':1,'windows':1})
            (curated/'manifest.json').write_text(json.dumps(manifest))
            with duckdb.connect(str(source)) as db:
                db.execute('CREATE SCHEMA web_alphagenome')
                db.execute('CREATE VIEW unrelated AS SELECT 42 AS value')
                db.execute("CREATE VIEW web_alphagenome.manifest AS SELECT true id, CAST('"+json.dumps(original)+"' AS JSON) AS data")
                for name in ['genes','protein_gene','tracks']:
                    db.execute(f'CREATE VIEW web_alphagenome.{name} AS SELECT 1 AS value')
                    db.execute(f"COPY (SELECT 1 AS value) TO '{curated/name}.parquet' (FORMAT PARQUET)")
                db.execute('CREATE VIEW web_alphagenome.windows AS SELECT * FROM range(2)')
                db.execute(f"COPY (SELECT 0 window_start,100 window_end,10 retention_start,90 retention_end,'model' source_run_id,'crop' crop_run_id) TO '{curated/'windows.parquet'}' (FORMAT PARQUET)")
            rejected=root/'rejected.duckdb'
            with self.assertRaisesRegex(ValueError,'scope changed'):
                bind_catalog(source,curated,rejected)
            self.assertFalse(rejected.exists())
            self.assertFalse(rejected.with_name(rejected.name+'.building').exists())
            destination=root/'candidate.duckdb'
            result=bind_catalog(source,curated,destination,pilot=True)
            self.assertEqual(result['counts']['windows'],1)
            with duckdb.connect(str(destination),read_only=True) as db:
                self.assertEqual(db.execute('SELECT value FROM unrelated').fetchone(),(42,))
            with duckdb.connect(str(source),read_only=True) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM web_alphagenome.windows').fetchone(),(2,))
            config=root/'candidate.yaml'
            self.assertEqual(write_configuration(curated,config)['crop_run_id'],'crop')
            with self.assertRaises(FileExistsError):
                write_configuration(curated,config)
