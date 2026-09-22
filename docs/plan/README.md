# 按阶段查看方案

更新：2026-09-22。**当前为[01 公网预览后优化](01_preview_optimization/README.md)**。旧方案已按00阶段归档，本目录不再平铺首版、第二版和精修文件。

| 阶段 | 方案位置 | 如何使用 |
| --- | --- | --- |
| 01 公网预览后优化 | [当前计划与修订入口](01_preview_optimization/README.md) | 查看本轮目标、依赖、已明确要求与待讨论事项；专题方案确认后在本阶段维护 |
| 00 首版构建与公网预览 | [原方案索引](../archive/00_initial_preview/plan/README.md) | 31份旧方案保留原文与日期，作为已建网站和服务数据的基线；当时状态以00 record为证 |

## 当前方案的适用方式

归档是文档分阶段，不等于撤销全部已确认规则。未被替代的身份、关联、数据契约和工程方案继续适用，入口如下；用户本轮明确要求优先于冲突的旧展示要求。当前[55项方案](01_preview_optimization/01_solutions.md)、[已选UI工具](01_preview_optimization/03_ui_toolkit.md)及[数据决定](../research/01_preview_optimization/01_data_decisions.md)已形成；膜范围/方法已确定，全转录本补全已取消，代表ID与UniProt序列匹配目标已确认；其他科学选择按当前数据决定标记。待比较的选项不能直接写成已确认科学规则，也不能把当前网站已实现的旧行为当作01优化已完成。

| 领域 | 00基线位置 | 01阶段对应事项 |
| --- | --- | --- |
| 整体架构与运行 | [overall](../archive/00_initial_preview/plan/overall.md)、[构建策划](../archive/00_initial_preview/plan/site_construction/README.md)（含架构/经验/流程） | 沿用未受影响技术方案；不继承旧轮次的执行状态 |
| 服务数据与数据库 | [保存与入库](../archive/00_initial_preview/plan/service_data_storage.md)、[本地构建](../archive/00_initial_preview/plan/local_table_build.md)、[PostgreSQL](../archive/00_initial_preview/plan/postgresql.md) | 数据补全确定后修改受影响契约与导入路径，不因目录整理重导入 |
| 首页、总览与帮助 | [homepage](../archive/00_initial_preview/plan/homepage.md)、[data_overview](../archive/00_initial_preview/plan/data_overview.md)、[全库统计与说明](../archive/00_initial_preview/plan/database_overview_documentation.md)、[ui_help](../archive/00_initial_preview/plan/ui_help.md) | UI；MEM变动后的分类与统计同步 |
| 蛋白概况、定位与功能 | [protein_overview](../archive/00_initial_preview/plan/protein_overview.md)、[身份字段](../archive/00_initial_preview/plan/identity_function_tables.md)、[功能通路表](../archive/00_initial_preview/plan/function_pathway_tables.md) | MEM、LOC、GO、MF、PH、RE |
| 序列、PTM与结构 | [sequence](../archive/00_initial_preview/plan/sequence.md)、[sequence_fields](../archive/00_initial_preview/plan/sequence_fields.md)、[sequence_ptm](../archive/00_initial_preview/plan/sequence_ptm.md)、[精修方案](../archive/00_initial_preview/plan/sequence_structure_refinement.md) | SQ、AT、ST；新选择方式、色阶、膜viewer与结构选区 |
| 变异与预测 | [variant](../archive/00_initial_preview/plan/variant.md)、[variant_tables](../archive/00_initial_preview/plan/variant_tables.md)、[证据面板](../archive/00_initial_preview/plan/variant_evidence_refinement.md) | VA；注释继续以代表转录本为主；全转录本补全取消，代表ID展示及UniProt canonical/isoform序列匹配为待落实目标 |
| 表达、QTL与PPI | [context](../archive/00_initial_preview/plan/context.md)、[context_tables](../archive/00_initial_preview/plan/context_tables.md)、[expression](../archive/00_initial_preview/plan/expression.md) | EX、PP；测量筛选、矩阵和级联分类 |
| AlphaGenome | [expression_alphagenome](../archive/00_initial_preview/plan/expression_alphagenome.md) | 沿用当前独立板块方案；新预测/分辨率工作按具体任务确定 |
| 疾病 | [disease](../archive/00_initial_preview/plan/disease.md)、[disease_tables](../archive/00_initial_preview/plan/disease_tables.md) | DI；新增ClinVar条件专区需要数据关系方案 |
| 旧网站多轮展示 | [website_v1](../archive/00_initial_preview/plan/website_v1.md)、[website_v2](../archive/00_initial_preview/plan/website_v2.md) | 仅用于查首版和迭代背景；本轮反馈与后续采用方案决定新的展示要求 |

问题ID及原始反馈统一见[55条清单](../research/01_preview_optimization/issues.md)，这里不复制逐项描述。生效的科学规则由负责模块维护。

## 后续维护

01阶段专题方案在确有确认内容时按`01_主题.md`、`02_主题.md`编号建立，注明对应问题ID、采用决定、输入/输出、依赖、验收标准和替代的旧条款；编号仅用于定位，不表示科学优先级。无需复制31份旧文档，也不预建空方案。新专题生效后更新本索引的对应入口，明确哪些基线继续沿用。

当前授权由用户请求及已确认记录决定；旧计划中的“仅规划”“未授权”等历史文字不能推翻后续授权。实际执行与验证写入[record](../record/README.md)，问题状态回链记录。目录说明见[总索引](../README.md)。
