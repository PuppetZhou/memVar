"""Read-only regression checks against the configured legacy display bundle."""
import math
import struct
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from Web.src.api.alphagenome import asset_root, decode
from Web.src.api.main import app


class AlphaGenomeExpressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (asset_root() / 'alphagenome_catalog.duckdb').exists():
            raise unittest.SkipTest('Legacy display bundle is not installed')
        cls.client = TestClient(app)
        cls.base = '/api/proteins/P00533/expression/alphagenome'
        response = cls.client.get(cls.base)
        response.raise_for_status()
        cls.catalog = response.json()
        cls.gene = cls.catalog['genes'][0]['ensembl_gene_id']
        cls.tile = cls.catalog['genes'][0]['tiles'][0]['tile_id']

    def test_all_modalities_are_readable_and_bounded(self):
        modalities = {t['modality'] for t in self.catalog['tracks']}
        self.assertEqual(len(modalities), 9)
        for modality in sorted(modalities):
            with self.subTest(modality=modality):
                track = next(t for t in self.catalog['tracks'] if t['modality'] == modality)
                response = self.client.get(self.base + '/track', params={
                    'gene': self.gene, 'tile': self.tile, 'track_id': track['track_id'], 'bins': 1024})
                self.assertEqual(response.status_code, 200, response.text[:300])
                data = response.json()
                self.assertEqual(data['end'] - data['start'], 1048576)
                if data['kind'] == 'signal':
                    self.assertEqual(len(data['mean']), 1024)
                    self.assertEqual(len(data['maximum']), 1024)
                    self.assertEqual(data['bin_width'], 1024)
                    self.assertTrue(all(a is None or b is None or a <= b for a, b in zip(data['mean'],data['maximum'])))
                elif data['kind'] == 'contacts':
                    self.assertEqual(len(data['values']), data['size'] ** 2)
                    self.assertEqual(data['size'], 128)
                else:
                    self.assertLessEqual(len(data['items']), 200)
                    self.assertTrue(all(j['value'] > 0 for j in data['items']))

    def test_gene_scope_and_invalid_requests(self):
        defaults = {'gene': self.gene, 'tile': self.tile, 'track_id': 'rna_seq:000', 'bins': 256}
        for changed, status in [({'gene': 'ENSG00000000000'},404), ({'tile': 'tile_999'},404),
                                ({'track_id': "rna_seq:000' OR 1=1"},404), ({'bins': 512},422),
                                ({'tile': '../../secret'},422)]:
            response = self.client.get(self.base+'/track', params={**defaults,**changed})
            self.assertEqual(response.status_code,status,response.text[:200])

    def test_current_identity_mismatch_is_not_silently_linked(self):
        with patch('Web.src.api.alphagenome.get_protein',return_value={'accession':'P00533','hgnc_ids':['HGNC:other']}):
            response = self.client.get(self.base)
            self.assertEqual(response.status_code,200)
            self.assertFalse(response.json()['available'])
            self.assertEqual(response.json()['genes'],[])
            response = self.client.get(self.base+'/track',params={'gene':self.gene,'tile':self.tile,'track_id':'rna_seq:000'})
            self.assertEqual(response.status_code,404)

    def test_missing_values_remain_missing(self):
        self.assertEqual(decode(struct.pack('<eee',0,math.nan,math.inf),3),[0,None,None])

    def test_all_display_resolutions(self):
        for bins in (256,1024,4096):
            response=self.client.get(self.base+'/track',params={'gene':self.gene,'tile':self.tile,'track_id':'rna_seq:000','bins':bins})
            self.assertEqual(response.status_code,200)
            self.assertEqual(len(response.json()['mean']),bins)
            self.assertEqual(response.json()['bin_width'],1048576/bins)


if __name__ == '__main__':
    unittest.main()
