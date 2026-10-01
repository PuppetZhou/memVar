"""Regression checks for the PostgreSQL API semantics DuckDB must preserve."""
import concurrent.futures
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import duckdb

from Web.src.api.db import DatabaseConfigurationError, DuckDBEngine
from Web.src.api.duckdb_sql import translate


class DuckDBQueryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'catalog.duckdb'
        with duckdb.connect(str(self.path)) as conn:
            conn.execute('CREATE TABLE t (id INTEGER, payload JSON, scores DOUBLE[])')
            conn.execute("INSERT INTO t VALUES (1, '{\"names\":[\"A\",\"B\"],\"contexts\":[{\"accession\":\"P1\",\"extra\":0}],\"values\":[\"0\",null,\"NA\"]}', [0,NULL,-2]), (2, NULL, [])")
        with patch.dict(os.environ, {'MEMVAR_DUCKDB_PATH': str(self.path)}):
            self.engine = DuckDBEngine()

    def tearDown(self):
        self.engine.dispose()
        self.tmp.cleanup()

    def query(self, sql, params=None):
        return self.engine.query(sql, params or {})

    def test_json_values_types_and_context_membership(self):
        rows = self.query("SELECT payload AS details,payload->'values'->>0 AS zero,payload->'values'->>1 AS missing FROM t WHERE payload->'contexts' @> CAST(:context AS jsonb)", {'context': '[{"accession":"P1"}]', 'unused': 1})
        self.assertEqual(rows[0]['zero'], '0')
        self.assertIsNone(rows[0]['missing'])
        self.assertEqual(rows[0]['details']['values'], ['0', None, 'NA'])
        self.assertEqual(self.query("SELECT id FROM t WHERE payload->'names' ? :name", {'name': 'B'}), [{'id': 1}])

    def test_json_aggregate_filter_order_null_and_empty(self):
        sql = "SELECT jsonb_agg(jsonb_build_object('id',id,'value',payload) ORDER BY id DESC) FILTER(WHERE id>0) result FROM t"
        result = self.query(sql)[0]['result']
        self.assertEqual([r['id'] for r in result], [2, 1])
        self.assertIsNone(result[0]['value'])
        self.assertIsNone(self.query(sql + ' WHERE false')[0]['result'])
        self.assertEqual(self.query("SELECT jsonb_object(ARRAY['null','zero']::text[],ARRAY[NULL,'0']::text[]) result")[0]['result'], {'null': None, 'zero': '0'})

    def test_lateral_json_and_array_ordinality(self):
        self.assertEqual(self.query('SELECT id::integer FROM t ORDER BY id'), [{'id': 1}, {'id': 2}])
        rows = self.query("SELECT c->>'accession' accession FROM t CROSS JOIN LATERAL jsonb_array_elements(payload->'contexts') c WHERE c->>'accession'=:accession", {'accession':'P1'})
        self.assertEqual(rows, [{'accession': 'P1'}])
        self.assertEqual(self.query('SELECT s.position::integer position,s.score FROM t CROSS JOIN LATERAL unnest(scores) WITH ORDINALITY s(score,position) WHERE id=1 ORDER BY position'), [{'position':1,'score':0.0},{'position':2,'score':None},{'position':3,'score':-2.0}])

    def test_any_empty_and_null_and_postgres_null_order(self):
        self.assertEqual(self.query('SELECT id FROM t WHERE id=ANY(:ids)', {'ids': []}), [])
        self.assertEqual(self.query('SELECT id FROM t WHERE id=ANY(:ids)', {'ids': [None, 2]}), [{'id':2}])
        self.assertEqual(self.query('SELECT payload->>\'absent\' absent,id FROM t ORDER BY payload DESC,id')[0]['id'], 2)

    def test_postgres_like_escape_default(self):
        self.assertEqual(self.query("SELECT 'a_b' ILIKE :pattern AS matches", {'pattern': '%a\\_b%'}), [{'matches': True}])
        self.assertEqual(self.query("SELECT 'acb' ILIKE :pattern AS matches", {'pattern': '%a\\_b%'}), [{'matches': False}])

    def test_json_table_explicit_column_alias(self):
        result = self.query("SELECT x.value->>'accession' accession FROM t CROSS JOIN LATERAL jsonb_array_elements(payload->'contexts') x(value) WHERE x.value->>'accession'='P1'")
        self.assertEqual(result, [{'accession': 'P1'}])
        result = self.query("SELECT x.value->>'accession' accession FROM t, jsonb_array_elements(payload->'contexts') x(value) WHERE x.value->>'accession'='P1'")
        self.assertEqual(result, [{'accession': 'P1'}])

    def test_libc_text_and_distinct_array_order(self):
        sql = "SELECT value FROM (VALUES ('ABC-family'),('ABC transporter'),('a'),('B'),(NULL)) t(value) ORDER BY value"
        self.assertEqual([r['value'] for r in self.query(sql)], ['a','ABC-family','ABC transporter','B',None])
        sql = "SELECT array_agg(DISTINCT value ORDER BY value) FILTER(WHERE value IS NOT NULL) items FROM (VALUES ('ABC-family'),('ABC transporter'),('a'),('B'),(NULL)) t(value)"
        self.assertEqual(self.query(sql)[0]['items'], ['a','ABC-family','ABC transporter','B'])

    def test_distinct_jsonb_aggregate_implicit_sort(self):
        result = self.query("SELECT jsonb_agg(DISTINCT jsonb_build_object('x',value)) items FROM (VALUES ('B'),(NULL),('a'),('B')) t(value)")[0]['items']
        self.assertEqual(result, [{'x': None}, {'x': 'a'}, {'x': 'B'}])

    def test_ordered_set_quantile_keeps_numeric_measure(self):
        result = self.query("SELECT percentile_cont(ARRAY[0.25,0.5,0.75]) WITHIN GROUP (ORDER BY value) FILTER(WHERE value>=0) quartiles FROM (VALUES (0.0::double precision),(1.0::double precision),(2.0::double precision)) t(value)")[0]['quartiles']
        self.assertEqual(result, [0.5, 1.0, 1.5])

    def test_exists_barrier_removal_preserves_truth(self):
        self.assertEqual(self.query('SELECT EXISTS(SELECT 1 FROM t LIMIT 1 OFFSET 0) available'), [{'available':True}])
        self.assertNotIn('LIMIT', translate('SELECT EXISTS(SELECT 1 FROM t LIMIT 1 OFFSET 0) available'))
        self.assertEqual(self.query('SELECT EXISTS(SELECT 1 FROM t LIMIT 0 OFFSET 0) available'), [{'available':False}])
        self.assertIn('LIMIT 0', translate('SELECT EXISTS(SELECT 1 FROM t LIMIT 0 OFFSET 0) available'))
        self.assertEqual(self.query('SELECT EXISTS(SELECT 1 FROM t LIMIT 1 OFFSET 2) available'), [{'available':False}])
        self.assertIn('OFFSET 2', translate('SELECT EXISTS(SELECT 1 FROM t LIMIT 1 OFFSET 2) available'))

    def test_row_local_any_and_empty_source_array(self):
        sql = "SELECT :value=ANY(string_to_array(:source,'&')) matched"
        for source,value,expected in [('a&b','a',True),('a&b','c',False),('a&b',None,None),('',None,False),('','',False),(None,'a',None)]:
            self.assertEqual(self.query(sql, {'source':source,'value':value}), [{'matched':expected}])

    def test_source_lookup_preserves_all_link_associations(self):
        from Web.src.api.variant_support import duckdb_source_rows
        links=[{'variant_id':'v1','record_id':'r1','alt_index':1},
               {'variant_id':'v1','record_id':'r1','alt_index':2},
               {'variant_id':'v2','record_id':'r1','alt_index':1},
               {'variant_id':'v1','record_id':'r2','alt_index':1}]
        def read(sql,params):
            if 'variant_source_link' in sql:
                return links
            key=params['record_id']
            return [{'record_id':key,'source':'ClinVar' if key=='r1' else 'COSMIC','native_id':key}]
        with patch('Web.src.api.variant_support.query',side_effect=read) as queries, patch('Web.src.api.variant_support.engine') as current:
            current.return_value.source_record_files.return_value = None
            rows=duckdb_source_rows(['v1','v2'],'r.native_id',['ClinVar','COSMIC'])
        self.assertEqual(len(rows),4)
        self.assertEqual([row['alt_index'] for row in rows if row['variant_id']=='v1' and row['record_id']=='r1'],[1,2])
        self.assertEqual(queries.call_count,3)

    def test_source_file_locator_keeps_overlap_and_unknown_bounds(self):
        metadata={'format_version':1,'snapshot_id':'fixture','rows':3,'relation':'web_variant.variant_source_record','key':'record_id',
            'files':[{'path':'a.parquet','min_record_id':'a','max_record_id':'z'},
                     {'path':'b.parquet','min_record_id':'m','max_record_id':'t'},
                     {'path':'c.parquet','min_record_id':None,'max_record_id':None}]}
        (self.path.parent/'source-record-files.json').write_text(json.dumps(metadata))
        (self.path.parent/'manifest.json').write_text(json.dumps({'snapshot_id':'fixture','objects':[{'schema':'web_variant','name':'variant_source_record','rows':3}]}))
        self.assertEqual(self.engine.source_record_files('r'), [str(self.path.parent/name) for name in ['a.parquet','b.parquet','c.parquet']])
        self.assertEqual(self.engine.source_record_files('zz'), [str(self.path.parent/'c.parquet')])

    def test_float4_shortest_expression_and_arrays(self):
        result = self.query('SELECT 0.1::real scalar, ARRAY[0.1::real,NULL,-2::real] AS "values"')[0]
        self.assertEqual(result, {'scalar': 0.1, 'values': [0.1, None, -2.0]})

    def test_source_file_locator_rejects_a_different_snapshot(self):
        locator={'format_version':1,'snapshot_id':'fixture','rows':3,
                 'relation':'web_variant.variant_source_record','key':'record_id','files':[]}
        (self.path.parent/'source-record-files.json').write_text(json.dumps(locator))
        for snapshot_id,rows in [('other',3),('fixture',4)]:
            (self.path.parent/'manifest.json').write_text(json.dumps({
                'snapshot_id':snapshot_id,'objects':[{'schema':'web_variant',
                'name':'variant_source_record','rows':rows}]}))
            with self.assertRaises(DatabaseConfigurationError):
                self.engine.source_record_files('r')

    def test_concurrent_requests_have_independent_cursors(self):
        def run(n):
            return self.query('SELECT :n AS value,range(100) AS values', {'n': n})[0]['value']
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(list(pool.map(run, range(32))), list(range(32)))


if __name__ == '__main__':
    unittest.main()
