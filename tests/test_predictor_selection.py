"""Read-only regression for the shared prediction column's expanded selection."""
import unittest

from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.evidence import prediction_dictionary


class PredictorSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.root = '/api/proteins/P00533/variants'
        cls.fields = [p['field'] for p in prediction_dictionary()]

    def page(self, fields, **kwargs):
        response = self.client.get(self.root, params={
            'predictors': ','.join(fields) if fields else 'none', 'limit': 3, **kwargs})
        self.assertEqual(response.status_code, 200, response.text[:300])
        return response.json()

    def test_all_fields_preserve_selected_order_and_existing_evidence(self):
        selected = ['AlphaMissense_score', 'SIFT_score', 'REVEL_score', 'CADD_phred']
        small = self.page(selected)
        large = self.page(self.fields)
        self.assertGreater(len(self.fields), 12)
        self.assertTrue(large['items'])
        for before, after in zip(small['items'], large['items'], strict=True):
            self.assertEqual(before['annotation_id'], after['annotation_id'])
            self.assertEqual([p['field'] for p in after['predictions']], self.fields)
            by_field = {p['field']: p for p in after['predictions']}
            self.assertEqual(before['predictions'], [by_field[f] for f in selected])
        next_page = self.page(self.fields, cursor=large['next_cursor'])
        key = lambda row: (row['variant_id'], row['annotation_id'], row['gene_id'])
        self.assertFalse({key(r) for r in large['items']} & {key(r) for r in next_page['items']})

    def test_duplicate_empty_and_unknown_selections(self):
        row = self.page(['SIFT_score', 'REVEL_score', 'SIFT_score'])['items'][0]
        self.assertEqual([p['field'] for p in row['predictions']], ['SIFT_score', 'REVEL_score'])
        self.assertEqual(self.page([])['items'][0]['predictions'], [])
        self.assertEqual(self.client.get(self.root, params={
            'predictors': 'SIFT_score,unknown_score'}).status_code, 422)

    def test_cursor_remains_bound_to_selection(self):
        first = self.page(self.fields)
        response = self.client.get(self.root, params={
            'predictors': 'SIFT_score', 'cursor': first['next_cursor']})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
