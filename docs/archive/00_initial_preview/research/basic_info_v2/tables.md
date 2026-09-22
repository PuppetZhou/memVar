# 当前33表的关联与精简审查

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

2026-09-21：本页是候选精简审查。实际采纳字段、统一外链视图与NC_编号边界修正见[版本记录](../../../../record/00_initial_preview/20260921_basic_info_v2.md)；未采纳建议不能解读为已经删列。

本轮只读核对当前PostgreSQL构建清单及表体积，对照全部33张Parquet的schema与列压缩元数据；对少数候选冗余做定向等价检查。没有全库扫描所有字段，没有删除列。机器清单见[table_inventory.json](results/table_inventory.json)，相等性检查见[redundancy_checks.json](results/redundancy_checks.json)。

## 1. 如何link

共同原则：身份用accession，具体残基对象用sequence_id，来源实体用各自ID；没有关联时允许NULL/空集合，不按名称、相同基因或截断isoform后缀猜连接。所有一对多查询先确定粒度，不能把多个独立数组展开后作笛卡尔乘积。

| 内容及现有表 | 关联路径 | 特别注意 |
| --- | --- | --- |
| protein、protein_sequence | protein.default_sequence_id → protein_sequence.sequence_id | sequence_id虽然可能与accession字符串相同，仍是不同实体键 |
| protein_isoform | (accession, isoform_id) → sequence_ids数组 → protein_sequence.sequence_id | 显式isoform -1可指向不带-1的canonical序列；跨条目关系和不可获取状态保留 |
| protein_gene | protein.accession → protein_gene.accession → hgnc_id | 多对多；基因身份不证明isoform序列对应 |
| protein_external_reference | accession；scope_type=isoform时用(accession,scope_id)连isoform声明；gene时连HGNC | 外部ID类型与适用范围是两件事。ENST是转录本编号，也可能出现在某个isoform的xref记录中 |
| protein_function_overview、protein_function_annotation | overview.accession → protein；default_annotation_id → annotation.annotation_id；全部注释按accession取 | 未解析具名对象不进canonical补填；通用注释保留entry语义 |
| protein_go_annotation、go_term | accession → annotation；go_id → go_term.go_id | 同时保留subject_id、form_id、relation、extension和原证据；MF/BP/CC共用 |
| protein_pathway、pathway、pathway_relation、pathway_topic | accession → protein_pathway → (source,pathway_id)；parent/child/topic ID再连同source的pathway | 当前仅Reactome，所以现有数据库有pathway_id唯一索引；以后多来源必须将source纳入FK与关系主键 |
| protein_rhea_reaction、rhea_reaction | accession → protein_rhea_reaction.rhea_id → rhea_reaction | master_id只是方向家族关系，不把其他方向自动加给蛋白 |
| protein_gtopdb_target、gtopdb_target、gtopdb_record、gtopdb_ligand | accession → target桥 → target；每条record的protein_contexts限定实际关联，再通过target_id/ligand_id连字典 | 不能把桥上一个target的所有records都自动归给每个蛋白；复合体背景与自身靶点分开 |
| protein_uniprot_location | accession → 原comment；isoform_ids → 同条目isoform声明 | 保留位置、topology、orientation的原配对关系和限定条件 |
| hpa_subcellular_location | Gene=Ensembl gene ID；protein_contexts数组中保存已确认accession/HGNC关联 | 当前Web没有单独gene_ensembl表，实际桥已嵌入；不能假定数据库中存在该上游表，也不能把Gene当HGNC ID |
| membrane_uniprot_feature | accession；mapped_sequence_id → protein_sequence.sequence_id；feature_id标识原feature | source_sequence_id、mapped_sequence_id含义分开；坐标是否可用看coordinate_status/can_locate_exactly |
| membrane_topology_source、membrane_topology_feature、membrane_topology_location、membrane_topology_domain | source_sequence_id连source与feature；feature_id连location/domain；location.sequence_id连目标序列；model_record_id标记约束模型 | 原始来源坐标与映射后坐标不能混用；同feature可有多mapping/block；source中protein_contexts只是身份背景 |
| membrane_contact_identity、membrane_biodolphin_interaction、membrane_biodolphin_site | BioDolphin的source_object_id ↔ interaction.source_sequence_id；interaction_id → site；site.sequence_id → 目标序列 | site表按interaction_id+coordinate_system+site_order保留两套编号，不能算两次独立位点 |
| membrane_contact_identity、membrane_mplid_residue | (dataset_id=MPLID, source_object_id)连来源残基；成功mapping的sequence_id+target_position连目标位点 | 同源对象可关联多个accession，不能只靠来源对象身份展开后继承坐标 |
| membrane_opm_observation | accession连蛋白；sequence_id+target_position连位点；source_structure_key与PDB/model/chain定位来源观察 | 保留逐结构几何，不跨结构平均；只有mapping_status=mapped用于目标坐标查询 |
| deeptmhmm2_prediction、deeptmhmm2_segment | sequence_id → protein_sequence；sequence_id连prediction与segment | owner_accession不是所有声明它的条目；跨条目使用需经过isoform声明 |

新GO slim桥和膜标签表按[rules](rules.md)关联。数据库不应为页面每个小板块重新复制protein或sequence表。

## 2. 值得精简的字段

下表是改造清单建议，除外链代码修复外尚未执行投影变更。裁剪发生在Web服务层，上游原生和正式科研表不删。

| 表／组 | 值得精简的列或结构 | 保留及实施条件 |
| --- | --- | --- |
| protein | inclusion_basis的固定长句移到构建元数据；entry_version/sequence_version/source_release可保留为内部元数据 | accession、名称、别名、gene_names、default_sequence_id保留；不为节省很小空间删除有用身份字段 |
| protein_sequence | 当前已经精简；source_release可由数据集说明提供 | sequence_id、owner_accession、is_canonical、length、sequence保留；不合并序列字符串相同但ID不同的实体 |
| protein_isoform | source_database/source_release移到元数据；sequence_parent_accessions可经sequence_ids查owner；has_cross_entry_sequence可派生 | isoform声明、alias、sequence_ids、source_sequence_status、sequence_available及失败原因保留；来源comment/isoform顺序至少保留可定位原记录的键 |
| protein_gene | 现有4列无需再缩 | accession、hgnc_id、hgnc_status、evidence均有作用 |
| protein_external_reference | 当前修复先补齐类型、转录本编号和各角色URL；将来可用带kind/id/url的related_identifiers替代稀疏角色列，但本版不为缩列增加一套链接表 | accession、来源记录键、database_name、原external_id、scope及真实配对关系不能删；重复URL不值得单独改变粒度 |
| protein_function_overview | default_sequence_id可从protein取得；selection_rule固定字符串移到构建元数据 | accession、default_annotation_id、status保留；7,715行default_sequence_id已核对与protein完全一致 |
| protein_function_annotation | text与structured_items_json中的texts[].value重复，可在后续投影中只保留一份有序文本+配对证据，再按需组合文本 | 当前先不盲删JSON：催化反应、辅因子结构和逐段证据都在其中；source_order负责既定选择规则，不能误删 |
| protein_uniprot_location | 固定comment_type、source_release可移到元数据；source_order若可从来源键还原可不单列 | locations_json的配对结构、note、scope、isoform_ids、mapping_status保留，不做最终定位 |
| protein_go_annotation | symbol、object_name、synonyms属于来源对象描述，可从服务注释表去除；aspect可通过go_term.namespace取；ontology_version移元数据 | 原对象subject_id/form_id/object_id、原GO ID及解析后go_id、relation、is_negative、evidence_code、reference、with_from、extension、assigned_by、必要状态及source_records保留。两个mapping_status属于不同层次，不能因名称相似删一列 |
| go_term | 当前无任意本体浏览需求，subsets全列表可由选定slim桥替代；若服务端不解析别名，alt_ids留上游 | go_id、名称、namespace、定义、obsolete与链接保留；不要只剩slim类别 |
| pathway、pathway_relation、pathway_topic、protein_pathway | 关系表中species/release、可从pathway还原的URL与来源固定值可集中；主题表species可移除 | source+ID、父子/主题关系、不同证据及mapping_level保留；pathway.disease_pathway_status为Reactome自身属性，不是Basic info疾病xref，本轮不误删 |
| protein_rhea_reaction | master_id、direction从rhea_reaction取得；常量source_release可集中 | 两列已对13,145行核对完全一致；保留accession、association_id、rhea_id、mapping_status、source_accession及原来源记录键 |
| rhea_reaction | source_release移元数据；不再展开完整原始RDF | equation、direction、is_transport、participants的侧别/计量/ChEBI必须保留；参与物URI不能按名字合并 |
| gtopdb_target、gtopdb_ligand | 共有版本集中；重复名称继续从字典查询 | 家族/亚基、物种、化学结构、完整肽序列及修饰保留，用户此前已明确纳入 |
| gtopdb_record | 当前带类型union约70列，可将各类型专用的稀疏字段放details JSONB，核心ID、record_type、action、可查询数值保留列 | 此举主要简化schema，不保证压缩空间显著下降。原测量文本与numeric解析值不是重复事实：关系符、单位、失败状态必须留；记录自己的亚基/物种/上下文不能简单从target字典覆盖 |
| hpa_subcellular_location | 若Gene name与基础名称用途重复，可不作为服务字段；source_snapshot集中；不需要的单细胞变化/周期字段可留上游 | Gene、主/附加/胞外位置、总体及逐位置可靠性、GO ID与protein_contexts保留；此类可选科学背景列需按最终范围确认后再裁剪 |
| membrane_uniprot_feature | sequence_length从序列表取；detail_id已无Web详情表可作为内部回溯字段或移出；dataset与固定分组值集中 | 当前source_sequence_id与mapped_sequence_id的43,014行值相等，但含义不同，通用映射设计不据此删原对象。label与description有74行不同，不能当重复列直接删除 |
| membrane_topology_source | archive_member、identity_status等归来源详情；已确认完全相同的来源序列可用目标sequence_id引用，但不能无条件删sequence | 原生来源序列/结构链可与目标不同；declared_length与actual_length不一定相等，需保留来源异常能力 |
| membrane_topology_feature | raw_attributes占本表Parquet压缩量约73%，优先梳理其中已列化的start/end/type/method等重复键；其余约束详情可移到按feature_id查询的详情表 | 不能整列删除：来源独有约束和方法参数可能只在这里。新增详情表是为了减少常用查询负载，不是减少事实 |
| membrane_topology_location、membrane_topology_domain | foundation_release移元数据；dataset_id/method可在验证相等后经feature或source取得 | feature_id/mapping_id/block_index、sequence_id及目标start/end必须保留；同名source与target坐标不互相替换；domain模型侧别与support保留 |
| membrane_contact_identity | 现有5列已接近最小 | 这是来源身份桥，不与位点表强并，以保留没有成功mapping的来源对象 |
| membrane_biodolphin_interaction | source_sites与原编号字符串、派生site表存在重叠，可保留一份原词项和完整解析状态后精简重复容器；source_site_rows/mapped_site_rows可按site派生 | interaction_id、来源对象、PDB/链、配体、测量条件及亲和力保留；lipid_disease等非接触分析字段可留上游，但不借Basic info移除疾病xref指令自动删除所有名称含disease的列 |
| membrane_mplid_residue | split、cluster_id是来源训练/基准上下文，可只留上游；SIFTS日期及版本、foundation_release移到来源元数据；详细中间SIFTS注释可留核查层 | source_member/source_row、PDB/链/插入码、原残基、接触标签、距离/confidence、目标坐标及失败原因保留。去掉日期列前按实际文件/结构维度集中，不能伪造整个来源同一日期 |
| membrane_biodolphin_site | foundation_release移元数据；反查PDB等可经interaction取得，但必须先确认source_chain_id与原链/映射链的区别 | interaction_id、coordinate_system、site_order、raw_token、原坐标、parse/mapping状态、目标坐标及mapping_method保留 |
| membrane_opm_observation | SIFTS/基准版本与结构固定属性按source_structure_key集中；可把mapping审计细节留上游 | 多个深度、距离和膜内原子比例是不同物理量，不因占空间就删掉；未定义目标字段前不把全部连续几何合成类别或单值 |
| deeptmhmm2_prediction、deeptmhmm2_segment | seconds、finished_at、prediction_run等运行管理列移元数据/上游；sequence_length、owner_accession、is_canonical可由sequence表查；probabilities_raw_21若保留完整等价解析结构后可不重复入Web | topology_string与topology_io含义不同，未核对不能当重复；保留protein_type、预测/失败状态、适用性、所需概率与区段，不把真实0和不适用合并 |

## 3. 空间与取舍

当前数据库表及索引合计的主要占用：OPM约1102 MB、拓扑feature约761 MB、拓扑location约443 MB、MPLID约440 MB、GO annotation约299 MB。这是本次只读pg_total_relation_size值，不是删列后能保证节省的空间。

Parquet压缩元数据显示：OPM主要体积来自真实连续几何；MPLID主要来自距离；拓扑feature主要来自raw_attributes；GO有明显来源/描述重复；DeepTMHMM2同时保存原21项概率和解析JSON。优先精简重复描述与运行信息，不以删除科学数值换小表。

不建议为了少表将33表合成宽表。当前实体/关系拆分总体合理；可先保持33表，修复xref和裁剪冗余。后续新增GO slim桥、膜标签表有明确用途；是否把拓扑详情另拆一表由实际查询需求决定，不预先以减少表数为目标。

## 4. 推荐执行顺序

1. 已执行代码修复：正确编号类型、RefSeq配对、NULL保留；在临时目录完成必要验证，尚未刷新现有服务表。
2. 第一批字段优化建议：移出固定运行元数据，去掉overview.default_sequence_id和Rhea关系表master_id/direction，删除GO来源对象名称冗余；这些不改变已确认科学内容。
3. 第二批结构优化建议：清理拓扑raw_attributes重复键、整理GtoPdb专用详情、去掉功能原文的双份存储；先保证所有证据和对象语义仍能从服务数据取得，再验证实际字段及查询。
4. GO slim与膜标签先完成负责模块派生；Web链接对应实体。最终服务数据验证通过后再更新PostgreSQL。
