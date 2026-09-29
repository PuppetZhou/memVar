"""Direct-summary identity, overlapping categories and database serving checks."""
import os
import unittest
from collections import defaultdict
from pathlib import Path

from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.disease_classification import mondo_ids, record_classification, distribution, SCHEMES


class ClassificationIdentityTests(unittest.TestCase):
    def test_only_exact_direct_summary_identifiers(self):
        self.assertEqual(mondo_ids('MONDO:0000001|MONDO:MONDO:0000002; MONDO:0000001,OMIM:123456'),
                         ['MONDO:0000001', 'MONDO:0000002'])
        self.assertEqual(mondo_ids('MONDO:123;prefixMONDO:0000001;MONDO:00000010;RCV0000001'), [])
        self.assertEqual(mondo_ids(None), [])

    def test_record_does_not_inherit_other_source_diseases(self):
        data = {'available': True, 'by_mondo': {'MONDO:0000001': [{'category_id': 'a'}],
                                               'MONDO:0000002': [{'category_id': 'b'}]}}
        result = record_classification('MONDO:0000001', data)
        self.assertEqual(result['diseases'], [{'mondo_id': 'MONDO:0000001', 'classifications': [{'category_id': 'a'}]}])
        self.assertEqual(record_classification('OMIM:123456', data)['diseases'], [])
        self.assertFalse(record_classification(None, {'available': False, 'by_mondo': {}})['available'])


@unittest.skipUnless(os.environ.get('MEMVAR_LIVE_TESTS') == '1', 'Requires the imported local service database')
class ClassificationLiveTests(unittest.TestCase):
    def test_egfr_matches_independent_published_parquet_sets(self):
        import pyarrow.parquet as pq
        from Web.src.api.evidence_disease import clinvar_condition_rows
        root = Path(__file__).resolve().parents[2]
        ids = {row['variant_id'] for row in clinvar_condition_rows('P00533')}
        data = distribution(list(ids) + list(ids))  # Duplicate source associations must not change the denominator.
        self.assertEqual(data['total_variants'], len(ids))
        mapping = defaultdict(set)
        for row in pq.read_table(root / 'manuscript/analysis/result/q7_multiaxis_v1/context_classification_mapping.parquet').to_pylist():
            if row['subject_type'] == 'disease' and row['category_id']:
                mapping[row['subject_id']].add((row['scheme'], row['category_level'], row['category_id']))
        expected, mapped, with_mondo = defaultdict(set), defaultdict(set), set()
        for row in pq.read_table(root / 'manuscript/analysis/result/q7_summary_variant_mondo.parquet').to_pylist():
            id = row['variant_id']
            if id in ids:
                with_mondo.add(id)
                for scheme, level, category in mapping[row['mondo_id']]:
                    expected[scheme, level, category].add(id)
                    mapped[scheme, level].add(id)
        self.assertEqual(data['variants_with_mondo'], len(with_mondo))
        for result in data['schemes']:
            key = result['scheme'], result['level']
            self.assertEqual(result['mapped_variants'], len(mapped[key]))
            self.assertEqual(result['mapped_variants'] + result['unmapped_variants'], len(ids))
            for item in result['items']:
                self.assertEqual(item['variant_count'], len(expected[*key, item['category_id']]))
        etiology = data['schemes'][1]
        self.assertGreater(sum(item['variant_count'] for item in etiology['items']), etiology['mapped_variants'])

    def test_empty_and_missing_mondo_are_not_negative_categories(self):
        data = distribution([])
        self.assertEqual(data['total_variants'], 0)
        self.assertEqual(len(data['schemes']), len(SCHEMES))
        self.assertTrue(all(item['variant_count'] == 0 for scheme in data['schemes'] for item in scheme['items']))

    def test_http_contract_and_invalid_protein(self):
        client = TestClient(app)
        response = client.get('/api/proteins/P00533/diseases/clinvar-classification')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['overlapping_categories'])
        self.assertFalse(response.json()['kegg_disease_identity_equivalence'])
        self.assertNotIn('/home/', response.text)
        self.assertEqual(client.get('/api/proteins/INVALID/diseases/clinvar-classification').status_code, 404)


if __name__ == '__main__':
    unittest.main()
