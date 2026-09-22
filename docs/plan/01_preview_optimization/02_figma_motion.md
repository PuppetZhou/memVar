# 02 Figma视觉协作与动效方向沿革

2026-09-22追加：用户已选定shadcn/ui＋Motion＋Radix Colors＋Lucide/Tabler。当前工程采用与调用方法以[03工具接入方案](03_ui_toolkit.md)为准；Motion替代本文件此前React Bits主要候选路线。下方保留Figma设计brief及前期候选依据，不作为安装React Bits/GSAP的指令。Figma画布仍未交付。

## 分工与设计交付

Figma用于确定页面层级、字体/间距/边框/颜色token、可复用组件及交互状态；Motion用于React实现中的主要动效，React Bits仅保留可选参考。采用哪个工具与最终审美效果是两件事，先用同一组真实内容比较，不默认搬用其展示站整体配色。

建议一个设计文件按页面组织：`00 Foundations`（token与字体）、`01 Components`（按钮/来源标签/筛选/证据弹层）、`02 Protein workspace`（基础信息与细胞图）、`03 Sequence and variant`（Atlas/结构/预测）、`04 Expression`（样本热图）、`05 Desktop states`（空/错/加载及键盘状态）。重复元素用组件实例，组件样式和状态统一维护。手机及390px窄屏设计按2026-09-22用户决定延后，不纳入当前样稿验收。

首批设计两种轻量方向供比较：

- **A：清晰科研工作台（推荐）**。白/近白背景、细灰边框、蓝色主操作、小范围来源色；数据字重与留白建立层级，尽量少用大面积彩底。现有英语界面与真实ID/长名称保留。
- **B：柔和层次**。同一信息结构，增加极浅蓝灰分区、局部柔和阴影和有限透明度；透明效果只用于浮层/导航，不用于数值表和热图。

两种方向用P00533及Q12809的实际页面内容，至少覆盖一段GO/来源证据、一块密集残基格、一张完整评分卡和表达样本区域；占位内容明确标“设计样例”，不编造科学数值。局部组件通过后再扩展页面，不要求先重画整个站点。

字体先核对当前页面实际字体和Figma可用字体，再比较一种清晰sans-serif（候选Inter/现有系统字体）；残基/基因组字符用等宽字体或数字特性。正文不依赖低透明度灰字制造层次。具体选型在样稿中决定，不提前引入大体积字体包。

## 前期React Bits候选依据（当前不采用为主动效库）

官方仓库提供可选择技术版本的组件，当前项目是React 19、TypeScript及普通CSS，优先采用对应TS/CSS实现，无需为动效重搭前端。[官方仓库](https://github.com/DavidHDev/react-bits)。

| 候选/实现 | 本项目用途 | 调整与验收 |
| --- | --- | --- |
| [Fade Content](https://www.reactbits.dev/animations/fade-content) | 初次出现的说明/概览区域、必要弹层内容 | 建议150–220ms、不开文字模糊；只对完整区域触发，不逐行隐藏证据 |
| [Animated Content](https://www.reactbits.dev/animations/animated-content) | 首页小段内容或卡片的轻量进入 | 建议4–8px位移、180–240ms、最多一小组错峰；滚动时不反复移走已读内容 |
| [Spotlight Card](https://www.reactbits.dev/components/spotlight-card) | 少量首页来源入口的候选反馈 | 弱光照且保持文字对比；不用于所有数据卡，更不挂到每个残基或热图格 |
| 局部CSS/共享组件状态 | 残基、PTM点、按钮hover、选中框、筛选chip | 约100–160ms transform/边框过渡；PTM保持高对比；键盘focus与触摸具备等效操作 |
| 稳定的展开/收起 | GO详情、ClinVar条件、来源解释 | 最终位置稳定、焦点可返回；查看数据的操作不等待完整长动画 |

2026-09-22核对官方源码：TS/CSS版本FadeContent与AnimatedContent使用`gsap`/`ScrollTrigger`，当前项目package.json没有GSAP；SpotlightCard使用React＋CSS。不能误写成“只需现有Motion依赖”。实际选择后仅安装所需依赖，固定组件来源/版本并做局部包体和交互核对。[Fade源码](https://github.com/DavidHDev/react-bits/blob/main/src/ts-default/Animations/FadeContent/FadeContent.tsx)、[Animated源码](https://github.com/DavidHDev/react-bits/blob/main/src/ts-default/Animations/AnimatedContent/AnimatedContent.tsx)、[Spotlight源码](https://github.com/DavidHDev/react-bits/blob/main/src/ts-default/Components/SpotlightCard/SpotlightCard.tsx)。建议时长/位移是本项目设计值，不是照抄库默认值。

不采用全站光标尾迹、持续粒子、文字逐字解密、大幅倾斜卡片等作为数据阅读默认行为；这类演示不解决本轮反馈中的密集信息可读性。若首页确实需要装饰背景，单独比较一处即可，不扩散到蛋白详情。

## 共享设计与科学图层

- Figma的标签色、间距、圆角等token对应前端CSS变量；科学图表色板另列，source/type/临床原分类/JSD/variant count各自语义保持一致。
- Atlas与structure使用相同的计数分档和JSD色阶。一般PTM标记统一，PTM type模式才展开13类配色；数据不同来源不因颜色相同变成统一证据。
- hover/focus/selected/loading/empty/error都要设计；数值筛选与图表状态不靠动画结束才生效。
- 尊重`prefers-reduced-motion`：减少动效时立即显示最终内容，保留高亮、焦点和tooltip信息。千位残基或大量热图格不各自建立重动画实例。
- Figma确认的是静态信息层级与状态；真实残基/结构联动、热图性能和动效时序必须在现有React中做有界原型验证，不能只用设计截图验收。

## 本轮实际核查状态与下一步

已读取Figma相关技能；插件目录查询显示Figma已安装且启用，但本会话可调用工具列表中没有`use_figma`、截图或新建文件工具，且未发现可用tool-search入口。因此本轮没有创建Figma文件，不要求重复安装。后续能调用Figma连接后，优先复用用户指定文件；未指定则创建独立样稿文件并交付可审阅链接。当前设计brief和数据方案可继续推进。

React Bits页面为客户端渲染，普通网页读取无法展示交互；本轮核对了官方索引、仓库和三个TS组件源码，未实际浏览器验收其视觉，也未安装组件。导入采用组件时保留其官方来源与许可文本，不把外部组件抹去署名。

2026-09-22并行实现选择方向A的轻量科研工作台取值，已将共享CSS token、焦点/按钮/标签状态及少量局部CSS动效直接构建到React页面；没有引入React Bits或GSAP依赖，不声称完成React Bits组件试用。此选择减少当前密集数据页面的动画负担；具体桌面观感尚未通过浏览器验收。Figma工具在本会话仍不可调用，文件/画布/两种方向的真实数据样稿未创建，UI-02继续待完成。后续能调用Figma时先比较真实样稿，再决定是否需要额外组件；不以本文件或代码token代替设计交付。[执行与验证记录](../../record/01_preview_optimization/20260922_parallel_web_execution.md)。
