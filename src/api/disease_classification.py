"""Database-only access to the confirmed Q7 multiaxis disease classification."""
import re
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from .db import one, query
from .evidence_disease import clinvar_condition_rows

router = APIRouter(prefix='/api', tags=['disease classification'])
SCHEMES = (
    ('mondo_body_system', 'direct_root_child', 'MONDO · Body system'),
    ('mondo_etiology', 'direct_root_child', 'MONDO · Etiology'),
    ('kegg', 'entry_category_optimized', 'KEGG · Disease categories'),
)
PREDICATE = """((m.scheme IN ('mondo_body_system','mondo_etiology') AND m.category_level='direct_root_child')
    OR (m.scheme='kegg' AND m.category_level='entry_category_optimized'))"""


def available():
    return one("SELECT to_regclass('web_classification._build_manifest') IS NOT NULL AS available")['available']


def mondo_ids(value):
    """The published Q7 direct-summary token rule; never infer from names/RCVs."""
    tokens = [token.strip() for token in re.split(r'[,|;]', value or '')]
    return sorted({'MONDO:' + token[-7:] for token in tokens
                   if re.fullmatch(r'MONDO:(?:MONDO:)?[0-9]{7}', token)})


def source_classifications(variant_id, sources):
    ids = sorted({id for row in sources if row['source'] == 'ClinVar'
                  for id in mondo_ids((row['details_json'] or {}).get('PhenotypeIDS'))})
    if not available():
        return {'available': False, 'by_mondo': {}}
    rows = query(f'''SELECT m.* FROM web_classification.context_classification_mapping m
        JOIN web_classification.variant_mondo b ON b.mondo_id=m.subject_id
        WHERE b.variant_id=:variant AND b.mondo_id=ANY(:ids)
          AND m.subject_type='disease' AND m.subject_namespace='MONDO' AND {PREDICATE}
        ORDER BY m.subject_id,m.scheme,m.category_label''', {'variant': variant_id, 'ids': ids}) if ids else []
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['subject_id']].append(row)
    return {'available': True, 'by_mondo': dict(grouped)}


def record_classification(value, data):
    return {'available': data['available'], 'diseases': [
        {'mondo_id': id, 'classifications': data['by_mondo'].get(id, [])}
        for id in mondo_ids(value)]}


def distribution(variant_ids):
    ids = sorted(set(variant_ids))
    bridge = one('''SELECT count(DISTINCT variant_id) AS variants_with_mondo,
        count(DISTINCT mondo_id) AS disease_ids FROM web_classification.variant_mondo
        WHERE variant_id=ANY(:ids)''', {'ids': ids})
    counts = query(f'''SELECT m.scheme,m.category_level,m.category_id,m.category_label,
        GROUPING(m.category_id) AS is_total,count(DISTINCT b.variant_id) AS variant_count
        FROM web_classification.variant_mondo b
        JOIN web_classification.context_classification_mapping m ON m.subject_id=b.mondo_id
        WHERE b.variant_id=ANY(:ids) AND m.subject_type='disease' AND m.subject_namespace='MONDO'
          AND m.category_id IS NOT NULL AND {PREDICATE}
        GROUP BY GROUPING SETS ((m.scheme,m.category_level,m.category_id,m.category_label),
                               (m.scheme,m.category_level))''', {'ids': ids})
    categories = query('''SELECT scheme,level,category_id,category_label,anatomical_category
        FROM web_classification.classification_categories ORDER BY category_label''')
    schemes = []
    for scheme, level, label in SCHEMES:
        selected = [r for r in counts if r['scheme'] == scheme and r['category_level'] == level]
        mapped = next((r['variant_count'] for r in selected if r['is_total']), 0)
        lookup = {r['category_id']: r['variant_count'] for r in selected if not r['is_total']}
        items = [{**c, 'variant_count': lookup.get(c['category_id'], 0)} for c in categories
                 if c['scheme'] == scheme and c['level'] == level]
        items.sort(key=lambda r: (-r['variant_count'], r['category_label']))
        schemes.append({'scheme': scheme, 'level': level, 'label': label,
                        'mapped_variants': mapped, 'unmapped_variants': len(ids) - mapped,
                        'with_mondo_unmapped': bridge['variants_with_mondo'] - mapped, 'items': items})
    manifest = one('SELECT manifest FROM web_classification._build_manifest')['manifest']
    summary = manifest['summary']
    return {'total_variants': len(ids), **bridge, 'without_mondo': len(ids) - bridge['variants_with_mondo'],
            'schemes': schemes, 'versions': {'rules': manifest['data_version'],
                'mondo': summary['mondo_version'], 'kegg': summary['kegg']['disease_last_update']},
            'counting_unit': 'distinct ClinVar summary SNVs linked to this protein through its genes',
            'overlapping_categories': True, 'kegg_disease_identity_equivalence': False}


@router.get('/proteins/{accession}/diseases/clinvar-classification')
def protein_classification(accession: str):
    records = clinvar_condition_rows(accession)
    if not available():
        raise HTTPException(503, 'Disease classification data has not been loaded.')
    return distribution([r['variant_id'] for r in records])
