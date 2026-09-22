# 已确认方案

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

本页保留原首版方案索引；此前“plan不归档”的目录安排已被用户2026-09-22追加要求替代，当前计划与适用契约通过上方索引查阅。阶段定位见[文档总索引](../../../README.md)，当前研究见[01阶段](../../../research/01_preview_optimization/README.md)；下文指向archive的链接是原研究依据，旧研究中的进度/授权不作为当前状态。

2026-09-22新增[下一阶段问题与优化目标](../../../research/01_preview_optimization/issues.md)：14个区域、55条反馈已描述、定位和分类，包含用户明确要求与待比较方案；本轮仅登记审查，尚未实施。后续采用的具体方案再更新本目录对应文档；以下旧版实现与验收不代表新目标已完成。

2026-09-21第二版已本地交付，包含追加序列精简、PTMD迁移和人体导航；04:30已完成变异类别/预测概览、GO/JSD交互及定位/通路精简，05:12完成共享坐标八轨Sequence Browser、范围交互与膜特征面板：现行展示修订见[网站第二版](website_v2.md)，逐项问题、调研与实际进度见[第二版问题记录](../research/website_v2/issues.md)。旧展示题尚未回答不再阻塞本次明确要求的修改。

2026-09-21已确认[网站构建策划](site_construction/README.md)：独立维护参考经验、后端/API/前端架构与采用理由。服务表已入库，并在自主构建授权下交付[网站初版](website_v1.md)，实际实现与定向验收见[交付记录](../../../record/00_initial_preview/20260921_website_v1.md)。[逐轮审查](../research/display_selection.md)的字段选择题保持原回答状态，当前推荐分层不等于用户逐项选择。

从[整体页面方案与实施依赖](overall.md)进入。本轮已确认修订、待决处理方案和33表精简审查集中于[Basic info第二轮优化](../research/basic_info_v2/README.md)；实际执行与数据库验收见[本版record](../../../record/00_initial_preview/20260921_basic_info_v2.md)。

本目录维护用户已确认的方案及明确授权自主落实的实施基线，二者在对应文档注明；研究依据、待决问题及统计留在docs/research，进度入口见[Web README](../../../../README.md)。方案直接更新，重要替代决定见[历史索引](../../../history/README.md)。

| 方案 | 已确认范围 | 状态 |
| --- | --- | --- |
| [全库总览与说明](database_overview_documentation.md) | 分类统计、来源版本、介绍与使用指南 | 已交付；见[验证记录](../../../record/00_initial_preview/20260921_database_overview.md) |
| [网站第二版](website_v2.md) | 用户具体反馈下的摘要面板、全序列交互、变异频率/预测选择及来源证据 | 本地构建与代表性交互验收通过；见[交付记录](../../../record/00_initial_preview/20260921_website_v2.md) |
| [网站初版](website_v1.md) | 自主授权下的默认/展开/隐藏字段、序列与结构、最小运行环境 | 本地实现与代表性浏览器验收完成；未公网部署 |
| [蛋白概览](protein_overview.md) | 概览结构与膜标签；身份/序列、完整功能注释、GO/Reactome/Rhea/GtoPdb展示、KEGG后续扩展、细胞定位、膜视图与下游复用及统计面板 | 展示规则已确认；当前本地实现见下方构建方案 |
| [本地保存与入库](service_data_storage.md) | Parquet服务表、目录职责、开发验证与正式入库时机 | 本地构建已执行，按追加授权执行本地PostgreSQL导入 |

本轮[本地表构建方案](local_table_build.md)落实cleaned身份、46张当前表和10个普通视图和未接入项；实际清单见[data/README](../../../../data/README.md)。

功能与通路的具体表契约见[13张服务表与字段方案](function_pathway_tables.md)，包含Rhea/GtoPdb点击详情保留范围。

第二部分已确认[序列优先](sequence.md)，五组轨道、仅canonical及PTM五来源保留规则已确认，[字段精简与整合](sequence_fields.md)已确认，已导入[Sequence版本](../../../record/00_initial_preview/20260921_sequence_v1.md)，突变后续接入；主显示边界及页面统计后续落实。

[突变板块](variant.md)已确认MANE Select优先、variant_id关联、来源与预测分类展开及AlphaGenome展示；[五张核心服务表及辅助表](variant_tables.md)已构建并导入，见[Variant验收](../../../record/00_initial_preview/20260921_variant_v1.md)。

[蛋白context](context.md)已确认PPI筛选式分库表格、QTL组织概览/条目/基因坐标视图，暂不进行QTL突变mapping；[Expression](expression.md)已确认来源→数据类型→组织/细胞类型的展示层级、折叠截选与独立Cancer板块，并记录字段精简和关联方案。三部分服务表已构建并导入，见[Context验收](../../../record/00_initial_preview/20260921_context_v1.md)。

[本地PostgreSQL方案](postgresql.md)维护连接、导入、类型与事务替换；mapping上游结果见[膜模块](../../../../../modules/membrane/docs/site_mapping_result.md)。

2026-09-20讨论收口：补入[身份七表字段](identity_function_tables.md)、[PPI/QTL字段与3+5表](context_tables.md)、[疾病展示与关联](disease.md)、[数据总览](data_overview.md)。来源统计留research；字段和展示方案在plan维护。此次只归整文档，尚未完成的科学选择见[实施依赖](overall.md#讨论已收口仍需落实的事项)。

疾病服务表已于2026-09-21构建并导入web_disease：[20表/12视图契约](disease_tables.md)、[版本验收](../../../record/00_initial_preview/20260921_disease_v1.md)。

- [Variant证据面板精修](variant_evidence_refinement.md)：Genomic/AA列精简排序、ClinVar星级及ID分组、频率色阶、预测总览筛选、ΔΔG方向、Transcript分层；已完成真实数据与窄屏验收。
