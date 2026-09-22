# 蛋白基础信息与功能介绍：实体与字段方案

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

确认日期：2026-09-20。七表设计及字段规则纳入plan；展示规则见[蛋白概览](protein_overview.md)。当前七表已构建，实际列与输入以[本地构建](local_table_build.md)、[数据清单](../../../../data/README.md)为准，本页维护逻辑契约。来源统计见[字段审查](../research/protein_overview/identity_function.md)。

## 1. 设计目标与来源

以UniProt accession作为蛋白页面入口，明确区分蛋白条目、isoform声明与实际序列。基础名称及功能内容采用当前UniProt 2026_03；HGNC标识沿用foundation已确认关系，不按基因名称重新猜配。页面默认canonical不等于每条功能都是canonical特异实验结论。

科研身份与关联由foundation维护。当前用户已授权采用UniProt cleaned身份及同版JSON的机械注释投影，具体输入例外和FUNCTION解析规则以[本地构建](local_table_build.md)为准；不再沿用早期必须等待上游全部curated才可构建的限制。此投影不代表上游注释模块已完成正式发布。

## 2. 七张逻辑服务表

现有上游关系尽量复用；以下为Web/data/tables与PostgreSQL的逻辑设计，不要求每个页面模块各自建一套蛋白主表。

| 表 | 一行含义与键 | 核心字段 | 页面用途 |
| --- | --- | --- | --- |
| protein | 一个UniProt条目；PK accession | protein_name、gene_names（数组）、taxon_id、default_sequence_id、source_release | 名称、编号、human；默认序列入口 |
| protein_sequence | 一条已获取序列；PK sequence_id | owner_accession、sequence、length、is_canonical、source_release | 当前序列、长度及下载 |
| protein_isoform | 一个条目声明的isoform；PK (accession, isoform_id) | isoform_name、aliases（数组）、is_canonical、sequence_ids（数组）、sequence_available、availability_reason | 标出isoform，列出可用与不可获取状态 |
| protein_gene | 一个已确认蛋白—HGNC关联；PK (accession, hgnc_id) | hgnc_status、evidence、source_release | HGNC链接；多关联保留多行 |
| protein_external_reference | 一条Ensembl/RefSeq来源交叉引用；PK reference_id | accession、database_name、external_id、identifier_type、scope_type、scope_id、url、相关gene/protein/transcript编号及来源键 | UniProt/HGNC从已有身份关系通过protein_external_reference_all视图组合，避免重复存关系 |
| protein_function_overview | 一个蛋白默认页面的FUNCTION选择结果；PK accession | default_annotation_id（可空）、status | 默认序列从protein获取，固定selection_rule从构建元数据获取；普通详情视图可组合这些字段 |
| protein_function_annotation | 一条FUNCTION或四类补充来源注释；PK annotation_id | accession、comment_type、scope_type、scope_label、isoform_ids（数组）、mapping_status、text、structured_items、evidences、source_record_key、source_release | 五类注释完整保存，按适用对象展开，每类可含多条 |

共同说明：

- gene_names来自UniProt；HGNC关系表不以另一个来源符号覆盖这些名称。无需为这两个模块单独复制完整HGNC数据库。
- sequence_ids数组忠实保留现有声明关系，包括跨条目序列；其中每项应关联实际序列表。工程构建检查数组引用，若后续需要频繁关系查询或数据库外键约束，再拆isoform—sequence关系表，当前不预建。
- 未获取序列不伪造空序列实体或长度0；isoform声明保留不可获取状态。无显式isoform编号的canonical只展示真实sequence_id及canonical标记，不拼接虚构编号。
- 外链表scope_type/scope_id表达entry、isoform、gene或来源尚未解析的对象；不能将条目级xref当成精确序列对应关系。UniProt/HGNC链接可由已有标识生成，其他xref从上游正式整理记录读取。
- 必要外部库名称、ID和来源关系入库；UniProt/HGNC已有身份不在xref表重复存储，完整URL通过受控模板及普通视图提供，不能仅保存URL而丢失标识。本轮范围为UniProt、HGNC、Ensembl、RefSeq，疾病标识已去除。缺少编号允许NULL，不强补。identifier_type区分原external_id类型，物理表用gene_id_full/protein_id_full/nucleotide_id_full保存来源配对编号；普通视图恢复完整角色编号及URL。只有RNA类型才填transcript_id_full，NC_等核酸编号不冒充转录本；RefSeq蛋白用protein链接，核酸用nuccore链接。2026-09-21本版已落实编号修复及物理关系去重，主编号仅存external_id，角色列仅保存来源配对编号；对应完整编号和URL通过普通视图恢复。实际交付见[版本记录](../../../record/00_initial_preview/20260921_basic_info_v2.md)。
- source_release保存来源本身版本，不引入Web release目录。构建输入路径与构建时间集中放配置/数据说明，不在每行复制绝对路径。
- annotation_id/reference_id采用内部普通标识，配合source_release/source_record_key追溯，不计算SHA。来源顺序号只在当前来源版本内定位，不当作跨版本永久生物学ID。
- structured_items/evidences为可空结构化字段（入PostgreSQL可用JSONB），仅保存展示或追溯需要的结构，不复制原始完整payload。催化反应、辅因子不能只读comment通用text字段，须解析其专门结构；如来源含Rhea/ChEBI标识保留对应标识及链接，不重新做跨来源推断。
- overview.default_annotation_id外键指向同一服务库protein_function_annotation，必须属于同一accession且为FUNCTION；不复制选中原文。overview是默认展示选择结果，不承担完整注释存储。
- annotation按来源comment保存，保留内部全部文本段落及证据对应关系；同一isoform可有多条FUNCTION。同一comment明确适用于多个isoform时保留全部关联，不任选一个；isoform_ids为空不等于canonical。数组项关联当前accession的isoform声明，序列通过声明关系取得。
- scope_type取entry、isoform、processed_product、unresolved；scope_label保存来源原始molecule名称，mapping_status记录关联状态。没有molecule的通用注释与无法解析的具名对象分开。即使序列不可获取，仍可关联已确认isoform声明并保留注释。

## 3. FUNCTION默认选择：规则已确认

权威规则维护在[方案](protein_overview.md#功能介绍已确认展示规则)：canonical优先，其次条目通用，同级按UniProt原始顺序取第一条，否则默认留空。规则仅选择默认展示项，不筛除服务库中的其他注释。来源molecule名称必须通过明确关系识别canonical，不能假设Isoform 1就是canonical。

例如本地P00533有一般功能、Isoform 2功能和另一条无molecule的感染相关功能。采用上述规则会选首条一般功能，其他记录在上游及服务库均保留，展开后可查看。已有673个蛋白有多条FUNCTION，不能将“取一条”简单理解成所有蛋白按首行截取。

status区分selected、source_missing、no_applicable_annotation、scope_unresolved。现有628个缺FUNCTION是来源文本缺失数量；最终默认展示覆盖以实际选择结果为准，不能用该来源统计代替；当前选择已随七表构建执行。

四类补充信息已确认按canonical对应信息与条目通用信息分组展示，两组均不限制一条；其他isoform信息折叠查看。来源明确限定其他产物的内容保留scope标签，不能无标签地挂到canonical；具体分组控件属于后续页面设计。

## 4. 页面与API

身份区：protein_name；accession；gene_names与HGNC；human；当前sequence_id/isoform名称、canonical标记及对应length；外部标识链接。

功能区：默认最多一条FUNCTION预览，下方四个并列类别；展开后按条目通用、isoform、加工产物及待解析对象分组，查看全部FUNCTION和补充注释。同一组有多条则全部显示。无FUNCTION或补充字段缺失时，数据库用NULL/空集合，页面留空，不使用“无功能/无辅因子”等生物学否定措辞。长文本可视觉折叠，数据库保留全部来源注释原文。

API可将上述关系组装成identity、sequence、external_references、function_preview、annotation_groups五组对象，无需让前端分别查询七张表。展开内容可按需请求，但必须可从服务数据库取得，不能只留下上游文件引用。内部source_record_key、selection_rule和路径不默认返回页面；来源名称、版本及有用文献链接可按需返回。没有确认完整isoform切换交互时，不预设切换后继承canonical简介和其他轨道。

## 5. 后续落实与必要验收

FUNCTION选择优先级及补充信息分组保留；外部xref本轮排除疾病标识。具名功能对象无法对应isoform时不补给canonical；默认canonical及通用背景语义保持。外链修复和字段精简进度见[本版记录](../research/basic_info_v2/README.md)，不要把代码修复当作已刷新数据库。

必要核对仅覆盖本次契约：条目覆盖当前目标；默认序列存在且长度匹配；isoform声明状态和跨条目关系未丢失；多HGNC关系保留；每蛋白最多一条默认选中FUNCTION且引用同蛋白注释；所选来源五类注释完整入库，未因默认选择丢失其他isoform或同对象多条记录；选中对象范围正确；四类结构化内容解析正确；缺失与不适用分开；外链可从库内标识/URL重现。统计原始有文本数、最终选择数及空值原因，不能以已有7,087个有文本蛋白代替最终选择覆盖数。

蛋白基础信息末尾将加入[数据总览面板](../research/protein_overview/data_overview.md)，本轮仅记录大纲，不增加统计表或计算指标。
