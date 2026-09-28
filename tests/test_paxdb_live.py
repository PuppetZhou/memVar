"""Opt-in live PaxDB contract checks against the imported local database."""
import os
import unittest
from fastapi.testclient import TestClient
from Web.src.api.main import app

@unittest.skipUnless(os.environ.get('MEMVAR_TEST_LIVE')=='1','requires imported local PaxDB')
class PaxDbLiveTests(unittest.TestCase):
 def setUp(self):self.client=TestClient(app)
 def get(self,**params):
  r=self.client.get('/api/proteins/P00533/expression/paxdb',params=params)
  self.assertEqual(r.status_code,200);return r.json()
 def test_context_partition_and_no_hidden_fields(self):
  counts=[]
  for kind in ['tissue','cell','fluid','fraction','whole']:
   result=self.get(context_type=kind)
   self.assertEqual(result['taxon_id'],9606);counts.append(result['total'])
   for row in result['items']:
    self.assertFalse(set(row)&{'gene_name','string_external_id','id','filename','weights'})
    self.assertTrue(row['integrated'])
  self.assertEqual(sum(counts),48)
 def test_navigation_and_source_value(self):
  result=self.get(context_type='tissue',organ='KIDNEY')
  self.assertEqual(result['total'],1)
  self.assertEqual(result['items'][0]['abundance'],'3.6')
  self.assertEqual(self.get(context_type='cell',organ='KIDNEY')['total'],0)
 def test_study_pagination_and_validation(self):
  a=self.get(collection='studies',context_type='cell',limit=30)
  b=self.get(collection='studies',context_type='cell',limit=30,offset=30)
  self.assertEqual(a['total'],64)
  self.assertEqual(a['maximum'],b['maximum'])
  self.assertGreaterEqual(a['maximum'],max(float(r['abundance']) for r in a['items']+b['items']))
  self.assertFalse({r['record_key'] for r in a['items']}&{r['record_key'] for r in b['items']})
  self.assertTrue(all(not r['integrated'] for r in a['items']))
  self.assertEqual(self.client.get('/api/proteins/P00533/expression/paxdb',params={'limit':101}).status_code,422)
  self.assertEqual(self.client.get('/api/proteins/P00533/expression/paxdb',params={'context_type':'invalid'}).status_code,422)
if __name__=='__main__':unittest.main()
