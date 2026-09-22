"""Small complete-query summaries; counts do not come from paginated table rows."""
from collections import defaultdict
from functools import lru_cache
from fastapi import APIRouter,Query
from .db import query,one
from .evidence_common import require_protein
from .evidence_context import ppi_scope,ppi_collections,ppi_type_name,PPI_TYPE,PPI_METHOD,short_mi,EXPRESSION,GTEX_EXPRESSION,expression_spec,expression_context_label
from .disease_ptmd import ptmd_summary_data
router=APIRouter()


def group(dimension,key,label,count,unit,filter,**extra):
    return dict(dimension=dimension,key=key,label=label,count=int(count),records=int(count),unit=unit,filter=filter,**extra)


@lru_cache(maxsize=96)
def _ppi_summary(accession,source,interaction_type,detection_method,dataset=""):
    require_protein(accession)
    scope=ppi_scope(dataset)
    rows=query(f'''WITH matched AS MATERIALIZED (SELECT DISTINCT record_id FROM web_context.ppi_protein_link WHERE target_accession=:accession),
        linked AS MATERIALIZED (SELECT i.* FROM matched m JOIN web_context.ppi_interaction i USING(record_id))
        SELECT i.provider,{PPI_TYPE} raw_type,{PPI_METHOD} raw_method,count(*) records,
        count(*) FILTER(WHERE i.details_json->>'Negative'='true') negative_records
        FROM linked i WHERE {scope} GROUP BY i.provider,raw_type,raw_method ORDER BY i.provider,raw_type,raw_method''',{'accession':accession,'dataset':dataset})
    groups=[];source_counts=defaultdict(int);types=defaultdict(int);negative=0
    for row in rows:
        label=row['provider']+': '+(ppi_type_name(row['raw_type']) or 'Source type unavailable')
        method_label=row['provider']+': '+(short_mi(row['raw_method']) or row['raw_method']) if row['raw_method'] else ''
        if (source and row['provider']!=source) or (interaction_type and label!=interaction_type) or (detection_method and method_label!=detection_method):continue
        source_counts[row['provider']]+=row['records'];types[(row['provider'],label)]+=row['records'];negative+=row['negative_records']
    for provider in ('BioGRID','IntAct'):
        count=source_counts[provider]
        groups.append(group('source',provider,provider,count,'source_interaction_records',{'source':provider},source=provider))
    for (provider,label),count in types.items():groups.append(group('type',label,label,count,'source_interaction_records',{'source':provider,'interaction_type':label},source=provider))
    return dict(groups=groups,collections=ppi_collections(accession),dataset=dataset,totals={'records':sum(source_counts.values()),'negative_records':negative,'sources':sum(v>0 for v in source_counts.values()),'interaction_types':len(types)},
                scope='Selected collection: distinct stored record_id after verified duplicate-packaging reuse. Mutation entries are source feature records linked by affected-protein identity.',
                notes=['Context collections overlap full collections and one another; do not add their counts as independent observations.', 'Source project labels are not patient diagnoses or proof of tissue-specific interactions.', 'Mutation coordinates and sequences have not been validated against canonical sequences or project variants.'])

@router.get('/proteins/{accession}/ppi/summary')
def ppi_summary(accession:str,source:str='',interaction_type:str='',detection_method:str='',dataset:str=Query('',max_length=160)):
    return _ppi_summary(accession,source,interaction_type,detection_method,dataset)


@lru_cache(maxsize=96)
def _disease_summary(accession,source):
    require_protein(accession)
    rows=query('''SELECT DISTINCT e.evidence_id,e.disease_id,e.source FROM web_disease.protein_disease_evidence e
        WHERE e.accession=:accession AND (:source='' OR e.source=:source)''',{'accession':accession,'source':source})
    by_source=defaultdict(list)
    for row in rows:by_source[row['source']].append(row)
    groups=[group('source',provider,provider,len(records),'source_evidence_records',{'source':provider},source=provider,
                  diseases=len({r['disease_id'] for r in records if r['disease_id']})) for provider in ('ClinGen','GenCC','HPO','OMIM') for records in [by_source.get(provider,[])]]
    dosage=query('''SELECT gene_id,gene_symbol,haploinsufficiency,triplosensitivity,report_url
        FROM web_disease.gene_dosage WHERE gene_id IN
        (SELECT gene_id FROM web_disease.gene_protein_link WHERE accession=:accession)''',{'accession':accession})
    return dict(groups=groups,gene_dosage=dosage,ptmd=ptmd_summary_data(accession)['totals'],totals={'records':len(rows),'evidence_records':len(rows),'diseases':len({r['disease_id'] for r in rows if r['disease_id']}),'sources':len(by_source)},
                scope='Distinct source assertion IDs and distinct original disease IDs linked to the selected protein genes.',
                notes=['Disease IDs from different vocabularies are not merged.','Evidence classifications retain each source definition; gene evidence does not classify individual variants.'])

@router.get('/proteins/{accession}/diseases/summary')
def disease_summary(accession:str,source:str=''):
    return _disease_summary(accession,source)


@lru_cache(maxsize=96)
def _qtl_summary(accession,source,tissue,qtl_type):
    require_protein(accession)
    rows=query('''SELECT d.dataset_id,d.provider,d.kind,
        coalesce(d.details_json->>'tissue',d.details_json->>'Tissue',d.details_json->>'background') tissue,
        sum(c.record_count)::bigint records
        FROM web_context.qtl_context_count c JOIN web_context.context_dataset d USING(dataset_id)
        WHERE c.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
        AND c.table_name IN ('gtex_qtl_pair','eqtlgen_cis','qtlbase_association')
        GROUP BY d.dataset_id,d.provider,d.kind,d.details_json ORDER BY d.provider,d.kind,d.dataset_id''',{'accession':accession})
    rows=[r for r in rows if (not source or r['provider']==source) and (not tissue or r['tissue']==tissue) and (not qtl_type or r['kind']==qtl_type)]
    sources=defaultdict(int);types=defaultdict(int);tissues=defaultdict(int)
    for row in rows:
        sources[row['provider']]+=row['records'];types[(row['provider'],row['kind'])]+=row['records']
        if row['tissue']:tissues[(row['provider'],row['tissue'])]+=row['records']
    groups=[group('source',p,p,n,'source_association_records',{'source':p},source=p) for p in ('GTEx','eQTLGen','QTLbase') for n in [sources[p]]]
    groups += [group('type',p+':'+t,t,n,'source_association_records',{'source':p,'qtl_type':t},source=p,qtl_type=t) for (p,t),n in types.items()]
    groups += [group('tissue',p+':'+t,t,n,'source_association_records',{'source':p,'tissue':t},source=p,tissue=t) for (p,t),n in sorted(tissues.items(),key=lambda item:(-item[1],item[0]))]
    return dict(groups=groups,totals={'records':sum(sources.values()),'sources':sum(v>0 for v in sources.values()),'datasets':len(rows),'tissues':len(tissues),'types':len(types)},
                scope='Published qtl_context_count for full gene-associated pairs/association tables; GTEx phenotype summaries are excluded.',
                notes=['Counts are source association records, not independent discoveries or counts above a new significance threshold.',
                       'Types/tissues are provider-qualified; identical labels across sources do not prove equivalent cohorts.'])

@router.get('/proteins/{accession}/qtl/summary')
def qtl_summary(accession:str,source:str='',tissue:str='',qtl_type:str=''):
    return _qtl_summary(accession,source,tissue,qtl_type)


@lru_cache(maxsize=96)
def _expression_summary(accession,source,category,dataset):
    require_protein(accession)
    specs=[GTEX_EXPRESSION]+EXPRESSION
    specs=[s for s in specs if (not source or s[1]==source) and (category in ('','all') or s[2]==category) and (not dataset or s[0]==dataset)]
    records=[]
    params={'accession':accession}
    for name,provider,cat,measurement,unit,extra in specs:
        if provider=='GTEx':
            counts=one('''SELECT count(*) records,count(DISTINCT s.sample_id) contexts,
                count(*) FILTER(WHERE r.values->>s.sample_index::int IS NOT NULL AND r.values->>s.sample_index::int NOT IN ('','NA','NaN','-','.')) available_values
                FROM web_context.expression_gtex_gene_median_tpm r
                JOIN web_context.expression_gtex_sample s ON s.dataset_id='gtex_expression:gtex_gene_median_tpm'
                WHERE r.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)''',params)
        else:
            counts=one(f'''SELECT count(*) records,count(DISTINCT context_id) contexts,
                count(*) FILTER(WHERE "{measurement}" IS NOT NULL AND "{measurement}" NOT IN ('','NA','NaN','-','.')) available_values
                FROM web_context.expression_{name}_detail
                WHERE hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)''',params)
        if counts['records']:
            records.append(dict(name=name,provider=provider,category=cat,measurement=measurement,measurement_unit=unit,**counts))
    sources=defaultdict(lambda:{'records':0,'contexts':0});categories=defaultdict(lambda:{'records':0,'contexts':0})
    groups=[]
    for row in records:
        for aggregate,key in [(sources,row['provider']),(categories,row['category'])]:
            aggregate[key]['records']+=row['records'];aggregate[key]['contexts']+=row['contexts']
        groups.append(group('dataset',row['name'],row['provider']+' · '+row['measurement']+' · '+row['name'].replace('_',' '),row['records'],'source_observation_records',
                            {'source':row['provider'],'category':row['category'],'dataset':row['name']},source=row['provider'],category=row['category'],dataset=row['name'],
                            measurement=row['measurement'],measurement_unit=row['measurement_unit'],contexts=row['contexts'],context_unit='dataset_contexts',available_values=row['available_values']))
    groups=[group('category',cat,cat,v['records'],'source_observation_records',{'category':cat},category=cat,contexts=v['contexts'],context_unit='dataset_contexts') for cat in ('normal','cancer','cell_line','single_cell') for v in [categories[cat]]] + [group('source',p,p,v['records'],'source_observation_records',{'source':p,'category':'all'},source=p,contexts=v['contexts'],context_unit='dataset_contexts') for p,v in sources.items()] + groups
    return dict(groups=groups,totals={'records':sum(r['records'] for r in records),'contexts':sum(r['contexts'] for r in records),'datasets':len(records),'sources':len(sources),'available_values':sum(r['available_values'] for r in records)},
                scope='Complete selected gene observations in the V1-displayed source datasets. Context counts are distinct within each dataset and retain dataset identity.',
                notes=['Category/source context totals count dataset–context pairs, not harmonized unique biological tissues.',
                       'Record counts can be summarized; RNA/protein values and units are never pooled.',
                       'GTEx uses official gene-level tissue medians; full individual-sample/transcript matrices are outside this displayed set.'])

@router.get('/proteins/{accession}/expression/summary')
def expression_summary(accession:str,source:str='',category:str='all',dataset:str=''):
    return _expression_summary(accession,source,category,dataset)


@lru_cache(maxsize=8)
def _expression_contexts(accession,dataset):
    require_protein(accession)
    name,provider,category,measurement,unit,_=expression_spec(dataset)
    params={'accession':accession}
    if provider=='GTEx':
        rows=query('''SELECT s.sample_id context_key,s.sample_id context,count(*) records,
            count(*) FILTER(WHERE r.values->>s.sample_index::int IS NOT NULL
              AND r.values->>s.sample_index::int NOT IN ('','NA','NaN','-','.')) available_values
            FROM web_context.expression_gtex_gene_median_tpm r
            JOIN web_context.expression_gtex_sample s ON s.dataset_id='gtex_expression:gtex_gene_median_tpm'
            WHERE r.hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
            GROUP BY s.sample_id ORDER BY s.sample_id''',params)
    else:
        # Table and measurement identifiers come only from the fixed display specification.
        rows=query(f'''SELECT context_id::text context_key,context_json,count(*) records,
            count(*) FILTER(WHERE "{measurement}" IS NOT NULL
              AND "{measurement}" NOT IN ('','NA','NaN','-','.')) available_values
            FROM web_context.expression_{name}_detail
            WHERE hgnc_id IN (SELECT hgnc_id FROM web.protein_gene WHERE accession=:accession)
            GROUP BY context_id,context_json ORDER BY context_id''',params)
    groups=[group('context',r['context_key'],expression_context_label(r) or 'Source context '+r['context_key'],r['records'],
                  'source_observation_records',{'source':provider,'category':category,'dataset':name,'context_key':r['context_key']},
                  source=provider,category=category,dataset=name,available_values=r['available_values'],
                  measurement=measurement,measurement_unit=unit,context_details=r.get('context_json')) for r in rows]
    return dict(dataset=name,source=provider,category=category,measurement=measurement,measurement_unit=unit,groups=groups,
                totals={'records':sum(r['records'] for r in rows),'contexts':len(rows),'available_values':sum(r['available_values'] for r in rows)},
                scope='Original contexts within this selected dataset and the selected protein genes.',
                notes=['Contexts retain all source dimensions; labels do not merge tissues, cell types, samples or cohorts.',
                       'Counts describe source observations; expression values are not summed across contexts.'])


@router.get('/proteins/{accession}/expression/contexts')
def expression_contexts(accession:str,dataset:str=Query(...,min_length=1,max_length=100),
                        query:str=Query('',max_length=200),limit:int=Query(100,ge=1,le=200),offset:int=Query(0,ge=0,le=100000)):
    result=_expression_contexts(accession,dataset)
    groups=result['groups']
    if query:
        term=query.casefold()
        groups=[g for g in groups if term in g['label'].casefold()]
    return {**result,'groups':groups[offset:offset+limit],'filtered_contexts':len(groups),
            'has_more':offset+limit<len(groups),'limit':limit,'offset':offset}
