"""Expression reference predictions: existing downsampled assets, read-only.

PostgreSQL remains the current protein identity authority. The small legacy
catalog is read in place; dense signals never become PostgreSQL row records.
"""
from contextlib import contextmanager
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import struct

import duckdb
from fastapi import APIRouter, HTTPException, Query
import yaml

from .core import get_protein

router = APIRouter(prefix='/api/proteins', tags=['expression predictions'])
WEB = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def asset_root():
    config = yaml.safe_load((WEB / 'config/alphagenome.yaml').read_text())
    return Path(os.environ.get('MEMVAR_ALPHAGENOME_ASSETS', config['assets_path'])).resolve()


@contextmanager
def catalog():
    try:
        connection = duckdb.connect(str(asset_root() / 'alphagenome_catalog.duckdb'), read_only=True,
                                    config={'threads': 1})
    except (OSError, duckdb.Error):
        raise HTTPException(503, 'AlphaGenome display catalog is unavailable.') from None
    try:
        yield connection
    except (OSError, duckdb.Error):
        raise HTTPException(503, 'AlphaGenome display data could not be read. Please retry.') from None
    finally:
        connection.close()


def rows(connection, sql, parameters=None):
    result = connection.execute(sql, parameters or [])
    names = [column[0] for column in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def candidates(connection, accession):
    protein = get_protein(accession)
    # Reuse the historical explicit accession→gene link only when the HGNC
    # identity is also present in the current PostgreSQL protein mapping.
    found = rows(connection, '''SELECT DISTINCT g.* FROM protein_gene_coverage c
        JOIN gene g USING(ensembl_gene_id)
        WHERE c.uniprot_accession=? AND c.has_prediction AND c.display_ready
        ORDER BY g.ensembl_gene_id''', [protein['accession']])
    return [g for g in found if g['hgnc_id'] in protein['hgnc_ids']]


def safe_asset(relative, folder):
    root = asset_root()
    path = (root / str(relative)).resolve()
    if not path.is_relative_to(root / folder) or not path.is_file():
        raise HTTPException(503, 'AlphaGenome display asset is unavailable.')
    return path


def decode(blob, expected):
    if len(blob) != expected * 2:
        raise HTTPException(503, 'AlphaGenome display array has an invalid size.')
    # JSON has no NaN/Infinity. Preserve unavailable values as null, never zero.
    return [value if math.isfinite(value) else None
            for (value,) in struct.iter_unpack('<e', blob)]


@router.get('/{accession}/expression/alphagenome')
def summary(accession: str):
    with catalog() as c:
        genes = candidates(c, accession)
        for gene in genes:
            gene['tiles'] = rows(c, '''SELECT t.* FROM tile t JOIN prepared_tile p
                USING(ensembl_gene_id,tile_id) WHERE t.ensembl_gene_id=? ORDER BY t.tile_index''',
                [gene['ensembl_gene_id']])
        tracks = rows(c, 'SELECT * EXCLUDE(source_column_index) FROM track ORDER BY modality,track_id')
    try:
        manifest = json.loads((asset_root() / 'build_manifest.json').read_text())
        if manifest.get('schema_version') != 1 or manifest.get('prediction_kind') != 'reference_sequence_tracks':
            raise ValueError('Unsupported display snapshot')
    except (OSError, ValueError):
        raise HTTPException(503, 'AlphaGenome display manifest is unavailable or unsupported.') from None
    return {'genes': genes, 'tracks': tracks, 'available': bool(genes),
            'snapshot': manifest['created_utc'], 'assembly': manifest['genome_build'],
            'prediction_kind': manifest['prediction_kind'], 'levels': manifest['pyramid_bins'],
            'missing_modalities': manifest['missing_official_modalities'],
            'junction_limit_per_track': manifest['junction_limit_per_track'],
            'mapping': 'Historical accession–Ensembl link, checked against current HGNC identity',
            'note': 'Reference-sequence predictions, not measured expression or REF/ALT variant effects. '
                    'Downsampled bins preserve mean and maximum, not base-level positions.'}


@router.get('/{accession}/expression/alphagenome/track')
def track(accession: str, gene: str = Query(pattern=r'^ENSG[0-9]{11}$'),
          tile: str = Query(pattern=r'^tile_[0-9]{3}$'),
          track_id: str = Query(min_length=1, max_length=80),
          bins: int = Query(1024)):
    if bins not in (256, 1024, 4096):
        raise HTTPException(422, 'Choose 256, 1024 or 4096 display bins.')
    with catalog() as c:
        if not any(g['ensembl_gene_id'] == gene for g in candidates(c, accession)):
            raise HTTPException(404, 'This prediction gene is not linked to the current protein identity.')
        selected = rows(c, 'SELECT * EXCLUDE(source_column_index) FROM track WHERE track_id=?', [track_id])
        prepared = rows(c, '''SELECT p.*,t.window_start_0based,t.window_end_0based,t.chromosome
            FROM prepared_tile p JOIN tile t USING(ensembl_gene_id,tile_id)
            WHERE p.ensembl_gene_id=? AND p.tile_id=?''', [gene, tile])
        if not selected or not prepared:
            raise HTTPException(404, 'Prediction track or window is unavailable.')
        metadata, bundle = selected[0], prepared[0]
        result = {'track': metadata, 'gene': gene, 'tile': tile, 'assembly': 'GRCh38',
                  'chromosome': bundle['chromosome'],
                  'start': bundle['window_start_0based'], 'end': bundle['window_end_0based'],
                  'coordinate_system': '0-based half-open; UI labels are 1-based closed'}
        modality = metadata['modality']
        if modality == 'splice_junctions':
            path = safe_asset(bundle['junction_relative_path'], 'junctions')
            result.update(kind='junctions', items=rows(c, '''SELECT rank,chromosome,start_0based,end_0based,strand,value
                FROM read_parquet(?) WHERE track_id=? ORDER BY rank''', [str(path), track_id]),
                retention='At most the 200 strongest positive junctions per track and model window.')
        elif modality == 'contact_maps':
            path = safe_asset(bundle['contact_relative_path'], 'contacts')
            data = rows(c, 'SELECT * FROM read_parquet(?) WHERE track_id=?', [str(path), track_id])
            if not data:
                raise HTTPException(404, 'Contact matrix is unavailable.')
            row = data[0]
            size = row['matrix_size']
            result.update(kind='contacts', size=size, values=decode(row['mean_float16_le'], size * size),
                          bin_width=(result['end']-result['start'])/size,
                          source_resolution_bp=row['source_resolution_bp'])
        else:
            path = safe_asset(bundle['signal_relative_path'], 'tracks')
            data = rows(c, 'SELECT * FROM read_parquet(?) WHERE track_id=? AND level_bins=?',
                        [str(path), track_id, bins])
            if not data:
                raise HTTPException(404, 'Signal level is unavailable.')
            row = data[0]
            result.update(kind='signal', bins=bins, bin_width=(result['end']-result['start'])/bins,
                          source_resolution_bp=row['source_resolution_bp'],
                          mean=decode(row['mean_float16_le'], bins), maximum=decode(row['max_float16_le'], bins))
        return result
