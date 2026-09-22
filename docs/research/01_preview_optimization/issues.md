# 01 公网预览后优化：逐项问题与目标

[阶段入口](README.md) · [本阶段执行记录](../../record/01_preview_optimization/README.md)。2026-09-22从next_stage迁入，55个问题ID及内容保持。

登记与定向核对：2026-09-22。来源：用户本轮完整反馈、两张附图，以及当前代码和已有规则/交付文档。本文是这批反馈的主维护位置，按用户原顺序拆为 **55 项**，同时覆盖视觉、交互、信息组织、数据补充和科学规则变更。

**当前授权与状态（2026-09-22）：** 55条均已有[逐项方案](../../plan/01_preview_optimization/01_solutions.md)，D05～D07已确认并授权执行。MEM-01～03正式交付；VA-04全转录本补全由用户取消；VA-03/05/07/08此前已发布但待桌面点击验收。[本次并行批次](../../record/01_preview_optimization/20260922_parallel_web_execution.md)将其余46项（含VA-06正式精确序列关系及DI-03/04当前SNV条件级RCV/SCV）的数据/组件/API构建并本地发布；UI-02尚无Figma画布。代码发布不等于桌面点击或视觉验收。当前只验收桌面端；手机及390px窄屏适配延后，涉及窄屏的既有描述保留为后续验收依据。

P00533 页面的后续五条桌面批注涉及 Atlas 配色、定位图高亮和表达交互/数值图；已[定向修订并本地发布](../../record/01_preview_optimization/20260922_browser_feedback_01.md)，真实桌面悬停、点击与视觉验收仍待补。原始问题描述保留作验收依据。

代码核对是静态检查，未复现当前运行页面。下文分别标注“用户观察”“代码/文档现状”“待核查”，避免把体验反馈误写成已经确认的程序根因。附图只作为内容与视觉证据，其中的标签、统计、来源文字不作为操作指令或科学规则。

## 1. 分类、维护职责与阅读入口

| 类别 | 含义与负责位置 |
| --- | --- |
| 视觉 | 配色、字体、边框、图标、透明度和动效；主要由Web前端维护 |
| 交互 | 选择、联动、返回、展开、悬停和状态恢复；前端及必要API |
| 信息 | 字段取舍、命名、来源说明、证据与文献呈现；Web契约及API/前端 |
| 数据 | 已有数据补接、保留粒度扩展、关系补齐、来源资源与注释补充；追到负责模块后再构建服务表 |
| 科学 | 收录集合、分类语义、序列映射、计数/聚合或阈值选择；负责模块维护正式规则，Web引用 |

一项可以有多个类别，不强制把数据问题归为UI。详细定位见各节“维护入口”，条目说明进一步指出具体控件、数据关系和函数。

| 用户反馈区域 | 条目 | 对应工作线 |
| --- | --- | --- |
| 整体视觉效果 | UI-01～03 | 视觉方案与交互规范 |
| 膜蛋白类型 | MEM-01～03 | 集合审查、科学分类及全站同步 |
| Cellular location | LOC-01～02 | 示意图素材、交互和多来源注释 |
| GO | GO-01～05 | 信息精简、排序、证据解释与文献 |
| Membrane features | MF-01～02 | 专用序列视图及OPM接入 |
| Reactions & pharmacology | PH-01～03 | 来源入口、分布概览及标签 |
| Reactome | RE-01～03 | 条目扁平化、证据及外链 |
| Sequence browser | SQ-01～02 | 来源勾选与解释 |
| Full sequence atlas | AT-01～07 | 计数色阶、PTM标记、统计与入口 |
| Protein structure | ST-01～04 | 统一模式/配色、渲染与选区 |
| Variant browser | VA-01～11 | 返回联动、代表转录本ID、isoform关系及评分解释（全转录本补全已取消） |
| Expression | EX-01～04 | 测量类型筛选与矩阵展示 |
| PPI | PP-01～02 | 来源→主题→有效分类的级联选择 |
| Disease | DI-01～04 | 标签精简、证据分色及ClinVar专区 |

## 2. 视觉效果

维护入口：[全局样式](../../../frontend/src/styles.css)、[共享UI组件](../../../frontend/src/components/ui.tsx)、[首页样式](../../../frontend/src/components/homepage.css)、[既有架构与设计参考](../../archive/00_initial_preview/plan/site_construction/reference_lessons.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| UI-01 / 视觉、交互 | 当前文字、配色、边框及交互有较强“AI感”，希望整体更有质感；考虑更好的模板或动效。 | 按03方案采用shadcn/ui、Motion与Radix配色，保留既有页面顺序。本轮追加CATVariant真实EGFR字体/色表对照、鲜明数量色/PTM圆点、结构选择器、功能纵排、SwissBioPics细胞图和Expression类别色；已构建、本地8000发布及限定桌面交互验证。用户观感验收继续，不能据此关闭55项或全部文字审查；逐批修改、素材许可、剩余分支和3D性能限制见[最新UI记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#catvariant对照与五条局部重设计)。 |
| UI-02 / 视觉、方案研究 | 希望推荐模板网站，由用户提供/挑选选项。 | 后续提供可浏览的模板/设计参考网站和少量适合科研数据密集页面的候选；用户选定方向后做真实数据局部样稿。用户已选Figma与React Bits方向，见[视觉方案](../../plan/01_preview_optimization/02_figma_motion.md)；未安装模板或生成Figma画布。 |
| UI-03 / 视觉 | 重新审视透明度、配色方案和字体选择。 | 比较字体层级、字重、背景/边框透明度、强调色与图表色；用普通/hover/selected/disabled等状态核对可读性。输出一套可复用设计取值，后续各图表和标签遵循；不能仅凭颜色区分重要状态。 |

## 3. 膜蛋白类型划分

维护入口：[现行四类标签规则](../../../../modules/membrane/docs/basic_membrane_labels.md)、[负责脚本](../../../../modules/membrane/scripts/build_basic_labels.py)、[foundation计划](../../../../modules/foundation/docs/plan.md)、[来源配置](../../../../config/sources.yaml)。下游包括[膜概况](../../../frontend/src/components/MembraneOverview.tsx)、[首页](../../../frontend/src/components/HomePage.tsx)、[检索](../../../frontend/src/components/ProteinSearch.tsx)及[全库统计构建](../../../src/database/build_catalog_statistics.py)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| MEM-01 / 信息、科学 | 解释目前膜蛋白类型划分依据。 | **已完成。** 主分类表保留规则版本、primary evidence label、全部证据标签和canonical TM feature数；蛋白概览仍可进入原证据记录。[交付与验证](../../record/01_preview_optimization/20260922_membrane_classification_v1.md)。 |
| MEM-02 / 科学、数据 | 用户已明确决定采用下述膜蛋白分类树：整合膜内分跨膜与脂锚定，跨膜再分单次/多次，外周排除整合。 | **已完成。** 采用canonical TM feature、适用明确脂锚topology/GPI feature，TM优先，外周排除整合，机制未注释单列；原重叠证据另表保留。[正式规则](../../../../modules/membrane/docs/basic_membrane_labels.md)。 |
| MEM-03 / 数据、科学、统计 | 按本地UniProt2026_03正式范围实际统计，保留用户分类结构。 | **已完成。** 正式范围7,715；整合5,654（TM5,213、非TM脂锚441）、外周1,015、机制未注释1,046；TM单次2,380、多次2,833。API、首页、筛选、总览和PostgreSQL使用同一主分类表。[交付](../../record/01_preview_optimization/20260922_membrane_classification_v1.md)。 |

以下保留最初的分类示例。**用户已于2026-09-22澄清数字只作方法说明，类型不变，实际以本地2026_03及现有范围统计；当前方法/试算以D01/D02为准。**

```text
膜蛋白 7,741（KW-0472）
├─ 整合膜蛋白 5,711
│  ├─ 跨膜蛋白 5,231（ft_transmem）
│  │  ├─ 单次 2,391
│  │  └─ 多次 2,840
│  └─ 脂锚定蛋白 480（topology ∪ 脂修饰关键词）
├─ 外周膜蛋白 1,014（SL-9903，排除整合后）
└─ 膜相关、机制未注释 1,016（membrane associate）
   └─ 单列，或按“策略2”并入外周
```

算术上2,391+2,840=5,231，5,231+480=5,711，5,711+1,014+1,016=7,741；算术相容不证明来源集合已经互斥或完整。用户随后授权方法制定，当前已选择机制未注释单列，不采用策略2；本轮不改变蛋白范围。后续发布同步服务表、检索、首页、分类统计和说明。

## 4. Cellular location

维护入口：[OverviewLocations](../../../frontend/src/components/OverviewLocations.tsx)、[概况API](../../../src/api/core.py)、[定位研究](../../archive/00_initial_preview/research/protein_overview/cellular_location.md)、[现行概况方案](../../archive/00_initial_preview/plan/protein_overview.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| LOC-01 / 视觉、交互、素材 | 现有亚定位不直观；在排版不变的条件下加入参考UniProt的cell亚定位互动示意图，需要细胞素材。 | 现行组件以位置标签与展开为主。目标是在既有面板内高亮该蛋白的定位区域，鼠标点击区域展开详细注释，交互参照下方人体组织图；后续比较适合的可交互SVG/素材及区室覆盖。保留现有排版是明确约束。 |
| LOC-02 / 信息、交互、数据映射 | 同一细胞图能容纳多个source的定位注释，上方选择器保持不变。 | 保留来源/对象scope选择器和来源追溯；明确每个来源原术语如何映到图中区域。同区域可展开多个来源，不能因为共用图就合并为跨来源共同结论；HPA基因定位与UniProt蛋白/isoform对象范围仍可辨。无法归图的注释要有可访问入口。 |

用户参考：[UniProt Q01279 subcellular location](https://www.uniprot.org/uniprotkb/Q01279/entry#subcellular_location)。本轮打开该链接仅返回JavaScript回退页面，未实际核验其交互；后续设计时需浏览器查看，不能把上述目标描述当作已验证的UniProt实现细节。

## 5. GO

维护入口：[OverviewOntology / GoAspect](../../../frontend/src/components/OverviewOntology.tsx)、[Overview / GO列表与详情](../../../frontend/src/components/Overview.tsx)、[GO汇总API](../../../src/api/overview_summary.py)、[GO slim正式规则](../../../../modules/Function/docs/go_slim.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| GO-01 / 信息 | 不需要展示source annotation和original terms两套数量。 | 当前GoAspect确实显示两套总数和相关文字。精简概览冗余数量；GO slim排序所用内部计数仍可保留。需区分“去掉冗余总数字”和“删除分类本身”，不因此删除原始注释。 |
| GO-02 / 信息 | evidence code需要解释含义。 | 当前列表/详情直接显示代码。提供代码全称、简短说明及可查依据，放在标签悬停/帮助等可发现位置；不能只给不透明的缩写。 |
| GO-03 / 视觉、信息 | overview的GO slim按数量从多到少排序，并使用合适渐变。 | 当前API按namespace/name排序，前端沿用返回顺序。明确采用现有哪一种分类计数排序，建议沿用条形当前annotation_count并清楚说明口径，数量不是功能活性；分类降序与同值稳定排序、渐变图例一起核对。 |
| GO-04 / 视觉、信息 | 展开后不同evidence code使用不同颜色标签。 | GO原注释列表与详情同时处理；统一代码→名称→颜色，保留文字解释。证据类型颜色不自行转换成高/低可信度结论。 |
| GO-05 / 信息、数据补接 | **补充缺失的文献链接。** | 当前GO详情把reference作为普通Fields值，仅另链GO term definition。追查原reference/多引用字段，PMID等能解析的编号连到原文献，其他引用按其类型保留；不是只链接GO词条。验收包括多引用、非PMID及来源无文献三种情况。 |

## 6. Membrane features

维护入口：[MembraneOverview](../../../frontend/src/components/MembraneOverview.tsx)、[MembraneTopology](../../../frontend/src/components/MembraneTopology.tsx)、[膜概况API](../../../src/api/membrane_overview.py)、[膜mapping结果](../../../../modules/membrane/docs/site_mapping_result.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| MF-01 / 交互、信息 | 当前占用大小合适；点击展开后单独弹出sequence viewer，专门展示膜注释。 | 保持主卡大小，不把完整viewer塞入首屏；现有弹层已有overview/features/topology/evidence，另有跳到全局sequence的链接。目标是在膜弹层内提供独立可缩放/点选的序列视图，查看膜区段及证据，而不是只跳走。 |
| MF-02 / 数据补接、交互 | 希望这部分加入OPM。 | OPM已存在于膜观测表和详情API，不能登记为全新未收集库。下一步核查哪些已映射OPM位置/结构链可以进入MF-01的viewer，保留PDB/链/方法和坐标语义；原坐标未映射者单独给入口，不强行绘到canonical。区分已有数据接入与确有缺口需补充。 |

## 7. Reactions & pharmacology

维护入口：[Overview / 反应药理入口及列表](../../../frontend/src/components/Overview.tsx)、[概况API](../../../src/api/core.py)、[Rhea/GtoPdb服务契约](../../archive/00_initial_preview/plan/function_pathway_tables.md)、[Function结果](../../../../modules/Function/docs/result.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| PH-01 / 视觉、交互、信息 | Rhea · GtoPdb现在太小，需要突出来源，直接以两个标签为入口，点击展开。 | 把来源名称做成清楚、可点击的两个入口；各自展开对应内容。GtoPdb可同时显示Guide to Pharmacology全称，避免只有泛称“Reactions & pharmacology”而来源不显眼。 |
| PH-02 / 信息、统计 | Pharmacological context展开先看数据情况，如TYPE与action分布、inhibition各有多少。 | 当前有type/action/affinity条目，需增加当前蛋白的药理概览API或查询。明确统计的是记录、独立配体还是其他对象，保留type和action各自含义；点击概览后可查支撑记录。精确分组/去重口径需核查字段再决定。 |
| PH-03 / 视觉、信息 | 不同inhibitor或不同action可用不同颜色。 | 两种着色方向均保留为候选，后续比较按配体类别还是action更易阅读；不要把每个抑制剂都强制分配独立颜色。颜色必须有说明，并与PH-02分布和列表一致。 |

## 8. Reactome Pathway

维护入口：[OverviewOntology / PathwayCatalog](../../../frontend/src/components/OverviewOntology.tsx)、[通路API](../../../src/api/overview_summary.py)、[当前概况方案](../../archive/00_initial_preview/plan/protein_overview.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| RE-01 / 信息、视觉 | 首次展开后的条目应有更多有效信息；evidence code直接列在条目旁并用颜色标签，不再二次点击才能看到。 | 当前PathwayCatalog把evidence_code放在每项Disclosure内部。把证据及可理解说明前置到列表行；用颜色+文字，并核查Reactome自身代码含义，不直接套用其他来源的语义。 |
| RE-02 / 信息精简 | 避免source_pathway_association等下划线内部词；不需要Association status exact_entry及Relationship source_pathway_association。 | 当前条目详情确实展示relationship/mapping_status。移除这些无助阅读的可见字段，必要内部字段仍保留用于查询与溯源；其余用户可见命名用自然语言。 |
| RE-03 / 交互 | 上述简单记录无需再展开，直接提供箭头链接到source record。 | 简单路径条目变为名称/ID/证据标签/来源箭头，减少层级；保留原来源链接及已有official diagram入口的合理位置。目标是一次展开即可读核心信息并跳到来源。 |

## 9. Sequence browser

维护入口：[SequenceViewer / track settings](../../../frontend/src/components/SequenceViewer.tsx)、[紧凑注释轨道](../../../frontend/src/components/CompactAnnotationTracks.tsx)、[sequence API](../../../src/api/sequence.py)、[topology API](../../../src/api/membrane_topology.py)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| SQ-01 / 交互 | Domain、PTM、Topology不用下拉选择项，改成勾选更方便。 | 三者当前均为select；不要与已有“显示/隐藏轨道”checkbox混淆。改为可见的来源勾选控件，核查多来源并行显示所需API；尤其topology目前单一来源加载，不能只换控件外观。并列来源保持各自注释，不静默投票合并。 |
| SQ-02 / 信息 | 为每个数据库来源加解释。 | 来源勾选旁提供简短用途、注释/预测性质及详情链接，使读者知道可选来源。涵盖Domain、PTM、Topology，不只补PTM；解释与数据说明共用维护位置。 |

## 10. Full sequence atlas

维护入口：[FullSequenceAtlas](../../../frontend/src/components/FullSequenceAtlas.tsx)、[共享featureStyle/variantFill](../../../frontend/src/components/sequence-model.ts)、[atlas样式](../../../frontend/src/components/full-sequence-atlas.css)、[位点详情](../../../frontend/src/components/ResidueEvidence.tsx)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| AT-01 / 视觉、统计展示 | 当前2–3绿色、4–7蓝色，而大部分集中4–7，颜色不能细分变异数。参考CATVariant采用更细间隔。 | 当前代码色档是0/1/2–3/4–7/8–15/16+。保留用户提供的候选分界见下方；后续查看实际位点计数分布，再确定互斥、完整的分档和图例，包括>8尾部。这里只改变计数可视化，不能改变variant定义或canonical映射范围。 |
| AT-02 / 视觉 | PTM颜色在绿色残基背景上难分辨，难看出哪些位点有PTM。 | 同时检查残基背景、PTM点、边框/形状和选中态的对比；即使不辨PTM类型，也应立即看出“有PTM”。不能只换某一PTM色而保留与背景混淆。 |
| AT-03 / 交互、视觉 | 鼠标移到残基时希望有放大或动感；PTM小点同样需要反馈。 | 分别设计hover、focus与selected状态，轻量放大/描边/提示可作为候选；点击目标与注释能对应，避免缩放遮挡相邻残基。保留“放大或动感”是方案选择，不固定某一种动画。 |
| AT-04 / 信息、视觉 | 一般模式无需用多种颜色区分所有PTM类型；让读者知道是PTM即可，减少一长排图注。 | 默认叠加层采用简洁PTM标记/图例；用户列出的13类完整保留在数据、统计与专用类型模式，不把图例精简等同删类型。 |
| AT-05 / 交互、统计 | 点击PTM图注作为入口，展示当前蛋白有多少PTM、各类型多少。 | 增加可发现的统计入口并能查看支撑位点/记录；先明确独立位置、位置×类型、来源记录三者区别和当前来源筛选范围，避免重复来源导致“PTM总数”含混。 |
| AT-06 / 交互 | 在PTM type模式中保留点击PTM类型进行选择的方式。 | AT-04只精简默认图注；专用PTM type模式仍保留类型筛选、颜色与选择反馈，不全局删去分类图例。 |
| AT-07 / 信息、交互 | PTM source也要作为入口，说明有哪些source可选。 | 显式展示可用来源及简介/覆盖，允许进入选择；不能依赖读者偶然发现下拉菜单。与SQ-02复用来源说明，同时保持atlas自身入口可发现。 |

用户给出的CATVariant计数图例参考，**尚未当作已确认的互斥分箱规则**：`No variants`、`1 variant`、`≤ 4 variants`、`≤ 5 variants`、`≤ 6 variants`、`≤ 8 variants`。若采用上界表达，需解释对应区间，并补齐超过8的情况；本轮没有独立核验CATVariant当前页面。

用户列出的PTM类型全部登记：Phosphorylation、Disulfide bond、Ubiquitination、Glycosylation、Other PTM、Acetylation、Cross-link、Oxidation、Nitrosylation、Methylation、Lipidation、Dephosphorylation、Sumoylation。减少默认图注不表示统一这些类型的来源科学定义。

## 11. Protein structure

维护入口：[StructureViewer](../../../frontend/src/components/StructureViewer.tsx)、[SequenceViewer](../../../frontend/src/components/SequenceViewer.tsx)、[共享颜色定义](../../../frontend/src/components/sequence-model.ts)、[结构API](../../../src/api/structures.py)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| ST-01 / 信息、视觉、联动 | 结构的模式与配色应和上方sequence view一致。 | 当前部分共享variantFill/featureStyle，但domain独立色板、膜只取UniProt、PTM只取dbPTM，模式状态独立。逐模式核对名称、来源选择、色阶、图例和缺失显示；统一语义，讨论切换是否自动同步，不只做到两边都有同名按钮。 |
| ST-02 / 展示缺口核查 | 用户反馈结构缺少JSD。 | 代码已有jsd lens，界面名称为Conservation，读取conservation并着色。登记为“用户未看到/未生效，需复现”，而不是断言从未实现。后续核对运行版本、入口命名、数据加载、颜色及图例，确保明确可选JSD并与上方一致。 |
| ST-03 / 交互、渲染、潜在数据补充 | Ribbon没问题；另一种style需调整，希望简单选择surface、口袋等基础表达，不要复杂控件。 | 当前已有Ribbon与Smooth surface · legacy两个选项，需要验证surface实际效果再优化。口袋为待评估功能：表面渲染不等于已知/预测口袋；先核对是否有口袋数据或仅需视觉表面凹陷，新增检测方法需独立研究，不生成虚构口袋注释。 |
| ST-04 / 交互、坐标映射 | 无法在结构区域直接选想要的残基/区段；增加简单sequence选择，可单选或拖选范围。 | 当前组件仅接收selectedPosition，内置sequencePanel关闭，主要由上方序列单点驱动。增加结构区本地序列选择/拖选及清除，核查与上方选中态的双向同步；仅按已验证残基映射高亮，片段之外和未映射位置有明确反馈。 |

## 12. Variant browser

维护入口：[VariantCatalog](../../../frontend/src/components/VariantCatalog.tsx)、[VariantEvidencePanels](../../../frontend/src/components/VariantEvidencePanels.tsx)、[VariantDistribution](../../../frontend/src/components/VariantDistribution.tsx)、[SequenceViewer](../../../frontend/src/components/SequenceViewer.tsx)、[工具说明字典](../../../frontend/src/components/predictor-guides.ts)、[PredictionToolkit](../../../frontend/src/components/PredictionToolkit.tsx)、[证据API](../../../src/api/evidence.py)、[转录本状态/条件](../../../src/api/variant_support.py)、[服务构建](../../../src/build/build_variant.py)、[上游variant规则](../../../../modules/variant/docs/rules.md)、[foundation计划](../../../../modules/foundation/docs/plan.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| VA-01 / 交互 | Variant consequences overview点进去后，如何回退？ | 核查后果分类→筛选列表/详情的实际导航，不预设一定发生路由跳转。提供显式返回/恢复概览入口，返回后保留合理原状态；浏览器返回与局部返回均需可理解。 |
| VA-02 / 联动、交互 | 上方sequence选区延续到下方variant是好的，但如何取消/回退？希望有指引或悬浮辅助面板。 | URL存在variants_canonical_start/end等范围条件，需展示筛选来自哪个区段，提供单项清除、退出联动范围、必要的全部重置。提示条/悬浮面板为候选；取消区段筛选不应无说明地清掉用户其他筛选，区分“返回”与“重置”。 |
| VA-03 / 科学说明、现状核查 | 用户认为目前优先Ensembl canonical，询问其他转录本如何处理。 | **代码/本地发布已完成，桌面交互验收待补。** [本批记录](../../record/01_preview_optimization/20260922_variant_identity_ui.md)。 已确认文档实际是MANE Select优先、基因无MANE才用Ensembl canonical；canonical标记筛选又不等于代表选择或UniProt序列匹配。需对照代表样本、API与页面解释真实选取规则，解决当前误读；本次没有要求一律改成Ensembl canonical优先。 |
| VA-04 / 数据扩展、信息 | 原诉求：其他转录本可展开查看所有注释基础结果。**2026-09-22用户取消此补全目标。** | 保留原问题供追溯；不重建已清理的全VEP衍生表、不新增全转录本切换，继续当前代表后果范围。具体决定见[D03](01_data_decisions.md)；取消不等于实现。VA-05的ID展示和VA-06的序列匹配继续开展。 |
| VA-05 / 信息、数据补接 | selected consequence中缺转录本ID；每个转录本基本信息必须能看到。 | **代码/本地发布已完成，桌面交互验收待补。** [本批记录](../../record/01_preview_optimization/20260922_variant_identity_ui.md)。 当前Overview的Selected consequences表未显式列ID；单独TranscriptEvidence已使用transcript_id与Ensembl链接。需定位入口与字段传递差异，在核心后果结果直接显示ENST及已有ENSP、版本、MANE/canonical标志、后果/HGVS等必要信息，其他转录本按需展开。不是只在很深的详情保留ID。 |
| VA-06 / 数据、科学关联、信息 | 比起泛化Association context matched，更重要的是到底匹配哪个UniProt accession/isoform；有mapping标出来，没有则not match。 | **正式关系、PostgreSQL、API及前端已发布，桌面验收待补。** [本批记录](../../record/01_preview_optimization/20260922_parallel_web_execution.md)。以全长氨基酸精确相等证明序列匹配，gene关联只限定候选；多目标全部保留，精确未匹配/输入缺失分别显示。序列相等不自动证明该变异位点映射。 |
| VA-07 / 信息结构 | 变异详情精简：ClinVar和COSMIC归入Clinical。 | **代码/本地发布已完成，桌面交互验收待补。** [本批记录](../../record/01_preview_optimization/20260922_variant_identity_ui.md)。 当前DetailTab分别为ClinVar、COSMIC。改为Clinical一级入口，下分来源并保留各自意义；COSMIC记录不能自动解释为ClinVar致病断言。 |
| VA-08 / 命名 | Population改成Frequency。 | **代码/本地发布已完成，桌面交互验收待补。** [本批记录](../../record/01_preview_optimization/20260922_variant_identity_ui.md)。 当前gnomAD页签label为Population。改用户可见名称，保留频率来源、群体/亚群体信息和真实零/缺失区分，不删除群体维度。 |
| VA-09 / 信息精简 | Prediction最重要；展开后不要source status、prediction、matching、field等机械字段占主内容。 | PredictionDashboard当前卡片和详情仍有字段/状态等实现性描述。删除重复标题和面向内部的字段名，评分及解释优先；必要的“无可用分数/未匹配”可以简明状态或分组呈现，与VA-11一致，不隐瞒缺失或伪造匹配。 |
| VA-10 / 信息、工具依据 | 每个工具要有简要介绍、评判标准、范围（是否0–1）和方向（高/低意味着什么），最好能看评分条。 | predictor-guides已存meaning/scale/direction/criterion及来源，PredictionToolkit已有使用，但不等于变异详情已充分呈现。逐工具核查并复用说明；有依据才画范围/阈值，原始分数、rankscore等不同尺度分开，不能所有值都归一成“越大越致病”。 |
| VA-11 / 交互、信息组织 | 预测结果按工具类别或是否match组织，直接比较，不要逐页翻卡片。 | 当前PredictionDashboard按每页9项slice分页。提供分组总览、组内可展开/比较的评分条或紧凑矩阵，保留可用性信息；按工具类别/匹配状态的具体组合待方案比较。验收必须能快速比较本变异的所有可用预测，而不靠连续翻页。 |

**本节关键区分：** “页面看不到转录本ID”与“数据只保留代表后果”是两项问题；“选中Ensembl canonical”与“匹配UniProt canonical/isoform”不是同一关联。VA-03解释当前规则；VA-04全转录本补全已由用户取消；VA-05/06继续明确代表对象及其编码蛋白与UniProt的匹配，不改变代表注释主体。

## 13. Expression

维护入口：[ContextPanels / Expression及context列表](../../../frontend/src/components/ContextPanels.tsx)、[ContextDisplay / assay分类](../../../frontend/src/components/ContextDisplay.tsx)、[表达明细API](../../../src/api/evidence_context.py)、[表达汇总API](../../../src/api/evidence_summaries.py)、[表达展示方案](../../archive/00_initial_preview/plan/expression.md)、[expression模块结果](../../../../modules/expression/docs/result.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| EX-01 / 信息精简 | HPA tissue RNA等面板文字和上方标题重复。 | 逐层核对来源卡、dataset标题、context标题与记录详情；各层只保留必要的来源/测量/组织上下文，避免重复抄同一名称。用户例子保留为HPA tissue RNA，附图另是Cancer sample RNA。 |
| EX-02 / 交互、信息 | 不仅按来源选择，还要按数据类型选择，如RNA-seq、MS。 | 当前已有ASSAYS/DATASET_ASSAYS与What was measured?概览，但介绍卡不等于可用筛选。增加测量类型筛选并和source联动，覆盖现有RNA-seq、单细胞、MS、染色等实际类别；空组合不能混入其他测量。 |
| EX-03 / 可视化、交互、API/数据 | HPA cancer sample RNA按表格/条目逐页看不合理；用颜色表达数值的热图，悬停展开详细值，避免翻600多页。 | 附图明确为8,384 contexts/records、每页12个卡片、共699页。问题实质是大量样本列表缺少整体数值分布，不拘泥“表格”或“卡片”叫法。研究组织/癌种与样本矩阵或紧凑热图，hover显示样本/原值/单位，点击可追溯；需要全范围数据或明确汇总API，不能拿当前12条作全量热图。 |
| EX-04 / 可视化、科学聚合 | 其他表达数据也应按组织等做热图矩阵，直观看出数量差异。 | 扩展到适合的组织/细胞/样本数据，不只修HPA cancer。明确每个矩阵的轴、测量量、单位、样本量与缺失；区分表达数值大小和记录数量，RNA与MS不直接共用可比较色标。若需均值/中位数、变换或跨来源合并，先核对科学口径，保留原值与来源。 |

用户截图证据：[Expression context反馈](assets/expression_context_feedback.png)。其中可见`Cancer sample RNA · pTPM`、`RNA · Bulk RNA-seq`及Glioblastoma Multiforme (validation)样本AK002等；不能由截图推断其余所有dataset都有8,384条。

## 14. PPI

维护入口：[ContextPanels / PPI筛选](../../../frontend/src/components/ContextPanels.tsx)、[PpiOverview](../../../frontend/src/components/PpiOverview.tsx)、[PPI/context API](../../../src/api/evidence_context.py)、[汇总API](../../../src/api/evidence_summaries.py)、[PPI模块计划](../../../../modules/PPI/docs/plan.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| PP-01 / 交互、信息架构 | collection不应把所有组合列一起；先选source，再选主题。 | 当前Collection select把source和collectionLabel拼接成平铺选项，虽然PpiOverview有额外筛选入口，仍不等于目标级联流程。建立source→主题的清楚选择层级，支持返回上层，并保留当前选择可见。 |
| PP-02 / 交互、数据选项 | 选择主题后，只列该主题可用分类，如互作方式。 | 从当前来源/主题的数据生成有效interaction type/detection method等分类；明确用户“互作方式”在各库具体对应哪个字段，不把不同概念揉成一个集合。上层改变清理失效下层条件，避免所有来源×主题×类型组合平铺。 |

## 15. Disease

维护入口：[ContextPanels / Disease及详情](../../../frontend/src/components/ContextPanels.tsx)、[疾病证据API](../../../src/api/evidence_disease.py)、[疾病构建](../../../src/build/build_disease.py)、[variant证据API](../../../src/api/evidence.py)、[疾病模块计划：ClinVar后续原则](../../../../modules/disease/docs/plan.md)、[疾病结果](../../../../modules/disease/docs/result.md)。

| ID / 类别 | 用户问题与目标 | 定位、讨论与完成标准 |
| --- | --- | --- |
| DI-01 / 信息精简 | Disease的Relationship没有必要展示。 | 当前列表和DiseaseDetail仍可见relationship_status/Relationship。去除主列表与详情中无助阅读的内部关系字样；不删除底层疾病—基因—变异关系数据。 |
| DI-02 / 视觉、信息 | Source classification、evidence等不同信息标签要用颜色区分。 | 当前已存在ContextTag和classification着色，但本轮反馈说明区分仍不够。按来源、原分类、证据类型等明确视觉层级及解释；同色不暗示跨来源临床标准完全等价，不能凭颜色生成新的证据评级。 |
| DI-03 / 数据扩展、信息 | 新开ClinVar专区，把ClinVar中的disease condition逐项列举。 | **当前SNV范围正式关系、PostgreSQL、API及页面已发布，桌面验收待补。** [本批记录](../../record/01_preview_optimization/20260922_parallel_web_execution.md)。条件集合与成员原名/ID分开，RCV分类只属于整个TraitSet。 |
| DI-04 / 数据扩展、交互 | 展开某个condition后，能看到关联位点、disease ID等信息。 | **当前SNV范围正式关系、PostgreSQL、API及页面已发布，桌面验收待补。** [本批记录](../../record/01_preview_optimization/20260922_parallel_web_execution.md)。从summary来源行和精确VariationID×AlleleID关联RCV/SCV观察版本；无RCV、summary未列SCV与未验证UniProt位点均明确显示，不把VCV总体分类复制给条件成员。 |

用户参考图：[疾病/条件—变异展开样式](assets/disease_variant_reference.png)。图中有`somatic mutation`、`Reported`、计数2、variant density、G719S/L858R与`Variant Table descriptions (UniProt/EBI Proteins Variation)`来源。它说明“条目展开后关联变异与来源可见”的交互意图；截图来源不是ClinVar，不据此将somatic mutation定义为ClinVar疾病条件，也不新增密度/Reported分类的科学规则。

## 16. 下一阶段讨论与执行分组

以下工作包保留为导航，具体处理已形成[55项方案](../../plan/01_preview_optimization/01_solutions.md)；已实施/发布与尚待验收项以文首当前状态及对应record为准，不沿用最初未启动状态。

| 工作包 | 对应条目 | 先形成什么 | 完成时交付什么 |
| --- | --- | --- | --- |
| A. 集合与注释完整性 | MEM、VA-03～06、DI-03～04 | 当前/目标集合对照、代表ENST/ENSP可见性、UniProt序列关系、ClinVar条件关系方案 | 上游规则/产物、服务表/API与显示链路；无法获取部分有明确状态 |
| B. 全站视觉与组件 | UI、各节颜色/标签要求 | 少量模板候选与真实页面样稿，字体/配色/边框/动效方案 | 统一样式及桌面/窄屏代表交互；数据规则不因视觉改变 |
| C. 基础信息与来源证据 | LOC、GO、MF、PH、RE | 细胞图素材、膜viewer设计、统计与参考链接字段核查 | 多来源定位/膜注释与文献可达，精简后的概览和详情 |
| D. 序列—结构—变异操作 | SQ、AT、ST、VA-01～02及07～11 | 共享模式/色阶、选择状态、返回与取消、评分解释方案 | 可完成从选区到变异/结构再返回的闭环；所有可用预测可比较 |
| E. 表达与互作浏览 | EX、PP | 样本/组织矩阵原型、测量筛选、PPI有效级联选项 | 热图数值可追溯、避免大量分页，筛选与真实数据匹配 |
| F. 疾病现有展示精简 | DI-01～02 | 字段和标签视觉规则 | 与ClinVar新专区相容的现有疾病页面；无需等待新关系构建完成 |

MEM集合/版本与方法、D05～D07已确认；D03全转录本补全已取消，D04代表ID与UniProt序列匹配目标已确认，注释继续以代表转录本为主。本轮实现及剩余缺口按[并行批次记录](../../record/01_preview_optimization/20260922_parallel_web_execution.md)维护；各条原始反馈保留为桌面验收依据，不把整包“代码已写”当作每条验收完成。

## 17. 本轮核对范围与维护边界

- 已按原反馈顺序覆盖14个区域、55条目标；用户的分类树、色档示例、13类PTM、两张附图及UniProt参考链接均保留。
- 已静态核对关键前端组件、相关API/服务构建入口和膜分类/代表转录本/疾病关联文档；追加完成膜标签/feature必要列的有界试算，没有扫描变异大表、重新入库、重跑预测或实际浏览器全站验收。
- JSD、surface、工具说明、转录本ID、assay介绍及部分彩色标签已有代码基础，保留用户体验问题并注明待复现，不以此关闭反馈。OPM有数据基础；代表序列匹配和ClinVar专区涉及实际关系补充，全转录本补全已取消。
- 9月21日的[旧问题与实施记录](../../archive/00_initial_preview/research/website_v2/issues.md)仍记录当时验收事实；本轮要求与其不同的地方进入新一轮讨论/优化，不把旧“已验收”解释为新需求已完成。采用方案后更新对应`docs/plan/`和负责模块规则，验证后链接`docs/record/`或模块`result.md`，本文继续维护问题状态，避免多份清单重复抄写。
