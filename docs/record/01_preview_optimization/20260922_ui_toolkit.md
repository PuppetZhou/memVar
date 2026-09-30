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


## 发布基线后的五条桌面反馈

2026-09-22。QTL 人体图从200×347放大至275×476，左栏同步加宽；点位随SVG等比放大。序列来源控件使用独立浅蓝底和显著按钮；Topology改为来源入口→该来源下的类型/方法复选列表，并提供返回入口。来源按名称首段分组，原始option ID、来源证据、可用状态和多来源选择语义保持不变。结构局部残基条支持垂直鼠标滚轮和横向触控板浏览，只移动32残基窗口；保留选区，边界放行页面滚动，Ctrl/Meta缩放不拦截。膜特征详情改为突出按钮，基本信息六字段分卡片并以底色区分身份、物种和序列。

验证：TypeScript/Vite通过；沿用此前Browser无可用实例后的已授权独立Playwright，在4174/Q12809以1230×837检查组织图大小及Brain点选、膜详情打开、Topology的HTP选层及返回UniProt保留选择、滚轮正向与横向反向浏览及选区不变。1470宽无横向溢出，页面身份/内容及框架覆盖检查通过，控制台0应用错误，仅Mol* ReadPixels性能提示。截图在/tmp/memvar-feedback-{overview,tissue,structure,topology-final}.png。未扩大为移动端或全蛋白验收。最终index-DPNrjsTz.js/index-7VHsDzQI.css发布本地8000。


## 恢复公网预览

2026-09-22 18:36 HKT，用户授权使用 screen 后台启动 ngrok 并公布。独立会话 memvar-ngrok 转发 http://127.0.0.1:8000，入口 https://renewably-ashy-undiluted.ngrok-free.dev 。启动时继承的HTTP代理触发ERR_NGROK_9009，已仅为ngrok进程清除代理环境变量后成功连接，未修改全局代理或凭据。公网首页及Q12809 overview API均返回200，首页确认当前index-DPNrjsTz.js版本。核查从本机经公网域名发起，不代表所有外部网络均已验收。日志保存在忽略的.runtime/ngrok.log；screen后台运行不等同于开机自启。


## 20:59 运行检查与恢复

2026-09-22 20:58 HKT检查发现screen中的ngrok仍在运行，PostgreSQL端口55432监听正常，但网站8000无监听，公网首页及接口均502。当前退出原因未确定，旧/tmp日志不能证明本次退出原因。20:58:53以用户级systemd临时服务memvar-web-preview.service恢复网站，Restart=always、RestartSec=3，脱离工具终端生命周期；ngrok仍由原screen会话管理。20:59复核本地及公网首页、Q12809/P00533 overview、Q12809 sequence、QTL summary、structures全部200且JSON可解析，首页JS/CSS可获取；本地响应约0.03–0.35秒，公网约0.55–1.26秒。服务active/running，NRestarts=0。该验证从服务器经公网地址发起，不代表所有外部网络；临时服务未配置开机启动。


## 克制配色试版、反应式与变异滚动列表

2026-09-22。根据新一轮八条批注试行灰蓝操作色、近中性表面、深色正文；样式集中于refined-surfaces.css，降低装饰色饱和度而非整块降低透明度。膜来源信息改为无分割线的轻底网格，去掉标签套框；详情入口取消橙底边框，保留加粗文字与箭头。疾病六来源保留外框和来源色点，去掉彩色顶线、内部证据框及重复横线；QTL/Expression等来源卡片一并收敛表面色。科学轨道与来源分类保留独立颜色。

Functional context及Rhea反应式共用ReactionEquation：浅底、数学衬线字体及明确电荷括号的上标显示；来源词语、等号和方向不改写，不自动推导化学式。Reactome概览移除重复TAS标签，详情证据保留。

变异目录改为50行一批的游标滚动加载，固定高度、粘性表头，取消翻页栏。筛选/预测列变化隔离查询缓存并回顶，旧分页URL归一到全列表起点；续载失败保留现有行并支持重试，空结果和末尾状态独立显示。没有修改后端数据收录或排序规则。

频率依据核查：[ClinGen Variant Curation SOP](https://www.clinicalgenome.org/docs/variant-curation-sop/)及其[2021 SOP](https://clinicalgenome.org/site/assets/files/5933/variant_curation_sop_2_0_jan_2021.pdf)。一般BA1需要大洲人群AF>0.05、至少2000个观察等位基因及基因/变异例外审查；BS1/PM2依赖具体疾病/基因规则。不能将overall AF、零频率或缺失直接转换为良性/致病证据。本轮仅把原连续AF量级色阶改为低饱和灰蓝，并在频率详情提供上述依据；没有新建ACMG判定或正式科学阈值。

验证：TypeScript/Vite通过。独立Playwright沿用已授权Browser无实例降级，在P00533的1470/1230桌面检查页面、截图与横向溢出；实际滚轮50→100行，start_lost筛选6行且回顶、noncanonical空结果及返回、末尾提示、频率说明展开均通过。模拟续载请求失败（预期产生网络错误）后仍保留50行，恢复请求并重试至100行；正常访问无应用错误，仅既有Mol* ReadPixels性能提示。Q12809页面和膜详情可打开。截图/tmp/memvar-muted-{overview,disease,variants,reaction}.png。未做全量4096行性能或全移动端验收。最终index-DNPCApWG.js/index-CXugCG_H.css同步本地8000，ngrok保持关闭；README及计划纠正当前公网状态。


## 2026-09-27暂停公网与本地开发衔接

用户要求跟进现状、暂停发布并继续展示细节优化。实查ngrok仍转发本机8000，与此前“已关闭”记录不符；已对该网站ngrok进程发送TERM，复核无ngrok进程、4040无监听。现有memvar-web-preview用户服务保持active/running，8000 API健康检查返回PostgreSQL只读ok。

启动Vite时遇到系统文件监听数上限（ENOSPC），改为仅在开发服务使用CHOKIDAR_USEPOLLING=true、CHOKIDAR_INTERVAL=500，不调整全局系统参数。用户级临时服务memvar-web-dev.service从Web/frontend运行npm run dev，仅监听127.0.0.1:5173；页面HTTP 200，经5173代理的/api/health返回PostgreSQL只读ok。服务脱离工具终端生命周期，但未配置开机启动。可用systemctl --user stop memvar-web-dev停止，journalctl --user -u memvar-web-dev查看日志；手动终端启动可在Web/frontend使用CHOKIDAR_USEPOLLING=true CHOKIDAR_INTERVAL=500 npm run dev。

日常改动在5173热更新查看，8000保留现有构建版；完成定向验证后再更新构建产物，公网保持暂停。本轮只核对运行入口与API健康，未做浏览器交互验收，未修改页面、数据库或科学规则。


## 2026-09-28膜架构与来源证据重排

根据用户七条页面批注重做 Membrane architecture & source evidence。默认入口改为Sequence & OPM：先展示UniProt全长区段及原始胞内/胞外注释，再展示按PDB/chain/model切换的OPM深度图和残基窗口；区段、残基和深度点支持悬停/键盘聚焦读数，点选残基保留其结构证据表。OPM表展示canonical residue、PDB/chain、PDB residue、geometry及depth，替代小字号嵌套卡片。UniProt合并start/end，直接列类型、区间、注释和证据；Topology保留数据集/来源条目选择、来源序列轨道和类型/区间/role表，方法/文献等有内容时直接显示；DeepTMHMM2只保留膜类型、信号肽及预测区段。mapping、coordinate status、EXACT等技术字段不再默认展示，API及上游数据保留。

OPM序列接口增加每条原结构观察的depth、basis、model、PDB残基及插入码，未聚合不同结构/模型值。深度沿用现行几何规则：正值在膜核心内、负值在核心外，不解释为胞内/胞外朝向；现有来源侧别只在相应拓扑轨道呈现，不引入新朝向推断。来源序列轨道使用来源编号；无法投影的OPM记录另以PDB编号表保留。缺深度不画成零，未知/不确定位点保留文本而不强行投影。实现：`frontend/src/components/MembraneOverview.tsx`、`MembraneTopology.tsx`、`MembraneSequenceViewer.tsx`、`MembraneTrack.tsx`及`src/api/membrane_overview.py`。

验证：

- TypeScript与项目安装的Vite 6.4.3候选构建通过，8458模块。6项既有拓扑检查及新增1项OPM模型/插入码/缺失与零回归通过。
- EGFR序列接口425条结构观察，与原details接口逐条核对position/PDB/chain/model/原编号/depth/basis，完全一致；其中44条缺signed depth，界面保留其结构并明确缺失。未做全数据集扫描。
- 应用内Browser返回无可用实例，发现列表为空；按既有降级采用本机Playwright。EGFR区段和残基悬停、点选、深度点键盘Enter、OPM链切换、缺深度结构、UniProt无展开表、HTP方法Hmmtop六行、TOPDB原PMID、预测区段、结构分页/空来源及Escape通过。1414×827及1230×837无新增根/弹窗横向溢出。
- KRAS/P01116无UniProt膜区段及无OPM状态正常；Q12809的9组原PDB编号记录仍可见。不同编号未混入canonical轨道。控制台无应用错误。本批未验收全部蛋白、完整移动端或3D结构朝向。
- 候选通过后重启本地8000 API，复制新资源并最后原子替换index；旧assets保留。最终`index-Bfr6sQMG.js`、`index-Ct0rDk31.css`；8000健康检查通过，实际发布页再次检查深度hover读数/高亮、残基表、拓扑与预测通过。ngrok无进程；未开放公网，未重导入数据库。

截图和浏览器检查脚本保存在`Web/output/playwright/`，包括`membrane-published-20260928.png`、`membrane-topology-20260928.png`、`membrane-residue-20260928.png`、`membrane-empty-20260928.png`、`membrane-pdb-numbering-20260928.png`及本批`membrane_*_check.js`。用户视觉验收继续；先前全站55项与移动端未完成状态不因本次局部交付自动关闭。


## 2026-09-28证据标签筛选区与来源记录五条批注

按用户五条页面批注完成展示精简：

- Reactome详情移除TAS标签，保留通路名称/ID、主题、来源及官方图链接；API evidence_code不变。
- GO标签从按大类统一颜色改为按原始证据代码配色，例如IDA青绿、IMP蓝、IPI紫；代码、全称和说明仍保留。配色不建立科学置信等级或改变来源分类，维护于`OverviewEvidence.tsx`。
- Variant筛选保留两组语义标题与原输入控件，外观改为单一浅灰背景、去除组边框及分隔线，维护于`refined-surfaces.css`。
- ClinVar将Disease / condition和ClinVar records分栏；MedGen/MONDO/MeSH/Orphanet等ID与RCV/SCV各归其区，去掉链接卡片背景/框线和重复数量，改为紧凑标签行。RCV说明移入标签提示，SCV保留Germline/Somatic impact/Oncogenicity类别。原条件列表与ID列表仍不推断一一配对，原始字段入口保留。COSMIC说明仅在COSMIC页显示。
- COSMIC改为五列表：ID（含次级legacy ID）、Transcript、CDS、AA、Sample count；删除Gene、重复HGVSc/HGVSp、SO_TERM和每行独立Open source入口，ID本身可跳转。每条来源记录保留，不跨转录本去重或累加sample count；计数继续指原GENOME_SCREEN_SAMPLE_COUNT。

本批仅前端展示调整，不改API、数据库或科研规则。TypeScript及项目Vite 6.4.3构建通过（8458模块）；使用既有本机Playwright降级，对EGFR检查Reactome无TAS但链接可用、GO的IMP/IDA实际前景/背景色不同、筛选组透明且边框0、ClinVar疾病与RCV/SCV分区、COSMIC六条记录与六个COSV链接及每行原count=2、COSMIC来源筛选/R2Q搜索、Escape返回和1230宽度无根/弹窗横向溢出。1414宽度截图已目检；既有Mol* ReadPixels性能warning保留，不扩大为全站/移动端验收。

候选通过后复制资源并原子替换本地8000入口，保留旧assets；最终`index-C7YBMfBc.js`、`index-k79CoIgt.css`。本批无需重启后端；8000实际发布页再次通过ClinVar分区/COSMIC六行及计数/来源筛选/搜索检查，API健康正常，控制台0应用错误。截图及可重用检查脚本保存在`Web/output/playwright/evidence-{reactome,go,filters,clinvar,cosmic}-20260928.png`及`evidence_*_check.js`；用户视觉验收继续，公网仍暂停。


## 2026-09-28数据库风格微调

以GitHub main `fcb8ca9`为调整前基线。用户确认现有素材和布局，仅授权配色、字体及表面样式微调；不做组件重排。实际浏览UniProt P00533及gnomAD EGFR详情，参考白/灰阅读底、清晰深色文字及蓝色操作提示，保留memVar品牌与科学配色。外层浅紫/浅粉改为中性灰白，蓝色选中态及键盘焦点；标题改为Inter 600，减少负字距；外层卡片/弹窗圆角5px、控件4px，取消常驻卡片阴影和来源入口悬停上浮。来源入口按已有compact-accent显示轻浅底色。膜区段、OPM、GO、变异预测、结构与序列色标不变。维护于`refined-surfaces.css`及`interaction-polish.css`，未改组件结构、API或数据。

验证：TypeScript/Vite构建通过；应用内Browser无可用实例，按既有流程使用本机Playwright。EGFR概览、膜详情打开/Escape、GO的IMP/IDA颜色差异、变异筛选区截图检查；1414与1230桌面无新增根/弹窗横向溢出，弹窗稳定态opacity=1、白色标题栏、5px圆角。截图在`output/playwright/style-{overview,membrane,go,variants}-20260928.png`，参考截图为`reference-{uniprot,gnomad}.png`。未作全蛋白/移动端验收。

候选资源更新至本地8000，保留旧assets并原子替换index；当前`index-Dua5DTtI.js`/`index-DTKlfwxH.css`。未恢复公网或提交本轮风格变更；等待用户视觉反馈。此前Medical方案作为历史依据保留，当前外层风格以上述授权为准。


### 同日追加：概览底板与变异标签去框

用户对第一版具体批注：变异标签配色/框线及概览卡片仍过度装饰。只调整`refined-surfaces.css`：连续白色阅读底、外层模块保留分组横线；身份字段、图标底座、膜来源入口取消背景块；变异表格中的来源按钮、consequence、ClinVar、预测标签去底色/外框，氨基酸取消底块。原语义文字色、连续评分色、星级和图表色标保持，不改变字段、排布、数据或点击处理器。表头/斑马纹改为中性灰，保留行边界。

TypeScript/Vite通过；本机Playwright目检1414桌面截图，1230根页面无横向溢出；实查身份边框0、来源/ClinVar标签边框0且背景透明，ClinVar绿色文字仍保留，来源详情打开和Escape通过。截图`output/playwright/style-flat-{overview,variants}-20260928.png`。更新本地8000，未提交本轮样式、未恢复公网，等待视觉反馈；全站及移动端未作完整验收。


### 同日追加：用户色板与适度外框

用户提供两组颜色并要求Basic information及Membrane features恢复适当边框。当前外层色板采用#577590混白4%为页面底、混白34%为边框，#0081a7用于焦点及混白10%的选中态，#00afb9混白4%用于工具区，#fdfcdc混白35%用于膜标题区，#fed9b7混白20%用于膜来源hover。两组cerulean独立命名，未覆盖科学色标。两个概览区域恢复1px外框/4px圆角，无阴影；字段及变异标签保持去框状态。高饱和红橙未铺成大面积背景。

TypeScript/Vite构建通过。Playwright实查两个外框1px/4px，变异标签边框仍为0；1414截图目检、1230无根横向溢出。截图`output/playwright/style-user-palette-20260928.png`。候选已更新本地8000，未推送Git或恢复公网。


### 同日纠正：统一第一套色板并恢复UI组件外观

用户否定混用色板及孤立黄色标题，明确要求纠正。采用第一套五色：#0081a7焦点/操作与调浅边界，#00afb9工具底/hover，#fdfcdc混白28%为全页阅读底、22%为身份字段底，#fed9b7混白22%为来源入口、40%为hover，#f07167用于悬停/键盘焦点的箭头点缀。移除第二套蓝灰/蓝色变量。恢复8px外层卡片、6px图标容器和来源入口、原interaction-polish交互文件（包含reduced-motion），膜标题恢复白色。变异表格文字标签无框、科学色标与组件结构不改。

TypeScript/Vite通过，1414截图目检；实查膜标题白色、概览外框1px、变异标签0边框、来源入口杏色；1230无根横向溢出，膜详情打开/Escape通过。截图`output/playwright/style-palette-corrected-20260928.png`。已更新本地8000，未提交本轮样式或恢复公网。此前同日试版只作历史依据，当前方案以此条为准。


### 同日更新：蓝色阅读基调与文字对比度

根据用户新色板及gnomAD截图，替代五色页面装饰。撤掉奶黄/杏色底与珊瑚悬停箭头，蓝白/浅灰背景、深色阅读文字。#001233正文与标题、#33415c说明、#0353a4链接、#0466c8焦点；卡片边框/图标容器/交互保留。概览标签14px、值15px，导航14px，说明与表格正文适度加大；未改变科学色标、数据或组件布局。

TypeScript/Vite通过；1414概览及变异表格截图目检、1230无根横向溢出；实查标签为#33415c/14px、评分独立色仍保留。截图`output/playwright/style-blue-{reading,table}-20260928.png`。更新本地8000供用户比较，未提交Git或恢复公网，完整移动端未验收。


### 同日更新：四处卡片增添色与深蓝层级

按用户四条批注落实具体模块，而非只调整外层字体：表达入口GTEx海草绿、HPA蓝、FANTOM黄、CPTAC珊瑚橙，来源浅底/色边，选中卡片#002855白字；疾病卡片改为白底彩色顶线、深蓝大计数、按来源hover与选中反馈，ClinGen蓝/GenCC绿/HPO暗青/OMIM橙/ClinVar红/PTMD2珊瑚橙。ContextPanels来源色同步使用相同值。变异分类卡片深蓝顶线，后果色使用用户橙/红/绿/蓝灰等新色，文字取同色系深色提高对比；分类映射/计数不变。主变异表深蓝表头白字，浅蓝灰斑马行；预测数值、ClinVar科学分类和结构置信色标保持。

实现：`ContextDisplay.tsx`、`ContextPanels.tsx`、`variant-evidence-model.ts`及`refined-surfaces.css`。TypeScript/Vite通过，1414四处截图目检；表达HPA选择等待异步状态后正确、ClinGen来源切换后显示2条原断言记录（内嵌表格，不是弹窗）、1230根横向溢出检查通过。表头及选中卡片实际为#002855白字；原focus-visible规则未修改，本批未完整验收键盘导航。截图`output/playwright/accent-{expression,diseases,categories,table}-20260928.png`。更新本地8000；未提交Git、未恢复公网，未扩大到全站/移动端验收。


### 同日更新：浅表头与表达来源色、变异行信息精简

用户认为整块深蓝过重，明确要求表格/表达选中变浅。表头改#e9eff5深色文字；表达选中使用来源16%浅底、色边和深色字，来源配色改GTEx #90be6d、HPA #f9844a、FANTOM #4d908e、CPTAC #f9c74f，并同步来源色映射。consequence 14px/600突出，转录本12px灰色保留可点击；来源按钮删除箭头。删除表格重复的“UniProt position”行，以选中记录原canonical_positions传入详情，在Variant与Representative transcripts页展示；已有Position列不变，无位点时不新增断言。不更改数据或API。

TypeScript/Vite通过。Playwright验证主表无vc-mapped或来源SVG；7:55019282记录打开转录本详情可读“UniProt canonical position · P00533 / 2”，Escape正常；1414表格/表达截图目检、1230无根横向溢出。截图`output/playwright/soft-{variant-table,expression}-20260928.png`。候选更新本地8000，Git未提交，公网未恢复。

### 同日更新：序列轨道标签与catalog文字层级

删除SequenceViewer alignedRow标题旁的装饰点，8条轨道保留数据图形及图例。catalog以用户gnomAD截图为排版参考：变异标识15px/500蓝色、consequence 14px/600、辅助转录本与评分说明12px；表头14px、浅灰蓝底，斑马行减淡、单元格上下8px，预测数字15px。字段、来源交互和科学色标不变。TypeScript/Vite通过；EGFR桌面检查确认装饰点0、轨道8、详情可打开并Escape关闭，1230宽无页面横向溢出。截图output/playwright/type-{variant-catalog,sequence-labels}-20260928.png。本地8000更新，未提交Git或恢复公网；全站及手机未作本轮验收。

### 同日更新：来源图标一致性与canonical标记精简

表达来源数据库图标、场景图标与箭头/选中勾统一采用来源色的深色调，图标底色使用来源浅底。catalog仅省略canonical行的重复Ensembl canonical，保留非canonical/未知提示和详情转录本信息，表头改Consequence。TypeScript/Vite通过；1176宽EGFR检查canonical标签为0、GTEx/HPA/FANTOM图标随来源色变化、无根横向溢出。截图output/playwright/source-icons-20260928.png。本地8000更新；未提交Git或发布公网。

### 同日更新：功能与细胞定位概览高度

仅对overview功能/Reactome/定位卡片收紧头尾和正文间距、功能标签间距、反应式padding，取消细胞定位布局390px最小高度及卡片拉伸，定位列表最小行高61改44px，保留全部标签与详情入口。桌面功能导航155px，为反应式让出宽度。TypeScript/Vite通过；1414与1176×827截图检查三张卡片可在滚动至本区后完整呈现，1176无根横向溢出。截图output/playwright/compact-overview-1176-20260928.png。本地8000已更新，未提交Git或发布公网。

## 2026-09-28：PaxDB后端与页面接入

用户确认organ归纳进入现有人体互动图，cell独立；默认字段通过，gene_name、string_external_id、id、filename、weights仅后端保留。上游配置与来源保持mapping/发布见科研工作区modules/expression/docs/paxdb_mapping_review.md；419成员均H.sapiens且全部2,452,008源行均9606.，映射目标6,999蛋白均human。人类来源包含细胞系等，不宣称全部正常组织。

配置config/paxdb.yaml引用20260928_paxdb_01。build_paxdb.py投影为data/tables/paxdb，import_paxdb.py独立事务导入web_paxdb（419 datasets、826,088 observations、6,999 mapping），主键/外键与计数通过；当前web.protein无缺失关联，API reader仅获读权限。源码保留全部后端信息；无丰度合并、13条重复源ID按来源行号保留。

新增/api/proteins/{accession}/expression/paxdb及summary，原值分页按organ/context_type过滤、参数约束。页面Protein measurements→PaxDB提供Integrated protein abundance与Individual protein studies；默认三列Context/Abundance(ppm)/Dataset。组织复用QTL人体导航组件（对PaxDB使用上游显式body_region）；cells、fluids、cell fractions、whole organism独立，内部字段不进入公开详情。

验证：前端构建通过；MEMVAR_TEST_LIVE=1 python -m unittest Web.tests.test_paxdb_live -v共3测试通过（分区计数、人类/公开字段、肾脏原值、分页与无效参数）。EGFR 48 integrated/254 studies，其中研究cell64；Playwright测试图→肾脏3.6ppm→详情、Cells、研究切换、空记录状态、1176无根横向溢出。截图output/playwright/paxdb-{map,cells}-20260928.png。只验收本轮桌面范围；本地8000更新，未Git提交/公网发布。

### 同日更新：表达入口对齐与PaxDB连续丰度表

表达来源块与右侧场景区等高，去除侧边色条、彩色图标底块，使用中性图标与浅蓝选中。PaxDB默认入口简为Protein abundance；默认表仅Tissue/Context与Abundance(ppm)，不重复展示Integrated或Dataset。单项研究名放组织名下辅助区，类型仍保留详情。使用useInfiniteQuery滚动加载替代Previous/Next，后端仍有界分页；线性蓝色横条按当前筛选完整结果的最大值缩放，原始ppm不改，加载后续记录不改变比例。构建及3项live API测试通过（新增跨页maximum一致检查）；浏览器实测37默认组织记录全部呈现、研究167行滚动加载完成且无Next按钮、来源左右高度一致、详情可开关。截图expression-neutral-20260928.png与paxdb-bars-20260928.png。更新本地8000，未提交Git或发布公网。

### 同日更新：配色恢复与GitHub提交

按用户要求撤回柔和附加色系试用，恢复此前红、橙、绿、青与蓝色的来源和内容强调配色；保留PaxDB接入、连续丰度表、中性图标、入口对齐及此前文字层级调整。恢复后重新构建本地预览，并将当前网站源码、配置及必要文档提交GitHub；数据、凭据与运行产物不上传。

### 同日更新：iOS组件风格试用

新增独立ios-surfaces.css并由main.tsx加载：圆角卡片、系统字体优先、浅灰分组背景、白色分段选中块、轻阴影、按压反馈、导航毛玻璃及22px圆角弹窗；尊重减少动态和减少透明度偏好。保留数据与科学色标。TypeScript/Vite通过；EGFR页面实测标识弹窗可打开、Escape关闭，RNA/Protein切换正常，1176px及390px无根横向溢出。截图output/playwright/ios-{overview,dialog,expression,mobile}.png；仅本轮局部页面检查，不代表全站移动端验收。本地8000已更新，未提交GitHub。

### 同日更新：依据Apple指南调整材质与反馈

2026-09-28在线读取Apple HIG官方页面对应DocC JSON（常规检索连接失败，官方站点可直接访问）：[Materials](https://developer.apple.com/design/human-interface-guidelines/materials)、[Motion](https://developer.apple.com/design/human-interface-guidelines/motion)、[Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)、[Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)。采用的原则：玻璃用于导航与交互层，内容保持清晰；自定义按钮提供按压态，反馈短促、允许中断；保留键盘及减少动态效果支持。网页实现为近似材质，不声称复现原生Liquid Glass光学或触觉反馈。

候选实现：导航冷白渐变、20px模糊和125%饱和度；分段控件白色高光及紧阻尼弹簧（stiffness 520、damping 38、mass .7），仅作用选中底块；按压85ms/缩至.975，释放220ms，大卡片仅缩至.992；弹窗入场240ms/退场140ms，遮罩只淡入淡出，不动画化模糊半径。删除帮助图标弹跳及来源卡片hover位移，粗指针主要操作44px触控目标。上述数字均为memVar试用值，并非Apple规定。数据色标、API及查询行为不变。

构建通过；浏览器核对弹窗动画名/240ms、键盘Space关闭和焦点返回、快速RNA/Protein切换；按压85ms，reduced-motion下transform none/transition 0s且弹窗animation none；390px无根横向溢出。截图ios2-dialog.png与ios2-expression.png。浏览器有外部Google Fonts连接失败及WebGL截图警告，系统字体回退正常；未进行真实iOS设备性能验收。更新本地8000预览，未提交GitHub。


## 2026-09-28统一配色与动效试行

用户要求统一配色与动效、改善Variant Catalog质感，并以指定11色替代CATVariant序列色系；授权先实施一版再根据观感调整或回退。保留此前未提交iOS代码，仅记录本次增量。

- 界面：`frontend/src/ios-surfaces.css`集中维护最终iOS表面和交互变量，灰白背景、白色内容面、统一蓝色操作态；导航保留轻透明，表格和弹窗内容使用实底。数据介绍页链接复用主色。
- Sequence：`frontend/src/lib/palette.ts`维护用户11色、临床分类图色、对比度文字及CSS共享色标；`sequence-model.ts`维护展示映射。变异数量的0、1、2–4、5、6、7–8、9+分档不变；PTM、二级结构、膜区段、来源图例和JSD同步使用新色系。数量不等于致病性，缺失与零仍分开。临床分类保持标签并使用独立配色。共享该模型的Structure科学着色和渐变图例同步更新，原生pLDDT色标保留。
- Variant Catalog：边框和圆角统一，表头文字分主次，Ref/Alt保持单行；固定首列支持横向滚动；数值使用等宽数字属性，源名称为轻量按钮，评分文字为深色、小色标保留既有分类或连续评分方向。未调整原始值、分类判断或阈值。
- 动效：`lib/motion.tsx`统一160ms内容反馈、收敛分段选择器弹簧，取消内容位移；小按钮轻按压，弹窗200ms打开/120ms关闭；残基格子取消缩放，避免密集数据跳动。保留运行时减少动态效果支持。

验证（本地1600×1100、EGFR/P00533）：

1. `npm run build`（frontend目录）通过TypeScript及Vite；`git diff --check`通过。
2. Variant初始50行正常；横向滚动350px首列位置不变；`7:55019278 A→G`详情打开、关闭通过。
3. Atlas数量、PTM、JSD模式切换通过，1,210格；JSD图例端点与实际颜色函数一致。
4. 模拟`prefers-reduced-motion: reduce`，残基transition为0s、transform为none，弹窗animation为none；恢复普通设置正常。
5. 0–29计数核对分档与本轮前一致；全部数量格子文字对比度≥4.5，JSD 0–1以0.001步长核对的最低对比度4.588。仅为本轮颜色验证，不代表全站无障碍审计。
6. 最终浏览器error级控制台消息为0。此前截图过程出现WebGL ReadPixels性能警告；未进行3D性能或全站负载测试。

产物：本地8000已载入新版；截图与颜色核对位于`output/playwright/style-20260928/`，含`after-catalog.png`、`after-atlas-viewport.png`、`variant-dialog.png`及`palette-check.json`。本轮不发布公网或推送GitHub；用户观感与移动端验收未完成。

回退：`output/style-20260928/before/`保存实际修改前文件，包括此前未提交修改；`output/style-20260928/trial.patch`只描述本轮增量。在Web目录先运行`git apply --reverse --check output/style-20260928/trial.patch`，通过后再反向应用，随后在frontend目录重新`npm run build`。存在后续修改导致冲突时逐文件处理，不使用`git reset --hard`。备份和补丁为本地忽略产物，不上传仓库。


## 2026-09-28点击反馈与预测配色追加

依据用户浏览器批注：上一版评分颜色不易区分damage与否，指定`#CC247C/#E95351/#F7A24F/#FBEB66/#4EA660/#79CAFB/#5292F7/#AA77E9`；另要求让可点击、可选择部分具有统一iOS反馈。仅修改前端呈现。

- `lib/palette.ts`追加独立predictionPalette、predictionCalls与连续predictionRamp。原来源明确分类采用粉红/绿/橙，连续方向色阶为绿→黄→橙→红→粉红，无damage阈值；无损伤方向的原生0–1分数使用青→蓝→紫；其余原生分数用蓝。文字采用较深同色衍生值，避免黄色和浅青文字对比度不足。上一轮序列分类配色保留。
- `scoreVisual`保留原SCORE_SCALES、sourceCall及predTone逻辑；PredictionValue显示浅底、鲜明色标与来源分类标签，没有来源分类显示“No source call”。不把REVEL连续分数转成Damaging/Tolerated，不按数值覆盖来源判定。
- `ios-surfaces.css`末尾的Shared affordances集中维护操作反馈：170ms悬停提亮与轻阴影；75ms按下，普通控件缩到.985、大卡片.996；持久选中用蓝色底与内边线；键盘焦点2px蓝框。分段选择器保留原滑动指示，主要按钮保留深蓝底白字；禁用项排除，减少动态效果设置关闭过渡和缩放。文字链接提供下划线提示。科学残基与SVG轨道不纳入通用控件缩放。

验证：TypeScript/Vite构建、`git diff --check`通过。EGFR浏览器检查来源按钮hover背景`rgb(237,243,251)`及阴影、press缩放.985/75ms、来源详情开合、键盘focus-visible蓝框、主按钮hover深蓝底白字、分段选择器单一滑动指示、功能分类持续选中。减少动态效果时press无transform、transition 0s。SIFT低分方向及原D/T分类保持，REVEL未给分类时不推断；两类连续色阶0.001步长的文字对比度最低4.756。不是全站、移动端或真实设备触觉验收，网页反馈为视觉反馈。

截图及必要核对记录：`output/playwright/touch-20260928/`。本次新增回退包`output/touch-20260928/trial.patch`，从本轮前的真实工作区生成；在Web目录先`git apply --reverse --check output/touch-20260928/trial.patch`，通过后反向应用并重新构建。上一版色板试行不被一并撤销；有后续修改冲突时逐处处理。


## 2026-09-28白底简洁化与表格去装饰

依据最新ProtVar参考图与四条浏览器批注调整当前试行，替代前版相应的卡片背景、边框及评分装饰：

- 白底阅读面，主要板块按标题、留白和细横线组织；概览、筛选、表达等减轻嵌套边框，导航保留轻透明。交互保留悬停、短促按压、持续选中与键盘焦点，取消装饰性阴影和选中内边线。
- Variant Catalog保留固定首列、浅表头与细横线；所有列间竖线移除。评分色条、评分底色及分类标签底色删除；无来源分类只显示原始分值，不重复“No source call”。表头说明与分值提示继续明确来源分类和连续评分的区别。
- ClinVar、后果与分类文字提高饱和度。`palette.ts`的`evidenceInk`维护分类文字，`predictionTextColor`保留连续色阶色相并按可读性降低亮度；不再混入深蓝灰。未修改分类、评分方向、阈值或数据库。

验证：TypeScript/Vite构建及`git diff --check`通过；本地EGFR实际13列表头左右边框均为0，Ambiguous及其标签计算背景为透明、色条伪元素不存在；详情打开关闭通过。连续两类色阶按0.001步长核对，浅色悬停背景上的最低文字对比度4.602，三类分类文字均超过4.62。实际表格与概览截图见`output/playwright/clean-20260928/`。仅完成本轮桌面定向检查，不表示全站及移动设备验收。

本地8000构建已更新，无GitHub推送。本轮独立回退补丁`output/clean-20260928/trial.patch`从本轮前真实工作区生成；在Web目录先运行`git apply --reverse --check output/clean-20260928/trial.patch`，通过后再反向应用并重新构建。只撤销本轮改动；此前未提交工作保留，有后续冲突时逐处处理。


## 2026-09-28恢复模块边界与macOS参考

用户确认白底清爽，但无框区块难以分组。本轮在`frontend/src/ios-surfaces.css`恢复主模块、概览功能／定位等区块、表达选择容器与数据集卡片、疾病来源卡片及指标卡片的细边框。大区块14px圆角，操作卡片沿用紧凑圆角；白底、无重阴影、蓝色选中态保留。疾病卡片恢复顶部来源色线。表格仍无列间竖线，评分及分类标签仍无底色；数据、原始分类与科学规则未修改。

参考核查：[Figma官方说明](https://help.figma.com/hc/en-us/articles/24037833895831-Get-started-with-Apple-s-UI-kit)明确列出Apple macOS 26 UI kit，含组件、样式和示例屏幕，可从Libraries或Community添加。用户[文件链接](https://www.figma.com/community/file/1543337041090580818/macos-26)在当前Web检索及Playwright中不可读取，浏览器返回403；未查看内部画板、未导入资源、未宣称数值取自kit。本轮判断：桌面组件的分组、工具栏、分段选择器和状态规范适合后续参考；实际细框和圆角参数为memVar本地试行值，按用户批注实施。

验证：TypeScript/Vite构建通过。1414px EGFR实页中概览区块、Expression容器和Diseases主模块为白底／1px边框／14px圆角，表达和疾病卡片边框恢复。Expression可切至Individual cell lines并返回Cancer samples；表格所有th/td左右边框仍为0、评分背景透明。390px根页面宽度390，无根横向溢出；不代表完整移动端验收。截图见`output/playwright/blocks-20260928/`，本地8000已更新。未推送GitHub或发布公网。

本轮独立回退：`output/blocks-20260928/trial.patch`。在Web目录先`git apply --reverse --check output/blocks-20260928/trial.patch`，通过后反向应用并重新构建；该补丁仅回退本轮，保留更早工作。

## 2026-09-29Apple组件参考核对

读取交接、现行计划、共用分段控件/动效和`ios-surfaces.css`，查看2026-09-28 Expression截图。当前工作区仍为`/home/xuyzh/memVar-re`；8000 EGFR页面HTTP返回200，仅证明入口可访问，本轮未重新进行浏览器交互验收。Figma `whoami`成功，返回Starter团队及View席位，具体文件权限待真实链接核对；旧交接中的授权阻塞不再适用。

重新核对[Figma官方Apple kit说明](https://help.figma.com/hc/en-us/articles/24037833895831-Get-started-with-Apple-s-UI-kit)，确认提供iOS/iPadOS 26与macOS 26 kit。通过Apple官方DocC JSON读取[Segmented controls](https://developer.apple.com/design/human-interface-guidelines/segmented-controls)及[Materials](https://developer.apple.com/design/human-interface-guidelines/materials)：分段控件适合相关模式/状态选择；Liquid Glass主要用于导航和控件层，应节制使用，内容层避免铺设该材质。

本项目判断：优先校准Expression的RNA/Protein模式控件，再检查工具栏按钮、筛选和详情弹窗的状态一致性。多来源数据集卡片保留名称、测量与记录数，不能压缩成难以区分来源的分段选项；表格、序列和评分继续使用清晰实底。现有分段控件已基于Radix与Motion，实际kit参考应适配到现有组件。CSS存在早期样式与末尾覆盖，实施时仅整理涉及的选择器并以computed style验证。当前弹簧/时长为项目自定义，未获得kit动效证据。

初步评估时仅有Community地址，曾请求复制后的`/design/`链接。随后用户要求直接调用优化，以下执行结果替代“等待链接后再优化”的安排。

### 直接调用与本地实施

Figma创建[组件对照文件](https://www.figma.com/design/kmxJzBoxwUrhs5zeqbzOqY)成功。`get_libraries`返回iOS/iPadOS 26与macOS 26，`search_design_system`检索到两套Segmented control。服务将三项检索限制为一项，button/search field未处理。尝试`importComponentSetByKeyAsync`导入iOS组件返回`Not permitted to upsert from library`（`INVALID_ARGUMENT`）；未获得节点、截图或动效参数，文件尚无设计画板，不据此声称复刻Apple kit。账号授权成功与库组件导入权限分开记录。

本地实施：`ModeToggleGroup`增加可选等宽布局，Expression启用，标签简化为RNA/Protein并保留原完整aria-label。分段选中采用600字重，相关区域按压保持尺寸，禁用态明确；`ios-surfaces.css`将本批相关表面样式合并回主要维护段，移除末尾重复规则，修复增强对比度指示边框被覆盖。显式清除旧`.cx-assay-overview > div`五列布局对新等宽控件的影响。正常桌面每项154.5×40px，总宽320px；粗指针最小高度44px。尺寸、颜色、过渡仍是项目适配值，科学内容与来源卡片结构不变。

验证：Browser运行时连接列表为空，使用Playwright CLI。TypeScript/Vite候选构建通过；EGFR RNA↔Protein、重复点击不取消选中、方向键定位/空格激活与2px焦点、Individual cell lines↔Cancer samples通过；单一选中及单一滑块、增强对比度1px边框、减少动态时transition为0s通过。最终短标签再次验证等宽等高和切换，390px页面无根横向溢出且标签无溢出；不是全站/移动端验收。截图`output/playwright/apple-controls-20260929/after.png`已目视核对。发布候选构建到本地8000后再次验证切换和短标签，未推送GitHub或开放公网。

回退：`output/apple-controls-20260929/trial.patch`仅包含本批三个前端文件增量，基于真实修改前工作区生成；`git apply --reverse --check`通过。反向应用后需重新构建。先前所有未提交修改保留。Figma精确组件参考受库导入权限限制，其余本地UI优化可继续。

## 2026-09-29苹果风格整体界面试行

用户认为上一批局部分段控件调整不足，明确授权参考苹果交互、材质与组件体系，且整体字体颜色/背景配色可以优化。本批在现有布局中实施，依据此前核对的Apple HIG；Figma真实kit导入限制仍未解除，本批参数为项目适配值。

- `ios-surfaces.css`维护当前UI主题：外层`#f5f5f7`，阅读面白色，正文`#1d1d1f`、次级`#60616a`、辅助`#6e6e73`，操作蓝`#0066cc`；系统字体优先，统一标题字重/字距。主模块18px、控件9–12px、详情22px圆角，保留模块细框与来源色。修改现有主要规则并补充对应控件段落，没有再叠一份主题文件。共用交互规则通过`--touch-radius`尊重组件圆角，避免来源卡片被覆盖为8px；搜索结果面板同步为18px。
- `App.tsx`章节导航加入Motion移动选中块，滚动时增加轻阴影；导航采用24px模糊的浅透明表面。头部搜索增加清除/Escape及清除后焦点返回；空输入的提交按钮禁用。390px头部改为导航与搜索两行，避免固定高度造成重叠。
- `components/ui/filter-select.tsx`基于已安装Radix Select提供浮层选择菜单，接入共用`SelectFilter`：选中勾号、键盘定位/输入匹配、Home/Enter/Escape与焦点返回。使用`filter:`前缀编码空值，输出去掉前缀；All仍返回原空字符串，现有值与来源含义不变。原生科学viewer内的select保留，仅统一其外观。
- 工具栏、搜索边框、按钮主次及可点击来源卡片反馈统一；详情弹窗采用轻背景模糊、稳定标题栏、独立正文滚动和圆形关闭入口。提示气泡采用深灰表面，加载提示采用局部中性底；保留既有内容切换/展开Motion实现，不声称新增数据加载缓存或旧结果保留机制。
- 无修改科研处理、原始值、评分方向或独立色板；ClinVar conflicting文字显式保留原色，避免跟随新的UI蓝。表格无列间竖线、评分无底色规则保留。

验证（2026-09-29，工作区Playwright，桌面1440×1080）：TypeScript/Vite最终构建与`git diff --check`通过；EGFR ClinVar来源选择、键盘Home/Enter恢复All、Escape关闭与焦点返回，名称详情开合/焦点返回/正文滚动，搜索清除/Escape，章节单一选中与单一滑块通过。菜单测试等待实际键盘焦点稳定后再按Enter，避免测试事件过快造成误判。首页搜索AQP4并进入P55087通过；390px根页面无横向溢出，头部搜索底部92px在105px头部内、章节导航起点119px，无重叠。减少动态/增强对比度时菜单和弹窗动画关闭、导航/菜单/遮罩模糊关闭、选中边框保留。新UI文字代表组合对比度最低4.658，不代表全站无障碍审计。

截图位于`output/playwright/apple-system-20260929/`：`overview.png`、`menu.png`、`dialog.png`、`expression.png`、`diseases.png`、`home.png`、`search.png`、`narrow.png`；含修改前的overview/expression对照。上述关键画面已目视核对，窄屏图为AQP4。验证摘要`output/apple-system-20260929/verification.json`。本批仅验证受影响路径，不表示所有页面/长菜单/移动设备均已验收。

最终候选构建已复制到工作区`frontend/dist`，保留旧assets并最后替换index。无GitHub推送、无公网部署。用户先前访问`localhost:8000`返回连接拒绝，当前只确认工作区内服务正常；客户端转发尚未恢复，交付以截图和代码为据，不再直接把该URL称为用户可用链接。

增量回退：`output/apple-system-20260929/trial.patch`覆盖本批三个既有文件及新增`filter-select.tsx`，修改前状态在`before/`；反向应用检查通过。回退后重新构建，本批之前的未提交工作保留。


## 2026-09-29序列与结构分值配色

用户反馈JSD、PeSTo与binding site在结构中难以区分，给出八色色板并授权优化序列呈现。本批只调整呈现，不修改科学值或数据处理。

- `lib/palette.ts`集中维护`sequenceScoreStops`与`sequenceScoreColor`：0、0.2、0.4、0.6、0.8、1对应`#5292F7`、`#79CAFB`、`#FBEB66`、`#F7A24F`、`#E95351`、`#CC247C`，段间RGB线性插值。六个颜色锚点不是分类阈值，不按蛋白分布或排名重映射；灰色仍表示无分数/无注释，0为蓝色。绿色、紫色未强行加入有序色阶。
- `sequence-model.ts`的JSD与界面预测映射共用上述函数。`ConservationPlot`、`InterfaceAnnotations`曲线按纵轴分数着色并加轻描边，下方增加逐残基色带；缺失位置保留灰底且不跨缺口连线。原数值读出、片段/partner/类别选择及位点证据入口保留。共享界面色阶也同步用于SPPIDER-seq，未修改其分数含义。
- `ScoreColorKey.tsx`与`score-color-key.css`共享SVG颜色锚点与图例；结构图例增加0/0.25/0.5/0.75/1刻度。JSD atlas和残基详情图例同步，序列格保留黑/白自适应文字。旧主题端点渐变替换为同一CSS渐变变量，避免代码换色而图例仍是旧色。
- `featureStyle`将原binding注释单独呈现为Binding site玫红，其余Functional site颜色保留。`StructureViewer`在精确映射的binding残基增加玫红球棍，维持灰色未注释背景；用户选择仍为蓝色球棍。未增加位点、口袋预测或任何分数阈值。

验证：TypeScript/Vite构建及`git diff --check`通过。EGFR 1,210个JSD逐残基色带与接口原值映射全部一致；PeSTo切换Lipid binding后1,210个色块全部一致。键盘JSD读出R2=0.545852，PeSTo读出原值0.00072767236；Enter打开R2证据，Escape关闭。JSD atlas和结构图例已核对新渐变；JSD/PeSTo丝带、PeSTo分子表面以及binding玫红球棍均完成浏览器实页截图核对，无结构着色错误。本地8000复核六个新颜色锚点及1,210个PeSTo色块生效；390px页面无根横向溢出。此为EGFR定向验证，不代表所有蛋白、partner或完整移动端验收。

截图：`output/playwright/sequence-colors-20260929/sequence.png`（含修改前对照）、`structure-jsd.png`、`structure-pesto.png`、`pesto-surface.png`、`structure-binding.png`。验证摘要和独立增量回退：`output/sequence-colors-20260929/verification.json`、`trial.patch`。回退先`git apply --reverse --check output/sequence-colors-20260929/trial.patch`，再反向应用并构建；之前未提交工作保留。本地`frontend/dist`已更新，未推送或公网部署；用户端预览转发仍未验证恢复。


### 同日微调：两套柔和连续色阶

用户反馈六色色阶过艳，要求红蓝与蓝黄橙。当前版本替代上文共同六色色阶：JSD为0蓝`#648FC1`→1红`#C96F72`，PeSTo及共用界面预测为0蓝`#648FC1`→0.5浅黄`#EDDA91`→1橙`#D78C52`。中间颜色仍线性插值，0.5只是颜色锚点；无阈值或分数变换。Binding site沿用上一批玫红球棍。

`palette.ts`按`jsd`/`interface`分别维护锚点；`ScoreGradient`、`ScoreColorKey`显式接收色阶类型，序列曲线/色带、结构、atlas及残基详情同步。构建、差异格式检查、EGFR曲线与两类结构图例核对通过；实看JSD丝带与PeSTo表面截图，无着色错误。本地8000构建已更新，2/3个SVG锚点分别生效；未重复无关数据或交互验收。

截图：`output/playwright/sequence-colors-soft-20260929/sequence.png`、`jsd-ribbon.png`、`pesto-surface.png`。独立增量回退为`output/sequence-colors-soft-20260929/trial.patch`，反向应用检查通过。恢复前先检查冲突，回退后重新构建。


### 同日更新：用户指定青蓝与酒红色板

用户提供两套完整色板，并确认分别用于JSD浅青→深蓝、PeSTo亮红→酒红。本次仅改`palette.ts`的两组锚点：JSD按9个给定色值由`#CAF0F8`到`#03045E`，PeSTo/SPPIDER按10个给定色值由`#E01E37`到`#641220`。原输入末尾`ff`为完全不透明，代码保留等价六位RGB。锚点均匀分配于0–1并线性插值，0在浅/亮端、1在深端；不作阈值、分位数或非线性重映射。此决定替代上一节蓝红/蓝黄橙的配色，binding site不变。

TypeScript/Vite构建、差异格式与回退检查通过；EGFR序列显示9/10个渐变锚点，实际映射0/0.5/1分别为JSD `#caf0f8/#00b4d8/#03045e`、PeSTo `#e01e37/#ad1e35/#641220`，结构切换与图例正常且无着色错误。已核对序列与两类丝带截图；本地构建更新，未重复数据或整站测试。

截图在`output/playwright/sequence-palette-20260929/`；本次独立回退为`output/sequence-palette-20260929/trial.patch`，仅包含本轮色板调整，应用前先反向检查并在回退后重新构建。


## 2026-09-29结构可读性与CATVariant参考

用户认为3D结构直接沿用sequence颜色区分度不足，提供CATVariant截图并询问原理。核查[CATVariant公开结构组件](https://catvariant.com/assets/Results-hYbukpfr.js)：通过`getPy2DmolHtml`加载iframe，并以`CATVARIANT_PY2DMOL_STATE`传入逐残基颜色、选中及映射；不是默认Mol*材质。其代码还将较浅默认灰映射为更深灰。上游[py2Dmol](https://github.com/sokrypton/py2Dmol)说明可交互的结构投影、管状/插画表示及描边、宽度、光照控制。截图可见粗色块、轮廓与较平的着色，但无图例，未推断截图颜色的科学类别或声称取得其确切渲染参数。参考源码保存在`output/structure-rendering-20260929/reference/`。

[Mol*官方Quick Styles](https://molstar.org/viewer-docs/tips/quick-styles/)支持描边与ignore-light；结合当前安装包实现，本批保留现有Mol*引擎、坐标和科学色标，只改表示/材质。`StructureViewer.tsx`默认Residue backbone（圆柱/球骨架，sizeFactor 0.55），同时保留Ribbon与Molecular surface。新增Appearance选择：默认Clear colours · outlined；Depth shading保留立体着色。平色模式对主体与选中/结合位点球棍统一ignoreLight；白底、1px灰描边（threshold 0.33），关闭深度雾、遮蔽与投射阴影；表面不再开启illumination路径追踪。`viewers.css`桌面视口由420增至540px，窄屏沿用340px。色阶、0–1方向、位点映射及序列外观不变。

实页检查发现并修复初载时序问题：PDBe `render()`只完成UI初始化并启动`load()`，不会等待模型。旧代码立即`setReady(true)`，可能先画空结构、后被加载完成的默认pLDDT/cartoon覆盖。本批在render前订阅`events.loadComplete`，成功后才启用着色；失败显示加载错误，清理时取消订阅。该修复是本轮确保颜色实际生效所必需，非修改科学数据。

验证：TypeScript/Vite构建、`git diff --check`及增量回退检查通过。EGFR初载后选择JSD，读取实际渲染器确认backbone、sizeFactor 0.55、ignoreLight=true、outline开启、fog/illumination关闭，overpaint为1211层（灰底＋1210个残基）。完成JSD/PeSTo实图、三种表示和两种外观切换；shaded实际outline关闭，骨架/球棍ignoreLight=false。M1选择在外观切换后保留，清除与重置通过，无结构着色错误。未进行全站、多模型、全部蛋白或性能基准验收。

截图`output/playwright/structure-rendering-20260929/`含`jsd-backbone.png`、`pesto-backbone.png`、`pesto-ribbon.png`、`pesto-surface.png`。`before.png`保留初载旧实现现象，不作为同分数受控A/B对照。用户截图跨色相色块也贡献可分辨性，不能据此保证相近连续值获得同等色差；当前保留用户已确认色阶，不新增分箱、阈值或分位数重映射。

验证摘要及独立增量回退位于`output/structure-rendering-20260929/verification.json`和`trial.patch`。补丁仅涉及本批两个文件；反向应用前先检查，再重新构建。最终候选已更新本地`frontend/dist`；无GitHub推送或公网部署，用户端转发可用性仍未确认。


### 同日更新：协调取色，缩减色相跨度

用户提供新的JSD和binding色板，明确不要求严格串联所有色值，要求符合当前界面风格。本次选取JSD `#A8DADC/#457B9D/#1D3557`（雾蓝/钢蓝/藏蓝），binding界面预测 `#56CFE1/#5390D9/#6930C3`（青蓝/天蓝/靛紫），分别作为0/0.5/1显示锚点。采用给定色板子集，避免整串色相跳变；原值保持连续线性插值，未作分箱或科学阈值。UniProt binding site及其球棍同步改为`#6930C3`，结构提示改为不绑定色名的Coloured sticks，避免后续配色变化留下过时文案。此节替代之前完整青蓝/酒红两套色阶和玫红binding site。

仅修改`palette.ts`与上述结构提示。TypeScript/Vite构建、差异格式与回退检查通过；EGFR曲线/色带的两组图例与锚点一致，三种着色模式切换正常，binding site图例为rgb(105,48,195)，无结构着色错误。已核对序列、JSD骨架、PeSTo骨架及结合位点截图；现有描边平色保留，不重复无关交互或数据测试。本地构建已更新。

截图`output/playwright/sequence-coordinated-20260929/`：`sequence.png`、`jsd.png`、`binding.png`、`binding-sites.png`。独立回退`output/sequence-coordinated-20260929/trial.patch`反向检查通过；仅回退本轮两个文件增量，应用后重新构建。


## 2026-09-29恢复GitHub配色与立体默认模式

用户反馈当前结构观感略失真，要求保留并优化此前模式，JSD与binding回退GitHub提交版。`git fetch origin main`后确认远端与本地HEAD均为`2dffcfb63906f6296c42b57dec3d08241f95d0e7`；定向读取提交中的`sequence-model.ts`，通过现有共用色板恢复JSD `#F5F0FF`→`#8055C0`、PeSTo/SPPIDER `#E0F2FE`→`#2563EB`→`#6D28D9`，独立binding site回到提交原有的`#DB2777`玫红。此决定替代上节青蓝/靛紫协调取色。仅恢复颜色映射，保留逐残基色带、图例、atlas与结合位点球棍等近期功能。

`StructureViewer.tsx`恢复Ribbon＋Depth shading为默认；Molecular surface和新增Residue backbone、Clear colours描边均可选。骨架sizeFactor由0.55降至0.35，减少粗管拥挤；描边由深灰改为浅灰，三种表示均增加轻局部遮蔽，立体模式采用0.55环境光＋0.45方向光。保留白底、关闭深度雾，表面使用实时光照而非旧路径追踪；无坐标修改。沿用`loadComplete`着色时序修复及540px视口。

验证：TypeScript/Vite构建、差异格式与增量反向应用检查通过。两套映射各取1001个0–1分值，与GitHub原函数逐一比对共2002次，无差异。EGFR六种表示/外观组合均实际检查，JSD overpaint均1211层（灰底＋1210个残基），描边与ignoreLight状态正确，轻遮蔽开启。PeSTo表面和binding site丝带完成截图核对；M1跨外观切换保留，清除选择与重置相机正常，无结构告警。首次交互脚本在清除后等待已移除的状态节点超时；修正为检查节点数量后通过，属于检查脚本问题。未进行全蛋白或性能基准验收。

截图位于`output/playwright/structure-restore-20260929/`；`output/structure-restore-20260929/verification.json`保存验证摘要，`trial.patch`仅含本轮两个前端文件增量。应用回退前先反向检查并重新构建。本地`frontend/dist`已更新，8000返回入口与候选构建一致；未推送GitHub或公网部署，用户端转发仍未验证。


### 同日更新：骨架采用独立插画外观

用户要求Residue backbone模仿CATVariant，在之前粗骨架平色版本上优化渲染。本批只改骨架参数与外观切换：sizeFactor恢复0.55、保留圆柱/球接头、网格回退径向分段24、哑光材质；默认灰轮廓`#697582`与平色，局部遮蔽radius 4、bias 0.8、灰蓝遮蔽色`#798797`，帮助区分重叠。可选Depth shading采用0.7环境光与0.3方向光。保持原坐标、GitHub配色、分数映射和当前相机，不声称复刻py2Dmol的完整渲染方式。

外观选择改为按表示分别保存在当前组件会话中：初始Ribbon/shaded、Molecular surface/shaded、Residue backbone/outlined；用户切换外观后再切换表示，保留各自选择。丝带与表面的渲染参数不变，默认仍是Ribbon。

TypeScript/Vite构建、差异格式与增量反向检查通过。EGFR实页核对骨架sizeFactor 0.55、ignoreLight、轮廓、遮蔽参数，JSD覆盖1211层（灰底＋1210残基）；PeSTo截图、三模式默认外观切换、M1选中跨外观切换及清除通过，无结构告警。本地8000构建已更新；未做全蛋白/性能测试，未推送或公网部署。

截图`output/playwright/backbone-illustrative-20260929/jsd.png`、`pesto.png`；验证摘要和本轮单文件增量回退位于`output/backbone-illustrative-20260929/verification.json`、`trial.patch`。回退前反向检查，再重新构建。


## 2026-09-29QTL坐标轨道与互作入口精简

状态更新：用户随后要求删除QTL轨道；该功能已撤除，下面的轨道实现与验证仅为历史记录。互作入口精简仍适用，当前配色见文末“QTL轨道撤除与配色统一”。

按用户四条批注完成：

- 互作继续使用上方IntAct/BioGRID来源卡片及集合卡片；删除下方重复Source/Collection下拉框，尚未选定集合时不显示空记录区。选定后保留相互作用类型、检测方法筛选和来源证据范围。
- QTL类型按钮保留单层可点击外框，内部apaqtl/eqtl/sqtl改为纯文字；说明区由黄色底/边框改为项目浅中性灰、细边及12px圆角。科学P值和来源阈值保持原规则。
- 增加QTL genomic distribution：读取PostgreSQL，覆盖当前来源、类型及组织的全部记录，不受表格已加载页数限制；同版本/染色体/坐标合并为一个点并保留记录计数。密集点仅在绘制时分组，点击分组放大后可选择单个坐标；点选后表格仅显示该坐标记录并获得焦点，Show all positions恢复全部记录。
- 保留不同assembly和染色体，未提供有效坐标或assembly的记录不画点并明确计数、仍保留在原表。该视图是来源基因组坐标轨道，不画未经入库确认的基因边界、外显子或DNA碱基，不执行liftover。点颜色仅指示交互选择，不表示显著性。

实现：`QtlPositionViewer.tsx`、`ContextPanels.tsx`、`qtl-tissue-browser.css`；API `GET /api/proteins/{accession}/qtl/positions`及现有QTL记录接口新增成组的chromosome/position/assembly筛选。坐标筛选在来源行排序编号后应用，保留原record_id；游标绑定坐标和版本，避免跨筛选复用。来源或组织/类型切换清除已选坐标。

验证（2026-09-29）：5项定向测试通过，包括版本分轨/坐标缺失、完整范围与同坐标多记录、原record_id一致、点选后的cursor/offset、原跨dataset分页、组织筛选与空结果。EGFR GTEx为1,546条/700个坐标；apaQTL为39条/34坐标；皮下脂肪sQTL为11条/9坐标；QTLbase为29,113条/6,494坐标/21条染色体轨道，完整计数吻合。首次坐标查询分别约0.06–0.11秒（GTEx）和0.80秒（QTLbase）；此为EGFR局部实测。

TypeScript/Vite构建通过，本地8000 API服务已重启更新。1414×827浏览器核对提示区实际背景rgb(245,245,247)、边框rgb(229,229,233)；点簇放大、点选至单条原始记录、清除位置回到39条、IntAct来源→Full collection进入10条分页且无重复Choose控件通过。浏览器无JS错误，仅既有Molstar截图触发WebGL性能提示。截图位于`output/playwright/qtl-navigation-20260929/{qtl,selected-position,interactions}.png`。不据此宣称完成全站或手机验收。


## 2026-09-29QTL轨道撤除与配色统一

用户要求删除轨道并跟随后续全站配色，本次替代上面的QTL轨道试行。已移除`QtlPositionViewer`、专用坐标API/辅助模块及其测试，原QTL接口恢复既有来源/组织/类型筛选与分页。前端自动清除旧URL的qtl_chromosome/qtl_position/qtl_assembly，避免残留位置筛选。互作来源/集合入口精简继续保留。

QTL样式在`ios-surfaces.css`中按`#qtl`限定，复用当前全站surface/text/border/primary变量：去金色模块强调、彩色数量和绿色P值底块；白底、浅灰说明区、细灰边、柔和蓝色组织统计条和蓝色交互状态。类型文字不套彩色框，来源卡片/类型按钮明确标示选中态；身体示意图原有解剖区域色保留。原来源阈值和自定义P值比较逻辑、全部记录及临床含义不变。

验证：TypeScript/Vite构建与原QTL跨dataset分页测试通过；1414×827实页确认轨道0、旧坐标参数已清除、apaQTL完整39条；P值命中文字为rgb(0,102,204)且底色透明，说明区为rgb(245,245,247)、组织条rgb(144,189,235)。自定义参考1e-6产生24条命中/15条其他，仍为39条。记录和组织面板截图在`output/playwright/qtl-restyle-20260929/`（截图时仅临时隐藏悬浮导航遮挡，不修改页面功能）。本地8000服务及构建已更新。


## 2026-09-29四处密度与交互批注

用户四处浏览器批注要求压缩概览和生化区、明确点击入口、对齐Guide to Pharmacology入口与内容、删除结构Start/End输入及Visible residues区，悬停蓝条显示残基，并改善变异表字号。实现由`Overview.tsx`、`StructureSequenceSelector.tsx`及其CSS、`ios-surfaces.css`维护。生化来源入口和预览置于同一列，去重复来源标题；来源卡片保留细边框。后续批注采用图标入口、膜分类与底部动作无框，替代初版普遍加框与View文字的方案。结构保留全长映射条、拖动范围、端点键盘调整和Reset，悬停显示序列字母/位置及chain/结构编号，未映射时明确说明；移除局部32残基窗口及其浏览逻辑。Ref/Alt字母12→17px，consequence 13→15px。数据和科学规则未改。

2026-09-29 13:45 HKT附近，独立Playwright浏览器在1414×827、EGFR（P00533）验证：三个概览详情入口可开关；L606悬停显示Chain A/residue 606；拖动创建选区、方向键端点+1、Esc清除、End从空选区创建1210位置、Reset通过。浏览器实测字母17px、后果15px；Rhea/GtoPdb入口与内容左边分别45/715px，两侧预览顶部相同。结构选择区约173px高，身份卡约154px。TypeScript/Vite候选构建及diff空白检查通过；截图在工作区`output/playwright/density-{overview,reactions,structure,hover,variants}.png`，其中reactions截图早于最后12px预览顶部对齐修订，最终对齐已通过DOM坐标核对。

5173开发预览自动更新；候选构建位于`/tmp/memvar-ui-density-build`，未发布到8000静态目录。应用内浏览器无可连接实例，因此不宣称直接检查用户61290转发页面。其他任务同时修改AlphaGenome前后端；开发页观察到AVI接口404和热更新期间依赖数组变长提示，未改其代码或重启后端。验证仅覆盖本轮EGFR桌面变化，不代表全站、移动端或AlphaGenome新链路验收。


### 同日跟进：11条轻量呈现批注

移除膜分类、两个底部入口和药理预览action标签框；功能来源链接取消下划线。Rhea/GtoPdb使用已有Lucide ArrowRight，仅保留图标及悬停提示，整个来源入口仍可点击。Cellular location两个原生select取消贴边的系统箭头，改固定16px箭头、距右侧10px及34px文字预留区。Prediction toolkit主容器改共享白底。频率列移除地球图标、15px中等字重与等宽数字，原e计数只改排版为×10上标指数；原百分比换算、有效位数、零/缺失、色标与点击详情保持。

5173 EGFR 1414×827定向核对：相关边框均0px、来源链接text-decoration为none、预测区rgb(255,255,255)、AF图标0个、指数使用sup；Source HPA/All sources和scope Isoform 2/All available objects切换、两处图标入口弹窗及频率人口详情开关通过。TypeScript/Vite候选构建通过。截图`output/playwright/density-followup-{location,reactions,frequency}.png`；仍仅更新开发预览，未重启后端或覆盖8000静态目录。


## 2026-09-29落实分析第3–6点

授权：表格比较、组件质感、字体角色和动效；未采用第1–2点的对象标题重排、按宽度分类弹窗或右侧详情栏。新`EvidenceNumber.tsx`复用调用方既有格式化结果，只将e计数转为×10上标，接入主表AF、详情总AF/各population/原AF/图注最大值和预测读数。共用DataTable增加scope=col与列/行定位属性，主表数值列右对齐；portal详情表格采用共享字体、细横边、固定表头，正文作为滚动容器。频率读数取消蓝/青/紫装饰背景和顶部彩线，保留AF原科学颜色、组数、AC/AN、来源、图例与量尺。预测详情容器去装饰渐变，分类/评分语义保留。身份表复制控件在悬停/键盘焦点显示，粗指针常显，成功/失败有状态文本。

`ios-surfaces.css`统一report与dialog-body文字角色和数值字形；频率指标22px、子组17px、正文15px、辅助13px，主表沿用14px正文/17px残基。`lib/motion.tsx`内容过渡140ms、展开180ms；保留既有弹窗200ms和分段弹簧，表格高频按钮禁缩放，减少动态关闭过渡。

回归检查发现原Modal的opener在表格重绘后isConnected=false，导致关闭后焦点落回body。已在共用Modal记录原表格行/列及控件序号，在关闭/父状态更新后优先返回原元素，原元素重建则找到同位置新控件；不抢占其他新打开的dialog。临时诊断日志已移除。

验证：TypeScript/Vite最终候选构建、diff空白检查通过；EGFR 1414×827主表和频率详情均显示7.40×10⁻⁵%，关闭后焦点和表格scrollTop保持；身份表header在正文滚动300px后固定在内容视口，ENST00000275493.7复制内容准确；快速展开/收起、减少动态即时展开及dialog animation=none通过。截图`output/playwright/reading-{frequency,table,identifiers}.png`。只覆盖本批代表路径，未全量检查所有来源详情、设备或每个缺失分支。用户视觉反馈待续。

5173自动更新，候选构建`/tmp/memvar-ui-reading-build`；未覆盖8000静态产物、未重启后端或改动其他任务的AlphaGenome代码。

## 2026-09-29科学配色与详情视觉审查

用户要求统一科学配色，并指出Variant表格色彩不协调、转录本详情密集、GO证据代码区别不明显。当前已用指定序列11色替换旧预测8色、后果独立色和GO旧色；`lib/palette.ts`集中维护填色与深色文字、预测/后果/临床/频率/证据代码映射。链接取指定cerulean的可读深色，非方向分数与AF末端取oxford navy。移除两份旧consequence文字覆盖，预测详情donut图例同步接入；临床/稳定性详情保持中性底，仅保留语义文字和小面积边线。

转录本详情去掉蓝绿套框、ID及变化值小卡，采用17px标题、13px说明、15–16px身份/变更值和20–24px节间距；全长序列关系为浅灰说明区，边线不编码匹配状态。所有来源说明与字段继续展示。GO/Reactome标签改为实色代码块＋中性说明；常见IDA、EXP、HDA分别为blue、sage、coral。有限色板允许代码间复用，代码和原始解释始终保留，颜色不表示证据等级。

验证：TypeScript/Vite候选构建至`/tmp/memvar-palette-build`通过；EGFR 1414×827实页核对主表、转录本、GO（IDA/EXP/HDA）、ClinVar及预测切换。临床Likely benign边线为`#67a583`；预测来源图例与共享色板一致。390px转录本详情单列、内容宽325px与滚动宽相等。对分类文字及两条连续色阶各101点抽样，最浅交互底`#f4f6f8`上最低对比4.62:1；全部证据代码块文字最低5.23:1。cerulean链接加深至`#417494`。`git diff --check`通过。截图位于科研工作区`output/playwright/palette-{table,transcript,go}.png`。

交付到5173开发服务；8000运行正常，本批未覆盖其静态产物或重启后端。内置浏览器仍无可用绑定，使用独立Playwright核对；未验证用户端61290转发。科学分类、评分方向/量尺/阈值、AF原值与零/缺失语义、代表转录本及序列关联均未改动。序列JSD/interface/binding保持用户此前专门确认的回退色；AlphaGenome与后端数据优化保持原任务。此记录是本轮区域验收，不代表所有页面和所有证据类型均已视觉验收。

## 2026-09-29PaxDB整合丰度直接展示

根据三处批注，Protein abundance整合视图将原组织计数条替换为组织名称、ppm原值和线性丰度条，直接放在人体导航旁的同一滚动区，撤除下方重复记录面板。Cells、Fluids & secretions及其余非组织整合类别不再重复展示All/单项筛选按钮；保留context type切换和点击名称查看数据集详情。Individual protein studies可能同组织多条，继续保留原来源导航/筛选，不聚合或选择代表丰度。

`PaxDbBrowser.tsx`复用同一丰度表渲染，`QtlTissueNavigator`新增可选列表内容槽，默认QTL/单项研究仍为原计数导航。整合值续页自动加载并保留失败重试，避免区域筛选只看到首个API页；后端API、来源记录、数值及分类不变。显示量尺取API当前context type的maximum；区域/搜索只筛选行，不重算maximum。`paxdb.css`处理内嵌表头、单滚动区及共享蓝色丰度条。

验证：TypeScript/Vite构建至`/tmp/memvar-pax-inline-build`及diff空白检查通过。EGFR实页整合组织37行、仅1张表；Brain/spinal cord筛选4行，搜索cerebral为1行，120 ppm原值及条宽前后一致，数据集详情可开关。Cells/Fluids各5行且重复筛选容器均为0；Cells原值14.0、0.011、58.4、53.2、8.25，Fluids原值17.6、7.34、17.4、3.17、0.749保持。Individual studies组织选择仍出现原数据集名和Clear selection，QTL仍渲染原导航（本页32行）。截图：科研工作区`output/playwright/pax-inline-{tissues,fluids}.png`。5173开发预览已更新；本批未覆盖8000静态版或重启后端，未验证用户61290端口转发。


## 2026-09-30结构位点邻域与变异悬停

选中位点同时在主链表示和球棍表示上使用洋红色；切换及清除选择恢复原注释配色。取消单残基默认紧贴镜头，使用 Mol* focusLoci 的 minRadius=20、extraRadius=12 保留空间邻域；这是结构浏览邻域，不是计算或确认的结合口袋。

`StructureViewer.tsx` 处理三维拾取事件、选中颜色和邻域镜头，`StructureSiteInspector.tsx` 独立读取已有位点变异 API。只对 exact_current_canonical 映射开放位点关联；替换来自匹配位置的 canonical_positions，ClinVar classification 与 oncogenicity 保留来源含义，缺失标为 Not classified。面板最多显示8条注释并提供完整证据入口，不生成突变后的结构。样式由 structure-site.css 维护。

验证：TypeScript/Vite 构建通过；EGFR P00533 真实浏览器验证10项，包括 L858 选中及20 Å最小镜头半径、主链/球棍着色、L858M/L858R不同临床注释、实际三维残基悬停与点击、切换后旧高亮消除、W898C缺失临床证据、390px窄屏面板边界，以及清除后恢复原色与移除标记。Mol* 原生点击会创建额外邻域表示，核对各表示的高亮均对应同一新位点而非以表示数量判断。截图保存在本地忽略目录 output/playwright/structure-pocket-{after,inspector,mobile}.png。无后端、数据或科学阈值改动；本轮未提交 GitHub。


## 2026-09-30预测器分数阅读优化

预测主表和详情复用 PredictionScale：原生0–1轴保留数值方向，蓝色表示较低预测影响、红色表示较高预测影响，SIFT等反向工具的颜色轴反转；黑色刻度显示原始数值位置。表头直接标明 Higher/Lower = more effect/impact。有来源分类的分数与标签按来源分类着色（红：damaging类；蓝：tolerated类；琥珀：uncertain类）。连续轴仅表达原始分数方向，不是来源分类分段，也不是工具间可比的校准概率；因此某些分数的位置与来源二分类颜色不同是预期行为。无来源分类不生成标签，未审查方向或无界分数不生成0–1轴；缺失无标尺，真实零保留。

CADD和AVI PHRED显示来源参考分布的近似上尾排名，Top百分比=100×10^(−PHRED/10)，保持原始PHRED数值；不是当前页面变异排名或患病概率。ESM1b只把已匹配来源类别D/T展开为Deleterious/Tolerated，不按−7.5重新分类。依据：[dbNSFP5.4a字段字典](https://dist.genos.us/release/dbNSFP5.4a_variant.columns.txt)、[SIFT说明](https://sift.bii.a-star.edu.sg/www/SIFT_help.html)、[CADD原始/PHRED尺度说明](https://cadd.bihealth.org/info)，AVI沿用已确认predictor-guides来源解释。

本次局部替代预测面板此前绿/红及多色色阶；ClinVar、consequence、review stars与序列配色不改变。不添加ACMG证据强度或稳定性结论。实现位于PredictionScale.tsx、prediction-scale.css、PredictionValue和scoreVisual；主表方向组件共用。TypeScript/Vite构建通过；真实EGFR位点3检查正反方向标尺、来源分类、PHRED参考排名、缺失无条、表头无文本溢出，点击分数可打开预测详情。截图为本地output/playwright/prediction-scales.png。未变更后端数据，未提交GitHub。

2026-09-30排名强调补充：CADD/AVI共用PredictionValue中的Top百分比改为独立一行、14px加粗深色，reference rank保持次级说明；主表及预测详情同步生效，换算与来源含义不变。

2026-09-30后续视觉调整（替代本节红/蓝文字及分类框）：分数、方向提示和来源分类统一为中性深色，去掉方向底框与分类边框。颜色集中在0–1原生标尺、来源分类小圆点及PHRED排名填充条；Top百分比仍加粗。PHRED采用固定0–40显示轴（40+封顶），连续蓝→红插值、填充长度与原PHRED线性对应，用于展示不同上尾排名的差异；40不是科学分类阈值，也不是分数上限，悬停及端点明确说明。排名百分比公式不变，无阈值分类及后端改动。构建通过，真实页面确认无底框/边框、不同PHRED产生不同填充颜色，截图prediction-refined.png。


## 2026-09-30精细表面与原始预测分数参考

结构surface由coarse-surface改为Mol* molecular-surface（resolution 0.7 Å、probeRadius 1.4 Å、高质量、哑光材质），显式保留plddt-confidence主题以避免预设强制单色。Appearance新增Studio lighting · progressive（渐进光照、去噪、32次迭代），支持时使用GPU光照；不支持时Mol*回退标准绘制。Depth shading仍默认，插画骨架保留。未改坐标、来源分数或映射。

原始分数逐字段审查依据[dbNSFP5.4a官方字段字典](https://dist.genos.us/release/dbNSFP5.4a_variant.columns.txt)。维护位置predictor-references.ts和PredictionReference.tsx，虚线参考点＋实线当前值；说明和链接在预测详情展开。参考点：ESM1b −7.5/0（测试集参考/模型等偏好）；PROVEAN −2.5；BayesDel +AF 0.0692655、−AF −0.0570105；MetaSVM 0；MutationAssessor 0.8/1.935/3.5；GPN-MSA −7；popEVE −5.056/−4.617；MisFit S 0.0001噪声参考；bStatistic 0/1000。MPC、VARITY R/ER LOO、GERP++ RS只标来源范围，无临床界线。共14个字段配置。

ESM1b、PROVEAN、BayesDel、MetaSVM、MutationAssessor、GPN-MSA等轴范围取字典报告范围，仅作为绘图上下文，异常范围值扩展轴而不截掉。popEVE字典范围段误写ESM1b名称，本轮不引用该范围，采用包含当前值和参考点的局部视窗，并明确说明；不将其作为官方范围。bStatistic和MisFit使用定义范围；保守性/选择强度单独蓝色轴，不使用致病红蓝。CADD raw、Eigen raw/PC raw、GERP NR/92 mammals、phyloP17、AVI raw、AlphaGenome splicing等没有本轮可用通用分类参考，明确显示No established reference cutoff，不捏造分界。PHRED保留已实现排名视图。不按这些参考重新生成D/T或临床等级。


验证：TypeScript/Vite构建、git diff --check、14个参考配置有效值/范围检查通过；真实EGFR L858原始分数展示了ESM1b/PROVEAN参考线，预测详情能展开来源说明及链接。实际Mol*状态确认molecular-surface与plddt-confidence主题，Studio照明开/关正常，surface/backbone切换保留L858选择，悬停信息可用。第一轮悬停检查被同时打开的预测详情遮挡而超时，关闭详情后顺序复验通过。软件浏览器中精细表面重建和着色耗时明显高于旧粗表面，未承诺全蛋白性能，Ribbon默认不变。截图output/playwright/studio-surface.png、predictor-references.png；构建已更新，未推送GitHub。


## 2026-09-30插画骨架优化并设为默认

按用户明确要求，StructureViewer初始表示改为Illustrated backbone，默认Clear colours · outlined；替代前述Ribbon默认决定。骨架sizeFactor由0.55增至0.65、径向分段32，保留离散残基颜色colorMode=default与圆柱/球形接头。插画模式使用正交投影，灰轮廓#78828d，局部遮蔽半径4→2.4、bias 0.8→1.2、遮蔽色改为浅灰#b2bac3；减弱阴影对颜色的干扰。Ribbon/Surface及其他外观仍可选；来源颜色映射、坐标、位点关联不变。

验证：TypeScript/Vite构建及git diff --check通过；浏览器刷新后默认backbone，实际表示sizeFactor=0.65，膜注释着色与L858选中/悬停面板正常。截图output/playwright/illustrated-default.png。仅本地预览构建更新，未提交GitHub。


## 2026-09-30SPPIDER伙伴位点轨道

此处分行方案已由下方“坐标轴标记与悬停卡片”替代，阈值依据继续有效。

用户要求Binding interface下新增SPPIDER预测位点，并明确授权查作者/analysis阈值后采用阈值标记。科学定义与来源证据统一维护于科研工作区`modules/PPI/docs/rules.md`的“SPPIDER-seq网站位点标记”：≥0.5，默认query-as-receptor、可切换query-as-peptide，伙伴和两个head独立，不做Q6分析中的跨伙伴并集，不加FDR过滤。正式Parquet、PostgreSQL原值和API未改。

`SppiderPartnerTrack.tsx`调用既有伙伴及逐伙伴分数API，每页4个伙伴，支持accession搜索及分页；标签保留同序列accession别名，悬停说明其共享伙伴序列。每行用一种颜色区分伙伴，孤立达标位点为圆点、相邻达标位点合并条带，空缺/低于阈值打断。`sppider-sites.ts`集中维护显示判定和连续段；原分数、角色和是否达标在悬停展示。点击与键盘选择沿用残基证据面板；最低绘图宽度的小标记按自身残基范围拾取，避免全长缩放时误选相邻位置。

JSD及PeSTo曲线下的逐位色带和横向0–1图例删除，保留曲线、纵轴、原值悬停与位点操作；不改既有连续配色。此次展示更新补充此前保留逐残基色带的要求。

验证：TypeScript/Vite构建、diff空白检查通过；`node --experimental-strip-types --test frontend/tests/sppider-sites.test.mjs`两项通过，覆盖阈值等号、缺失/非法值、间隔、窗口裁剪及空结果。EGFR实页首4伙伴receptor达标位点为15/16/17/13；首伙伴peptide为1，与API逐值计数一致；搜索Q9Y5S9、下一页、角色切换和键盘读取正常。悬停F287显示原值0.50417066（显示0.5042）与伙伴；点击圆点打开F287残基证据。首次点击测试发现像素取整可选邻位，已按标记范围修复并刷新构建后复验通过。截图`output/playwright/sppider-sites.png`、`sppider-hover.png`。已更新8000静态预览；未提交GitHub，未进行全库性能测试。


## 2026-09-30SPPIDER坐标轴标记与悬停卡片

用户明确不要独立伙伴轨道，改为原坐标轴圆点及悬停展开。删除SppiderPartnerTrack和对应CSS，在Binding interface下的既有ResidueAxis上叠加SppiderSiteMarkers；不增加独立行、顶部重复标记、伙伴搜索或常驻分页。点放大与卡片淡入/缩放支持reduced motion，Portal和边缘避让避免被轨道裁切；鼠标可进入卡片操作。同坐标多个伙伴只画一个标记，12px内相邻坐标收拢并在卡片提供具体残基选择，屏幕分组不生成代表分数或合并科学记录。

新增只读sppider-markers与逐位伙伴接口，查询全部当前query预测，不再只显示首4个伙伴；严格沿用PPI规则的receptor≥0.5，旧连续曲线的两个query head仍可切换。原始分数、accession别名及direction_evidence→context_dataset的数据库来源在卡片逐伙伴显示，来源查全不使用原先LIMIT 20证据截断；每页6个伙伴。颜色仅用于卡片伙伴识别，不能解释为结合强度。数据表与原始分数不修改。

验证：前端两项屏幕分组测试保留全部坐标/计数且缩放可分离；后端两项实库测试核对F287全量78个伙伴与marker计数一致、原分数一致、来源dataset集合一致、角色和坐标参数验证。EGFR查询有595个receptor达标坐标，查询实测约0.13秒（仅此样本）。真实浏览器确认旧轨道行数为0，悬停出现来源IntAct/BioGRID及分数，进入卡片后可切换近邻F150并打开对应位点证据。TypeScript/Vite与diff检查通过。截图output/playwright/sppider-axis-card.png。更新8000服务与静态构建，未提交GitHub。


## 2026-09-30默认骨架Confidence着色修复

用户报告Illustrated backbone在Confidence下整链单色。实页状态确认实际colorTheme为chain-id；Ribbon→backbone回归断言在修复前稳定失败。单独恢复plddt-confidence后clearSelection不会破坏主题，定位为representation type切换时未指定colorTheme，Mol*重置为该表示默认chain-id。StructureViewer的backbone updateRepresentations显式携带plddt-confidence，与surface已采用的处理一致；注释和选中位点仍在该基础主题上overpaint。

验证：TypeScript/Vite、diff检查通过；真实浏览器首次加载默认backbone、Ribbon→backbone、Membrane topology→Confidence均保留plddt-confidence。实际残基颜色采样得到#0053d6/#65cbf3/#ffdb13/#ff7d45，与pLDDT图例一致。截图output/playwright/backbone-confidence-fixed.png。回归在真实渲染器完成，没有引入仅匹配源码文本的伪单元测试；未加产品调试代码。8000构建已更新，未提交GitHub。


## 2026-09-30本批GitHub发布

用户授权提交当前网站改动：结构位点邻域/悬停、默认Illustrated backbone与Confidence修复、预测器参考标尺/PHRED排名、SPPIDER坐标轴标记及来源卡片。本批前端构建、定向接口/坐标分组测试和真实浏览器验证见上述各节。数据、凭据及运行截图不随代码发布；独立DuckDB＋Parquet迁移规划保持本地未提交。


## 2026-09-30膜拓扑来源选择

用户澄清扩展Membrane topology来源，而不是新增domain板块。Sequence Viewer把Topology选择移至Membrane行侧边，默认UniProt；共享TopologySourcePicker提供按来源分组的来源/方法勾选、搜索和重置。来源取既有sequence API的已映射topology options：DeepTMHMM2、HTP各预测方法/整合结果、TOPDB及TmAlphaFold等按实际蛋白可用项展示。多选沿用独立纵向lane和同一SVG横坐标，侧栏与整轨宽度不增加；菜单区分prediction/source annotation/experimental/integrated/structure-derived，不合并来源事实。

StructureViewer新增Topology by source单选，取所选topology_id的现有序列位置着色，移除仅UniProt的硬编码过滤。不同来源的3D结果逐项切换，不构建跨来源共识；切换来源时不保留旧来源数据作为新来源颜色。沿用模型exact_current_canonical映射门槛、位点选中覆盖与Confidence基础主题；API、数据库和预测均不修改。

用户最终选择浅色方案，替代大片深靛配色：membrane-palette.ts集中五色，跨膜区#f28482、胞内#f5cac3、胞外#84a59d、信号区#f6bd60、其他拓扑类型#f7ede2。sequence-model和MembraneTrack共用，三维图及图例随之同步；分类规则和缺失灰色保留，页面继续白底。

验证：TypeScript/Vite和diff检查通过。EGFR Sequence Viewer默认UniProt，双选DeepTMHMM2、三选HTP/Hmmtop后宽度均为1376px，重置恢复UniProt。真实结构默认来源UniProt，DeepTMHMM2着色覆盖1210残基（含其signal/Extracellular/TMhelix/Cytoplasmic四段），HTP/Hmmtop切换、切回Confidence通过；实际Mol* overpaint核对四类新颜色与图例一致。第一次自动化用check等待已自动关闭的radio弹层而超时，改为click并核对最终渲染状态后通过；三lane文字检索因含序号导致exact定位超时，DOM复核及重置操作通过。截图output/playwright/topology-sequence-sources.png、topology-structure-deeptmhmm2.png（改色前交互）及topology-warm-palette.png（上一版配色；后续按用户要求更新为浅色，重新通过构建与diff检查）。8000构建已更新；本批按用户要求提交GitHub，独立DuckDB＋Parquet迁移规划保留本地。
