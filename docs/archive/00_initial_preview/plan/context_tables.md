# PPI/QTL：列精简与查询设计

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

更新：2026-09-21。用户确认将既有讨论纳入plan；字段投影与逻辑表组织采用本方案，展示规则见[context](context.md)。来源范围和科学边界不变，已按本方案构建并导入PostgreSQL，实际精简及验收见[本版记录](../../../record/00_initial_preview/20260921_context_v1.md)。

## PPI字段

| 层 | 保留内容 |
| --- | --- |
| 默认列表 | 伙伴名称/源标识、物种、互作类型、检测方法、文献入口、来源interaction ID/链接；context作为筛选条件或简短标签 |
| 点击详情 | 双方原始标识及必要别名、实验/生物学角色、宿主或条件、来源confidence/score及原名、通量、表型/修饰/备注（来源有时）、阴性或其他限定标记 |
| 后台 | record_id、dataset/source/version、端点与映射候选、context membership、来源原键及已确认身份关联 |
| 网站可省略 | 原始整行、绝对路径、大小/mtime、来源checksum、解析调试列；未用于检索的重复别名/历史ID留上游 |

BioGRID的Experimental System与Experimental System Type分开，一个是方法一个是类别；IntAct detection method与interaction type同样分开，不用名称相似直接建立跨来源等价分类。阴性结果、非蛋白对象等改变解释的字段必须在列表有提示，而不只隐藏在深层详情。没有可靠UniProt ID时显示原标识，不生成错误外链。

context菜单从现有ppi_dataset.context_raw和已验证字段生成可用值，保留原词与来源。默认列表以当前数据库full集合或明确选定context为入口；不要默认把full与所有context简单拼接，否则同一观察重复出现。多集合结果若日后需要统一展示，要先确认原生interaction身份与membership，不仅按两端名称去重。

采用ppi_record、ppi_participant、ppi_dataset三类逻辑服务结构；同库同schema的context文件可纵向整合，source/kind/context键仍保留。数据库分开显示不要求物理拆成两套schema。来源没有的上下文不补造；场景词表具体值需读取现有数据后确定。

官方依据：[BioGRID结果页说明](https://wiki.thebiogrid.org/doku.php/results)、[实验系统定义](https://wiki.thebiogrid.org/doku.php/experimental_systems)。其互作包含物理和遗传等，不保证全部为直接结合；本项目遵循具体记录含义。

## QTL字段

| 来源 | 默认列表列 | 详情与后台保留 |
| --- | --- | --- |
| GTEx pairs | 来源variant标识/坐标、phenotype/event、组织、P值及效应 | gene/group、效应SE、来源已有MAF/样本计数、min_pval_nominal/pval_beta等原统计、组装、来源版本与行键；不存在者不补 |
| GTEx summary | 默认不混入配对列表 | q值、代表关联与表型模型汇总、原始分组，单独基因/表型详情 |
| eQTLGen | SNP/rsID、GRCh37坐标、Pvalue、Zscore、FDR | AssessedAllele/OtherAllele、NrCohorts/NrSamples、BonferroniP、源Gene及背景；GenePos为来源基因中心，不充当TSS或基因起止 |
| QTLbase | 来源SNP位置、性状区间、Pvalue、研究/组织/QTL类型 | hg19与hg38两套原坐标、Mapped_gene、Sourceid；经研究字典取PMID、Population、Sample_size等；无REF/ALT、效应或FDR时不造字段值 |

筛选后的数据库、QTL类型、组织和当前基因可放表头，不必每行重复显示；数据库仍保存查询必需的键。QTLbase的PMID/组织/样本量只在dataset保存一次，GTEx/eQTLGen研究常量同理；hg19/hg38等两套真实坐标不是冗余应删字段。

源文本的数值解析成可排序便利列前，核对精度、极小P值、0/NA/缺失与不等号，必要时保留原文本。P=0不直接转成无限绘图高度；若后续采用-log10(P)图轴，需要明确绘图上限和原值提示。当前可先使用无P值纵轴的坐标标记。

可不入网站库：原始整行、绝对路径/压缩成员清单、重复研究标题/期刊等每行副本、重复gene symbol（可从身份表取显示名）；保留Sourceid、源gene身份、原始表型、来源坐标/组装、等位基因、统计和匹配状态。不能因列很多就删除效应等位基因、sQTL事件ID或QTLbase性状区间。

## 数量概览与基因坐标视图

按hgnc_id × database × qtl_type × source_tissue × study需要的维度预计算轻量计数，明确统计输入角色pairs/association及当前筛选。summary不混入；eQTLGen含非显著记录，来源数量不等于显著QTL数量。不跨数据库累加为独立发现，不通过基因—多蛋白展开后计数。

大量结果在服务端分页，点击概览后图和表使用相同查询条件。统计可增加一张派生qtl_context_count表/物化视图，或构建时输出汇总；以下5类逻辑服务表不变。任意筛选后的计数不能拿未过滤预计算值冒充。

坐标视图规则：

- 横轴为染色体基因组坐标，标明组装；基因区段和QTL来源位置分别标记。候选范围不截掉基因外cis/trans关联，可缩放/平移；不同染色体分开，不画到同一基因轴。
- GTEx使用已有b38位置，eQTLGen使用GRCh37，QTLbase选择其已有匹配组装坐标；不做liftover或variant_id连接。
- 当前foundation基因坐标不能直接用于所有组装。匹配版本的基因起止若缺失，仍可展示来源位置表或单独坐标轨道，但不能绘制错误基因轮廓；补齐同组装参考注释另行登记来源。
- 基因区段需要起止与链方向；若要显示外显子/转录本模型，还需匹配组装的注释，不根据SNP位置推断。当前不预设这一复杂度。

## 待核实事项

PPI：实际context标签菜单、不同来源互作类型原词、伙伴身份及full/context重复包装；仅做显示整合不生成新实验关系。

QTL：可用组织/研究维度、各类P值及效应字段的精确含义、坐标与基因参考组装、派生计数与分页一致性。保留既有来源完整记录，不进行突变mapping、不加显著性阈值、不删除低显著记录。

上述事项按09-21授权落实；执行结果以本版记录为准，不把此前未构建状态作为当前限制。

## 逻辑表与关联

PPI采用3表：ppi_record保存来源关系与证据详情，ppi_participant保存全部端点/角色/物种和映射候选，ppi_dataset保存来源、版本与context集合。保留record到dataset的集合归属；同一记录属于多个集合时不得用单值字段覆盖其他归属。来源研究见[PPI/QTL调研](../research/context/ppi_qtl.md)。

QTL采用5类：gtex_qtl_pair（用qtl_type区分e/s/apa）、gtex_qtl_summary、eqtlgen_cis、qtlbase_association、qtl_dataset。保留各源异构字段与原粒度，研究元数据集中维护；统计表或物化视图按查询需要增加，不计入这5类基础表。3+5不包括共享foundation实体、预测界面或未来variant mapping。

串联：蛋白→已确认基因身份→QTL来源记录→研究/组织；蛋白→PPI参与者→来源关系→其他参与者及证据。不以同基因推断isoform、位点或变异关联。

## 2026-09-21精简与导入决定

- QTL保持五类基础结构，研究/组织/版本通过dataset关联；不复制蛋白维度。不做variant mapping，不用gnomAD AF替换QTL原af。保留全部原统计、效应等位基因、事件ID及双组装坐标。原数值字符串保留精度及特殊缺失，不默改零值。
- GTEx配对中的表型级常量只有逐组核实一致才可抽取；未证明固定时继续保留。summary不混入pairs或替代它。
- PPI按同数据库、相同原生内容核实full/context重复包装，共用正文；membership保存所有原记录及集合归属。不同内容即使interaction ID相同也分别保留，不按两端名称合并。
- 参与者的原身份、物种、角色和全部原注释保留；项目蛋白关联独立存储，不因多候选扩展正文。去掉来源checksum与内部文件路径等工程列，不去掉阴性、方法或文献。
- 原“3表”是逻辑职责，不限制实际物理表数；增加membership和蛋白关联表以保存多对多关系。
- 本轮使用同库独立web_context schema，防止并行Variant/Sequence构建替换web schema时覆盖本板块。通过现有HGNC/accession键跨schema查询；完整构建与验收信息独立维护。

本轮并行隔离例外：context当前Parquet保存在`Web/data/context_tables/`，不放入由主任务整体替换的`Web/data/tables/`；避免主任务清理旧表目录时删掉本板块产物。此目录仅保存当前版本，不建立releases/runs。
