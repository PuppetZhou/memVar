"""Build current local Web Parquet tables. No database access or upstream writes."""
from __future__ import annotations
import gzip
import json
import os
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import polars as pl
import pyarrow.parquet as pq
import yaml
from external_references import uniprot_xref_fields

WEB = Path(__file__).resolve().parents[2]
ROOT = WEB.parent
INPUTS = yaml.safe_load((WEB / 'config/inputs.yaml').read_text())
RULES = yaml.safe_load((WEB / 'config/tables.yaml').read_text())


def js(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def read(key, name=None):
    path = ROOT / INPUTS[key]['path']
    return pl.read_parquet(path / (name + '.parquet') if name else path)


def nested(df, key, column):
    return df.group_by(key, maintain_order=True).agg(pl.struct(pl.exclude(key)).alias(column))


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Build:
    def __init__(self, destination):
        self.destination = destination
        self.catalog = []
        self.tables = {}
        self.checks = []
        self.genes = read('protein_gene')
        self.target = self.genes.select('accession').unique()
        self.accessions = set(self.target['accession'])

    def put(self, name, df, group, inputs, key, meaning, status='ready', note=''):
        removed = RULES.get('deduplicated_columns', {}).get(name, [])
        if removed:
            df = df.drop(removed)
        require(df.height > 0, f'{name}: unexpectedly empty')
        if key:
            require(df.select(pl.struct(key).n_unique()).item() == df.height, f'{name}: duplicate key {key}')
            require(not any(df[k].null_count() for k in key), f'{name}: null key')
        if 'accession' in df.columns:
            require(not (set(df['accession'].drop_nulls()) - self.accessions), f'{name}: unknown protein')
        folder = self.destination / group
        folder.mkdir(exist_ok=True)
        path = folder / (name + '.parquet')
        df.write_parquet(path, compression='zstd', statistics=True)
        require(pq.ParquetFile(path).metadata.num_rows == df.height, f'{name}: write count mismatch')
        self.tables[name] = path
        self.catalog.append(dict(name=name, category=group, path=str(path.relative_to(self.destination)),
                                 rows=df.height, bytes=path.stat().st_size, primary_key=key,
                                 grain=meaning, inputs=inputs, status=status, note=note,
                                 deduplicated_columns=removed,
                                 columns={k:str(v) for k,v in df.schema.items()}))
        print(f'{group}/{name}: {df.height:,}', flush=True)

    def fk(self, child, column, parent, parent_column):
        a=pl.read_parquet(self.tables[child], columns=[column]).drop_nulls().unique()
        b=pl.read_parquet(self.tables[parent], columns=[parent_column]).unique()
        require(a.join(b, left_on=column, right_on=parent_column, how='anti').height == 0,
                f'{child}.{column} -> {parent}.{parent_column}: broken reference')
        self.checks.append(f'{child}.{column} -> {parent}.{parent_column}')

    def identity(self):
        entries=read('identity','protein_entry').join(self.target,on='accession',how='semi')
        require(entries.height == len(self.accessions), 'identity target coverage')
        require(entries.filter((pl.col('taxon_id') != 9606) | ~pl.col('reviewed')).height == 0, 'identity scope')
        self.entries={r['accession']:r for r in entries.to_dicts()}
        iso=read('identity','protein_isoform').join(self.target,on='accession',how='semi')
        self.isos=defaultdict(list)
        for r in iso.to_dicts(): self.isos[r['accession']].append(r)
        sequence_ids=set(x for r in iso['sequence_ids'].to_list() for x in r)
        seq=read('identity','protein_sequence').filter(pl.col('accession').is_in(self.accessions) | pl.col('sequence_id').is_in(sequence_ids))
        require(seq.filter(pl.col('length') != pl.col('sequence').str.len_chars()).height==0,'sequence length')
        require(sequence_ids <= set(seq['sequence_id']), 'isoform sequence references')
        self.put('protein',entries.select('accession','entry_name',pl.col('recommended_protein_name').alias('protein_name'),
                 'alternative_protein_names','secondary_accessions',pl.col('primary_gene_names').alias('gene_names'),
                 'taxon_id','reviewed',pl.col('canonical_sequence_id').alias('default_sequence_id'),
                 'entry_version','sequence_version','source_release').with_columns(
                 pl.lit(RULES['metadata']['protein_inclusion_basis']).alias('inclusion_basis')),
                 'identity',['identity','protein_gene'],['accession'],'一个UniProt膜蛋白条目')
        self.put('protein_sequence',seq.select('sequence_id',pl.col('accession').alias('owner_accession'),'is_canonical',
                 'length','sequence','source_release'),'identity',['identity'],['sequence_id'],'一条可获取序列')
        self.put('protein_isoform',iso.drop('isoform_json','source_file'),'identity',['identity'],['accession','isoform_id'],'一条来源isoform声明')
        self.put('protein_gene',self.genes,'identity',['protein_gene'],['accession','hgnc_id'],'已确认蛋白—HGNC关联')
        self.fk('protein','default_sequence_id','protein_sequence','sequence_id')
        xrefs=read('identity','protein_xref').filter(pl.col('database').is_in(['Ensembl','RefSeq'])).join(self.target,on='accession',how='semi')
        rows=[]
        for r in xrefs.iter_rows(named=True):
            fields = uniprot_xref_fields(r)
            # The primary ID is already in external_id; store only its source-declared partners.
            for role in ['gene', 'protein', 'transcript', 'nucleotide']:
                fields.pop(role + '_url')
                if fields['identifier_type'] == role:
                    fields[role + '_id_full'] = None
            # RefSeq's source partner can be an RNA or a genomic molecule (e.g. NC_),
            # so retain NucleotideSequenceId once; typed RNA IDs are exposed by the view.
            fields.pop('transcript_id_full')
            rows.append(dict(reference_id=f"uniprot:{INPUTS['identity']['version']}:{r['accession']}:xref:{r['xref_order']}",accession=r['accession'],
              database_name=r['database'],scope_type='isoform' if r['isoform_id'] else 'entry',scope_id=r['isoform_id'] or r['accession'],
              **fields,source_record_key=str(r['xref_order']),source_release=INPUTS['identity']['version']))
        self.put('protein_external_reference',pl.from_dicts(rows,infer_schema_length=None),'identity',['identity'],['reference_id'],
                 '一条Ensembl/RefSeq来源交叉引用；UniProt/HGNC由统一外链视图组合')

    def scope(self, acc, label):
        if not label: return 'entry', [], 'entry_general'
        # Exact source-declared identifiers/names only; no fuzzy matching or split-name guessing.
        hits=[]
        for r in self.isos[acc]:
            names=[r['isoform_id'],*(r['isoform_aliases'] or []),r['isoform_name'],'Isoform '+r['isoform_name']]
            if label in names: hits.append(r['isoform_id'])
        if len(hits)==1: return 'isoform',hits,'source_name_exact'
        return 'unresolved',[],'scope_unresolved'

    def comments(self):
        functions=[]; locations=[]; seen=set()
        for path in sorted((ROOT/INPUTS['uniprot_pages']['path']).glob('*.json.gz')):
            with gzip.open(path,'rt') as f: entries=json.load(f)['results']
            for e in entries:
                acc=e['primaryAccession']
                if acc not in self.accessions: continue
                seen.add(acc)
                require(any(k['id']=='KW-0472' for k in e.get('keywords',[])),f'{acc}: membrane keyword missing')
                for order,c in enumerate(e.get('comments',[]),1):
                    typ=c['commentType']
                    if typ not in RULES['function_types'] and typ!='SUBCELLULAR LOCATION': continue
                    scope, ids, state=self.scope(acc,c.get('molecule'))
                    row=dict(annotation_id=f'uniprot:2026_03:{acc}:comment:{order}',accession=acc,comment_type=typ,
                      scope_type=scope,scope_label=c.get('molecule'),isoform_ids=ids,mapping_status=state,
                      source_order=order,source_record_key=f'{acc}:comment:{order}',source_release='2026_03')
                    if typ in RULES['function_types']:
                        row['text']='\n\n'.join(t['value'] for t in c.get('texts',[]) if t.get('value')) or None
                        # Preserve selected comment fields and nested evidence pairing, never the entire entry payload.
                        row['structured_items_json']=js({k:v for k,v in c.items() if k not in ['commentType','molecule']})
                        functions.append(row)
                    else:
                        row['locations_json']=js(c.get('subcellularLocations',[]))
                        row['note_json']=js(c.get('note'))
                        locations.append(row)
        require(seen==self.accessions,'raw UniProt / cleaned target mismatch')
        f=pl.from_dicts(functions,infer_schema_length=None)
        self.put('protein_function_annotation',f,'identity',['uniprot_pages','identity'],['annotation_id'],'一条选定类型的原生UniProt功能comment')
        overview=[]
        byacc=defaultdict(list)
        for r in functions:
            if r['comment_type']=='FUNCTION': byacc[r['accession']].append(r)
        for acc in sorted(self.accessions):
            canonical={r['isoform_id'] for r in self.isos[acc] if r['is_canonical']}
            rows=byacc[acc]
            candidates=[r for r in rows if r['text'] and canonical.intersection(r['isoform_ids'])]
            if not candidates: candidates=[r for r in rows if r['text'] and r['scope_type']=='entry']
            selected=min(candidates,key=lambda r:r['source_order']) if candidates else None
            overview.append(dict(accession=acc,default_sequence_id=self.entries[acc]['canonical_sequence_id'],
              default_annotation_id=selected['annotation_id'] if selected else None,
              status='selected' if selected else ('source_missing' if not rows else 'no_applicable_annotation'),
              selection_rule=RULES['metadata']['function_selection_rule']))
        self.put('protein_function_overview',pl.from_dicts(overview),'identity',['uniprot_pages','identity'],['accession'],'每蛋白的默认FUNCTION引用')
        self.fk('protein_function_overview','default_annotation_id','protein_function_annotation','annotation_id')
        self.put('protein_uniprot_location',pl.from_dicts(locations,infer_schema_length=None),'localization',['uniprot_pages','identity'],['annotation_id'],
                 '一条定位comment；原生位置、膜拓扑/朝向及配对证据嵌套保存',note='膜概览复用其中原生topology，不另建重复膜类别表')

    def functional(self):
        go=read('go','go_annotation_protein').join(read('go','go_annotation'),on='annotation_id',how='left',suffix='_annotation')
        go=go.join(nested(read('go','go_annotation_source').drop('source_file'),'annotation_id','source_records'),on='annotation_id',how='left')
        self.put('protein_go_annotation',go,'function_pathway',['go'],['accession','annotation_id'],'一条GO陈述—蛋白关联，保留证据和原对象')
        slim=read('go_slim_mapping')
        category_ids=pl.read_csv(ROOT/INPUTS['go_slim']['path'],separator='\t').select(
            (pl.lit('GO:')+pl.col('?x').str.extract(r'GO_(\d+)')).alias('go_id'))
        wanted=pl.concat([go.select('go_id').unique(),category_ids]).unique()
        terms=read('go','go_term').drop('raw_stanza_json').join(wanted,on='go_id',how='semi').with_columns(
            (pl.lit('https://amigo.geneontology.org/amigo/term/')+pl.col('go_id')).alias('url'),pl.lit(INPUTS['go']['version']).alias('source_release'))
        self.put('go_term',terms,'function_pathway',['go','go_slim'],['go_id'],'项目注释及全部generic slim类别术语；MF/BP/CC共用')
        self.put('go_slim_mapping',slim,'function_pathway',['go_slim_mapping'],['term_id','category_id'],'同aspect的GO term到generic slim类别；is_a/part_of可达关系')
        for column in ['term_id','category_id']: self.fk('go_slim_mapping',column,'go_term','go_id')
        self.fk('protein_go_annotation','go_id','go_term','go_id')
        paths=read('reactome','reactome_pathway').join(nested(read('reactome','reactome_pathway_description').drop('name'),'pathway_id','descriptions'),on='pathway_id',how='left')
        self.put('pathway',paths.with_columns(pl.lit('Reactome').alias('source')),'function_pathway',['reactome'],['source','pathway_id'],'一个来源通路及全部来源说明')
        for name,src,key,meaning in [('pathway_relation','reactome_pathway_relation',['parent_id','child_id'],'一条通路父子关系'),('pathway_topic','reactome_pathway_topic',['pathway_id','topic_id'],'一条通路—官方主题关系')]:
            d=read('reactome',src)
            if name=='pathway_topic': d=d.drop('pathway_name','topic_name')
            self.put(name,d.with_columns(pl.lit('Reactome').alias('source')),'function_pathway',['reactome'],key,meaning)
        assoc=read('reactome','reactome_association_protein').join(read('reactome','reactome_protein_pathway'),on='association_id',how='left',suffix='_source')
        assoc=assoc.join(nested(read('reactome','reactome_association_source'),'association_id','source_records'),on='association_id',how='left').with_columns(pl.lit('Reactome').alias('source'))
        self.put('protein_pathway',assoc,'function_pathway',['reactome'],['accession','association_id'],'一条来源通路关联—蛋白关系')
        self.fk('protein_pathway','pathway_id','pathway','pathway_id')
        for table,col in [('pathway_relation','parent_id'),('pathway_relation','child_id'),('pathway_topic','pathway_id'),('pathway_topic','topic_id')]: self.fk(table,col,'pathway','pathway_id')
        compounds=read('rhea','rhea_compound').drop('details_json').rename({'accession':'compound_accession'})
        participants=read('rhea','rhea_reaction_participant').drop('participant_details_json').join(compounds,on='compound_uri',how='left')
        reactions=read('rhea','rhea_reaction').drop('details_json').join(nested(participants,'rhea_id','participants'),on='rhea_id',how='left')
        self.put('rhea_reaction',reactions,'function_pathway',['rhea'],['rhea_id'],'一个原生反应方向实体，参与物有序嵌套')
        assoc=read('rhea','rhea_association_protein').drop('source_accession').join(read('rhea','rhea_protein_reaction'),on='association_id',how='left')
        check=assoc.join(reactions.select('rhea_id','master_id','direction'),on='rhea_id',how='left',suffix='_reaction')
        require(check.height==assoc.height and check.filter(
            ~pl.col('master_id').eq_missing(pl.col('master_id_reaction')) |
            ~pl.col('direction').eq_missing(pl.col('direction_reaction'))).is_empty(),'Rhea duplicated attributes differ')
        self.put('protein_rhea_reaction',assoc,'function_pathway',['rhea'],['accession','association_id'],'一条来源反应关联—蛋白关系')
        self.fk('protein_rhea_reaction','rhea_id','rhea_reaction','rhea_id')
        targets=read('gtopdb','gtopdb_target').select('target_id','target_name','type','subunit_id','subunit_name','human_swissprot','source_record_id','source_release','source_url')
        families=read('gtopdb','gtopdb_target_family').select('target_id','family_id','family_name','source_record_id')
        self.put('gtopdb_target',targets.join(nested(families,'target_id','families'),on='target_id',how='left'),'function_pathway',['gtopdb'],['target_id'],'一个药理学靶点，保留亚基及家族')
        ligand=read('gtopdb','gtopdb_ligand').select('ligand_id','name','type','species','smiles','inchi','inchikey','uniprot_id','ensembl_id','pubchem_cid','chembl_id','source_record_id','source_release','source_url')
        pep=read('gtopdb','gtopdb_peptide').select('ligand_id','source_record_id','source_release','single_letter_amino_acid_sequence','three_letter_amino_acid_sequence','helm','post_translational_modification','chemical_modification','subunit_ids','subunit_names','smiles','inchi','inchikey')
        self.put('gtopdb_ligand',ligand.join(nested(pep,'ligand_id','peptide_records'),on='ligand_id',how='left'),'function_pathway',['gtopdb'],['ligand_id'],'一个配体及化学结构、全部肽来源记录')
        context=read('gtopdb','gtopdb_association_protein')
        records=[]
        for kind in ['interaction','endogenous_pairing','endogenous_detail']:
            d=read('gtopdb','gtopdb_'+kind)
            d=d.drop([c for c in ['approved','patent_numbers','target','ligand','target_name','ligand_name','target_url','ligand_url'] if c in d.columns])
            records.append(d.rename({'record_kind':'record_type'}))
        record=pl.concat(records,how='diagonal_relaxed').join(nested(context,'association_id','protein_contexts'),on='association_id',how='left')
        self.put('gtopdb_record',record,'function_pathway',['gtopdb'],['record_type','source_record_id'],'一条原生药理作用/配对/详情；保留逐记录蛋白上下文')
        direct=read('gtopdb','gtopdb_target_protein').with_columns(pl.lit('source_target_accession').alias('relationship'))
        contextual=context.join(record.select('association_id','target_id'),on='association_id',how='left').select('target_id','accession','relationship','source_accession','mapping_status',pl.col('association_id').alias('source_record_id'))
        bridge=pl.concat([direct.drop('source_url'),contextual],how='diagonal_relaxed')
        bridge=bridge.group_by('target_id','accession','relationship',maintain_order=True).agg(pl.struct('source_accession','mapping_status','source_record_id').alias('supporting_records'))
        self.put('protein_gtopdb_target',bridge,'function_pathway',['gtopdb'],['target_id','accession','relationship'],'蛋白—靶点—关系类型，官方映射和复合体背景分开')
        for t,c,p in [('gtopdb_record','target_id','gtopdb_target'),('gtopdb_record','ligand_id','gtopdb_ligand'),('protein_gtopdb_target','target_id','gtopdb_target')]: self.fk(t,c,p,c)

    def localization(self):
        hpa=read('hpa')
        bridge=self.genes.join(read('gene_ensembl').select('hgnc_id','ensembl_gene_id'),on='hgnc_id').select('accession','hgnc_id','ensembl_gene_id').unique()
        d=hpa.join(nested(bridge,'ensembl_gene_id','protein_contexts'),left_on='Gene',right_on='ensembl_gene_id',how='left')
        require(d['protein_contexts'].null_count()==0,'HPA gene link missing')
        d=d.with_columns(pl.lit(INPUTS['hpa']['version']).alias('source_snapshot'),
                        (pl.lit('https://www.proteinatlas.org/')+pl.col('Gene')+pl.lit('/subcellular')).alias('url'))
        self.put('hpa_subcellular_location',d,'localization',['hpa','protein_gene','gene_ensembl'],['Gene'],'源基因定位汇总及已确认蛋白关联',note='原生逐位置可靠性列原样保存；不把顶层Reliability赋给所有位置')

    def membrane(self):
        identities=read('membrane','identity_link')
        topo=identities.filter(pl.col('dataset_id').is_in(RULES['topology_datasets']))
        src=read('membrane_source','source_sequence').join(topo.select(pl.col('source_object_id').alias('source_sequence_id')).unique(),on='source_sequence_id',how='semi')
        src=src.join(nested(topo.drop('dataset_id','tm_reporting_subset').rename({'source_object_id':'source_sequence_id'}),'source_sequence_id','protein_contexts'),on='source_sequence_id',how='left')
        record=read('membrane_source','source_record').select('record_id','native_id','archive_member')
        src=src.join(record,on='record_id',how='left')
        self.put('membrane_topology_source',src,'membrane',['membrane','membrane_source'],['source_sequence_id'],'来源序列/结构链及蛋白身份关联；不等于坐标映射')
        feat=read('membrane_source','source_feature').join(src.select('source_sequence_id'),on='source_sequence_id',how='semi')
        self.put('membrane_topology_feature',feat,'membrane',['membrane_source','membrane'],['feature_id'],'原生区段/方法预测/约束，含未定位记录')
        loc=read('membrane','feature_location').join(feat.select('feature_id'),on='feature_id',how='semi')
        self.put('membrane_topology_location',loc,'membrane',['membrane'],['feature_id','mapping_id','block_index'],'已发布exact映射后的明确序列区段')
        dom=read('membrane','domain_feature_link').join(feat.select('feature_id'),on='feature_id',how='semi').join(read('membrane_source','domain_side_annotation').drop('payload'),on='model_record_id',how='left')
        self.put('membrane_topology_domain',dom,'membrane',['membrane','membrane_source'],['feature_id','model_record_id'],'来源TOPDOM约束及模型侧别；不是新domain扫描')
        for t,c,p,pc in [('membrane_topology_feature','source_sequence_id','membrane_topology_source','source_sequence_id'),('membrane_topology_location','feature_id','membrane_topology_feature','feature_id'),('membrane_topology_location','sequence_id','protein_sequence','sequence_id'),('membrane_topology_domain','feature_id','membrane_topology_feature','feature_id')]: self.fk(t,c,p,pc)
        contact=identities.filter(pl.col('dataset_id').is_in(['BioDolphin','MPLID'])).drop('tm_reporting_subset')
        self.put('membrane_contact_identity',contact,'membrane',['membrane'],['dataset_id','source_object_id','accession'],'接触来源对象—蛋白身份关联',status='source_coordinates_only',note='身份关联自身不证明坐标；使用对应的已验证位点mapping表')
        bio=read('membrane_source','biodolphin_interaction').join(contact.filter(pl.col('dataset_id')=='BioDolphin').select(pl.col('source_object_id').alias('source_sequence_id')).unique(),on='source_sequence_id',how='semi')
        keep=['interaction_id','source_sequence_id','BioDolphinID','protein_UniProt_ID','entry_source']+[c for c in bio.columns if c.startswith('complex_') or c.startswith('lipid_')]
        bio=bio.select(keep).join(nested(read('membrane_source','interaction_site'),'interaction_id','source_sites'),on='interaction_id',how='left').with_columns(pl.lit('not_projected').alias('sequence_mapping_status'))
        sites=read('site_mapping','biodolphin_site_mapping')
        native_sites=read('membrane_source','interaction_site').join(bio.select('interaction_id'),on='interaction_id',how='semi')
        site_keys=['interaction_id','coordinate_system','site_order']
        require(native_sites.sort(site_keys).equals(sites.select(native_sites.columns).sort(site_keys),null_equal=True),
                'BioDolphin source_sites differs from independent site table')
        summary=sites.group_by('interaction_id').agg(pl.len().alias('source_site_rows'),(pl.col('mapping_status')=='mapped').sum().alias('mapped_site_rows'))
        bio=bio.drop('sequence_mapping_status').join(summary,on='interaction_id',how='left').with_columns(
            pl.when(pl.col('source_site_rows').is_null()).then(pl.lit('source_sites_absent'))
            .when(pl.col('mapped_site_rows')==pl.col('source_site_rows')).then(pl.lit('all_source_sites_mapped'))
            .when(pl.col('mapped_site_rows')>0).then(pl.lit('partially_mapped'))
            .otherwise(pl.lit('no_verified_mapping')).alias('sequence_mapping_status'))
        self.put('membrane_biodolphin_interaction',bio,'membrane',['membrane_source','membrane','site_mapping'],['interaction_id'],'蛋白链—配体实例及来源编号位点',status='mapping_processed',note='位点映射见membrane_biodolphin_site；PDB和Re-numbered分别保留，不当作两组独立位点')
        mplid=read('site_mapping','mplid_residue_mapping').drop('identity_confirmed','sifts_candidate_count')
        self.put('membrane_mplid_residue',mplid,'membrane',['site_mapping'],['source_member','source_row'],
                 '来源PDB链残基观察及已验证位置/失败状态',status='mapping_processed',note='仅mapping_status=mapped可用于序列坐标查询；保留来源正负标签')
        self.put('membrane_biodolphin_site',sites,'membrane',['site_mapping'],['interaction_id','coordinate_system','site_order'],
                 '一个来源位点词项及验证后的序列位置/失败状态',status='mapping_processed')
        self.fk('membrane_biodolphin_site','interaction_id','membrane_biodolphin_interaction','interaction_id')
        opm=read('site_mapping','opm_residue_mapping').select(
            'source_observation_id','source_accession','pdb_id','model_id','local_chain_id','pdb_resseq','insertion_code','pdb_residue',
            'accession','sequence_id','target_position','target_residue','mapping_status','mapping_method','is_wildtype_residue',
            'sifts_date','sifts_uniprot_release','sifts_pdb_release','foundation_release','selected_altloc',
            'geometry_type','observed_dum_surface','membrane_half_thickness_A','site_coordinate_basis',
            'site_signed_depth_A','ca_signed_depth_A','distance_to_boundary_A','distance_outside_membrane_A',
            'distance_to_midplane_A','distance_to_observed_surface_A','heavy_atom_fraction_in_core','atoms_cross_boundary',
            pl.col('rule_version').alias('source_geometry_rule_version')).with_columns(
            (pl.col('pdb_id')+pl.lit('.pdb')).alias('source_structure_key'))
        self.put('membrane_opm_observation',opm,'membrane',['site_mapping'],['source_observation_id'],
                 '一个来源OPM结构残基观察及新核对的位置/失败状态',status='mapping_processed',
                 note='连续几何值来自原OPM结构观察；不导入旧膜分类、侧别共识及2Å关系标签')
        deep=read('site_mapping','deeptmhmm2_prediction').rename({'accession':'owner_accession'})
        self.put('deeptmhmm2_prediction',deep,'membrane',['site_mapping'],['sequence_id'],
                 '一条与当前输入序列完全一致的DeepTMHMM2预测',note='计算预测；含全部阴性及不适用概率状态')
        self.put('deeptmhmm2_segment',read('site_mapping','deeptmhmm2_segment'),'membrane',['site_mapping'],
                 ['sequence_id','segment_order'],'一条DeepTMHMM2预测区段；1-based闭区间')
        for table in ['membrane_mplid_residue','membrane_biodolphin_site','membrane_opm_observation','deeptmhmm2_prediction','deeptmhmm2_segment']:
            self.fk(table,'sequence_id','protein_sequence','sequence_id')
        self.put('protein_membrane_label',read('membrane_labels'),'membrane',['membrane_labels'],
                 ['accession','sequence_id','label'],'canonical蛋白四类膜标签及明确UniProt支持；具体标签可重叠')
        self.fk('protein_membrane_label','sequence_id','protein_sequence','sequence_id')
        classification=read('membrane_classification')
        require(classification.height==len(self.accessions),'primary membrane classification target coverage')
        require(classification['accession'].n_unique()==len(self.accessions),'one primary membrane classification per protein')
        require(classification.filter(
            (pl.col('primary_class')=='transmembrane') != (pl.col('canonical_tm_feature_count')>0)
        ).height==0,'transmembrane class and canonical feature count agree')
        self.put('protein_membrane_classification',classification,'membrane',['membrane_classification'],
                 ['accession'],'每个canonical蛋白一个互斥膜主类、父类及跨膜子类；原重叠证据另见protein_membrane_label')
        self.fk('protein_membrane_classification','sequence_id','protein_sequence','sequence_id')

    def validate(self):
        # All exact topology coordinates must fall in the associated sequence, without remapping.
        loc=pl.read_parquet(self.tables['membrane_topology_location'])
        seq=pl.read_parquet(self.tables['protein_sequence']).select('sequence_id','length')
        invalid=loc.join(seq,on='sequence_id').filter((pl.col('start')<1)|(pl.col('end')<pl.col('start'))|(pl.col('end')>pl.col('length')))
        require(invalid.height==0,'topology coordinate bounds')
        overview=pl.read_parquet(self.tables['protein_function_overview'])
        annotations=pl.read_parquet(self.tables['protein_function_annotation'])
        chosen=overview.filter(pl.col('default_annotation_id').is_not_null()).join(annotations,left_on='default_annotation_id',right_on='annotation_id',suffix='_annotation')
        require(chosen.filter((pl.col('accession')!=pl.col('accession_annotation'))|(pl.col('comment_type')!='FUNCTION')).height==0,'FUNCTION ownership')
        # Full source record counts are conserved by lossless joins and the typed GtoPdb union.
        expected={'protein_go_annotation':read('go','go_annotation_protein').height,
                  'protein_pathway':read('reactome','reactome_association_protein').height,
                  'protein_rhea_reaction':read('rhea','rhea_association_protein').height,
                  'gtopdb_record':sum(read('gtopdb','gtopdb_'+k).height for k in ['interaction','endogenous_pairing','endogenous_detail'])}
        for name,count in expected.items(): require(pq.ParquetFile(self.tables[name]).metadata.num_rows==count,f'{name}: count conservation')
        # Nested records must preserve all evidence contexts and reaction participants.
        for table, column, source_key, source_table in [
            ('protein_go_annotation','source_records','go','go_annotation_source'),
            ('gtopdb_record','protein_contexts','gtopdb','gtopdb_association_protein'),
            ('rhea_reaction','participants','rhea','rhea_reaction_participant'),
            ('gtopdb_ligand','peptide_records','gtopdb','gtopdb_peptide')]:
            output=pl.read_parquet(self.tables[table])
            # GO source links can occur once per linked protein; compare after annotation de-duplication.
            if table=='protein_go_annotation': output=output.unique('annotation_id')
            require(output.select(pl.col(column).list.len().sum()).item()==read(source_key,source_table).height,
                    f'{table}: nested source records lost')
        self.checks.append('nested_GO_GtoPdb_Rhea_evidence_and_peptide_counts')
        # Exercise the P00533 protein -> GO/pathway/reaction/target links on actual output.
        example={}
        for name in ['protein','protein_function_annotation','protein_go_annotation','protein_pathway','protein_rhea_reaction','protein_gtopdb_target','membrane_topology_location']:
            example[name]=pl.scan_parquet(self.tables[name]).filter(pl.col('accession')=='P00533').select(pl.len()).collect().item()
        require(all(example[k]>0 for k in example),'P00533 query chain')
        return dict(status='passed',protein_count=len(self.accessions),table_count=len(self.catalog),
                    checks=['table_primary_keys','protein_scope','sequence_lengths','isoform_sequence_references',
                            'membrane_keyword','FUNCTION_ownership','topology_coordinate_bounds','source_record_count_conservation',*self.checks],
                    example_P00533=example,postgresql='not_imported')


def main():
    data=WEB/'data'; data.mkdir(exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='.tables-',dir=data))
    try:
        build=Build(temporary)
        for stage in [build.identity,build.comments,build.functional,build.localization,build.membrane]: stage()
        from sequence_tables import build_sequence
        build_sequence(build)
        validation=build.validate()
        built_at=datetime.now(timezone.utc).isoformat()
        manifest=dict(data_version=RULES['data_version'],built_at=built_at,inputs=INPUTS,rules=RULES,tables=build.catalog,validation=validation)
        # Independently published variant tables share this directory, not this build.
        extension = data/'tables/variant'
        if (extension/'manifest.json').exists():
            shutil.copytree(extension, temporary/'variant', copy_function=os.link)
            vm = json.loads((extension/'manifest.json').read_text())
            manifest['extensions'] = {'variant': {'manifest': 'variant/manifest.json', 'data_version': vm['data_version']}}
        (temporary/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        lines=['# 当前本地网站服务表','',f"数据版本：`{RULES['data_version']}`。",'',f'构建时间（UTC）：{built_at}。构建验证通过；数据库导入状态见[导入报告](postgresql_import.json)，须与本次built_at一致；[查询验证](postgresql_validation.json)独立记录。',
               '',f'共{len(build.catalog)}张Parquet表；蛋白范围{len(build.accessions):,}个。表文件按identity、function_pathway、localization、membrane、sequence分类。',
               '', '构建入口：`python src/build/build_tables.py`（Web目录）；依赖polars、pyarrow、PyYAML。',
               '输入快照见[inputs.yaml](../config/inputs.yaml)，选择及暂缓项见[tables.yaml](../config/tables.yaml)。',
               '完整字段类型、主键、输入、行数和验证记录见[manifest.json](tables/manifest.json)。',
               '', '原生注释与预测/约束保留来源和method/role；缺失不补零。接触与OPM仅mapping_status=mapped可按目标坐标查询；未映射来源记录保留。',
               'UniProt功能/定位从同版raw选择comment并机械解析，不消费探索runs、不改写注释；scope无法精确解析时保留unresolved。',
               '四类膜标签和GO slim映射读取负责模块curated；统一外链及可恢复冗余属性通过PostgreSQL普通视图查询。',
               '', '| 分类 | 表 | 行数 | 一行含义 | 状态 |','|---|---|---:|---|---|']
        for t in build.catalog:
            lines.append(f"| {t['category']} | [{t['name']}](tables/{t['path']}) | {t['rows']:,} | {t['grain']} | {t['status']} |")
        lines+=['','## 本轮未构建','']+[f'- **{k}**：{v}。' for k,v in RULES['deferred'].items()]
        lines+=['','以上为未接入/未计算，不代表来源无数据。GO CC复用GO表；序列、结构及位点页面复用膜表，不重复保存。',
                '', '## 验证范围','', '已核对所有表主键、蛋白范围、关键外键、序列长度、默认FUNCTION归属、已映射拓扑坐标边界和功能来源记录数守恒，并查询P00533关联链。',
                '本脚本仅验证Parquet；PostgreSQL导入/查询状态以相同built_at的报告为准。未进行API、页面或并发负载验证。所有文件先在临时目录构建并验证，通过后替换当前目录；正常异常恢复旧目录，不保留历史数据版本。']
        destination=data/'tables'; previous=data/'.tables-previous'
        require(not previous.exists(),'Previous interrupted replacement exists; inspect data/.tables-previous before rebuilding')
        if destination.exists(): os.replace(destination,previous)
        try: os.replace(temporary,destination)
        except BaseException:
            if previous.exists(): os.replace(previous,destination)
            raise
        if previous.exists(): shutil.rmtree(previous)
        readme=data/'.README.md.tmp'; readme.write_text('\n'.join(lines)+'\n'); os.replace(readme,data/'README.md')
        print(json.dumps(validation,ensure_ascii=False,indent=2))
    finally:
        if temporary.exists(): shutil.rmtree(temporary)


if __name__=='__main__': main()
