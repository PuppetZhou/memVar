"""Canonical Sequence service projections; scientific mappings remain upstream."""
import json
import polars as pl
from build_tables import ROOT,INPUTS,RULES,read,nested,require,js

def build_sequence(b):
    proteins=pl.read_parquet(b.tables['protein']).select('accession','default_sequence_id')
    canonical=set(proteins['default_sequence_id'])
    seqs=pl.read_parquet(b.tables['protein_sequence'])
    # Keep the already-published membrane scope, adding only canonical other features.
    f=read('uniprot_features','sequence_feature').join(proteins,on='accession')
    f=f.filter((pl.col('mapped_sequence_id')==pl.col('default_sequence_id'))|pl.col('source_type').is_in(RULES['uniprot_membrane_types'])).drop('default_sequence_id')
    d=read('uniprot_features','feature_detail').join(f.select('feature_id'),on='feature_id',how='semi')
    details=[]
    for r in d.iter_rows(named=True):
        payload=json.loads(r['payload_json'])
        # Coordinates and evidence are held once in the feature and evidence columns.
        extra={k:v for k,v in payload.items() if k not in ['description','location','type','evidences','featureId']}
        details.append(dict(feature_id=r['feature_id'],description=r['description'],details_json=js(extra) if extra else None))
    ev=read('uniprot_features','feature_evidence').join(f.select('feature_id'),on='feature_id',how='semi').drop('payload_json')
    f=f.join(pl.from_dicts(details,infer_schema_length=None),on='feature_id',how='left').join(nested(ev,'feature_id','evidences'),on='feature_id',how='left')
    b.put('uniprot_sequence_feature',f,'sequence',['uniprot_features'],['feature_id'],'共用UniProt feature：canonical全部类型及既有膜记录；Sequence视图仅取canonical')
    # Dataset metadata now; source coverage statistics are deliberately deferred.
    datasets=[]
    ptm_d=read('ptm','annotation_dataset')
    for r in ptm_d.iter_rows(named=True):
        datasets.append(dict(dataset_id=r['dataset_id'],source=r['source'],source_release=r['source_release'],method=None,snapshot=r['snapshot_run']))
    ud=read('uniprot_features','annotation_dataset').to_dicts()[0]
    datasets.append(dict(dataset_id=ud['dataset_id'],source=ud['source'],source_release=ud['source_release'],method=ud['mapping_method'],snapshot=ud['run_id']))
    for r in read('conservation','conservation_dataset').iter_rows(named=True):
        datasets.append(dict(dataset_id=r['dataset_id'],source='JSD/UniRef90',source_release=r['uniref_release'],method=r['method'],snapshot=r['pipeline_version']))
    datasets.append(dict(dataset_id=INPUTS['pfam']['version'],source='Pfam',source_release=INPUTS['pfam']['release'],method='hmmscan --cut_ga; exact-input reuse and incremental scan',snapshot=INPUTS['pfam']['version']))
    b.put('sequence_dataset',pl.from_dicts(datasets),'sequence',['ptm','uniprot_features','conservation','pfam'],['dataset_id'],'来源与方法最小字典；不计算来源覆盖统计')
    b.fk('uniprot_sequence_feature','dataset_id','sequence_dataset','dataset_id')
    # PTM records and exact sites are independent, so unmapped facts remain queryable.
    p=ROOT/INPUTS['ptm']['path']
    records=pl.read_parquet(p/'annotation_record/*.parquet')
    detail=pl.read_parquet(p/'annotation_detail/*.parquet')
    sites=read('ptm','site_index').filter(pl.col('sequence_id').is_in(canonical))
    links=read('ptm','record_site').join(sites.select('site_id'),on='site_id',how='semi')
    known_noncanonical=set(seqs.filter(~pl.col('is_canonical'))['sequence_id'])
    iso=pl.read_parquet(b.tables['protein_isoform'])
    known_noncanonical.update(iso.filter(~pl.col('is_canonical'))['isoform_id'])
    # Declared canonical aliases must not be excluded by a different naming convention.
    known_noncanonical-=set(iso.filter(pl.col('is_canonical'))['isoform_id'])
    selected=records.filter(pl.col('mapped_sequence_id').is_in(canonical)|
        (pl.col('mapped_sequence_id').is_null() & ~pl.col('source_sequence_id').is_in(known_noncanonical).fill_null(False)))
    require(selected.join(links.select('record_id').unique(),on='record_id',how='semi').height==links['record_id'].n_unique(),'canonical PTM records missing')
    candidates=read('ptm','mapping_candidate').join(seqs.select('sequence_id',pl.col('owner_accession').alias('candidate_accession')),on='sequence_id').filter(pl.col('candidate_accession').is_in(b.accessions)).group_by('record_id').agg(pl.col('candidate_accession').unique().sort().alias('candidate_accessions'))
    selected=selected.join(candidates,on='record_id',how='left').join(detail,on='record_id',how='left')
    verified_statuses=['full_sequence_exact','full_sequence_equal_identifier_changed','original_window_exact','uniprot_native_exact']
    mapping_check=selected.join(proteins,left_on='target_accession',right_on='accession',how='left')
    require(mapping_check.filter(pl.col('mapped_sequence_id').is_not_null() != pl.col('mapping_status').is_in(verified_statuses)).height==0,'PTM mapping status is not reconstructible')
    require(mapping_check.filter(pl.col('mapped_sequence_id').is_not_null() & ((pl.col('mapped_sequence_id')!=pl.col('default_sequence_id')) | (pl.col('mapped_start')!=pl.col('source_start')) | (pl.col('mapped_end')!=pl.col('source_end')))).height==0,'PTM verified mapping cannot be reconstructed')
    selected=selected.with_columns(pl.when(pl.col('target_accession').is_null()).then(pl.col('candidate_accessions')).otherwise(pl.lit(None,dtype=pl.List(pl.String))).alias('candidate_accessions'))
    out=[]
    for r in selected.iter_rows(named=True):
        is_uni=r['dataset_id'].startswith('UniProt:')
        payload=json.loads(r.pop('payload_json'))
        r['uniprot_feature_id']=r['source_record_id'] if is_uni else None
        r['source_accession']=r.pop('accession');r['accession']=r.pop('target_accession')
        for col in ['source_file','source_row','mapped_sequence_id','mapped_start','mapped_end']:r.pop(col)
        if is_uni:
            for col in ['description','source_start','source_end','source_type','source_sequence_id','source_object_id']:r[col]=None
            r['details_json']=None
        elif r['dataset_id'].startswith('dbPTM:'):
            r['details_json']=js({'source_entry_name':payload[0],'position_raw':payload[2],'window':payload[5]})
        elif r['dataset_id'].startswith('ProteomeScout:'):
            r['details_json']=js({k:v for k,v in payload.items() if k!='evidence'})
        elif r['dataset_id'].startswith('PTMD2:'):
            r['details_json']=js({k:v for k,v in payload.items() if k not in ['UniProt','Residue','Type','PDAs_id','Sentence','PMID']})
        else:
            r['details_json']=js({k:v for k,v in payload.items() if k not in ['evidence','comment','type','start_pos','end_pos']})
        out.append(r)
    rec=pl.from_dicts(out,infer_schema_length=None)
    b.put('ptm_record',rec,'sequence',['ptm'],['record_id'],'一条canonical已映射或未定位PTM来源记录；UniProt详情通过feature引用')
    b.put('sequence_site',sites.drop('accession'),'sequence',['ptm'],['site_id'],'canonical序列上的唯一PTM残基位置')
    b.put('ptm_record_site',links,'sequence',['ptm'],['record_id','site_id','endpoint_role'],'来源记录—明确canonical位点连接；端点角色独立保留')
    evidence=pl.read_parquet(p/'annotation_evidence/*.parquet').join(rec.select('record_id','uniprot_feature_id'),on='record_id',how='inner').filter(pl.col('uniprot_feature_id').is_null()).drop('uniprot_feature_id')
    # PS citation descriptions belong to their dataset, not every occurrence.
    ps=evidence.filter(pl.col('namespace')=='ProteomeScout_dataset')
    citations=ps.select('identifier','url','is_current','payload_json').unique()
    require(citations['identifier'].n_unique()==citations.height,'PS citation ID has conflicting definitions')
    b.put('ptm_evidence_dataset',citations.rename({'identifier':'source_dataset_id','payload_json':'details_json'}),'sequence',['ptm'],['source_dataset_id'],'ProteomeScout原始证据数据集说明；记录保留各次关联')
    evidence=evidence.with_columns(pl.when(pl.col('namespace')=='ProteomeScout_dataset').then(pl.lit(None,dtype=pl.String)).otherwise(pl.col('payload_json')).alias('payload_json'),pl.when(pl.col('namespace')=='ProteomeScout_dataset').then(pl.lit(None,dtype=pl.String)).otherwise(pl.col('url')).alias('url'),pl.when(pl.col('namespace')=='ProteomeScout_dataset').then(pl.lit(None,dtype=pl.Boolean)).otherwise(pl.col('is_current')).alias('is_current'))
    b.put('ptm_evidence',evidence,'sequence',['ptm'],['evidence_id'],'非UniProt PTM逐条证据；UniProt通过共用feature查询')
    for t,c,parent,pc in [('ptm_record','dataset_id','sequence_dataset','dataset_id'),('ptm_record','uniprot_feature_id','uniprot_sequence_feature','feature_id'),('sequence_site','sequence_id','protein_sequence','sequence_id'),('ptm_record_site','record_id','ptm_record','record_id'),('ptm_record_site','site_id','sequence_site','site_id'),('ptm_evidence','record_id','ptm_record','record_id')]:b.fk(t,c,parent,pc)
    check_sites=sites.join(seqs.select('sequence_id','sequence','length'),on='sequence_id')
    require(check_sites.filter((pl.col('position')<1)|(pl.col('position')>pl.col('length'))|(pl.col('residue')!=pl.col('sequence').str.slice(pl.col('position')-1,1))).height==0,'PTM residue/coordinate mismatch')
    b.checks.extend(['canonical_PTM_selection','PTM_site_residue_identity','PS_citation_definition_unique','PTM_mapping_reconstruction_verified'])
    # JSD per-sequence constants are moved to summary after verifying their constancy.
    jsd=read('conservation','residue_conservation')
    summary=read('conservation','conservation_protein_summary')
    keys=['sequence_id','dataset_id']
    constants=jsd.select(*keys,'n_sequences','alignment_scope','homology_status').unique()
    require(constants.height==summary.height,'JSD sequence constants vary')
    require(summary.join(constants,on=keys,suffix='_site').filter((pl.col('n_sequences')!=pl.col('n_sequences_site'))|(pl.col('alignment_scope')!=pl.col('alignment_scope_site'))).height==0,'JSD summary disagreement')
    summary=summary.join(constants.select(*keys,'homology_status'),on=keys).drop('length','accession')
    require(set(jsd['sequence_id'])==canonical,'JSD canonical coverage')
    b.put('conservation_sequence',summary,'sequence',['conservation'],keys,'canonical序列计算背景和同源支持状态')
    jsd=jsd.drop('accession','foundation_release','n_sequences','alignment_scope','homology_status')
    b.put('residue_conservation',jsd,'sequence',['conservation'],['sequence_id','position','dataset_id'],'一个canonical残基的JSD和逐位点质量事实')
    for t in ['conservation_sequence','residue_conservation']:b.fk(t,'dataset_id','sequence_dataset','dataset_id')
    b.checks.append('JSD_sequence_constants_verified_before_deduplication')
    for name,key,meaning in [('pfam_entry',['pfam_accession'],'一个Pfam条目的名称、类型及Clan'),('pfam_hit',['hit_id'],'一条canonical Pfam命中，保留alignment/envelope/HMM坐标'),('pfam_sequence',['sequence_id'],'每条canonical的Pfam处理状态，包括已扫描零命中')]:
        df=read('pfam',name).with_columns(pl.lit(INPUTS['pfam']['version']).alias('dataset_id'))
        b.put(name,df,'sequence',['pfam'],key,meaning)
        b.fk(name,'dataset_id','sequence_dataset','dataset_id')
    b.fk('pfam_hit','pfam_accession','pfam_entry','pfam_accession')
    require(set(read('pfam','pfam_sequence')['sequence_id'])==canonical,'Pfam canonical coverage')
    b.checks.append('Pfam_current_canonical_coverage')
