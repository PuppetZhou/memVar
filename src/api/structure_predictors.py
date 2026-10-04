"""Canonical predictor records and the confirmed per-residue extrema projection.

Scientific contract: modules/variant/docs/rules.md, 2026-10-04.
Original records remain available; source values and mapping scope are unchanged.
"""
from collections import defaultdict
from functools import lru_cache
import math
from fastapi import APIRouter, HTTPException, Query
from .db import query
from .variant_support import variant_conditions
from .evidence_common import clean

router = APIRouter(prefix='/api/proteins', tags=['structures'])
FIELDS = {
    'AlphaMissense_score': ('AlphaMissense', 'c."AlphaMissense_score"', '0–1'),
    'ESM1b_score': ('ESM1b', 'c."ESM1b_score"', 'Original score'),
    'ThermoMPNN_ddg': ('ThermoMPNN', 'd.ddg_pred', 'kcal/mol'),
    'alphagenome_avi_raw': ('AlphaGenome · AVI raw', 'v.alphagenome_avi_raw', 'Original score'),
    'alphagenome_avi_phred': ('AlphaGenome · AVI PHRED', 'v.alphagenome_avi_phred', 'PHRED'),
    'alphagenome_splicing': ('AlphaGenome · Merged splicing', 'v.alphagenome_splicing', 'Original magnitude'),
}
RULES = {
    'ESM1b_score': ('minimum', 'Minimum score per residue; lower ESM1b scores indicate stronger predicted effect.'),
    'ThermoMPNN_ddg': ('signed_absolute_maximum', 'Largest absolute ΔΔG per residue, with its original sign: negative stabilizing, positive destabilizing.'),
}


def original_records(accession, field, offset=0, limit=None):
    if field not in FIELDS:
        raise HTTPException(422, 'Choose a supported structure predictor.')
    where, params, protein = variant_conditions(accession)
    _, expression, _ = FIELDS[field]
    params.update(offset=offset, limit=limit)
    rows = query('''WITH selected AS MATERIALIZED (
        SELECT c.* FROM web_variant.variant_consequence c WHERE '''+where+''')
        SELECT c.variant_id,c.annotation_id,c.gene_id,c."Feature" transcript_id,
               d.prediction_id,d.sequence_id,d.position,d.ref_aa,d.alt_aa,'''+expression+''' score
        FROM selected c JOIN web_variant.variant_ddg_link l
          ON l.variant_id=c.variant_id AND l.annotation_id=c.annotation_id AND l.gene_id=c.gene_id
        JOIN web_variant.ddg_prediction d USING(prediction_id)
        JOIN web_variant.variant v ON v.variant_id=c.variant_id
        WHERE d.sequence_id=:sequence_id ''' +
        (" AND d.model='ThermoMPNN' AND d.checkpoint='thermoMPNN_default.pt'" if field=='ThermoMPNN_ddg' else '') + '''
        ORDER BY d.position,c.variant_id,c.annotation_id,c.gene_id,d.prediction_id''' +
        (' LIMIT :limit OFFSET :offset' if limit is not None else ''), params)
    for row in rows:
        row['score'] = clean(row['score'])
    return protein, rows


@router.get('/{accession}/structure/predictor-records')
def predictor_records(accession: str, field: str = 'AlphaMissense_score',
                      offset: int = Query(0, ge=0), limit: int = Query(5000, ge=1, le=10000)):
    protein, rows = original_records(accession, field, offset, limit+1)
    label, _, unit = FIELDS[field]
    return dict(field=field,label=label,unit=unit,sequence_id=protein['sequence_id'],length=protein['length'],
                items=rows[:limit],next_offset=offset+limit if len(rows)>limit else None,
                mapping_scope='verified_canonical_ddg_links',
                note='Each record retains its genomic variant, selected annotation and protein substitution. No averaging, maximum or cross-variant score merging is applied.')


def summarize_sites(rows, field):
    """Keep all tied source identities; opposite-sign absolute ties have no scalar."""
    rule = RULES.get(field, ('maximum', 'Maximum score per residue.'))[0]
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['position']].append(row)
    sites = []
    for position, original in sorted(grouped.items()):
        finite = [r for r in original if isinstance(r['score'], (int, float)) and math.isfinite(r['score'])]
        records = []
        if finite:
            extreme = (min(r['score'] for r in finite) if rule == 'minimum' else
                       max(abs(r['score']) for r in finite) if rule == 'signed_absolute_maximum' else
                       max(r['score'] for r in finite))
            records = [r for r in finite if (abs(r['score']) if rule == 'signed_absolute_maximum' else r['score']) == extreme]
        values = sorted({r['score'] for r in records})
        sites.append(dict(position=position, score=values[0] if len(values)==1 else None,
                          status='opposite_sign_tie' if len(values)>1 else 'scored' if values else 'no_finite_score',
                          extreme_values=values, records=records,
                          scored_variant_count=len({r['variant_id'] for r in finite}),
                          scored_substitution_count=len({(r['ref_aa'],r['alt_aa']) for r in finite}),
                          scored_annotation_count=len({(r['variant_id'],r['annotation_id'],r['gene_id']) for r in finite})))
    return sites


@lru_cache(maxsize=24)
def extrema_data(accession, field):
    protein, rows = original_records(accession, field)
    label, _, unit = FIELDS[field]
    sites = summarize_sites(rows, field)
    values = [v for site in sites for v in site['extreme_values']]
    rule, explanation = RULES.get(field, ('maximum', 'Maximum score per residue; higher values indicate stronger predicted effect.'))
    if field == 'AlphaMissense_score':
        bounds = [0,1]
        scale_note = 'Fixed native 0–1 scale; not a clinical classification.'
    elif field == 'ThermoMPNN_ddg':
        extent = max((abs(v) for v in values), default=0) or 1
        bounds = [-extent,extent]
        scale_note = 'Symmetric native ΔΔG scale around zero, spanning this protein’s extrema. Compare values across proteins, not colors.'
    else:
        bounds = [min([0]+values),max([0]+values)]
        if bounds[0] == bounds[1]:
            bounds[1] = bounds[0]+1
        scale_note = 'Native score scale spanning this protein’s extrema and zero. Compare values across proteins, not colors.'
    return dict(field=field,label=label,unit=unit,sequence_id=protein['sequence_id'],length=protein['length'],
                rule=rule,rule_label=explanation,sites=sites,scale=dict(min=bounds[0],max=bounds[1],note=scale_note),
                scored_positions=sum(bool(s['extreme_values']) for s in sites),
                mapped_positions=len(sites),mapping_scope='verified_canonical_ddg_links',
                note='Extrema use all finite scores on published canonical variant links, independent of the variant table filters. This is the available project variant set, not all possible substitutions. Models are never combined.',
                tie_note='All tied records are retained. Equal absolute ΔΔG with opposite signs is marked as a tie, not assigned an arbitrary direction.')


@router.get('/{accession}/structure/predictor-extrema')
def predictor_extrema(accession: str, field: str = 'AlphaMissense_score'):
    return extrema_data(accession, field)
