"""The runtime selects one complete website package without scientific paths."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import unittest
from unittest.mock import patch
import duckdb

try:
    from src import runtime
except ModuleNotFoundError:
    from Web.src import runtime


class RuntimeTests(unittest.TestCase):
    def test_data_root_selects_coherent_package(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('manifest.json', 'catalog_statistics.json',
                         'source-record-files.json', 'structures/manifest.parquet',
                         'alphagenome/manifest.json', 'alphagenome/genes.parquet',
                         'alphagenome/protein_gene.parquet', 'alphagenome/tracks.parquet',
                         'alphagenome/windows.parquet'):
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.touch()
            (root / 'alphagenome/assets/tiles').mkdir(parents=True)
            protein = root / 'data/web/protein/part-000000.parquet'
            protein.parent.mkdir(parents=True)
            with duckdb.connect(str(root / 'catalog.duckdb')) as database:
                database.execute(f"COPY (SELECT 'P00533' AS accession) TO '{protein}' (FORMAT PARQUET)")
                database.execute('CREATE SCHEMA web')
                database.execute(f"CREATE VIEW web.protein AS SELECT * FROM read_parquet('{protein}')")
            (root / 'package.json').write_text('{"status":"complete"}')
            with patch.dict('os.environ', {'MEMVAR_DATA_ROOT': str(root),
                                         'MEMVAR_DUCKDB_PATH': '/missing/old.duckdb',
                                         'MEMVAR_STRUCTURE_ROOT': '/missing/structures',
                                         'MEMVAR_ALPHAGENOME_REFERENCE_ROOT': '/missing/tiles'}):
                self.assertEqual(runtime.catalog_path(), root / 'catalog.duckdb')
                self.assertEqual(runtime.structure_root(), root / 'structures')
                self.assertEqual(runtime.alphagenome_root(), root / 'alphagenome/assets')
                self.assertEqual(runtime.statistics_path(runtime.catalog_path()), root / 'catalog_statistics.json')
                runtime.check()
                with TemporaryDirectory() as outside_directory:
                    outside = Path(outside_directory) / 'protein.parquet'
                    shutil.copyfile(protein, outside)
                    with duckdb.connect(str(root / 'catalog.duckdb')) as database:
                        database.execute(f"CREATE OR REPLACE VIEW web.protein AS SELECT * FROM read_parquet('{outside}')")
                    with self.assertRaisesRegex(runtime.RuntimeConfigurationError, 'rebind it offline'):
                        runtime.check()
                    with duckdb.connect(str(root / 'catalog.duckdb')) as database:
                        database.execute(f"CREATE OR REPLACE VIEW web.protein AS SELECT * FROM read_parquet('{protein}')")
                (root / 'source-record-files.json').unlink()
                with self.assertRaisesRegex(runtime.RuntimeConfigurationError, 'source-record-files.json'):
                    runtime.check()
                (root / 'source-record-files.json').touch()
                (root / 'package.json').write_text('{"status":"building"}')
                with self.assertRaisesRegex(runtime.RuntimeConfigurationError, 'not complete'):
                    runtime.check()


if __name__ == '__main__':
    unittest.main()
