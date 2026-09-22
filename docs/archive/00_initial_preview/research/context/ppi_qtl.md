# 蛋白context：PPI与QTL首期设计讨论

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

> 2026-09-21：本板块已按后续授权构建、导入并验证；下文是此前研究快照，现状见[本版记录](../../../../record/00_initial_preview/20260921_context_v1.md)。

日期：2026-09-20。PPI数据库分开展示及互作方式/context筛选、QTL组织计数和坐标视图已确认，见[plan](../../plan/context.md)；本轮不执行来源过滤、去重或新映射；Expression后续单独讨论。数值引用已验证交付，不重新全量扫描。

## PPI：伙伴列表与原生关系证据

当前来源为BioGRID5.0.259和IntAct（本地统一release未知）。35份来源文件4,712,021行，其中2,083,370行至少一端/affected关联项目，包括full、context和mutation，不是独立PPI数。

| 来源组 | 项目相关行 | 项目蛋白数 |
| --- | ---: | ---: |
| BioGRID full | 648,212 | 6,829 |
| BioGRID context | 646,710 | 6,538 |
| IntAct full | 589,700 | 6,769 |
| IntAct context | 169,896 | 3,963 |
| IntAct mutation | 28,852 | 1,261 |

当前按BioGRID、IntAct分开展示，可按互作方式和context筛选。主表按原生条目保留，伙伴提供检索入口；显示伙伴名称、可用accession/原生ID、物种、关系/实验类型、数据库入口及文献入口。点击展开每条来源观察、检测方法、参与者角色、context、来源ID、引用及负结果等状态。同一伙伴多记录可折叠，但不合并成统一真假/置信度；伙伴身份歧义保持候选，不选一个accession。

伙伴可以不是膜蛋白，不能只显示项目内伙伴。当前endpoint_link主要用于定位项目端，伙伴的完整实体字典仍须依据原始端点标识整理。来源中的小分子等非蛋白参与者单独标明，不当作蛋白伙伴计数；是否另放其他分子关系列表后续确认。物理/遗传、直接/间接、阴性/阳性不混成“直接结合”。当前上游不限定物理互作，Web若只默认某一类需另行确认。

PPI小网络图可后续增加，首期表格足够。伙伴数应在对象解析后统计；不能将此前667,996个混合基因/来源标识对直接当成准确蛋白互作对。

IntAct mutation是互作相关突变背景，适合在伙伴详情或后续突变证据中查看；当前仅完成affected身份关联，未完成坐标/序列验证，不直接连到项目variant_id或site。PeSTo/SPPIDER-seq已于2026-09-21验证并发布[序列位点预测科学数据集](../../../../../../modules/PPI/docs/interface_predictions.md)，可作为PostgreSQL服务数据补充，当前尚未入库。结构分片、伙伴和预测头独立保留，可供sequence/structure联动；属于界面预测而非新实验PPI证据，不能作为支持伙伴存在的额外实验票数。

服务层采用3张逻辑表，现行字段契约见[plan](../../plan/context_tables.md)：ppi_record（来源关系/上下文/证据详情）、ppi_participant（端点原生身份/角色/物种及全部映射候选）、ppi_dataset（来源/版本/context集合）。伙伴列表由查询聚合，后续性能有需要再派生索引，不先建立所谓唯一实验表。与普通protein实体引用兼容，但不强迫非项目伙伴成为项目收录蛋白。

可精简首屏及服务冗余：原始整行文本、重复名称/原文件路径、解析调试字段；保留context membership、证据关系、来源ID、物种、阴性标记及身份状态。full/context中的重复包装不计独立实验，也不直接删除。

## QTL：分子表型的调控关联背景

共保留251,750,112条项目记录，包含不同粒度，不是独立变异数或全部显著关联数。

| 来源 | 当前保留记录 |
| --- | ---: |
| GTEx v11 eQTL pairs / summary | 23,608,070 / 309,465 |
| GTEx v11 sQTL pairs / summary | 34,306,280 / 218,668 |
| GTEx v11 apaQTL pairs / summary | 4,835,546 / 166,360 |
| eQTLGen full cis（2019-12批次） | 36,395,279 |
| QTLbase v2，21类有目标记录 | 151,910,444 |

QTLbase另有1,681条研究元数据。GTEx pairs是来源显著配对；eQTLGen保留目标基因全部full cis检验，含非显著项；QTLbase不能因有P值就统称显著。

推荐按QTL类型、来源、组织/研究筛选，下方分页表：变异原生标识或坐标、目标基因/表型、组织、QTL类型、P值、效应（来源有时）、来源/研究。点击展开效应等位基因、SE/Zscore、FDR/q值（各自原义）、样本量/人群及PMID。不存在的字段留空；不要把Zscore统一改称beta，或把QTLbase位置记录伪造为REF/ALT变异。

以hgnc_id通过foundation连接当前蛋白，这是基因背景，不是该isoform的独立调控实验证据。sQTL/apaQTL需要保留事件/表型ID与group，不仅存gene。QTLbase对某些分子表型提供Mapped_gene，不能统一声称它是实验验证靶基因。

QTL不限制在当前10,866,094个编码SNV内，很多关联变异可以在非编码区。用户已明确本阶段不进行突变mapping，不构建项目variant_id交叉链接；GTEx b38 REF/ALT仍需规范化核对，eQTLGen为GRCh37且AssessedAllele不是保证的ALT，QTLbase缺REF/ALT只能提供位置候选。没有精确variant_id不影响按基因查看QTL。

首期服务结构采用5类逻辑表：gtex_qtl_pair（加qtl_type合并三类pairs，保留异构字段）、gtex_qtl_summary（保持原summary粒度）、eqtlgen_cis、qtlbase_association（21类用qtl_type组织，可分区）、qtl_dataset（来源研究与元数据）。统一API，不强行合并为2.52亿行全字段宽表。统一类型或拼接字段前验证原始精度、缺失表示及表型意义。

GTEx summary不混进pairs计数，dataset共用但保留Sourceid命名空间；原始组织名保留，不先跨来源合并组织或平均效应。服务端按gene+类型+组织/来源分页；需要具体阈值时应由用户明确选择/确认默认，不擅自加统一P/FDR阈值。

## 当前展示决定与字段清单

PPI采用分数据库条目表与互作方式/context筛选；QTL先看数据库×类型×组织记录数量，点击进入条目和同组装基因坐标视图，暂不做突变mapping。字段精简及坐标条件见[清单](field_retention.md)。PPI关联身份/实验类型，QTL关联基因/表型/变异对象；它们可以简单展示，但保持这两套关系边界。以上3+5表及字段方案已于2026-09-20纳入plan，尚未构建，不包含共享foundation实体及预测界面表。

证据：[PPI结果](../../../../../../modules/PPI/docs/result.md)、[PPI表契约](../../../../../../modules/PPI/docs/tables.md)、[QTL正式交付](../../../../../../modules/expression/docs/result.md)、[QTL映射规则](../../../../../../modules/expression/docs/qtl_mapping_plan.md)。来源文档中的历史启动/未执行文字不覆盖后续完成报告。
