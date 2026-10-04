"""The confirmed strongest-effect extrema must preserve direction and provenance."""
import unittest
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.structure_predictors import summarize_sites, FIELDS


def record(score, i, position=10):
    return dict(score=score,position=position,variant_id=f'v{i}',annotation_id=f'a{i}',gene_id='g',
                ref_aa='L',alt_aa='R' if i%2 else 'M',prediction_id=i)


class StructureExtremaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client=TestClient(app)

    def get(self, accession='P00533', field='AlphaMissense_score', endpoint='predictor-extrema'):
        response=self.client.get(f'/api/proteins/{accession}/structure/{endpoint}',params={'field':field,'limit':10000})
        self.assertEqual(response.status_code,200,response.text[:300])
        return response.json()

    def test_direction_ties_zero_and_nonfinite(self):
        rows=[record(v,i) for i,v in enumerate([-.8,.7,.7,None,float('nan'),float('inf')])]
        maximum=summarize_sites(rows,'AlphaMissense_score')[0]
        self.assertEqual(maximum['score'],.7)
        self.assertEqual([r['variant_id'] for r in maximum['records']],['v1','v2'])
        self.assertEqual(maximum['scored_variant_count'],3)
        self.assertEqual(summarize_sites(rows,'ESM1b_score')[0]['score'],-.8)
        self.assertEqual(summarize_sites(rows,'ThermoMPNN_ddg')[0]['score'],-.8)
        tied=summarize_sites([record(-2,0),record(2,1)],'ThermoMPNN_ddg')[0]
        self.assertEqual(tied['status'],'opposite_sign_tie')
        self.assertIsNone(tied['score'])
        self.assertEqual(tied['extreme_values'],[-2,2])
        zero=summarize_sites([record(0,0),record(None,1)],'ThermoMPNN_ddg')[0]
        self.assertEqual((zero['status'],zero['score']),('scored',0))
        missing=summarize_sites([record(None,0),record(float('-inf'),1)],'ESM1b_score')[0]
        self.assertEqual(missing['status'],'no_finite_score')
        self.assertIsNone(missing['score'])

    def test_duplicate_annotations_do_not_change_extrema_or_variant_count(self):
        rows=[record(.7,0),record(.3,1)]
        duplicate={**rows[0],'annotation_id':'other'}
        site=summarize_sites(rows+[duplicate],'AlphaMissense_score')[0]
        self.assertEqual(site['score'],.7)
        self.assertEqual(site['scored_variant_count'],2)
        self.assertEqual(site['scored_annotation_count'],3)
        self.assertEqual(len(site['records']),2)

    def test_all_real_model_extrema_match_complete_original_records(self):
        for field in FIELDS:
            with self.subTest(field=field):
                data=self.get(field=field)
                raw=self.get(field=field,endpoint='predictor-records')
                self.assertIsNone(raw['next_offset'])
                self.assertEqual(data['sites'],summarize_sites(raw['items'],field))
                site=next(s for s in data['sites'] if s['position']==858)
                expected={'AlphaMissense_score':.9968,'ESM1b_score':-11.775072,
                          'ThermoMPNN_ddg':.05236208438873291,'alphagenome_avi_raw':1.47}
                if field in expected:
                    self.assertAlmostEqual(site['score'],expected[field],places=7)
                self.assertGreater(data['scale']['max'],data['scale']['min'])
                self.assertTrue(all(r['sequence_id']=='P00533' for s in data['sites'] for r in s['records']))
                self.assertEqual(data['scored_positions'],sum(bool(s['extreme_values']) for s in data['sites']))

    def test_empty_unknown_and_invalid_field(self):
        data=self.get(accession='A0A075B6H7',field='ThermoMPNN_ddg')
        self.assertEqual(data['scored_positions'],0)
        self.assertEqual(data['sites'],[])
        root='/api/proteins/P00533/structure/predictor-extrema'
        self.assertEqual(self.client.get(root,params={'field':'bad"SQL'}).status_code,422)
        self.assertEqual(self.client.get('/api/proteins/UNKNOWN/structure/predictor-extrema').status_code,404)


if __name__=='__main__':
    unittest.main()
