"""Shared variant filters and source-preserving display metadata for the V2 API."""
from collections import defaultdict
import math
import re
from urllib.parse import unquote
from fastapi import HTTPException
from .db import query, one
from .evidence_common import clean

AA3 = {'Ala':'A','Arg':'R','Asn':'N','Asp':'D','Cys':'C','Gln':'Q','Glu':'E','Gly':'G','His':'H','Ile':'I','Leu':'L','Lys':'K','Met':'M','Phe':'F','Pro':'P','Ser':'S','Thr':'T','Trp':'W','Tyr':'Y','Val':'V','Ter':'*','Sec':'U','Pyl':'O'}
AA1 = {v:k for k,v in AA3.items()}
FREQUENCIES = {'overall':'AF_exomes', **{p:'AF_exomes_'+p for p in ('afr','amr','asj','eas','fin','mid','nfe','remaining','sas','grpmax')}}
FREQUENCY_LABELS = {'overall':'Overall exomes', 'afr':'African / African American','amr':'Admixed American','asj':'Ashkenazi Jewish','eas':'East Asian','fin':'Finnish','mid':'Middle Eastern','nfe':'Non-Finnish European','remaining':'Remaining','sas':'South Asian','grpmax':'Maximum ancestry-group AF'}
CLINICAL_GROUPS = {'pathogenic':'Pathogenic / likely pathogenic','uncertain':'Uncertain significance',
                   'benign':'Benign / likely benign','conflicting':'Conflicting source classifications',
                   'other':'Other source classification','unclassified':'No source classification'}
TRANSCRIPT_LABELS = {'canonical':'VEP canonical transcript','noncanonical':'Non-canonical transcript (not flagged by VEP)',
                     'unknown':'Unknown transcript status'}
TRANSCRIPT_STATUS_SQL = '''CASE WHEN c."Feature_type"='Transcript' AND c."Feature" ~ '^ENST[0-9]+([.][0-9]+)?$'
    THEN CASE WHEN c."CANONICAL"='YES' THEN 'canonical'
              WHEN c."CANONICAL" IS NULL OR c."CANONICAL"='' THEN 'noncanonical'
              ELSE 'unknown' END ELSE 'unknown' END'''


def transcript_status(feature_type,transcript,canonical):
    if feature_type!='Transcript' or not re.fullmatch(r'ENST\d+(?:\.\d+)?',transcript or ''):return 'unknown'
    if canonical=='YES':return 'canonical'
    if canonical in (None,''):return 'noncanonical'
    return 'unknown'


def clinical_display_group(labels):
    """Mutually exclusive source-label grouping for plots, never a new clinical call."""
    normalized=[re.sub(r'\s+',' ',str(label).replace('_',' ').strip().lower()) for label in labels if label]
    meaningful=[label for label in normalized if label not in ('-','.','na','not provided','not specified','none')]
    if any('conflict' in label for label in meaningful):
        return 'conflicting'
    tokens={token.strip() for label in meaningful for token in re.split(r'[/;,]',label)}
    classes={key for key,terms in [('pathogenic',{'pathogenic','likely pathogenic'}),
                                   ('benign',{'benign','likely benign'}),('uncertain',{'uncertain significance'})]
             if tokens & terms}
    if len(classes)>1:return 'conflicting'
    if classes:return next(iter(classes))
    return 'other' if meaningful else 'unclassified'


def amino_change(hgvsp):
    text = unquote(hgvsp or '').split(':')[-1]
    match = re.fullmatch(r'p\.\(?([A-Z][a-z]{2}|[A-Z*])(\d+)([A-Z][a-z]{2}|[A-Z*=?])\)?', text)
    if not match:
        return {'ref_aa':None,'aa_position':None,'alt_aa':None,'protein_change':text or None,'aa_scope':'selected_transcript'}
    ref, pos, alt = match.groups()
    ref, alt = AA3.get(ref, ref), AA3.get(alt, alt)
    return {'ref_aa':ref,'aa_position':int(pos),'alt_aa':alt,'protein_change':f'{ref}{pos}{alt}','aa_scope':'selected_transcript'}


def protein_identity(accession):
    row=one('SELECT p.accession,p.default_sequence_id AS sequence_id,s.length FROM web.protein p LEFT JOIN web.protein_sequence s ON s.sequence_id=p.default_sequence_id WHERE p.accession=:accession',{'accession':accession})
    if not row:
        raise HTTPException(404,'Protein not found')
    return row


def variant_conditions(accession, source='', consequence='', position=None, search='', canonical_start=None, canonical_end=None,
                       frequency='overall', clinvar='', af_min=None, af_max=None, af_status='',transcript_status='all'):
    if source and source not in ('ClinVar','COSMIC','gnomAD','dbSNP'):
        raise HTTPException(422,'Unknown variant source')
    if frequency not in FREQUENCIES:
        raise HTTPException(422,'Unknown frequency population')
    if af_status not in ('','available','missing','zero','positive','invalid'):
        raise HTTPException(422,'Unknown frequency status')
    if transcript_status not in ('all',*TRANSCRIPT_LABELS):
        raise HTTPException(422,'Unknown VEP transcript status')
    protein=protein_identity(accession)
    for value in (canonical_start,canonical_end):
        if value is not None and (value<1 or value>(protein['length'] or 0)):
            raise HTTPException(422,'Canonical range is outside this sequence')
    if canonical_start is not None and canonical_end is not None and canonical_start>canonical_end:
        raise HTTPException(422,'Canonical range start must not exceed end')
    if any(v is not None and (not math.isfinite(v) or v<0 or v>1) for v in (af_min,af_max)) or (af_min is not None and af_max is not None and af_min>af_max):
        raise HTTPException(422,'Allele-frequency bounds must be between 0 and 1')
    params=dict(accession=accession,sequence_id=protein['sequence_id'],source=source,consequence=consequence,position=position,
                search=search,canonical_start=canonical_start or 1,canonical_end=canonical_end or protein['length'],clinvar=clinvar,af_min=af_min,af_max=af_max,
                transcript_status=transcript_status)
    conditions=['c.gene_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)']
    if transcript_status!='all':conditions.append('('+TRANSCRIPT_STATUS_SQL+')=:transcript_status')
    if source=='dbSNP':
        conditions.append('EXISTS (SELECT 1 FROM web_variant.variant_dbsnp s WHERE s.variant_id=c.variant_id LIMIT 1 OFFSET 0)')
    elif source:
        conditions.append('''EXISTS (SELECT 1 FROM web_variant.variant_source_link sl JOIN web_variant.variant_source_record sr USING(record_id)
            JOIN web_variant.variant_dataset sd USING(dataset_id) WHERE sl.variant_id=c.variant_id AND sd.source=:source LIMIT 1 OFFSET 0)''')
    if consequence:
        conditions.append(':consequence = ANY(string_to_array(c."Consequence",\'&\'))')
    if position is not None:
        conditions.append('EXISTS (SELECT 1 FROM web_variant.variant vp WHERE vp.variant_id=c.variant_id AND vp.pos=:position)')
    if canonical_start is not None or canonical_end is not None:
        conditions.append('''EXISTS (SELECT 1 FROM web_variant.variant_ddg_link dl JOIN web_variant.ddg_prediction d USING(prediction_id)
            WHERE dl.annotation_id=c.annotation_id AND dl.gene_id=c.gene_id AND dl.variant_id=c.variant_id
            AND d.sequence_id=:sequence_id AND d.position BETWEEN :canonical_start AND :canonical_end LIMIT 1 OFFSET 0)''')
    if clinvar:
        conditions.append('''EXISTS (SELECT 1 FROM web_variant.variant_source_link sl JOIN web_variant.variant_source_record sr USING(record_id)
            JOIN web_variant.variant_dataset sd USING(dataset_id) WHERE sl.variant_id=c.variant_id AND sd.source='ClinVar'
            AND sr.details_json->>'ClinicalSignificance'=:clinvar LIMIT 1 OFFSET 0)''')
    if search:
        # Search is literal text, with explicit single-AA substitution / position conveniences.
        params['text_search']='%'+search.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
        parts=['c.variant_id ILIKE :text_search','c."HGVSp" ILIKE :text_search','c."HGVSc" ILIKE :text_search','c."Feature" ILIKE :text_search']
        if search.lower().startswith('rs'):
            parts.append('EXISTS (SELECT 1 FROM web_variant.variant_dbsnp dbs WHERE dbs.variant_id=c.variant_id AND dbs.rsid ILIKE :text_search LIMIT 1 OFFSET 0)')
        change=amino_change('p.'+search.removeprefix('p.'))
        if change['aa_position']:
            params.update(aa_ref=change['ref_aa'],aa_alt=change['alt_aa'],aa_pos=str(change['aa_position']))
            if change['alt_aa']=='=':
                parts.append('(c."Protein_position"=:aa_pos AND c."Amino_acids"=:aa_ref)')
            else:
                params['aa_pair']=change['ref_aa']+'/'+change['alt_aa']
                parts.append('(c."Protein_position"=:aa_pos AND c."Amino_acids"=:aa_pair)')
        elif search.isdigit():
            params['aa_pos']=search
            parts.append('c."Protein_position"=:aa_pos')
        conditions.append('('+' OR '.join(parts)+')')
    af='f."'+FREQUENCIES[frequency]+'"'
    frequency_checks=[]
    if af_min is not None:frequency_checks.append(af+'>=:af_min')
    if af_max is not None:frequency_checks.append(af+'<=:af_max')
    if af_status=='available':frequency_checks.append(af+' BETWEEN 0 AND 1')
    elif af_status=='zero':frequency_checks.append(af+'=0')
    elif af_status=='positive':frequency_checks.append(af+'>0 AND '+af+'<=1')
    elif af_status=='invalid':frequency_checks.append(af+' IS NOT NULL AND NOT ('+af+' BETWEEN 0 AND 1)')
    if frequency_checks:
        conditions.append('EXISTS (SELECT 1 FROM web_variant.variant_frequency f WHERE f.variant_id=c.variant_id AND '+' AND '.join(frequency_checks)+' LIMIT 1 OFFSET 0)')
    if af_status=='missing':
        conditions.append('NOT EXISTS (SELECT 1 FROM web_variant.variant_frequency f WHERE f.variant_id=c.variant_id AND '+af+' IS NOT NULL LIMIT 1 OFFSET 0)')
    return ' AND '.join(conditions),params,protein


def base_cte(where):
    return '''WITH base AS MATERIALIZED (SELECT c.variant_id,c.annotation_id,c.gene_id,c."Consequence" consequence
        FROM web_variant.variant_consequence c WHERE '''+where+'''),
        ids AS MATERIALIZED (SELECT DISTINCT variant_id FROM base) '''


def canonical_rows(ids,sequence_id):
    if not ids or not sequence_id:return []
    return query('''SELECT l.variant_id,l.annotation_id,l.gene_id,d.sequence_id,d.position,d.ref_aa,d.alt_aa
        FROM web_variant.variant_ddg_link l JOIN web_variant.ddg_prediction d USING(prediction_id)
        WHERE l.variant_id=ANY(:ids) AND d.sequence_id=:sequence_id ORDER BY d.position,d.ref_aa,d.alt_aa''',{'ids':ids,'sequence_id':sequence_id})


def page_source_evidence(ids):
    if not ids:return []
    return query('''SELECT l.variant_id,r.record_id,d.source,r.native_id,
        CASE WHEN d.source='ClinVar' THEN r.details_json->>'ClinicalSignificance' END classification,
        CASE WHEN d.source='ClinVar' THEN r.details_json->>'ReviewStatus' END review_status,
        CASE WHEN d.source='ClinVar' THEN r.details_json->>'Origin' END origin,
        CASE WHEN d.source='ClinVar' THEN r.details_json->>'Oncogenicity' END oncogenicity,
        CASE WHEN d.source='ClinVar' THEN r.details_json->>'SomaticClinicalImpact' END somatic_clinical_impact
        FROM web_variant.variant_source_link l JOIN web_variant.variant_source_record r USING(record_id)
        JOIN web_variant.variant_dataset d USING(dataset_id) WHERE l.variant_id=ANY(:ids)
        AND d.source IN ('ClinVar','COSMIC','gnomAD') ORDER BY d.source,r.record_id''',{'ids':ids})


def raw_predictions_for_rows(rows,selected_fields):
    """Expose a source category only after the persisted context and chosen numeric value agree."""
    ids=list({r['variant_id'] for r in rows})
    if not ids:return
    pred_fields={field:field.removesuffix('_score')+'_pred' for field in selected_fields if field.endswith('_score')}
    requested=set(selected_fields)|set(pred_fields.values())|{'Ensembl_transcriptid','Ensembl_proteinid','aapos'}
    # Field names come exclusively from the validated published predictor dictionary.
    keys=','.join("'"+key.replace("'","''")+"'" for key in sorted(requested))
    values=','.join("r.details_json->>'"+key.replace("'","''")+"'" for key in sorted(requested))
    raw=query(f'''SELECT l.variant_id,r.record_id,jsonb_object(ARRAY[{keys}]::text[],ARRAY[{values}]::text[]) AS data
        FROM web_variant.variant_source_link l JOIN web_variant.variant_source_record r USING(record_id)
        JOIN web_variant.variant_dataset d USING(dataset_id) WHERE l.variant_id=ANY(:ids) AND d.source='dbNSFP' ''',{'ids':ids})
    by_variant=defaultdict(list)
    for item in raw:by_variant[item['variant_id']].append(item)
    for row in rows:
        matches=row.get('matches_json') or []
        for pred in row['predictions']:
            field=pred['field']; raw_field=pred_fields.get(field)
            values=set()
            pred.update(source_pred=None,source_pred_status='not_available',raw_pred_field=raw_field)
            if raw_field is None or pred['value'] is None:continue
            for item in by_variant[row['variant_id']]:
                data=item['data']; source_value=data.get(raw_field)
                score=data.get(field)
                if not source_value or not score:continue
                if pred['scope']=='variant':
                    if ';' not in source_value and ';' not in score and clean(source_value) is not None:
                        try:
                            if math.isclose(float(score),pred['value'],rel_tol=1e-9,abs_tol=1e-12):values.add(source_value)
                        except ValueError:pass
                    continue
                for match in matches:
                    if match.get('dbnsfp_row_id')!=item['record_id'] or match.get('mapping_status')!='context_matched':continue
                    transcripts=str(data.get('Ensembl_transcriptid') or '').split(';')
                    proteins=str(data.get('Ensembl_proteinid') or '').split(';')
                    positions=str(data.get('aapos') or '').split(';')
                    labels=source_value.split(';'); scores=score.split(';')
                    if not (len(transcripts)==len(proteins)==len(positions)==len(labels)==len(scores)):continue
                    for i,(transcript,protein,position) in enumerate(zip(transcripts,proteins,positions)):
                        if (transcript,protein,position)!=(match.get('source_transcript_id'),match.get('source_protein_id'),match.get('source_aapos')):continue
                        try:
                            if clean(labels[i]) is not None and math.isclose(float(scores[i]),pred['value'],rel_tol=1e-9,abs_tol=1e-12):values.add(labels[i])
                        except ValueError:continue
            if len(values)==1:pred.update(source_pred=next(iter(values)),source_pred_status='matched_source_category')
            elif len(values)>1:pred['source_pred_status']='conflicting_source_categories'
