"""Counts from complete source associations and the already-published GO-slim bridge."""
from functools import lru_cache
from collections import defaultdict
from .db import query

GO_SLIM_SQL='''SELECT s.category_id,t.name,t.namespace,t.url,
    count(DISTINCT s.annotation_id) annotation_count,count(DISTINCT s.go_id) term_count,
    jsonb_agg(DISTINCT jsonb_build_object('subject_id',s.subject_id,'form_id',s.form_id,
      'relation',s.relation,'extension',s.extension)) contexts
    FROM web.protein_go_slim s JOIN web.go_term t ON t.go_id=s.category_id
    WHERE s.accession=:accession GROUP BY s.category_id,t.name,t.namespace,t.url
    ORDER BY t.namespace,annotation_count DESC,s.category_id'''


@lru_cache(maxsize=96)
def go_summary_data(accession):
    params={'accession':accession}
    rows=query('''SELECT aspect,grouping(aspect) is_total,count(DISTINCT annotation_id) annotation_count,count(DISTINCT go_id) term_count,
        count(DISTINCT annotation_id) FILTER(WHERE is_negative) negative_annotation_count,
        count(DISTINCT annotation_id) FILTER(WHERE evidence_code='ND') no_data_annotation_count
        FROM web.protein_go_annotation WHERE accession=:accession GROUP BY GROUPING SETS ((aspect),())''',params)
    values={r['aspect']:{k:v for k,v in r.items() if k!='is_total'} for r in rows if not r['is_total']}
    aspects=[values.get(aspect,{'aspect':aspect,'annotation_count':0,'term_count':0,'negative_annotation_count':0,'no_data_annotation_count':0}) for aspect in ('F','P','C')]
    total=next(r for r in rows if r['is_total'])
    return {'totals':{key:total[key] for key in ('annotation_count','term_count','negative_annotation_count','no_data_annotation_count')},
            'aspects':aspects,'categories':query(GO_SLIM_SQL,params),
            'scope':'Complete protein-associated original GO statements. Categories use the published positive generic GO-slim bridge.',
            'notes':['Annotation counts are source statements, not independent experiments; term counts are distinct non-null stored go_id values, retaining original resolution/obsolete states.',
                     'GO-slim categories can overlap and are not added to direct annotations; NOT, ND, obsolete/unresolved terms and parent-context-only associations are excluded by the published view.',
                     'Original subject, isoform, relation and extension contexts remain explicit; category aggregation does not claim canonical-sequence-specific function.']}


@lru_cache(maxsize=96)
def pathway_summary_data(accession):
    rows=query('''SELECT a.association_id,a.pathway_id,a.source,pt.topic_id,t.name
        FROM web.protein_pathway a JOIN web.pathway p ON p.pathway_id=a.pathway_id AND p.source=a.source
        LEFT JOIN web.pathway_topic pt ON pt.pathway_id=a.pathway_id AND pt.source=a.source
        LEFT JOIN web.pathway t ON t.pathway_id=pt.topic_id AND t.source=pt.source
        WHERE a.accession=:accession ORDER BY a.source,pt.topic_id,a.pathway_id,a.association_id''',{'accession':accession})
    grouped=defaultdict(list)
    for r in rows:
        if r['topic_id']:grouped[(r['source'],r['topic_id'],r['name'])].append(r)
    topics=[{'source':source,'topic_id':topic,'name':name,'association_count':len({r['association_id'] for r in members}),
             'pathway_count':len({r['pathway_id'] for r in members}),'filter':{'topic_id':topic}}
            for (source,topic,name),members in grouped.items()]
    return {'totals':{'association_count':len({r['association_id'] for r in rows}),
                      'pathway_count':len({(r['source'],r['pathway_id']) for r in rows})},'topics':topics,
            'scope':'Complete published source pathway associations and existing source-defined topic memberships.',
            'notes':['Distinct pathway IDs differ from association records (source object, evidence and relationship contexts).',
                     'Pathways can belong to multiple topics; topic counts are not added as distinct pathways.',
                     'These counts do not measure activation, enrichment, importance or molecular interaction networks.']}
