# Expression / QTL / PPI / Disease 独立展示审查

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

核对日期：2026-09-21。范围为第二版的“摘要 → 选择来源/类别 → 分页记录 → 原证据”，只复用正式 PostgreSQL 数据，不修改科学筛选、关联规则或数值。本文补充[总体研究](analysis.md)和[问题清单](issues.md)；接口实现及局部验证以[API 记录](../website_v2_api.md)为准。

## 参考证据与取舍

| 证据 | 实际实现或官方说明 | 采纳 | 本轮未采纳 |
| --- | --- | --- | --- |
| 旧站 [expression-overview.tsx](/home/xuyzh/memVar/website/frontend/components/expression/expression-overview.tsx) 与 [model.ts](/home/xuyzh/memVar/website/frontend/components/expression/model.ts) | tissue × modality 矩阵；点选后列原记录；明确区分无记录、测量缺失、真实零和分类染色；各数值 modality 有独立显示量尺 | 原值/单位与来源详情、缺失不等于零、先选择再查看记录 | 旧组织名称 crosswalk、PaxDB 模块及每蛋白第 95 百分位显示截顶不自动继承。当前数据集合与旧站不同，本轮不新增跨来源组织映射或数值变换 |
| 旧站 [interaction-summary.tsx](/home/xuyzh/memVar/website/frontend/components/interaction-summary.tsx) | 先选 BioGRID/IntAct；按 curation context/category 点柱条进入筛选；分别报告 evidence records 与 distinct native interaction IDs | 来源及原类别保留、详情保留负证据及来源 context；按用户最新要求，当前图表改为只读，筛选表默认可见 | 当前 API 仅提供存储 record_id 计数，没有 native ID 统计；不得把当前柱条称为唯一互作、唯一蛋白对或独立实验证明。旧 context 分组不凭名称推断生物组织活性 |
| [VarSome Clinical Cards 官方说明](https://docs.varsome.com/en/clinical-cards)，本轮重新打开 | 区分 gene 与 variant 卡片；来源卡片提供摘要和明细；无相关信息可灰显 | Disease 以 ClinGen/GenCC/HPO/OMIM 来源卡进入原关系，明细继续按来源分区，空来源显示真实 0 | 不移植 ACMG/AMP 分类、跨预测器 meta-score、样本级分析或参考站的数据范围；未登入其私人样本页面，不声称复现完整临床工作流 |

采用卡片交互是本轮用户授权范围内的工程展示选择；不把旧站或参考网站的科学处理自动写成已确认规则。

## 当前统计口径

主要维护位置：[evidence_summaries.py](../../../../../src/api/evidence_summaries.py)、[evidence_context.py](../../../../../src/api/evidence_context.py)、[evidence_disease.py](../../../../../src/api/evidence_disease.py)。前端为 [ContextPanels.tsx](../../../../../frontend/src/components/ContextPanels.tsx)。

| 模块 | 统计的一行是什么 | 分组及点击 | 必须保留的限制 |
| --- | --- | --- | --- |
| Expression | 当前纳入展示的数据集内的原测量记录；`contexts` 在各 dataset 内去重后汇总 | category / source / dataset；dataset 卡使用接口返回的精确 filter | 跨 dataset 的 context 总数是 dataset–context pairs，不是统一组织数或独立细胞数；记录数与有值数不同；只汇总记录数，不汇总不同单位表达值 |
| QTL | 已发布 `qtl_context_count` 中完整关联表的源记录数 | provider-qualified source / type / tissue | 不含 GTEx phenotype summary 重复计数；不等于独立 QTL、因果发现或重新设阈值后的显著结果；同名组织不能证明同一队列 |
| PPI | 先取得当前 accession 关联的 distinct record_id，再统计正式 full collections 的记录 | BioGRID / IntAct 指标与 interaction type 条形图只读；下方常驻表格使用来源和类别筛选器 | 不等于 unique partner pair、native interaction ID 或独立确认；负证据、非蛋白参与者和来源 feature 在记录/详情保留 |
| Disease | 原 `evidence_id` 来源记录，另计该来源内的原 `disease_id` | ClinGen / GenCC / HPO / OMIM | 不跨词表合并 disease ID；ClinGen activity summary 不是独立断言，HPO navigation 记录不是 HPO annotation 数量；不同来源分类不合并成项目结论 |
| PTMD2 | 当前蛋白直接关联或候选关联的原 PTM/disease record | Disease 板块独立卡片；原 Disease / source_type 筛选 | 不并入四类 gene–disease evidence 总数；Disease 原文不映为标准疾病；MutationSite/来源位置不投射 canonical；不把所有记录叫作实验验证 |

四种 summary 都来自当前查询范围的数据库或已发布计数表，不使用第一页长度。source/category/dataset 是同一集合的不同分组层，前端不将它们相加。Expression 先选 measurement，再按该 dataset 内的 context_key 进入原始记录；PPI 表格始终可见；QTL/Disease 选来源或上下文后进入列表。原始列表每页 10 条，cursor 同时绑定 accession 和过滤条件。

## 定向真实数据核对

以下是本轮 P00533 局部读取结果，用于验证含义，不是写入前端的常量，也不替代完整数据库发布验收。使用现有 API Python 函数和只读连接，没有启动新服务或扫描全库。

| 样本 | 实际响应 | 展示判断 |
| --- | --- | --- |
| Expression summary | 11,368 来源记录，11,362 主测量值可用；normal 337、cancer 8,415、cell_line 1,236、single_cell 1,380 | 四卡显示记录覆盖量。数值大小不是表达高低，context 总数不能标成 11,368 个组织 |
| HPA `cancer_data`，breast cancer | High=`"0"`；Medium=`"2"`、Low=`"1"`、Not detected=`"7"`；单位 IHC category counts | High 为分类计数，0 必须保留；其余分类在原证据中可查看，不转换为 TPM、不推断整个组织无表达 |
| CPTAC `cancer_cptac`，Colon AC | logFC=`"-0.416558"`；调整后 p 值=`"1.03E-15"` | 保留负数及原统计量，不借用旧站 `log10(1 + max(0, value))` 渲染表达强度 |
| HPA `rna_single_cell_type`，adipocytes | nCPM=`"343.9"` | 明确单细胞类别和 nCPM，不能标为 TPM |
| HPA `dvp_cell_type_group_data`，cardiomyocytes | Intensity=null；补充 Matched nCPM=`"13.7"` | 主测量缺失，补充 RNA 值存在；不能拿 nCPM 填补 intensity 或将 null 当成 0 |
| Disease summary | ClinGen 2 记录/1 ID，GenCC 9/4，HPO 2/2，OMIM 4/2；独立 dosage 1 条 | 来源内 disease ID 可重复出现于其他来源，卡片 ID 数不得简单相加为唯一疾病数 |
| ClinGen `MONDO:0005233` | `relationship_status=activity_summary_not_independent_assertion`，分类 null；详情另含 GenCC 记录 | 保留 activity 状态与缺失分类，详情按来源分区，不把三行解释为三个独立肯定结论 |
| HPO/OMIM `OMIM:616069` | 两来源共享这个原 ID；HPO navigation 与 OMIM inheritance 各自保留；表型例 HP:0003577、PCS、频率 1/1、PMID:24691054 | 可以在同一个原 ID 详情中并列来源；疾病关联表型不自动证明每个相关基因/变异都有该表型；原 reference/qualifier/aspect 保留 |

疾病详情按精确原 `disease_id` 取证据，并以所选蛋白关联基因限定关系记录；表型则是疾病层注释。MONDO 映射状态是额外元数据，不作为此处自动跨 ID 合并的授权。

## 本轮发现与已做的局部修正

1. 表达 source 卡可打开多个类别，原表格没有逐行类别提示。现已在 context 下方显示 Normal tissues / Cancer / Cell lines / Single cells，详情保留 dataset 名称。
2. `Fields` 默认略去 null，导致表达详情中的主测量缺失不明显。现显式显示 `Missing source measurement (not zero)`，真实数值 0 与字符串 `"0"` 保留；dataset 卡同时展示主测量有值数，避免将所有记录称为有效数值。
3. 选择 expression source 后，measurement 卡原来仍混列其他来源。现按所选 source/category 显示相应集合，点击仍使用后端原 filter；没有修改任何数据筛选定义。
4. Disease detail 已返回但未显示的 `is_obsolete`、`mondo_mapping_status`、`definition_source`、HPO `modifier/aspect/phenotype_status` 已加入详情；原 phenotype/mapping key 保留在来源区。新增一句对象说明，区分 gene–disease 关系与 disease-level phenotype。
5. 仅有 ClinGen gene dosage、没有 disease evidence 时，灰卡可能令剂量信息不可达。后端已把原 dosage 查询补到 summary，前端在来源卡之外提供独立入口；不把 dosage 行计作疾病关系。
6. summary 的 `available_values` 排除了字符串 `NaN`，旧 list clean 未排除。已交 API 任务统一 `clean('NaN') → null`；数值/字符串 0 保留。API 任务仅定向核对 P00533，无额外全表扫描。
7. 只有类别和 dataset 卡片仍缺用户要求的组织/细胞概览。现补独立 context 浏览区，默认选择可用 GTEx measurement，否则取当前类别内可用集合；类别/来源/measurement 卡仅切换集合，点击具体 context_key 才打开原始记录。context 名称保留来源原文，支持服务端关键词搜索与每页 12 项，不把癌症样本标签统一重命名成组织。P00533 定向核对：GTEx 有 68 contexts，`Brain` 搜索匹配 13 项，Brain_Amygdala 对应 1 条 TPM=4.63782；癌症 RNA 8,384 contexts 只传当前页。该改动不建立跨 dataset context 合并规则。

## 2026-09-21 最新展示调整

本节记录用户在浏览器验收后的新要求，替代上一版 PPI 必须先点图表才能看列表的交互。

**PPI。** BioGRID/IntAct 指标卡和类别横条仅显示数量，使用普通元素而非按钮，不再充当进入表格的入口。下方表格默认请求第一页，来源、interaction category 筛选器始终可见。修改来源清除旧类别及 cursor，仍保留负证据、非蛋白参与者和原来源角色/feature 详情。

**Expression。** 新增四类分布介绍面板，分别呈现 Normal tissues、Cancer、Cell lines、Single cells 的 source records 与 dataset contexts。短条长度仅编码记录数；不会把 TPM、nTPM、nCPM、IHC 分类计数、logFC 或 intensity 放在同一量尺。类别图下保留 measurement 选择、组织/细胞/样本 context 搜索和分页。该面板描述已显示数据的覆盖，不声称哪类组织表达最高。

**Regulatory associations。** 使用原生 SVG 绘制一张人体轮廓，提供脑、肺、心/动脉等导航点，右侧仍显示来源原始组织标签和真实 association record 数。`regionForTissue` 的名称匹配仅维护在前端 `ContextPanels.tsx`，其目的是缩小待浏览标签集合，不生成正式组织分类表、不改变请求的原 tissue filter、不合并科学记录。不识别的名称保留在 Other / unmapped，按钮数字是源 tissue label 个数；横条数字仍是源关联记录数。人体位置是示意，不能读成解剖测量、疾病活性或因果位置。参考 PTMD 官方图的证据由根任务维护于[总体研究](analysis.md)，本组件没有复制其图片或数据。

**PTMD2。** 从序列区域移至 Disease 的独立来源入口；迁移序列入口由根任务负责。新接口为 `/proteins/{accession}/diseases/ptmd/summary` 与 `/diseases/ptmd`，数据粒度见 [disease_ptmd.py](../../../../../src/api/disease_ptmd.py)。主 Disease summary 的 `ptmd` 计数与 gene–disease `totals` 分开。列表保留原 Disease、PTM 类型、State、MutationSite、CellType，详情保留 Enzyme、原研究文字、来源位置/序列、身份/映射/关联状态、验证标志及 PubMed 引用；空 URL 仅在明确 `namespace=PubMed` 时按原 PMID 生成来源链接。candidate protein association 在列表和详情单独标明；State 原代码不猜测含义。API 任务定向验证 P00533 为 463 个原记录、59 个原 Disease 标签，不能据此称为 463 项实验验证或 59 个标准化疾病。

此轮只调整 `ContextPanels.tsx`、`context-v2.css` 与本文；在现有 frontend 目录执行 `npx tsc -b` 通过，未构建或启动服务，最终交互/响应式状态仍由根任务统一浏览器验收。

## 未扩展范围与待验收

- 当前 Expression summary 仅列本轮已纳入展示的数据集，不代表磁盘/数据库全部表达矩阵已进入网站。GTEx 为官方 gene-level tissue median；未加入 individual-sample/transcript matrix。
- Expression 的“无该来源记录”与“来源整体不在当前展示集合”不能通过前端造 0 混淆。category 四卡及已定义 PPI/QTL/Disease 来源的 0 由后端返回；HTTP 错误显示错误态，不渲染成空数据。
- PPI 原 native interaction ID 仍在来源详情，summary 暂无其独立统计；当前不声称迁移了旧站全部 context 图。
- Disease 详情最多提供前 100 条来源关系并明确提示限制；HPO 表型另行分页。本轮不添加临床分级或跨来源证据打分。
- 所有改动仍需根任务在唯一现有服务完成浏览器联调，重点验收 source 卡 → 对应列表 → 详情、灰卡、缺值/0、筛选切换重置分页与窄屏可读性。本文不把静态核对或 Python 函数返回视作浏览器通过。


## 2026-09-21 基础信息：最新精简决定与 GO 完整统计

本节记录用户最新审查后的展示决定，替代曾计划加入完整细胞 SVG、默认展开 Reactome 路径卡阵列的方案。仅改变网站呈现，不修改数据库或科学关联规则。

| 官方依据 | 采纳 | 未采纳或已被替代 |
| --- | --- | --- |
| [UniProt Subcellular location](https://www.uniprot.org/help/subcellular_location)说明受控位置/拓扑、isoform 对象和交互细胞图 | 原标签、来源、对象、拓扑与证据分开保留 | 用户要求减少图文，已删除完整细胞 SVG 及其 compartment 名称映射；不继承 SwissBioPics 绘图或形成跨来源共识 |
| [GO subset guide](https://geneontology.org/docs/go-subset-guide/)将 slim 用于类别概览；[GO annotations](https://geneontology.org/docs/go-annotations/)区分对象、关系与证据 | 三个 aspect 独立可视区，点类别读取对应原注释 | 不称作功能重要性、富集或活性；不从当前页猜总量，不隐藏原对象或 NOT |
| [Reactome Diagram Widget](https://reactome.org/DiagramJs/)与 [Axon guidance](https://www.reactome.org/content/detail/R-HSA-422475)提供真实事件图及稳定 ID | 详情链接对应 ID 的官方 PathwayBrowser 图 | 不引入外部脚本、复制图片或编造节点边；默认大卡阵列改为短预览 |

**Function。** 主视图和详情完全去掉 `comment_type=FUNCTION` 长原文，包含旧 Entry Level Annotation 区；数据库/API 原条目保留。默认显示短家族描述、来源 EC 编号及非 FUNCTION 注释类别。催化、辅因子、调控、家族证据仍保留对象和来源详情；UniProt 按钮可查看原站，没有自动改写科学断言。

**Cellular location。** 紧凑 Source / Applies to 选择器，默认最多四个原标签 chip，余项通过 `+N locations` 查看。点原标签才显示 topology、orientation、isoform、对应 HPA reliability、原 notes 与引用。仅在同一 source + scope + 原文标签内去重界面标签，保留全部原 evidence records；HPA gene scope 不改称 canonical 蛋白证据。主视图不再显示细胞图、区域归类或多段解释。

**GO。** `/overview/go/summary` 提供完整 annotation / distinct term 计数，三个 aspect 默认各预览最多五个已发布 slim 类别；沿用 API 顺序，不另构功能排名。条形来自已发布正向映射，类别重叠不能相加为总量。`/overview/go?slim_id=...&aspect=...` 精确筛选原注释并返回完整 total，列表服务器分页。全部原注释仍含 NOT / ND，详情保留 subject、form、relation、extension、with/from、assigned_by 与证据。API 代理定向核对 P00533 为 1,149 annotations / 93 terms；F 732/23、P 102/43、C 315/27；`GO:0048856` 类别与原筛选 total 均为 1。这是样本核对，不是前端常量。

**Reactome。** 默认仅显示真实 pathway / association 总数、最多三个 topic chips、三个路径名预览和 View pathways。完整 topic 筛选、每页六条原关系、来源与 official diagram 均在详情。API 代理核对 P00533 为 82 associations / 78 distinct pathway IDs；Developmental Biology 有 8 associations，limit=2 时 total 仍为 8。不同 topic 可重叠，不相加为独立路径数。Rhea 面板继续独立保留。

**视觉与验证。** 分类颜色改为较饱和蓝、紫、青绿、橙、粉，说明文字加深，GO 条形取消淡化；说明/操作通常至少 12px，窄屏选择器与标签换行。维护位置为 [Overview.tsx](../../../../../frontend/src/components/Overview.tsx)、[OverviewLocations.tsx](../../../../../frontend/src/components/OverviewLocations.tsx)、[OverviewOntology.tsx](../../../../../frontend/src/components/OverviewOntology.tsx)、[overview-v2.css](../../../../../frontend/src/components/overview-v2.css)。既有 frontend 目录执行 `npx tsc -b` 通过；未构建、启动服务或创建浏览器。交互及窄屏由根任务在唯一现有浏览器验收。


<a id="expression-ppi-20260921"></a>
## Expression与IntAct mutation专项展示审查（2026-09-21）

用户问题：context只有前后翻页、Overview没有说清测量技术、IntAct mutation未突出效应且重复范围/身份、GTEx组织下划线直接进入界面。核对当前API、源字段和现行Expression方法契约后，确定均可在前端完成，不变更PostgreSQL/API或科学产物。

### 14个已显示Expression集合的测量含义

| 集合键 | 来源 | 实际测量类型 | 保留的量值/单位 |
| --- | --- | --- | --- |
| gtex_gene_median_tpm | GTEx | bulk RNA-seq组织中位数 | median TPM |
| rna_tissue_hpa | HPA | bulk RNA-seq | nTPM |
| rna_tissue_fantom | FANTOM，经HPA | CAGE | tags per million |
| normal_ihc_data | HPA | IHC正常组织抗体染色 | 定性Level |
| ms_tissue_sample_data | HPA | MS蛋白质谱 | source intensity |
| cancer_data | HPA | 癌症IHC | 染色类别计数，主显示High及原详情 |
| cancer_cptac | CPTAC，经HPA | MS癌症蛋白组 | 原logFC |
| rna_cancer_sample | HPA | bulk RNA-seq癌症样本 | pTPM |
| rna_celline | HPA | bulk RNA-seq细胞系 | nTPM |
| rna_cell_line_cancer | HPA | bulk RNA-seq癌症细胞系 | nTPM |
| rna_single_cell_type | HPA | 单细胞/单核RNA-seq类型汇总 | nCPM |
| rna_single_cell_cluster | HPA | 单细胞/单核RNA-seq cluster | nCPM |
| dvp_cell_type | HPA | DVP蛋白质谱 | source intensity |
| dvp_cell_type_group_data | HPA | DVP分组蛋白质谱 | intensity；Matched nCPM保留为辅助信息 |

依据：[HPA tissue methods](https://www.proteinatlas.org/humanproteome/tissue/method)明确HPA/GTEx RNA-seq、FANTOM CAGE及MS强度；[HPA下载说明](https://www.proteinatlas.org/about/download)核对各dataset的对象与粒度；[DVP methods](https://www.proteinatlas.org/humanproteome/single%2Bcell/dvp/method)确认质谱与配对RNA群体是不同测量。已逐项对照当前`EXPRESSION_SPECS`和P00533 summary中的14个集合，不因上游下载页面某简短标题而把FANTOM错标RNA-seq。

P00533当前显示覆盖：bulk RNA-seq 5集合/9728记录、single-cell RNA-seq 2/1329、CAGE 1/46、MS 4/122、IHC 2/143，总11368来源记录。该计数是数据覆盖，不表示表达高低，也不代表独立细胞数。

### IntAct效应为何曾不明显

当前API已将`Feature type`转换为可读`interaction_type`，没有丢失这些字段；主表弱化为紫色badge，详情默认铺大量身份/范围字段。第一批真实记录的type恰好为`mutation(MI:0118)`，确实未报告方向。用户关注的增强/减弱等在其他原记录中存在。

采用明确原词的显示映射：increasing/decreasing及其strength/rate子类、disrupting、causing、with no effect。通用mutation独立灰色显示，未知词不推断。原文仍紧随醒目的effect标题显示，strength与rate不合成同一种定量效应，也不跨不同伙伴聚合。背景资料：[IMEx原始研究](https://www.nature.com/articles/s41467-018-07709-6.pdf)和[IntAct curation manual](https://raw.githubusercontent.com/intact-portal/intact-portal-documentation/master/assets/intact-curation-manual.pdf)；本轮网页工具能检索其相关内容，直接打开manual的PDF受content-type限制，因此不宣称完整重读全文，实施依据以实际源标签和既有契约为准。

发现并避免：源参与者解析只读取明确UniProt ID；去掉affected accession后若没有其他可解析标识，不能断言自互作。显示source participant，原参与者仍在附加证据中。

### 文本展示审查范围

Expression的context卡片、选中标题、列表和详情；QTL组织柱图、搜索和明细；PPI集合名称/tooltip及mutation短名。人类可读标签通过display label格式化，保留原filter键和源ID。变异ID、样本ID、ontology ID等机器身份不做全站字符串替换，避免破坏查询或外链。

[方案](../../plan/expression.md#expression-display-refinement)与[交付记录](../../../../record/00_initial_preview/20260921_expression_ppi_refinement.md)维护最终行为及验证；不重复其他并行模块的修改状态。
