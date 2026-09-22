# Expression：来源、展示分组与待决事项

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

> 2026-09-21：本板块已按后续授权构建、导入并验证；下文是此前研究快照，现状见[本版记录](../../../../record/00_initial_preview/20260921_context_v1.md)。

2026-09-20。展示与精简方案已纳入[plan](../../plan/expression.md)。本文件保留来源状态与待核实依据；未执行表达汇总、字段删除或服务表构建。

## 目标与当前基础

回答当前蛋白对应基因在哪里表达、RNA与蛋白各有什么证据，以及正常组织、癌症和细胞系背景有何不同。基因表达可作为蛋白页面的context，不自动代表canonical或特定isoform的蛋白丰度。

依据[上游结果](../../../../../../modules/expression/docs/result.md)2026-09-14完整发布记录：

| 来源 | 当前正式产物 | 对网站的含义 |
| --- | --- | --- |
| HPA | 17张筛选表，84,669,985条目标来源记录 | 包括定位、预后等，并非全部都是表达测量；来源列已保留，尚需网站字段投影 |
| GTEx v11 | gene TPM与gene median TPM各7,601条基因索引；66,510条转录本索引；19,616条gene TPM样本注释 | 索引不是表达值，需绑定对应原始矩阵提取；覆盖基因不等于检出表达 |
| Tabula Sapiens | 7,653条目标基因索引 | 需读取配套矩阵并确认统计口径，尚无本项目细胞类型表达汇总 |

来源细节以[HPA审查](../../../../../../modules/expression/docs/hpa_download_review.md)、[GTEx核对](../../../../../../modules/expression/docs/gtex_collection.md)、[Tabula Sapiens审查](../../../../../../modules/expression/docs/tabula_sapiens_review.md)和[上游规则](../../../../../../modules/expression/docs/rules.md)为准。这里不把旧计划中的“未mapping”覆盖完整发布结果。

## 当前决定与来源依据

用户确认按数据集来源→数据类型→组织/细胞类型展示，可折叠与截选，Cancer独立成板块。此前按组织/细胞类型优先划分三个模块的建议未采纳，不指定GTEx或HPA覆盖其他来源。展示、字段精简与串联规则统一维护于[Expression方案](../../plan/expression.md)。

HPA官方将IHC记录定义为基因、组织、细胞类型、表达等级和可靠性；RNA与质谱有独立定义，见[官方数据说明](https://www.proteinatlas.org/humanproteome/tissue/data)。本地来源版本以已收集文件记录为准。

## 需核实与处理

1. GTEx当前样本矩阵与官方median文件的队列描述存在日期/LCM分组差异；展示官方median时保留其来源口径，但在声称样本明细可重现中位数之前需核对。不得用不同队列样本数装饰median。
2. HPA pTPM仍是RNA指标；FANTOM为CAGE相关计量，不是RNA-seq TPM；蛋白MS保留自己的强度定义和样本/重复关系，暂不另算跨来源平均。
3. Tabula Sapiens含不同技术、供者与处理矩阵，来源版本、矩阵含义及汇总加权方式需在上游确认。不将所有细胞简单视为独立供者，不将HPA与Tabula重叠研究视为独立验证。
4. HPA组织/细胞类型字典与MS汇总等补充文件在既有审查中有缺口；实施统一筛选前核实当前收集状态，不能臆造映射。
5. 转录本表达保留作为后续展开内容；转录本到具体蛋白isoform的关系需另行确认，不套用canonical默认值。
6. HPA亚细胞定位已进入蛋白概述，本区引用即可；已排除的HPA旧GTEx/consensus不重新引入。历史PaxDB不是当前已确认来源。

下一步按已确认方案核对具体字段与样本/背景关联，确定服务表契约；无需等待Tabula统计才能整理已有HPA测量表。
