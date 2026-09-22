"""Published interface scores, with exact Web sequence links and explicit contexts."""
from fastapi import APIRouter, HTTPException, Query
from .db import one, query
from .sequence import sequence_params

router=APIRouter(prefix='/api/proteins',tags=['interface predictions'])
PESTO_FIELDS=['p_protein','p_nucleic_acid','p_ion','p_ligand','p_lipid']

def context(accession):
    protein,params=sequence_params(accession)
    available=one("SELECT to_regnamespace('web_interface') IS NOT NULL available")['available']
    links=query('SELECT * FROM web_interface.web_sequence_link WHERE canonical_accession=:accession',params) if available else []
    exact={r['method']:r for r in links if r['mapping_status']=='exact' and r['web_sequence_id']==params['sequence_id']}
    return protein,params,available,links,exact

@router.get('/{accession}/interface/summary')
def summary(accession:str):
    protein,p,available,links,exact=context(accession)
    structures=[];partners=0
    if 'PeSTo' in exact:
        structures=query('''SELECT structure_id,fragment,model,manifest_start AS start,manifest_end AS "end",status,residue_count
         FROM web_interface.pesto_structure WHERE sequence_id=:key ORDER BY manifest_start,structure_id''',{'key':exact['PeSTo']['source_key']})
    if 'SPPIDER-seq' in exact:
        partners=one('SELECT count(*) count FROM web_interface.sppider_prediction WHERE query_sequence_key=:key',{'key':exact['SPPIDER-seq']['source_key']})['count']
    return {'status':'available' if available else 'not_imported','sequence_id':p['sequence_id'],'mapping':links,
            'pesto_structures':structures,'sppider_partners':partners,'pesto_fields':PESTO_FIELDS,
            'data_version':'20260921_interface_predictions_01',
            'notes':['Computational predictions, not observed physical interactions.',
             'PeSTo scores retain their individual structure fragment; five binding classes are not mutually exclusive.',
             'Both SPPIDER-seq heads score the query sequence conditional on the selected partner. No partner or fragment aggregation.']}

@router.get('/{accession}/interface/pesto')
def pesto(accession:str,structure_id:str=Query(...,max_length=100)):
    _,p,_,_,exact=context(accession)
    if 'PeSTo' not in exact:raise HTTPException(404,'No PeSTo prediction mapped to the current sequence')
    rows=query('''SELECT canonical_position AS position,canonical_residue AS residue,chain,structure_residue_id,
      insertion_code,plddt,p_protein,p_nucleic_acid,p_ion,p_ligand,p_lipid
      FROM web_interface.pesto_prediction WHERE sequence_id=:key AND structure_id=:structure_id
      ORDER BY canonical_position,chain,structure_residue_id''',{'key':exact['PeSTo']['source_key'],'structure_id':structure_id})
    if not rows:raise HTTPException(404,'This structure has no prediction for the current sequence')
    return {'method':'PeSTo','structure_id':structure_id,'sequence_id':p['sequence_id'],'items':rows,'scale':[0,1]}

@router.get('/{accession}/interface/partners')
def partners(accession:str,search:str=Query('',max_length=100),offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=100)):
    _,p,_,_,exact=context(accession)
    if 'SPPIDER-seq' not in exact:return {'items':[],'has_more':False,'sequence_id':p['sequence_id']}
    rows=query('''SELECT v.partner_sequence_key,s.length,
      COALESCE((SELECT array_agg(r.canonical_accession ORDER BY r.canonical_accession) FROM web_interface.canonical_reference r
       WHERE r.sequence_key=v.partner_sequence_key),ARRAY[]::text[]) AS accessions
      FROM web_interface.sppider_prediction v JOIN web_interface.sequence_content s ON s.sequence_key=v.partner_sequence_key
      WHERE v.query_sequence_key=:key AND (:search='' OR v.partner_sequence_key ILIKE :pattern OR EXISTS
       (SELECT 1 FROM web_interface.canonical_reference r WHERE r.sequence_key=v.partner_sequence_key AND r.canonical_accession ILIKE :pattern))
      ORDER BY v.partner_sequence_key LIMIT :limit OFFSET :offset''',{'key':exact['SPPIDER-seq']['source_key'],'search':search,'pattern':'%'+search+'%','limit':limit+1,'offset':offset})
    return {'sequence_id':p['sequence_id'],'items':rows[:limit],'has_more':len(rows)>limit}

@router.get('/{accession}/interface/sppider')
def sppider(accession:str,partner:str=Query(...,max_length=100)):
    _,p,_,_,exact=context(accession)
    if 'SPPIDER-seq' not in exact:raise HTTPException(404,'No partner-conditioned prediction mapped to the current sequence')
    args={'key':exact['SPPIDER-seq']['source_key'],'partner':partner}
    row=one('''SELECT query_sequence_key,partner_sequence_key,length,receptor_probability,peptide_probability
      FROM web_interface.sppider_prediction WHERE query_sequence_key=:key AND partner_sequence_key=:partner''',args)
    if not row:raise HTTPException(404,'Prediction for this partner is unavailable')
    evidence=query('''SELECT ppi_record_id,ppi_dataset_id,query_endpoint,partner_endpoint
      FROM web_interface.direction_evidence WHERE query_sequence_key=:key AND partner_sequence_key=:partner
      ORDER BY ppi_dataset_id,ppi_record_id LIMIT 20''',args)
    return {**row,'sequence_id':p['sequence_id'],'method':'SPPIDER-seq','scale':[0,1],'source_evidence':evidence,
      'note':'Both arrays index the query sequence, 1-based. Original PPI provenance may include genetic, negative and context observations; it is not extra experimental support.'}

@router.get('/{accession}/interface/sites/{position}')
def site(accession:str,position:int,partner:str=Query('',max_length=100),offset:int=Query(0,ge=0),limit:int=Query(10,ge=1,le=50)):
    _,p,available,links,exact=context(accession)
    length=one('SELECT length FROM web.protein_sequence WHERE sequence_id=:sequence_id',p)['length']
    if not 1<=position<=length:raise HTTPException(422,'Position is outside the current sequence')
    pesto_rows=[];sppider_rows=[]
    if 'PeSTo' in exact:
        pesto_rows=query('''SELECT structure_id,canonical_position AS position,canonical_residue AS residue,plddt,
          p_protein,p_nucleic_acid,p_ion,p_ligand,p_lipid FROM web_interface.pesto_prediction
          WHERE sequence_id=:key AND canonical_position=:position ORDER BY structure_id''',{'key':exact['PeSTo']['source_key'],'position':position})
    if 'SPPIDER-seq' in exact:
        sppider_rows=query('''SELECT partner_sequence_key,receptor_probability[:position] AS receptor_probability,
          peptide_probability[:position] AS peptide_probability FROM web_interface.sppider_prediction
          WHERE query_sequence_key=:key AND (:partner='' OR partner_sequence_key=:partner)
          ORDER BY partner_sequence_key LIMIT :limit OFFSET :offset''',{'key':exact['SPPIDER-seq']['source_key'],'position':position,'partner':partner,'limit':limit+1,'offset':offset})
    return {'status':'available' if available else 'not_imported','sequence_id':p['sequence_id'],'position':position,
            'pesto':pesto_rows,'sppider':sppider_rows[:limit],'has_more':len(sppider_rows)>limit,
            'scope':'Separate structure fragments and separate partners; raw continuous scores, no threshold.'}
