"""Small deployment smoke: retained defaults, identities, native bins and bounds.

Run against a separate candidate before changing a live service. This does not
repeat the full scientific value comparison or inspect every HDF5 file.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import duckdb
import requests


def smoke(base_url, accession='P00533', *, catalog_path=None, expected_windows=None,
          expected_crop=None, expected_source=None, extra_accession=None):
    observations=[]
    catalog_counts=None
    if catalog_path:
        with duckdb.connect(str(catalog_path),read_only=True) as db:
            catalog_counts={name:db.execute(f'SELECT count(*) FROM web_alphagenome.{name}').fetchone()[0]
                            for name in ['genes','protein_gene','tracks','windows']}
            info=json.loads(db.execute('SELECT data FROM web_alphagenome.manifest WHERE id').fetchone()[0])
        assert catalog_counts=={name:info['counts'][name] for name in catalog_counts}
        if expected_windows is not None:
            assert catalog_counts['windows']==expected_windows, f"Expected {expected_windows} windows, found {catalog_counts['windows']}"
            if expected_windows==7750:
                assert info.get('crop_status')=='complete', 'The crop catalog is not marked complete'
        if expected_crop:
            assert info['crop_run_id']==expected_crop, 'The catalog crop identity differs'
        if expected_source:
            assert info['source_run_id']==expected_source, 'The catalog model source identity differs'
    def get(path, params=None, status=200):
        response=requests.get(base_url.rstrip('/')+path,params=params,timeout=30)
        assert response.status_code == status, (response.url,response.status_code,response.text[:300])
        observations.append(dict(path=path,status=status,seconds=round(response.elapsed.total_seconds(),4)))
        return response.json()
    health=get('/api/health')
    assert health.get('database') == 'DuckDB',health
    prefix=f'/api/proteins/{accession}/expression/alphagenome'
    catalog=get(prefix)
    if expected_crop:
        assert catalog['storage_snapshot']==expected_crop, 'The running API crop identity differs'
    if expected_source:
        assert catalog['snapshot']==expected_source, 'The running API model source identity differs'
    gene=next(g for g in catalog['genes'] if g['tiles'])
    tile=gene['tiles'][0]
    low,high=tile['retention_start_0based'],tile['retention_end_0based']
    assert tile['window_start_0based'] <= low < high <= tile['window_end_0based']
    assert catalog['storage_snapshot'] != catalog['snapshot']
    common=dict(gene=gene['ensembl_gene_id'],tile=tile['tile_id'],bins=16,limit=3)
    for modality in ['rna_seq','contact_maps']:
        selected=next(t for t in catalog['tracks'] if t['modality']==modality)
        result=get(prefix+'/track',dict(common,track_id=selected['track_id']))
        assert (result['requested_start'],result['requested_end'])==(low,high)
        assert result['storage_snapshot']==catalog['storage_snapshot']
        assert (result['model_window_start_0based'],result['model_window_end_0based'])==(tile['window_start_0based'],tile['window_end_0based'])
        edges=result['bin_edges']
        assert edges[0] <= low < high <= edges[-1]
        assert all(a < b for a,b in zip(edges,edges[1:]))
        if modality=='contact_maps':
            assert len(result['values'])==result['size']**2
        else:
            assert len(result['mean'])==len(result['maximum'])==len(edges)-1
    for start,end in [(low-1,high),(low,high+1)]:
        get(prefix+'/track',dict(common,track_id='rna_seq:000',start=start,end=end),422)
    if extra_accession:
        extra=get(f'/api/proteins/{extra_accession}/expression/alphagenome')
        assert extra['available'], f'No retained windows for non-pilot accession {extra_accession}'
        assert extra['storage_snapshot']==catalog['storage_snapshot']
        assert extra['snapshot']==catalog['snapshot']
        assert any(g['tiles'] for g in extra['genes'])
    return dict(status='passed',base_url=base_url,accession=accession,
                tile=tile['tile_id'],model_snapshot=catalog['snapshot'],
                storage_snapshot=catalog['storage_snapshot'],retention=[low,high],
                catalog_counts=catalog_counts,extra_accession=extra_accession,requests=observations)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base_url')
    parser.add_argument('--accession',default='P00533')
    parser.add_argument('--report',type=Path)
    parser.add_argument('--catalog',type=Path)
    parser.add_argument('--expected-windows',type=int)
    parser.add_argument('--expected-crop')
    parser.add_argument('--expected-source')
    parser.add_argument('--extra-accession',help='Check an available gene absent from the nine-window pilot, e.g. Q9Y663.')
    args=parser.parse_args()
    try:
        result=smoke(args.base_url,args.accession,catalog_path=args.catalog,
                     expected_windows=args.expected_windows,expected_crop=args.expected_crop,
                     expected_source=args.expected_source,extra_accession=args.extra_accession)
    except Exception as error:
        result=dict(status='failed',base_url=args.base_url,error_type=type(error).__name__,error=str(error))
    text=json.dumps(result,indent=2)+'\n'
    if args.report:
        args.report.write_text(text)
    print(text)
    sys.exit(0 if result['status']=='passed' else 1)
