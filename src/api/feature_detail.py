"""Details for one clicked feature or an explicit same-site PTM marker's records."""
from fastapi import APIRouter,HTTPException,Query
from .db import query,one
from .variant_support import protein_identity
from .evidence_common import fields
router=APIRouter()

@router.get('/proteins/{accession}/sequence/feature')
def feature_detail(accession:str,source:str=Query(...,max_length=100),feature_id:str=Query('',max_length=2000),
                   record_ids:str=Query('',max_length=100000),limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0,le=10000)):
    protein=protein_identity(accession)
    params=dict(accession=accession,sequence_id=protein['sequence_id'],id=feature_id,limit=limit+1,offset=offset)
    result=dict(source=source,feature=None,records=[],evidence=[],has_more=False,sequence_id=protein['sequence_id'],coordinate_system='1-based inclusive on the explicitly mapped canonical sequence')
    if record_ids or source=='PTM':
        ids=list(dict.fromkeys(v.strip() for v in (record_ids or feature_id).split(',') if v.strip()))
        if not ids or len(ids)>1000:
            raise HTTPException(422,'Provide 1–1000 explicit PTM record IDs')
        params['ids']=ids
        rows=query('''SELECT r.record_id,split_part(r.dataset_id,':',1) source,r.source_type,r.description,r.topic,
            r.source_record_id,r.source_sequence_id,r.source_start,r.source_end,r.source_residue,
            r.mapping_status,r.evidence_status,r.details_json details
            FROM web.ptm_record_detail r WHERE r.record_id=ANY(:ids) AND r.dataset_id NOT LIKE 'PTMD2:%' AND EXISTS (
                SELECT 1 FROM web.ptm_record_site l JOIN web.sequence_site s USING(site_id)
                WHERE l.record_id=r.record_id AND s.sequence_id=:sequence_id)
            ORDER BY r.record_id LIMIT :limit OFFSET :offset''',params)
        if not rows and offset==0:
            raise HTTPException(404,'No requested PTM record maps to this canonical sequence')
        selected=[r['record_id'] for r in rows[:limit]]
        evidence=query('''SELECT record_id,namespace,identifier,url,evidence_kind kind,is_current
            FROM web.ptm_evidence_all WHERE record_id=ANY(:ids) ORDER BY record_id,namespace,identifier''',{'ids':selected}) if selected else []
        positions=query('''SELECT l.record_id,s.position,s.residue,l.endpoint_role FROM web.ptm_record_site l
            JOIN web.sequence_site s USING(site_id) WHERE l.record_id=ANY(:ids) AND s.sequence_id=:sequence_id
            ORDER BY l.record_id,s.position,l.endpoint_role''',{'ids':selected,'sequence_id':protein['sequence_id']}) if selected else []
        for row in rows[:limit]:
            row['evidence']=[e for e in evidence if e['record_id']==row['record_id']]
            row['positions']=[p for p in positions if p['record_id']==row['record_id']]
            row['fields']=fields(row,['source_type','description','source_sequence_id','source_start','source_end','source_residue','mapping_status','evidence_status'])
        result.update(source='PTM',records=rows[:limit],has_more=len(rows)>limit,limit=limit,offset=offset,requested_records=len(ids))
        return result
    if not feature_id:
        raise HTTPException(422,'feature_id is required')
    if source=='UniProt':
        feature=one('''SELECT feature_id,source_record_id,source_feature_id,label,source_type,description,
            source_sequence_id,sequence_scope,mapped_sequence_id,mapping_status,location_kind,start,"end",
            start_modifier,end_modifier,coordinate_status,can_locate_exactly,interpretation_status,details_json details,evidences evidence
            FROM web.sequence_uniprot_feature WHERE feature_id=:id AND accession=:accession AND sequence_id=:sequence_id''',params)
        if feature:
            feature['fields']=fields(feature,['source_type','description','source_sequence_id','sequence_scope','start','end','location_kind','start_modifier','end_modifier','coordinate_status','interpretation_status'])
            result['evidence']=feature.get('evidence') or []
    elif source=='Pfam':
        feature=one('''SELECT h.hit_id,h.pfam_accession,e.pfam_id,e.description,e.entry_type,e.clan_id,e.clan_name,
            h.model_accession,h.model_length,h.hmm_start,h.hmm_end,h.ali_start,h.ali_end,h.env_start,h.env_end,
            h.domain_c_evalue,h.domain_i_evalue,h.domain_score,h.domain_bias,h.alignment_accuracy,'alignment' displayed_boundary
            FROM web.pfam_hit h JOIN web.pfam_entry e USING(pfam_accession) WHERE h.hit_id=:id AND h.sequence_id=:sequence_id''',params)
        if feature:
            feature['fields']=fields(feature,['pfam_accession','pfam_id','description','entry_type','clan_id','clan_name','ali_start','ali_end','env_start','env_end','hmm_start','hmm_end','model_length','domain_i_evalue','domain_c_evalue','domain_score','domain_bias','alignment_accuracy','displayed_boundary'])
            result['evidence']=[{'namespace':'Pfam','identifier':feature['pfam_accession'],'url':'https://www.ebi.ac.uk/interpro/entry/pfam/'+feature['pfam_accession'].split('.')[0]}]
    elif source=='DeepTMHMM2':
        if not feature_id.isdigit():raise HTTPException(422,'DeepTMHMM2 feature_id is the segment order')
        params['segment_order']=int(feature_id)
        feature=one('''SELECT s.segment_order,s.name,s.start,s."end",p.protein_type,p.status,p.mapping_status,
            p.has_signal_peptide,p.has_transit_peptide,p.membrane_type_applicable,p.membrane_types,p.membrane_selection_method,
            p.membrane_probabilities_json membrane_probabilities
            FROM web.deeptmhmm2_segment s JOIN web.deeptmhmm2_prediction p USING(sequence_id)
            WHERE s.sequence_id=:sequence_id AND s.segment_order=:segment_order''',params)
        if feature:
            feature['evidence_kind']='prediction'
            feature['fields']=fields(feature,['name','start','end','protein_type','status','mapping_status','membrane_type_applicable','membrane_types','membrane_selection_method'])
    else:
        feature=one('''SELECT f.feature_id,f.dataset_id source,f.record_id,f.source_sequence_id,f.role,f.method,f.native_type,
            f.model_id,f.start source_start,f."end" source_end,f.coordinate_status,f.raw_attributes details,
            l.start,l."end",l.mapping_status,s.chain_id,s.coordinate_basis,s.native_id
            FROM web.membrane_topology_feature f JOIN web.membrane_topology_location l USING(feature_id,dataset_id)
            JOIN web.membrane_topology_source s ON s.source_sequence_id=f.source_sequence_id
            WHERE f.feature_id=:id AND l.sequence_id=:sequence_id AND (:source='Topology' OR f.dataset_id=:source) LIMIT 1''',{**params,'source':source})
        if feature:feature['fields']=fields(feature,['source','native_type','role','method','record_id','source_sequence_id','model_id','chain_id','source_start','source_end','start','end','coordinate_basis','mapping_status'])
    if not feature:
        raise HTTPException(404,'This feature is not associated with the selected canonical sequence')
    result['feature']=feature
    return result
