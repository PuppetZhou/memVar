"""Coverage is finite-score presence, not a merged effect or pathogenicity score."""
import unittest
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.db import query, one
from Web.src.api.sequence_prediction_coverage import COUNTS_SQL, finite_score_sql


class SequencePredictionCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.path = '/api/proteins/P00533/sequence/prediction-coverage'

    def get(self, path, **params):
        r = self.client.get(path, params=params)
        self.assertEqual(r.status_code, 200, r.text[:300])
        return r.json()

    def test_finite_zero_and_missing_values(self):
        rows = query('''WITH scores(name,value) AS (VALUES
            ('zero',0::double precision),('positive',0.25::double precision),
            ('missing',NULL::double precision),('nan','NaN'::double precision),
            ('positive_infinity','Infinity'::double precision),('negative_infinity','-Infinity'::double precision))
            SELECT name FROM scores WHERE ''' + finite_score_sql('value') + ' ORDER BY name')
        self.assertEqual([r['name'] for r in rows], ['positive','zero'])

    def test_duplicate_transcripts_do_not_inflate_variant_counts(self):
        rows = query('''WITH mapped(variant_id,annotation_id,gene_id,scored,position) AS (VALUES
            ('v1','a1','g1',true,10),('v1','a1','g1',true,10),
            ('v1','a2','g1',true,10),('v2','a3','g1',false,10),
            ('v1','a1','g1',true,20)) ''' + COUNTS_SQL)
        first, second, total = rows
        self.assertEqual((first['variant_count'],first['scored_variant_count']), (2,1))
        self.assertEqual((first['annotation_count'],first['scored_annotation_count']), (3,2))
        self.assertEqual((second['variant_count'],second['scored_variant_count']), (1,1))
        self.assertEqual((total['variant_count'],total['scored_variant_count']), (2,1))
        self.assertEqual((total['annotation_count'],total['scored_annotation_count']), (3,2))

    def test_filtered_sites_match_original_variant_rows(self):
        for field in ('AlphaMissense_score','REVEL_score','SIFT_score'):
            with self.subTest(field=field):
                data = self.get(self.path, predictor=field, source='ClinVar')
                self.assertEqual(data['predictor']['field'], field)
                self.assertEqual(data['mapping_scope'],'verified_canonical_ddg_links')
                self.assertTrue(data['sites'])
                site = data['sites'][0]
                p = site['position']
                page = self.get('/api/proteins/P00533/variants', **data['detail_query'],
                                canonical_start=p,canonical_end=p,limit=100)
                self.assertIsNone(page['next_cursor'])
                scored = {r['variant_id'] for r in page['items'] if any(s['field']==field and isinstance(s['value'],(float,int)) for s in r['predictions'])}
                self.assertEqual(site['variant_count'],len({r['variant_id'] for r in page['items']}))
                self.assertEqual(site['scored_variant_count'],len(scored))
                self.assertTrue(all('score' not in r and 'mean' not in r and 'maximum' not in r for r in data['sites']))

    def test_real_sift_zero_is_covered_and_detail_retains_value(self):
        candidate = one('''SELECT d.position,c.variant_id FROM web_variant.variant_consequence c
            JOIN web_variant.variant_ddg_link l USING(variant_id,annotation_id,gene_id)
            JOIN web_variant.ddg_prediction d USING(prediction_id)
            WHERE c.gene_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession='P00533')
            AND d.sequence_id='P00533' AND c."SIFT_score"=0 LIMIT 1''')
        self.assertIsNotNone(candidate)
        data = self.get(self.path,predictor='SIFT_score')
        site = next(s for s in data['sites'] if s['position']==candidate['position'])
        self.assertGreater(site['scored_variant_count'],0)
        page = self.get('/api/proteins/P00533/variants',predictors='SIFT_score',
                        canonical_start=site['position'],canonical_end=site['position'],limit=100)
        row = next(r for r in page['items'] if r['variant_id']==candidate['variant_id'])
        self.assertEqual(row['predictions'][0]['value'],0)

    def test_empty_and_invalid_choices(self):
        empty = self.get(self.path,consequence='not_a_retained_consequence')
        self.assertEqual(empty['sites'],[])
        self.assertEqual(empty['totals']['mapped_variants'],0)
        for params in [{'predictor':'CADD_phred'},{'predictor':'bad"SQL'},{'source':'Unknown'},{'transcript_status':'bad'}]:
            self.assertEqual(self.client.get(self.path,params=params).status_code,422)
        self.assertEqual(self.client.get('/api/proteins/NOT_A_PROTEIN/sequence/prediction-coverage').status_code,404)


if __name__=='__main__':
    unittest.main()
