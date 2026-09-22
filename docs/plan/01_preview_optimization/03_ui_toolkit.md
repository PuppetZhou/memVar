# 03 已选组件、配色、动效与图标：接入及优化计划

2026-09-22。用户明确选定shadcn/ui、Motion、Radix Colors，并提供Lucide/Tabler SVG。本文件替代此前Mantine推荐及React Bits作为主要动效候选的工程路线；Figma继续作为设计协作工具，未交付画布的状态保持。用户已授权继续完成原位视觉/组件/动效实施、实际验收及Git追踪；不改变科学数据或既定图表量尺。桌面优先。

## 当前迭代：排布纠正与滚动记录（2026-09-22）

用户纠正：要移至Functional下方的是Reactome；GO恢复原全宽三列。上一批GO移动来自实现误解，不再作为现行要求。全蛋白选择器撤掉注释缩略图与浮层，保留简单单点/片段选择、端点微调及独立窗口Reset。Expression补回明确收起，ClinVar展开详情限制高度内部滚动；QTL记录取消翻页改游标增量滚动，Assembly移至来源说明；Full/Topic/Mutation分色。

2026-09-22用户确认：QTL默认按来源标准配色（GTEx每条关联nominal P≤来源阈值；eQTLGen来源FDR<0.05；QTLbase缺少统一标准为未知），保留自定义原始P阈值模式。两种模式均不筛选记录，不将基因级q-value当作关联级q-value。API投影已有统计字段，不重建上游数据。详见[记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#排布纠正与滚动记录)。

## 上批：序列缩略图与局部版面（2026-09-22）

按用户指定的 [EGFR sequence browser调研](../../research/09-egfr-sequence-browser.md) 落实搜索/选中分离、真实注释缩略图、密度切换和短颜色过渡。本批曾将GO移至Functional下方；用户后续澄清实际指Reactome，该排布已由当前迭代纠正。结构粗拖柄改为16px圆点与透明操作区域，沿用已核实的范围事务与Reset语义。

Expression一次展开后内部滚动、组织显示标签去下划线；QTL组织列表直接内部滚动。六项consequence全显示，Variant过滤器、疾病六来源卡和QTL来源卡强化颜色及边界。科学数据、来源类别、量尺与映射规则不变。限定桌面验收、发布产物与保留边界统一见[本批记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#序列缩略图与局部版面)。

## 上批：空白、Reset与阅读层级（2026-09-22）

三处最新批注已实现并本地发布：概览卡片按内容高度；序列搜索栏对齐、窗口Reset归位；结构仅一对大拖柄并新增显著Reset。共享主标题24px、Overview子标题19px、疾病表正文15px；疾病/互作/ClinVar表格强化列间留白和浅底分组，GenCC原类别色增加浅底标签。状态作用域按审查第九节复核，未改变数据和模块顺序。

EGFR/AQP4、1470/1230桌面、拖动取消/键盘/reduce/独立Reset与8000实际发布检查通过。[证据与限制](../../record/01_preview_optimization/20260922_ui_toolkit.md#空白reset与阅读层级)。这是列明组件的交付，不代表全站每个弹层/表格或12类问题全部验收关闭。

## 上批：结构端点、预测工具与疾病面板九条批注（2026-09-22）

已完成代码、TypeScript/Vite构建、限定桌面实际交互及8000本地发布复核；等待用户继续视觉验收。范围：全长结构选择器端点/选区、预测工具官方入口/分类反馈/信息分块、移除AF与预测列分隔、独立canonical位置输入、疾病卡片对齐、PTMD完整来源统计筛选、ClinVar REF/Position/ALT分块。保留既有布局和科学规则；PTMD只增加原始CellType统计及查询，不投影canonical位点。

修复实际操作发现的快速连续筛选覆盖及范围上限重载间隙问题。EGFR与AQP4、1470×837和1230×837、键盘/Escape/reduce检查与限制见[交付记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#结构端点预测工具与疾病面板九条批注)。已核实9个工具family官方入口；其他工具保留方法/定义链接，未虚构官网。公网关闭，全面移动端和历史细分证据分支仍未完成。

## 上批：CATVariant对照与五条局部重设计（2026-09-22）

用户继续要求鲜明序列色与PTM圆点、重设计结构选择器、功能类别纵排＋真实记录预览、采用有许可的细胞图素材，以及Expression分类色；并补充字体、字号、局部背景和边框引导。保持已认可的页面排布、模块顺序与科学口径。审查[第九节](../../research/01_preview_optimization/02_typography_information_audit.md#9-参考数据库对照板块辨识背景与操作引导)中的显示窗口/共享残基/结构局部选区/Variant筛选四种状态独立，是本批验收边界。

四组并行：Sequence与共享科学色表；Structure选择控件；功能/Expression内部组件；细胞素材、共享视觉层级与集成。已取得CATVariant真实EGFR页面样式和序列图例，按实际用途借鉴。细胞图采用SwissBioPics的CC BY 4.0动物细胞矢量素材，并保留署名；分组仅沿用memVar当前来源映射，不引入新的GO/UniProt关联规则。shadcn Item的图标—标题—描述—操作模式仅作局部组织参考，复用已安装Tabs/Button/Dialog与Motion。

本批已完成实现、EGFR/AQP4限定桌面交互、最终TypeScript/Vite构建及8000本地发布复核；代码提交`4f0c825`。此前灰绿数量色与中性PTM菱形由本批鲜明色及洋红圆点替代，分箱、来源和记录数量保持。用户视觉验收继续，公网关闭；实际证据、素材许可、构建信息及未完成分支见[本批record](../../record/01_preview_optimization/20260922_ui_toolkit.md#catvariant对照与五条局部重设计)。

## 上批：文字层级与信息引导（2026-09-22）

用户要求落实[字体与信息审查](../../research/01_preview_optimization/02_typography_information_audit.md)，同级信息使用一致icon/dot、白底页面用适度浅表面分组，同时解决数量1与2–4颜色接近及PTM标记冲突。本轮已授权实施，不受该审查初始“只审查”记录限制；审查原文作为依据保留，实际状态写入本计划与现有UI record。

四组并行：Sequence/Structure量尺及标记；Variant表、图例及预测详情；Expression/IntAct/GenCC及context；概览、首页、共享排版与集成。先减少无效副行，再提升对象/结果/图例/单位和来源字号；不以全站缩放、统一大字号或叠加厚框代替排版。保留已有开合与切换动效、数据/筛选/单位/映射语义。

原位采用：普通信息14–15px，主要对象15–16px，图例/来源/表头13–14px，纯提示12px作为试排基线；用浅Slate组区、组标题和同级图标建立阅读顺序。最终取值以1470×837、1280×800实际表现决定。临床/GO/GenCC等来源类别不转为项目评分；0与缺失保持区别。

本批已完成实现、TypeScript/Vite构建、EGFR/AQP4及GenCC/IntAct的限定桌面检查，并发布至本地8000。真实CATVariant EGFR已截图对照；Motion/CSS开合、退出、返焦和reduce已复核，修复了深处滚动及锚点偏移导致导航高亮不准。代码、实际交互、发布及未覆盖B/D分支分别见[本批record](../../record/01_preview_optimization/20260922_ui_toolkit.md#文字层级信息引导与配色复核)。下一步是用户观感验收及有实际数据的剩余详情分支；不自动关闭全部审查项。公网仍关闭。

## 当前迭代：九条真实页面批注（2026-09-22）

上批原位控件、动效与本地发布后，用户继续验收提出以下九条改进。本批已完成代码实现、候选生产页面验证及8000本地发布复核，等待用户继续验收观感；5174同步保留。沿用页面模块顺序和科学规则，降低默认展开量、调整组件内部呈现及科学色表的视觉取值。实现、证据和限制见[九条批注交付记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#九条真实页面批注修订)。

| 批注 | 本轮决定与完成标准 |
| --- | --- |
| 1 来源选项过多 | Domains/PTM/Topology默认显示类别和已选摘要；点击展开完整来源，多选状态保持；独立说明入口再解释来源/方法，不在checkbox选择时强制打开说明 |
| 2 序列范围拖动 | 指针附近持续显示残基位置及当前起止范围；拖动、两端resize、键盘、取消和恢复均检查 |
| 3 数量配色 | 采用用户提供的冷→暖色彩，高数量用红；0/1/2–4/5/6/7–8/9+阈值不变；Sequence/Structure同量尺共用色表并明确红色为数量而非致病性 |
| 4 结构范围 | 局部重设计，指针附近显示残基字母/编号和映射状态，补精确起止输入；拖动仍只预览，松手提交，Escape恢复 |
| 5 清除按钮 | Variant分布选区有显著状态和Lucide重置图标；清除只影响当前范围，保留其他来源/工具筛选 |
| 6 组件风格/配色 | 概览的嵌套信息减少卡片框与顶部装饰线，保留网格及原信息；数据图多色承担科学含义，基础标签用稳定对比度 |
| 7 Expression引导 | 数据类型→数据库/collection/context，assay与pTPM/nTPM等单位进入准确说明；查现行数据键和官方方法，不以单位名称充当分类，不合并异质量尺 |
| 8 表达矩阵过长 | 默认只展示前10组并明确范围/总数，按需增加或展开全部/收起；完整数值保留，条形scale始终按原全集，不随预览变化 |
| 9 细胞图标签 | 文字与背景图形分层绘制，标签不继承图形淡化；加高对比底，键盘/hover与原标签证据入口继续可用 |

本轮仍用真实EGFR，并补AQP4缺失注释及表达缺失值案例。检查1470×837用户视口与1280×800；构建、浏览器真实操作、发布状态和Git记录回写现有UI record，不新增计划目录。

## 本地判断与采用方案

本地React/TypeScript/Vite此前使用普通CSS、自写共享ui.tsx、TanStack Table、Nightingale和Mol*，Lucide已经安装。样式经过多轮覆盖，颜色、边框和过渡有改进，但没有统一的控件来源和动态状态规范。基础库接入不等于所有55项体验目标完成；用一个运行预览和实际共用控件验证，再分模块迁移。

| 层次 | 采用 | 职责与边界 |
| --- | --- | --- |
| 通用组件 | [shadcn/ui官方registry](https://ui.shadcn.com/docs/installation/vite)，Radix primitives，new-york样式起点 | 组件源代码落在本项目；Button、Card、Dialog、Tooltip、Checkbox、Field先接入，后续按需增加。不安装Mantine或Tabler Admin整套页面框架 |
| UI配色 | [Radix Colors](https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale) | Slate背景/正文/边框＋真正的Blue主操作/链接/选中态；分类色限制在小图标、标签，科学色板独立维护；已在真实首页/蛋白页实施，验证状态见本批record |
| 主动效 | [Motion for React](https://motion.dev/docs/react) | 详情内容进入、选择反馈进入/退出；单个残基和热图格用轻CSS状态，不各建动画实例 |
| 图标 | [Lucide React](https://lucide.dev/guide/react)＋[Tabler Icons React](https://docs.tabler.io/icons/libraries/react) | Lucide为通用语汇，Tabler补充用户明确选择的三种；按组件具名导入，无运行时全库查表 |
| 设计协作 | Figma；React Bits保留可选参考 | 本轮不以Figma连接作为代码接入前置，不新增GSAP或React Bits依赖 |

工程采用Tailwind v4的theme/utilities，不启用全局Preflight；只对带data-slot的新增组件做基础重置。旧共享styles.css置于legacy cascade layer，其他已有科学视图样式仍保留。这样可以避免全局重置改变Nightingale、Mol*或原生表单。不是把所有旧CSS自动改写成Tailwind。若后续修改来源组件，应保留本地适配并通过CLI的diff检查升级。

## 用户选定图标逐项定位

统一入口：[icons.ts](../../../frontend/src/lib/icons.ts)。现有演示页曾展示12种唯一图标；新方案将其用于实际操作和模块入口，撤下用户流程中的图标展柜。混合库保持统一尺寸和线性风格。文字标签仍保留。

| 用户粘贴项 | 实际组件 | 本项目语义/落点 |
| --- | --- | --- |
| copy | Lucide Copy | 复制accession/variant ID；成功和失败反馈，不静默失败 |
| rotate-ccw（两次相同SVG） | Lucide RotateCcw | 清除/重置当前选区；重复项合并为一个组件 |
| brain（未指定标签） | Lucide Brain | 采用为Prediction入口；实际预测仍按原来源说明 |
| 通路 share-2 | Lucide Share2 | 通路/关系入口 |
| 统计学、频率 chart-no-axes-combined | Lucide ChartNoAxesCombined | 汇总统计；频率专项采用下面的柱形图标 |
| 数据收集 database | Lucide Database | 来源集合/数据概览 |
| network 通路（再次粘贴Database SVG） | 实际仍是Lucide Database | 记录此文字与图形不一致；不虚称Network图标。通路先用已明确的Share2，Database仍表示数据集合 |
| frequency chart-no-axes-column | Lucide ChartNoAxesColumn | Frequency入口 |
| Clinical microscope | Lucide Microscope | Clinical入口，保留临床来源名称 |
| atom（未指定标签） | Lucide Atom | 采用为结构/分子视图 |
| dna | Tabler IconDna2 | Sequence入口/区段操作 |
| select | Tabler IconAdjustments | 筛选与显示选项 |
| 注释、知识库 | Tabler IconLibrary | 注释/证据及知识库入口 |

用户链接的[Tabler Admin](https://tabler.io/admin-template)是整套管理模板；本轮实际采用的是其明确粘贴的Tabler Icons，不因此额外引入Bootstrap管理模板。所有命名与以上差异已保留，不默默替换用户素材。

## 当前范围：保留布局，融合组件与动效（2026-09-22最新确认）

**用户确认当前布局和信息展示基本可行，不需要完全重构；重点是在现有位置融入已选UI素材/组件，且必须优化动效。** 这替代此前代理提出的首页/结果页重排、移动导航、删除/合并整块内容及`/design-system`重定向方案。上述结构性方案未实施，现撤出近期计划。现有页面、模块顺序、信息分组、入口和数据契约作为基线。

允许的局部调整：字体、字重、颜色、边框、圆角、按钮高度、图标、组件内部间距，以及保持语义和状态的原位控件替换。一般替换不增加操作步骤；本轮用户明确要求的来源逐层展开、表达矩阵按需展开属于已授权例外，保留全部来源、字段及默认科学筛选。原有55项中已明确的科学与功能修复继续保留；不借视觉优化扩大改动范围。

### 页面与参考定位

- `/`为[真实首页](../../../frontend/src/components/HomePage.tsx)，`/protein/:accession`为[蛋白页](../../../frontend/src/App.tsx)，保留各自布局与展示顺序。
- `/design-system`为[组件样例页](../../../frontend/src/components/DesignSystemPreview.tsx)，不是实际科研首页。保留为局部组件比较入口，不自动重定向、不把样例统计搬进科研页；最终效果以真实页面验收。
- [CATVariant](https://catvariant.com/)及本地[视觉审查](../../../Web-research-reference-2026-09-20/docs/sites/catvariant/03-ui-visual-design.md)用于理解基础信息与多维科学色的平衡，不复制整站布局或统计。
- [VarCards2](http://www.genemed.tech/varcards2/#/index/home)此前网页读取403，视觉参考尚待补核；不阻塞已选组件的局部融合。

### 素材与组件如何决定

每个替换先明确“当前控件的问题→匹配的组件→保留的操作和信息→可见改善”。采用[shadcn官方组件](https://ui.shadcn.com/docs/components)作为通用控件来源，统一项目主题；现有专业viewer及科学图继续维护，避免套整页模板。优先复用已经接入的组件，未接入者按需安装，不先堆积依赖。

| 原位置/需求 | 采用方式 | 保留边界与验收 |
| --- | --- | --- |
| 按钮、复制、清除、分页 | 已接入Button＋Lucide/Tabler图标；统一hover/pressed/focus | 按钮位置、标签和行为不变；复制结果明确，清除可恢复 |
| 证据与记录详情 | 已接入Dialog、Tooltip；保留当前弹层模式 | 不擅自换成侧栏；检查内容滚动、Escape、关闭动效和触发点焦点返回 |
| 原有折叠内容 | 按场景用Accordion/Collapsible或完善现有Disclosure | 保留默认开合和多项同时展开规则；打开、关闭均有完整过渡 |
| 原有互斥模式/面板切换 | 需要时用Tabs或单选Toggle Group | 只有真正切换同一区域内容才用Tabs；页内锚点导航仍为链接，不更换展示模型 |
| 多来源/多注释选择 | 已接入Checkbox/Field；长选项列表按需用Popover/Combobox | 多选不变单选；保留数量、来源解释、已选项及清除；短列表不强制隐藏 |
| 帮助、evidence code解释 | Tooltip用于短解释；长内容复用可点击说明弹层 | hover之外可键盘/点击访问；文献链接不隐藏在难以操作的浮层里 |
| Sequence、PTM、热图、结构 | 保留现有科学组件，统一外围控件与轻量交互 | 维持坐标、图例、量尺与映射；不换成普通模板图表 |
| 生物学示意图、模块图标 | 沿用已有用户素材和已选图标；调尺寸、描边、局部交互 | 不随意替换科学内容；图标配文字，不改成纯图标入口 |

新增模板/素材选择标准：匹配现有交互、适合密集科研内容、可接入主题、键盘/焦点行为完整、无额外重依赖，外部素材核对许可与署名。Figma可用于局部状态/样式设计；React Bits仅在有明确落点时借鉴，不作为新增另一套动效运行时的理由。技术选型与常规适配由agent完成，无需用户逐项选参数。

## Radix颜色、排版与组件规范（现行实现）

维护入口仍为[design-system.css](../../../frontend/src/design-system.css)，组件复用shadcn、Lucide/Tabler与现有共享ui.tsx；不引入另一套UI框架。新增真实`@radix-ui/colors/blue.css`，**Blue不是把现有Indigo变量改名**。

| 语义变量/用途 | 目标值 | 约束 |
| --- | --- | --- |
| canvas / background | Slate1–2 | 明亮中性背景 |
| surface / card / popover | 白色 | 普通卡片不铺模块色 |
| text / foreground | Slate12 | 正文、标题、数据主值 |
| text-secondary / muted-foreground | Slate11 | 辅助信息保持可读，不降低整段opacity |
| border / border-strong | Slate6–7 / Slate8 | 1px浅边框，依用途区分非交互与输入框 |
| link / focus | Blue11 / Blue8 | 链接可辨识，键盘focus有完整轮廓 |
| primary / primary-hover | Blue11 / Blue12，白字 | 优先小字对比度；不机械套用9/10 |
| selection / selection-text | Blue3–5 / Blue12 | 全站交互状态一致，当前项另有下划线或轮廓 |
| category-icon | Violet11、Cyan11、Green11、Orange11、Pink11等既有类别色 | 模块身份用于小图标/局部标签；科学数据另有配色，不受此面积限制 |
| scientific colours | 各数据维度独立色表/色阶，按实际图例维护 | 可用于残基填充、轨道、标记、评分条和图表；不能被primary或模块主题色覆盖 |

依据[Radix官方用途说明](https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale)选择背景、状态、边框与文字阶位，再核对真实配对。已对本地3.0.0包的sRGB色值计算：白字/Blue9约3.26，白字/Blue10约3.63，不满足本轮普通小字4.5目标；白字/Blue11约4.77、Blue12约12.62，采用后者组合。Slate11/Slate2约5.65。仍需浏览器实际状态检查，不能把这些局部计算写成整站无障碍认证。

排版/尺寸规范（保持原有信息密度，具体取值按组件角色）：

- 首页保留原hero尺寸和600字重；结果对象名28px/700，主模块22px/650，Overview子卡18px/650，小标题14–17px/600；正文14–15px/400–450，行高1.5–1.65；辅助信息12–13px/400。不将整段正文加粗。
- 数量列与指标使用`font-variant-numeric: tabular-nums`；只有ID/坐标需要时使用等宽字体；表格数值右对齐，标签列左对齐。
- 间距采用4/8/12/16/24/32px；卡片半径8px，按钮/输入6px；常规按钮36px，紧凑按钮32px；操作图标16px，模块图标18–20px。
- 普通卡片不加阴影和顶部彩线；紧密信息用一个区块的行/列/分隔线表达。Dialog/Popover允许轻阴影，hover只做短色彩过渡，减少动效偏好仍生效。
- 图表色阶、临床分类、PTM标记、预测阈值等与UI主题分别维护，图例与单位局部可见。不为“更好看”改变阈值、统计口径或合并科学来源。

### 多维信息的色彩与字形分工（用户进一步澄清）

2026-09-22：用户强调CATVariant值得借鉴的是多色搭配对多维信息的组织能力，同时基础/背景信息保持统一风格。不能把上面的Slate＋Blue解读为全站单色，也不能将“少量分类色”扩大为压缩科学图中必要的类别。多色的数量由同时要回答的问题决定，不预设六色必须处处出现。

| 信息层 | 内容与视觉职责 | 强调方式 |
| --- | --- | --- |
| 基础身份 | 蛋白名、accession、物种、长度、版本 | 统一字体/中性色；研究对象靠位置与字号突出，标签常规字重、值中等字重；不逐字段铺彩底 |
| 背景与解释 | 功能描述、方法、来源说明、计数口径 | 与正文同字体，常规字重、稍小字号和稳定行距；Slate11保持可读，避免整段浅色或加粗 |
| 模块身份 | Sequence、Variant、Expression等入口 | 中性标题＋小面积类别图标，Overview子标题使用4%类别浅底；可帮助定位，但不决定该模块所有图表颜色 |
| 操作状态 | 搜索、展开、筛选、当前模块、当前残基/区段 | Blue主要操作；选区优先描边/括号/指示器，保留原数据填充色；focus和selected须能同时识别 |
| 科学证据 | 注释类别、数量、频率、评分、临床来源分类 | 在实际轨道/残基/图表内使用多色及局部图例；饱和度与面积服务于当前分析重点 |

Sequence browser / Full sequence atlas的目标分工：

- 残基背景一次表达当前选中的一个主量尺（如变异数或当前评分），相邻有序档位保持可判断的深浅/进阶关系；换模式同步更换图例、单位、方向说明。既有分箱和科学阈值不因视觉调整改变。
- Domain和Topology用独立轨道/区间边界表达类别，PTM用独立洋红圆点（类型模式保留原多类型色）；不让三类信息竞争同一格背景。重叠位点需仍能分别看出区间、PTM和数值档位。
- 默认PTM概览使用一个清晰标记色，点击进入类型/来源统计；PTM type模式才展开类型多色；PTM source模式按来源提供图例与筛选。保留用户已定的“默认简化、按需多维展开”。
- 当前选择使用外轮廓/区段括号加文字坐标，不覆盖其数值颜色；hover轻量放大时核对不会遮挡邻位点或丢失PTM标记。无数据与真实零分别表示。
- 序列与结构在**相同科学模式、相同量尺**下共用映射和图例含义；模块身份色不参与结构残基上色。来源不同或量尺不同则显式说明，不伪装可比较。

Variant browser的目标分工：

- Consequence为离散类别，使用可区分的分类色及名称；Variant数量和频率属于有序量，使用有方向的色阶/条长及单位，不能用随机彩虹暗示连续大小。
- Clinical保留来源原分类，用类别色＋完整标签表达；不把Clinical入口的玫红等同于“致病”。来源标签、证据等级、临床分类应处于不同位置，避免三个彩色标签同时抢占每行重点。
- Prediction按方法组组织浏览，组别图标可以多色；具体分数条必须保留工具名、范围/方向、缺失及匹配状态。不同工具的数值不因使用同色条就被当作同一标准，未授权时不统一归一化或重新划分阈值。
- 选中的consequence、临床类别或位点保持其数据颜色，额外用边框、勾选或文字显示筛选状态；清除操作始终可见。红绿色以文字/形状补充，不能仅靠色相区分。

科学色表维护时按语义命名，例如`variant-count`、`consequence`、`ptm-type`、`clinical-classification`、`prediction-score`；UI变量使用`surface/text/border/action/selection/category-icon`。这些是职责划分，不要求新增复杂主题框架。现有颜色常量先按实际使用核查再整理；Radix用于UI及适合的类别配色，定量科学渐变保留独立生成规则和阈值。

字体进一步约定：整个页面使用同一无衬线字体栈；序列字母与必要ID/坐标使用等宽字体，数值采用等宽数字。对象名600、模块标题600、字段标签400–500、正文400–450、关键值500–600；同一级标题跨模块同字号/字重，不因模块颜色不同而变化。不同时用大字号、粗体、亮色、彩底强调每一项；每个区块先明确一个主要阅读目标。

视觉验收补充：使用同时有变异背景、Domain/Topology边界、PTM及当前选区的真实位置检查叠加；切换到PTM type后核对图例；以真实Variant结果核对consequence/Clinical/Prediction各色的含义和筛选恢复。去掉分类色时仍能借助标签和形状理解状态；保留颜色时能更快区分维度。本轮已以EGFR T648验证变异底色、Pfam/UniProt边界、PTM标记和选中轮廓叠加，并核对PTM类型模式与AQP4缺失状态；具体证据及验证范围见[本批record](../../record/01_preview_optimization/20260922_ui_toolkit.md#原位组件与动效实施)。

## 动效方案：在现有操作上补齐状态连续性

主库继续使用[Motion](https://motion.dev/docs/react-animation)。现行[共享动效](../../../frontend/src/lib/motion.tsx)提供Reveal、保留子树的ContentTransition、开合成对且关闭即inert的CollapseRegion，以及SelectionFeedback。共享Disclosure已采用Radix Collapsible；Modal保留Radix焦点管理并在150ms退出完成后通知父组件卸载，业务跳转也沿同一关闭链路。模式控件使用单个指示器，残基和热图格继续使用CSS。

以下为现行交互规范与实际实现时长；库不强制这些参数。

| 操作 | 实现 | 关键约束 |
| --- | --- | --- |
| 按钮/图标hover与按下 | 120–150ms颜色/边框反馈，必要时不超过1px按下位移 | 普通文本与卡片不持续浮动；不改变布局尺寸 |
| 已有模式/标签切换 | 指示器180ms移动，内容180ms由0.65恢复至1（不重挂数据子树） | 查询/状态立即更新；保持滚动位置，不在旧数据上显示新标签；不同时控制同一节点的CSS与Motion变换 |
| 折叠打开/关闭 | 箭头旋转；短内容180ms高度＋透明度 | 进出成对；大表/长列表不全量高度动画；收起后不能tab到隐藏内容 |
| 详情弹层 | 遮罩淡入/淡出，面板150ms微缩放 | 退出结束再卸载；焦点管理沿用Radix，关闭后回原触发点；用户可立即操作 |
| Sequence→Variant选区反馈 | 状态条180ms进入/退出，选区边界立即响应 | 不跳动整页、不盖住数据色；清除时联动状态恢复 |
| 残基/PTM hover或focus | 约100–120ms描边、局部放大、注释浮层 | 轻CSS/已有viewer机制，避免每格挂Motion实例；核对叠加与遮挡 |
| 数据加载与更新 | 延迟响应时显示稳定占位/加载提示；完成后轻过渡 | 数值直接呈现真实值，不从0滚动计数；真实0、缺失与加载分别表示 |

图表颜色切换时保证当前图例与数据对应；不通过颜色渐变制造不存在的中间科学数值。数字、序列、长表不做逐字/逐行错峰入场。关键反馈可见而简短，不增加等待。沿用[减少动效支持](https://motion.dev/docs/react-accessibility)，偏好减少动效时移除位移/缩放、立即完成必要状态变化；[共享偏好hook](../../../frontend/src/lib/use-reduced-motion.ts)监听系统设置运行中变化，避免只在挂载时读取。

## 实施批次与验收目标

1. **代表控件原位优化：** 真实蛋白页的来源多选、一个证据弹层、一个折叠入口、模式切换和选区状态条。复用已装组件，先建立统一状态样式和进出动效，不重排整页。
2. **扩展共用组件：** 将通过验证的Button/Dialog/Disclosure/选择控件逐步用于其他原位置；保持文字、字段、默认值、选项和操作路径。
3. **科学视图局部反馈：** Sequence/PTM/Variant hover、选中、清除，沿用前文多维颜色分工及科学图例；大型渲染器不重新替换。
4. **桌面验证及本地交付：** 构建通过后检查1440×1000与1280×800下的真实页面，静态截图对照布局、实际点击核对动效；验证键盘focus、关闭返回、减少动效、筛选/选区不丢失、无溢出或新增明显卡顿。桌面通过前不恢复ngrok；手机全面验收继续延后。

视觉与动效验收分开：截图证明外观与布局保持，交互过程证明打开/关闭/切换/选择反馈。依赖安装、组件演示、HTTP200或构建成功都不能替代真实页面验收。本轮范围已明确并已实施；代码、本地发布和实际验收分别记录，不将开发页交互通过等同于生产发布或全部55项关闭。

## 接入产物与如何让agent使用

- [components.json](../../../frontend/components.json)：官方registry、Radix/new-york、Lucide及`@/`路径；新增组件在[components/ui](../../../frontend/src/components/ui/)，原[ui.tsx](../../../frontend/src/components/ui.tsx)保留兼容入口。
- [package.json](../../../frontend/package.json)/package-lock.json固定依赖，Vite接Tailwind，tsconfig与Vite同时配置别名；新包精确版本和验证见本批record。
- [旧预览组件](../../../frontend/src/components/DesignSystemPreview.tsx)当前仍挂到`/design-system`；最新范围保留路由作为组件比较入口，不再计划首页重定向。来源checkbox和区段从来不是科学数据查询。
- 共享Modal改用shadcn Dialog，保留可滚动大内容、标题、Escape/点击外侧关闭与触发点焦点返回；共享Pager采用Button；Variant详情Clinical/Frequency/Prediction入口采用选定语义图标。其余旧控件逐批迁移。

复现和增补（在`Web/frontend`执行；普通库不需要MCP插件）：

```bash
npm ci
npm run dev
npx shadcn@latest info --json
npx shadcn@latest search @shadcn -q popover
npx shadcn@latest docs popover
npx shadcn@latest add @shadcn/popover
npm run build
```

`npm ci`复现本项目锁定依赖；shadcn的latest命令用于后续查看/按需新增组件，不保证未来源码与本次相同。对已有组件先`add --dry-run`和`--diff`，不能直接覆盖本地修改。本轮CLI产生的裸`cn`导入已改到`@/lib/utils`，移除冗余cn包；以后新增也要检查别名和类型。

调用约定：

```tsx
import { Button } from '@/components/ui/button';
import { CopyIcon } from '@/lib/icons';
import { Reveal } from '@/lib/motion';
// copyAccession由业务层实现，并报告成功/失败。
<Reveal><Button variant="outline" onClick={copyAccession}>
  <CopyIcon data-icon="inline-start"/>Copy accession
</Button></Reveal>
```

用户后续只需提供“资源具体页面/组件名＋希望用于哪个位置＋期望交互”。Agent先查本地组件和官方docs，复用主题/图标/动效入口，再用真实数据检验。不要再次引入另一套组件主题或默认把用户给的SVG粘贴成独立不受控样式。

## 后续优化顺序与验收

1. 已在真实P00533原位实施并扩展共享控件；完整实施/交互证据、结构性能限制及生产发布状态由[交付记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#原位组件与动效实施)维护。
2. 筛选/来源：SQ-01/02、AT-07、EX-02、PP-01/02逐步改为Field/Checkbox、Popover或Combobox；保留完整数据选择语义及清除行为。
3. 详情/阅读：GO/Reactome/药理/Variant来源入口统一标签、Tooltip、Dialog/Sheet；页面底层关系和量纲不动。Clinical、Frequency、Prediction分组保持用户已定结构。
4. 选区连续性已补齐：Sequence→Variant→Structure状态反馈、清除、焦点返回及筛选保留。结构拖动仅预览，松手提交；继续关注大范围Mol*提交的渲染开销，不以帧率波动修改科学映射。
5. 科学图素材单独比较。Figma样稿及React Bits特定组件仍可后续提供；首页沿用现有结构，只做局部样式/组件优化，既有cell素材和科学图契约不因本轮主题改动被替换。

完成首批不等于全站视觉验收完成。整站控件与硬编码CSS仍需逐批迁移；科学图交互、桌面观感按实际页面检查，移动端仍延后。

2026-09-22补充交付：QTL人体底图采用Servier/Bioicons解剖SVG，圆点交互保留；简洁序列滑条及轨道虚线恢复贴近指针的Residue提示。[实际记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#人体导航素材与残基悬停编号)。

2026-09-22后续反馈已实施：Location说明折叠与来源预览、移除结构范围hover重复框、真实Chain/Focus入口、OpenMoji卡通导航（替代肌肉图）。AlphaGenome新增CDS/蛋白对应轨道仍仅讨论，未授权实施；[依据与边界](../../record/01_preview_optimization/20260922_ui_toolkit.md#location说明压缩链入口与卡通导航)。
