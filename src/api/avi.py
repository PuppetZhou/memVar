"""Gene-scoped AVI scores and unchanged source feature contributions."""
from __future__ import annotations

import base64
import json

from fastapi import APIRouter, HTTPException, Query

from .core import get_protein
from .db import one, query

router = APIRouter(prefix='/api', tags=['AlphaGenome AVI'])

# Display groups describe the input features; no group scores are calculated.
FEATURES = [
    ('merged_splicing', 'Splicing', 'splicing'),
    ('max_abs_atac', 'ATAC', 'accessibility'),
    ('max_abs_contact_maps', 'Contact maps', 'contacts'),
    ('max_abs_dnase', 'DNase', 'accessibility'),
    ('max_abs_chip_tf', 'Transcription factor ChIP', 'chip'),
    ('max_abs_chip_histone', 'Histone ChIP', 'chip'),
    ('max_abs_cage', 'CAGE', 'transcription'),
    ('max_abs_procap', 'PRO-cap', 'transcription'),
    ('max_abs_rna_seq', 'RNA-seq', 'transcription'),
    ('max_abs_polyadenylation', 'Polyadenylation', 'transcription'),
    ('alphamissense', 'AlphaMissense', 'protein'),
    ('cactus_241_way', 'Cactus 241-way', 'conservation'),
    ('protein_termination', 'Protein termination', 'protein'),
    ('start_lost', 'Start lost', 'protein'),
    ('stop_lost', 'Stop lost', 'protein'),
    ('phastcons_470_way', 'PhastCons 470-way', 'conservation'),
    ('is_insertion', 'Insertion indicator', 'variant_type'),
    ('is_deletion', 'Deletion indicator', 'variant_type'),
]


def read_cursor(value: str | None, context: list) -> tuple[int, str] | None:
    if not value:
        return None
    try:
        if len(value) > 2048:
            raise ValueError
        decoded = json.loads(base64.urlsafe_b64decode(value.encode()))
        position, variant_id = decoded['after']
        if (decoded['context'] != context or type(position) is not int or position < 1
                or not isinstance(variant_id, str) or len(variant_id) > 100):
            raise ValueError
        return position, variant_id
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise HTTPException(422, 'Invalid AVI cursor for this genomic view.') from None


def write_cursor(row: dict, context: list) -> str:
    return base64.urlsafe_b64encode(json.dumps(
        {'context': context, 'after': [row['position'], row['variant_id']]},
        separators=(',', ':')).encode()).decode()


def feature_contributions(record: dict | None) -> list[dict]:
    return [dict(feature=feature, label=label, group=group,
                 value=record[feature + '_contribution'])
            for feature, label, group in FEATURES] if record else []


@router.get('/proteins/{accession}/expression/alphagenome/avi')
def avi_track(accession: str, gene: str = Query(pattern=r'^ENSG[0-9]{11}$'),
              tile: str = Query(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9_:.-]+$'),
              start: int | None = Query(None, ge=0), end: int | None = Query(None, gt=0),
              limit: int = Query(10000, ge=1, le=20000), cursor: str | None = None,
              include_contributions: bool = True):
    from .alphagenome import get_context
    gene_row, window = get_context(accession, gene, tile)
    start = window['window_start_0based'] if start is None else start
    end = window['window_end_0based'] if end is None else end
    if not window['window_start_0based'] <= start < end <= window['window_end_0based']:
        raise HTTPException(422, 'The AVI viewport must be inside the selected model window.')
    chromosome = str(window['chromosome']).removeprefix('chr')
    context = [accession.upper(), gene, tile, start, end]
    after = read_cursor(cursor, context)
    parameters = dict(gene_id=gene_row['hgnc_id'], chrom=chromosome, start=start, end=end,
                      limit=limit + 1)
    scope = '''FROM web_variant.variant v
        WHERE v.chrom=:chrom AND v.pos>:start AND v.pos<=:end
          AND EXISTS (SELECT 1 FROM web_variant.variant_consequence c
                      WHERE c.variant_id=v.variant_id AND c.gene_id=:gene_id)'''
    # Table presence is checked once per request, together with the existing
    # count; missing attribution never triggers one lookup per variant.
    counted = one('''SELECT count(*) AS n,
        to_regclass('web_avi.attribution') IS NOT NULL AND
        to_regclass('web_avi._build_manifest') IS NOT NULL AS attribution_available
        ''' + scope, parameters)
    total = counted['n']
    available = include_contributions and counted['attribution_available']
    pagination = ''
    if after:
        parameters.update(after_position=after[0], after_id=after[1])
        pagination = ' AND (v.pos,v.variant_id)>(:after_position,:after_id)'
    page_sql = '''SELECT v.variant_id,v.pos AS position,v.ref,v.alt,
        v.alphagenome_avi_raw AS raw,v.alphagenome_avi_phred AS phred,v.avi_status AS status
        ''' + scope + pagination + ' ORDER BY v.pos,v.variant_id LIMIT :limit'
    snapshot = None
    if available:
        columns = ','.join('a.' + feature + '_contribution' for feature, _, _ in FEATURES)
        # Bound the score page before joining the 18 source columns. Values and
        # manifest share this statement's snapshot during an atomic publication.
        # Starting at the manifest retains its identity for an empty score page.
        records = query('WITH page AS MATERIALIZED (' + page_sql + ''')
            SELECT p.*,a.variant_id AS attribution_variant_id,a.avi_attribution_status,
            ''' + columns + ''',m.data_version AS source_snapshot
            FROM (SELECT data_version FROM web_avi._build_manifest LIMIT 1) m
            LEFT JOIN page p ON true
            LEFT JOIN web_avi.attribution a ON a.variant_id=p.variant_id
            ORDER BY p.position,p.variant_id''', parameters)
        snapshot = records[0]['source_snapshot'] if records else None
        if snapshot is None:
            raise HTTPException(503, 'The AVI contribution snapshot is unavailable.')
        records = [row for row in records if row['variant_id'] is not None]
    else:
        records = query(page_sql, parameters)
    has_more = len(records) > limit
    attribution_status = ('available' if available else
                          'not_available' if include_contributions else 'not_requested')
    items = []
    for row in records[:limit]:
        linked = row if available and row['attribution_variant_id'] is not None else None
        items.append({**{key: row[key] for key in ('variant_id', 'position', 'ref', 'alt', 'raw', 'phred', 'status')},
                      'contributions': feature_contributions(linked),
                      'attribution_status': linked['avi_attribution_status'] if linked else
                      ('not_available' if include_contributions else 'not_requested')})
    return dict(kind='avi', items=items, start=start, end=end, chromosome=window['chromosome'],
                total=total, has_more=has_more,
                attribution_status=attribution_status, source_snapshot=snapshot,
                attribution_note=('Original signed feature contributions; missing entries remain null. '
                                  'Their sum is not used to reconstruct AVI raw or PHRED scores.'
                                  if available else 'Feature contributions were not requested.'
                                  if not include_contributions else
                                  'Feature contributions are not installed in this database snapshot.'),
                next_cursor=write_cursor(items[-1], context) if has_more else None,
                scope='Current gene-associated project SNVs', score_scale='AVI PHRED',
                assembly='GRCh38', coordinate_system='Viewport: 0-based half-open; SNV position: 1-based',
                note='Each point is one reference/alternate allele. Unrepresented positions are not zero scores. '
                     'Source feature contributions retain their original sign and missing values; '
                     'their sum is not used to reconstruct AVI raw or PHRED scores.')


@router.get('/variants/{variant_id}/avi')
def avi_detail(variant_id: str, accession: str = ''):
    variant = one('''SELECT variant_id,chrom AS chromosome,pos AS position,ref,alt,
        alphagenome_avi_raw AS raw,alphagenome_avi_phred AS phred,avi_status AS status
        FROM web_variant.variant WHERE variant_id=:id''', {'id': variant_id})
    if not variant:
        raise HTTPException(404, 'Variant not found.')
    if accession:
        protein = get_protein(accession)
        linked = one('''SELECT 1 AS linked FROM web_variant.variant_consequence
            WHERE variant_id=:id AND gene_id=ANY(:genes) LIMIT 1''',
                     {'id': variant_id, 'genes': protein['hgnc_ids']})
        if not linked:
            raise HTTPException(404, 'Variant is not associated with this protein gene.')
    available = one("SELECT to_regclass('web_avi.attribution') IS NOT NULL AS available")['available']
    # Read values and source identity in one statement: a concurrent schema
    # publication must not label an old contribution row with the new snapshot.
    payload = one('''SELECT a.*,m.data_version AS source_snapshot
        FROM web_avi._build_manifest m LEFT JOIN web_avi.attribution a ON a.variant_id=:id
        LIMIT 1''', {'id': variant_id}) if available else None
    record = payload if payload and payload['variant_id'] is not None else None
    contributions = feature_contributions(record)
    return {
        'variant': {**{k: variant[k] for k in ('variant_id', 'chromosome', 'position', 'ref', 'alt')},
                    'assembly': 'GRCh38'},
        'score': {k: variant[k] for k in ('raw', 'phred', 'status')},
        'attribution': {
            'status': record['avi_attribution_status'] if record else 'not_available',
            'source_snapshot': payload['source_snapshot'] if payload else None,
            'contributions': contributions,
            'note': 'Source feature contributions; their sum is not used to reconstruct the AVI score. '
                    'Contributions have no biosample or gene-specific attribution in this source.'},
    }
