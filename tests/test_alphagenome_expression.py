"""Native reference-window access, source identity, and lossless viewport semantics."""
import json
import math
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import h5py
import numpy as np
from fastapi.testclient import TestClient
from Web.src.api.alphagenome import (aggregate_signal, asset_root, finite, read_contacts,
    read_junctions, read_signal, viewport, retained_window, validate_retained_group, manifest)
from Web.src.api.db import one
from Web.src.api.main import app


class NativeArrayTests(unittest.TestCase):
    def test_manifest_binds_model_and_retained_storage_configuration(self):
        source={'schema_version':2,'source_run_id':'original','checkpoint_revision':'checkpoint'}
        config={'source_run_id':'original','checkpoint_revision':'checkpoint'}
        with patch('Web.src.api.alphagenome.one',return_value={'data':source}), patch('Web.src.api.alphagenome.configuration',return_value=config):
            self.assertEqual(manifest(),source)
            source.update(crop_run_id='crop',retention_flank_bp=10000)
            with self.assertRaises(Exception) as error:
                manifest()
            self.assertEqual(error.exception.status_code,503)
            config.update(crop_run_id='crop',retention_flank_bp=10000)
            self.assertEqual(manifest(),source)
            config['retention_flank_bp']=1000
            with self.assertRaises(Exception) as error:
                manifest()
            self.assertEqual(error.exception.status_code,503)

    def test_retained_native_alignment_offsets_and_original_event_indices(self):
        window=retained_window({'window_start_0based':1000,'window_end_0based':2024,
                                'retention_start':1130,'retention_end':1510,'chromosome':'chr1',
                                'source_run_id':'original','crop_run_id':'crop'})
        self.assertEqual(viewport(window,None,None),(1130,1510))
        with self.assertRaises(Exception) as error:
            viewport(window,1129,1510)
        self.assertEqual(error.exception.status_code,422)
        with tempfile.TemporaryDirectory() as folder, h5py.File(Path(folder)/'crop.h5','w') as handle:
            handle.attrs.update(retention_start=1130,retention_end=1510,crop_run_id='crop',source_run_id='original',retention_flank_bp=10000)
            group=handle.create_group('signal')
            group.attrs.update(chromosome='chr1',resolution=128,interval_start=1128,interval_end=1512)
            group.create_dataset('values',data=np.array([1.,0.,3.])[:,None])
            validate_retained_group(handle,group,window,'rna_seq',{'crop_run_id':'crop','source_run_id':'original','retention_flank_bp':10000})
            result=read_signal(group,0,1130,1510,100)
            self.assertEqual(result['mean'],[1.,0.,3.])
            self.assertEqual(result['bin_edges'],[1128,1256,1384,1512])
            full=handle.create_group('full')
            full.attrs.update(resolution=128,interval_start=1000)
            full.create_dataset('values',data=np.array([99.,1.,0.,3.,99.,99.,99.,99.])[:,None])
            self.assertEqual(read_signal(full,0,1130,1510,100),result)
            matrix=np.arange(64).reshape(8,8)
            contacts=handle.create_group('contacts')
            contacts.attrs.update(chromosome='chr1',resolution=128,interval_start=1128,interval_end=1512)
            contacts.create_dataset('values',data=matrix[1:4,1:4,None])
            full_contacts=handle.create_group('full_contacts')
            full_contacts.attrs.update(resolution=128,interval_start=1000)
            full_contacts.create_dataset('values',data=matrix[...,None])
            validate_retained_group(handle,contacts,window,'contact_maps',{'crop_run_id':'crop','source_run_id':'original','retention_flank_bp':10000})
            self.assertEqual(read_contacts(contacts,0,1130,1510,2),read_contacts(full_contacts,0,1130,1510,2))
            with self.assertRaises(ValueError):
                validate_retained_group(handle,group,window,'rna_seq',{'crop_run_id':'different','source_run_id':'original','retention_flank_bp':10000})
            group.attrs['interval_start']=1000
            with self.assertRaises(ValueError):
                validate_retained_group(handle,group,window,'rna_seq',{'crop_run_id':'crop','source_run_id':'original','retention_flank_bp':10000})
            junctions=handle.create_group('junctions')
            junctions.attrs.update(chromosome='chr1',interval_start=1130,interval_end=1510)
            for name,data in [('start',[1100,1400]),('end',[1200,1600]),
                              ('strand',np.array(['+','-'],dtype='S1')),
                              ('source_event_index',[17,93]),('values',np.array([0.,-1.])[:,None])]:
                junctions.create_dataset(name,data=data)
            validate_retained_group(handle,junctions,window,'splice_junctions',{'crop_run_id':'crop','source_run_id':'original','retention_flank_bp':10000})
            events=read_junctions(junctions,0,1130,1510,0,100)['items']
            self.assertEqual([e['source_event_index'] for e in events],[17,93])
            self.assertEqual([e['value'] for e in events],[0.,-1.])
            self.assertEqual(events[0]['start_0based'],1100)

    def test_unequal_bins_preserve_every_value_and_peak(self):
        edges, mean, maximum = aggregate_signal(np.array([0., 1., 2., 3., 10.]), 2)
        self.assertEqual(edges.tolist(), [0, 2, 5])
        self.assertEqual(mean.tolist(), [.5, 5.])
        self.assertEqual(maximum.tolist(), [1., 10.])
        self.assertEqual(finite([0, math.nan, math.inf, -2]), [0, None, None, -2])

    def test_native_and_contact_boundaries_and_all_junction_values(self):
        with tempfile.TemporaryDirectory() as folder:
            with h5py.File(Path(folder) / 'native.h5', 'w') as handle:
                signal = handle.create_group('signal')
                signal.attrs.update(resolution=128, interval_start=1000)
                signal.create_dataset('values', data=np.arange(8).reshape(8, 1))
                result = read_signal(signal, 0, 1001, 1385, 100)
                self.assertEqual((result['start'], result['end']), (1000, 1512))
                self.assertEqual(result['bin_edges'], [1000, 1128, 1256, 1384, 1512])
                self.assertEqual(result['mean'], [0, 1, 2, 3])
                contacts = handle.create_group('contact')
                contacts.attrs.update(resolution=2048, interval_start=1000)
                matrix = np.arange(16).reshape(4, 4) - 8
                contacts.create_dataset('values', data=matrix[..., None])
                result = read_contacts(contacts, 0, 1001, 7145, 2)
                self.assertEqual(result['bin_edges'], [1000, 5096, 9192])
                self.assertEqual(result['values'], [-5.5, -3.5, 2.5, 4.5])
                self.assertEqual(result['maximum'], [-3, -1, 5, 7])
                junctions = handle.create_group('junctions')
                junctions.attrs['chromosome'] = 'chr1'
                junctions.create_dataset('start', data=[10, 20, 30, 100])
                junctions.create_dataset('end', data=[40, 50, 60, 150])
                junctions.create_dataset('strand', data=np.array(['+', '-', '+', '-'], dtype='S1'))
                junctions.create_dataset('values', data=np.array([0., -1., 2., 3.])[:, None])
                first = read_junctions(junctions, 0, 15, 100, 0, 2)
                second = read_junctions(junctions, 0, 15, 100, 2, 2)
                self.assertEqual([row['value'] for row in first['items']], [0, -1])
                self.assertEqual(first['total'], 3)
                self.assertTrue(first['has_more'])
                self.assertEqual(second['items'][0]['source_event_index'], 2)
                self.assertFalse(second['has_more'])

    def test_viewport_does_not_silently_switch_or_merge_windows(self):
        window = {'window_start_0based': 100, 'window_end_0based': 200}
        self.assertEqual(viewport(window, None, None), (100, 200))
        for start, end in [(99, 150), (150, 201), (150, 150), (190, 180)]:
            with self.assertRaises(Exception) as error:
                viewport(window, start, end)
            self.assertEqual(error.exception.status_code, 422)


class AlphaGenomeExpressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not asset_root().is_dir():
            raise unittest.SkipTest('Native reference snapshot is not installed')
        cls.client = TestClient(app)
        cls.base = '/api/proteins/P00533/expression/alphagenome'
        response = cls.client.get(cls.base)
        response.raise_for_status()
        cls.catalog = response.json()
        cls.gene = cls.catalog['genes'][0]['ensembl_gene_id']
        cls.window = cls.catalog['genes'][0]['tiles'][0]
        cls.tile = cls.window['tile_id']
        cls.performance = {}

    def test_catalog_has_all_new_modalities_and_shared_tracks(self):
        self.assertEqual(len(self.catalog['tracks']), 1517)
        self.assertEqual(len(self.catalog['biosamples']), 33)
        self.assertEqual(len({t['modality'] for t in self.catalog['tracks']}), 11)
        shared = [t for t in self.catalog['tracks'] if t['shared']]
        self.assertEqual(len(shared), 4)
        self.assertTrue(all(t['modality'] == 'splice_sites' and t['biosample_key'] is None for t in shared))
        counts = one("SELECT count(*) AS n FROM web_alphagenome.genes WHERE prediction_status<>'eligible'")
        self.assertEqual(counts['n'], 66)

    def test_mane_cds_preserves_exons_and_rejects_unlinked_gene(self):
        response=self.client.get(self.base+'/cds',params={'gene':self.gene})
        self.assertEqual(response.status_code,200)
        model=response.json()
        self.assertEqual(model['transcript_id'],'ENST00000275493.7')
        blocks=[b for b in model['segments'] if b['feature']=='CDS']
        self.assertEqual(len(blocks),28)
        self.assertEqual(sum(b['end_0based']-b['start_0based'] for b in blocks),3630)
        self.assertEqual((blocks[0]['start_0based'],blocks[0]['end_0based']),(55019277,55019365))
        self.assertEqual([b['start_0based'] for b in model['segments'] if b['feature']=='stop_codon'],[55205614])
        invalid=self.client.get(self.base+'/cds',params={'gene':'ENSG00000000000'})
        self.assertEqual(invalid.status_code,404)

    def test_all_modalities_are_readable_at_native_source_resolution(self):
        origin = self.window['window_start_0based']
        for modality in sorted({t['modality'] for t in self.catalog['tracks']}):
            with self.subTest(modality=modality):
                track = next(t for t in self.catalog['tracks'] if t['modality'] == modality)
                started = time.monotonic()
                response = self.client.get(self.base + '/track', params={
                    'gene': self.gene, 'tile': self.tile, 'track_id': track['track_id'],
                    'start': origin + 1001, 'end': origin + 11002, 'bins': 1024, 'limit': 25})
                self.performance[modality] = round(time.monotonic() - started, 4)
                self.assertEqual(response.status_code, 200, response.text[:300])
                data = response.json()
                if data['kind'] == 'signal':
                    self.assertLessEqual(len(data['mean']), 1024)
                    self.assertEqual(len(data['bin_edges']), len(data['mean']) + 1)
                    self.assertTrue(all(a <= b for a, b in zip(data['mean'], data['maximum'])))
                    self.assertLessEqual(data['start'], origin + 1001)
                    self.assertGreaterEqual(data['end'], origin + 11002)
                elif data['kind'] == 'contacts':
                    self.assertEqual(len(data['values']), data['size'] ** 2)
                    self.assertEqual(data['source_resolution_bp'], 2048)
                    self.assertEqual(data['bin_edges'][0], origin)
                else:
                    self.assertLessEqual(len(data['items']), 25)
                    self.assertEqual(data['has_more'], data['total'] > 25)

    def test_exact_native_values_and_junction_pagination(self):
        origin = self.window['window_start_0based']
        params = {'gene': self.gene, 'tile': self.tile, 'track_id': 'rna_seq:000',
                  'start': origin + 11111, 'end': origin + 11119, 'bins': 1024}
        response = self.client.get(self.base + '/track', params=params)
        self.assertEqual(response.status_code, 200)
        with h5py.File(asset_root() / 'tiles' / f'{self.tile}.h5') as handle:
            source = handle['rna_seq']['values'][11111:11119, 0].astype(float).tolist()
            self.assertEqual(response.json()['mean'], source)
            self.assertEqual(response.json()['maximum'], source)
            contacts = self.client.get(self.base + '/track', params={**params,
                'track_id': 'contact_maps:000', 'start': origin + 1000, 'end': origin + 3000}).json()
            self.assertEqual(contacts['values'], handle['contact_maps']['values'][:2, :2, 0].astype(float).ravel().tolist())
            for offset in (0, 3):
                result = self.client.get(self.base + '/track', params={
                    'gene': self.gene, 'tile': self.tile, 'track_id': 'splice_junctions:000',
                    'offset': offset, 'limit': 3}).json()
                self.assertEqual([x['source_event_index'] for x in result['items']], list(range(offset, offset + 3)))
                self.assertEqual([x['value'] for x in result['items']],
                                 handle['splice_junctions']['values'][offset:offset + 3, 0].astype(float).tolist())

    def test_gene_scope_and_invalid_requests(self):
        defaults = {'gene': self.gene, 'tile': self.tile, 'track_id': 'rna_seq:000', 'bins': 256}
        for changed, status in [({'gene': 'ENSG00000000000'}, 404),
                                ({'tile': 'HGNC_0_tile999'}, 404),
                                ({'track_id': "rna_seq:000' OR 1=1"}, 404),
                                ({'bins': 4097}, 422), ({'tile': '../../secret'}, 422),
                                ({'start': self.window['window_start_0based'] - 1}, 422)]:
            response = self.client.get(self.base + '/track', params={**defaults, **changed})
            self.assertEqual(response.status_code, status, response.text[:200])
        with patch('Web.src.api.alphagenome.get_protein', return_value={'accession': 'P00533', 'hgnc_ids': ['HGNC:other']}):
            response = self.client.get(self.base)
            self.assertFalse(response.json()['available'])
            self.assertEqual(response.json()['genes'], [])
            self.assertEqual(self.client.get(self.base + '/track', params=defaults).status_code, 404)

    def test_unavailable_gene_retains_explanation(self):
        candidate = one("""SELECT p.accession FROM web_alphagenome.genes g
            JOIN web_alphagenome.protein_gene p USING(hgnc_id)
            JOIN web.protein_gene c ON c.accession=p.accession AND c.hgnc_id=p.hgnc_id
            WHERE prediction_status='mitochondrial_no_unpadded_1mb_context' LIMIT 1""")
        result = self.client.get(f"/api/proteins/{candidate['accession']}/expression/alphagenome").json()
        self.assertFalse(result['available'])
        self.assertTrue(result['genes'])
        self.assertEqual(result['genes'][0]['prediction_status'], 'mitochondrial_no_unpadded_1mb_context')
        self.assertEqual(result['genes'][0]['tiles'], [])


if __name__ == '__main__':
    unittest.main()
