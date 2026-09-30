"""AVI coordinates, allele pagination and source-value display boundaries."""
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from Web.src.api.avi import FEATURES, read_cursor, write_cursor
from Web.src.api.main import app


class AviTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.base = '/api/proteins/P00533/expression/alphagenome/avi'
        self.args = dict(gene='ENSG00000146648', tile='HGNC_3236_tile000', start=100, end=200)
        self.context = ({'hgnc_id': 'HGNC:3236'}, dict(chromosome='chr7',
                        window_start_0based=0, window_end_0based=1048576))

    def test_cursor_is_bound_to_viewport_and_retains_same_position_alleles(self):
        context = ['P00533', 'ENSG00000146648', 'HGNC_3236_tile000', 100, 200]
        cursor = write_cursor(dict(position=101, variant_id='GRCh38:7:101:A:C'), context)
        self.assertEqual(read_cursor(cursor, context), (101, 'GRCh38:7:101:A:C'))
        with self.assertRaises(HTTPException):
            read_cursor(cursor, context[:-1]+[201])
        with self.assertRaises(HTTPException):
            read_cursor('not a cursor', context)

    def test_track_keeps_zero_negative_and_missing_scores(self):
        items = [dict(variant_id='GRCh38:7:101:A:C', position=101, ref='A', alt='C',
                      raw=-0.1, phred=0, status='matched'),
                 dict(variant_id='GRCh38:7:101:A:G', position=101, ref='A', alt='G',
                      raw=None, phred=None, status='position_not_found')]
        with patch('Web.src.api.alphagenome.get_context', return_value=self.context, create=True), \
             patch('Web.src.api.avi.one', return_value={'n': 2, 'attribution_available': False}), \
             patch('Web.src.api.avi.query', return_value=items) as fetch:
            response = self.client.get(self.base, params={**self.args, 'limit': 1})
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertEqual(body['items'][0]['raw'], -0.1)
            self.assertEqual(body['items'][0]['phred'], 0)
            self.assertEqual(body['items'][0]['contributions'], [])
            self.assertEqual(body['items'][0]['attribution_status'], 'not_available')
            self.assertEqual(body['attribution_status'], 'not_available')
            self.assertIsNone(body['source_snapshot'])
            self.assertTrue(body['has_more'])
            sql, values = fetch.call_args.args
            self.assertIn('v.pos>:start AND v.pos<=:end', sql)
            self.assertEqual(values['start'], 100)
            self.assertEqual(values['chrom'], '7')

    def test_track_contributions_keep_source_values_statuses_and_allele_pagination(self):
        def row(alt, status, linked=True):
            result = {feature + '_contribution': None for feature, _, _ in FEATURES}
            result.update(variant_id='GRCh38:7:101:A:' + alt, position=101, ref='A', alt=alt,
                          raw=-0.25, phred=0, status='matched',
                          attribution_variant_id='GRCh38:7:101:A:' + alt if linked else None,
                          avi_attribution_status=status, source_snapshot='source_example')
            return result
        records = [row('C', 'matched_missing_score'), row('G', 'position_not_found'), row('T', None, False)]
        records[0].update(merged_splicing_contribution=0, max_abs_atac_contribution=-0.1,
                          max_abs_contact_maps_contribution=1.2345678901234567)
        with patch('Web.src.api.alphagenome.get_context', return_value=self.context), \
             patch('Web.src.api.avi.one', return_value={'n': 3, 'attribution_available': True}) as count, \
             patch('Web.src.api.avi.query', return_value=records) as fetch:
            response = self.client.get(self.base, params={**self.args, 'limit': 2})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body['attribution_status'], 'available')
        self.assertEqual(body['source_snapshot'], 'source_example')
        self.assertEqual(len(body['items']), 2)
        self.assertTrue(body['has_more'])
        first, missing = body['items']
        self.assertEqual(first['raw'], -0.25)
        self.assertEqual(first['phred'], 0)
        self.assertEqual(first['attribution_status'], 'matched_missing_score')
        self.assertEqual(len(first['contributions']), 18)
        self.assertEqual([v['value'] for v in first['contributions'][:4]],
                         [0, -0.1, 1.2345678901234567, None])
        self.assertEqual(missing['attribution_status'], 'position_not_found')
        self.assertTrue(all(v['value'] is None for v in missing['contributions']))
        context = ['P00533', self.args['gene'], self.args['tile'], 100, 200]
        self.assertEqual(read_cursor(body['next_cursor'], context), (101, 'GRCh38:7:101:A:G'))
        count.assert_called_once()
        fetch.assert_called_once()
        sql, _ = fetch.call_args.args
        self.assertIn('LEFT JOIN web_avi.attribution', sql)
        self.assertIn('web_avi._build_manifest', sql)

    def test_empty_score_page_retains_attribution_snapshot_without_a_fake_snv(self):
        with patch('Web.src.api.alphagenome.get_context', return_value=self.context), \
             patch('Web.src.api.avi.one', return_value={'n': 0, 'attribution_available': True}), \
             patch('Web.src.api.avi.query', return_value=[{'variant_id': None,
                   'source_snapshot': 'installed_source'}]):
            response = self.client.get(self.base, params=self.args)
        body = response.json()
        self.assertEqual(body['items'], [])
        self.assertEqual(body['source_snapshot'], 'installed_source')
        self.assertEqual(body['attribution_status'], 'available')
        self.assertFalse(body['has_more'])
        self.assertIsNone(body['next_cursor'])

    def test_installed_contributions_distinguish_an_absent_variant_row(self):
        row = dict(variant_id='GRCh38:7:101:A:C', position=101, ref='A', alt='C',
                   raw=1.25, phred=2.5, status='matched', attribution_variant_id=None,
                   avi_attribution_status=None, source_snapshot='installed_source')
        with patch('Web.src.api.alphagenome.get_context', return_value=self.context), \
             patch('Web.src.api.avi.one', return_value={'n': 1, 'attribution_available': True}), \
             patch('Web.src.api.avi.query', return_value=[row]):
            response = self.client.get(self.base, params=self.args)
        body = response.json()
        self.assertEqual(body['attribution_status'], 'available')
        self.assertEqual(body['items'][0]['attribution_status'], 'not_available')
        self.assertEqual(body['items'][0]['contributions'], [])
        self.assertEqual(body['items'][0]['raw'], 1.25)

    def test_optional_light_response_does_not_join_contribution_tables(self):
        item = dict(variant_id='GRCh38:7:101:A:C', position=101, ref='A', alt='C',
                    raw=None, phred=None, status='position_not_found')
        with patch('Web.src.api.alphagenome.get_context', return_value=self.context), \
             patch('Web.src.api.avi.one', return_value={'n': 1, 'attribution_available': True}), \
             patch('Web.src.api.avi.query', return_value=[item]) as fetch:
            response = self.client.get(self.base, params={**self.args, 'include_contributions': False})
        body = response.json()
        self.assertEqual(body['attribution_status'], 'not_requested')
        self.assertIsNone(body['source_snapshot'])
        self.assertEqual(body['items'][0]['contributions'], [])
        self.assertEqual(body['items'][0]['attribution_status'], 'not_requested')
        self.assertNotIn('web_avi.attribution', fetch.call_args.args[0])

    def test_invalid_range_never_queries_scores(self):
        with patch('Web.src.api.alphagenome.get_context', return_value=self.context, create=True), \
             patch('Web.src.api.avi.query') as fetch:
            response = self.client.get(self.base, params={**self.args, 'end': 100})
            self.assertEqual(response.status_code, 422)
            fetch.assert_not_called()

    def test_detail_does_not_reconstruct_avi_from_contributions(self):
        variant = dict(variant_id='GRCh38:7:101:A:C', chromosome='7', position=101,
                       ref='A', alt='C', raw=-0.25, phred=0, status='matched')
        record = {feature+'_contribution': None for feature, _, _ in FEATURES}
        record.update(variant_id=variant['variant_id'], source_snapshot='example',
                      avi_attribution_status='matched_missing_score',
                      merged_splicing_contribution=0, max_abs_atac_contribution=-0.1)
        with patch('Web.src.api.avi.one', side_effect=[variant, {'available': True}, record]):
            response = self.client.get('/api/variants/GRCh38:7:101:A:C/avi')
        body = response.json()
        self.assertEqual(body['score']['raw'], -0.25)
        self.assertEqual(body['attribution']['source_snapshot'], 'example')
        self.assertEqual(len(body['attribution']['contributions']), 18)
        self.assertEqual(body['attribution']['contributions'][0]['value'], 0)
        self.assertEqual(body['attribution']['contributions'][1]['value'], -0.1)
        self.assertIsNone(body['attribution']['contributions'][2]['value'])

    def test_unmapped_detail_retains_installed_source_snapshot(self):
        variant = dict(variant_id='GRCh38:7:101:A:C', chromosome='7', position=101,
                       ref='A', alt='C', raw=None, phred=None, status='position_not_found')
        with patch('Web.src.api.avi.one', side_effect=[variant, {'available': True},
                {'variant_id': None, 'source_snapshot': 'installed_snapshot'}]):
            response = self.client.get('/api/variants/GRCh38:7:101:A:C/avi')
        body = response.json()['attribution']
        self.assertEqual(body['source_snapshot'], 'installed_snapshot')
        self.assertEqual(body['status'], 'not_available')
        self.assertEqual(body['contributions'], [])


if __name__ == '__main__':
    unittest.main()
