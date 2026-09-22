"""Protein-level views of original topology records; no new topology consensus."""
import json
import xml.etree.ElementTree as ET
from fastapi import APIRouter, HTTPException, Query
from typing import Literal
from .db import one, query
from .variant_support import protein_identity

router = APIRouter()

SOURCES = """SELECT source_sequence_id,record_id,dataset_id,native_id,chain_id,actual_length
 FROM web.membrane_topology_source WHERE protein_contexts @> CAST(:context AS jsonb)"""


def topology_records(accession, sequence_id):
    params = {'context': json.dumps([{'accession': accession}]), 'sequence_id': sequence_id}
    rows = query("""WITH sources AS MATERIALIZED (""" + SOURCES + """), mapped AS (
      SELECT feature_id,min(start) start,max("end") "end",count(*) blocks,
        array_agg(DISTINCT mapping_status) statuses
      FROM web.membrane_topology_location WHERE sequence_id=:sequence_id GROUP BY feature_id)
      SELECT s.source_sequence_id,s.record_id,s.dataset_id AS source,s.native_id,s.chain_id,s.actual_length,
        count(f.feature_id) feature_count,count(m.feature_id) mapped_feature_count,
        count(*) FILTER(WHERE f.role='experimental_evidence') experimental_regions,
        count(*) FILTER(WHERE f.role='constraint') constraint_regions,
        count(*) FILTER(WHERE f.role='structure_region') structure_regions,
        coalesce(array_agg(DISTINCT f.method ORDER BY f.method) FILTER(WHERE f.role='method_prediction' AND f.method IS NOT NULL),'{}') methods,
        coalesce(array_agg(DISTINCT f.method ORDER BY f.method) FILTER(WHERE f.role='constraint' AND f.method IS NOT NULL),'{}') constraint_sources,
        coalesce(jsonb_agg(jsonb_build_object('id',f.feature_id,'type',f.native_type,
          'start',f.start,'end',f."end",'attributes',f.raw_attributes->'parent_attributes',
          'canonical_start',m.start,'canonical_end',m."end",'mapped_blocks',m.blocks,
          'mapping_statuses',m.statuses) ORDER BY f.start,f."end",f.feature_id)
          FILTER(WHERE f.role='integrated_topology'),'[]'::jsonb) integrated_segments
      FROM sources s LEFT JOIN web.membrane_topology_feature f
        ON f.record_id=s.record_id AND f.source_sequence_id=s.source_sequence_id
      LEFT JOIN mapped m ON m.feature_id=f.feature_id
      GROUP BY s.source_sequence_id,s.record_id,s.dataset_id,s.native_id,s.chain_id,s.actual_length
      ORDER BY CASE s.dataset_id WHEN 'HTP' THEN 0 WHEN 'TOPDB' THEN 1
        WHEN 'TmAlphaFold/cctop' THEN 2 ELSE 3 END,s.dataset_id,s.native_id,s.chain_id NULLS FIRST,s.source_sequence_id""", params)
    for row in rows:
        tm, reliability = [], []
        for segment in row['integrated_segments']:
            attributes = segment.pop('attributes', None) or {}
            for key, value in attributes.items():
                dest = tm if key.lower() == 'numtm' else reliability if key.lower() == 'reliability' else None
                if dest is not None and value is not None and value not in dest:
                    dest.append(value)
        row['reported_tm_counts'] = tm
        row['reliability_values'] = reliability
        row['signal_region_reported'] = any(s['type'] in ('S', 'Signal') for s in row['integrated_segments'])
        row['mapping_note'] = ('Some source features map to the current canonical sequence.'
                               if row['mapped_feature_count'] else
                               'Protein identity link only; no mapped feature on this canonical sequence.')
    return rows


def parse_topology_evidence(attributes):
    """Unpack explicit source XML fields without treating each region as an experiment."""
    xml = attributes.get('evidence_xml')
    if not xml:
        return [], 'not_supplied'
    try:
        root = ET.fromstring(xml)
    except (ET.ParseError, ValueError):
        return [], 'unparsed'
    results = []
    for exp in root.iter():
        if exp.tag.rsplit('}', 1)[-1] != 'Exp':
            continue
        text = lambda name: next((' '.join(e.itertext()).strip() for e in exp
                                  if e.tag.rsplit('}', 1)[-1] == name), None)
        pdbs = []
        for node in exp.iter():
            if node.tag.rsplit('}', 1)[-1] == 'pdbRef':
                pdbs.append({'id': node.get('ID'), 'chains': [c.get('ID') for c in node.iter()
                             if c.tag.rsplit('}', 1)[-1] == 'Chain' and c.get('ID')]})
        results.append({'type': text('Type'), 'subtype': text('Subtype'), 'reference': exp.get('Ref'),
                        'value': text('Value'), 'structures': pdbs})
    return results, 'parsed' if results else 'no_experiment_element'


@router.get('/proteins/{accession}/overview/membrane/topology')
def topology_details(accession: str, source_sequence_id: str = Query(..., max_length=120),
                     role: Literal['', 'integrated_topology', 'method_prediction', 'constraint', 'experimental_evidence', 'structure_region'] = '',
                     method: str = Query('', max_length=120), limit: int = Query(20, ge=1, le=100),
                     offset: int = Query(0, ge=0, le=100000)):
    protein = protein_identity(accession)
    params = {'context': json.dumps([{'accession': protein['accession']}]), 'id': source_sequence_id,
              'sequence_id': protein['sequence_id'], 'role': role, 'method': method,
              'limit': limit + 1, 'offset': offset}
    source = one(SOURCES + ' AND source_sequence_id=:id', params)
    if not source:
        raise HTTPException(404, 'No source record is associated with this protein.')
    params['record_id'] = source['record_id']
    where = """ FROM web.membrane_topology_feature f WHERE f.record_id=:record_id
      AND f.source_sequence_id=:id AND (:role='' OR f.role=:role) AND (:method='' OR f.method=:method)"""
    total = one('SELECT count(*) total' + where, params)['total']
    rows = query('SELECT f.feature_id,f.role,f.method,f.native_type,f.model_id,f.start,f."end",f.coordinate_status,f.raw_attributes' + where +
                 ' ORDER BY f.start NULLS LAST,f."end" NULLS LAST,f.feature_id LIMIT :limit OFFSET :offset', params)
    ids = [r['feature_id'] for r in rows[:limit]]
    locations = query('''SELECT feature_id,start,"end",mapping_status FROM web.membrane_topology_location
      WHERE feature_id=ANY(:ids) AND sequence_id=:sequence_id ORDER BY feature_id,block_index''',
      {'ids': ids, 'sequence_id': protein['sequence_id']}) if ids else []
    domains = query('''SELECT feature_id,model_database,model_id,side,support_raw
      FROM web.membrane_topology_domain WHERE feature_id=ANY(:ids) ORDER BY feature_id,model_record_id''', {'ids': ids}) if ids else []
    for row in rows[:limit]:
        raw = row.pop('raw_attributes') or {}
        row['source_attributes'] = {k: v for k, v in raw.items() if k != 'evidence_xml'}
        row['evidence'], row['evidence_status'] = parse_topology_evidence(raw)
        row['locations'] = [l for l in locations if l['feature_id'] == row['feature_id']]
        row['domains'] = [d for d in domains if d['feature_id'] == row['feature_id']]
    return {'source': source, 'sequence_id': protein['sequence_id'], 'items': rows[:limit],
            'total': total, 'has_more': len(rows) > limit, 'offset': offset, 'limit': limit,
            'coordinate_note': 'Start/end refer to the original source sequence. Canonical positions require explicit mapping.'}
