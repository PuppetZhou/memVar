"""Collection membership, mutation projection and pagination regressions."""
import unittest
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.db import query


class PpiCollectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client=TestClient(app)
        cls.root='/api/proteins/P00533/ppi'
        response=cls.client.get(cls.root+'/summary')
        response.raise_for_status()
        cls.summary=response.json()
        cls.collections=cls.summary['collections']
        cls.mutation=next(c for c in cls.collections if c['kind']=='intact_mutation')
        cls.cancer=next(c for c in cls.collections if c['source']=='IntAct' and c['context']=='Cancer')

    def get_page(self, **params):
        response=self.client.get(self.root,params=params)
        self.assertEqual(response.status_code,200,response.text[:300])
        return response.json()

    def test_default_full_scope_is_unchanged(self):
        counts=query('''SELECT count(DISTINCT l.record_id) n FROM web_context.ppi_protein_link l
            JOIN web_context.ppi_membership m USING(record_id) JOIN web_context.context_dataset d USING(dataset_id)
            WHERE l.target_accession='P00533' AND d.kind IN ('biogrid_full','intact_full')''')[0]['n']
        self.assertEqual(self.summary['totals']['records'],counts)
        self.assertEqual(len(self.collections),35)
        self.assertTrue(all(r['record_kind']=='interaction' for r in self.get_page(limit=10)['items']))

    def test_context_counts_and_membership_use_same_scope(self):
        for collection in [self.cancer,self.mutation]:
            with self.subTest(collection=collection['context'] or collection['kind']):
                did=collection['dataset_id']
                summary=self.client.get(self.root+'/summary',params={'dataset':did}).json()
                self.assertEqual(summary['totals']['records'],collection['records'])
                expected={r['record_id'] for r in query('''SELECT DISTINCT m.record_id FROM web_context.ppi_membership m
                    JOIN web_context.ppi_protein_link l USING(record_id)
                    WHERE m.dataset_id=:dataset AND l.target_accession='P00533' ''',{'dataset':did})}
                self.assertEqual(len(expected),collection['records'])
                page=self.get_page(dataset=did,limit=10)
                self.assertTrue({r['record_id'] for r in page['items']}<=expected)
                if page['next_cursor']:
                    next_page=self.get_page(dataset=did,limit=10,cursor=page['next_cursor'])
                    self.assertTrue({r['record_id'] for r in next_page['items']}<=expected)
                    self.assertFalse({r['record_id'] for r in page['items']}&{r['record_id'] for r in next_page['items']})

    def test_mutation_source_fields_and_details(self):
        page=self.get_page(dataset=self.mutation['dataset_id'],limit=10)
        for item in page['items']:
            self.assertEqual(item['record_kind'],'mutation')
            self.assertNotIn('MI:',item['interaction_type'])
            raw=query('SELECT details_json FROM web_context.ppi_interaction WHERE record_id=:id',{'id':item['record_id']})[0]['details_json']
            for key,field in [('range','Feature range(s)'),('original','Original sequence'),('resulting','Resulting sequence'),('participants_raw','Interaction participants')]:
                self.assertEqual(item['mutation'][key],raw.get(field))
            self.assertIn('not validated',item['coordinate_status'])
        detail=self.client.get('/api/ppi/'+page['items'][0]['record_id'],params={'accession':'P00533'}).json()
        self.assertTrue(detail['publications'])
        self.assertTrue(detail['fields'])
        self.assertTrue(any(c['kind']=='intact_mutation' for c in detail['collections']))
        self.assertTrue(detail['mapping_statuses'])

    def test_mutation_effect_filter(self):
        did=self.mutation['dataset_id']
        option=next(v for v in self.get_page(dataset=did,limit=1)['filters']['interaction_types'] if v.endswith('mutation disrupting'))
        page=self.get_page(dataset=did,interaction_type=option,limit=10)
        self.assertTrue(page['items'])
        self.assertTrue(all('IntAct: '+r['interaction_type']==option for r in page['items']))
        summary=self.client.get(self.root+'/summary',params={'dataset':did,'interaction_type':option}).json()
        self.assertGreaterEqual(summary['totals']['records'],len(page['items']))
        self.assertEqual(len([g for g in summary['groups'] if g['dimension']=='type']),1)

    def test_invalid_and_empty_collections_and_cursor_scope(self):
        for invalid in ['does-not-exist','hpa:rna_tissue_hpa']:
            self.assertEqual(self.client.get(self.root,params={'dataset':invalid}).status_code,422)
            self.assertEqual(self.client.get(self.root+'/summary',params={'dataset':invalid}).status_code,422)
        empty=next(c for c in self.collections if c['records']==0)
        self.assertEqual(self.get_page(dataset=empty['dataset_id'])['items'],[])
        mutation=self.get_page(dataset=self.mutation['dataset_id'],limit=1)
        self.assertEqual(self.client.get(self.root,params={'dataset':self.cancer['dataset_id'],'cursor':mutation['next_cursor']}).status_code,400)
        self.assertEqual(self.get_page(dataset=self.mutation['dataset_id'],source='BioGRID')['items'],[])

if __name__=='__main__':unittest.main()
