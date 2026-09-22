# 已选UI工具接入、原位优化与验证记录

2026-09-22。用户选择shadcn/ui、Motion、Radix Colors及粘贴的Lucide/Tabler图标，要求调研优化、修订计划并搭建使用。具体选择、图标歧义、组件/颜色/动效规则及后续顺序集中于[03方案](../../plan/01_preview_optimization/03_ui_toolkit.md)。本批未改变科学数据、API契约或公网暂停状态。

## 实际交付

- 在现有React/Vite项目接入Tailwind v4插件、`@/`别名及components.json，采用官方@shadcn、Radix/new-york、Lucide；CLI 4.21.0获取Button、Card、Dialog、Tooltip、Checkbox、Field及依赖Label/Separator，共8份组件源文件。逐个读取检查，修正CLI输出的裸cn导入，改用本地utils，并卸载冗余cn包。
- Radix Colors通过语义变量统一Slate/Indigo及模块辅助色；styles.css归入legacy层，字体网络import移至顶层；只引入Tailwind theme/utilities，对新增data-slot控件做最小reset，避免全局Preflight作用于已有科学viewer。
- MotionConfig及Reveal接入共享详情/折叠内容；预览页AnimatePresence支持选区提示进入和退出；共用Modal使用shadcn Dialog，保留大内容滚动、标题、Escape、外侧点击关闭和焦点返回；共享Pager换Button。
- 12个用户选定唯一图标在lib/icons.ts具名导出，Variant详情的Clinical/Frequency/Prediction入口已采用相应语义图标。其他全站图标迁移仍按方案推进；两次RotateCcw合并；network文字对应的Database SVG差异明确记录。
- `/design-system`懒加载预览展示图标、配色、多选、复制、选区清除和详情弹层。页面标记为交互样例，来源选择不调用科学查询或写数据库。Figma画布未创建、React Bits/GSAP及Mantine/Tabler Admin未安装。

核对依赖：Motion13.4.0、Radix Colors3.0.0、Tabler Icons3.47.0、Radix UI1.6.7、Tailwind及Vite插件4.3.3、tw-animate-css1.4.0；已有Lucide0.468.0继续使用。完整实际解析版本由package-lock.json维护，后续用npm ci复现。

## 验证与发布

1. TypeScript与Vite生产构建通过（8,440模块）。首次候选构建发现字体import嵌入legacy层的CSS警告，已移到顶层；最终构建无该警告。入口JS约964.07kB/gzip288.67kB、入口CSS279.02kB/gzip54.82kB，预览懒加载JS22.69kB/gzip8.01kB；这是本批大小，不是相对基线的增长测量。既有Mol*大资源仍独立。
2. 通过Playwright CLI在1440×1000桌面headless Chromium实际操作预览：Dialog打开、Escape关闭和焦点返回；OPM勾选后状态更新；选区进入/清除；授予浏览器剪贴板权限后核对复制内容为P00533；emulate reduced-motion后新选区无transform。开发环境的Motion减少动效提示是预期警告，无JavaScript错误。
3. 真实P00533页面打开Names & identifiers，验证Dialog宽度/视口边界、Escape与触发点焦点恢复；打开膜sequence viewer并关闭，页面可继续访问。页面截图已检查，未出现本批全局样式导致的明显布局破坏。未据此宣称所有3D渲染、嵌套详情或55项桌面路径都已验收。
4. 候选构建先写临时目录，验证后复制静态资源到frontend/dist，再替换index.html；保留旧静态资源供已有标签页读取。8000本地API health返回PostgreSQL只读ok，公网ngrok仍未启动。
5. 生产入口`http://127.0.0.1:8000/design-system`实际浏览器复核：组件资源加载、Dialog内Tab焦点、外侧点击关闭、触发点焦点恢复和选区反馈通过。不是只检查HTTP200。
6. 生产预览控制台0错误/0警告。定向检查11份现行文档、252处本地链接，均可定位；问题清单与方案55个ID仍一一对应。临时5174开发服务已停止，本地8000生产服务继续可用。

截图证据：[本地生产预览](../../../../output/playwright/ui-kit-production.png)、[P00533证据弹层](../../../../output/playwright/protein-evidence-dialog.png)、[P00533概览](../../../../output/playwright/protein-overview-kit.png)。截图按Playwright技能放在项目output/playwright，应用代码和方案仍由Web维护。

## 首批接入时的限制（后续进展见文末）

工具基础及共用控件已接入并本地发布，不等于整站重设计完成。部分模块仍有旧硬编码颜色和自写控件；native details收起仍即时，弹层整体退出也未统一交给Motion。后续按03方案迁移来源筛选、证据入口和sequence→variant反馈，避免安装库后继续各处写不同风格。手机验收仍延后；Figma工具可用性不阻塞当前代码。未重新运行数据流程或全库扫描。


## 多色配色追加优化

2026-09-22。根据用户最新要求，将首批偏单一Indigo的视觉方案改为CATVariant启发的明亮多色模块体系；当前分工和agent调用约定维护于[03方案](../../plan/01_preview_optimization/03_ui_toolkit.md#radix颜色规则与维护位置)。

- 新增已安装Radix Colors中的Cyan、Orange、Pink样式导入，连同Indigo、Violet、Green形成六组模块色，Slate继续用于正文/中性表面。没有新增npm包。
- design-system.css集中映射常态、hover、selected、边框、强调、文字和图标前景色；修正旧统一蓝色active覆盖。真实蛋白页的导航、概览分区、Sequence/Structure与Context模块标题采用同一映射；Variant面板色从amber改为purple，与导航一致。科学图层、阈值和数据不变。
- 预览页新增六组可切换选中态的模块色按钮、六组12级色条、彩色图标及卡片标题，保留来源勾选/复制/弹层/选区操作。它仍为明确标注的UI样例。
- TypeScript及Vite生产构建通过（8,440模块）；最终入口CSS286.84kB/gzip56.66kB，预览JS24.62kB/gzip8.51kB。候选产物验证后发布本地8000服务，旧assets保留。
- 1440×1000桌面浏览器验证：六组按钮aria-pressed切换、选区显示/清除、Dialog Escape关闭与异步焦点返回通过；真实P00533页多色导航、Sequence选中态、Expression标题实际检查通过；预览与蛋白页均无横向溢出。应用内Browser连接无可用实例，实际用Playwright CLI headless Chromium核对；未声称直接操作了用户标签页。
- 发布后再次检查8000预览：选中态及紫色选区反馈正常，控制台0错误/0警告；P00533的Expression绿色边框与Variant紫色边框均为预期的Radix9，API health为PostgreSQL只读ok。临时5174开发服务已停止。
- 使用安装包的sRGB色值计算：六组12级文字/5级选中底对比度8.21–9.96；全局按钮白字/Indigo9为5.21、hover为6.02；模块图标前景/9级实底最低3.90。此为本批指定配对，不是整站或P3色域的无障碍认证。实底彩色图标旁保留深色文字标签。

截图：[多色预览](../../../../output/playwright/radix-multicolor-preview.png)、[真实P00533概览](../../../../output/playwright/radix-protein-overview.png)。后续仍需逐批迁移旧控件及来源标签；本批不改动科学图例或科研数据，不扩大为整站视觉验收。


## 科研页面重构策划与再次关闭公网

2026-09-22 04:11:46 UTC（香港12:11:46）核对。用户澄清“先关闭，修复完毕再公开”，替代上一条含糊的公网启动表述。此前进程检查发现已有`ngrok http 127.0.0.1:8000`（PID2107897）；本轮未启动或重启ngrok，已向该进程发送TERM。复核无ngrok进程、4040管理端口未监听；本地8000 `/api/health`返回PostgreSQL只读ok。保留`1147810.memVar` screen会话和website/ngrok窗口，未停止本地网站或数据库。

本轮根据用户完整反馈审查App、HomePage、HomeEvidence、Overview、design-system.css及现有API字段，将[03当前方案](../../plan/01_preview_optimization/03_ui_toolkit.md#当前页面定位与问题分析2026-09-22最新修订)改为科研任务优先的Slate＋Blue结构。四项问题逐条定位，分别规定首页和结果页顺序、真实指标/来源/时间语义、紧凑导航、配色/文字/数字/尺寸规范、实施批次和验收目标。上一版六色大面积处理被替代，历史记录保留。

CATVariant首页可读取，并结合既有本地视觉审查；VarCards2读取403，未声称完成其视觉复核。Browser连接此前返回No browser is available且实例列表为空；公网开放不是修复浏览器工具连接的必要条件，不再为此启动ngrok。

已核对现有catalog/statistics的模块快照时间、来源版本与蛋白overview身份字段，明确模块build时间不等于单条蛋白上游更新时间。对已安装Radix Colors3.0.0的Blue/Slate指定配对进行sRGB对比度计算，结果写入03方案。**本轮只更新策划和运行状态，未修改前端代码、重建dist或执行科学数据流程；新版页面尚未实施/验收。**


同日进一步澄清：用户要求学习CATVariant用颜色组织多维信息的能力，基础/背景信息保持统一字体、字重和大小。已直接修订03方案：Slate＋Blue仅约束基础界面与通用交互；Sequence/Variant的数据填充、轨道、PTM、分类及评分仍按各自科学含义采用多色，选区另以轮廓表示。补充同模式序列—结构色义一致、默认PTM简化/类型模式多色、不同工具分数量尺不可混同及叠加验收要求。本次为策划澄清，未修改代码、科学规则或公网状态。


同日用户进一步收窄范围：当前布局和信息展示基本满意，要求融入已选UI素材/组件并切实优化动效，不大幅改布局或信息顺序。03方案已直接撤回首页/结果页重排及/design-system重定向，改为原位控件替换、状态样式及进出动效优化；补充组件选择表、动效落点/时长建议、实际已接入与尚缺部分及桌面验收路径。旧结构性建议未实施；本次仅改计划与索引，未修改前端或公网状态。


## 原位组件与动效实施

2026-09-22。用户授权继续实施、自主决定常规设计参数并补齐Git追踪。本节替代前文“新版尚未实施”的当前状态；前文保留为历史批次。以真实首页、P00533/EGFR为主例，P55087/AQP4补充缺失注释案例；没有更改数据收录、代表转录本、映射门槛、评分尺度、分类阈值或服务数据。

### 实际修改与设计判断

- **基础界面：** `design-system.css`导入真正的Radix Blue；白色/Slate阅读表面，统一模块标题、字段标签和正文字重。去掉普通卡片/导航同时出现的彩底、彩框、顶部彩线和阴影；模块小图标保留辅助色，科学色板独立。沿用首页背景图、区域顺序、7栏证据入口与膜分类网格，未引入整页模板。
- **组件：** 复用shadcn Button/Dialog/Tooltip/Checkbox；补Tabs、Radix Collapsible和单选ModeToggleGroup。首页7层证据换为带键盘导航的Tabs；分类展开/关闭仍在原处。Sequence来源、轨道多选和Display options保留选项/默认值；Variant预测选择器与Structure模式栏沿用原字段与数据视图。长帮助由原生dialog统一到Radix，保留嵌套使用。
- **进出与切换：** Button的120–150ms hover/pressed/focus；Dialog及遮罩150ms进入/退出，关闭完毕才卸载，修复退出尾帧闪回。业务按钮的Open filtered catalog/View in structure/PTM type跳转也先走退出链路。Disclosure/首页分类以180ms高度＋透明度成对开合，闭态立即inert，子树不卸载；模式指示器和内容180ms反馈，不清空筛选、不重新挂载viewer。选区状态条180ms进入/清除；Compact PTM/Variant单个注释浮层120ms进入/退出，格子只用CSS。
- **科学叠加：** Atlas选中/hover不再用强制蓝底覆盖变异或PTM色；Domain/Topology边界、独立PTM菱形和Blue选择轮廓可共存。默认PTM概览简化，类型模式展开多色。缺失数量或未知上界用“—”，不伪造零。原始变异consequence/临床分类/工具分数及量尺说明保留。
- **联动与性能：** 打开残基目录只替换位点区间与互斥搜索/分页参数，保留来源、consequence、频率、转录本与预测工具。Structure以蓝色ball-and-stick表达选区，主表示保留当前科学色；拖动只预览轮廓、松手提交，Escape恢复旧范围。连续映射区间仅在链、canonical坐标、author坐标均连续且无插入码时合并查询；不跨缺口。相同范围重复选择不重建表示；同量尺选择/清除保留颜色，不再重复绘制全长颜色。App中不依赖残基的模块memo化。
- **可访问性：** Dialog涵盖X/Escape/遮罩关闭、Tab循环与返回原触发点，包括SVG图表标记；关闭折叠不再可Tab进入。共享`useReducedMotion`监听系统偏好实时变化，不必刷新，不通过重挂应用/科学viewer实现。无逐字动画、虚假数字滚动或持续弹跳。

[CATVariant](https://catvariant.com/)首页已在本机Chromium实际打开并检查截图；借鉴明亮阅读层级及局部多色信息组织，未复制代码、图像或连续打字效果。VarCards2本次未补做视觉复核，既有403不能当作已看过页面。新增Tabs源代码来自shadcn官方registry，既有依赖继续复用；没有新增npm依赖或下载不明许可图片。[THIRD_PARTY_NOTICES](../../../frontend/public/THIRD_PARTY_NOTICES.txt)维护shadcn/Radix/Motion/Lucide/Tabler许可与署名。

### 实际交互与外观证据

应用内Browser返回“No browser is available”，实例列表为空；采用独立本机Playwright/Chromium访问127.0.0.1，未连接用户标签页、未为浏览器开公网。1440×1000与1280×800按下列流程实测，截图逐张查看，动效另以实际操作和requestAnimationFrame中间状态验证。

| 范围 | 已验证结果 | 证据 |
| --- | --- | --- |
| 首页 | 7层标签位置/计数单位保留；Predictions→Expression方向键切换；分类展开/关闭且焦点回Integral；Search键盘focus为3px Blue轮廓；1280无横向溢出；同页面切reduce后标签与折叠0动画 | [1280截图](../../../output/playwright/home-1280.png)、[1440截图](../../../output/playwright/home-1440.png) |
| EGFR选区 | T648的变异背景rgb(185,212,255)、Domain/Topology边界和PTM标记同时保留；证据显示2 mapped variants/1 PTM/4 features。Escape回648；clear清除Sequence/Variant/Structure反馈。ClinVar筛选后Open filtered catalog仍为ClinVar、区间648–648，关闭后再定位Structure | [证据弹层](../../../output/playwright/egfr-evidence-candidate.png)、[概览](../../../output/playwright/egfr-overview-1440.png) |
| 来源/模式/注释 | Display options勾选、Escape、再开状态保留；Atlas PTM切换实测内容opacity0.65→1/指示器移动；Compact PTM/Variant hover浮层出现与移出关闭；PTM summary退出再切类型模式 | [Sequence QA](../../../output/playwright/sequence-controls-qa.json) |
| 共享弹层/折叠 | Names的X/Escape/遮罩均关闭并返焦；Prediction筛选搜索/勾选、折叠进退及Apply保存；嵌套Help只关闭顶层。退出opacity1→0、尾帧保持0，折叠height0↔196.7，关闭即inert；SVG g触发点也返焦。运行中reduce变化保留AlphaMissense筛选和勾选，恢复偏好后动效恢复 | [共享QA](../../../output/playwright/shared-controls-qa.json)、[折叠](../../../output/playwright/shared-prediction-disclosure.png)、[嵌套Help](../../../output/playwright/shared-nested-help.png) |
| AQP4缺失案例 | 323aa；Functional无注释；145残基缺少Secondary，M1灰色且显示No secondary structure annotation；PTM无标记时显示No mapped PTM，未替换为真零。取消GlyGen→切模式→返回保留；选择/清除/Escape返焦通过，1280无溢出。API频率缺失113与真实零4保持区别 | [缺失Secondary](../../../output/playwright/memvar-p55087-secondary-1280.png)、[缺失PTM](../../../output/playwright/memvar-p55087-ptm-1280.png)、[QA](../../../output/playwright/sequence-controls-qa.json) |
| Structure | WebGL实际出图；Variant/JSD/PTM切换、蓝棒选区及clear保留主色、canvas不变；来源勾选保留；拖选93–416取消回749。完整1–1210选区映射1210/1210，PTM129位点颜色保留；Clear图标已修正为16px | [结构QA](../../../output/playwright/structure-controls-qa.json) |

### 构建、发布与版本追踪

- 最终候选`npm run build -- --outDir dist-ui-candidate`通过TypeScript与Vite（8,444模块），没有构建警告。入口JS1,011.19kB/gzip304.43kB；入口CSS303.55kB/gzip59.05kB；Sequence JS74.45kB、Structure JS19.11kB；既有Mol*插件6,098.17kB独立加载。这是本次产物大小，不是完整包性能评分。
- 候选生产服务4174通过后，将资源复制到dist并最后原子替换index.html；旧assets保留供已有标签页读取。8000已发布`index-BDTkvVRq.js`/`index-BA-PZZhj.css`。实际发布入口复核首页标签与分类开合、EGFR Names/残基弹层Escape返焦/清除、AQP4缺失Secondary及1280无溢出，通过；本次发布smoke控制台0错误/0警告。完整3D操作的GPU警告另见下文，不由smoke结果推断消失。[发布QA](../../../output/playwright/ui-published-qa.json)。5174保留供用户同步验收，4174完成后关闭。8000健康检查为PostgreSQL只读ok；无ngrok进程、4040无监听。
- Web独立Git仓库的`e27cad7`是开始追踪时的在途快照，已包含本轮部分改动，不能当作完整优化前基线。原位组件、主题、动效和许可实现提交为`8fa269d`；本节及索引验证记录随后独立提交；没有remote/push。数据、环境文件、依赖目录、构建和浏览器缓存不纳入源码提交。6份本轮现行文档的197个本地链接均存在；`git diff --check`通过。许可文件随public静态资源发布，8000返回text/plain。

### 限制与保留事项

- 软件WebGL环境有Mol* ReadPixels性能warning，非JavaScript错误；减少动效开发提示属预期。热更替换hook时旧tab曾有Hook顺序暂态错误，刷新后重新验证；最终发布必须以全新加载控制台为准。
- 拖动预览/取消及重复相同选择约16.8ms帧间隔；一次性完整3D范围提交约922ms，仍有约283ms主线程空档。同一Chromium、1280×800、Variant count模式交替3轮比较旧8000与候选4174：最大帧间隔中位数，单残基316.7→183.4ms、重复选择300→16.8ms、清除350→266.7ms；两版首轮选择均约1133ms。没有观察到新增性能回归，但不是稳定60fps证明。完整数据及生产结构截图见[候选性能QA](../../../output/playwright/structure-prod-candidate-qa.json)和[蓝棒选区](../../../output/playwright/structure-prod-selected-final.png)。
- 本轮不关闭历史55项全部问题；Figma画布未交付，整站旧控件逐处完全迁移并非本轮前置；手机全面验收继续延后。公开发布未执行，ngrok保持关闭。没有重跑科学数据流程。

## 九条真实页面批注修订

2026-09-22。用户继续检查真实EGFR页面后提出九条批注，本节记录后续实际交付，替代上批对应视觉取值。分工为Sequence来源/范围、Variant与Structure、Expression、概览/集成四组。保持Overview → Sequence → Structure → Variants → Expression → QTL → AlphaGenome → Interactions → Diseases顺序；没有修改API、数据规则、收录、来源整合、代表转录本或映射语义。

### 原位修改及动效

| 批注 | 已实现内容 |
| --- | --- |
| 1 来源选项展开过多 | Sequence默认三个Radix Popover触发项，显示Domains/PTM/Topology与已选摘要。展开保留完整来源checkbox及计数；独立Details再展开来源、方法、证据类型及实际记录ID，勾选不强制展开说明。Popover进退、详情高度过渡和Escape返焦落实 |
| 2 序列拖动无编号 | 单个轻量提示层显示指针残基、范围和长度；拖选与两端resize实时反馈，松手应用，Escape取消恢复，方向键/Shift/Home/End可调整，双击恢复全长。没有给每个残基挂Motion实例 |
| 3 数量色阶 | 保持0/1/2–4/5/6/7–8/9+原分箱，依次采用白色、#7b95c6、#49c2d9、#a2c986、#fded95、#f59c7c、#c85e62；深色文字。Sequence/Structure共用sequence-model色表；灰色仍为缺失，明确红色表示数量多，不代表致病性。临床类别颜色/名称未改变 |
| 4 结构选区 | 同一位置补Start/End精确输入、坐标刻度、指针附近残基字母/编号、链映射和范围读数。拖动只预览、释放提交；Escape恢复、无效输入保留原选区；Clear使用Lucide并回焦slider；沿用同一Mol* canvas与既有优化 |
| 5 清除按钮 | Variant distribution增加紧邻图例的选区状态条和RotateCcw Clear range按钮，保留进出反馈；清除只移除范围，保留ClinVar等其他筛选，键盘焦点返回分布图 |
| 6 概览风格 | 保留原网格和全部来源指标，膜证据四列改用分隔线，功能入口减少嵌套卡框；去掉重复彩线和图标底块。基础标签统一Slate，来源小圆点及科学数据继续用类别色 |
| 7 Expression引导 | 改为RNA/Protein → 数据库 → tissue/cell/cancer context入口，保留全部14个collection。测量方法和记录数仍在按钮中，单位放入独立解释及当前选择信息；不再把pTPM/nTPM当分类。模式切换沿用共享指示器和短内容过渡 |
| 8 表达矩阵过长 | 默认前10组，支持追加10组/全部/收起，始终显示当前数与总数；图表尺度按完整collection计算，原始数据顺序和详情保留。组详情开合采用CollapseRegion，退出立即inert，完成后再恢复列宽，避免关闭时高度反增；收起列表后焦点返回标题 |
| 9 细胞图标签 | 先绘背景形状，再绘全部12个独立标签；标签不继承形状淡化，白底/深字、无注释虚线边框。hover/focus只强调对应形状，Enter/Space查看原始标签；未注释不被表述为生物学不存在。原映射、来源计数和适用对象保留 |

单位说明核对了[HPA RNA方法](https://www.proteinatlas.org/humanproteome/tissue/method/transcriptomics)和[HPA单细胞方法](https://www.proteinatlas.org/humanproteome/single%2Bcell/single%2Bcell%2Btype/method)：pTPM为protein-coding abundance按每样本百万归一，nTPM增加跨样本TMM归一，nCPM为单细胞TMM-normalized protein-coding CPM。CAGE标签、蛋白强度/log fold change、IHC分类继续分开。[GTEx来源入口](https://gtexportal.org/home/downloads/adult-gtex/overview)是SPA，68组context含义另结合已有GTEx来源核验及实际API确认，未称为68种独立组织。本批没有引入新依赖或外部图形素材，继续已有Lucide及许可文件。

### 实际验证证据

- **Sequence：** EGFR默认三个来源入口、Topology全部28选项保留；Hmmtop说明实际显示HTP:314、seq:9872。勾选与Details独立；Escape回Topology。拖303–666显示Residue666/364aa；resize到787后取消回666，Shift+Right到676，双击回1–1210。AQP4默认dbPTM、GlyGen选择关闭再开保留。普通及动态减少动效模式均实测。[QA](../../../output/playwright/sequence-progressive-qa.json)、[收敛](../../../output/playwright/sequence-feedback-collapsed.png)、[来源说明](../../../output/playwright/sequence-feedback-source-details.png)、[拖动截图](../../../output/playwright/sequence-feedback-range-drag.png)。
- **Structure/Variant：** 输入745–750显示K745–A750、6/6映射；750–1211错误不覆盖旧选择；拖93–231为预览，Escape恢复原6残基且canvas不变。Variant选中后Clear保留ClinVar，焦点回分布图，Structure清除回slider。1280减少动效下仍可用、无根溢出。[QA](../../../output/playwright/feedback-structure-variant-qa.json)、[结构读数](../../../output/playwright/feedback-structure-range-tooltip.png)、[候选清除条](../../../output/playwright/feedback-candidate-clear.png)、[新数量色表](../../../output/playwright/feedback-candidate-atlas.png)。
- **Expression：** GTEx 10→20→68→10，首条宽度始终84.1535%；HPA nTPM/pTPM切换恢复10组；1,206细胞系全部仍可展开。原始癌症样本1.3979 pTPM弹窗Escape返焦；EGFR DVP的3个缺失仍标Missing，IHC分类图例展开前后相同；其他Variant转录本与800–850区间query保留。组详情实测height 0→424→0，关闭即inert；reduce时无动画。[QA](../../../output/playwright/expression-context-qa.json)、[1470导航](../../../output/playwright/expression-navigation-1470.png)、[精简矩阵](../../../output/playwright/expression-matrix-compact.png)、[缺失案例](../../../output/playwright/expression-protein-missing.png)。
- **概览/图示：** 1470×837与1280×800实测12标签全部opacity1、12px字；所有标签包围框无交叠、页面无横向溢出。Nucleus键盘选择仍展开两条UniProt原标签并保留焦点。已人工检查截图。[细胞图](../../../output/playwright/feedback-cell-map.png)、[1280](../../../output/playwright/feedback-cell-map-1280.png)、[发布概览](../../../output/playwright/feedback-published-overview.png)。
- **候选生产：** 4174重复EGFR来源/Details/Escape、303–666取消、结构745–750应用/清除、共享数量图例、Expression10→68→10、Variant清除保留ClinVar及reduce动画为0。首页1280搜索AQP4唯一命中并进入P55087；其GTEx默认10/68，DVP21/27缺失、药理无记录说明保留；页面无横向溢出。[集成及发布QA](../../../output/playwright/feedback-integration-qa.json)、[首页/AQP4 QA](../../../output/playwright/feedback-candidate-secondary-qa.json)。

### 构建、发布与当前状态

- `tsc --noEmit -p tsconfig.json`和`npm run build -- --outDir dist-ui-candidate`通过；8,444模块，无构建警告。入口JS1,020.82kB/gzip307.45kB、CSS306.68kB/gzip59.58kB；Sequence77.17kB、Structure22.27kB，Mol*6,098.17kB仍独立加载。这不是整站性能认证。
- 候选通过后复制静态资源、最后原子替换dist/index.html，保留旧assets。8000实际加载`index-C6yj8GYJ.js`及`index-Cn0FPuMW.css`；发布后重新操作EGFR来源退出返焦、结构6残基应用/清除，核对10组表达、12标签与1470无溢出，本次复核0错误/0警告。候选完整3D检查另有4条ReadPixels GPU提示，不据此声称消除既有软件WebGL开销。
- 代码提交`f328374`，本节及现行索引另行提交；没有remote/push。6份当前文档的217个本地链接均存在，`git diff --check`通过。8000健康为PostgreSQL只读ok，5174保留供用户继续验收。4174候选验证后关闭；ngrok未运行、4040未监听。无科学数据重跑或重新入库。
- **状态区分：** 九条反馈对应代码已实现、本地8000已发布、上述实际交互已检查；用户审美/使用验收仍继续，未关闭所有55项。手机全面检查、Figma画布与3D首次/大范围提交性能限制继续保留；本批未重做无关全量性能试验。


## 文字层级、信息引导与配色复核

2026-09-22。用户要求继续落实[文字与信息审查](../../research/01_preview_optimization/02_typography_information_audit.md)，并给出CATVariant卡片、筛选区参考。本节记录本批实施；审查文件的“仅审查”描述属于该文件作者的审查范围，不是本轮禁止实现。继续四组分工，保留原模块顺序、主要操作和数据含义。

### 实现与设计取舍

- **统一基础层级：** 身份信息在原六列中加入同级Lucide图标与浅Slate底；普通Fields用一致圆点和标签；模块标题、控件组与数据内容以浅表面和间距区分。身份值15px、正文14–15px、通用表格14px/表头13px；实页发现legacy末尾旧规则仍覆盖表格，已修正。去掉普通表头全大写，不用全站缩放。首页原示例卡补实际UniProt标识行，搜索结果加基因/标识/长度图标，单页结果不再展示无用翻页按钮。
- **Sequence/Structure：** 数量分箱仍为0/1/2–4/5/6/7–8/9+；新色为白、`#bdcce0`、`#84c4ac`、`#c8d990`、`#fded95`、`#f59c7c`、`#c85e62`。1与2–4分成灰蓝/青绿，也避免1与缺失灰混同。PTM存在用Slate菱形及白色隔离边，PTM类型模式保留各类型色。主量尺与边界/标记分组，图例13–14px；0、缺失、选中轮廓与单位保留，Sequence/Structure共用色表。
- **状态与操作命名：** 明确Visible window、Shared residue focus、Structure range、Catalog range filter；恢复相机叫Reset camera；清除写明对象。共享焦点不被描述成目录已筛选；窗口变化不新增范围联动。Variant的Clear filters & residue说明保留人群和预测列；范围清除同步清掉已失效的范围搜索输入。集成时复现深处滚动后导航仍高亮Overview，改为每帧最多测量九个模块边界，并监听模块尺寸/挂载变化，保持当前模块判定准确。
- **Variant：** 原位分Variant selection与Transcript & population两个控件组；评分仍保留各工具独立方向和量尺，端点说明移到列头，移除No source category空副行、固定人群逐格重复文字。Toolkit保留61字段及原默认，弱化覆盖计数，机器字段/来源说明按需展开。临床领域、结论和review分层；ΔΔG原单位/符号与转录本匹配限制保留。
- **Expression/Context：** 数据类型→数据库→context引导保持，context和值14px、方法/单位12px；原10组预览保留，源值重复副行与每行外框收敛，全集合最大值/最大绝对值缩放说明直接可见。GenCC逐条列疾病、分类、遗传和提交机构；IntAct把参与者类型/物种贴近名称，方法与interaction类别分层，保留重复源记录及阴性分支。ClinVar、AlphaGenome提高必要context/来源/单位字号。
- **概览与详情：** GO、Reactome证据名称可读；IEA明确Automatic并保留原代码，不转为质量等级。GO false布尔占位不逐项展示，真实NOT/obsolete仍保留。膜来源、功能入口、通路和药理预览提高关键文字，药理None类型以—及解释表示。确定单页的共享Pager只显示实际条数，多页分页继续保留。

本批唯一API改动是`evidence_disease.py`列表投影增加数据库已有的`submitter`；没有新推断、合并、数据构建或入库。EGFR GenCC修改前后9条记录的全部旧字段、顺序、游标一致；7家原提交机构、5个实际报告链接。分类解释核对[GenCC官方说明](https://clinicalgenome.org/docs/gencc/)、[ClinGen定义](https://www.clinicalgenome.org/docs/gene-disease-validity-classification-information/)；Supportive独立保留，不设项目等级或排序。IEA参照[GO官方证据分类](https://geneontology.org/docs/guide-go-evidence-codes/)。没有引入新依赖或外部图片；继续已接入的shadcn/Radix、Motion及已有图标许可。

### CATVariant实际比对

应用内Browser仍返回`No browser is available`且实例列表为空；按既有授权用独立本机Playwright访问本地及参考站，没有开启公网。实际打开[CATVariant EGFR](https://catvariant.com/genes/EGFR)，取得[参考筛选区](../../../output/playwright/typography-catvariant-egfr-filters.png)，并对照用户给定首页卡片。此为本主任务真实渲染证据，补足审查文档第9节“外站仅文字读取”的限制，不反写该次历史审查结论。

| 比对项 | 本轮采用 | 有意保留的差异 |
| --- | --- | --- |
| 卡片信息顺序 | 对象名优先，来源/标识同行图标，次级说明常规字重 | 首页仍为原三张研究案例，不补造更新时间或来源没有的变异总数 |
| 筛选区 | 明确组标题、对齐字段、浅Slate控件区、Lucide语义图标 | 保留memVar代表转录本/人群及科研筛选，不复制CATVariant的证据数量或分类体系 |
| 图与表 | 类别图例紧邻数据，单位和工具方向持续可见 | 保留密集序列、Mol*及表格局部横向滚动，不照搬大卡片尺寸；参考站实测Sort and filter标题14px，不把参考字号当全站硬规则 |
| 背景与强调 | 白色数据表面、浅中性分组，Blue聚焦操作 | 科学数量/临床/评分各自编码，模块色仅辅助定位 |

### 实际检查与覆盖边界

- **概览/首页：** 1470与1280宽度检查，无文档横向溢出。身份字段实测13px标签/15px值；Names弹层13px表头/14px记录，Escape回Names入口；GO 20条/页可进入第2页，嵌套详情退出后仍回原列表；Reactome证据名称与来源可见，弹层无溢出。首页AQP4搜索仅1条结果，保留323aa与P55087。[概览](../../../output/playwright/typography-overview-after-1470.png)、[1280](../../../output/playwright/typography-overview-1280.png)、[首页](../../../output/playwright/typography-home-examples.png)、[详情](../../../output/playwright/typography-identity-dialog.png)。
- **Sequence：** EGFR来源28项、默认UniProt保留；303–666拖动/取消，键盘及恢复；T648类型色、证据表及说明开合；Structure745–750映射6/6。AQP4 M1 secondary缺失灰与变异数0白色有别；窗口100–200不改URL，恢复全序列保留结构150–155局部范围及共享T155焦点；clear按其作用域清除。[QA](../../../output/playwright/typography-sequence-qa.json)、[最终图例](../../../output/playwright/typography-sequence-egfr-atlas-1470.png)。该组截图高度为1000/900，root集成另用837/800，不混称同一viewport。
- **Variant：** 1470/1280字号、工具删选/Default/折叠、弹层Escape、范围清除返焦、reduce通过；SIFT真0、AF0与缺失、L858R三领域断言及各自review、ThermoMPNN−0.0336 kcal/mol可读；Clear filters & residue保留afr和四预测列，独立范围/焦点清除不相互覆盖。[QA](../../../output/playwright/typography-variant-qa.json)、[原位筛选与表格](../../../output/playwright/typography-variants-comparison.png)。
- **Context：** GenCC9条断言/7机构/5链接；IntAct小分子与chick/mouse物种明确、重复行保留；Expression10→20→10收起返焦，HPA bone marrow真实0.0 nTPM与详情Escape通过。ClinVar RCV000899512.9/SCV001043787.6的提交者、review及日期保留；AlphaGenome context14px、预测身份/信号说明保留。1470/1280无根溢出。[QA与逐项状态](../../../output/playwright/typography-context-qa.json)、[GenCC](../../../output/playwright/typography-context-gencc-1470.png)、[表达导航](../../../output/playwright/typography-context-expression-nav-1470.png)。

审查覆盖按真实状态保留：B01–B07/D01–D03涉及共享排版与部分概览详情；Rhea side_order原始含义、药理原始与转换量尺的完整重分组未在本轮改变。B09–B12/D05–D06有代表残基验证；B08/B13–B15/D04的DeepTMHMM、结构接触、PeSTo/SPPIDER详情没有穷举。B16/D07–D11主路径已测，未知review/未匹配预测分支未新造样例。B17/D12的QTL详情为代码审查，极小P值风险未复现，不擅改格式。B18/B21及B23/D13–D16覆盖范围见Context QA；B19/B20/B22/D15/D17的IntAct mutation、PTMD、HPO频率与dosage详细层级未全面修订/验收。B24/D18的junction/contact-map和B25版本文档未逐分支验收。U系列窗口/焦点/范围命名及主路径开合已核，移动端全面验收仍延后。以上不是55项或全部审查项关闭。

### 本批构建与发布

- 最终`npm run build -- --outDir dist-ui-candidate`通过TypeScript及Vite，8,444模块，无构建警告；入口JS1,033.25kB/gzip310.72kB、CSS327.01kB/gzip62.55kB；Sequence78.17kB、Structure22.38kB。既有Mol*独立6,098.17kB，不据此宣称整站性能认证。
- 4174候选实测Dialog进入/退出各150ms并Escape返焦、Topology28项/Escape、Structure745–750与独立清除、Variant清范围保留ClinVar、Expression10→20→10及返焦；reduce来源popover动画none/活动动画0。1470×837无根溢出。修复导航后，再测1280×800首页搜索AQP4、窗口100–200不改URL、缺失secondary图例和模块跳转。[集成QA](../../../output/playwright/typography-integration-qa.json)。早期Popover测试选择器错误已纠正；导航停在旧模块则是实际应用问题，修复后另行重建和验证。
- 复制候选资源后最后原子替换dist/index.html，保留旧assets。8000现加载`index-Czzd91lX.js`/`index-DjuHuAYw.css`，实际发布页再次核对七档色、15px身份值、GenCC9条及提交机构、10组表达、28个来源选项、Dialog返焦、Sequence→Structure→Variants导航，通过且本次发布smoke为0错误/0警告。[发布QA](../../../output/playwright/typography-published-qa.json)、[发布概览](../../../output/playwright/typography-published-overview.png)。开发完整3D交互仍出现ReadPixels GPU warning，不因轻量smoke未出现而宣称已消除。
- 实现提交`82c9b22`，概览锚点间距统一为85px的收尾提交`d1eb324`，文档另行提交；无remote/push。7份现行文档的312个本地链接均存在，`git diff --check`通过。8000健康为PostgreSQL只读ok，5174保留；4174与本任务独占浏览器验收后关闭。ngrok无进程、4040无监听；没有公开发布、科学数据重跑或重新入库。
- **剩余与限制：** 上述B/D分支及移动端未全部验收；Figma画布未交付，3D初次/大范围提交开销沿用既有记录。极速脚本连续更新路由、未等React提交时可覆盖前次参数的既有现象记录在Variant QA；正常节奏的实际筛选/清除通过，本批未重写路由机制。代码已实现、本地已发布、列明的实际交互已检查；用户观感验收继续。


## CATVariant对照与五条局部重设计

2026-09-22。用户在上一批验收后继续提出Sequence配色/PTM、Structure选择器、功能分类、细胞图素材、Expression类别色，并补充字体、字号、背景和边框引导。四组并行实施，保留模块顺序与科研口径；审查[第九节](../../research/01_preview_optimization/02_typography_information_audit.md#9-参考数据库对照板块辨识背景与操作引导)作为状态作用域和分层验收依据。代码实现提交`4f0c825`；本批为本地发布，未恢复公网。

### 参考核实与实际采用

- **CATVariant实页：** 在独立本机Chromium实际打开[EGFR](https://catvariant.com/genes/EGFR)，检查DOM computed style并截图。字体为Inter；对象名30px/700，主要科学模块标题24px/600，白色数据表面。memVar保留既有Inter和密度：对象名28px/700，主模块22px/650，Overview子卡18px/650；主模块白色标题＋底分隔，子卡标题4%类别浅底、小色底图标，控件保持Slate。未复制其全页装饰网格或重新排版。见[参考截图](../../../output/playwright/fresh-five-cat-typography.png)。
- **科学色：** CAT实测数量色为白、`#e5e7eb`、`#86efac`、`#93c5fd`、`#fde68a`、`#fca5a5`；已用于memVar原有0/1/2–4/5/6/7–8档。memVar仍有原9+档，使用`#f87171`延伸；这是本地保留的量尺，不声称参考站有相同9+图例。PTM简化标记采用实测洋红`#be185d`、8px圆点及白色隔离边；类型模式仍用各原类型色。CAT默认PTM38个，memVar默认多来源209个位点，未为复制画面删掉来源。详见[实测色值](../../../output/playwright/fresh-five-catvariant-sequence-reference.json)。
- **UI素材：** 参考[shadcn Item](https://ui.shadcn.com/docs/components/radix/item)的图标、标题、描述、操作行组织，实际复用已接入的shadcn/Radix vertical Tabs、Button、Dialog和Motion；未安装整页后台模板或新增运行时。shadcn MIT等既有许可保留。
- **细胞素材：** 使用[SwissBioPics](https://www.swissbiopics.org/)动物细胞SVG，经[Bioicons原文件](https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-by-4.0/Microbiology/SwissBioPics/Animal_cells.svg)取得；[官方许可](https://www.swissbiopics.org/help)为CC BY 4.0。保留原图几何和标识，移除不可见描述及空链接，添加区域浅色、交互高亮、旁侧清晰标签和来源操作。页面显示作者/许可/改编说明，[THIRD_PARTY_NOTICES](../../../frontend/public/THIRD_PARTY_NOTICES.txt)保存来源。SVG区域ID只选择图形，不参与来源映射；原`regionFor`规则和原始标签/对象分组不变。素材独立按需加载，真实首页不请求它。

### 原位组件、动效与验证

| 部分 | 本批可见修改 | 实际交互证据 |
| --- | --- | --- |
| Sequence | 鲜明灰/绿/蓝/黄/粉/红分档，突出PTM圆点；悬停显示类型和来源；固定44px预览避免长提示顶动序列 | EGFR1210残基/209PTM；T648进入类型/证据、Escape返焦、清除；1280/1470多来源K867/Y1016/K1188提示无溢出。AQP4真0白色与二级结构缺失灰色保持。Sequence/Structure同量尺色一致。[QA](../../../output/playwright/fresh-five-sequence-qa.json) |
| Structure | 全长覆盖概览＋32残基局部窗口，字母/编号、起止手柄、输入、映射tooltip；浏览窗口独立于范围与Variant筛选 | EGFR745–750、100–900拖动预览/取消/松手；AQP4及单点首尾边界、无效输入、pointercancel、clear返焦。32→33残基键盘扩展仍保留活动手柄和焦点。Mol* canvas不重建，同范围Apply不重复触发busy；小反馈用CSS。[QA](../../../output/playwright/fresh-five-structure-qa.json) |
| Functional context | 左侧纵向分类；右侧真实首条来源注释预览，标题类别色、正文中性；完整记录仍可打开 | EGFR催化反应/调控/Family；AQP4真实H2O反应与Family，无虚构EC；键盘上下切换，Modal中换类后Escape仍回稳定入口，引用展开状态保留。切换和Dialog退出采到连续中间帧。[QA](../../../output/playwright/fresh-five-context-qa.json) |
| Cellular location | 科研矢量图＋图外区域列表/数量；悬停/焦点高亮图形；无注释区域按需展开；保留未匹配原始位置入口 | EGFR7个有注释区域/16原始来源标签；AQP4 3区域及Other source location。UniProt/HPA和Protein entry/Gene筛选、标签详情Escape返焦通过。修复Clear region禁用导致焦点落BODY，现回原区域。展开opacity0.76→1、关闭0.41→0→卸载；reduce四帧opacity1/0动画。[QA](../../../output/playwright/fresh-five-root-qa.json) |
| Expression | RNA青蓝、Protein紫；数据库浅底、assay图标和文字类别色，Blue仅标当前选择 | EGFR/AQP4、1470/1280 RNA/Protein/collection切换、默认10组、单位说明和reduce通过；未改变数据量尺、上下文、原值/单位和缺失状态。[QA](../../../output/playwright/fresh-five-context-qa.json) |

### 构建、发布与限制

- 最终`npm run build -- --outDir dist-ui-candidate`通过TypeScript/Vite，8,450模块。入口JS1,035.70kB/gzip311.40kB、CSS332.27kB/gzip63.42kB；新增按需动物细胞315.69kB/gzip91.62kB，首页实测不加载；Structure25.81kB，既有Mol*仍为独立6,098.17kB。没有因UI优化运行科学数据流程或重新入库。
- 4174候选首页/EGFR实测：1470×837及1280×800无根溢出；首页7715蛋白条目加载并可搜索AQP4；主/子标题实测22/18px。新色、209PTM、细胞图详情与clear返焦、32/33残基手柄边界、取消、导航跟随通过；候选本轮主路径控制台0错误/0警告。[候选概览](../../../output/playwright/fresh-five-candidate-overview.png)、[结构](../../../output/playwright/fresh-five-candidate-structure.png)、[首页](../../../output/playwright/fresh-five-candidate-home.png)。
- 复制候选资源后原子替换dist/index.html，旧assets保留。8000已使用`index-DgPPzBDT.js`/`index-CGC_LM3e.css`；再次验证功能分类/完整详情/Escape返焦、细胞素材及区域、新序列色与结构控件，真实Expression在HPA Protein/qualitative IHC（123条）与GTEx RNA/TPM（68条）之间切换通过；发布检查0错误/0警告，1470/1280无根溢出。见[发布概览](../../../output/playwright/fresh-five-published-overview.png)、[表达](../../../output/playwright/fresh-five-published-expression.png)和[root QA](../../../output/playwright/fresh-five-root-qa.json)。健康接口为PostgreSQL只读ok；5174保留。候选4174和本任务独占浏览器已关闭，没有开启ngrok，4040无监听。
- 应用内Browser再次返回`No browser is available`且列表为空；采用既有授权的独立本机Playwright CLI，无公网连接。开发期间并行写入CSS前曾有HMR 500，样式落盘后刷新恢复，最终页面检查单独进行；脚本早期locator选择错误也不归为网站故障。开发Mol* ReadPixels警告、主动模拟reduce的Motion提示单独记录，不声称彻底消除所有3D开销。
- 文档同步现有阶段计划、README、issue及审查状态补注；7份本轮修改文档的325个本地链接均存在，`git diff --check`通过。
- **未完成项：** 本批列明的代码、构建、实际交互与本地发布已完成，用户视觉验收继续；不等于55项及文字审查全部关闭。移动端全面验收、既有Figma画布、上节列明的罕见/细分证据分支仍未完成。大结构或大范围第一次3D提交的既有性能限制仍在；本批没有做全站性能认证、改科学分组或创建假数据验证缺失分支。


## 结构端点、预测工具与疾病面板九条批注

2026-09-22。继续原位优化，不修改模块顺序、收录口径、阈值、来源合并或坐标映射。三组实施：预测工具；疾病/API；结构端点、位置输入与集成。应用内Browser仍返回`No browser is available`且列表为空，依据技能排障后沿用独立本机Playwright CLI，无公网连接。

### 实际修改

- **Structure：** 全长条增加两个带残基编号的可拖端点、蓝色选区和图例；单残基端点垂直错开，首尾标签限制在控件内。保留32残基窗口、映射提示、拖动预览/松手提交、Escape取消/清除，以及键盘活动端点返焦。轻量DOM/CSS，无逐残基Motion实例。
- **Prediction：** 分类色icon、浅背景分层、hover/focus说明和边框反馈，不把悬停变成已选择。Picker将Score range、Reading the score、Annotation scope拆为三个dl信息块；官方资源入口与Method/definitions区分。核实AlphaMissense、ALoFT、CADD、REVEL、SIFT、SIFT4G、ESM1b、GPN、AlphaGenome九个family；网站/作者仓库/文档分别标注。来源例：[AlphaMissense](https://github.com/google-deepmind/alphamissense)、[ALoFT](https://github.com/gersteinlab/aloft)、[REVEL](https://sites.google.com/site/revelgenomics/)、[SIFT](https://sift.bii.a-star.edu.sg/www/SIFT_help.html)、[AlphaGenome](https://www.alphagenomedocs.com/)。修正三个旧DOI末尾多余括号，未更改评分解释。
- **Variant：** 删除AF与首个预测列间竖线；新增明确标注UniProt canonical position的独立输入，支持858或700–900、独立清除、越界提示，保留其他来源/工具筛选与旧关键词搜索兼容。缓存已知序列长度避免查询重载期间失去上限验证。快速导航以当前已提交URL为基础打补丁，避免恢复旧筛选。
- **Diseases：** 来源标题与右上计数对齐，计数单位、Evidence说明、范围分块；1230宽三列。PTMD2增加完整来源记录的PTM type和CellType横条；点击可组合过滤，再次点击/独立Clear恢复。原CellType字符串不合并，缺失单独Not reported；不将记录数冒称位点数。EGFR463条，其中CellType缺失430条、非缺失33条，PTM类型总和463。ClinVar使用已有结构字段显示REF/Position/ALT，保留selected transcript only或verified UniProt提示；去重复variant_id小字，表头保留GRCh38。

### 验证及发布

- 最终`npm run build -- --outDir dist-ui-candidate`通过（8450模块）；主JS1042.13kB/gzip313.15，主CSS338.52kB/gzip64.45。Mol*分包沿用既有6098.17kB，不宣称全站性能认证。
- `python -m unittest Web.tests.test_ptmd_distributions Web.tests.test_direct_pagination`：6项通过。新增测试对照完整原始CellType记录计数、缺失集合、各类别过滤及类型组合；未重跑科学整理或重新入库。
- EGFR全长端点键盘155→156保持焦点；拖动预览L156–K328后Escape恢复L156–G239；全长拖动提交G485–Y727。单点首/中/尾检查，AQP4单点1两个端点不相交，End箭头变1–2；reduce下残基transition为0s。位置858和700–900正确写入URL；1211报错且URL不变；清除范围保留ClinVar。AF单元格border-right为0px。快速PTMD组合筛选最初覆盖前项，改为URL局部patch后复测通过，十条可见记录同时满足Phosphorylation与缺失CellType，单独取消缺失仍保留类型。
- 1470×837/1230×837无新增根溢出；工具分组hover不改变4个已选字段，ALoFT Picker三块信息可见，Escape返回原Loss of function按钮，reduce无过渡。ClinVar首条C/333/=和第二条L/156/P显示正确，重复小字为0。截图：[结构](../../../output/playwright/nine-followup-structure.png)、[位置筛选](../../../output/playwright/nine-followup-filters.png)、[预测入口](../../../output/playwright/nine-predictor-intro.png)、[工具说明](../../../output/playwright/nine-predictor-picker.png)、[疾病卡片](../../../output/playwright/nine-followup-diseases.png)、[ClinVar](../../../output/playwright/nine-followup-clinvar.png)、[AQP4 reduce](../../../output/playwright/nine-followup-aqp4-reduce.png)。
- 候选4174验证后复制资源、最后原子替换dist/index.html，旧assets保留。本地8000现为`index--6KtR9Ck.js`/`index-jvELTSOw.css`，发布页首页/EGFR再验证身份、无根溢出、PTMD组合和真实表行；页面运行错误0。[发布PTMD](../../../output/playwright/nine-followup-production-ptmd.png)。开发3D过程中仍有既有ReadPixels GPU警告，reduce提示不计作错误。验收脚本一次错误使用不存在的`.di-condition`定位器，改为真实`.di-condition-row`后通过，不归为网站故障。
- 后端新增CellType统计/过滤后重启；一次服务会话退出143导致发布smoke连接拒绝，恢复为独立本地进程后重新验证通过，不把该实际服务中断误记为Browser连接故障。最终健康接口PostgreSQL/read_only正常，5174保留；公网未开启。

**剩余/限制：** 本批代码与列明的本地交互已完成，用户视觉验收继续；未核实独立官网的其他预测工具继续显示已有方法/定义链接。未扩展移动端、Figma画布、全部历史罕见证据分支或全站性能认证。CATVariant沿用上批已核实字体/色表和浅表面引导，本批未声称重新抓取全站参考或新增外部模板素材。


## 空白、Reset与阅读层级

2026-09-22。用户针对功能卡片大段空缺、序列搜索栏错位、结构端点难用和无明显Reset再次批注，并列出12类阅读问题。按原位置实施，不搬移GO等后续模块，不修改科学含义。

- **空白：** Overview网格取消等高拉伸；功能卡片随内容结束，EGFR实测约372.5px，对侧细胞图约679px。卡片内约307px虚空被去除；同排后续位置仍由较高卡片决定，不声称整行空间全部消失。功能正文15px，完整证据仍可展开。
- **Sequence：** 搜索框/Find/FASTA统一36px高度及中心线；移除上方重复Show full sequence，窗口操作行新增浅蓝outline＋RotateCcw的`Reset window · full sequence`。窗口名为Sequence display window，概览使用浅底虚线边界，与结构实心选区区别；科学残基色不变。
- **Structure：** 仅保留全长条的一对主要端点，30×36px可拖区域，短选区编号上下错开；删除局部残基行重复端点。局部行保留点击/拖动、精确输入和View start/end。标题右上始终显示`Reset structure selection`：清除范围及共享残基焦点，局部窗口回1–32；Variant筛选保留。Reset camera继续独立。新控件hover/active/focus轻CSS，reduce禁用过渡。
- **阅读层级：** 主模块24px/700、Overview子标题19px/650、疾病表正文15px。疾病/互作/ClinVar代表表格使用白色主对象列、浅Slate辅助列和更清楚的单元格间距，避免整行连续灰底；主对象与来源ID、操作链接分级。GenCC既有独立类别色保留并加入浅底/细边标签；Definitive、Limited、Moderate、Strong、Supportive在EGFR真实9条记录中均核对。未增设阈值，也未把Supportive排进强弱连续量尺。

### 实际检查

- TypeScript/Vite候选构建通过，8450模块。候选4174与开发5174检查EGFR/AQP4，1470×837和1230×837无新增根溢出。应用内Browser仍无实例，使用独立本机Playwright，公网未开启。
- EGFR339–599选区，末端键盘599→600后焦点保留，全长仅2个slider；AQP4单点1的两拖柄不重叠，箭头调整为1–2；拖动预览1–24后Escape恢复1–2。Reset恢复无选区；reduce下残基transition为0s。
- EGFR窗口100–200→Reset后为1–1210，同时结构339–599仍在；再Reset结构后无范围、局部1–32，URL中的ClinVar来源及GenCC疾病筛选均保持。未把窗口重置当作全站清除。
- 实测主标题24px、疾病正文15px；Sequence三个控件height均36px且center完全一致。截图：[概览内容高度](../../../output/playwright/hierarchy-overview.png)、[结构拖柄](../../../output/playwright/hierarchy-structure.png)、[GenCC列与类别](../../../output/playwright/hierarchy-gencc.png)、[Sequence](../../../output/playwright/hierarchy-sequence.png)。早期截图在滚动后立即取得，导航高亮可能尚未更新；最终发布截图已等导航状态提交。
- 候选通过后原子替换dist/index.html，8000发布为`index-DVNkkaSY.js`/`index-CV4q762q.css`；发布页复测单残基Reset、36px对齐、24px标题、无溢出。[发布截图](../../../output/playwright/hierarchy-published-sequence.png)。开发完整3D操作控制台0错误，沿用Mol* ReadPixels警告；reduce提示单列，不宣称全站所有GPU开销已消除。此批无API变更，未重复数据库/科学流程或增加镜像实现测试。

**边界：** 本批三处具体反馈及列明的共享阅读样式已实现、本地发布、限定实际操作已验收；12类问题继续作为逐页/逐表审查框架，不声称每个罕见数据分支、弹层和专用图表均已完成。移动端全面验收、全站性能认证、未核实工具官网等既有未完成项保持。

## 序列缩略图与局部版面

2026-09-22 17:03 +08:00。按用户八条新批注与指定 [EGFR序列调研](../../research/09-egfr-sequence-browser.md) 实施；不将参考站未核实的预测聚合、实验量尺或空间邻域计算引入memVar。

### 实现

- 全蛋白导航缩略图添加真实每位点变异计数、已勾选来源的结构域/区域、膜片段及PTM；缩放仍保留全序列坐标，并叠加搜索命中和共享选择。拖动/端点键盘调整只改变显示窗口。底色、边界、PTM标记、搜索外框分别表达含义。
- 搜索与共享选择分离：位置/范围/序列片段匹配，片段查找全部出现位置；独立状态条、清除和跳转。清除搜索保留共享残基，窗口Reset保留搜索。Atlas密度Auto/25/50（按容器上限适配），切换优先保留选中或搜索位置；字母同步放大。180ms颜色/透明度过渡，reduce为0；未声称逐帧动画性能验收。
- 结构选择器参考 [shadcn Slider](https://ui.shadcn.com/docs/components/radix/slider) / [Radix Slider](https://www.radix-ui.com/primitives/docs/components/slider) 的细圆thumb和轻交互环。16px可见圆点＋28×32px透明操作区，单点两侧分配hit area；复用已有drag事务，不以更换底层组件破坏Escape回退或精确映射。
- GO移至Functional context左列下方，三aspect使用现有Radix Tabs，Location同步高度。此处当时误解了目标模块；用户后续明确要求移动Reactome，已由下方“排布纠正与滚动记录”替代。
- Expression十组预览，一次展开全collection后420px内部滚动，取消Show more/all/fewer；显示标签去下划线，源值/keys/title不改。QTL全部匹配组织376px内部滚动，保留搜索/分组，筛选改变后回到列表顶部。滚动模式参考 [Scroll Area](https://ui.shadcn.com/docs/components/radix/scroll-area)，本地使用原生可聚焦滚动region。
- 六种variant consequence完整展示；Variant查询/转录本两组蓝青浅底；疾病六来源各自彩边、浅底、白色说明块，QTL来源卡强化来源颜色与选中边界，零记录禁用含义保持。

### 验证及发布

- TypeScript与Vite构建通过：8451模块；`index-BOTpJiZF.js` 1050.07kB（gzip316.02），`index-puRt9IF3.css`345.07kB（gzip65.55）。Mol*仍为独立大资源；未将本批作为性能优化宣称。先在4174候选生产页验证，再复制资源并最后原子替换8000的index。
- EGFR，1230桌面：790–795精确6命中、初始共享选中为0；点T790打开源证据；清搜索保留T790；Reset窗口恢复1–1210；切PTM lens仍6命中且图例更新；25/行实际格子37.16px、字号增大。非法1211得到错误且无命中；缩略图拖动得到242–484；reduce计算样式transition=0s。
- Expression实测68组、420/1931px可见/完整高度、内部scrollTop600且整页scrollY不变，显示标签下划线0；QTL32行、376/1264px、内部scrollTop500；Brain搜索11行且回滚动顶部。
- 结构EGFR方向键406→407，拖动预览后Escape恢复407；补充1470/1280检查M1/A1210单点hit area无重叠、745–776边界焦点保持、鼠标调整到802。AQP4候选生产页单点1两target不重叠；Reset清结构范围/共享选择，局部窗口1–32，搜索1与URL ClinVar筛选保留。
- GO鼠标/方向键切换，1230下两列均889.7px；六consequence252px无内部滚动。六来源卡实际computed样式确认不同色边/浅底；8000重新打开确认新主资源、6命中、GO三tab、Expression68组及无根级横向溢出。
- 浏览器0应用错误；Mol* ReadPixels性能warning仍存在。开发、候选及实际发布页面分别核对，不把仅URL变化当作渲染完成。

截图与补充QA：`Web/output/playwright/sequence-thumbnail-current.png`、`structure-fine-endpoints-current.png`、`layout-go-current.png`、`layout-diseases-current.png`、`fine-structure-handles-qa.json`。本批使用独立本机Playwright；延续Browser连接无可用实例的已确认降级，未开启公网。测试会话和临时候选预览完成后关闭，本地8000/5174继续。

### 保留边界

本批关闭列明的桌面改动与交互，不代表全部12类/55项或每个证据弹层完成。3D空间邻域、未确认的预测/实验聚合不新增；移动端全面验收与全站剩余证据分支继续按原计划。用户提供的09调研文档保留原位原文，未改写其中观察和待验证结论。


## 排布纠正与滚动记录

2026-09-22。按最新八条批注纠正实现，本节替代上批GO位置与全长缩略图方案。

- Functional context下方改放Reactome，右侧Cellular location同步布局；GO恢复后续全宽三栏，三个aspect同时可见。
- Sequence全长导航重做为简洁细轨与两个端点，删除重复注释缩略图、图例和大悬浮面板。点击选择单点，拖动选择片段，键盘精调端点，保留精确输入、窗口Reset及Escape取消；搜索和共享残基语义保持独立。
- Expression展开后保留全collection内部滚动，新增Collapse collection，收起恢复十组预览并将焦点放回按钮。
- QTL记录使用540px内部滚动，滚近底部自动读取后续cursor，取消翻页操作；过滤条件改变后从顶部开始，后续加载失败可重试。Assembly列改为表上来源坐标说明，不将其他来源强制标成GRCh38。
- P值新增可输入的显示参考阈值，满足≤参考值时显示青色，其他值中性；默认留空，未新增统一科学阈值，未筛除记录或调整原始P值。等待用户指定默认数值或来源标准。
- IntAct Full、Topic、Mutation分别蓝、青、紫；ClinVar条件内SNV表限制高度并固定表头，支持内部滚动。ClinVar原有每页25条服务端分页及总量保留，本次未声称整库一次加载。

### 验证与交付

- TypeScript/Vite通过，8451模块；最终资源index-CNQpT7xg.js、index-BEgPedvi.css。候选验证后复制资源、最后原子替换8000的index；5174开发服务保留。
- EGFR在1470与1230宽度下：点击606单点、方向键扩至606–607、拖动303–424、Escape恢复以及Reset至1–1210均通过。Q12809确认Reactome六通路在Function下方，GO恢复三栏。
- Expression 68组展开后可滚动，Collapse恢复10组且焦点回按钮。ClinVar条件25条当前页记录在518px区域滚动，实测scrollTop600。
- GTEx apaQTL 39条完整展示于内部滚动区；eQTL由50条滚动加载至100条，无重复行。测试输入5e-8时39条中15条着色、24条中性，记录数量不变；该测试值未设为默认。
- 三类IntAct标签实测背景及文字颜色不同；浏览器零应用错误，沿用Mol* ReadPixels警告。截图：output/playwright/corrected-reactome-q12809.png、simple-sequence-selector.png、qtl-scroll-reference.png。

此批不修改后端或正式科学数据，未扩大为移动端全面验收。用户提供的09调研文档保持原文，未纳入本批提交。


## QTL来源判定与自定义参考

2026-09-22用户确认方案后实现。数据库已保留GTEx pval_nominal_threshold，新增API source_assessment投影（统计量、值、阈值、比较符、依据及met/not_met/unavailable）；原始阈值同时加入详情。GTEx逐条nominal P≤来源阈值；eQTLGen使用来源FDR<0.05（0.05不通过）；QTLbase不推断统一标准。缺失、非法值不当作零，合法零保留。未新增基因级q-value到关联记录，也未重建、筛除正式数据。

前端默认Source criterion；Custom P threshold保留手动输入，切换只改颜色，输入值切换后保留。来源模式明确eQTLGen颜色依据FDR而列中展示原始P；悬停及详情提供判定依据。达标青色，未达标与不可判定均中性且文字区分。自定义默认值仍为空，与来源判定独立。

验证：4项后端测试覆盖GTEx逐条阈值及等号、eQTLGen严格小于边界、缺失/非法/零及QTLbase不推断；TypeScript/Vite通过。真实GTEx EGFR apaQTL 39条来源模式全部达标，自定义5e-8变为15达标/24超出，切回恢复39，记录数不变。实际API验证eQTLGen Q5QGZ9 FDR=0保留且达标、QTLbase不可判定。沿用已确认的Browser无实例降级，独立Playwright验证，未开启公网。

补充验收：GTEx详情显示实际阈值0.0000169899；QTLbase页面显示Criterion unavailable且无达标着色。最终生产资源index-wy09-u74.js / index-CBNaiMHP.css已更新本地8000，API同步启用，5174开发服务保留。截图output/playwright/qtl-source-criteria-published.png；无新增应用错误。


## 人体导航素材与残基悬停编号

2026-09-22，按三条批注完成。QTL人体导航底图更换为Bioicons收录的Servier Medical Art musculature-front.svg（原始SVG，CC BY 3.0；页面及随附LICENSE署名）。参考检索核对Servier当前素材库授权，但采用文件按Bioicons附带3.0授权保留。旧手绘轮廓和器官图形移除，新图降低显示不透明度并校准12类示意圆点位置；来源组织分组、计数与点击/键盘交互不改，圆点为导航示意，不代表每个组织的精确解剖坐标。

简洁序列滑条恢复紧凑Residue编号提示，鼠标移动、拖动及端点键盘操作均更新；轨道虚线旁增加跟随鼠标的字母+编号提示，边缘限制在轨道范围内，不恢复旧大浮层与重复缩略图。

验证：TypeScript/Vite通过（8452模块），1470宽度滑条中点606/左端1、轨道G729提示正确；QTLbase Brain点选后15组织并保持选中状态。1230宽度右端1210、拖动显示当前编号、Escape恢复1–1210，无根横向溢出。候选截图qtl-servier-body.png、sequence-hover-number.png、sequence-slider-hover.png位于output/playwright。应用页面无控制台错误，既有Mol*警告保留；独立本机Playwright沿用已确认的Browser不可用降级。最终index-BwFVFL03.js/index-C7S_XmuN.css原子更新本地8000，5174保留。本批不改后端及科学数据。


## Location说明压缩、链入口与卡通导航

2026-09-22，用户新批注1–4实施；第5条AlphaGenome映射仅讨论。

- Cellular location说明/未注释区域合并至底部Reading notes折叠入口，署名在角落保留；区域列表增高并展示最多两项真实来源标签，完整证据仍由点击进入，计数不改。
- 删除结构范围选择器重复残基/chain悬浮框及对应hover状态，保留端点编号、精确输入、拖选、Escape与Reset。
- 结构API新增真实PDB链ID及残基数（不依赖canonical匹配是否成功）；工具栏显示Chain及Focus chain，聚焦所选链。EGFR当前是AlphaFold A链1210残基，不虚构多链模型，不新增PDB采集或多链序列映射。相机定位不更改科学配色/共享范围。
- QTL素材更换为OpenMoji person-standing SVG卡通轮廓，适配浅蓝填充及细边，圆点位置重新校准；按CC BY-SA 4.0署名并保留适配文件许可。替代先前Servier肌肉图。

验证：TypeScript/Vite通过，真实EGFR API返回A/1210/exact_current_canonical；1230页面Focus chain可操作，无结构selector tooltip。Reading notes展开保留缺失含义说明、收起不占大块空间；区域预览实际UniProt Secreted。卡通Brain点选保留11组织标签，页面无横向溢出；应用控制台0错误，沿用Mol*性能warning。候选最终index-B45aaK4o.js/index-DLFIclmJ.css发布本地8000，API同步更新，5174保留。截图output/playwright/cartoon-tissue-body.png、location-source-preview.png。浏览器沿用已确认独立Playwright降级。

### AlphaGenome蛋白映射讨论（未实施）

当前API只核对历史accession→Ensembl关联与HGNC身份，不能证明转录本翻译产物匹配当前canonical蛋白。显示数组为降采样mean/max（截图1024 bp/bin），不能作为单残基分辨率信号。foundation保留Ensembl GTF/CDS/pep，可作为后续核对依据，但本批未构建映射。

建议未来在同一基因组横轴上增加选定转录本的exon/CDS轨道，在CDS区段标对应蛋白aa范围；点击CDS区段再联动蛋白序列。必须核对组装版本、转录本版本、链方向、CDS phase及翻译序列一致性；UTR/内含子/调控区无直接残基对应，负链方向相反，跨外显子密码子需按CDS拼接处理。禁止将整段基因组按长度线性压到蛋白上，或把一个1024bp bin解释成单残基预测值。此建议仅讨论，未修改AlphaGenome数据或界面。


## 新Logo与首页插图裁剪

2026-09-22。页头首页及内页统一采用用户docs/logo.png，原样复制为前端资源；仅CSS隐藏周围画布留白，未重绘或修改Logo文件。替代旧Dna图标+文字组合，首页链接及可访问名称保留。

首页Peripheral membrane问题为SVG viewBox与正方形viewport比例不同，letterbox区域露出原图相邻内容。为原图分类插图添加独立clipPath，限制到各自viewBox范围；保留本体、真实计数和分类入口。1470首页截图确认两侧灰条及右下相邻绿色部分消失；1230内页Logo完整，搜索/导航无横向溢出。TypeScript/Vite通过，最终index-Scd6NrcY.js/index-BjrbWIxu.css本地发布8000。原始docs/logo.png及用户09研究文档不改写、不纳入本次提交。截图output/playwright/new-logo-home.png、peripheral-crop.png、new-logo-protein.png；独立Playwright沿用已确认降级。


## 用户提供的人体组织底图

2026-09-22。将用户 docs/tissue.png 原样复制至 frontend/src/assets/tissue.png，替换 QTL 组织导航的 OpenMoji 底图；按新图调整 12 个组织导航圆点的大致位置，保留组织匹配规则、悬停、点击和键盘交互。移除旧素材署名，原始用户图片不改写。

验证：TypeScript/Vite 构建通过；1230 截图确认透明底图及圆点位置，Brain 点击与 Enter 取消选择断言通过，1470 页面无横向溢出。截图 output/playwright/user-tissue.png。候选 index-DyA1CzDT.js/index-Cgg8KNzn.css 已发布本地8000并核对入口。


## GitHub 发布基线

2026-09-22。用户确认当前网站版本并授权发布到 PuppetZhou/memVar。仓库根对应 Web/，README 改为面向独立代码仓库的功能、依赖、运行与数据边界说明；AGENTS 与当前计划记录后续以当前 main 为基线提交。新增忽略环境、数据库文件及调研 results 导出；已跟踪的11个调研结果文件仅从发布索引排除，本地原件保留。旧开发历史保存在本地 local/pre-github-20260922 分支，发布主线以当前源码树创建独立初始提交，避免历史数据被一同推送。原始 Logo、组织图仍保留本地，运行所需素材副本随 frontend 发布。定向检查未发现已跟踪环境凭据或匹配的密钥，数据目录仅包含 README。
