# 网站第二版：信息层次与交互方案

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-21。依据用户对运行初版及七张截图提出的修改要求执行，替代[初版](website_v1.md)中顶部功能长简介、全折叠入口、局部60残基网格、固定少数预测器主列、直接列表优先的展示方式。既有科学规则和服务数据契约继续有效。不是重新逐项征求展示许可，也不重新导入数据库。

进度、问题及验收的唯一工作清单见[第二版问题记录](../research/website_v2/issues.md)；调研证据与取舍见[调研分析](../research/website_v2/analysis.md)。第三轮反馈及定位/通路精简已验收；共享坐标Sequence Browser于04:56完成构建与代表性交互验收；用户随后确认布局并追加的可读性、范围操作和Membrane Association详情优化也已于05:12完成实现与代表性验收，逐项状态见问题清单。历史及本轮实际范围与限制见[交付记录](../../../record/00_initial_preview/20260921_website_v2.md)。

## 1. 共同设计

- 直接进入蛋白身份信息；导航保持Overview、Sequence、Structure、Variants、Expression、QTL、Interactions、Diseases。
- 参考CATVariant明亮蓝色操作、紫/青/橙/粉图例、浅灰交替行与细条；Basic Information、Expression、QTL及Disease采用白色卡片、浅灰分层和细边框；颜色集中在圆形图标、关键数值、小标签与图表，不使用整块绿/黄/紫底色划分基础模块。标题用深灰，表格采用中性交替行和蓝色交互状态；标题、统计数字、标签、说明形成字号和对比度层级。实质信息同时用文字表达，颜色不作为唯一载体。
- 先显示真实统计或简短内容，后通过卡片、柱条、来源标签打开分页明细。汇总来自当前蛋白的完整筛选结果，不能使用当前分页冒充总量。
- 数据来源、适用对象、统计单位、坐标系、缺失状态必须可见。正常与癌症、RNA与蛋白、实验与预测不混为一个数值。
- 图表中的计数分段是显示尺度，不新增生物学分类阈值。临床分类保留来源原文；红/绿/橙分别提示来源致病/良性/不确定类别，冲突单列。不存在跨预测器投票或自建统一致病分。

## 2. 基础信息

身份行保留蛋白名、gene、UniProt、canonical长度与膜类别。完全移除UniProt FUNCTION长文（包括Entry Level Annotation详情），保留非FUNCTION的家族/反应/辅因子等结构化注释与官方来源入口。

独立分区：Function、Subcellular location、Membrane、功能特征/GO、Reactome通路、反应与药理。各分区默认能看到内容或明确的无数据状态；详情使用弹窗或分页展开。亚细胞定位仅按同来源、同适用对象组织和视觉去重，不生成跨来源统一定位。拓扑区段在序列中表达；依据用户后续精简指示，定位去掉复杂细胞示意，使用简洁图标/定位标签、紧凑来源与isoform/entry选择器，原证据按需展开，主面板不重复铺长文。GO的Function、Process、Component分为宽松独立区域，按现有slim关系统计完整覆盖并精确筛选原注释；Reactome缩为简短总计、少量通路预览与查看入口；完整列表及真实官方图按需打开，不根据名字虚构连线。

Membrane association白底摘要增加canonical UniProt原Transmembrane、Intramembrane与Topological domain计数，以及原膜标签和简洁区段位置示意。DeepTMHMM2作为重要来源直接进入默认预览，以独立白底来源分区、紫色名称/标签及数值给出一句简介、原蛋白类型、预测TM螺旋数和信号肽结果；有TM beta strands时补充原计数，View details直接打开预测详情。仅ok且input_sequence_exact的结果显示当前canonical预测摘要，缺失/未验证与真实零分开。点击View membrane features打开独立详情：UniProt原feature/坐标/引用、DeepTMHMM2原预测类型及区段、各结构来源的已映射观测和分页记录。Sequence跳转是次级入口。各来源不投票合成统一结论，结构观测记录/位置/PDB计数不称跨膜次数；零条已映射记录不等于生物学阴性。

## 3. 序列与结构

- 全长范围导航显示当前窗口和左右手柄：拖选新范围、手柄改变边界、键盘调整、双击复位；数值输入、Zoom/Pan与首尾坐标拖选同步。注释轨道支持鼠标、键盘预览与点击，详情读取所点feature的原始记录及证据。
- 参考CATVariant，将Variant density、Domain/Region、Membrane、Functional sites、PTM、Secondary、JSD、Interface排入一个紧凑面板，共享首尾坐标轴、窗口、缩放及纵向位置导线。完整序列网格保留在其下；Atlas来源/类型筛选独立，模式前置详情及预测覆盖方案见[Atlas细化](sequence_structure_refinement.md#full-sequence-atlas细化2026-09-21-0616后反馈)。
- PTM默认dbPTM，使用较高绘图区、较大标记和聚合注释数；按屏幕密度聚合临近标记，点击展开原位置/类型/来源，View table按当前窗口打开注释表。可切全部来源，PTMD2仍仅在Disease。显示聚合不改变原记录或科学证据。
- Domain默认同时显示UniProt与Pfam，纳入原Domain/Repeat/Region/Motif/Coiled coil；Chain/Signal/Compositional bias由Processing开关按需显示。来源筛选只作用Domain，不影响PTM、膜或功能。Secondary将helix/strand/turn放入一条较高的彩色原区间轨道，保留原边界，不生成未注释loop。功能位点缺失明确留空，不为丰富展示而补造。
- 颜色按PTM类型、结构类别、domain/region/膜区段分类，也可切换按来源着色；每轨提供图例。Pfam仍使用正式alignment边界，不改成envelope边界。
- 增加整条canonical序列，每行50残基，按位置选择并联动已有结构。窄屏局部横向滚动。白/灰/绿/蓝/黄/粉背景表示计数档位；3px域/膜边界与9px多类型PTM点标记叠加，支持已映射变异数、PTM、二级结构、JSD四个观察方式。
- 变异分布与逐残基计数只复用已发布annotation→ddG prediction→当前canonical验证关系；标记这是已验证映射覆盖子集。所选transcript的HGVSp不能直接成为canonical位置。其余变异仍在目录可查。
- 04:28后的最新反馈明确恢复Sequence的Variant density作为唯一位置分布轨道；Catalog继续只显示后果横条及六类ClinVar临床汇总。密度保留充分柱高与最小可读bin宽，按当前窗口自适应分bin，点击bin缩放共享窗口；累计单位是已验证variant–position links。致病/可能致病红、VUS橙、良性/可能良性绿、冲突紫、其他蓝、未分类灰，沿用来源显示归组，不生成新诊断。
- Interface在同一面板内以原0–1分数显示；设置按需展开，PeSTo分片/结合类型和SPPIDER伙伴/query角色保持独立。切换膜来源保留Interface上下文，加载时不冒用旧膜轨道。
- JSD提供原0–1纵轴、0.5参考线及悬停十字线，显示原位点数值、相邻差值和来源支持状态；点击/键盘选择共享残基。0.5不是阈值，相邻差值不声称生物学趋势。
- PTMD2从Sequence所有展示入口移到Disease，原产物保留；不投射未验证位点。保留FASTA、其他未定位PTM注释及当前结构严格逐残基映射、pLDDT图例。不增加新预测或未发布位点数据。

## 4. Variant Catalog

目录主表依次显示：Genomic variant（位置与核苷酸REF→ALT）、Position（所选转录本位置和短AA变化）、Ref、Alt、后果、来源可点标签、原始临床分类、群体AF、用户选择的预测器。GRCh38只在列头标注；完整variant ID与HGVSc移入详情。坐标列明确所选转录本，不能暗示canonical。2026-09-21追加的[Variant证据精修方案](variant_evidence_refinement.md)维护ClinVar分域星级/ID、Population色阶、Prediction总览筛选、Stability方向和Transcript精简；替代此前完整ID/HGVSc在主格重复显示的设计。

目录之前展示当前完整筛选范围的后果横条和六类ClinVar环图，后果有重叠时不把其和称为唯一变异数。复合后果分别着色。预测介绍面板区分61个评分字段与43种来源工具标签，按阅读用途分组、介绍适用对象与可用覆盖，再进入字段选择。AlphaMissense独立说明并默认展示。

来源按钮定位ClinVar、COSMIC等实际来源注释；保留临床review和原分类。预测器面板按已有机制分组选择显示列；仅已有明确原量尺才绘制数值条，原prediction label独立可见。缺失与零分开。AF主显示百分比，保留来源、群体、原值；不把AF解释为致病风险。

提供来源、后果、原临床分类、频率可用状态、文本搜索、代表转录本canonical/non-canonical/unknown和已验证canonical映射范围筛选。VEP的CANONICAL标记与UniProt映射是独立维度；未标记canonical的有效Transcript实体归为non-canonical，实体/标记不明归unknown。只筛选已发布代表后果，不声称包含该基因全部转录本。筛选与分页保持可重现URL状态，切换条件清除旧游标。

## 5. Expression、QTL、PPI和疾病

Expression先给normal tissue/cancer/cell line/single cell覆盖介绍与分布，记录数与dataset-context数区分，再按source、measurement/组织或细胞给统计卡片和柱条；统计表示记录覆盖，表达原测量与单位在展开中显示。QTL增加原创SVG人体位置导航及原组织横条，按来源和原tissue筛选；人体图使用普通文档布局，随页面滚动，不启用sticky悬停。UI器官词典不是科学映射，无法示意的原名仍保留；极小P值保持原文。

PPI原生interaction category环图为只读总览，置于Source project collections之前；完整来源卡及Collection下拉优先IntAct、BioGRID，IntAct mutation作为后续独立证据入口，默认仍查full collections，显式URL选择保持有效；下方常驻分页表格及source、interaction category筛选器，用户通过筛选器选条件；统计为来源记录数，native interaction ID在原详情可见，当前不额外提供其distinct汇总，也不称作唯一PPI边数。负证据、context及原mutation说明在详情保留。

Disease增加独立PTMD2卡与原Disease/State/MutationSite/CellType/Enzyme、来源类型、映射状态及文献详情，区分实验支持和potential记录。按来源卡片展示记录数、来源证据性质；展开该来源列表及具体证据。区分基因疾病关系、剂量、表型及具体变异结论，不恢复未执行的ClinVar条件关联。

各记录分页保留Previous/Next，并提供1-based页码输入与Go/Enter直接跳转，包括蛋白检索、变异目录/预测详情、基础注释/膜观测、Sequence/PTM/Interface、Expression组织及记录、QTL/PPI、Disease/PTMD及表型详情。已知总数显示真实总页数；未知总数不伪造总页数，空页保留跳回入口；非法页码拒绝，筛选变化重置分页。新增offset访问兼容原cursor，cursor存在时优先cursor，不顺序遍历所有前页。

## 6. 实施和验收

复用当前React/FastAPI、一个8000端口、现有PostgreSQL及只读角色；不新建环境。新增查询只使用现有表/索引和已确认粒度。仅在代表性查询实际慢时定向优化，不能悄悄缩减统计覆盖。

验收：真实P00533及不同数据覆盖蛋白；整序列长度和末位、feature hover/click/原证据、range到目录、预测器选择、AF零与缺失、来源原分类、表达/互作/疾病卡片→过滤→详情、结构联动；桌面及窄屏布局、API异常与空状态。实现结果和实际测量写入问题记录和最终交付记录。
