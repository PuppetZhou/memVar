"""Current HGNC identities and PostgreSQL catalog, with native reference HDF5 reads."""
from __future__ import annotations
from collections import defaultdict
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import h5py
import numpy as np
from fastapi import APIRouter, HTTPException, Query
import yaml
from .core import get_protein
from .db import one, query

router = APIRouter(prefix='/api/proteins', tags=['expression predictions'])
WEB = Path(__file__).resolve().parents[2]
COORDINATES = '0-based half-open; UI labels are 1-based closed'


@lru_cache(maxsize=1)
def configuration():
    return yaml.safe_load((WEB / 'config/alphagenome.yaml').read_text())


def asset_root():
    return Path(os.environ.get('MEMVAR_ALPHAGENOME_REFERENCE_ROOT', configuration()['reference_root'])).resolve()


def manifest():
    row = one('SELECT data FROM web_alphagenome.manifest WHERE id')
    if not row or row['data']['schema_version'] != 2:
        raise HTTPException(503, 'AlphaGenome reference catalog is unavailable.')
    data = row['data']
    if (data['source_run_id'] != configuration()['source_run_id'] or
            data['checkpoint_revision'] != configuration()['checkpoint_revision']):
        raise HTTPException(503, 'AlphaGenome catalog and configured reference snapshot differ.')
    return data


def candidates(accession):
    protein = get_protein(accession)
    genes = query('''SELECT g.* FROM web_alphagenome.genes g
        JOIN web_alphagenome.protein_gene p USING(hgnc_id)
        WHERE p.accession=:accession AND g.hgnc_id=ANY(:hgnc_ids)
        ORDER BY g.hgnc_id''', {'accession': protein['accession'], 'hgnc_ids': protein['hgnc_ids']})
    for gene in genes:
        gene.update(gene_start_1based=int(gene['start']) if gene['start'] is not None else None,
                    gene_end_1based_inclusive=int(gene['end']) if gene['end'] is not None else None,
                    gene_strand=gene['strand'], chromosome=('chr' + gene['chrom']) if gene['chrom'] else None)
    return genes


WINDOW_COLUMNS = '''*,window_start AS window_start_0based,window_end AS window_end_0based,
    core_start AS core_start_0based,core_end AS core_end_0based'''


def get_context(accession: str, gene: str, tile: str) -> tuple[dict, dict]:
    """Authorize a single source window against both frozen and current HGNC identity."""
    selected = next((g for g in candidates(accession) if g['ensembl_gene_id'] == gene), None)
    if selected is None:
        raise HTTPException(404, 'This prediction gene is not linked to the current protein identity.')
    window = one(f'''SELECT {WINDOW_COLUMNS} FROM web_alphagenome.windows
        WHERE hgnc_id=:hgnc AND tile_id=:tile''', {'hgnc': selected['hgnc_id'], 'tile': tile})
    if not window:
        raise HTTPException(404, 'Prediction window is unavailable for this gene.')
    return selected, window


def viewport(window, start, end):
    low, high = window['window_start_0based'], window['window_end_0based']
    start = low if start is None else start
    end = high if end is None else end
    if start < low or end > high or start >= end:
        raise HTTPException(422, 'Viewport must be a nonempty interval within the selected model window.')
    return start, end


def safe_asset(relative):
    root = asset_root()
    path = (root / relative).resolve()
    if not path.is_relative_to(root / 'tiles') or not path.is_file():
        raise HTTPException(503, 'AlphaGenome reference file is unavailable.')
    return path


def track_public(row):
    return {k: v for k, v in row.items() if k not in ('source_column_index', 'metadata_json')}


def finite(values):
    """JSON cannot represent NaN/Infinity; unavailable values must never become zero."""
    return [float(v) if math.isfinite(float(v)) else None for v in np.asarray(values).ravel()]


def boundaries(length, bins):
    return np.linspace(0, length, min(length, bins) + 1, dtype=np.int64)


def aggregate_signal(values, bins):
    edges = boundaries(len(values), bins)
    values = np.asarray(values, dtype=np.float64)
    means = np.add.reduceat(values, edges[:-1]) / np.diff(edges)
    maximum = np.maximum.reduceat(values, edges[:-1])
    return edges, means, maximum


def read_signal(group, index, start, end, bins):
    resolution = int(group.attrs['resolution'])
    origin = int(group.attrs['interval_start'])
    first = (start - origin) // resolution
    last = (end - origin + resolution - 1) // resolution
    values = group['values'][first:last, index]
    edges, means, maxima = aggregate_signal(values, bins)
    coordinates = origin + (first + edges) * resolution
    return dict(kind='signal', start=int(coordinates[0]), end=int(coordinates[-1]), bins=len(means),
                bin_width=float((coordinates[-1] - coordinates[0]) / len(means)),
                bin_edges=coordinates.tolist(), mean=finite(means), maximum=finite(maxima),
                source_resolution_bp=resolution,
                aggregation='native' if len(values) == len(means) else 'mean_and_maximum',
                retention='Every native position in the viewport contributes to a bin; maximum preserves peaks.')


def read_contacts(group, index, start, end, bins):
    resolution = int(group.attrs['resolution'])
    origin = int(group.attrs['interval_start'])
    first = (start - origin) // resolution
    last = (end - origin + resolution - 1) // resolution
    values = np.asarray(group['values'][first:last, first:last, index], dtype=np.float64)
    edges = boundaries(len(values), min(512, bins))
    widths = np.diff(edges)
    sums = np.add.reduceat(np.add.reduceat(values, edges[:-1], axis=0), edges[:-1], axis=1)
    means = sums / (widths[:, None] * widths[None, :])
    maxima = np.maximum.reduceat(np.maximum.reduceat(values, edges[:-1], axis=0), edges[:-1], axis=1)
    coordinates = origin + (first + edges) * resolution
    return dict(kind='contacts', start=int(coordinates[0]), end=int(coordinates[-1]), size=len(means),
                values=finite(means), maximum=finite(maxima) if len(values) != len(means) else None,
                bin_edges=coordinates.tolist(),
                bin_width=float((coordinates[-1] - coordinates[0]) / len(means)),
                source_resolution_bp=resolution,
                aggregation='native' if len(values) == len(means) else 'mean_and_maximum',
                retention='Two-dimensional matrix within one model window; windows are never merged.')


def read_junctions(group, index, start, end, offset, limit):
    starts, ends = group['start'][:], group['end'][:]
    matched = np.flatnonzero((starts < end) & (ends > start))
    indices = matched[offset:offset + limit]
    # Reading one complete track avoids thousands of random HDF5 point selections.
    values = group['values'][:, index]
    strands = group['strand'][:]
    items = [dict(source_event_index=int(i), rank=offset + j + 1,
                  chromosome=str(group.attrs['chromosome']), start_0based=int(starts[i]),
                  end_0based=int(ends[i]), strand=strands[i].decode(),
                  value=float(values[i]) if np.isfinite(values[i]) else None) for j, i in enumerate(indices)]
    return dict(kind='junctions', items=items, total=len(matched), offset=offset, limit=limit,
                has_more=offset + len(items) < len(matched), source_resolution_bp=None,
                retention='All overlapping source events, including zero values, in original event order; paginated without score filtering.')


@router.get('/{accession}/expression/alphagenome')
def summary(accession: str):
    info = manifest()
    genes = candidates(accession)
    for gene in genes:
        windows = query(f'SELECT {WINDOW_COLUMNS} FROM web_alphagenome.windows WHERE hgnc_id=:hgnc ORDER BY tile_index',
                        {'hgnc': gene['hgnc_id']})
        gene['tiles'] = [{k: v for k, v in row.items() if k != 'relative_path'} for row in windows]
        gene['available'] = bool(windows)
    tracks = [track_public(t) for t in query('SELECT * FROM web_alphagenome.tracks ORDER BY modality,source_column_index')]
    by_sample = defaultdict(list)
    for track in tracks:
        if track['biosample_key']:
            by_sample[track['biosample_key']].append(track)
    biosamples = [dict(biosample_key=key, ontology_curie=key,
                      biosample_name=items[0]['biosample_name'],
                      biosample_names=sorted({t['biosample_name'] for t in items}),
                      biosample_type=items[0]['biosample_type'],
                      modalities=sorted({t['modality'] for t in items}), track_count=len(items))
                 for key, items in by_sample.items()]
    biosamples.sort(key=lambda b: (b['biosample_name'].lower(), b['biosample_key']))
    return dict(genes=genes, tracks=tracks, biosamples=biosamples,
                shared_modalities=sorted({t['modality'] for t in tracks if t['shared']}),
                available=any(g['available'] for g in genes), snapshot=info['source_run_id'],
                source_finished_at=info['source_finished_at'], assembly=info['assembly'],
                prediction_kind=info['prediction_kind'], model_version=info['model_version'],
                checkpoint_revision=info['checkpoint_revision'], levels=[256, 1024, 4096],
                missing_modalities=[], junction_limit_per_track=None,
                mapping='Frozen foundation protein–HGNC link checked against current PostgreSQL HGNC identity',
                coordinate_system=COORDINATES,
                note='Reference-sequence predictions; distinct from measured expression and AVI variant scores. '
                     'Signals retain native source resolution; mean and maximum bins are computed only for display. '
                     'Overlapping model windows remain separate predictions.')


@router.get('/{accession}/expression/alphagenome/cds')
def mane_cds(accession: str, gene: str = Query(pattern=r'^ENSG[0-9]{11}$')):
    selected = next((g for g in candidates(accession) if g['ensembl_gene_id'] == gene), None)
    if selected is None:
        raise HTTPException(404, 'This gene is not linked to the current protein identity.')
    row = one('SELECT model FROM web_mane.gene_cds WHERE gene_id=:id AND ensembl_gene_id=:gene',
              {'id': selected['hgnc_id'], 'gene': gene})
    return row['model'] if row else dict(status='not_available', segments=[], transcript_id=None)


@router.get('/{accession}/expression/alphagenome/track')
def track(accession: str, gene: str = Query(pattern=r'^ENSG[0-9]{11}$'),
          tile: str = Query(pattern=r'^HGNC_[0-9]+_tile[0-9]{3}$'),
          track_id: str = Query(min_length=1, max_length=80),
          bins: int = Query(1024, ge=1, le=4096), start: int | None = Query(None, ge=0),
          end: int | None = Query(None, ge=1), offset: int = Query(0, ge=0),
          limit: int = Query(1000, ge=1, le=10000)):
    info = manifest()
    _, window = get_context(accession, gene, tile)
    start, end = viewport(window, start, end)
    selected = one('SELECT * FROM web_alphagenome.tracks WHERE track_id=:track', {'track': track_id})
    if selected is None:
        raise HTTPException(404, 'Prediction track is unavailable.')
    path = safe_asset(window['relative_path'])
    result = dict(track=track_public(selected), gene=gene, tile=tile, assembly=info['assembly'],
                  snapshot=info['source_run_id'], chromosome=window['chromosome'], start=start, end=end,
                  requested_start=start, requested_end=end, coordinate_system=COORDINATES,
                  model_version=info['model_version'], checkpoint_revision=info['checkpoint_revision'])
    try:
        with h5py.File(path, 'r') as handle:
            if (not handle.attrs.get('complete') or
                    handle.attrs.get('checkpoint_revision') != info['checkpoint_revision'] or
                    handle.attrs.get('prediction_backend') != info['backend'] or
                    json.loads(handle.attrs['tile'])['tile_id'] != tile):
                raise ValueError('Reference snapshot identity mismatch')
            group = handle[selected['modality']]
            if (group.attrs['chromosome'] != window['chromosome'] or
                    int(group.attrs['interval_start']) != window['window_start_0based'] or
                    int(group.attrs['interval_end']) != window['window_end_0based']):
                raise ValueError('Reference interval mismatch')
            index = selected['source_column_index']
            if selected['modality'] == 'splice_junctions':
                payload = read_junctions(group, index, start, end, offset, limit)
            elif selected['modality'] == 'contact_maps':
                payload = read_contacts(group, index, start, end, bins)
            else:
                payload = read_signal(group, index, start, end, bins)
            result.update(payload, source_dtype=str(group['values'].dtype))
    except (OSError, KeyError, ValueError, IndexError):
        raise HTTPException(503, 'AlphaGenome native reference data could not be read.') from None
    return result
