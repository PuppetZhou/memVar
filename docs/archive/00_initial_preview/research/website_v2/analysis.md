# 第二版调研分析与上下文

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

日期：2026-09-21；范围：第二版及03:58–04:03追加反馈、后续定位/通路精简。当前问题与处理状态见[问题清单](issues.md)，采用后的方案见[website_v2](../../plan/website_v2.md)。

## 任务上下文

PostgreSQL导入已完成。用户从逐板块展示选择推进到自主构建初版，现要求直接修改为第二版，并明确同步记录问题、调研细节及方案。本轮重点是信息展示、可解释颜色和交互，使用现有正式数据；不重新决定科学收录范围，不重新导入，也不创建第二个测试环境。

用户提供五张2026-09-21截图：02:41为需移除的冗长PubMed简介；02:46为全残基彩色序列；02:48为变异密度与feature hover；02:50为带AF、预测器、原分类的目录；02:56为统计卡片。截图是交互/信息结构参考，截图内KCNH2记录数不用于memVar。

## 已阅读与重新核查的证据

1. 项目[既有调研目录](../../../../../Web-research-reference-2026-09-20/README.md)及CATVariant的[交互](../../../../../Web-research-reference-2026-09-20/docs/sites/catvariant/04-interaction.md)、[视觉细节](../../../../../Web-research-reference-2026-09-20/docs/sites/catvariant/08-icons-and-microdesign.md)。它们是2026-09-20研究快照，实时页面观察需另行区分。
2. [CATVariant KCNH2](https://catvariant.com/genes/KCNH2)，本轮重新打开公开网页和浏览器UI。实际观察全序列lens按钮（Prevalence、Predicted Functional Impact、Variant Hotspot）、density与domain坐标、可点注释、分类/AF/预测器区域；对PAS 41–70执行hover与click。完整页面存在大量结构及分析内容，本项目仅采用符合当前正式数据的交互模式。
3. [VarSome Clinical Cards官方说明](https://docs.varsome.com/en/clinical-cards)：按来源/数据类型组织摘要卡片，再展开原证据，缺数据项可禁用；提供显示选项。这里借鉴来源卡片和明细层次，不引入VarSome的ACMG/AMP自动分类。
4. 旧项目只读实现：`/home/xuyzh/memVar/website/frontend/components/interaction-summary.tsx`、`components/expression/expression-overview.tsx`。互作按source/context/category分组、点柱条跳筛选，区分原记录与native IDs；表达把不同measurement分别表达。复用交互思路，不自动继承旧数据聚合或颜色阈值。
5. 当前真实接口`/api/proteins/P00533/sequence`：426个PTM聚合feature、16个domain/region feature、146个secondary、3个UniProt膜/拓扑区段、6个功能位点/区域（本轮局部观察值，不作固定常量）。PTM图元只有record_ids/count，原证据必须进一步查detail，不能仅把图元当完整注释。
6. 本轮后端真实库局部验证（2026-09-21，尚非最终浏览器验收）：P00533共4,096个DNA variants；已验证canonical映射2,773个、覆盖1,120残基；1,323个缺当前服务可用验证关系；频率有值2,168个/缺1,928个。数据覆盖和详情端点由[API实施记录](../website_v2_api.md)维护；这里的数字用于发现问题，最后以实际接口为准。

### KCNH2本轮实际交互补充

目录搜索输入`P2L`后，界面显示`Showing 1 of 2407 variants`，主行同时保留REVEL、AlphaGenome、PolyPhen-2、SIFT、CADD、PHYLOP各自值、MAVE原值及ClinVar/EBI/UniProt独立分类。采纳的是“短变化检索+并列不同证据”，不采纳站点自有INCONCLUSIVE/priority score作为本项目判定。

对Predicted Functional Impact做hover，观察到Average（weighted average）、REVEL、AlphaMissense等选项。本项目改为可显式选择已发布预测器，避免未经确认的跨方法平均。公开服务端文本报告2,412条，而此时浏览器目录显示2,407条；本轮未调查其差异原因，因此不将任何参考站统计作为我方验收数值。

[VarSome Variant table官方说明](https://docs.varsome.com/en/variant-table)用于复核临床分类、HGVS/位置、原来源annotation的独立职责。未登入其样本系统，不声称完整复现了私人样本页面。

## 采纳与取舍

**从“折叠目录”改成“摘要→选择→明细”。** 完全折叠让用户不知道有何数据；完全展开造成长文本占屏。每子区先呈现短内容或统计，用可点来源、类别、组织引导下一步。

**颜色分别表达对象。** 模块底色用于定位；PTM/二级结构/来源颜色用于分类；AF、JSD、预测分数表示各自原量尺；临床分类的红绿橙只解释原来源结论。CATVariant界面上的集成prioritization或impact不能直接移植为memVar的新科学评分。

**全序列与轨道双视图。** 轨道适合区域边界和缩放，残基网格适合逐位点浏览与计数。两者共享canonical及所选残基，但所选transcript HGVSp与canonical并不等价。严格复用正式验证关系可立即提供可信的变异分布，其余目录记录明确保留。

**总览计数应可解释。** 不能统计第一页、把各来源计数相加成唯一变异数、把互作context memberships当唯一蛋白对、把来自不同单位的表达值混排。所有summary采用已确认粒度与完整当前筛选范围，unit/scope随API返回。

## 细节复核依据与新增发现

- 独立Context审查：[context_review.md](context_review.md)，包括旧站Expression模型、PPI摘要与VarSome来源卡片、采纳/未采纳及真实0/缺值处理。
- SIFT/REVEL细条量尺：参照[SIFT原论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC3394338/)与[REVEL官方说明](https://sites.google.com/site/revelgenomics/)，仅用原0–1数值线性长度，并注明SIFT低值/REVEL高值各自方向，不反转、不新增阈值、不变成致病概率。CADD PHRED无同样固定上限，因此不用伪0–1条。
- HTP原生拓扑字母及来源性质参照[HTP原论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4445273/)和[CCTOP官方代码定义](https://topdb.unitmp.org/documents/cctop)。显示字典限定HTP源，M表示膜区段、I/O表示内外；不把任意来源M字符都解释为膜。
- GlyGen原N-linked/O-linked需可读的糖基化颜色；糖基化术语对照[UniProt官方说明](https://www.uniprot.org/help/carbohyd)。原source_type仍显示。Dephosphorylation不能因包含phospho而显示为Phosphorylation，匹配顺序已独立处理。
- 读本地安装Nightingale `withZoom`源码核实其坐标domain为[start,end+1]，残基字符位于半格中心；自绘轨道和JSD采用相同scale并统一左右内边距。该问题来自实际独立代码审查，不归咎于参考站。
- 首轮Expression有category/source/measurement概览，但缺少用户明确需要的逐组织/细胞总览，继续补`/expression/contexts`单dataset分页分组；不把不同来源组织名强行合并，也不将癌症样本ID声称为唯一组织。

## 浏览器与执行边界（运行记录）

本轮内置浏览器工具返回无可用浏览器，按工具排障只检查一次列表。复用既有`memvar-v1` Chrome会话查看参考页和验收同一8000服务；不是另建环境。功能验收产物临时存`/tmp/memvar-v2-qa`，最终记录将写明真实通过范围，不能把仅有代码或API测试记成浏览器完成。

## 追加反馈调研与采用（2026-09-21约03:40）

用户03:28人体图与03:30分数条截图为追加依据。PTMD移Disease、PPI图纯展示直接替代此前相冲突方案。

[PTMD 2.0官网](https://ptmd.biocuckoo.cn/)文本请求502，但现有Chrome成功访问，实际看到首页All PDAs by tissue location：人体器官示意配右侧原组织名称横条，上方PTM类型环图与State图。截图`/tmp/memvar-v2-qa/ptmd-reference.png`仅作审查证据。借鉴位置导航与计数，不复制人体图片、不将PTMD疾病组织数据用于我方QTL；器官UI词典不是科学本体映射。

PTMD官网明确区分文献实验支持与整合potential PDAs，不能把EGFR的463条全称实验验证。Disease保留原Disease/State/MutationSite/CellType/Enzyme、来源类型与映射状态，PTMD2从Sequence展示查询排除，原产物未改动。

CATVariant计数背景白/灰，再绿、浅蓝、黄、粉；颜色只解释计数档位，绿色AA不等于良性。变异分布另用原ClinVar六桶，规则见[API文档](../website_v2_api.md)；多label分歧不取所谓最严重分类。bin仅为视觉尺度，不改原位置。部分输入variant可能映射多个位置，图总和标为variant–position links，不暗称distinct DNA variants。

注释删减仅限默认显示：PTM默认UniProt、其他来源和all仍可选择，相邻位点合marker再点各自原记录。Domain默认UniProt明确域，Pfam与regions/processing可选；secondary单行、重叠可点选，多lane可选。这减少默认密度，不删除正式来源。

### 预测细条的扩展依据

定向核对[dbNSFP5.4a官方字段表](https://dist.genos.us/release/dbNSFP5.4a_variant.columns.txt)（49–60、73–150、156–160、181–185列），以[MutPred2官方帮助](https://mutpred.mutdb.org/help.html)、[AlphaMissense原发布](https://deepmind.google/blog/a-catalogue-of-genetic-mutations-to-help-pinpoint-the-cause-of-diseases/)交叉核对。当前正式字段为MutPred2_score，不能误用旧MutPred v1.2说明。

界面34个已核实字段使用原0–1轴，SIFT/SIFT4G低分方向不反转，phastCons只表示保守性，ALoFT fraction只表示受影响转录本比例。颜色只解释已匹配原判定的逐字段含义，不运行阈值；PolyPhen P是possibly damaging，AlphaMissense P是likely pathogenic，不用通用单字母字典。CADD、MutationTaster等本轮没有确定相同量尺的字段保留原数值。P00533/R2L局部API证据：AlphaMissense 0.1701/B、HDIV 0.02/B、HVAR 0.013/B、MutPred2 0.367965/BP、SIFT4G 0.02/D，均有匹配原分类；此处不由数值重新判定。


## 第三轮研究与取舍（03:58–04:03反馈；含后续精简指示）

### 参考对象与采纳边界

- 用户新增截图要求CATVariant式预测器介绍、UniProt定位与GO预览。本轮实际打开并读取Cellular Location区（包括Cell membrane、ER/Golgi、Nucleus和Isoform 2 Secreted等来源范围）的[UniProt EGFR entry](https://www.uniprot.org/uniprotkb/P00533/entry)，官方[Subcellular location说明](https://www.uniprot.org/help/subcellular_location)及[SwissBioPics帮助](https://www.swissbiopics.org/help)表明图形与定位ID关联，isoform限定和自由Note仍需分开。采用“按来源/适用对象看标签与证据”的结构。**用户后续认为细胞图不美观且文字反而增加，因此最终删除复杂示意图，采用简洁icon/定位标签和按需详情**；不以复刻参考图为目标。
- [GO subset官方说明](https://geneontology.org/docs/go-subset-guide/)解释slim是本体的概览子集；本项目已有generic slim桥，直接利用该已发布关系做三aspect预览。不是重新聚类、富集或自创GO层级。NOT/ND不进入正向slim支持计数，原全量注释仍可查。
- [Reactome Pathway Browser指南](https://reactome.org/userguide/pathway-browser)将层级概览、实际diagram及原事件详情区分；[Diagram Widget](https://reactome.org/dev/diagram)说明官方图嵌入方法。当前仅有已发布关联，不能从通路名推断连接。**后续精简指示替代大型pathway展示**：主面板少量通路预览与查看入口，官方diagram移到所需条目，避免默认铺开完整网络/长说明。
- [Ensembl VEP canonical选项](https://jun2026.archive.ensembl.org/info/docs/tools/vep/script/vep_options.html)与项目实际VEP116代码共同确认当前flag含义。原值及局部核对证据集中在[API记录](../website_v2_api.md)，不把MANE选择依据等同canonical实测flag，也不把未映射UniProt解释为non-canonical。
- [Ensembl consequence定义](https://jun2026.archive.ensembl.org/info/genome/variation/prediction/predicted_data.html)以allele与transcript为语境。目录对复合后果逐项着色，后果横条可重叠、不冒称互斥比例；ClinVar六类图使用既有显示归组，二者不能混称“预测诊断”。
- [AlphaMissense原研究](https://deepmind.google/research/publications/21083/)支持其missense适用对象；[AlphaGenome官方说明](https://deepmind.google/blog/alphagenome-ai-for-better-understanding-the-genome/)对应DNA调控/剪接等输出。前者默认独立展示；两者不混同，介绍卡不复制参考站的ACMG证据强度、工具百分位或综合priority score。

### 数据与实现细节

1. 完整当前筛选的summary返回后果、原临床类别、代表转录本状态和61字段可用覆盖。页面区分61字段/43种来源工具标签；这些标签不是独立方法数量，相关算法/版本不在网站自创归并。分组只是阅读导航。
2. 基因组列明确GRCh38、variant ID、chromosome/position和来源REF/ALT。用户“原始/替换后的剪接”结合其请求按核苷酸替换及原HGVSc展示；目前没有生成完整剪接前后序列或把SNV声称为实验剪接改变。
3. [本地JSD方法审查](../../../../../../modules/Site-Region/docs/conservation_review.md)定义为位点残基频率对固定背景分布的Jensen–Shannon divergence，保留原0–1值与覆盖支持状态。新增0.5虚线仅坐标参考；悬停上下箭头是与相邻位点的数值差，不是通路上调/下调、进化速率或致病概率。示例P00533 L858原值0.7439347288392442，原支持High；不重设科学阈值。
4. 新GO summary区分annotation record、distinct term及slim membership；Reactome区分association与distinct pathway。统计完整查询并与分类明细total相核对，不能只用首屏30条GO/15条Reactome估计覆盖。
5. 复杂图与文字同时增加会使摘要失效。本轮后续精简决定优先于早期复杂细胞图方案：主视图回答“在哪些位置/有哪些通路”，证据与长注释只在请求时出现；UniProt FUNCTION长文完全从页面及详情删除，正式源数据保留。

本轮不重导入已确认数据；同时维护的interface导入/序列结构任务见独立计划，其进度不在本轮冒记为已验收。

## 共享坐标轨道：P00533／Q12809 只读观察（2026-09-21）

用户追加要求集中显示 JSD、Domain/Region、Functional Site、PTM、Secondary、Variant Density、Interface。本次仅读取现有前端默认条件，并用真实只读库和当前 API 对两个蛋白取数；没有改 API/Sequence 文件、导入、构建或浏览器操作。以下是这两个对象的现有来源记录，不外推全库覆盖。

### 默认 domain 稀少的原因

核对时 `SequenceAtlas.tsx/FeatureTrack` 的局部 `localSource='UniProt'`、`regions=false`。因此全局选 All sources 仍会沿用局部 UniProt；domain 轨道只保留原类型精确为 Domain 的记录。P00533 默认只显示 Protein kinase 712–979 一条，Q12809 只显示 PAS 41–70、PAC 92–144 两条。其余已在 API 中，不是未导入。

建议默认显示已有 Domain、Repeat、Region、Motif、Coiled coil，同时显示或清楚提供 Pfam 来源行；保留原类型、来源与重叠，不把同位置不同来源合成科学共识。Chain、Signal、Compositional bias 放在可选 Processing/context 层，避免全长 Chain 遮住局部域。按此范围，两个示例分别有12、15条可默认呈现的原注释；这是显示取舍，不改变正式数据。

| 轨道或对象 | P00533（1210 aa） | Q12809（1159 aa） |
| --- | --- | --- |
| Domain/region 全部原记录 | 16：UniProt9＋Pfam7 | 20：UniProt14＋Pfam6 |
| UniProt 域/区段原类型 | Domain1、Repeat2、Region2；另Signal1、Chain1、Compositional bias2 | Domain2、Region5、Motif1、Coiled coil1；另Chain1、Compositional bias4 |
| Pfam hit 原类型 | Domain5、Repeat2 | Domain4、Family2 |
| Functional site | 6：Binding site4、Active site1、Site1 | 0 |
| Secondary（UniProt） | 146：Helix56、Beta strand76、Turn14 | 52：Helix30、Beta strand19、Turn3 |
| 默认 UniProt topology | 3：Topological domain2、Transmembrane1 | 15：Topological domain8、Transmembrane6、Intramembrane1 |
| JSD 已有数值位点 | 1210／1210 | 1159／1159 |
| 已验证变异位置／独立变异 | 1120个位点／2773变异 | 1068个位点／3224变异 |
| 当前目录变异／未获图中关系 | 4096／1323 | 4845／1621 |
| PeSTo当前精确映射输入 | 1个F1，1–1210，1210个residue | 1个F1，1–1159，1159个residue |
| SPPIDER-seq可选partner上下文 | 2658 | 18 |

### 功能位点与区段不可互换

P00533 已有功能记录为 ATP binding 718–726、745、790–791、855，Active site 837（Proton acceptor），Site 1016（Important for interaction with PIK3C2B）。这些原区间/位点可直接显示，不把范围缩成一个无说明的单点。

Q12809 没有 API `function` 类的独立 Binding site/Active site/Site；界面应明确无此类注释，不能为增加密度补造。其已有 UniProt **Motif 624–629（Selectivity filter）**及 **Region 742–842（cNMP-binding domain）**目前落在 domain/region 轨道；开放 region/motif 默认显示即可呈现。可将原 Motif 作为明确命名的功能 motif 展示，但不改称原来源 Binding site 或 Active site。类似地，P00533 Region 688–704 有二聚化/磷酸化/活化的原说明，仍保留 Region 身份与原范围。

两个对象 `unlocated_features` 均为空，当前不是坐标不明导致这些 domain/function 未绘出。Secondary 只显示原 Helix/Beta strand/Turn 覆盖，未注释空白不能自动补成 loop。

### PTM 计数及默认来源

核对时 PtmExplorer 与全序列网格的 PTM 默认均为 dbPTM；其他来源仍在 selector。下表分开 position/type/dataset marker、unique position 和 unique source record，不能把 marker 数当成实验数。跨来源同一位点和二硫键端点也不能简单相加成独立位点/记录。

| 来源 | P00533 marker／位置／原记录 | Q12809 marker／位置／原记录 |
| --- | --- | --- |
| dbPTM | 134／129／136 | 50／50／50 |
| UniProt | 98／98／73 | 11／11／11 |
| ProteomeScout | 167／154／167 | 55／55／55 |
| GlyGen | 27／27／156 | 4／4／4 |

全部来源 marker 数分别426、120。PTMD2已移至Disease，不在这些 Sequence marker 中。紧凑轨道可保持来源可切换，以 coverage/聚合 marker 导航，再展开原记录；不需改变底表或跨来源统一PTM证据。

### Density 与 Interface 可用边界

`/variants/summary.canonical_sites` 当前已返回全部已验证位置及六桶 `clinical_counts`，两个示例每个位点六桶之和均等于 variant_count。P00533 跨位点六桶总数为 pathogenic16／uncertain1666／benign46／conflicting178／other10／unclassified857，总2773；Q12809 为181／1306／13／170／0／1554，总3224。可直接按共享窗口分bin堆叠，不需要新增后端分类或把未验证的transcript位置投到canonical。跨位点累加单位仍为 variant–position associations，source桶不是网站新致病判定。

核对时 SequenceViewer 只保留 mapped variants 简报，未实际渲染已有 VariantDensity 组件；因此当前缺少集中density轨道属于呈现缺口，summary数据已可用。

Interface当前服务已返回上述精确映射与上下文。PeSTo 的五类连续分数不互斥，不合成统一接口标签；SPPIDER-seq必须选择partner并区分query的两个head，不平均partner或片段。集中共享坐标时可以沿用现有默认PeSTo片段与选定分数，但应保留方法/结构片段或partner上下文控件。这里仅核对接口可用性与返回数量，不代替预测科学验证或网页交互验收。

### 集成后的展示取舍（2026-09-21）

用户最新截图要求把多类信息放到同一序列层面。采用CATVariant共享横轴、短图例、按需详情的组织方式；增加本项目真实JSD与Interface连续值，保留原独立量尺。默认开放已有Pfam/UniProt region类以解决信息不可见，不重收集或补造功能位点。PTM仍默认dbPTM降低密度，其他来源通过独立selector查看；原表格移到按需弹层，避免打断纵向对照。Variant density只在Sequence保留一份，Catalog仍按后果/临床类别汇总。

界面实现位置：`frontend/src/components/SequenceViewer.tsx`组织共享窗口；`CompactAnnotationTracks.tsx`负责原边界/显示分箱/证据选择；`CompactVariantTrack.tsx`按已发布canonical sites六桶绘图。JSD和Interface原组件以compact模式接入。分类与来源字段不重新计算科学规则。原来独立卡片、每轨重复坐标和长说明改为首尾共享坐标与短标签。最新实际验收、限制见[交付记录](../../../../record/00_initial_preview/20260921_website_v2.md)。


<a id="variant-evidence-20260921"></a>
## Variant 证据面板专项复核（2026-09-21）

本轮在独立浏览器真实打开 [CATVariant KCNH2 variants table](https://catvariant.com/genes/KCNH2#variants-table)，查看主表并点击 P2L 进入其详情。不同于旧截图，本轮观察的页面同时呈现 population context、variant effect predictions、trafficking/activity、classification、prioritization；详情包含 score/evidence 条、预测器说明、clinical records 和外部数据库链接。

| 实际观察 | memVar 采用 | 不能直接照搬的部分 |
| --- | --- | --- |
| 变异短名，AF 百分比与细条、预测数字与彩色小条 | genomic 位置/替换简化，AA Position 在 Ref 前；不同输出用数值、条、标签表达 | 不能把某个工具的原值当成统一致病百分比 |
| ClinVar/EBI/UniProt 来源与 classification 分开，review 信息可见 | ClinVar 三类 assertion 独立；分类、星级、origin、conditions/IDs 分层 | 蛋白注释来源不能被当作临床审查；aggregate 星级不能继承给每条 SCV |
| Prediction 的 +more、说明折叠、分类/分数条、证据驱动总览 | 真实可用输出数、来源 call 分布、方法组覆盖、筛选后九卡分页 | 页面有自定义 weighted prioritization、PP3/BP4/percentile 与 high-impact agreement；本项目没有确认相同校准和权重，不引入 |
| 来源链接按数据库组织 | MedGen、MONDO、MeSH、HPO、RCV、SCV 使用独立组与颜色 | condition 字符串与 ID 列表无可靠逐项对应，前端不猜测配对 |

补充官方依据：

- [NCBI ClinVar review status](https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/)：practice guideline 4 星，expert panel 3 星，满足相应多提交者条件为 2 星，single submitter / conflicting classification 为 1 星，指定 no-criteria/no-classification 状态为 0 星。胚系、oncogenicity、somatic impact 分域应用其原状态；缺失保持未知。
- [NCBI ClinVar record details](https://www.ncbi.nlm.nih.gov/clinvar/docs/details/)：RCV 为 variant-condition 聚合记录，SCV 为 submission 记录。现有源字段分别列出其 accession，UI 不合并为同一类 ID。
- 评分尺度继续沿用已核对的 [dbNSFP 5.4a 字段词典](https://dist.genos.us/release/dbNSFP5.4a_variant.columns.txt) 与各工具原始说明，原 0–1 条只用于已确认字段。SIFT 低分方向在页面明确指出，source call 仅接受 API 已匹配类别。
- [ThermoMPNN 官方说明](https://github.com/Kuhlman-Lab/ThermoMPNN/blob/main/README.md)及现有 `evidence.py` convention：保留 mutant-minus-wild-type 原输出，负值预测稳定化、正值预测去稳定化。页面着色仅在 API 明确提供该 convention 时启用。

定向真实数据：EGFR L858R（GRCh38:7:55191822:T:G）有 55/61 个评分输出，17 个具有可解释的原 damaging/pathogenic call，38 个无可解释 call，6 个缺分；三类 ClinVar assertion 的星级分别 3/1/2；ThermoMPNN ΔΔG 为 -0.033615171909332275 kcal/mol。此数据用于本轮界面验证，不代表整库覆盖。

新增发现：部分 MONDO 源字符串是 `MONDO:MONDO:...`，展示链接只去掉重复命名空间而原 fields 保留；同义变异 HGVSp 含 `%3D`，应显示 `=`；AF=0 不等于未收录；61 个字段存在多个同工具输出，环图不能命名为独立工具一致率。

[现行方案](../../plan/variant_evidence_refinement.md)维护展示行为；[交付记录](../../../../record/00_initial_preview/20260921_variant_evidence_refinement.md)维护截图与实际验收。浏览器参考截图位于 `/tmp/memvar-sequence-refinement-qa/catvariant-catalog-reference.png`。

<a id="membrane-overview-20260921"></a>
## Basic Information 膜特征摘要核查（2026-09-21）

本轮将黄色 Membrane Association 的入口补为真实摘要及按需详情，网站仅投影已发布膜服务数据，不新增跨来源投票、膜类别或接触阈值。依据为当前 [membrane 规则](../../../../../../modules/membrane/docs/rules.md)、[四类膜标签](../../../../../../modules/membrane/docs/basic_membrane_labels.md)、[结构残基映射结果](../../../../../../modules/membrane/docs/site_mapping_result.md)及 PostgreSQL 小范围实查。

新增只读接口由 [membrane_overview.py](../../../../../src/api/membrane_overview.py) 实现，经 evidence router 接入：

- `GET /api/proteins/{accession}/overview/membrane/summary`：返回当前 `sequence_id/length`、已发布 `labels` 及 supporting_records、`uniprot.counts/locatable_counts/features`、`deeptmhmm2` 原预测状态和区段、`topology_sources`、`observations`。采用三段路径避免现有 `/overview/{section}` 路由匹配冲突。
- `GET /api/proteins/{accession}/overview/membrane/details?source=OPM|MPLID|BioDolphin&limit=20&offset=0`：返回 `items/total/has_more`；统一 canonical position/residue、PDB/链、原位置和 mapping 状态，各来源科学字段在 `fields` 中按需展开，原布尔值和零保留。来源白名单、绑定参数、单页至多 100 条。

主摘要的三个数字分别计数 canonical UniProt Transmembrane、Intramembrane、Topological domain **原 feature 记录**。视图通过 `mapped_sequence_id=protein.default_sequence_id` 限定对象，仍保留源 `sequence_scope` 和 mapping status；不精确边界计入原注释数，只有 `can_locate_exactly=true` 且两端存在时可绘坐标。`locatable_counts` 单独表明可绘数。没有注释不等于生物学不存在。

| 当前 canonical 对象 | UniProt TM / Intramembrane / Topological domain | DeepTMHMM2 原类型与 TMhelix 数 | OPM mapped 行 / 不重复位置 / PDB |
| --- | --- | --- | --- |
| P00533，1210 aa | 1 / 0 / 2；TM 646–668 | Alpha TM + SP；1（644–668）；另 signal 1–24 | 425 / 86 / 6 |
| Q12809，1159 aa | 6 / 1 / 8；膜内段 612–632 | Alpha TM；6；另 reentrant 615–627 | 1726 / 566 / 5 |

两例的 UniProt 膜 feature 均可精确定位；DeepTMHMM2 均为 `status=ok / mapping_status=input_sequence_exact`，分别保留 4 / 15 个原区段，其膜类型和 selection_method 为已发布预测原值。两者正式膜标签均为 integral_membrane。MPLID、BioDolphin 在这两条 canonical 的 mapped 范围均为 0，界面说明仅无该范围本地记录，不作阴性解释。

`topology_sources` 按 dataset、role、method 分组，返回 distinct record_id、distinct feature_id、映射区块数和原 mapping_statuses；两例各 30 组，包含来源约束、分方法预测、整合拓扑及实验/结构来源。不同角色或重复数据包不合为独立证据总数，不将其 feature 数称跨膜次数。

结构详情的粒度继续分别维护：OPM 是结构/模型/链残基几何观察，距离字段为 Å、heavy_atom_fraction 为 0–1；signed depth 正负是来源膜核心内外，不能表述为胞内/胞外侧。MPLID 保留接触及非接触行，min_distance 为来源候选配体集合距离 Å，不补造具体脂质伙伴。BioDolphin 保留配体身份及 PDB/Re-numbered 两套编号，行数不当独立结合事件或全部膜脂接触。

实际验证只使用当前环境 TestClient 和现有只读 PG：两 summary、OPM 前两页、两例 MPLID/BioDolphin 空页、非法来源 422、未知蛋白 404 均通过；OPM 相邻页 ID 无重叠。首次两摘要分别约 0.077 / 0.018 秒、11.5 / 21.9 KB（本次调用，非性能承诺）。额外按已知 P08183 验证 MPLID 4674 行和 BioDolphin 526 行的非空详情分支，原 false/0、距离单位及配体身份正常。三张结构观测表的定向 EXPLAIN 均使用已有 `(sequence_id,target_position) WHERE mapping_status='mapped'` 部分索引；不新增索引，不扫描全库。摘要缓存至多 96 个蛋白的小响应。未重启服务或改动 Sequence/Structure/API 科学数据。


<a id="information-colors-20260921"></a>
## 中性背景与信息着色复核（2026-09-21）

依据用户最新反馈重新查看[CATVariant KCNH2概览](https://catvariant.com/genes/KCNH2#overview)与[疾病页及展开](https://catvariant.com/genes/KCNH2#disease)。Web抓取超时，现有Playwright浏览器可正常访问并实际展开Romano-Ward syndrome；不是依据截图猜测所有交互。参考截图42–44保存在`/tmp/memvar-v2-qa/`。

观察：概览卡实际白底（rgb255/255/255）、深灰标题（rgb31/41/55）、轻边框和阴影；圆形图标、主数字和细条使用饱和色。疾病默认白卡，展开内容使用浅灰层次；Condition/Phenotype、来源支持和数量是小标签，外链蓝色。其Support和优先级计算不属于本项目已确认规则，仅借鉴信息组织。

本地发现：Basic卡在overview-v2.css与styles.css重复指定淡绿/黄/紫底，新增DeepTMHMM2预览又嵌套紫底，导致大面积底色抢占信息层级。清除重复全局覆写，由组件统一控制白色表面；保留原色系在图标、计数、GO柱条和小标签。DeepTMHMM2依然默认可见，紫色名称/预测标签/数值提供重要来源标识。

Expression/QTL/Disease按同一方法审查：表格浅灰交替行、蓝色悬停/选择、深色正文；类型/来源小标签与原始测量分别突出。统计计数和p值不着成临床致病判断；无来源临床分类的疾病或HPO表型不以红色制造风险暗示。真实零、缺失、原来源分类及预测/观测区分保持原契约。


## 滚动与直接跳页技术审查（2026-09-21）

Regulatory tissue图的停留源于`cx-human-panel`的`position:sticky;top:95px`，其容器边界限制正对应用户观察；改为static即可，未改SVG图层。PPI默认无dataset时后端本来就查full collections，问题是展示先列mutation及显式URL保留过去选择，因此只调整入口/下拉优先级，不覆盖用户明确筛选。

全站记录分页原有两类：offset与本地slice可直接跳页；variant/context/disease基于cursor历史，无法仅用已缓存cursor完成未访问页跳转。选用兼容offset参数，保留稳定来源排序和cursor（存在cursor时优先），不在前端循环抓取所有前页。QTL跨dataset使用现有gene/context计数定位；Expression只对直接跳页涉及的当前gene/context做数据集计数；其他列表直接SQL OFFSET。未知总量不冒充总页数，允许空页返回；现有有上限offset的注释接口使用独立maxPage输入验证，不显示为真实总页数。

已知限制：大offset可能比顺序cursor访问更慢，本轮未新增COUNT全表或改索引；只验证真实代表查询，不宣称全库任意页并发性能。现有正式数据和关联契约不变。
