# 细胞定位：来源与展示讨论

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

日期：2026-09-20。UniProt、GO CC与简洁HPA位置/可靠性展示已确认，规则见plan；当前两张服务表已按[本地构建方案](../../plan/local_table_build.md)落盘，实际状态见Web数据清单。本轮复用现有来源审查、统计与契约，没有重扫全量数据、下载或新增定位预测。

## 目标与边界

回答蛋白在细胞哪些位置被注释、来源是什么、适用于哪个对象及何种条件。区别细胞位置（细胞膜、内质网、线粒体等）、膜结合方式（跨膜/脂锚等）与残基拓扑区间。后两者留给膜关联特征和位点板块；定位来源中的相关信息保留供关联，不在多个页面独立生成科学结论。

## 当前来源

| 来源 | 现有内容与覆盖 | 状态与边界 |
| --- | --- | --- |
| UniProt2026_03 SUBCELLULAR LOCATION | 当前7,715条目都有该comment；可含位置、拓扑/朝向、注释文本、molecule及证据 | 已有无损comment解析，统一定位正式整理仍待完成；comment存在不代表都有具体细胞器定位 |
| GO CC，本体2026-07-26 | 正向默认CC标签覆盖7,715蛋白 | 正式GO表可复用；CC包括细胞组分/复合体，不能一概改成定位或膜位置 |
| HPA subcellular_location | 4,442条目标基因汇总记录，既有映射关联4,447个accession；14列 | expression已发布；本地版本说明为25.1/Ensembl109；基因级汇总，不是isoform级实验 |

UniProt计数引用本专题results/summary.json；GO来自Function交付结果；HPA来自[来源审查](../../../../../../modules/Function/docs/source_review.md#5-蛋白背景hpa复用与gtopdb补充2026-09-15)及其机器核对文件。各来源覆盖不可相加为独立蛋白数或实验数。

HPA字段：Gene、Gene name、Reliability、Main location、Additional location、Extracellular location、Enhanced、Supported、Approved、Uncertain、Single-cell variation intensity、Single-cell variation spatial、Cell cycle dependency、GO id。

## 推荐页面结构

1. UniProt定位说明：显示位置名称、适用对象及必要条件，展开注释和证据；条目通用与isoform特异信息分组。
2. GO CC表格：复用MF/BP表格形式，列完整名称、GO ID、关系、证据及文献。复合体成员关系保留原义，不能直接画成细胞器定位。
3. HPA：按用户确认直接展示位置与可靠性，可靠性采用颜色及文字图例，提供来源链接。不增加复杂主/附加卡片或单细胞/周期交互；来源字段后台保留。

不先生成一个排他性“最终定位”，不投票。相同位置可以在页面聚合入口中展示多个来源，但保留各自证据和对象；来源未明示位置相同或层级对应时不按字符串相似度合并。跨来源相同文献不算独立实验。

可后续加入细胞示意图导航，但首期不是必要条件。图上位置映射需要明确规则；本地cell.svg是资源入口，不代表已实现动态标注。先让表格和来源链完整。

## HPA特别需要保留的含义

Main/Additional为来源位置角色，Enhanced/Supported/Approved/Uncertain为来源可靠性信息，两者分开。逐位置可靠性按来源分组列匹配，顶层Reliability单独保存，不能直接赋给所有位置；GO id中的名称与ID配对按原文解析，不按不同列表顺序猜配。Uncertain保留并明确标记，不为了简洁删除。

当前汇总文件不含逐细胞系、抗体或图像ID，不能设计成已有逐实验图片库。可链接HPA定位页面查看原站详情；如需要把图片和细胞系数据纳入本地，另行明确来源和范围。单细胞强度变异不等于空间位置改变；没有该标记也不推断恒定定位。

HPA介绍与方法背景见[官方方法](https://www.proteinatlas.org/humanproteome/subcellular/method)、[定位可靠性说明](https://www.proteinatlas.org/humanproteome/subcellular/organelle)。这些用于解释概念，本地版本和覆盖以固定来源记录为准。

## 服务表建议与可精简项

建议初期新增2张逻辑服务表，GO CC复用现有go_term和protein_go_annotation，不为CC再复制一套GO表：

- protein_uniprot_location：一条原始定位comment—项目蛋白关联，内嵌原生subcellularLocations及配对证据，保留molecule、注释原文、来源ID/版本与已确认对象关联。避免将多个位置、拓扑和朝向拆散后错误组合。
- hpa_subcellular_location：一条源基因定位汇总，保留Gene、来源列及已确认蛋白关联；位置角色、可靠性、GO ID可解析成带原文的结构化详情，不复制为每个isoform。服务表是上游正式HPA记录的投影，不重写expression原始发布表。

这两张服务表已构建，当前字段以本地构建方案与数据清单为准。若后续确定要在线统计每个位置，按查询需求增关系表或视图，不提前扩展。

首屏可隐藏但保留详情：长注释、Additional location、逐证据、单细胞强度/空间变异及周期信息。不导入完整原始payload、绝对路径、图像embedding及UMAP特征。保留原始对象范围、限定语、映射状态、可靠性、来源和文献。

## 建议先确定

三来源展示方向已确认：UniProt说明、GO CC表格，HPA简洁位置及可靠性颜色；不做共识定位或冲突裁决。当前方案见[plan](../../plan/protein_overview.md)，下一步讨论膜关联特征。
