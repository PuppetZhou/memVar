"""Direct jumps preserve filtered source ordering and cursor continuation."""
import unittest
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.db import query


class DirectPaginationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def get(self, path, **params):
        response = self.client.get(path, params=params)
        self.assertEqual(response.status_code, 200, response.text[:300])
        return response.json()

    def assert_jump(self, path, params, key='items', limit=1):
        first = self.get(path, limit=limit, **params)
        self.assertTrue(first['next_cursor'])
        sequential = self.get(path, limit=limit, cursor=first['next_cursor'], **params)
        direct = self.get(path, limit=limit, offset=limit, **params)
        self.assertEqual(direct[key], sequential[key])
        self.assertEqual(direct['next_cursor'], sequential['next_cursor'])
        both = self.get(path, limit=limit, cursor=first['next_cursor'], offset=99999, **params)
        self.assertEqual(both[key], sequential[key])
        self.assertEqual(self.client.get(path, params={**params, 'offset': -1}).status_code, 422)
        return first

    def test_filtered_cursor_lists(self):
        cases = [
            ('variants', {'source': 'ClinVar', 'consequence': 'missense_variant', 'predictors': 'none'}),
            ('ppi', {'source': 'IntAct'}),
            ('expression', {'source': 'HPA', 'category': 'single_cell'}),
            ('qtl', {'source': 'GTEx', 'qtl_type': 'apaqtl'}),
            ('diseases', {'source': 'HPO'}),
            ('diseases/ptmd', {}),
        ]
        for suffix, params in cases:
            with self.subTest(endpoint=suffix):
                self.assert_jump('/api/proteins/P00533/' + suffix, params)

    def test_phenotypes_and_filter_bound_cursor(self):
        path = '/api/diseases/OMIM:616069'
        self.assert_jump(path, {'accession': 'P00533'}, key='phenotypes')
        path = '/api/proteins/P00533/diseases'
        first = self.get(path, limit=1, source='HPO')
        response = self.client.get(path, params={'source': 'GenCC', 'cursor': first['next_cursor'], 'offset': 1})
        self.assertEqual(response.status_code, 400)

    def test_expression_cross_dataset_boundary_and_context(self):
        path = '/api/proteins/P00533/expression'
        # One bounded page independently supplies both sides of GTEx -> HPA transition.
        baseline = self.get(path, category='normal', limit=100)['items']
        boundary = next(i for i, row in enumerate(baseline) if row['dataset'] != baseline[0]['dataset'])
        page = self.get(path, category='normal', offset=boundary - 1, limit=3)
        self.assertEqual(page['items'], baseline[boundary - 1:boundary + 2])
        after = self.get(path, category='normal', cursor=page['next_cursor'], limit=3)
        self.assertEqual(after['items'], baseline[boundary + 2:boundary + 5])
        record = baseline[boundary]
        params = {'category': 'normal', 'dataset': record['dataset'], 'context_key': record['context_key']}
        scoped = self.get(path, limit=100, **params)['items']
        self.assertTrue(scoped)
        self.assertEqual(self.get(path, offset=1, limit=100, **params)['items'], scoped[1:])

    def test_qtl_cross_dataset_boundary(self):
        path = '/api/proteins/P00533/qtl'
        counts = query('''SELECT d.dataset_id,sum(c.record_count)::bigint records
            FROM web_context.qtl_context_count c JOIN web_context.context_dataset d USING(dataset_id)
            WHERE c.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession='P00533')
            AND d.provider='GTEx' AND c.table_name='gtex_qtl_pair'
            GROUP BY d.dataset_id ORDER BY d.dataset_id''')
        boundary = counts[0]['records']
        page = self.get(path, source='GTEx', offset=boundary - 1, limit=1)
        self.assertEqual(page['items'][0]['record_id'], counts[0]['dataset_id'] + ':' + str(boundary - 1))
        sequential = self.get(path, source='GTEx', cursor=page['next_cursor'], limit=2)
        direct = self.get(path, source='GTEx', offset=boundary, limit=2)
        self.assertEqual(direct['items'], sequential['items'])
        self.assertEqual(direct['items'][0]['record_id'], counts[1]['dataset_id'] + ':0')
        spanning = self.get(path, source='GTEx', offset=boundary - 1, limit=3)
        self.assertEqual(spanning['items'], page['items'] + direct['items'])

    def test_out_of_range_empty_pages(self):
        for suffix, params in [('diseases', {'source': 'HPO'}), ('diseases/ptmd', {}),
                               ('expression', {'category': 'normal', 'dataset': 'rna_tissue_hpa'}),
                               ('qtl', {'source': 'GTEx', 'qtl_type': 'apaqtl'})]:
            with self.subTest(endpoint=suffix):
                page = self.get('/api/proteins/P00533/' + suffix, offset=99999, limit=1, **params)
                self.assertEqual(page['items'], [])
                self.assertIsNone(page['next_cursor'])


if __name__ == '__main__':
    unittest.main()
