"""Human PaxDB protein abundances; navigation groups do not aggregate values."""
from typing import Literal
from fastapi import APIRouter, Query
from .db import query, one
from .evidence_common import require_protein
router=APIRouter()
JOIN='''FROM web_paxdb.observations o
JOIN web_paxdb.protein_mapping m ON m.string_external_id=o.string_external_id
JOIN web_paxdb.datasets d ON d.id=o.dataset_id'''

@router.get('/proteins/{accession}/expression/paxdb/summary')
def summary(accession:str):
 require_protein(accession)
 rows=query(f'''SELECT d.integrated,count(*) records,count(DISTINCT d.id) datasets
 {JOIN} WHERE m.accession=:accession GROUP BY d.integrated ORDER BY d.integrated DESC''',{'accession':accession})
 return {'source':'PaxDB','taxon_id':9606,'collections':[{'dataset':'paxdb_integrated' if r['integrated'] else 'paxdb_studies','count':r['records'],'datasets':r['datasets']} for r in rows]}

@router.get('/proteins/{accession}/expression/paxdb')
def records(accession:str,collection:Literal['integrated','studies']='integrated',
            context_type:Literal['tissue','cell','fluid','fraction','whole']='tissue',
            organ:str=Query('',max_length=120),offset:int=Query(0,ge=0),limit:int=Query(30,ge=1,le=100)):
 require_protein(accession)
 args={'accession':accession,'integrated':collection=='integrated','kind':context_type,'organ':organ,'offset':offset,'limit':limit}
 base='m.accession=:accession AND d.integrated=:integrated'
 contexts=query(f'''SELECT d.organ,d.context_type,d.body_region,count(*) records {JOIN}
 WHERE {base} GROUP BY d.organ,d.context_type,d.body_region ORDER BY d.organ''',args)
 where=base+" AND d.context_type=:kind AND (:organ='' OR d.organ=:organ)"
 stats=one(f'SELECT count(*) total,max(o.abundance::double precision) maximum {JOIN} WHERE {where}',args)
 total=stats['total']
 rows=query(f'''SELECT d.organ,d.name,d.integrated,o.abundance,d.description,d.score,d.coverage,
 d.publication_year,d.link,o.dataset_id||':'||o.source_row record_key
 {JOIN} WHERE {where} ORDER BY d.organ,d.name,d.id,o.source_row LIMIT :limit OFFSET :offset''',args)
 return {'source':'PaxDB','taxon_id':9606,'unit':'ppm','collection':collection,'contexts':contexts,'items':rows,'total':total,'maximum':stats['maximum'],'offset':offset,'limit':limit}
