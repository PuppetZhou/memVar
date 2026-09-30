"""HTTP contracts for the GTEx tracks sharing the genomic browser's gene context.

Like the AlphaGenome/AVI HTTP tests, these use the installed read-only service
database. Boundary and paging expectations come from a small source-row sample.
"""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from Web.src.api import alphagenome
from Web.src.api.db import one, query
from Web.src.api.main import app


class QtlTrackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.base = '/api/proteins/P00533/qtl'
        cls.gene = 'ENSG00000146648'
        cls.dataset = 'gtex:eqtl:Adipose_Subcutaneous'
        cls.params = dict(gene=cls.gene, dataset=cls.dataset,
                          chromosome='chr7', start=0, end=159345973)
        cls.sample = query('''SELECT source_row,variant_id,phenotype_id,pval_nominal,
            slope,slope_se,pval_nominal_threshold FROM web_context.gtex_qtl_pair
            WHERE hgnc_id='HGNC:3236' AND dataset_id=:dataset
            ORDER BY source_row LIMIT 3''', {'dataset': cls.dataset})
        if len(cls.sample) != 3:
            raise AssertionError('The installed EGFR GTEx fixture must contain three source rows')

    def get(self, suffix, **params):
        response = self.client.get(self.base + suffix, params=params)
        self.assertEqual(response.status_code, 200, response.text[:300])
        return response.json()

    def test_catalog_retains_tissues_types_and_source_counts(self):
        catalog = self.get('/tracks', gene=self.gene)
        self.assertEqual((catalog['assembly'], catalog['source']), ('GRCh38', 'GTEx v11'))
        self.assertEqual({r['qtl_type'] for r in catalog['items']}, {'eqtl', 'sqtl', 'apaqtl'})
        self.assertTrue(all(r['tissue'] and r['records'] > 0 for r in catalog['items']))
        entry = next(r for r in catalog['items'] if r['dataset_id'] == self.dataset)
        count = one('''SELECT count(*) AS records FROM web_context.gtex_qtl_pair
            WHERE hgnc_id='HGNC:3236' AND dataset_id=:dataset''', {'dataset': self.dataset})
        self.assertEqual(entry['records'], count['records'])
        self.assertEqual(entry['tissue'], 'Adipose_Subcutaneous')

    def test_unlinked_gene_and_changed_current_identity_are_rejected(self):
        for suffix, params in [('/tracks', {'gene': self.gene}), ('/track', self.params)]:
            with self.subTest(endpoint=suffix):
                invalid = self.client.get(self.base + suffix, params={**params, 'gene': 'ENSG00000000000'})
                self.assertEqual(invalid.status_code, 404)
                self.assertEqual(invalid.json()['detail'], 'Gene is not linked to this protein')
                # Frozen AlphaGenome membership alone does not authorize a gene
                # removed from the current protein's HGNC identity.
                with patch('Web.src.api.alphagenome.get_protein', return_value={
                        'accession': 'P00533', 'hgnc_ids': ['HGNC:other']}):
                    changed = self.client.get(self.base + suffix, params=params)
                self.assertEqual(changed.status_code, 404)

    def test_dataset_must_be_gtex_and_available_for_the_selected_gene(self):
        # Both datasets exist: one is another provider linked to EGFR, the other
        # is a GTEx collection with no recorded pair for the selected gene.
        other_provider = one('''SELECT d.dataset_id FROM web_context.context_dataset d
            JOIN web_context.qtl_context_count c USING(dataset_id)
            WHERE c.hgnc_id='HGNC:3236' AND d.provider<>'GTEx'
            ORDER BY d.dataset_id LIMIT 1''')['dataset_id']
        other_gene = one('''SELECT c.dataset_id FROM web_context.qtl_context_count c
            JOIN web_context.context_dataset d USING(dataset_id)
            WHERE c.table_name='gtex_qtl_pair' AND d.provider='GTEx'
            AND NOT EXISTS(SELECT 1 FROM web_context.qtl_context_count own
                WHERE own.hgnc_id='HGNC:3236' AND own.dataset_id=c.dataset_id
                AND own.table_name='gtex_qtl_pair') LIMIT 1''')['dataset_id']
        for dataset in (other_provider, other_gene, 'not-a-dataset'):
            with self.subTest(dataset=dataset):
                response = self.client.get(self.base + '/track', params={**self.params, 'dataset': dataset})
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()['detail'], 'GTEx dataset is not available for this gene')

    def test_half_open_interval_keeps_source_position_and_values(self):
        source = self.sample[0]
        position = int(source['variant_id'].split('_')[1])
        included = self.get('/track', **{**self.params, 'start': position - 1, 'end': position})
        self.assertTrue(included['items'])
        self.assertTrue(all(r['position'] == position for r in included['items']))
        record = next(r for r in included['items'] if r['source_row'] == source['source_row'])
        self.assertEqual(record, {**source, 'position': position})
        excluded = self.get('/track', **{**self.params, 'start': position, 'end': position + 1})
        self.assertNotIn(source['source_row'], [r['source_row'] for r in excluded['items']])
        other_chromosome = self.get('/track', **{**self.params, 'chromosome': 'chr8',
                                              'start': position - 1, 'end': position})
        self.assertEqual(other_chromosome['items'], [])

    def test_paging_preserves_source_order_counts_and_empty_page_contract(self):
        first = self.get('/track', **self.params, limit=2)
        next_page = self.get('/track', **self.params, limit=1, offset=2)
        expected = [{**r, 'position': int(r['variant_id'].split('_')[1])} for r in self.sample]
        self.assertEqual(first['items'] + next_page['items'], expected)
        self.assertTrue(first['has_more'])
        self.assertEqual(first['total'], next_page['total'])
        self.assertEqual(next_page['offset'], 2)
        last = self.get('/track', **self.params, limit=2, offset=first['total'] - 1)
        self.assertEqual(len(last['items']), 1)
        self.assertEqual(last['total'], first['total'])
        self.assertFalse(last['has_more'])
        empty = self.get('/track', **self.params, limit=2, offset=first['total'])
        # count(*) OVER() has no row on an empty page: retain the existing API
        # behavior rather than introducing another count query in this refactor.
        self.assertEqual((empty['items'], empty['total'], empty['has_more']), ([], 0, False))

    def test_invalid_intervals_and_pagination_are_rejected(self):
        for changed in ({'start': -1}, {'end': 0}, {'start': 10, 'end': 10},
                        {'start': 11, 'end': 10}, {'offset': -1}, {'limit': 0}, {'limit': 5001}):
            with self.subTest(changed=changed):
                response = self.client.get(self.base + '/track', params={**self.params, **changed})
                self.assertEqual(response.status_code, 422)

    def test_each_http_request_resolves_gene_identity_once(self):
        for suffix, params in [('/tracks', {'gene': self.gene}),
                               ('/track', {**self.params, 'limit': 1})]:
            with self.subTest(endpoint=suffix), patch(
                    'Web.src.api.alphagenome.candidates', wraps=alphagenome.candidates) as candidates:
                self.get(suffix, **params)
                self.assertEqual(candidates.call_count, 1)


if __name__ == '__main__':
    unittest.main()
