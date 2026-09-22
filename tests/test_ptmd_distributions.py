"""PTMD distributions count full source records and preserve CellType missingness."""
import unittest
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.db import query
from Web.src.api.disease_ptmd import PTMD_WHERE


class PtmdDistributionTests(unittest.TestCase):
    def test_full_counts_and_exact_cell_filters(self):
        client = TestClient(app)
        base = '/api/proteins/P00533/diseases/ptmd'
        response = client.get(base + '/summary')
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        cells = [g for g in data['groups'] if g['dimension'] == 'cell_type']
        self.assertEqual(sum(g['count'] for g in cells), data['totals']['records'])
        raw = query(f"SELECT r.details_json->>'CellType' cell_type FROM web.ptm_record r WHERE {PTMD_WHERE}", {'accession': 'P00533'})
        self.assertEqual(len(raw), data['totals']['records'])
        missing = {None, '', '-', '.', 'NA', 'NaN'}
        for group in cells:
            expected = sum(row['cell_type'] in missing if 'cell_type_missing' in group['filter'] else row['cell_type'] == group['key'] for row in raw)
            self.assertEqual(group['count'], expected)
            response = client.get(base, params={**group['filter'], 'limit': 100})
            self.assertEqual(response.status_code, 200, response.text)
            records = response.json()['items']
            self.assertEqual(len(records), min(100, expected))
            self.assertTrue(all(record['cell_type'] is None if 'cell_type_missing' in group['filter'] else record['cell_type'] == group['key'] for record in records))
        ptm_type = next(g for g in data['groups'] if g['dimension'] == 'type')
        sample = client.get(base, params={**ptm_type['filter'], **cells[0]['filter'], 'limit': 2}).json()
        self.assertTrue(all(row['source_type'] == ptm_type['key'] for row in sample['items']))
