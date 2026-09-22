"""Canonical-site predictor coverage; never aggregate substitution scores."""
from functools import lru_cache
from fastapi import APIRouter, HTTPException
from .db import query, one
from .variant_support import variant_conditions

router = APIRouter(prefix='/api/proteins', tags=['sequence'])
PREDICTORS = {
    'AlphaMissense_score': 'AlphaMissense',
    'REVEL_score': 'REVEL',
    'SIFT_score': 'SIFT',
}
NOTE = ('Colour represents the number of distinct genomic variants with a finite source score, '
        'not a predicted effect or pathogenicity. Scores for different substitutions or transcript annotations '
        'are not averaged, maximized or combined. Only published links to the current canonical sequence are included.')


COUNTS_SQL = '''      SELECT position,grouping(position) is_total,
        count(DISTINCT variant_id) variant_count,
        count(DISTINCT variant_id) FILTER(WHERE scored) scored_variant_count,
        count(DISTINCT (variant_id,annotation_id,gene_id)) annotation_count,
        count(DISTINCT (variant_id,annotation_id,gene_id)) FILTER(WHERE scored) scored_annotation_count
      FROM mapped GROUP BY GROUPING SETS ((position),()) ORDER BY position NULLS LAST'''

def finite_score_sql(column):
    # Strict infinity bounds also reject PostgreSQL NaN, which sorts above Infinity.
    # Zero is a reported score, including SIFT=0; it must not be treated as missing.
    return f"{column} > '-Infinity'::double precision AND {column} < 'Infinity'::double precision"


@lru_cache(maxsize=96)
def coverage_data(accession, predictor, source, consequence, transcript_status):
    if predictor not in PREDICTORS:
        raise HTTPException(422, 'Choose AlphaMissense_score, REVEL_score or SIFT_score.')
    where, params, protein = variant_conditions(accession, source=source, consequence=consequence,
                                                transcript_status=transcript_status)
    definition = one('''SELECT field,source,scope,tool FROM web_variant.variant_prediction_field
                        WHERE field=:field''', {'field': predictor})
    if not definition or definition['scope'] != 'transcript_consequence':
        raise HTTPException(422, 'This predictor is not available as a selected-transcript score.')
    scored = finite_score_sql('c."' + predictor + '"')
    rows = query('''WITH selected AS MATERIALIZED (
        SELECT c.variant_id,c.annotation_id,c.gene_id,(''' + scored + ''') scored
        FROM web_variant.variant_consequence c WHERE ''' + where + '''),
      mapped AS MATERIALIZED (
        SELECT DISTINCT c.variant_id,c.annotation_id,c.gene_id,c.scored,d.position
        FROM selected c JOIN web_variant.variant_ddg_link l
          ON l.variant_id=c.variant_id AND l.annotation_id=c.annotation_id AND l.gene_id=c.gene_id
        JOIN web_variant.ddg_prediction d USING(prediction_id)
        WHERE d.sequence_id=:sequence_id)
''' + COUNTS_SQL, params)
    sites = [{k: v for k,v in row.items() if k != 'is_total'} for row in rows if not row['is_total']]
    total = next(row for row in rows if row['is_total'])
    return dict(sequence_id=protein['sequence_id'], length=protein['length'],
                predictor={**definition, 'label': PREDICTORS[predictor]},
                predictor_options=[dict(field=field,label=label) for field,label in PREDICTORS.items()],
                sites=sites,
                totals=dict(mapped_variants=total['variant_count'], scored_variants=total['scored_variant_count'],
                            mapped_annotations=total['annotation_count'], scored_annotations=total['scored_annotation_count'],
                            mapped_positions=len(sites), positions_with_scores=sum(s['scored_variant_count']>0 for s in sites)),
                unit='distinct_genomic_variants_with_finite_scores',
                mapping_scope='verified_canonical_ddg_links',
                filters=dict(source=source,consequence=consequence,transcript_status=transcript_status),
                note=NOTE,
                counting_note=('A variant counts once per position, even when several selected annotations carry scores. '
                               'Global totals deduplicate across positions; position counts must not be summed as unique variants.'),
                detail_query=dict(predictors=predictor,source=source,consequence=consequence,transcript_status=transcript_status))


@router.get('/{accession}/sequence/prediction-coverage')
def prediction_coverage(accession: str, predictor: str = 'AlphaMissense_score', source: str = '',
                        consequence: str = '', transcript_status: str = 'all'):
    return coverage_data(accession, predictor, source, consequence, transcript_status)
