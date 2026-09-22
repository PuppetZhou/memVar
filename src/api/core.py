"""Protein identity and source-separated overview projections."""
from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .db import one, query
from .overview_summary import go_summary_data,pathway_summary_data

router = APIRouter(prefix='/api', tags=['proteins'])


class Protein(BaseModel):
    accession: str
    protein_name: str | None
    gene_names: list[str]
    gene_name: str | None = None
    sequence_id: str | None
    length: int | None
    reviewed: bool | None
    entry_name: str | None = None
    alternative_protein_names: list[str] = []
    hgnc_ids: list[str] = []
    organism: str = 'human'


class ProteinSearch(BaseModel):
    items: list[Protein]
    has_more: bool
    total: int


class Overview(BaseModel):
    protein: Protein
    function: dict[str, Any]
    annotations: list[dict[str, Any]]
    isoforms: list[dict[str, Any]]
    external_references: list[dict[str, Any]]
    membrane_labels: list[dict[str, Any]]
    membrane_classification: dict[str, Any] | None = None
    go: dict[str, Any]
    go_slim: list[dict[str, Any]]
    pathways: dict[str, Any]
    locations: dict[str, Any]
    rhea: dict[str, Any]
    pharmacology: dict[str, Any]


PROTEIN_SQL = '''SELECT p.accession,p.protein_name,p.gene_names,
 p.gene_names->>0 AS gene_name,p.default_sequence_id AS sequence_id,s.length,p.reviewed,
 p.entry_name,p.alternative_protein_names,
 ARRAY(SELECT g.hgnc_id FROM web.protein_gene g WHERE g.accession=p.accession ORDER BY g.hgnc_id) AS hgnc_ids
 FROM web.protein p LEFT JOIN web.protein_sequence s ON s.sequence_id=p.default_sequence_id'''


def get_protein(accession: str) -> dict:
    protein = one(PROTEIN_SQL + ' WHERE p.accession=:accession', {'accession': accession.upper()})
    if not protein:
        raise HTTPException(404, 'Protein is not present in this database snapshot.')
    protein['organism'] = 'human'
    return protein


@router.get('/health')
def health():
    ready = one("SELECT EXISTS(SELECT 1 FROM web.protein LIMIT 1) AS available, "
                "current_setting('transaction_read_only')='on' AS read_only")
    return {'status': 'ok' if ready['available'] else 'empty', 'database': 'PostgreSQL', 'read_only': ready['read_only']}


MEMBRANE_CLASSES = {
    'integral_membrane': 'Integral membrane',
    'transmembrane': 'Transmembrane',
    'single_pass': 'Single-pass transmembrane',
    'multi_pass': 'Multi-pass transmembrane',
    'lipid_anchored': 'Lipid-anchored',
    'peripheral_membrane': 'Peripheral membrane',
    'membrane_related': 'Membrane-related, mechanism unannotated',
}


MEMBRANE_LOCATIONS_SQL = """SELECT loc->'location'->>'id' AS id,
 loc->'location'->>'value' AS label,count(DISTINCT l.accession) AS count
 FROM web.protein_uniprot_location l
 CROSS JOIN LATERAL jsonb_array_elements(l.locations_json) loc
 WHERE l.scope_type='entry' AND loc->'location'->>'value' ILIKE '%membrane%'
 AND loc->'location'->>'id' IS NOT NULL
 GROUP BY 1,2 ORDER BY count DESC,label"""


@router.get('/catalog/summary')
def catalog_summary():
    counts = one('''SELECT
      count(*) FILTER (WHERE parent_class='integral_membrane') AS integral_membrane,
      count(*) FILTER (WHERE primary_class='transmembrane') AS transmembrane,
      count(*) FILTER (WHERE transmembrane_subclass='single_pass') AS single_pass,
      count(*) FILTER (WHERE transmembrane_subclass='multi_pass') AS multi_pass,
      count(*) FILTER (WHERE primary_class='lipid_anchored') AS lipid_anchored,
      count(*) FILTER (WHERE primary_class='peripheral_membrane') AS peripheral_membrane,
      count(*) FILTER (WHERE primary_class='membrane_related') AS membrane_related
      FROM web.protein_membrane_classification''')
    return {'total_proteins': one('SELECT count(*) AS count FROM web.protein')['count'],
            'locations': query(MEMBRANE_LOCATIONS_SQL),
            'location_source': 'UniProt', 'location_scope': 'entry',
            'classes': [{'key': key, 'label': name, 'count': counts.get(key, 0)}
                        for key, name in MEMBRANE_CLASSES.items()]}


@router.get('/proteins', response_model=ProteinSearch)
def proteins(query_text: str = Query('', alias='query', max_length=120),
             limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
             membrane_location: str = Query('', pattern=r'^(SL-[0-9]{4})?$'),
             membrane_class: Literal['', 'integral_membrane', 'transmembrane', 'single_pass', 'multi_pass',
                                     'lipid_anchored', 'peripheral_membrane', 'membrane_related'] = ''):
    term = query_text.strip()
    pattern = '%' + term.replace(chr(92), chr(92)*2).replace('%', chr(92)+'%').replace('_', chr(92)+'_') + '%'
    params = {'term': term, 'exact': term.upper(), 'pattern': pattern,
              'limit': limit + 1, 'offset': offset, 'membrane_class': membrane_class,
              'membrane_location': membrane_location,
              'location_context': json.dumps([{'location': {'id': membrane_location}}])}
    # Membership uses EXISTS: overlapping labels never duplicate protein entries.
    where = """ WHERE (:term='' OR p.accession ILIKE :pattern
      OR p.entry_name ILIKE :pattern OR p.protein_name ILIKE :pattern
      OR p.gene_names::text ILIKE :pattern OR p.alternative_protein_names::text ILIKE :pattern
      OR p.secondary_accessions::text ILIKE :pattern)
      AND (:membrane_class='' OR EXISTS(SELECT 1 FROM web.protein_membrane_classification m
        WHERE m.accession=p.accession AND CASE :membrane_class
          WHEN 'integral_membrane' THEN m.parent_class='integral_membrane'
          WHEN 'transmembrane' THEN m.primary_class='transmembrane'
          WHEN 'single_pass' THEN m.transmembrane_subclass='single_pass'
          WHEN 'multi_pass' THEN m.transmembrane_subclass='multi_pass'
          ELSE m.primary_class=:membrane_class END))
      AND (:membrane_location='' OR EXISTS(SELECT 1 FROM web.protein_uniprot_location l
        WHERE l.accession=p.accession AND l.scope_type='entry'
        AND l.locations_json @> CAST(:location_context AS jsonb)))"""
    rows = query(PROTEIN_SQL + where + """
      ORDER BY CASE WHEN p.accession=:exact THEN 0 WHEN p.gene_names ? :exact THEN 1 ELSE 2 END,
      p.accession LIMIT :limit OFFSET :offset""", params)
    total = one('SELECT count(*) AS total FROM web.protein p' + where, params)['total']
    return {'items': rows[:limit], 'has_more': len(rows) > limit, 'total': total}


GO_SQL = '''SELECT a.annotation_id,a.go_id,t.name,a.aspect,a.evidence_code,a.reference,
 a.relation,a.is_negative,a.form_id,a.subject_id,a.extension,a.mapping_status,t.url,
 a.term_status,t.is_obsolete,a.with_from,a.assigned_by,'GO' AS source,
 CASE WHEN a.evidence_code IN ('EXP','IDA','IPI','IMP','IGI','IEP','HTP','HDA','HMP','HGI','HEP')
 THEN 'experimental' ELSE 'other' END AS evidence_group
 FROM web.protein_go_annotation a LEFT JOIN web.go_term t USING(go_id)
 WHERE a.accession=:accession AND (:aspect='' OR a.aspect=:aspect)
 AND (:slim_id='' OR EXISTS(SELECT 1 FROM web.protein_go_slim s
   WHERE s.accession=a.accession AND s.annotation_id=a.annotation_id AND s.category_id=:slim_id))
 ORDER BY a.is_negative,CASE WHEN a.evidence_code IN ('EXP','IDA','IPI','IMP','IGI','IEP','HTP','HDA','HMP','HGI','HEP') THEN 0 ELSE 1 END,a.aspect,t.name,a.annotation_id'''
PATHWAY_SQL = '''SELECT a.association_id,a.pathway_id,p.name,a.relationship,a.evidence_code,
 a.mapping_status,p.source_url,a.source,
 COALESCE((SELECT jsonb_agg(jsonb_build_object('id',pt.topic_id,'name',t.name) ORDER BY t.name)
 FROM web.pathway_topic pt LEFT JOIN web.pathway t ON t.pathway_id=pt.topic_id AND t.source=pt.source
 WHERE pt.pathway_id=a.pathway_id AND pt.source=a.source),'[]'::jsonb) AS topics
 FROM web.protein_pathway a JOIN web.pathway p ON p.pathway_id=a.pathway_id AND p.source=a.source
 WHERE a.accession=:accession AND (:topic_id='' OR EXISTS(SELECT 1 FROM web.pathway_topic pt
   WHERE pt.pathway_id=a.pathway_id AND pt.source=a.source AND pt.topic_id=:topic_id))
 ORDER BY p.name,a.association_id'''
RHEA_SQL = '''SELECT a.association_id,a.rhea_id,r.master_id,r.direction,r.equation,r.is_transport,
 r.source_url,a.mapping_status,r.participants,'Rhea' AS source FROM web.protein_rhea_reaction a
 JOIN web.rhea_reaction r USING(rhea_id) WHERE a.accession=:accession ORDER BY a.rhea_id,a.association_id'''
PHARM_SQL = '''SELECT r.association_id,r.record_type,r.target_id,t.target_name,r.ligand_id,l.name AS ligand_name,'GtoPdb' AS source,
 l.type AS ligand_type,r.type,r.action,r.endogenous,r.affinity_units,r.affinity_median,
 r.affinity_high,r.affinity_low,r.original_affinity_relation,r.original_affinity_units,
 r.original_affinity_median_nm,r.pubmed_id,r.interaction_parameter,r.interaction_value,
 r.interaction_pubmed_ids,r.assay_description,l.source_url AS ligand_url,t.source_url AS target_url,
 (SELECT jsonb_agg(c) FROM jsonb_array_elements(r.protein_contexts) c WHERE c->>'accession'=:accession) AS protein_contexts
 FROM web.gtopdb_record r LEFT JOIN web.gtopdb_target t USING(target_id)
 LEFT JOIN web.gtopdb_ligand l USING(ligand_id)
 WHERE r.protein_contexts @> CAST(:context AS jsonb)
 AND (:record_type='' OR r.record_type=:record_type) ORDER BY l.name,r.association_id'''


def page(sql: str, params: dict, limit: int, offset: int = 0) -> dict:
    rows = query(sql + ' LIMIT :limit OFFSET :offset', {**params, 'limit': limit + 1, 'offset': offset})
    return {'items': rows[:limit], 'has_more': len(rows) > limit, 'limit': limit, 'offset': offset}


@router.get('/proteins/{accession}/overview/{section}')
def overview_section(accession: str, section: Literal['go', 'pathways', 'rhea', 'pharmacology'],
                     limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
                     aspect: Literal['', 'F', 'P', 'C'] = '',slim_id:str=Query('',max_length=30),topic_id:str=Query('',max_length=100),
                     record_type:Literal['','pharmacological_record','endogenous_pairing','endogenous_detail']=''):
    protein = get_protein(accession)
    params = {'accession': protein['accession'], 'aspect': aspect,'slim_id':slim_id,'topic_id':topic_id,'record_type':record_type,
              'context': json.dumps([{'accession': protein['accession']}])}
    sql={'go': GO_SQL, 'pathways': PATHWAY_SQL, 'rhea': RHEA_SQL, 'pharmacology': PHARM_SQL}[section]
    result=page(sql,params,limit,offset)
    if section in ('go','pathways','pharmacology'):
        # Count the same complete filtered projection, before pagination.
        result['total']=one('SELECT count(*) total FROM ('+sql.rsplit(' ORDER BY ',1)[0]+') counted',params)['total']
        result['count_unit']=('source_annotation_records' if section=='go' else
                              'source_pathway_association_records' if section=='pathways' else
                              'source_pharmacology_records')
    return result


@router.get('/proteins/{accession}/overview/go/summary')
def go_summary(accession:str):
    return go_summary_data(get_protein(accession)['accession'])


@router.get('/proteins/{accession}/overview/pathways/summary')
def pathways_summary(accession:str):
    return pathway_summary_data(get_protein(accession)['accession'])


@router.get('/proteins/{accession}/overview/pharmacology/summary')
def pharmacology_summary(accession: str):
    protein = get_protein(accession)
    params = {'context': json.dumps([{'accession': protein['accession']}])}
    where = "protein_contexts @> CAST(:context AS jsonb)"
    totals = one(f'''SELECT count(*) record_count,count(DISTINCT ligand_id) ligand_count,
        count(*) FILTER(WHERE record_type='pharmacological_record') pharmacological_record_count,
        count(DISTINCT ligand_id) FILTER(WHERE record_type='pharmacological_record') pharmacological_ligand_count
        FROM web.gtopdb_record WHERE {where}''', params)
    record_types = query(f'''SELECT record_type value,count(*) count,count(DISTINCT ligand_id) ligand_count
        FROM web.gtopdb_record WHERE {where} GROUP BY record_type ORDER BY record_type''', params)
    types = query(f'''SELECT COALESCE(NULLIF(BTRIM(type),''),'Not stated') value,count(*) count,
        count(DISTINCT ligand_id) ligand_count FROM web.gtopdb_record WHERE {where}
        AND record_type='pharmacological_record' GROUP BY 1 ORDER BY count DESC,value''', params)
    actions = query(f'''SELECT COALESCE(NULLIF(BTRIM(action),''),'Not stated') value,count(*) count,
        count(DISTINCT ligand_id) ligand_count FROM web.gtopdb_record WHERE {where}
        AND record_type='pharmacological_record' GROUP BY 1 ORDER BY count DESC,value''', params)
    return {'totals': totals, 'record_types': record_types, 'types': types, 'actions': actions,
            'scope': 'Complete Guide to Pharmacology records linked to this protein in the current snapshot.',
            'notes': ['Type and action distributions use pharmacological_record rows only.',
                      'Endogenous pairing and detail rows remain separate record categories.',
                      'Distinct ligand counts do not imply independent experiments.']}


@router.get('/proteins/{accession}/overview', response_model=Overview)
def overview(accession: str):
    protein = get_protein(accession)
    params = {'accession': protein['accession'], 'aspect': '', 'slim_id':'','topic_id':'','record_type':'','context': json.dumps([{'accession': protein['accession']}])}
    function = one('''SELECT o.status,a.annotation_id,a.text,a.scope_type,a.scope_label,a.isoform_ids,'UniProt' AS source
      FROM web.protein_function_overview o LEFT JOIN web.protein_function_annotation a
      ON a.annotation_id=o.default_annotation_id WHERE o.accession=:accession''', params)
    annotations = query('''SELECT annotation_id,comment_type,scope_type,scope_label,isoform_ids,mapping_status,text,'UniProt' AS source,
      structured_items_json AS details FROM web.protein_function_annotation WHERE accession=:accession ORDER BY source_order''', params)
    isoforms = query('''SELECT i.isoform_id,i.isoform_name,i.is_canonical,i.sequence_available,i.sequence_availability_reason,
      i.sequence_ids,ARRAY(SELECT s.length FROM web.protein_sequence s WHERE i.sequence_ids ? s.sequence_id ORDER BY s.sequence_id) AS lengths
      FROM web.protein_isoform i WHERE accession=:accession ORDER BY isoform_order''', params)
    refs = query('''SELECT database_name,external_id,identifier_type,url,gene_id_full,protein_id_full,transcript_id_full,
      gene_url,protein_url,transcript_url,scope_type,scope_id FROM web.protein_external_reference_all
      WHERE accession=:accession ORDER BY database_name,external_id''', params)
    labels = query("SELECT label,sequence_id,supporting_records,'UniProt' AS source FROM web.protein_membrane_label WHERE accession=:accession ORDER BY label", params)
    classification = one('''SELECT accession,sequence_id,primary_class,parent_class,transmembrane_subclass,
      canonical_tm_feature_count,primary_evidence_label,evidence_labels,classification_rule,rule_version
      FROM web.protein_membrane_classification WHERE accession=:accession''', params)
    label_names = {'integral_membrane': 'Integral membrane protein', 'peripheral_membrane': 'Peripheral membrane protein',
                   'lipid_anchored': 'Lipid-anchored protein', 'membrane_related': 'Membrane-related protein'}
    for item in labels:
        item['label_name'] = label_names.get(item['label'], item['label'])
    uniprot = query('''SELECT annotation_id,scope_type,scope_label,isoform_ids,mapping_status,locations_json AS locations,note_json AS notes,'UniProt' AS source
      FROM web.protein_uniprot_location WHERE accession=:accession ORDER BY source_order''', params)
    hpa = query('''SELECT "Gene" AS gene_id,"Reliability" AS reliability,"Main location" AS main_location,
      "Additional location" AS additional_location,"Enhanced" AS enhanced,"Supported" AS supported,
      "Approved" AS approved,"Uncertain" AS uncertain,url,'HPA' AS source,'gene' AS scope_type FROM web.hpa_subcellular_location
      WHERE protein_contexts @> CAST(:context AS jsonb) ORDER BY "Gene"''', params)
    go_summary=go_summary_data(protein['accession'])
    pathway_summary=pathway_summary_data(protein['accession'])
    return {'protein': protein, 'function': function or {'status': 'no_function_annotation', 'text': None},
            'annotations': annotations, 'isoforms': isoforms, 'external_references': refs, 'membrane_labels': labels,
            'membrane_classification': classification,
            'go': {**page(GO_SQL, params, 30),'total':go_summary['totals']['annotation_count']}, 'go_slim': go_summary['categories'],
            'pathways': {**page(PATHWAY_SQL, params, 15),'total':pathway_summary['totals']['association_count']},
            'locations': {'uniprot': uniprot, 'hpa': hpa}, 'rhea': page(RHEA_SQL, params, 10),
            'pharmacology': page(PHARM_SQL, params, 15)}
