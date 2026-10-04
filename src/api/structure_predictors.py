"""Original variant scores on published canonical residue links; no site aggregation."""
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


@router.get('/{accession}/structure/predictor-records')
def predictor_records(accession: str, field: str = 'AlphaMissense_score',
                      offset: int = Query(0, ge=0), limit: int = Query(5000, ge=1, le=10000)):
    if field not in FIELDS:
        raise HTTPException(422, 'Choose a supported structure predictor.')
    where, params, protein = variant_conditions(accession)
    label, expression, unit = FIELDS[field]
    params.update(offset=offset, limit=limit+1)
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
        ORDER BY d.position,c.variant_id,c.annotation_id,c.gene_id,d.prediction_id LIMIT :limit OFFSET :offset''', params)
    for row in rows:
        row['score'] = clean(row['score'])
    return dict(field=field,label=label,unit=unit,sequence_id=protein['sequence_id'],length=protein['length'],
                items=rows[:limit],next_offset=offset+limit if len(rows)>limit else None,
                mapping_scope='verified_canonical_ddg_links',
                note='Each record retains its genomic variant, selected annotation and protein substitution. No averaging, maximum or cross-variant score merging is applied.')
