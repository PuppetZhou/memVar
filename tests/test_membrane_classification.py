"""Primary membrane classes stay mutually exclusive and API filters share one source."""
import unittest

from fastapi.testclient import TestClient

from Web.src.api.main import app


class MembraneClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_hierarchy_counts_and_filters_match(self):
        expected = {
            'integral_membrane': 5654,
            'transmembrane': 5213,
            'single_pass': 2380,
            'multi_pass': 2833,
            'lipid_anchored': 441,
            'peripheral_membrane': 1015,
            'membrane_related': 1046,
        }
        response = self.client.get('/api/catalog/summary')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['total_proteins'], 7715)
        self.assertEqual({row['key']: row['count'] for row in payload['classes']}, expected)
        for key, count in expected.items():
            filtered = self.client.get('/api/proteins', params={'membrane_class': key, 'limit': 1})
            self.assertEqual(filtered.status_code, 200)
            self.assertEqual(filtered.json()['total'], count)

    def test_overview_preserves_primary_class_and_source_labels(self):
        overview = self.client.get('/api/proteins/P00533/overview')
        self.assertEqual(overview.status_code, 200)
        data = overview.json()
        classification = data['membrane_classification']
        self.assertEqual(classification['primary_class'], 'transmembrane')
        self.assertEqual(classification['transmembrane_subclass'], 'single_pass')
        self.assertEqual(classification['canonical_tm_feature_count'], 1)
        self.assertTrue(data['membrane_labels'])
        summary = self.client.get('/api/proteins/P00533/overview/membrane/summary')
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.json()['classification'], classification)


if __name__ == '__main__':
    unittest.main()
