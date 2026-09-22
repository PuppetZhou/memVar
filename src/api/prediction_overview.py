"""Predictor catalog and coverage over the same selected variant consequences."""
from .db import one

DESCRIPTIONS={
    'AlphaGenome':'Variant-level AlphaGenome source summaries for sequence-function and splicing effects; not a selected-transcript-specific clinical classification.',
    'Loss of function':'ALoFT loss-of-function source outputs, including inheritance-mode probabilities and affected-transcript fraction.',
    'Conservation and background':'Evolutionary conservation or genomic background measures on their original scales; not probabilities of pathogenicity.',
    'Sequence models':'Source scores from sequence-informed models; each tool retains its own scale and source category.',
    'Amino acid substitution':'Tool-specific effects of amino-acid substitutions; transcript-scoped values retain the selected annotation identity.',
    'Integrated effect predictions':'Source computational effect scores, often integrating multiple inputs; these are not independent clinical confirmations.'}


def prediction_overview(where,params,definitions):
    expressions=[]
    for i,p in enumerate(definitions):
        field=p['field'];alias='c' if p['scope']=='transcript_consequence' else 'v'
        value=f'{alias}."{field}"'
        valid=f"{value} > '-Infinity'::double precision AND {value} < 'Infinity'::double precision"
        expressions.append(f'count(DISTINCT c.variant_id) FILTER(WHERE {valid}) AS variants_{i}')
        if p['scope']=='transcript_consequence':expressions.append(f'count(*) FILTER(WHERE {valid}) AS annotations_{i}')
    coverage=one('''WITH selected AS MATERIALIZED (SELECT c.* FROM web_variant.variant_consequence c WHERE '''+where+''')
        SELECT '''+','.join(expressions)+''' FROM selected c JOIN web_variant.variant v USING(variant_id)''',params)
    fields=[]
    for i,p in enumerate(definitions):
        fields.append({**p,'covered_variants':coverage[f'variants_{i}'],
                       'covered_annotations':coverage.get(f'annotations_{i}') if p['scope']=='transcript_consequence' else None})
    groups=[]
    for name in dict.fromkeys(p['group'] for p in fields):
        members=[p for p in fields if p['group']==name]
        labels=sorted({p['tool'] for p in members})
        groups.append({'name':name,'description':DESCRIPTIONS[name],'field_count':len(members),
                       'tool_label_count':len(labels),'tool_labels':labels,'fields':members})
    return {'field_count':len(fields),'tool_label_count':len({p['tool'] for p in fields}),
            'source_count':len({p['source'] for p in fields}),'groups':groups,
            'coverage_scope':'Complete current variant query; finite source values only. covered_variants is distinct genomic variants; covered_annotations applies only to selected transcript-consequence fields.',
            'tool_count_note':'tool_label_count counts distinct published tool labels, not independent methods or evidence. Multiple fields, model versions and related models can belong to one method family.'}
