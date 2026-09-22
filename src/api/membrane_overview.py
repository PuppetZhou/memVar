"""Source-preserving canonical membrane overview and paged structural observations."""
from collections import Counter
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, Query

from .db import one, query
from .evidence_common import fields
from .variant_support import protein_identity
from .membrane_topology import topology_records, router as topology_router

router = APIRouter()
router.include_router(topology_router)

FEATURE_COUNTS = {
    'Transmembrane': 'transmembrane_features',
    'Intramembrane': 'intramembrane_features',
    'Topological domain': 'topological_domains',
}
LABEL_NAMES = {
    'integral_membrane': 'Integral membrane protein',
    'peripheral_membrane': 'Peripheral membrane protein',
    'lipid_anchored': 'Lipid-anchored protein',
    'membrane_related': 'Membrane-related protein',
}
OBSERVATION_TABLES = {
    'OPM': 'membrane_opm_observation',
    'MPLID': 'membrane_mplid_residue',
    'BioDolphin': 'membrane_biodolphin_site',
}
OBSERVATION_NOTES = {
    'OPM': [
        'Each row is one source structure/model/chain residue geometry observation, not one membrane crossing.',
        'Signed depth is positive inside the source membrane core and negative outside; its sign is not a cytoplasmic/extracellular side label.',
        'Original geometry type and coordinate basis apply to each value; structures and chain copies are not averaged.',
    ],
    'MPLID': [
        'Each row is one source structure-chain residue record, including both contact and non-contact labels.',
        'min_distance is the original distance to the source candidate ligand set in angstroms; this source has no per-contact ligand identity.',
    ],
    'BioDolphin': [
        'Each row is a mapped source site token for a protein-chain/ligand instance.',
        'PDB and Re-numbered coordinates can describe the same binding residue; rows are not independent binding events.',
        'Source ligands include lipid-like and other compounds; these records are not all membrane-lipid contacts.',
    ],
}


@lru_cache(maxsize=96)
def membrane_summary_data(accession: str):
    protein = protein_identity(accession)
    params = {'accession': protein['accession'], 'sequence_id': protein['sequence_id']}
    labels = query('''SELECT label,sequence_id,supporting_records,'UniProt' source
        FROM web.protein_membrane_label WHERE accession=:accession
        AND sequence_id=:sequence_id ORDER BY label''', params)
    classification = one('''SELECT accession,sequence_id,primary_class,parent_class,transmembrane_subclass,
        canonical_tm_feature_count,primary_evidence_label,evidence_labels,classification_rule,rule_version
        FROM web.protein_membrane_classification WHERE accession=:accession AND sequence_id=:sequence_id''', params)
    for label in labels:
        label['label_name'] = LABEL_NAMES.get(label['label'], label['label'])
    features = query('''SELECT feature_id id,source_type,start,"end",description,label,
        source_record_id,source_feature_id,source_sequence_id,sequence_scope,mapping_status,
        location_kind,start_modifier,end_modifier,coordinate_status,can_locate_exactly,
        interpretation_status,evidences evidence,'UniProt' source
        FROM web.sequence_uniprot_feature WHERE accession=:accession AND sequence_id=:sequence_id
        AND source_type IN ('Transmembrane','Intramembrane','Topological domain')
        ORDER BY start NULLS LAST,"end" NULLS LAST,source_order,feature_id''', params)
    counts = {key: 0 for key in FEATURE_COUNTS.values()}
    locatable_counts = counts.copy()
    for feature in features:
        key = FEATURE_COUNTS[feature['source_type']]
        counts[key] += 1
        if feature['can_locate_exactly'] and feature['start'] is not None and feature['end'] is not None:
            locatable_counts[key] += 1
    prediction = one('''SELECT status,mapping_status,sequence_length,protein_type,tm_helix_count,
        beta_strand_count,has_signal_peptide,has_transit_peptide,membrane_type_applicable,
        membrane_types,membrane_selection_method,membrane_probabilities_json membrane_probabilities
        FROM web.deeptmhmm2_prediction WHERE sequence_id=:sequence_id''', params)
    if prediction is None:
        prediction = {'status': 'no_local_prediction', 'mapping_status': None, 'protein_type': None,
                      'membrane_types': None, 'has_signal_peptide': None}
    segments = query('''SELECT segment_order,name,start,"end" FROM web.deeptmhmm2_segment
        WHERE sequence_id=:sequence_id ORDER BY segment_order''', params)
    prediction.update(source='DeepTMHMM2', evidence_kind='prediction', segments=segments,
                      segment_counts=dict(Counter(row['name'] for row in segments)),
                      can_locate_exactly=(prediction['status'] == 'ok' and
                                          prediction['mapping_status'] == 'input_sequence_exact'),
                      scope='Original prediction for this sequence; no agreement or consensus with UniProt is inferred.')
    topology = query('''SELECT f.dataset_id source,f.role,f.method,
        count(DISTINCT f.record_id) records,count(DISTINCT f.feature_id) mapped_features,
        count(*) mapped_blocks,array_agg(DISTINCT l.mapping_status) mapping_statuses
        FROM web.membrane_topology_location l JOIN web.membrane_topology_feature f USING(feature_id,dataset_id)
        WHERE l.sequence_id=:sequence_id GROUP BY f.dataset_id,f.role,f.method
        ORDER BY f.dataset_id,f.role,f.method NULLS FIRST''', params)
    # Fixed source tables only. Each aggregate uses the existing sequence_id index;
    # no cross-protein materialization or per-position expansion is needed.
    observations = []
    for source, table in OBSERVATION_TABLES.items():
        totals = one('''SELECT count(*) records,count(DISTINCT target_position) mapped_positions,
            count(DISTINCT pdb_id) pdb_entries FROM web.''' + table + '''
            WHERE sequence_id=:sequence_id AND mapping_status='mapped' ''', params)
        observations.append({'source': source, **totals, 'unit': 'mapped_source_rows',
                             'scope': 'Current canonical sequence; mapping_status=mapped',
                             'notes': OBSERVATION_NOTES[source]})
    return {
        'accession': protein['accession'], 'sequence_id': protein['sequence_id'], 'length': protein['length'],
        'coordinate_system': '1-based inclusive on the explicitly associated canonical sequence',
        'classification': classification, 'labels': labels,
        'uniprot': {'counts': counts, 'locatable_counts': locatable_counts, 'features': features,
                    'unit': 'source_feature_records',
                    'scope': 'All UniProt membrane features explicitly associated with the current canonical sequence; uncertain coordinates are retained, but only exactly locatable features may be drawn.'},
        'deeptmhmm2': prediction, 'topology_sources': topology, 'observations': observations,
        'topology_records': topology_records(protein['accession'], protein['sequence_id']),
        'notes': [
            'UniProt source-feature counts, DeepTMHMM2 predicted segments, topology source records and structural residue observations are different objects and must not be added.',
            'Zero denotes no qualifying local record in this scope, not evidence that a membrane feature or interaction is biologically absent.',
            'Topology groups preserve source, method and evidence role; overlapping packages, source constraints and repeated records are not independent corroboration.',
        ],
    }


@router.get('/proteins/{accession}/overview/membrane/summary')
def membrane_summary(accession: str):
    return membrane_summary_data(accession)


@router.get('/proteins/{accession}/overview/membrane/sequence')
def membrane_sequence(accession: str):
    """Small, on-demand sequence projection for the membrane-only dialog."""
    summary = membrane_summary_data(accession)
    params = {'sequence_id': summary['sequence_id'], 'accession': summary['accession']}
    sequence = one('SELECT sequence,length FROM web.protein_sequence WHERE sequence_id=:sequence_id', params)
    rows = query('''SELECT target_position position,target_residue residue,pdb_id,
        local_chain_id chain_id,model_id,pdb_resseq source_position,insertion_code,geometry_type,mapping_method
        FROM web.membrane_opm_observation WHERE sequence_id=:sequence_id
        AND mapping_status='mapped' ORDER BY target_position,pdb_id,local_chain_id,model_id''', params)
    positions = {}
    for row in rows:
        position = row['position']
        item = positions.setdefault(position, {'position': position, 'residue': row['residue'],
                                               'record_count': 0, 'structures': {}})
        item['record_count'] += 1
        key = (row['pdb_id'], row['chain_id'])
        structure = item['structures'].setdefault(key, {'pdb_id': row['pdb_id'], 'chain_id': row['chain_id'],
                                                        'models': set(), 'geometry_types': set(),
                                                        'mapping_methods': set(), 'source_positions': set()})
        if row['model_id'] is not None:
            structure['models'].add(row['model_id'])
        if row['geometry_type']:
            structure['geometry_types'].add(row['geometry_type'])
        if row['mapping_method']:
            structure['mapping_methods'].add(row['mapping_method'])
        if row['source_position'] is not None:
            structure['source_positions'].add(f"{row['source_position']}{row['insertion_code'] or ''}")
    projected = []
    for item in positions.values():
        structures = []
        for structure in item.pop('structures').values():
            structures.append({**structure, 'models': sorted(structure['models']),
                               'geometry_types': sorted(structure['geometry_types']),
                               'mapping_methods': sorted(structure['mapping_methods']),
                               'source_positions': sorted(structure['source_positions'])})
        projected.append({**item, 'structures': structures})
    statuses = query('''SELECT mapping_status,count(*) records FROM web.membrane_opm_observation
        WHERE accession=:accession OR source_accession=:accession
        GROUP BY mapping_status ORDER BY mapping_status''', params)
    unmapped = query('''SELECT mapping_status,pdb_id,local_chain_id chain_id,count(*) records,
        min(pdb_resseq) first_source_position,max(pdb_resseq) last_source_position,
        array_agg(DISTINCT geometry_type ORDER BY geometry_type) geometry_types
        FROM web.membrane_opm_observation WHERE (accession=:accession OR source_accession=:accession)
        AND mapping_status<>'mapped' GROUP BY mapping_status,pdb_id,local_chain_id
        ORDER BY mapping_status,pdb_id,local_chain_id LIMIT 101''', params)
    return {'sequence_id': summary['sequence_id'], 'sequence': sequence['sequence'], 'length': sequence['length'],
            'coordinate_system': '1-based inclusive on the explicitly associated canonical sequence',
            'uniprot_features': summary['uniprot']['features'],
            'opm': {'positions': projected, 'mapping_statuses': statuses,
                    'unmapped_records': unmapped[:100], 'unmapped_has_more': len(unmapped) > 100,
                    'source_url': 'https://opm.phar.umich.edu/',
                    'scope': 'Structure/model/chain observations already mapped to the current canonical sequence.'}}


@router.get('/proteins/{accession}/overview/membrane/details')
def membrane_details(accession: str, source: Literal['OPM', 'MPLID', 'BioDolphin'],
                     limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    summary = membrane_summary_data(accession)
    params = {'sequence_id': summary['sequence_id'], 'limit': limit + 1, 'offset': offset}
    if source == 'OPM':
        rows = query('''SELECT source_observation_id::text id,target_position position,target_residue residue,
            pdb_id,model_id,local_chain_id chain_id,pdb_resseq source_position,pdb_resseq,insertion_code,
            pdb_residue,geometry_type,observed_dum_surface,site_coordinate_basis,"site_signed_depth_A",
            "distance_to_boundary_A","distance_outside_membrane_A","distance_to_midplane_A",
            "distance_to_observed_surface_A","membrane_half_thickness_A",heavy_atom_fraction_in_core,
            atoms_cross_boundary,mapping_status,mapping_method,is_wildtype_residue
            FROM web.membrane_opm_observation WHERE sequence_id=:sequence_id AND mapping_status='mapped'
            ORDER BY target_position,source_observation_id LIMIT :limit OFFSET :offset''', params)
        names = ['model_id','pdb_resseq','insertion_code','pdb_residue','geometry_type','observed_dum_surface',
                 'site_coordinate_basis','site_signed_depth_A','distance_to_boundary_A','distance_outside_membrane_A',
                 'distance_to_midplane_A','distance_to_observed_surface_A','membrane_half_thickness_A',
                 'heavy_atom_fraction_in_core','atoms_cross_boundary']
    elif source == 'MPLID':
        rows = query('''SELECT source_member || ':' || source_row::text id,source_member,source_row,
            target_position position,target_residue residue,pdb_id,chain_id,residue_number source_position,
            residue_number,insertion_code,residue_name,source_aa,is_contact,label_source,confidence,min_distance,
            mapping_status,mapping_method,is_wildtype_residue FROM web.membrane_mplid_residue
            WHERE sequence_id=:sequence_id AND mapping_status='mapped'
            ORDER BY target_position,source_member,source_row LIMIT :limit OFFSET :offset''', params)
        names = ['residue_number','insertion_code','source_aa','is_contact','label_source','confidence','min_distance']
    else:
        rows = query('''SELECT s.interaction_id || ':' || s.coordinate_system || ':' || s.site_order::text id,
            s.interaction_id,s.site_order,s.coordinate_system,s.target_position position,s.target_residue residue,
            s.pdb_id,s.source_chain_id chain_id,s.residue_number source_position,s.residue_number,s.insertion_code,
            s.residue_name,s.mapping_status,s.mapping_method,s.is_wildtype_residue,
            b."lipid_PDB_Name" ligand_name,b."lipid_Ligand_ID_CCD" ligand_id,
            b."lipid_pharmacological_class" pharmacological_class,b."complex_PubMed_ID" pubmed_id
            FROM web.membrane_biodolphin_site s JOIN web.membrane_biodolphin_interaction b USING(interaction_id)
            WHERE s.sequence_id=:sequence_id AND s.mapping_status='mapped'
            ORDER BY s.target_position,s.interaction_id,s.coordinate_system,s.site_order LIMIT :limit OFFSET :offset''', params)
        names = ['interaction_id','coordinate_system','residue_number','insertion_code','residue_name',
                 'ligand_id','ligand_name','pharmacological_class','pubmed_id']
    for row in rows[:limit]:
        row['fields'] = fields(row, names + ['mapping_status','mapping_method','is_wildtype_residue'])
        for field in row['fields']:
            if field['label'].endswith('_A') or field['label'] == 'min_distance':
                field['unit'] = 'Å'
            elif field['label'] == 'heavy_atom_fraction_in_core':
                field['unit'] = 'fraction (0–1)'
    total = next(item['records'] for item in summary['observations'] if item['source'] == source)
    return {'source': source, 'sequence_id': summary['sequence_id'], 'items': rows[:limit], 'total': total,
            'limit': limit, 'offset': offset, 'has_more': len(rows) > limit, 'unit': 'mapped_source_rows',
            'notes': OBSERVATION_NOTES[source]}
