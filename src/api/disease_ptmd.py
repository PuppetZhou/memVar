"""PTMD2 protein-associated disease-context records, without sequence projection."""
from functools import lru_cache
from collections import Counter
from fastapi import APIRouter,Query
from .db import query
from .evidence_common import require_protein,cursor_read,cursor_write,fields,clean

router=APIRouter()
PTMD_WHERE="""r.dataset_id LIKE 'PTMD2:%' AND
    (r.accession=:accession OR (r.accession IS NULL AND r.candidate_accessions ? :accession))"""
ASSOCIATION="CASE WHEN r.accession=:accession THEN 'protein_associated' ELSE 'candidate_protein_association' END"
NOTE='Original PTMD2 disease-context records associated with the protein; source positions and MutationSite are not canonical sequence coordinates or mapped project variants.'


@lru_cache(maxsize=96)
def ptmd_summary_data(accession):
    require_protein(accession)
    rows=query(f'''SELECT r.record_id,r.details_json->>'Disease' disease,r.details_json->>'CellType' cell_type,r.source_type,
        {ASSOCIATION} association_status FROM web.ptm_record r WHERE {PTMD_WHERE}
        ORDER BY r.record_id''',{'accession':accession})
    diseases=Counter(clean(r['disease']) for r in rows)
    types=Counter(clean(r['source_type']) for r in rows)
    cells=Counter(clean(r['cell_type']) for r in rows)
    associated=Counter(r['association_status'] for r in rows)
    groups=[]
    for dimension,counts,parameter in [('disease',diseases,'disease'),('type',types,'source_type'),('cell_type',cells,'cell_type')]:
        for value,count in sorted(counts.items(),key=lambda item:(-item[1],item[0] or '')):
            if value is None:
                if dimension=='cell_type':
                    groups.append({'dimension':dimension,'key':'missing','label':'Not reported','count':count,
                                   'unit':'source_ptm_disease_records','filter':{'cell_type_missing':'true'}})
                continue
            groups.append({'dimension':dimension,'key':value,'label':value,'count':count,
                           'unit':'source_ptm_disease_records','filter':{parameter:value}})
    return {'source':'PTMD2','totals':{'records':len(rows),'protein_associated':associated['protein_associated'],
                'candidate_protein_association':associated['candidate_protein_association'],
                'disease_labels':len([d for d in diseases if d is not None])},
            'groups':groups,'scope':NOTE,
            'notes':['Disease labels retain source text and are not merged with curated gene–disease assertion IDs.',
                     'State codes and verification flags retain their source meaning; no interpretation is inferred from a code.']}


@router.get('/proteins/{accession}/diseases/ptmd/summary')
def ptmd_summary(accession:str):
    return ptmd_summary_data(accession)


@router.get('/proteins/{accession}/diseases/ptmd')
def ptmd_records(accession:str,disease:str=Query('',max_length=1000),source_type:str=Query('',max_length=100),
                 cell_type:str=Query('',max_length=1000),cell_type_missing:bool=False,
                 limit:int=Query(20,ge=1,le=100),cursor:str='',offset:int=Query(0,ge=0)):
    require_protein(accession)
    context=['disease_ptmd',accession,disease,source_type,cell_type,cell_type_missing]
    after=cursor_read(cursor,context) or ''
    where=PTMD_WHERE+' AND r.record_id>:after'
    if disease:where+=" AND r.details_json->>'Disease'=:disease"
    if source_type:where+=' AND r.source_type=:source_type'
    if cell_type_missing:
        where+=" AND (r.details_json->>'CellType' IS NULL OR r.details_json->>'CellType' IN ('','-','.','NA','NaN'))"
    elif cell_type:where+=" AND r.details_json->>'CellType'=:cell_type"
    params={'cell_type':cell_type,'accession':accession,'disease':disease,'source_type':source_type,'after':after,'limit':limit+1,'offset':0 if cursor else offset}
    rows=query(f'''WITH page AS MATERIALIZED (SELECT r.* FROM web.ptm_record r WHERE {where}
        ORDER BY r.record_id LIMIT :limit OFFSET :offset)
        SELECT r.record_id,r.source_record_id source_id,'PTMD2' source,r.source_type,r.description,
        r.source_accession,r.source_sequence_id,r.source_start,r.source_end,r.source_residue,
        r.identity_status,r.mapping_status,r.evidence_status,r.candidate_accessions,
        {ASSOCIATION} association_status,r.details_json details,
        COALESCE((SELECT jsonb_agg(jsonb_build_object('namespace',e.namespace,'identifier',e.identifier,
          'url',e.url,'kind',e.evidence_kind,'is_current',e.is_current))
          FROM web.ptm_evidence_all e WHERE e.record_id=r.record_id),'[]'::jsonb) evidence
        FROM page r ORDER BY r.record_id''',params)
    for row in rows[:limit]:
        details=row.pop('details') or {}
        row.update(disease=clean(details.get('Disease')),state=clean(details.get('State')),
                   mutation_site=clean(details.get('MutationSite')),cell_type=clean(details.get('CellType')),
                   enzyme=clean(details.get('Enzyme')),source_position=clean(details.get('Position')),
                   fields=fields(details,['Disease','State','MutationSite','CellType','Enzyme','Position','Source','Is_experimental_verification','Gene name']))
    summary=ptmd_summary_data(accession)
    return {'items':rows[:limit],'next_cursor':cursor_write(rows[limit-1]['record_id'],context) if len(rows)>limit else None,
            'filters':{'diseases':[g['key'] for g in summary['groups'] if g['dimension']=='disease'],
                       'cell_types':[g['key'] for g in summary['groups'] if g['dimension']=='cell_type' and 'cell_type' in g['filter']],
                       'source_types':[g['key'] for g in summary['groups'] if g['dimension']=='type']},'note':NOTE}
