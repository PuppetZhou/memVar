# 序列五类展示：字段保留、整合与待处理清单

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

更新：2026-09-21。仅canonical，突变留到下一板块；来源最后统一统计，但保留逐条出处关联。五类分组见[轨道方案](sequence.md)，PTM字段收口见[PTM服务方案](sequence_ptm.md)。不删除科研原始或正式数据、不跨库去重；服务投影已导入，见[版本记录](../../../record/00_initial_preview/20260921_sequence_v1.md)；展示与统计剩余事项见下文。

## 通用最小契约

轨道API只返回绘图需要的record_id、sequence_id、位置/端点/区段、原始类型、短标签及来源提示；显示分组display_group不覆盖source_type。不确定边界必须带状态，未定位记录通过详情列表查询，不产生虚构坐标。默认不随轨道返回长文本和全部文献。

服务数据库保留：accession与明确sequence_id、参考版本、来源原始对象、来源记录键及版本、mapping_status与方法、坐标体系/边界修饰符、原始类型、详情/证据关系。原生坐标与目标坐标不同则分别保留；已确认相同且能通过来源键追溯时可避免冗余同值列。所有位置查询必须限定序列，不能只用accession+position。

## 五类字段取舍

| 分类 | 默认图上/悬停 | 点击详情：需存入服务库 | 整合与精简建议 |
| --- | --- | --- | --- |
| PTM | 位置、残基、修饰类型、来源标记；可聚合显示多记录数 | 五来源本轮范围内记录、修饰原文、证据/引用；糖链或成键信息；PTMD2疾病原名/ID（来源有时）、State、MutationSite、Sentence及引用 | 多来源使用统一record/site/link契约，topic同schema分片可导入同逻辑表；详情一对一可嵌入，但多端点与多证据关系不能丢 |
| Domains | 起止、名称/类型；UniProt与Pfam同组；二级结构子类型 | 来源ID/版本、完整描述、证据；Pfam条目类型/Clan、E-value/score及alignment/envelope/model坐标 | 复用同一feature主表和类型字段；词典名称/定义只保存一份；保留不同命中，不按重叠区间合并 |
| Membrane | 当前来源/方法下的TM、Intramembrane、侧别区段及对象 | 来源方法、记录role、原类型、证据/约束、原坐标与映射；结构链背景（适用时） | 复用膜服务记录；不复制多来源大宽表。DeepTMHMM2仍独立来源，接触按需叠加，非TOPO记录不计入区段数 |
| Function site | 位点/端点、Active site/Binding site/Site及配体短名 | 作用原文、ligand与ligandPart ID/名称、来源链接、证据与否定/条件说明 | 复用UniProt feature表，通过类型过滤。Binding site无description时用真实配体名称，不丢记录 |
| JSD | 位置、残基、JSD连续值与必要质量提示 | occupancy/gap、n_nongap、序列深度、homology_status、非标准残基及历史质量标记，方法与检索库版本 | 一行一个序列残基评分，蛋白/MSA批次信息放summary/dataset，不在每个位点重复；不另存按前端颜色离散的新等级 |

PTMD2没有来源标准疾病ID时原名保留，不能为方便展示猜配；突变具体详情字段和分类遵循[五表方案](variant_tables.md)，上表不扩大评分范围。

## 如何减少重复表和数据

1. 序列复用foundation服务实体，五组限定canonical并共用坐标；不在注释行重复完整蛋白序列或gene name。
2. Domains/二级结构与Function site共享feature契约，前端分组不同不要求物理分表。字段稀疏的特殊内容放有契约的详情，不建覆盖所有类型的巨型宽表。
3. UniProt PTM已由PTM整理记录引用原feature ID。Web为这份原记录建立一个权威入口，其他视图引用同一键，避免把它从UniProt feature表与PTM表各导入一份并重复展示。此为避免重复加载同一输入，不是合并不同数据库的PTM记录。
4. UniProt膜feature在TOPO和sequence之间同样共享来源键；不额外把“概览轨道副本”当成第二份注释。
5. PTM annotation_record/detail一对一时可投影成短字段+结构化详情；record_site保持多端点/位点角色，evidence维持与来源记录关联。证据与主表不作全量乘法展开。
6. 源版本/方法放dataset，术语描述放字典；PTM同一site的多来源记录仍分别保存。不以来源条数称独立实验数。
7. 原有GO/Rhea/GtoPdb的字典和外链有适用共享键时复用，不因同一个配体名称就新增跨库等价关系。
8. JSD逐位点、结构接触逐观察的粒度分别保留；突变下一板块处理，不为了减少表数合成一个site宽表。当前不固定总表数，先按查询与关系确认最小服务模型。

## 不进入网站库的冗余内容

原始TSV/XML/JSON整包、完整payload中未使用的重复字段、内部绝对路径、调试日志、重复蛋白名称与序列、重复词典定义。原始数据和上游可追溯入口继续保留。

JSD不导入完整MSA/检索命中列表到每个位点；历史entropy/WT frequency本来未纳入当前正式JSD产品，不在本轮新增网站轨道。完整MSA等计算输入继续留上游。

Pfam不导入完整domtblout原行及HMM模型大文件到服务库，但必要score、E-value、三类边界、来源与状态保留。复杂来源payload只有在确认选定字段能完整表达当前详情后才省略，不能先删后发现丢失疾病、配体或端点含义。

## 不能为了精简删除

PTM同位点多来源、多证据、未定位状态及PTMD2疾病原文；来源对象（不将其他isoform改挂canonical）；坐标不确定性；二硫键端点；Pfam不同命中及三类坐标；JSD同源支持不足标记；膜来源方法/role。没有明确源链接的引用原文保留，不伪造PMID。

## 还需核实或处理

| 优先事项 | 当前事实 | 下一步 |
| --- | --- | --- |
| UniProt服务字段投影 | 四组feature已正式发布 | 已投影共用feature并核对；Sequence视图仅取canonical，页面后续接入 |
| PTMD2精确连接 | 103,800条项目记录全部尚无正式site连接 | 本轮保留蛋白级来源详情，不新增映射研究，不凭残基吻合连site |
| PTM其他未连接记录 | 未连接总计153,279含PTMD2；含23,061条deprecated-only、26,418条其他未确定记录 | 沿用现有映射，分类保留状态；停用-only不自动恢复为现行位点，其他来源事实不删除 |
| Pfam新版交付 | 当前23,651条命中已正式发布并导入 | 已复用7,710条序列并补算5条；三套边界均保存，主轨道边界待确定 |
| JSD展示 | 7,715 canonical、4,364,831残基已发布 | 已按canonical导入，序列级背景移到summary并核对；原值保持 |
| 二级结构来源 | UniProt97,399条正式feature | 可直接做原生来源轨道；不能当成当前选中结构的DSSP。rSASA旧数据仍待整理，不默认加入本轮 |
| 膜数据接入 | DeepTMHMM2与OPM/接触本轮已按授权从cleaned接入Web，见[本地构建](local_table_build.md) | sequence复用现有来源键与mapping结果，仅mapped记录上轨，未定位记录继续保留 |
| 通用计数与API | 页面类别已确定 | 位点、feature和记录计数分开；来源汇总最后统一处理；先读轻量轨道，再按记录请求详情 |

来源证据见[Site-Region结果](../../../../../modules/Site-Region/docs/result.md)、[feature契约](../../../../../modules/Site-Region/docs/tables.md)、[PTM契约](../../../../../modules/Site-Region/docs/ptm_tables.md)及[JSD契约](../../../../../modules/Site-Region/docs/conservation_review.md)。已执行网站服务投影、字段精简及相关验证；上游来源保持不变，Pfam增量另发布新快照。
