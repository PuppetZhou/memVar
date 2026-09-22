"""Whole-query counts and verified canonical projections, never page-derived statistics."""
from functools import lru_cache
from collections import defaultdict,Counter
from fastapi import APIRouter, Query
from .db import query, one
from .variant_support import variant_conditions,base_cte,FREQUENCIES,FREQUENCY_LABELS,CLINICAL_GROUPS,clinical_display_group,TRANSCRIPT_LABELS,TRANSCRIPT_STATUS_SQL
from .prediction_overview import prediction_overview

router=APIRouter()

@lru_cache(maxsize=96)
def _summary(accession,source,consequence,position,search,canonical_start,canonical_end,frequency,clinvar,af_min,af_max,af_status,transcript_status):
    where,params,protein=variant_conditions(accession,source,consequence,position,search,canonical_start,canonical_end,frequency,clinvar,af_min,af_max,af_status,transcript_status)
    cte=base_cte(where)
    af='f."'+FREQUENCIES[frequency]+'"'
    totals=one(cte+f'''SELECT count(*) unique_variants,(SELECT count(*) FROM base) annotation_rows,
        count(*) FILTER(WHERE {af} BETWEEN 0 AND 1) frequency_available,
        count(*) FILTER(WHERE {af} IS NULL) frequency_missing,
        count(*) FILTER(WHERE {af} IS NOT NULL AND NOT ({af} BETWEEN 0 AND 1)) frequency_invalid,
        count(*) FILTER(WHERE {af}=0) frequency_zero,
        count(*) FILTER(WHERE {af}>0 AND {af}<=1) frequency_positive,
        min({af}) FILTER(WHERE {af} BETWEEN 0 AND 1) af_min,
        max({af}) FILTER(WHERE {af} BETWEEN 0 AND 1) af_max,
        percentile_cont(ARRAY[0.25,0.5,0.75]) WITHIN GROUP (ORDER BY {af}) FILTER(WHERE {af} BETWEEN 0 AND 1) af_quartiles
        FROM ids LEFT JOIN web_variant.variant_frequency f USING(variant_id)''',params)
    consequences=query(cte+'''SELECT unnest(string_to_array(consequence,'&')) value,count(DISTINCT variant_id) count
        FROM base GROUP BY value ORDER BY count DESC,value''',params)
    transcript_rows=query('SELECT '+TRANSCRIPT_STATUS_SQL+''' status,count(DISTINCT c.variant_id) variants,count(*) annotations
        FROM web_variant.variant_consequence c WHERE '''+where+' GROUP BY status',params)
    transcript_counts={r['status']:r for r in transcript_rows}
    transcript_groups=[{'key':key,'label':label,'count':transcript_counts.get(key,{}).get('variants',0),
                        'annotation_rows':transcript_counts.get(key,{}).get('annotations',0),'unit':'unique_variants',
                        'filter':{'transcript_status':key}} for key,label in TRANSCRIPT_LABELS.items()]
    from .evidence import prediction_dictionary,prediction_group
    predictor_summary=prediction_overview(where,params,[{**p,'group':prediction_group(p['field'])} for p in prediction_dictionary()])
    # Distinguish grouping NULL from a missing source category with an explicit grouping flag.
    source_rows=query(cte+'''SELECT d.source,r.details_json->>'ClinicalSignificance' classification,
        grouping(r.details_json->>'ClinicalSignificance') is_source_total,count(DISTINCT ids.variant_id) count
        FROM ids JOIN web_variant.variant_source_link l USING(variant_id)
        JOIN web_variant.variant_source_record r USING(record_id) JOIN web_variant.variant_dataset d USING(dataset_id)
        WHERE d.source IN ('ClinVar','COSMIC','gnomAD')
        GROUP BY GROUPING SETS ((d.source),(d.source,r.details_json->>'ClinicalSignificance'))
        HAVING grouping(r.details_json->>'ClinicalSignificance')=1 OR d.source='ClinVar'
        ORDER BY d.source,classification''',params)
    dbsnp=one(cte+'''SELECT count(*) count FROM ids WHERE EXISTS (SELECT 1 FROM web_variant.variant_dbsnp s WHERE s.variant_id=ids.variant_id LIMIT 1 OFFSET 0)''',params)['count']
    clinical_rows=query(cte+'''SELECT DISTINCT ids.variant_id,r.details_json->>'ClinicalSignificance' classification
        FROM ids JOIN web_variant.variant_source_link l USING(variant_id)
        JOIN web_variant.variant_source_record r USING(record_id) JOIN web_variant.variant_dataset d USING(dataset_id)
        WHERE d.source='ClinVar' ''',params)
    labels=defaultdict(list)
    for row in clinical_rows:labels[row['variant_id']].append(row['classification'])
    clinical_by_variant={vid:clinical_display_group(values) for vid,values in labels.items()}
    clinical_counts=Counter(clinical_by_variant.values())
    clinical_counts['unclassified']+=totals['unique_variants']-len(clinical_by_variant)
    canonical=query(cte+'''SELECT d.position,count(DISTINCT b.variant_id) variant_count,
        count(DISTINCT (d.ref_aa,d.alt_aa)) substitution_count,array_agg(DISTINCT b.variant_id) variant_ids
        FROM base b JOIN web_variant.variant_ddg_link l ON l.annotation_id=b.annotation_id AND l.gene_id=b.gene_id AND l.variant_id=b.variant_id
        JOIN web_variant.ddg_prediction d USING(prediction_id) WHERE d.sequence_id=:sequence_id
        GROUP BY d.position ORDER BY d.position''',params)
    mapped=len({vid for row in canonical for vid in row['variant_ids']})
    totals.update(canonical_mapped_variants=mapped,canonical_unmapped_variants=totals['unique_variants']-mapped,
                  canonical_variant_position_associations=sum(row['variant_count'] for row in canonical))
    groups=[]
    for row in consequences:
        groups.append(dict(dimension='consequence',key=row['value'],label=row['value'],count=row['count'],unit='unique_variants',filter={'consequence':row['value']}))
    for row in source_rows:
        if row['is_source_total']:
            groups.append(dict(dimension='source',key=row['source'],label=row['source'],count=row['count'],unit='unique_variants',filter={'source':row['source']}))
        elif row['classification']:
            groups.append(dict(dimension='clinvar',key=row['classification'],label=row['classification'],count=row['count'],unit='unique_variants',filter={'clinvar':row['classification']}))
    groups.append(dict(dimension='source',key='dbSNP',label='dbSNP',count=dbsnp,unit='unique_variants',filter={'source':'dbSNP'}))
    for key,label in [('missing','No selected AF'),('zero','AF = 0'),('positive','AF > 0'),('invalid','Outside AF range')]:
        groups.append(dict(dimension='frequency',key=key,label=label,count=totals['frequency_'+key],unit='unique_variants',filter={'af_status':key}))
    for row in canonical:
        counts=Counter(clinical_by_variant.get(vid,'unclassified') for vid in row.pop('variant_ids'))
        row.update(count=row['variant_count'],unit='unique_variants_at_position',filter={'canonical_start':row['position'],'canonical_end':row['position']},
                   clinical_counts={key:counts[key] for key in CLINICAL_GROUPS})
    return dict(totals=totals,groups=groups,canonical_sites=canonical,positions=canonical,
                transcript_groups=transcript_groups,predictor_summary=predictor_summary,
                transcript_scope='Selected Ensembl/VEP transcript consequences only: MANE Select first, Ensembl canonical only when no MANE Select. VEP CANONICAL status is independent of UniProt sequence mapping; variants with multiple selected annotations can appear in more than one transcript group.',
                clinical_groups=[{'key':key,'label':label,'count':clinical_counts[key],'unit':'unique_variants'} for key,label in CLINICAL_GROUPS.items()],
                clinical_grouping='Display grouping of original ClinVar ClinicalSignificance labels only: any conflict label or more than one of pathogenic/benign/uncertain classes gives conflicting; otherwise retain the single class, other substantive labels, or no classification. No highest-class selection or new clinical assessment.',
                canonical_counting_note='Each position counts distinct genomic variants after removing duplicate annotations. Sums across positions count variant-position associations; canonical_mapped_variants counts distinct variants across the complete query.',
                sequence_id=protein['sequence_id'],sequence_length=protein['length'],mapping_scope='verified_canonical_ddg_links',
                frequency={'population':frequency,'label':FREQUENCY_LABELS[frequency],'source':'gnomAD exomes 4.1','distribution':'quartiles of available individual variant AF values'},
                notes=['Counts cover the complete current query, not the current table page.',
                       'Source, consequence and ClinVar categories can overlap; their counts must not be added as distinct variants.',
                       'Canonical positions use only published annotation-to-ddG links on the current canonical sequence. Other variants remain in the catalog without a plotted coordinate.',
                       'AF quartiles describe the selected ancestry group; frequencies are never summed across variants or populations.'])

@router.get('/proteins/{accession}/variants/summary')
def variant_summary(accession:str,source:str='',consequence:str='',position:int|None=None,search:str=Query('',max_length=200),
                    canonical_start:int|None=None,canonical_end:int|None=None,frequency:str='overall',clinvar:str='',
                    af_min:float|None=None,af_max:float|None=None,af_status:str='',transcript_status:str='all'):
    from .evidence import variant_filters
    result=_summary(accession,source,consequence,position,search,canonical_start,canonical_end,frequency,clinvar,af_min,af_max,af_status,transcript_status)
    return {**result,'filters':variant_filters(accession)}
