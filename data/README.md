# 当前本地网站服务表

数据版本：`20260922_membrane_classification_v1`。

构建时间（UTC）：2026-09-21T17:55:07.146851+00:00。构建验证通过；数据库导入状态见[导入报告](postgresql_import.json)，须与本次built_at一致；[查询验证](postgresql_validation.json)独立记录。

共47张Parquet表；蛋白范围7,715个。表文件按identity、function_pathway、localization、membrane、sequence分类。

构建入口：`python src/build/build_tables.py`（Web目录）；依赖polars、pyarrow、PyYAML。
输入快照见[inputs.yaml](../config/inputs.yaml)，选择及暂缓项见[tables.yaml](../config/tables.yaml)。
完整字段类型、主键、输入、行数和验证记录见[manifest.json](tables/manifest.json)。

2026-09-22增量：VA-06代表ENSP→UniProt全长精确序列关系单独使用[variant配置](../config/variant.yaml)与`python src/build/build_variant_sequence.py`投影（Web目录），不重跑上述47张基础表或Variant主分区。已发布[status表](tables/variant_sequence/representative_protein_sequence_status.parquet)7707行、[候选序列关系表](tables/variant_sequence/representative_uniprot_sequence_relation.parquet)16665行，输入为foundation已确认快照；[独立manifest](tables/variant_sequence/manifest.json)。`python src/database/import_variant_sequence.py`已导入`web_variant_sequence` schema，orphan 0、7242条exact-match与状态汇总一致；API仅对核对为同一代表ENST/ENSP/选择方法的变异后果展示目标。该增量不改变基础表数据版本与47张计数，详见[执行记录](../docs/record/01_preview_optimization/20260922_parallel_web_execution.md)。

2026-09-22增量：DI-03/04当前SNV条件级证据读取[disease正式快照](../../modules/disease/data/curated/20260922_clinvar_snv_conditions_01/report.json)，通过[独立配置](../config/clinvar_snv.yaml)及`python src/build/build_clinvar_snv.py`投影五张[服务表](tables/clinvar_snv/manifest.json)：variant_rcv/rcv各1,812,773行，scv/variant_scv各2,073,487行，rcv_condition_member 1,970,800行。`python src/database/import_clinvar_snv.py`已原子导入`web_clinvar_snv` schema，当前Web变异来源行孤儿0；[导入报告](postgresql_clinvar_snv_import.json)。summary accession无版本，页面显示同周XML观察版本，RCV分类不拆给各条件成员。独立增量不改变上述47张基础表数量。

原生注释与预测/约束保留来源和method/role；缺失不补零。接触与OPM仅mapping_status=mapped可按目标坐标查询；未映射来源记录保留。
UniProt功能/定位从同版raw选择comment并机械解析，不消费探索runs、不改写注释；scope无法精确解析时保留unresolved。
四类膜标签和GO slim映射读取负责模块curated；统一外链及可恢复冗余属性通过PostgreSQL普通视图查询。

| 分类 | 表 | 行数 | 一行含义 | 状态 |
|---|---|---:|---|---|
| identity | [protein](tables/identity/protein.parquet) | 7,715 | 一个UniProt膜蛋白条目 | ready |
| identity | [protein_sequence](tables/identity/protein_sequence.parquet) | 16,655 | 一条可获取序列 | ready |
| identity | [protein_isoform](tables/identity/protein_isoform.parquet) | 13,091 | 一条来源isoform声明 | ready |
| identity | [protein_gene](tables/identity/protein_gene.parquet) | 7,724 | 已确认蛋白—HGNC关联 | ready |
| identity | [protein_external_reference](tables/identity/protein_external_reference.parquet) | 68,085 | 一条Ensembl/RefSeq来源交叉引用；UniProt/HGNC由统一外链视图组合 | ready |
| identity | [protein_function_annotation](tables/identity/protein_function_annotation.parquet) | 24,518 | 一条选定类型的原生UniProt功能comment | ready |
| identity | [protein_function_overview](tables/identity/protein_function_overview.parquet) | 7,715 | 每蛋白的默认FUNCTION引用 | ready |
| localization | [protein_uniprot_location](tables/localization/protein_uniprot_location.parquet) | 8,793 | 一条定位comment；原生位置、膜拓扑/朝向及配对证据嵌套保存 | ready |
| function_pathway | [protein_go_annotation](tables/function_pathway/protein_go_annotation.parquet) | 597,391 | 一条GO陈述—蛋白关联，保留证据和原对象 | ready |
| function_pathway | [go_term](tables/function_pathway/go_term.parquet) | 12,366 | 项目注释及全部generic slim类别术语；MF/BP/CC共用 | ready |
| function_pathway | [go_slim_mapping](tables/function_pathway/go_slim_mapping.parquet) | 10,335 | 同aspect的GO term到generic slim类别；is_a/part_of可达关系 | ready |
| function_pathway | [pathway](tables/function_pathway/pathway.parquet) | 2,883 | 一个来源通路及全部来源说明 | ready |
| function_pathway | [pathway_relation](tables/function_pathway/pathway_relation.parquet) | 2,899 | 一条通路父子关系 | ready |
| function_pathway | [pathway_topic](tables/function_pathway/pathway_topic.parquet) | 2,887 | 一条通路—官方主题关系 | ready |
| function_pathway | [protein_pathway](tables/function_pathway/protein_pathway.parquet) | 60,040 | 一条来源通路关联—蛋白关系 | ready |
| function_pathway | [rhea_reaction](tables/function_pathway/rhea_reaction.parquet) | 15,736 | 一个原生反应方向实体，参与物有序嵌套 | ready |
| function_pathway | [protein_rhea_reaction](tables/function_pathway/protein_rhea_reaction.parquet) | 13,145 | 一条来源反应关联—蛋白关系 | ready |
| function_pathway | [gtopdb_target](tables/function_pathway/gtopdb_target.parquet) | 2,184 | 一个药理学靶点，保留亚基及家族 | ready |
| function_pathway | [gtopdb_ligand](tables/function_pathway/gtopdb_ligand.parquet) | 8,047 | 一个配体及化学结构、全部肽来源记录 | ready |
| function_pathway | [gtopdb_record](tables/function_pathway/gtopdb_record.parquet) | 18,343 | 一条原生药理作用/配对/详情；保留逐记录蛋白上下文 | ready |
| function_pathway | [protein_gtopdb_target](tables/function_pathway/protein_gtopdb_target.parquet) | 2,272 | 蛋白—靶点—关系类型，官方映射和复合体背景分开 | ready |
| localization | [hpa_subcellular_location](tables/localization/hpa_subcellular_location.parquet) | 4,442 | 源基因定位汇总及已确认蛋白关联 | ready |
| membrane | [membrane_topology_source](tables/membrane/membrane_topology_source.parquet) | 40,149 | 来源序列/结构链及蛋白身份关联；不等于坐标映射 | ready |
| membrane | [membrane_topology_feature](tables/membrane/membrane_topology_feature.parquet) | 2,436,623 | 原生区段/方法预测/约束，含未定位记录 | ready |
| membrane | [membrane_topology_location](tables/membrane/membrane_topology_location.parquet) | 2,115,852 | 已发布exact映射后的明确序列区段 | ready |
| membrane | [membrane_topology_domain](tables/membrane/membrane_topology_domain.parquet) | 14,610 | 来源TOPDOM约束及模型侧别；不是新domain扫描 | ready |
| membrane | [membrane_contact_identity](tables/membrane/membrane_contact_identity.parquet) | 19,934 | 接触来源对象—蛋白身份关联 | source_coordinates_only |
| membrane | [membrane_biodolphin_interaction](tables/membrane/membrane_biodolphin_interaction.parquet) | 16,292 | 蛋白链—配体实例及来源编号位点 | mapping_processed |
| membrane | [membrane_mplid_residue](tables/membrane/membrane_mplid_residue.parquet) | 1,312,545 | 来源PDB链残基观察及已验证位置/失败状态 | mapping_processed |
| membrane | [membrane_biodolphin_site](tables/membrane/membrane_biodolphin_site.parquet) | 96,206 | 一个来源位点词项及验证后的序列位置/失败状态 | mapping_processed |
| membrane | [membrane_opm_observation](tables/membrane/membrane_opm_observation.parquet) | 2,975,891 | 一个来源OPM结构残基观察及新核对的位置/失败状态 | mapping_processed |
| membrane | [deeptmhmm2_prediction](tables/membrane/deeptmhmm2_prediction.parquet) | 16,655 | 一条与当前输入序列完全一致的DeepTMHMM2预测 | ready |
| membrane | [deeptmhmm2_segment](tables/membrane/deeptmhmm2_segment.parquet) | 114,283 | 一条DeepTMHMM2预测区段；1-based闭区间 | ready |
| membrane | [protein_membrane_label](tables/membrane/protein_membrane_label.parquet) | 7,753 | canonical蛋白四类膜标签及明确UniProt支持；具体标签可重叠 | ready |
| membrane | [protein_membrane_classification](tables/membrane/protein_membrane_classification.parquet) | 7,715 | 每个canonical蛋白一个互斥膜主类、父类及跨膜子类；原重叠证据另见protein_membrane_label | ready |
| sequence | [uniprot_sequence_feature](tables/sequence/uniprot_sequence_feature.parquet) | 248,288 | 共用UniProt feature：canonical全部类型及既有膜记录；Sequence视图仅取canonical | ready |
| sequence | [sequence_dataset](tables/sequence/sequence_dataset.parquet) | 9 | 来源与方法最小字典；不计算来源覆盖统计 | ready |
| sequence | [ptm_record](tables/sequence/ptm_record.parquet) | 642,233 | 一条canonical已映射或未定位PTM来源记录；UniProt详情通过feature引用 | ready |
| sequence | [sequence_site](tables/sequence/sequence_site.parquet) | 219,771 | canonical序列上的唯一PTM残基位置 | ready |
| sequence | [ptm_record_site](tables/sequence/ptm_record_site.parquet) | 500,825 | 来源记录—明确canonical位点连接；端点角色独立保留 | ready |
| sequence | [ptm_evidence_dataset](tables/sequence/ptm_evidence_dataset.parquet) | 37 | ProteomeScout原始证据数据集说明；记录保留各次关联 | ready |
| sequence | [ptm_evidence](tables/sequence/ptm_evidence.parquet) | 1,863,818 | 非UniProt PTM逐条证据；UniProt通过共用feature查询 | ready |
| sequence | [conservation_sequence](tables/sequence/conservation_sequence.parquet) | 7,715 | canonical序列计算背景和同源支持状态 | ready |
| sequence | [residue_conservation](tables/sequence/residue_conservation.parquet) | 4,364,831 | 一个canonical残基的JSD和逐位点质量事实 | ready |
| sequence | [pfam_entry](tables/sequence/pfam_entry.parquet) | 3,661 | 一个Pfam条目的名称、类型及Clan | ready |
| sequence | [pfam_hit](tables/sequence/pfam_hit.parquet) | 23,651 | 一条canonical Pfam命中，保留alignment/envelope/HMM坐标 | ready |
| sequence | [pfam_sequence](tables/sequence/pfam_sequence.parquet) | 7,715 | 每条canonical的Pfam处理状态，包括已扫描零命中 | ready |

## 本轮未构建

- **reactome_counts**：用户要求暂不计算。
- **membrane_counts**：暂不计算跨膜区段聚合；保留来源区段。
- **protein_data_overview**：统计指标尚未设计。
- **unresolved_structure_residues**：映射处理已完成；缺少唯一对应、链编号冲突及来源残基不符的行保留明确状态，不强配。

以上为未接入/未计算，不代表来源无数据。GO CC复用GO表；序列、结构及位点页面复用膜表，不重复保存。

## 验证范围

已核对所有表主键、蛋白范围、关键外键、序列长度、默认FUNCTION归属、已映射拓扑坐标边界和功能来源记录数守恒，并查询P00533关联链。
本脚本仅验证Parquet；PostgreSQL导入/查询状态以相同built_at的报告为准。未进行API、页面或并发负载验证。所有文件先在临时目录构建并验证，通过后替换当前目录；正常异常恢复旧目录，不保留历史数据版本。
