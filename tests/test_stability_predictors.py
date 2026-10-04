"""Check the new selector projection against the active snapshot and identity edges."""
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.stability_predictions import attach_stability, FIELD


class StabilityPredictorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def get(self, path, **params):
        response = self.client.get(path, params=params)
        self.assertEqual(response.status_code, 200, response.text[:300])
        return response.json()

    def test_identity_zero_missing_and_multiple_records_are_preserved(self):
        rows = [dict(variant_id='v',annotation_id=a,gene_id='g',predictions=[{'field':FIELD}]) for a in ('a','b','missing')]
        source = [dict(variant_id='v',annotation_id=a,gene_id='g',prediction_id=i,ddg_pred=score)
                  for a,i,score in [('a',1,0.0),('b',2,-1.2),('b',3,2.4)]]
        with patch('Web.src.api.stability_predictions.stability_records',return_value=source):
            attach_stability(rows,'P00533')
        a,b,missing = [row['predictions'][0] for row in rows]
        self.assertEqual(a['value'],0.0)
        self.assertEqual([r['ddg_pred'] for r in b['records']],[-1.2,2.4])
        self.assertIsNone(b['value'])
        self.assertEqual(missing['records'],[])
        self.assertIsNone(missing['value'])
        self.assertEqual(missing['status'],'no_linked_prediction')

    def test_real_selector_detail_and_original_stability_agree(self):
        data=self.get('/api/proteins/P00533/variants',predictors=FIELD,canonical_start=858,canonical_end=858,limit=100)
        self.assertTrue(data['items'])
        signs=[]
        for row in data['items'][:3]:
            pred=row['predictions'][0]
            detail=self.get('/api/variants/'+row['variant_id'],accession='P00533')
            original=[r for r in detail['ddg'] if r['annotation_id']==row['annotation_id'] and r['gene_id']==row['gene_id']]
            self.assertEqual([r['ddg_pred'] for r in pred['records']],[r['ddg_pred'] for r in original])
            self.assertTrue(all(r['accession']=='P00533' for r in pred['records']))
            self.assertIn('Protein stability',[g['name'] for g in detail['prediction_groups']])
            signs.extend(r['ddg_pred'] for r in original)
        self.assertTrue(any(v<0 for v in signs))
        self.assertTrue(any(v>0 for v in signs))

    def test_catalog_and_selector_counts_agree(self):
        data=self.get('/api/proteins/P00533/variants',predictors='none',limit=1)
        definitions=data['filters']['predictors']
        section=next(s for s in self.get('/api/catalog/statistics')['sections'] if s['id']=='predictors')
        metrics={m['key']:m['value'] for m in section['metrics']}
        self.assertEqual(metrics['fields'],len(definitions))
        self.assertEqual(metrics['tools'],len({p['tool'] for p in definitions}))
        self.assertEqual(next(p for p in definitions if p['field']==FIELD)['scope'],'protein_substitution')

    def test_structure_raw_records_match_selector_and_paginate(self):
        root='/api/proteins/P00533/structure/predictor-records'
        for field in ['AlphaMissense_score','ESM1b_score',FIELD,'alphagenome_avi_raw','alphagenome_avi_phred','alphagenome_splicing']:
            first=self.get(root,field=field,limit=2)
            second=self.get(root,field=field,limit=2,offset=first['next_offset'])
            keys=lambda rows:{(r['variant_id'],r['annotation_id'],r['gene_id'],r['prediction_id']) for r in rows}
            self.assertFalse(keys(first['items']) & keys(second['items']))
            row=first['items'][0]
            detail=self.get('/api/variants/'+row['variant_id'],accession='P00533')
            candidates=[p for g in detail['prediction_groups'] for p in g['items'] if p['field']==field]
            if candidates[0]['scope']!='variant':
                candidates=[p for p in candidates if p['annotation_id']==row['annotation_id'] and p['gene_id']==row['gene_id']]
            self.assertEqual(row['score'],candidates[0]['value'])
            self.assertEqual(row['sequence_id'],'P00533')
        self.assertEqual(self.client.get(root,params={'field':'bad"SQL'}).status_code,422)
        self.assertEqual(self.client.get('/api/proteins/UNKNOWN/structure/predictor-records').status_code,404)


if __name__=='__main__':
    unittest.main()
