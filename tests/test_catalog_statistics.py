"""Statistics retain source grain, serving snapshot and score-field distinctions."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from Web.src.api.main import app
from Web.src.api.catalog_statistics import STATISTICS


class CatalogStatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.data = json.loads(STATISTICS.read_text())
        cls.sections = {section['id']: section for section in cls.data['sections']}

    def test_active_snapshot_and_safe_public_payload(self):
        response = self.client.get('/api/catalog/statistics')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.data)
        text = response.text
        for private in ['/home/xuyzh/', 'PGPASSWORD', 'password', 'postgresql://', 'data/postgres', 'source_manifest']:
            self.assertNotIn(private, text)
        self.assertEqual({v['module'] for v in self.data['versions']}, {'proteins','variants','context','diseases','interface'})
        for version in self.data['versions']:
            self.assertTrue(version['service_version'])
            for source in version['upstream_versions']:
                self.assertTrue(source['version'])
                self.assertNotRegex(source['version'], r'^20\d{6}_')

    def test_stale_snapshot_is_not_silently_served(self):
        with patch('Web.src.api.catalog_statistics.query', return_value=[{'module':'proteins','version':'different-snapshot'}]):
            response = self.client.get('/api/catalog/statistics')
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('sections', response.json())

    def test_counts_and_grains_match_validated_import(self):
        tables = json.loads((STATISTICS.parent / 'postgresql_variant_import.json').read_text())['tables']
        metrics = {m['key']:m['value'] for m in self.sections['variants']['metrics']}
        self.assertEqual(metrics['variants'], tables['variant'])
        self.assertEqual(metrics['consequences'], tables['variant_consequence'])
        p = {m['key']:m['value'] for m in self.sections['predictors']['metrics']}
        self.assertEqual(p['fields'], p['dbnsfp_fields'] + p['alphagenome_fields'])
        self.assertLess(p['tools'], p['fields'])
        tools = next(b for b in self.sections['predictors']['breakdowns'] if b['key']=='tools')
        self.assertEqual(len(tools['rows']),p['tools'])
        self.assertEqual(sum(row['value'] for row in tools['rows']), p['fields'])
        for section in self.sections.values():
            for group in section['breakdowns']:
                self.assertTrue(group['note'])
                self.assertTrue(group['unit'])

    def test_source_registry_and_real_class_links(self):
        sources = self.data['sources']
        self.assertEqual(len({s['id'] for s in sources}),len(sources))
        for source in sources:
            if 'version' in source:
                self.assertTrue(source['version'])
        self.assertNotIn('version', next(s for s in sources if s['id']=='intact'))
        classes = next(b for b in self.sections['proteins']['breakdowns'] if b['key']=='classes')
        for row in classes['rows']:
            self.assertTrue(row['href'].startswith('/search?membrane_class='))
        source_groups = next(b for b in self.sections['proteins']['breakdowns'] if b['key']=='sources')
        self.assertTrue(all('href' not in r for r in source_groups['rows']))


if __name__ == '__main__':
    unittest.main()
