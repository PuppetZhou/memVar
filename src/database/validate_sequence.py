"""Validate Sequence before schema publication; also usable after import."""
import json
from pathlib import Path
import polars as pl
from import_tables import command,q,WEB

def validate_sequence(schema,manifest):
    s=q(schema)
    # Large PTM/JSD joins can otherwise choose a parallel hash plan that exceeds
    # the PostgreSQL container's bounded /dev/shm. Validation is deterministic
    # and does not benefit enough from parallel workers to justify that risk.
    def scalar(sql):
        output=command('SET max_parallel_workers_per_gather=0;\n'+sql,True).strip().splitlines()
        return int(output[-1])
    def require_zero(sql,label):
        n=scalar(sql)
        if n:raise ValueError(f'Sequence validation {label}: {n}')
    counts={t['name']:t['rows'] for t in manifest['tables']}
    for table in ['sequence_site','conservation_sequence','residue_conservation','pfam_hit','pfam_sequence']:
        require_zero(f'SELECT count(*) FROM {s}.{q(table)} x LEFT JOIN {s}.protein p ON p.default_sequence_id=x.sequence_id WHERE p.accession IS NULL;',table+' canonical scope')
    for table in ['sequence_site','residue_conservation']:
        require_zero(f'''SELECT count(*) FROM {s}.{table} x JOIN {s}.protein_sequence p USING(sequence_id)
WHERE x.position<1 OR x.position>p.length OR x.residue IS DISTINCT FROM substring(p.sequence FROM x.position::integer FOR 1);''',table+' residues')
    require_zero(f'''SELECT count(*) FROM {s}.residue_conservation WHERE jsd_conservation IS NULL OR jsd_conservation<0 OR jsd_conservation>1;''','JSD values')
    require_zero(f'''SELECT count(*) FROM {s}.conservation_sequence c JOIN {s}.protein_sequence p USING(sequence_id)
LEFT JOIN (SELECT sequence_id,count(*) n FROM {s}.residue_conservation GROUP BY sequence_id) r USING(sequence_id)
WHERE r.n IS DISTINCT FROM p.length;''','JSD coverage')
    require_zero(f'''SELECT count(*) FROM {s}.pfam_hit h JOIN {s}.protein_sequence p USING(sequence_id)
WHERE NOT (1<=env_start AND env_start<=ali_start AND ali_start<=ali_end AND ali_end<=env_end AND env_end<=p.length AND 1<=hmm_start AND hmm_start<=hmm_end AND hmm_end<=model_length);''','Pfam coordinates')
    require_zero(f'''SELECT count(*) FROM {s}.pfam_sequence p LEFT JOIN
(SELECT sequence_id,count(*) n FROM {s}.pfam_hit GROUP BY sequence_id) h USING(sequence_id)
WHERE p.hit_count<>coalesce(h.n,0);''','Pfam zero/hit counts')
    require_zero(f'''SELECT count(*) FROM {s}.ptm_record_site l JOIN {s}.ptm_record r USING(record_id)
WHERE r.topic='ptm_disease' OR r.evidence_status='deprecated_only';''','unverified/retired PTM must not have sites')
    require_zero(f'''SELECT count(*) FROM {s}.ptm_record_detail r JOIN {s}.ptm_record_site l USING(record_id)
JOIN {s}.sequence_site p USING(site_id) WHERE
(l.endpoint_role='site' AND p.position<>r.source_start) OR
(l.endpoint_role='start' AND p.position<>r.source_start) OR
(l.endpoint_role='end' AND p.position<>r.source_end);''','PTM endpoint role coordinates')
    require_zero(f'''SELECT count(*) FROM {s}.ptm_evidence e LEFT JOIN {s}.ptm_evidence_dataset d ON d.source_dataset_id=e.identifier
WHERE e.namespace='ProteomeScout_dataset' AND d.source_dataset_id IS NULL;''','PS evidence dictionary')
    require_zero(f'''SELECT count(*) FROM {s}.ptm_record WHERE accession IS NULL AND
(candidate_accessions IS NULL OR jsonb_array_length(candidate_accessions)=0);''','PTM ambiguous identity remains navigable')
    # Compare normalized source evidence counts to reconstructed view, scoped by retained IDs.
    rec=pl.read_parquet(WEB/'data/tables/sequence/ptm_record.parquet',columns=['record_id'])
    src=WEB.parent/manifest['inputs']['ptm']['path']
    expected=pl.scan_parquet(src/'annotation_evidence/*.parquet').join(rec.lazy(),on='record_id',how='semi').select(pl.len()).collect().item()
    actual=scalar(f'SELECT count(*) FROM {s}.ptm_evidence_all;')
    if expected!=actual:raise ValueError(f'PTM evidence loss: {actual} != {expected}')
    if scalar(f'SELECT count(*) FROM {s}.sequence_ptm_site;')!=counts['ptm_record_site']:raise ValueError('PTM site view row multiplication')
    # Check selected details and common-field reuse against source rows for each dataset.
    samples=pl.read_parquet(WEB/'data/tables/sequence/ptm_record.parquet').group_by('dataset_id').first().select('record_id')
    original=pl.scan_parquet(src/'annotation_record/*.parquet').join(samples.lazy(),on='record_id',how='semi').collect()
    for row in original.iter_rows(named=True):
        rid=row['record_id'].replace("'","''")
        actual_row=json.loads(command(f"SELECT row_to_json(t) FROM (SELECT * FROM {s}.ptm_record_detail WHERE record_id='{rid}') t;",True))
        for col in ['source_start','source_end','source_type','source_sequence_id','mapped_sequence_id','mapped_start','mapped_end']:
            if actual_row[col]!=row[col]:raise ValueError(f'PTM detail reconstruction differs: {col}')
    sqls={
      'PTM_site':f"SELECT * FROM {s}.sequence_ptm_site WHERE sequence_id='P00533' AND position BETWEEN 1000 AND 1100 LIMIT 50",
      'UniProt_features':f"SELECT feature_id,source_type,start,\"end\" FROM {s}.sequence_uniprot_feature WHERE sequence_id='P00533' LIMIT 100",
      'JSD_range':f"SELECT position,jsd_conservation,occupancy FROM {s}.residue_conservation WHERE sequence_id='P00533' AND position BETWEEN 1 AND 200 ORDER BY position",
      'Pfam_hits':f"SELECT h.*,e.pfam_id FROM {s}.pfam_hit h JOIN {s}.pfam_entry e USING(pfam_accession) WHERE sequence_id='P00533' ORDER BY ali_start"}
    plans={}
    for name,sql in sqls.items():
        plan=json.loads(command('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+sql,True))[0]
        plans[name]={'execution_ms':plan['Execution Time'],'rows':plan['Plan']['Actual Rows']}
    return {'status':'passed','checks':['canonical_scope','PTM_and_JSD_residue_identity','JSD_full_coverage','Pfam_coordinates_and_zero_hits','PTM_endpoint_roles','no_unverified_PTM_sites','PS_evidence_dictionary','unmapped_identity_navigation','PTM_evidence_count_reconstruction','source_detail_samples'],'ptm_evidence_rows':expected,'queries':plans}

if __name__=='__main__':
    manifest=json.loads((WEB/'data/tables/manifest.json').read_text())
    result=validate_sequence('web',manifest);result['data_version']=manifest['data_version'];result['input_built_at']=manifest['built_at']
    (WEB/'data/sequence_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
