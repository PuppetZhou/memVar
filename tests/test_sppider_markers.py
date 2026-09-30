"""Targeted live checks: marker membership, independent partner scores and provenance."""
import unittest
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.interface_predictions import context
from Web.src.api.db import query


class SppiderMarkersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.root = '/api/proteins/P00533/interface'

    def test_marker_count_matches_all_paginated_partners_and_original_scores(self):
        markers = self.client.get(self.root + '/sppider-markers').json()['items']
        marker = next(row for row in markers if row['position'] == 287)
        partners = []
        offset = 0
        while True:
            response = self.client.get(self.root + '/sppider-markers/287', params={'offset': offset, 'limit': 50})
            self.assertEqual(response.status_code, 200)
            page = response.json()
            partners.extend(page['items'])
            if not page['has_more']:
                break
            offset += 50
        self.assertEqual(len(partners), marker['partner_count'])
        self.assertEqual(len({row['partner_sequence_key'] for row in partners}), len(partners))
        for row in partners:
            self.assertGreaterEqual(row['score'], .5)
        row = next(row for row in partners if row['partner_sequence_key'] == 'seq_000002')
        original = self.client.get(self.root + '/sppider', params={'partner': row['partner_sequence_key']}).json()
        self.assertEqual(row['score'], original['receptor_probability'][286])
        self.assertIn('BioGRID', [source['provider'] for source in row['sources']])
        source_key = context('P00533')[-1]['SPPIDER-seq']['source_key']
        evidence = query('''SELECT DISTINCT ppi_dataset_id FROM web_interface.direction_evidence
            WHERE query_sequence_key=:key AND partner_sequence_key=:partner''',
            {'key': source_key, 'partner': row['partner_sequence_key']})
        self.assertEqual({source['dataset_id'] for source in row['sources']}, {source['ppi_dataset_id'] for source in evidence})

    def test_role_and_position_validation(self):
        self.assertEqual(self.client.get(self.root + '/sppider-markers', params={'role': 'invalid'}).status_code, 422)
        self.assertEqual(self.client.get(self.root + '/sppider-markers/0').status_code, 422)
        self.assertEqual(self.client.get(self.root + '/sppider-markers/1211').status_code, 422)
        response = self.client.get(self.root + '/sppider-markers/287', params={'role': 'peptide', 'limit': 50})
        self.assertEqual(response.status_code, 200)
        for row in response.json()['items']:
            raw = self.client.get(self.root + '/sppider', params={'partner': row['partner_sequence_key']}).json()
            self.assertEqual(row['score'], raw['peptide_probability'][286])
            self.assertGreaterEqual(row['score'], .5)


if __name__ == '__main__':
    unittest.main()
