# 第二版问题清单与实施状态

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

2026-09-22后续反馈另见[下一阶段问题与优化目标](../../../../research/01_preview_optimization/issues.md)。本文件保留9月21日当时的实施与验收事实；新反馈在新清单逐项维护，不能用本轮旧“已验收”状态关闭新目标。

维护时间：2026-09-21 04:30（香港时间；第三轮及后续精简已本地验收，03:56以前交付为历史记录）。用户要求逐条记录其反馈、追加发现和调研方案。本文件是本轮问题状态的主维护位置；不以代码已写替代联调通过。

入口：[采用方案](../../plan/website_v2.md) · [研究依据](analysis.md) · [API局部实施](../website_v2_api.md)。实际通过范围及限制见[交付与验证](../../../../record/00_initial_preview/20260921_website_v2.md)。

## 用户提出的问题

| ID | 问题 | 当前处理方案 | 状态/验收证据 |
| --- | --- | --- | --- |
| U01 | 顶部长FUNCTION及PubMed引用冗余 | 删除独立简介，直接呈现蛋白身份；原文详情方案现由U42取代 | 已验收：身份先显示，顶部长简介移除 |
| U02 | 字体、颜色、模块背景缺层次 | 淡色专题区域、标题/指标/说明三级字样与图标 | 已验收：CATVariant色系和字号，390px无整页溢出 |
| U03 | Basic Information小模块未独立 | Function、定位、膜、功能/通路、反应药理分区 | 已验收：独立基础面板 |
| U04 | reaction/function完全折叠看不到内容 | 子面板默认摘要或内容预览，再点详情 | 已验收：摘要可见，原文/引用在详情 |
| U05 | 定位和拓扑逐条堆积难抓重点 | 同来源同对象组织定位标签；拓扑在序列中展示 | 已核对：同来源同对象组织，未生成统一定位 |
| U06 | 缺整条序列网格 | 全canonical每行50残基，颜色lens和特征标记 | 已验收：P00533 1210及Q12809 1159全残基 |
| U07 | PTM/domain/secondary颜色单调且无法互动 | 语义图例、type/source颜色切换、hover/focus和点击详情 | 已验收：精简轨道、来源选择、hover/点击 |
| U08 | 详细注释未充分利用 | feature专用详情接口，按所点原记录显示注释和文献 | 已验收：PTM/Pfam/DeepTMHMM2原证据接口和弹窗 |
| U09 | Sequence缺突变汇总 | 已验证canonical子集的逐残基统计和分布选区→目录 | 已验收：canonical映射子集与bin→目录 |
| U10 | Variant source不能点ClinVar/COSMIC详情 | 来源按钮打开对应原注释 | 已验收：L858R ClinVar及COSMIC来源详情 |
| U11 | 氨基酸变化、位点不清楚，转录本占主空间 | 短change+Ref/position/Alt列，编号放详情 | 已验收：Ref/Position/Alt及原HGVS详情 |
| U12 | 多预测器不可选择显示 | 分组选择预测器主列，原值/原pred分开 | 已验收：61可选字段、最多12列、Apply更新URL |
| U13 | 原临床分类颜色及解释不够 | 来源原致病/良性/不确定/冲突色标及review | 已验收：原分类色标；11个边界用例 |
| U14 | 频率展示遗漏/不显著 | 主列AF/群体选择、频率可用统计、原群体详情 | 已验收：百分比、原AF、群体，R2L真零 |
| U15 | Expression/QTL直接列表缺总体组织/细胞视角 | 完整筛选范围summary→source/measurement/tissue选择→记录 | 已验收：Expression逐context、QTL人体导航到原记录 |
| U16 | PPI缺类别和来源图表 | U25取代点击图表入口；图只展示，表格及筛选器常驻 | 已验收：按U25完成只读图及常驻表 |
| U17 | 疾病需要VarSome式按来源组织 | 来源卡片→分页关系→原证据/表型 | 已验收：GenCC原疾病详情与独立PTMD2 |
| U18 | 总览到细节的交互及icon不足 | 统计卡、局部图例、来源按钮、筛选状态及详情返回 | 已验收：摘要/选择/原证据链路 |
| U19 | 需要清晰的上下文及MD管理 | 本问题表+研究依据+采用方案+完成后的验证记录 | 已完成：调研、问题、现行方案、交付记录和入口同步 |

## 03:28–03:30追加反馈

| ID | 用户问题 | 本轮执行方案 | 状态 |
| --- | --- | --- | --- |
| U20 | PTM过密，可考虑减少来源 | 默认UniProt，单行分组marker，可选来源/all，点分组看原位置来源 | 已验收：EGFR默认98个UniProt注释→51标记，其余源保留 |
| U21 | Domain与secondary多行拥挤 | 默认明确Domain，region/processing可选；secondary单行，重叠详情入口 | 已验收：默认单行，source/region/Separate annotations可选 |
| U22 | UI/颜色全面参考CATVariant | 蓝色操作、交替行、蓝紫绿橙粉分类、细条和清晰字号 | 已验收：色系、交互及字号；参考与取舍写入analysis |
| U23 | 变异分布多个位点一bin、临床类别占比 | 共享可选bin堆叠；六类原标签归组 | 已验收：六桶/完整计数，Q12809 50aa bins→101–150目录 |
| U24 | Full atlas颜色及PTM/membrane标记弱 | 白/灰/绿/蓝/黄/粉计数背景、3px区域边界、9pxPTM标记 | 已验收：全序列色档、边界与多类型PTM标记 |
| U25 | PPI图只展示，不当入口 | 图只读，表格+source/type筛选器常驻 | 已验收：PPI总览0个button，默认表格10行及source/type筛选 |
| U26 | PTMD移Disease、不占Sequence | 底表保留，Sequence入口排除；Disease专用summary/list/detail | 已验收：Sequence排除，Disease463条与PDA109原证据 |
| U27 | Regulation增加人体组织图 | 阅读PTMD实际图，原创SVG位置导航+来源组织横条 | 已验收：Brain→Brain_Cortex→原QTL记录 |
| U28 | Expression缺类别分布介绍 | 类别覆盖介绍+分布，记录数/原context数/测量分开 | 已验收：四类覆盖与dataset-context计数，逐context搜索 |
| U29 | CATVariant细分数条/颜色 | AF百分比与原值；已核实量尺的预测细条 | 已验收：34字段原0–1细条，原分类着色；AF原零/缺失区分 |

## 实施中额外发现的问题

| ID | 发现及证据 | 影响/处理 | 状态 |
| --- | --- | --- | --- |
| A01 | 所选transcript HGVSp不等价当前canonical | 禁止直接取HGVSp数字画sequence；复用发布ddG验证关系，明确未覆盖数 | 已核对：仅正式验证关联 |
| A02 | P00533有1,323个目录variant缺当前可用canonical验证关系 | 展示覆盖子集，不把未覆盖说成无变异，也不从目录删除 | 已验收：1323未覆盖目录变异仍保留 |
| A03 | sequence PTM feature是record_ids聚合，非全部源字段 | 新增按原record_ids分页查询的feature详情 | 已验收：原record_ids可分页查详情 |
| A04 | 一些完整Chain/region覆盖近整条序列 | 分开domain与region，颜色+可读标签+hover；全序列边框仅明确domain | 已修：默认明确Domain，regions/processing可选 |
| A05 | 第一页长度/来源之和易被误叫总数 | 后端summary按完整过滤范围和明确unit计算 | 已核对：完整查询统计，不来自分页 |
| A06 | 红色预测条易被误认临床致病结论 | 原prediction label、原量尺和来源原临床结论分开；不新增阈值 | 已核对：原量尺/原判定，不新增阈值或综合诊断 |
| A07 | 同一位置不同PTM来源/修饰会重叠 | 默认来源精简+附近位置合并入口；多lane改为可选展开，原记录保留 | 已验收：默认合并marker→原位置→原记录 |
| A08 | 全序列长网格可能导致窄屏溢出或渲染浪费 | 局部横向滚动、逐行content-visibility、预建位置索引 | 已验收：390px整页无溢出，网格局部滚动 |
| A09 | PPI记录/原互动ID/context membership不能当唯一PPI边 | 来源/类别统计保留原粒度与解释 | 已核对：记录数与native ID详情，不称唯一边 |
| A10 | 内置浏览器无可用连接 | 已核查工具列表为空；复用既有Chrome会话与8000服务 | 已完成：复用现有Chrome会话验收 |
| A11 | 独立审查发现Nightingale旧标签列与新feature SVG不共用横轴；JSD和位点中心差半格 | 去掉旧标签列，所有绘图区同12px内边距；统一1-based inclusive与残基中心，navigation ruler-padding=0 | 已验收：三坐标绘图区left62/width1156，统一inclusive定位 |
| A12 | `/phospho/`误把Dephosphorylation归成Phosphorylation；GlyGen N/O-linked被遗漏 | 去磷酸化先匹配；仅GlyGen原N/O-linked映射到糖基化颜色，原标签仍保留 | 已修：类型规则定向核对 |
| A13 | HTP使用S/O/M/I代码，DeepTMHMM2使用TMhelix，通用英文匹配漏膜边框 | 来源限定的显示字典，原native type不变；图例和全序列边框共用识别 | 已验收：DeepTMHMM2 25aa膜边界与原详情 |
| A14 | Expression原第二版仍只提供category/dataset卡，未真正做到组织/细胞总览 | 新增单dataset context汇总、搜索/分页、context_key精确筛选；不跨来源统一组织 | 已验收：Brain搜索13个context、精确上下文记录 |
| A15 | 表达跨类别行的对象不清楚；主测量缺值详情被Fields略去 | 主行显式category，详情缺值说明not zero，可用测量数独立 | 已修：对象与缺失状态明确 |
| A16 | 疾病的obsolete/MONDO mapping/HPO modifier等已返回但不可见 | 来源详情补状态，保留疾病层对象限定 | 已修：原状态/映射/修饰符在详情保留 |
| A17 | 浏览器验收时本地服务收到SIGTERM正常退出，位点请求暂时拒绝连接 | 已改为同一8000独立进程恢复；无数据库异常，实际重试L858→目录成功 | 已恢复：8000单进程，health只读ok |
| A18 | ClinVar分类原值'-'含义不清晰；预测值难比较 | 展示Not classified并保留原filter；SIFT/REVEL原0–1细条、方向说明，无新阈值 | 已修且验收：未分类原值保留，34字段量尺细条 |
| A19 | Nightingale初始化默认1–100覆盖整序列范围，切换拓扑看不到644膜段 | 插入前设display-start/end，range以真实sequence初始化 | 已验收：全长初始范围，切换拓扑不截到1–100 |
| A20 | PTMD官网区分实验PDAs与potential PDAs | Disease保留原source_type/classification及证据 | 已验收：PTMD2保留原类型/验证标志/映射状态 |
| A21 | 临床badge的substring判色与分箱规则不一致，否定短语可能误红 | 与后端一样标准化并精准拆token，冲突优先；未匹配预测call中性 | 已修：11个显示分类边界用例通过 |

| A22 | 最终截图中UniProt Topological domain两侧都被灰色通用类型覆盖 | 仅该来源该类型读取其原Extracellular/Cytoplasmic标签上色；原类型和坐标不变 | 已验收：胞外青/跨膜紫/胞内绿，原标签与坐标保留 |

## 当前协作与后续检查

- 根任务：Sequence交互/全序列、App整合、统一样式、参考研究、运行服务验收及本清单。
- API任务：所有后端summary、Variant主列增强、feature原注释详情及API实施证据。
- 基础/Context任务：基础信息和Expression/QTL/PPI/Disease面板。
- Variant任务：新目录、预测器/AF选项和来源详情。
- 本轮已完成：三代理分工及根任务集成，TypeScript/Vite构建、真实端点和代表浏览器验收，修复实际问题并同步文档。后续继续依据用户对当前版本的反馈调整；公网部署、全蛋白逐页与并发压测不在本轮范围。

独立Context研究见[context_review.md](context_review.md)。2026-09-21首轮真实浏览器已验证：P00533首屏、1,210全残基、PTM原文/PMID详情、L858→两条已验证位置变异、ClinVar/COSMIC各自原注释、可选AlphaMissense主列。尚未全部完成，后续按新增修正再验收。

## 序列密度与结构注释追加反馈（2026-09-21）

本轮仅处理以下新增问题；不改变前面尚在维护的验收状态。采用方案见[序列与结构精修](../../plan/sequence_structure_refinement.md)。

| ID | 用户反馈 | 采用方案 | 状态 |
| --- | --- | --- | --- |
| U30 | Sequence/Catalog重复Variant Distribution | 最新U52恢复Sequence唯一密度轨道；Catalog继续U37后果/临床汇总 | 最新范围见U49–U53 |
| U31 | PTM点形状无含义、分散后更密 | 独立PTM表格，默认dbPTM；序列只显示所选来源/类型的去重位点覆盖带，放大到局部才显示一致圆形位点 | 已完成，代表性验收通过 |
| U32 | Secondary structure凌乱 | 低倍率三类覆盖热带；局部倍率才显示helix/strand/turn原边界，原注释仍可点 | 已完成，代表性验收通过 |
| U33 | 各轨道缺序列标注且难调范围 | 每轨独立同坐标轴与局部残基行；增加Start/End、缩放、平移及拖选 | 已完成，代表性验收通过 |
| U34 | Function sites占独立空间但点很小 | 与Domain同面板的紧凑子行，形状统一并保留原详情 | 已完成，代表性验收通过 |
| U35 | Structure只有pLDDT | 增加domain、PTM、变异数、JSD、PeSTo、伙伴条件SPPIDER着色；仅精确序列映射 | 已完成，代表性验收通过 |
| U36 | 已发布预测PPI应入PostgreSQL并纳入位点 | 独立web_interface导入PeSTo及SPPIDER原连续分数、结构/伙伴/来源关系，保留向量和原mapping | 已导入并验证 |

追加发现：PeSTo的五类倾向非互斥；SPPIDER两个head均评分query，不是两个蛋白各一个分数。正式科学契约禁止跨分片/伙伴求max或平均，结构着色必须显示所选上下文。


## 03:58–04:03追加反馈：变异概览与基础注释可视化

本节为当前任务，替代此前保留Catalog位置分布、Function原文详情的展示决定。既有科学数据和同时进行的U31–U36序列/结构任务保留。三项子任务分别负责API与统计、Variant Browser、基础注释；根任务负责JSD、统一对比度、研究整合及浏览器验收。

| ID | 用户反馈 | 当前采用方案 | 状态 |
| --- | --- | --- | --- |
| U37 | 删除Variant Browser重复的Variant distribution | 后果横条及六类ClinVar临床统计替代位置图，完整筛选范围统计 | 已验收：位置图移除；完整后果/六类临床统计 |
| U38 | 预测器太多，需分类介绍；AlphaMissense默认显示 | 展示评分字段/来源工具标签数、浏览分组/说明/可用覆盖，分组进入选择面板；AlphaMissense独立卡及默认列 | 已验收：默认4列含AlphaMissense；分组选项6字段、隐藏/恢复 |
| U39 | 目录需基因座替换和variant ID | 主行增加GRCh38 chromosome/position、variant ID、核苷酸REF→ALT与来源HGVSc | 已验收：L858R的GRCh38:7:55191822:T:G及c.2573T>G |
| U40 | consequence需颜色区分 | missense/synonymous/start lost/stop gained/splice等分别着色，复合后果各自保留 | 已验收：六类后果色标；stop_gained筛到89条 |
| U41 | canonical/non-canonical筛选 | 依据VEP CANONICAL和原转录本实体，保留unknown；与UniProt精确位点映射分开 | 已验收：canonical4096、noncanonical0空态与恢复；API保留unknown |
| U42 | 完全删除Function长Entry Level Annotation | 页面及详情均不渲染UniProt FUNCTION长文；保留非FUNCTION结构化反应、家族等 | 已验收：主面板及Function详情无FUNCTION长段 |
| U43 | GO/Pathway拥挤，需图形预览 | GO三aspect独立预览/全量统计/精确slim筛选；Reactome按U47短预览，真实diagram在详情 | 已验收：三aspect完整统计；GO:0048856筛到1条原注释；通路按U47精简 |
| U44 | JSD缺数值、交互和中轴 | 原0–1纵轴、0.5参考线、悬停十字线/残基值/相邻差值/原支持状态、点击及键盘选位点 | 已验收：L858读数/点击/键盘/单残基窗口及窄屏刻度 |
| U45 | Cellular location需交互式图示 | 后续U48替代复杂细胞图；保留来源/适用对象和按需证据交互 | 已按U48精简并验收 |
| U46 | 色彩寡淡、字体过浅 | 提升蓝紫绿橙饱和度，正文/标签加深，图例文字与颜色同时表达 | 已验收：桌面及390px字体/饱和度，整页无横向溢出 |

新增审查发现：

| ID | 发现 | 处理 |
| --- | --- | --- |
| A23 | VEP canonical标记是代表转录本属性，不等于可映射UniProt；当前代表蛋白样本全为YES | canonical筛选解释限定已发布代表后果，空结果不宣称基因不存在其它转录本；unknown单独保留 |
| A24 | GO第一页会低估预览/分组统计；一个GO term可能有多条注释或多个slim关联 | 新summary计算完整查询；annotation、distinct term和slim membership分别说明，筛选列表total与对应统计核对 |
| A25 | Reactome关联表不能凭名称推断反应连线或上下游 | 只呈现已发布通路关联与真实官方diagram，不生成虚构网络 |
| A26 | 61评分字段并不是61个独立预测器 | 评分字段数与43种来源工具标签分开；raw/PHRED不同字段不伪称新方法，不复制参考站ACMG/综合分 |
| A27 | JSD趋势/0.5可能被误解为生物学阈值 | 原值及数轴直接展示，0.5仅坐标参考，相邻差值仅当前图读数；无新保守性/致病阈值 |
| A28 | 独立审查发现JSD单点窗口不画点、移出曲线丢失选择按钮、窄屏tooltip可被裁切 | 已修并验收：1–1有marker；选位点按钮可点击；390px tooltip在容器内，固定11px刻度不缩小 |


### 第三轮后续精简（优先于复杂图方案）

| ID | 用户反馈 | 最新决定 | 状态 |
| --- | --- | --- | --- |
| U47 | Reactome pathway展示过度 | 缩为简短总计、少量预览和查看入口；完整列表及真实diagram按需打开 | 已验收：3条预览；主题筛选8条/分页；官方diagram链接 |
| U48 | Cellular location图不美观，图文反而冗余 | 删除复杂细胞图，简洁icon/原标签，紧凑source/scope选择，细节及证据按需展开，删重复介绍 | 已验收：无细胞图，4标签+more，UniProt/HPA及Isoform 2原证据 |


## 序列/结构精修交付补充（04:24）

| ID | 问题或最新决定 | 处理与状态 |
| --- | --- | --- |
| SEQ-01 | 用户要求预测interface不要单独列主表，放入Sequence Browser | 已改成单轨原始分数曲线；PeSTo分片/类型、SPPIDER伙伴/角色可切换，与范围及位点证据联动；主轨无表格 |
| SEQ-02 | 验收发现窄屏SVG固定1000单位会压扁坐标字 | 逐轨坐标改为实际容器宽度，按可读密度显示字母；390px通过 |
| SEQ-03 | 结构不同lens切换可能残留上一次选中配色；多分片不能混合 | 串行应用颜色，恢复pLDDT且保留当前位点；Q01484 F14与其1,357个残基独立核对通过 |

[本轮交付和浏览器证据](../../../../record/00_initial_preview/20260921_sequence_structure_refinement.md)维护实际验收范围；不替代其他并行任务的状态。

### 旧版结构风格追加

| ID | 用户问题/核对结论 | 实现与验证 |
| --- | --- | --- |
| SEQ-04 | 旧版结构渲染更饱满，要求可切风格；旧版与当前均基于Mol*，旧版为Gaussian surface＋illumination，当前为cartoon | Render style新增Smooth surface · legacy，保留Ribbon；数据着色独立。两风格往返、PeSTo与pLDDT、390px验证通过，见[追加交付](../../../../record/00_initial_preview/20260921_sequence_structure_refinement.md) |


## 04:28后追加：共享坐标Sequence Browser

本轮直接实施用户指定的注释集合与CATVariant紧凑布局。替代U31–U34的分散默认展示，保留其原记录和交互；不变更Interface正式科学快照或结构实现。

| ID | 用户问题 | 当前实现 | 状态 |
| --- | --- | --- | --- |
| U49 | 多行分散，无法沿同一序列纵向比较 | 八类轨道共享首尾坐标、窗口和位置导线，开关独立 | 已完成：最终构建通过，桌面/390px实际验收 |
| U50 | Domain/Region和功能信息过少 | 默认UniProt+Pfam及原Region/Repeat/Motif；功能位点按真实来源显示 | EGFR12条、KCNH2 15条domain/region；function 6/0，原证据保留 |
| U51 | PTM表之外也应恢复序列注释 | dbPTM默认紧凑标记，屏幕密度聚合，原记录可展开；表格按需打开 | EGFR134 marker/129位点，全部来源426 marker，已点查原证据 |
| U52 | Sequence加入Variant density | 六类来源临床显示桶按窗口分bin；点击共享缩放，目录不重复 | bin点击到81–96，八轨起点及宽度仍一致 |
| U53 | Protein binding/Interface纳入整体 | 同面板连续分数轨道，设置保留模型/分片/类别/伙伴/角色 | 已验收：模型/角色切换、键盘窗内选择、切Topology保持伙伴与角色 |

补充审查发现：

| ID | 发现 | 处理 |
| --- | --- | --- |
| A29 | 旧UniProt-only且关闭regions使现有注释不可见 | 开放Pfam和原Region等；不把Chain混作domain |
| A30 | KCNH2真实无独立function注释；PTM的marker/位置/原记录计数不同 | selectivity filter保留Motif身份；计数明确单位，不补造功能位点或实验数 |
| A31 | Interface窗口外旧选择/hover与键盘值不一致 | 窗口变化清hover，aria/Focus/Enter使用同一有效位置；已实际浏览器复验 |
| A32 | 首次切Topology卸载子组件，丢失Interface上下文 | 保留同蛋白已加载数据与组件，膜加载单独标识，atlas不暂画旧膜；已实际浏览器复验 |



## 共享布局后的可读性及膜特征反馈（2026-09-21）

用户确认共享坐标的整体组织，进一步要求按信息量分配空间。保留U49的纵向对齐，替代其过度紧凑的行高；不再以所有轨道近似等高为目标。

| ID | 用户问题 | 当前方案 | 状态 |
| --- | --- | --- | --- |
| U54 | Secondary拆三条细行，原区段难辨 | 一条较高的彩色原区间轨道；Helix/Beta strand/Turn原类型保留 | 已实现，桌面/390px实际查看 |
| U55 | PTM、density标记/字体太小、遮盖 | PTM放大并明确显示聚合数；density增加柱高与bin可见宽度；图例独立留空间 | 已实现，桌面/390px无页面溢出 |
| U56 | 无法明显选择和伸缩序列范围 | 全长导航改为可见选择区和左右拖动手柄；拖选、手柄缩放、键盘、双击复位、数值/Zoom/Pan共享窗口 | 鼠标243–787/手柄/键盘/复位及390px触摸303–787通过 |
| U57 | 黄色Membrane Association信息少，只跳Track | 真实来源膜特征摘要和按需详情；跨膜数明确当前canonical/UniProt来源，其他来源与预测独立 | 已验收：EGFR1/0/2、KCNH2 6/1/8，原区间/预测/OPM分页/空态与390px详情 |

新增检查：共享坐标轴曾对50px残基字母viewBox统一固定35px高度，造成局部窗口文字缩小；现改为按实际模式32/50px，保留固定字号。范围导航需要显式触摸拖动和键盘入口，不以灰色概览或隐藏提示替代可发现操作。


## Variant 证据面板精修（2026-09-21）

| ID | 用户问题 / 补充发现 | 处理与状态 |
| --- | --- | --- |
| VE-01 | Genomic variant 重复 GRCh38/ID/HGVSc；Position 应在 Ref 前 | 首格缩为位置/替换，Position 前置；实际表头/单元格验证通过 |
| VE-02 | ClinVar classification、origin、review、ID 无层次 | 原分类分区、review 金色星级、origin 标签、conditions/namespace IDs 分组；RCV/SCV 分开；展开已验证 |
| VE-03 | Population 比例缺少颜色与直观大小 | 固定 AF 连续色阶、群体相对条、AC/AN；非零/真实零/缺失分别验证 |
| VE-04 | 预测器太多文字，缺少总面板与颜色引导 | 来源 call 分布、方法组覆盖、紧凑分数卡、搜索/组/call筛选/九卡分页；55分数+6缺失真实样例通过 |
| VE-05 | Stability 增减不直观 | 已确认 ThermoMPNN convention 对应方向色/箭头和零中心条，正负真实样例通过 |
| VE-06 | Transcript 文字密集、含义不明 | 蛋白/编码变化、exon/intron 默认；ID及注释上下文折叠，真实展开通过 |
| VE-07 | 发现 review 跨 assertion 域混用会错误赋星 | 三类 assertion 原 status 独立应用；L858R 3/1/2星分别验证；未知状态不当零星 |
| VE-08 | 发现 MONDO 重复前缀与 HGVS 编码符号 | 仅显示/URL规范化；原字段保留。MONDO链接与p.Arg2=验证通过 |
| VE-09 | 预测字段多于独立工具、score方向不同，易伪造成综合诊断 | 总览按输出计数，SIFT明确低分方向；未移植CATVariant合议/权重/临床阈值 |
| VE-10 | AF和ΔΔG可视条不同量尺容易跨变异误比 | AF颜色固定log尺度、群体条为局部线性；ΔΔG明确局部最大绝对值量尺，比较原数字 |

[展示方案](../../plan/variant_evidence_refinement.md) · [调研依据](analysis.md#variant-evidence-20260921) · [交付、截图与验证范围](../../../../record/00_initial_preview/20260921_variant_evidence_refinement.md)。以上已完成本地构建与代表性交互验收，不替代其他并行任务状态。


## 文案与按需帮助（2026-09-21）

| ID | 问题 | 处理 |
| --- | --- | --- |
| HELP-01 | Variant临床环图只能静态查看 | 环段/图例高亮、数量占比、点击固定、键盘按钮；不改变筛选 |
| HELP-02 | AlphaMissense与各板块长脚注重复 | 默认短标签；统计口径、证据限制移至就近问号 |
| HELP-03 | Expression覆盖说明重复多次 | 删除两段长文与重复上下文提示，合并至指南 |
| HELP-04 | AlphaGenome缺少统一模态解释 | 官方九模态含义/单位、本站分辨率/缺口/上下文规则集中展示 |
| HELP-05 | contact被误称频率、负值全映为零色 | 原数值不变；log-fold单位、0中心发散色标、缺失灰色 |
| HELP-06 | 问号仅为静态图标/hover title | 真按钮打开命名对话框；移除预测选择卡中无法点击的伪问号 |
| HELP-07 | 浏览器无连接 | 实例列表为空；真实交互、移动截图与控制台验收待补 |

[当前方案、官方资料与验证边界](../../plan/ui_help.md)。


## DeepTMHMM2默认预览（2026-09-21 05:19）

| ID | 用户问题 | 处理与状态 |
| --- | --- | --- |
| U58 | DeepTMHMM2是重要来源，应直接展示简介和简要概述 | 已完成：黄色膜面板内独立紫色预测预览，显示来源介绍、原蛋白类型、TM螺旋数、信号肽；直接打开预测详情。P00533/Q12809桌面与390px交互验收通过。 |

来源字段与原数据核对沿用[膜摘要研究](analysis.md#membrane-overview-20260921)；预测摘要不与UniProt计数混合。交付见[本轮记录](../../../../record/00_initial_preview/20260921_website_v2.md)。


## Expression与IntAct mutation细节（2026-09-21）

| ID | 用户问题 / 审查发现 | 处理与状态 |
| --- | --- | --- |
| EC-01 | Tissue & cell contexts只有前后翻页 | 改数字页码、首尾、省略号及直接跳页；6页/699页与搜索重置已验证 |
| EC-02 | Overview只给context类别，RNA-seq/MS等不明确 | 增加5类方法解释、数据集/详情badge；14集合按原测量核对完成 |
| EC-03 | IntAct mutation效应淹没在元数据中 | effect前置，箭头/方向颜色与ring统一；增强、减弱、中断、无效应真实记录通过 |
| EC-04 | Source range、mutation accession及重复字段冗余 | 主表/默认详情去掉范围和affected前缀，保留feature/伙伴/变换/文献，附加证据折叠 |
| EC-05 | GTEx Brain_Cortex等原始分隔符直接展示 | Expression/QTL标题、卡片、表和详情使用可读标签；原键和URL保留；实际Brain Cortex查询通过 |
| EC-06 | 通用mutation并不提供方向，不能填为无效应 | 明确Effect not specified，灰色；与来源with no effect蓝色分开 |
| EC-07 | FANTOM/DVP容易被统一误标RNA-seq | FANTOM=CAGE；DVP=MS；配对RNA字段不改变其主测量身份 |
| EC-08 | 只有一个可解析参与者ID时，不能猜自互作 | 保留source participant提示，完整原参与者在附加证据；不新增映射规则 |

[数据集与方法审查](context_review.md#expression-ppi-20260921) · [交付、截图和验证](../../../../record/00_initial_preview/20260921_expression_ppi_refinement.md)。以上前端优化已验收，不修改现有数据库或科学整理规则。


## 中性背景与条目信息着色（2026-09-21）

| ID | 用户问题 / 审查发现 | 处理与状态 |
| --- | --- | --- |
| U59 | Basic Information不应依靠绿/黄/紫整块背景划分 | 已完成：六个主卡实际白底/深灰标题，饱和图标和局部数字/标签；DeepTMHMM2保持重要默认来源，桌面/390px验收 |
| U60 | Expression/QTL/Disease及展开、表格需要信息级配色 | 已完成：中性表格与详情层次，来源/类别/原测量分别突出；HPA测量、GTEx统计、HPO/GenCC详情与手机交互验收 |
| A33 | 组件与全局重复设置Basic背景，新预览继续嵌套色底 | 已清除全局重复覆盖，组件维护背景；六主卡计算样式均rgb(255,255,255)，标题rgb(31,41,55) |

调研依据：[CATVariant实地配色复核](analysis.md#information-colors-20260921)。本轮不改变科研字段、分类阈值或数据库。


## 统一预测列与工具说明（2026-09-21）

| ID | 用户问题 / 审查发现 | 处理与状态 |
| --- | --- | --- |
| PRED-01 | 每个predictor独占一列，容纳数量有限 | 最初合并网格已被用户后续实看反馈替代：恢复独立纵列，收紧身份列；取消12项上限继续保留 |
| PRED-02 | Toolkit缺乏每个工具的含义和判定标准 | 61字段逐项补用途/量尺/方向/依据与链接，细节按需展开 |
| PRED-03 | 不同字段存在原分数、排名、类概率与条件阈值 | 各自解释；不补造统一阈值，不把相关模型视为独立投票 |
| PRED-04 | 修改代码后运行API仍限制12项 | 本地API已重载，真实20行×61字段请求200；只读回归通过 |
| PRED-05 | 当前侧会话Browser连接列表为空 | 前端构建通过；当前独立纵列、弹窗和移动端实际交互待验收，旧版本截图不作为本次证据 |

[方案与逐字段依据](../../plan/variant_evidence_refinement.md#统一预测列与prediction-toolkit2026-09-21追加) · [验证记录](../../../../record/00_initial_preview/20260921_variant_evidence_refinement.md#统一预测列与逐工具指南追加)。


## 滚动、PPI顺序与全站跳页（2026-09-21）

| ID | 用户问题 / 发现 | 实施状态 |
| --- | --- | --- |
| U61 | Regulatory组织图滚动时固定到容器底部 | 已修复：cx-human-panel原position:sticky/top95px改static；实测页面滚160px，图同步移动-160px |
| U62 | PPI category应在project collections上方，常规来源优先 | 已完成：只读环图提前，入口/下拉优先IntAct→BioGRID→后续mutation；不覆盖显式URL中的已选集合 |
| U63 | 所有记录分页应能输入页码 | 已接入共享PageJump并补7个cursor API的offset；构建及代表跳页/空页回退/手机验收通过，详见交付记录 |
| A34 | 仅加页码框无法跳到未缓存的cursor页 | 后端直接offset访问保持稳定排序/过滤；原cursor兼容，不逐页请求 |
| A35 | Interface位点伙伴分页被放在非空记录条件内 | 分页在offset>0的空页继续可见，避免无返回入口；技术上限与真实总数分开 |


## Catalog密度与分布图（2026-09-21后续反馈）

| ID | 问题 | 处理与状态 |
| --- | --- | --- |
| PRED-06 | 合并评分卡片占空间，实看不如原纵列 | 恢复独立列，删除统一网格；工具说明和多选能力保留 |
| PRED-07 | Ref/Alt等身份列留白多，评分空间不足 | 身份列固定紧凑宽度，评分列至少136px，浅色隔行与深标题 |
| PRED-08 | Catalog希望有Sequence同款Distribution | 复用组件和数据，点击bin筛选，清除范围；保留其它筛选和全序列概览 |
| PRED-09 | 分布图若也应用自己选区，会裁掉其它区间信息 | 独立排除canonical_start/end参数，其余条件与表格相同；旧统计/分类不变 |

[当前方案](../../plan/variant_evidence_refinement.md) · [本次验证与限制](../../../../record/00_initial_preview/20260921_variant_evidence_refinement.md#恢复独立预测列与catalog分布图后续追加)。

## Full Sequence Atlas（2026-09-21 06:16后反馈）

| ID | 问题 | 处理 |
| --- | --- | --- |
| ATLAS-01 | 位点摘要、全部feature和原始records重复铺开 | 按证据类型标签页，模式对应内容前置，原证据按需打开 |
| ATLAS-02 | PTM不区分来源、类型且无对齐列 | 来源色签＋类型色，对齐表格，来源/类型筛选保留原record数量 |
| ATLAS-03 | 只有笼统PTM marker图例 | 实际PTM类型图例/按钮与具体类型点，上色/筛选联动 |
| ATLAS-04 | 模式仅换颜色，点击内容不变 | PTM/secondary/JSD/variants/predictions默认焦点及内容顺序随lens改变 |
| ATLAS-05 | 方格被拉成长方形，右上角圆点裁切 | aspect-ratio 1，响应式每行数，去除row content-visibility裁切，标记放格子内 |
| ATLAS-06 | 缺少明确Variant/Predictor入口 | Variant数量/原ClinVar标签组，新增真实predictor coverage与逐替换评分 |
| ATLAS-A1 | 上方默认dbPTM筛选无形缩小Atlas来源 | Atlas独立默认all sources，并明确控制范围 |
| ATLAS-A2 | 多个替换分数若合并为位点颜色会混淆 | 按有评分变异数着色，原值按替换展示，不生成聚合致病分数 |

研究依据为用户提供CATVariant序列图：紧凑方格、类型边界与PTM点、模式说明/图例；本地实际接口确认PTM是position/source/type摘要，每项关联原record IDs。现行布局与计数见[方案](../../plan/sequence_structure_refinement.md#full-sequence-atlas细化2026-09-21-0616后反馈)，运行验证集中在[交付](../../../../record/00_initial_preview/20260921_atlas_refinement.md)。
