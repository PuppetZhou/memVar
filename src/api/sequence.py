"""Canonical coordinates only; detailed source records stay available on demand."""
from __future__ import annotations

from collections import defaultdict
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .core import get_protein, page
from .db import one, query

router = APIRouter(prefix='/api/proteins', tags=['sequence'])
MEMBRANE_TYPES = {'Transmembrane', 'Intramembrane', 'Topological domain'}


class SequenceView(BaseModel):
    sequence_id: str
    sequence: str
    length: int
    tracks: list[dict[str, Any]]
    conservation: list[dict[str, Any]]
    conservation_summary: dict[str, Any] | None
    topology_options: list[dict[str, Any]]
    annotation_source_options: dict[str, list[dict[str, Any]]]
    selected_topology: list[str]
    unmapped_ptm: dict[str, Any]
    unlocated_features: list[dict[str, Any]]
    coordinate_system: str = '1-based inclusive, canonical sequence'
    status: str = 'available'


UNMAPPED_SQL = '''SELECT r.record_id,r.source_record_id,split_part(r.dataset_id,':',1) AS source,r.source_type,
 r.description,r.source_start,r.source_end,r.source_sequence_id,r.mapping_status,r.evidence_status,
 r.identity_status,r.candidate_accessions,r.details_json AS details,
 CASE WHEN r.accession=:accession THEN 'protein_associated' ELSE 'candidate_protein_association' END AS association_status,
 COALESCE((SELECT jsonb_agg(jsonb_build_object('namespace',e.namespace,'identifier',e.identifier,'url',e.url,'kind',e.evidence_kind,'is_current',e.is_current))
  FROM web.ptm_evidence_all e WHERE e.record_id=r.record_id),'[]'::jsonb) AS evidence
 FROM web.ptm_record_detail r WHERE (r.accession=:accession OR (r.accession IS NULL AND r.candidate_accessions ? :accession))
 AND r.dataset_id NOT LIKE 'PTMD2:%'
 AND (:source='' OR split_part(r.dataset_id,':',1)=:source)
 AND NOT EXISTS (SELECT 1 FROM web.ptm_record_site l WHERE l.record_id=r.record_id)
 ORDER BY r.dataset_id,r.record_id'''


def sequence_params(accession: str) -> tuple[dict, dict]:
    protein = get_protein(accession)
    if not protein['sequence_id']:
        raise HTTPException(404, 'No canonical sequence is available for this protein.')
    return protein, {'accession': protein['accession'], 'sequence_id': protein['sequence_id'], 'source': ''}


@router.get('/{accession}/sequence/unmapped-ptm')
@router.get('/{accession}/sequence/unmapped')
def unmapped_ptm(accession: str, source: str = Query('', max_length=60),
                limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    _, params = sequence_params(accession)
    params['source'] = source
    return {**page(UNMAPPED_SQL, params, limit, offset),
            'status': 'protein_association_without_verified_site',
            'source_options': ['UniProt', 'dbPTM', 'ProteomeScout', 'GlyGen']}


@router.get('/{accession}/sequence', response_model=SequenceView)
def sequence(accession: str, topology: list[str] = Query(default=['uniprot'])):
    selected_topology = list(dict.fromkeys(topology))
    if selected_topology == ['none']:
        selected_topology = []
    if len(selected_topology) > 20 or any(not value or len(value) > 1000 for value in selected_topology):
        raise HTTPException(422, 'Too many or invalid topology selections.')
    protein, params = sequence_params(accession)
    seq = one('SELECT sequence,length FROM web.protein_sequence WHERE sequence_id=:sequence_id', params)
    if not seq:
        raise HTTPException(404, 'Canonical sequence is unavailable.')
    source_features = query('''SELECT feature_id AS id,start,"end",label,source_type,feature_group,
      description,location_kind,start_modifier,end_modifier,coordinate_status,can_locate_exactly,mapping_status
      FROM web.sequence_uniprot_feature WHERE accession=:accession AND sequence_id=:sequence_id
      ORDER BY start,"end",source_order''', params)
    buckets = {'domains': [], 'secondary': [], 'membrane': [], 'function': []}
    unlocated = []
    for feature in source_features:
        feature['source'] = 'UniProt'
        if not feature['can_locate_exactly'] or feature['start'] is None or feature['end'] is None:
            unlocated.append(feature)
            continue
        if feature['feature_group'] == 'ptm':
            continue  # PTM native records are already represented via record_site.
        group = ('membrane' if feature['source_type'] in MEMBRANE_TYPES else
                 'function' if feature['feature_group'] == 'functional_site' else
                 'secondary' if feature['feature_group'] == 'secondary_structure' else 'domains')
        buckets[group].append(feature)
    pfam = query('''SELECT h.hit_id AS id,h.ali_start AS start,h.ali_end AS "end",e.pfam_id AS label,
      e.description,h.pfam_accession,h.env_start,h.env_end,h.hmm_start,h.hmm_end,h.domain_i_evalue,
      h.domain_score,e.entry_type AS source_type,'Pfam' AS source,'alignment' AS boundary_type
      FROM web.pfam_hit h JOIN web.pfam_entry e USING(pfam_accession) WHERE h.sequence_id=:sequence_id
      ORDER BY h.ali_start,h.ali_end,h.hit_id''', params)
    buckets['domains'].extend(pfam)
    ptm_rows = query('''SELECT position,residue,record_id,endpoint_role,dataset_id,source_type,
      description,evidence_status FROM web.sequence_ptm_site WHERE sequence_id=:sequence_id
      AND dataset_id NOT LIKE 'PTMD2:%' ORDER BY position,record_id''', params)
    # A compact marker groups records at one position only, preserving all source
    # record IDs and bond endpoint roles; it never creates a filled bond interval.
    ptm_groups = {}
    for row in ptm_rows:
        key = (row['position'], row['source_type'], row['dataset_id'])
        if key not in ptm_groups:
            ptm_groups[key] = {'id': '|'.join(map(str, key)), 'start': row['position'], 'end': row['position'],
                'label': row['source_type'], 'source_type': row['source_type'],
                'source': row['dataset_id'].split(':')[0], 'record_ids': [], 'endpoint_roles': []}
        feature = ptm_groups[key]
        if row['record_id'] not in feature['record_ids']:
            feature['record_ids'].append(row['record_id'])
        if row['endpoint_role'] not in feature['endpoint_roles']:
            feature['endpoint_roles'].append(row['endpoint_role'])
    for feature in ptm_groups.values():
        feature['record_count'] = len(feature['record_ids'])
    topology_rows = query('''SELECT l.feature_id AS id,l.start,l."end",f.dataset_id AS source,f.record_id,
      f.source_sequence_id,f.role,f.method,f.native_type AS label,f.native_type AS source_type,f.model_id,
      l.mapping_status FROM web.membrane_topology_location l
      JOIN web.membrane_topology_feature f ON f.feature_id=l.feature_id AND f.dataset_id=l.dataset_id
      WHERE l.sequence_id=:sequence_id AND l.start IS NOT NULL AND l."end" IS NOT NULL
      AND f.role <> 'constraint' ORDER BY f.dataset_id,f.record_id,f.method,l.start''', params)
    topology_groups = defaultdict(list)
    for feature in topology_rows:
        key = json.dumps([feature['source'], feature['record_id'], feature['source_sequence_id'],
                          feature['role'], feature['method'], feature['model_id']], separators=(',', ':'))
        topology_groups[key].append(feature)
    options = [{'id': 'uniprot', 'label': 'UniProt · Source annotation', 'source': 'UniProt',
                'kind': 'source_annotation', 'count': len(buckets['membrane']), 'available': True}]
    role_labels = {'integrated_topology': 'Integrated topology', 'experimental_evidence': 'Experimental evidence',
                   'method_prediction': 'Prediction', 'structure_region': 'Structure-derived',
                   'source_annotation': 'Source annotation'}
    labels = defaultdict(list)
    for key, features in topology_groups.items():
        f = features[0]
        readable = ' · '.join(str(v) for v in [f['source'], f['method'], role_labels.get(f['role'], f['role'].replace('_', ' '))] if v)
        option = {'id': key, 'label': readable, 'source': f['source'], 'kind': f['role'],
                  'method': f['method'], 'source_record_id': f['record_id'],
                  'source_sequence_id': f['source_sequence_id'], 'model_id': f['model_id'],
                  'count': len(features), 'available': True}
        labels[readable].append(option)
        options.append(option)
    for same_label in labels.values():
        if len(same_label) > 1:
            for index, option in enumerate(same_label, 1):
                option['label'] += f' · Record {index}'
    prediction = one('''SELECT status,protein_type,mapping_status FROM web.deeptmhmm2_prediction
      WHERE sequence_id=:sequence_id''', params)
    if prediction and prediction['status'] == 'ok' and prediction['mapping_status'] == 'input_sequence_exact':
        options.append({'id': 'deeptmhmm2', 'label': 'DeepTMHMM2 · Prediction', 'source': 'DeepTMHMM2',
                        'kind': 'prediction', 'available': True})
    option_by_id = {option['id']: option for option in options}
    unknown = [value for value in selected_topology if value not in option_by_id]
    if unknown:
        raise HTTPException(422, 'A selected topology record is not available for the canonical sequence.')
    membrane_features = []
    for topology_id in selected_topology:
        option = option_by_id[topology_id]
        if topology_id == 'uniprot':
            features = buckets['membrane']
        elif topology_id == 'deeptmhmm2':
            features = query('''SELECT segment_order::text AS id,start,"end",name AS label,
              name AS source_type,'DeepTMHMM2' AS source,'prediction' AS evidence_kind
              FROM web.deeptmhmm2_segment WHERE sequence_id=:sequence_id ORDER BY segment_order''', params)
            option['count'] = len(features)
        else:
            features = topology_groups[topology_id]
        for feature in features:
            membrane_features.append({**feature, 'topology_id': topology_id,
                                      'topology_label': option['label'], 'topology_kind': option['kind']})
    buckets['membrane'] = membrane_features
    conservation = query('''SELECT position,jsd_conservation AS value,legacy_confidence AS status,
      occupancy,gap_frequency,n_nongap,nonstandard_residue FROM web.residue_conservation
      WHERE sequence_id=:sequence_id ORDER BY position''', params)
    summary = one('''SELECT dataset_id,filtered_sequence_count,median_occupancy,alignment_scope,
      low_depth,confidence,n_sequences,homology_status FROM web.conservation_sequence WHERE sequence_id=:sequence_id''', params)
    tracks = [{'id': 'ptm', 'label': 'PTM', 'type': 'site', 'color': '#a46dba', 'features': list(ptm_groups.values())},
              {'id': 'domains', 'label': 'Domains & regions', 'type': 'region', 'color': '#509887', 'features': buckets['domains']},
              {'id': 'secondary', 'label': 'Secondary structure · UniProt', 'type': 'region', 'color': '#d7a453', 'group': 'domains', 'features': buckets['secondary']},
              {'id': 'membrane', 'label': 'Membrane topology', 'type': 'region', 'color': '#6388b2', 'features': buckets['membrane']},
              {'id': 'function', 'label': 'Function sites', 'type': 'site', 'color': '#d58076', 'features': buckets['function']}]
    source_options = {
        'domains': [{'id': source, 'label': source, 'source': source, 'kind': 'source_annotation',
                     'count': sum(feature.get('source') == source for feature in buckets['domains']),
                     'available': True} for source in ('UniProt', 'Pfam')],
        'ptm': [{'id': source, 'label': source, 'source': source, 'kind': 'source_annotation',
                 'count': sum(feature.get('source') == source for feature in ptm_groups.values()),
                 'available': True} for source in ('UniProt', 'dbPTM', 'GlyGen', 'ProteomeScout')],
        'topology': options,
    }
    return {'sequence_id': protein['sequence_id'], 'sequence': seq['sequence'], 'length': seq['length'],
            'tracks': tracks, 'conservation': conservation, 'conservation_summary': summary,
            'topology_options': options, 'annotation_source_options': source_options,
            'selected_topology': selected_topology,
            'unmapped_ptm': {**page(UNMAPPED_SQL, params, 10), 'status': 'protein_association_without_verified_site'},
            'unlocated_features': unlocated}


@router.get('/{accession}/sites/{position}')
def site(accession: str, position: int, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    protein, params = sequence_params(accession)
    if position < 1 or position > protein['length']:
        raise HTTPException(422, 'Position is outside the canonical sequence.')
    params['position'] = position
    residue = one('SELECT substring(sequence FROM :position FOR 1) AS residue FROM web.protein_sequence WHERE sequence_id=:sequence_id', params)
    features = query('''SELECT feature_id AS id,start,"end",source_type,label,description,details_json AS details,
      evidences,coordinate_status,start_modifier,end_modifier FROM web.sequence_uniprot_feature
      WHERE accession=:accession AND sequence_id=:sequence_id AND feature_group<>'ptm'
      AND start<=:position AND "end">=:position AND can_locate_exactly ORDER BY source_order''', params)
    ptm = page('''SELECT r.record_id,split_part(r.dataset_id,':',1) AS source,r.source_type,
      r.description,r.evidence_status,r.mapping_status,r.details_json AS details,l.endpoint_role,
      COALESCE((SELECT jsonb_agg(jsonb_build_object('namespace',e.namespace,'identifier',e.identifier,'url',e.url,'kind',e.evidence_kind,'is_current',e.is_current))
       FROM web.ptm_evidence_all e WHERE e.record_id=r.record_id),'[]'::jsonb) AS evidence
      FROM web.sequence_site s JOIN web.ptm_record_site l USING(site_id)
      JOIN web.ptm_record_detail r USING(record_id)
      WHERE s.sequence_id=:sequence_id AND s.position=:position AND r.dataset_id NOT LIKE 'PTMD2:%'
      ORDER BY r.dataset_id,r.record_id,l.endpoint_role''', params, limit, offset)
    pfam = query('''SELECT h.hit_id,h.pfam_accession,e.pfam_id,e.description,h.ali_start,h.ali_end,h.env_start,h.env_end,
      h.hmm_start,h.hmm_end,h.domain_i_evalue,h.domain_score,'alignment' AS displayed_boundary
      FROM web.pfam_hit h JOIN web.pfam_entry e USING(pfam_accession)
      WHERE h.sequence_id=:sequence_id AND h.ali_start<=:position AND h.ali_end>=:position ORDER BY h.ali_start,h.hit_id''', params)
    conservation = one('''SELECT position,jsd_conservation AS value,occupancy,gap_frequency,n_nongap,legacy_confidence AS status,
      nonstandard_residue FROM web.residue_conservation WHERE sequence_id=:sequence_id AND position=:position''', params)
    contacts = {
        'opm': query('''SELECT pdb_id,model_id,local_chain_id AS chain_id,pdb_resseq,insertion_code,pdb_residue,target_residue,
          is_wildtype_residue,geometry_type,site_coordinate_basis,"site_signed_depth_A","distance_to_boundary_A",heavy_atom_fraction_in_core,mapping_status,mapping_method
          FROM web.membrane_opm_observation WHERE sequence_id=:sequence_id AND target_position=:position
          AND mapping_status='mapped' ORDER BY source_observation_id LIMIT 51''', params),
        'mplid': query('''SELECT pdb_id,chain_id,residue_number,insertion_code,source_aa,target_residue,is_wildtype_residue,
          is_contact,label_source,confidence,min_distance,mapping_status,mapping_method
          FROM web.membrane_mplid_residue WHERE sequence_id=:sequence_id AND target_position=:position
          AND mapping_status='mapped' ORDER BY source_member,source_row LIMIT 51''', params),
        'biodolphin': query('''SELECT s.interaction_id,s.site_order,s.coordinate_system,s.pdb_id,s.source_chain_id,s.residue_number,
          s.insertion_code,s.residue_name,s.target_residue,s.is_wildtype_residue,s.mapping_status,s.mapping_method,
          b."lipid_PDB_Name" AS ligand_name,b."lipid_Ligand_ID_CCD" AS ligand_id,b."lipid_pharmacological_class" AS pharmacological_class
          FROM web.membrane_biodolphin_site s JOIN web.membrane_biodolphin_interaction b USING(interaction_id)
          WHERE s.sequence_id=:sequence_id AND s.target_position=:position AND s.mapping_status='mapped'
          ORDER BY s.interaction_id,s.site_order LIMIT 51''', params)}
    contact_more = {key: len(rows) > 50 for key, rows in contacts.items()}
    return {'sequence_id': protein['sequence_id'], 'position': position, 'residue': residue['residue'],
            'features': features, 'ptm': ptm['items'], 'ptm_pagination': {k: v for k, v in ptm.items() if k != 'items'},
            'pfam': pfam, 'conservation': conservation, 'membrane_contacts': {k: v[:50] for k, v in contacts.items()},
            'membrane_contacts_has_more': contact_more}
