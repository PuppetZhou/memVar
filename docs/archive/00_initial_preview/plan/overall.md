# 蛋白页面整体组织与方案入口

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-20。根据逐板块已确认讨论归整；后续已授权并完成Basic info及canonical Sequence导入，当前版本见[记录](../../../record/00_initial_preview/20260921_sequence_v1.md)。

## Top-down页面顺序

| 顺序 | 板块 | 当前方案 |
| --- | --- | --- |
| 1 | 蛋白概览：身份/功能、通路、定位、膜信息及数据总览 | [概览](protein_overview.md)、[七张身份与功能表](identity_function_tables.md)、[功能通路表](function_pathway_tables.md)、[总览面板](data_overview.md) |
| 2 | 序列与位点注释：PTM、Domains、Membrane、Function site、JSD（本轮仅canonical） | [轨道](sequence.md)、[字段保留与整合](sequence_fields.md) |
| 3 | 变异与效应：MANE优先列表、来源/频率/预测详情 | [展示](variant.md)、[五张核心表](variant_tables.md) |
| 4 | 蛋白context：PPI、QTL、Expression | [context](context.md)、[PPI/QTL字段与3+5表](context_tables.md)、[Expression](expression.md) |
| 5 | 疾病与表型：基因疾病证据、表型、剂量及后续具体变异条件 | [疾病](disease.md) |

结构是序列/位点和膜注释的联动展示入口；具体结构浏览器布局、其他结构轨道及实验效应扩展尚未完整设计，不将当前讨论当作其完整实施方案。

## 共用实体与关联边界

蛋白页面使用accession与已确认基因身份，序列注释使用明确sequence_id，DNA变异使用variant_id及参考转录本后果，疾病保留来源ID和有语义的映射。canonical是页面默认；MANE是变异后果优先，二者不自动等同。

序列/结构/膜视图复用一份注释和位置关系，点击位点查询已映射变异。基因疾病、表达与QTL背景直接经基因导航，不强制经site，不推断isoform特异性。数据库保留、API返回和默认显示分别控制，展示精简不删科学信息。

## 讨论已收口、仍需落实的事项

| 事项 | 后续处理 |
| --- | --- |
| GO slim与Reactome计数 | goslim_generic的140类来源已补齐；映射方案见[本版规则](../research/basic_info_v2/rules.md)，已构建并接入；Reactome计数继续暂缓 |
| 膜标签与默认TOPO | 本轮改四类标签；默认canonical膜区段采用UniProt Feature，缺失不跨来源补齐；判定细则已正式落实；膜区段等聚合计数仍暂缓 |
| PTM/Pfam与序列定位 | 仅canonical，PTM复用现有映射并筛选字段；PTMD2未定位详情保留，Pfam已入库且主显示边界待落实；突变移至下一板块，来源最后统一统计 |
| 变异频率、密度及模型目录 | 五表精简方案已于09-21确认，VEP/dbNSFP/AlphaGenome统一组织并按variant/后果粒度关联；保留原值与来源注释。原生频率已于09-21发布；模型目录和密度口径仍待落实 |
| Expression统计 | 来源分开展示已确认；GTEx队列一致性和Tabula矩阵/统计规则仍需核实 |
| 疾病与总览 | 疾病展示已确认；ClinVar条件关联、疾病分类及未定义计数不能因文档收口宣称完成 |

待核实科学选择仅阻塞依赖它的产物，不重复确认已确定展示规则。已被明确暂缓的项目仍暂缓，本次归档不解除其边界。来源统计与比较留research，正式规则唯一维护在plan；实际46张服务表及本地数据库交付状态以[数据清单](../../../../data/README.md)为准。保存与入库见[服务数据](service_data_storage.md)、[PostgreSQL](postgresql.md)。
