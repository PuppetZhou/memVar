# 20260921_basic_info_v2

日期：2026-09-21。用户授权按当前方案检查冗余、精简服务数据并更新已有PostgreSQL。数据版本是本次工程/整理交付标识，不替代各来源自身版本，也不建立Web releases或历史数据副本。

当前状态：**已完成并通过验证**。本地`memvar_web.web`已切换为`20260921_basic_info_v2`，共35张业务表、5个普通视图及1张构建清单元数据表。对应Parquet构建时间（UTC）：`2026-09-20T16:13:53.485470+00:00`。

## 本版范围

- 身份、功能、GO/Reactome/Rhea/GtoPdb、定位、膜信息共35张业务表；新增GO slim分类桥和四类膜标签。
- 基础身份范围仍为7,715个蛋白和16,655条序列；原GO、反应、配体、结构位点等来源事实保留。
- 本次去重只改变Web存储和查询，不删除上游科研事实，不合并不同证据或不同映射层次。

## 已落实的冗余优化

| 物理表 | 删除的冗余 | 替代查询或维护位置 |
| --- | --- | --- |
| protein_function_overview | default_sequence_id、selection_rule | sequence从protein关联；规则在构建元数据；protein_function_overview_detail普通视图可恢复 |
| protein_rhea_reaction | master_id、direction | 从rhea_reaction关联；protein_rhea_reaction_detail普通视图可恢复 |
| membrane_biodolphin_interaction | source_sites及三列派生汇总 | 96,206条位点只存membrane_biodolphin_site；普通summary视图计算数量/状态，保留缺失NULL |
| protein_external_reference | 7,715条UniProt身份副本和7,724条HGNC关系副本 | UniProt取protein、HGNC取protein_gene；protein_external_reference_all普通视图组合，外链仍完整 |
| protein_external_reference | 主编号在角色列中的重复值、可派生角色URL | 主编号存external_id；来源配对编号各存一次；类型化角色编号和URL通过视图恢复 |
| protein | 固定inclusion_basis长句 | 构建rules.metadata维护 |
| protein_uniprot_location | 固定comment_type | 构建rules.metadata维护 |

逐字段等价性已在改造前验证，见[迁移前审查](20260921_basic_info_v2_audit.json)。对不等价的label/description、不同物理几何、原/目标坐标、逐证据、条件、映射状态等保留原字段，不为缩表删掉科学信息。

## 外链与编号修复

xref物理表从83,524行减为68,085行，只保存Ensembl/RefSeq来源记录；普通视图恢复完整83,524条外链。允许缺失编号，未知类型保留原ID但不猜URL。

RefSeq的来源属性NucleotideSequenceId不能一概称为转录本。28,472组蛋白—核酸配对中28,459组为RNA编号，13组是NC_核酸分子编号；后者transcript_id_full/transcript_url留NULL，nucleotide_id_full/nucleotide_url仍可用。物理表只存nucleotide_id_full一次；Ensembl的主ENST由external_id表达，ENSG/ENSP作为来源配对编号保留。

首次导入在发布前的视图校验中发现NC_边界，自动清理临时schema，旧库未切换。修复角色语义并增加回归用例后，小范围真实SQL验证完整外链和核酸类型通过，再重建并重试导入。未靠放宽缺失检查伪造转录本编号。

## 本版派生规则

- GO slim：Function正式发布10,335条term—category映射，140类，使用同aspect的is_a+part_of可达关系；Web GO字典补齐32个类别术语至12,366行。正向分类视图保留subject/条件/证据，排除NOT、ND、obsolete、根术语与仅父对象背景；见[上游规则](../../../../modules/Function/docs/go_slim.md)。
- 四类膜标签：membrane正式发布7,753行标签，覆盖7,715个默认canonical背景，允许重叠；见[上游规则](../../../../modules/membrane/docs/basic_membrane_labels.md)。默认膜区段用UniProt Feature。
- 疾病xref不进入Basic info；功能具名对象无法对应isoform则不补填canonical；定位不生成最终定位，不另起版本研究。

## 统一查询入口

普通视图不存储新的数据副本：

| 视图 | 用途 |
| --- | --- |
| protein_external_reference_all | 组合全部四库外链及正确对象编号 |
| protein_function_overview_detail | 默认FUNCTION引用、默认序列和选择规则 |
| protein_rhea_reaction_detail | 蛋白反应关联加反应属性 |
| membrane_biodolphin_interaction_summary | 接触实例加按interaction_id计算的位点数量/映射状态 |
| protein_go_slim | 正向GO分类记录，保留原注释对象及证据引用 |

例如：

```sql
SELECT database_name, external_id, url, gene_id_full, protein_id_full,
       transcript_id_full, nucleotide_id_full
FROM web.protein_external_reference_all
WHERE accession = 'P00533';

SELECT * FROM web.membrane_biodolphin_site
WHERE interaction_id = 'BioDolphin:9';

SELECT manifest->>'data_version' AS data_version, built_at
FROM web._build_manifest;
```

## 构建与更新

入口依次为根目录的`python run.py Function build-go-slim --publish`、`python run.py membrane build-basic-labels --publish`，以及Web的build_tables、import_tables、validate_import。科研派生使用独立run验证后发布；Web直接更新当前表。

PostgreSQL先导入临时schema、核对行数/外键及外链视图，再在事务中替换web；失败只清理临时schema。`_build_manifest`、Parquet manifest、导入报告与查询验证共同记录data_version及built_at。

## 验证与限制

已通过：

- 35张业务表行数、主键与标量外键；版本与built_at在Parquet、数据库、导入报告和验证报告一致。
- 原33表除外链物理去重和GO字典增补外，所有表行数保持不变；其他新数据来自已发布的两个上游派生。
- 外链物理表68,085行，统一视图83,524行且reference_id无重复；UniProt/HGNC不在xref物理表重复存储。Ensembl、常规RefSeq和NC_边界代表记录的编号/URL与正式构建函数一致。
- BioDolphin的96,206条独立位点保留，16,292条interaction的汇总视图与按位点表重算结果逐行一致；9,871条无来源位点记录的汇总计数继续为NULL。
- 膜标签7,753行、22,821个支持记录全部能回连保留的UniProt feature/comment；标签sequence_id与canonical一致。
- GO slim的10,335条关系同aspect，正向查询不混入仅父对象背景记录。
- JSONB详情往返、映射状态计数、真实零/不适用区别与两页游标查询通过；两页各50条且无重复。
- 五项外链针对性测试通过，其中包括NC_核酸配对不能伪作转录本。

本地查询耗时（单次EXPLAIN ANALYZE，非并发基准）：统一外链0.222 ms、BioDolphin汇总0.104 ms、GO slim分类0.61 ms、膜标签0.07 ms。其余位点/分页查询见[查询报告](../../../data/postgresql_validation.json)。

导入耗时167.22秒；当前数据库大小3,531,904,691 bytes，上一轮导入报告为3,530,553,011 bytes，净变化+1,351,680 bytes。本轮同时新增GO slim、膜标签及索引，整体大小约3.53 GB，不能将去重解释为数据库总体明显缩小。优化目标是减少重复生物学关系和冗余维护，同时保持完整查询。

[导入报告](../../../data/postgresql_import.json)、[查询验证](../../../data/postgresql_validation.json)、[服务表字段清单](../../../data/tables/manifest.json)记录当前运行细节。没有新增API或页面，不把单客户端SQL验证当作网站并发验收；Reactome计数、KEGG、总览统计仍暂缓。

