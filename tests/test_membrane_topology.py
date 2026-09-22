"""Source evidence and mapping boundaries for the membrane overview."""
import unittest
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.membrane_topology import parse_topology_evidence, topology_records


class MembraneTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.records = topology_records('P00533', 'P00533')

    def page(self, source, **params):
        response = self.client.get('/api/proteins/P00533/overview/membrane/topology',
                                   params={'source_sequence_id': source, **params})
        response.raise_for_status()
        return response.json()

    def test_htp_original_score_and_distinct_parent_facts(self):
        htp = next(r for r in self.records if r['source'] == 'HTP')
        self.assertEqual(htp['reported_tm_counts'], ['1'])
        self.assertEqual(htp['reliability_values'], ['94.77'])
        self.assertEqual(len(htp['methods']), 11)
        self.assertEqual(htp['constraint_regions'], 9)
        self.assertEqual([(s['start'], s['end']) for s in htp['integrated_segments']],
                         [(1, 24), (25, 645), (646, 667), (668, 1210)])

    def test_method_filter_pagination_and_constraint_models(self):
        page = self.page('seq:9872', role='method_prediction', method='Hmmtop', limit=2)
        second = self.page('seq:9872', role='method_prediction', method='Hmmtop', limit=2, offset=2)
        self.assertEqual(page['total'], 6)
        self.assertTrue(page['has_more'])
        self.assertTrue(all(r['method'] == 'Hmmtop' for r in page['items']))
        self.assertFalse({r['feature_id'] for r in page['items']} & {r['feature_id'] for r in second['items']})
        constraints = self.page('seq:9872', role='constraint')
        self.assertTrue(any(r['domains'] for r in constraints['items']))

    def test_topdb_evidence_preserves_structure_reference_and_chain(self):
        row = self.page('seq:1527', role='experimental_evidence', limit=1)['items'][0]
        self.assertEqual(row['evidence'][0]['reference'], '26586721')
        self.assertEqual(row['evidence'][0]['structures'], [{'id': '4uv7', 'chains': ['A']}])
        self.assertEqual(row['locations'][0]['mapping_status'], 'exact_full_sequence')
        self.assertNotIn('evidence_xml', row['source_attributes'])

    def test_identity_only_source_is_retained_without_canonical_positions(self):
        source = next(r for r in self.records if r['feature_count'] and not r['mapped_feature_count'])
        rows = self.page(source['source_sequence_id'])['items']
        self.assertTrue(rows)
        self.assertTrue(all(not r['locations'] for r in rows))

    def test_foreign_record_rejected(self):
        response = self.client.get('/api/proteins/Q12809/overview/membrane/topology',
                                   params={'source_sequence_id': 'seq:9872'})
        self.assertEqual(response.status_code, 404)

    def test_evidence_missing_malformed_and_literal_zero(self):
        self.assertEqual(parse_topology_evidence({}), ([], 'not_supplied'))
        self.assertEqual(parse_topology_evidence({'evidence_xml': '<bad'}), ([], 'unparsed'))
        evidence, status = parse_topology_evidence({'evidence_xml': '<Region xmlns="test"><Exp Ref="123"><Type>Experiment</Type><Value>0</Value></Exp></Region>'})
        self.assertEqual(status, 'parsed')
        self.assertEqual(evidence[0]['value'], '0')


if __name__ == '__main__':
    unittest.main()
