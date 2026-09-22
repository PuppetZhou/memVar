# Medical / Clinical Portal 设计参考审查

日期：2026-09-23。状态：技能已安装、检索已验证；以下为候选设计建议，尚未改动网站外观或科学规则。

## 安装与依据

- 官方 npm 包 `ui-ux-pro-max-cli@2.15.0` 已安装；在 Web 执行 `uipro init --ai codex`，生成 `.agents/skills/ui-ux-pro-max/`。入口为该目录的 SKILL.md，检索脚本为 scripts/search.py。项目级安装，不增加网站运行依赖。
- 官方 main 的审查快照为 `dcc40ff5133ef78276117db0cc34e7b83cc8aeba`；npm 版本与 main 不保证一致。main 文档给出的 --dry-run 在 2.15.0 不受支持；普通安装成功。
- 实际读取安装后的规则，并成功运行医疗设计系统和 Medical Clean 字体检索。技能可在下轮由助手发现，本轮已直接读取使用。
- 官方仓库：https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- 已验证医疗范例：https://uupm.cc/demo/medical-clinic 。包括服务、医生卡片、Patient Portal 展示区和预约表单；未确认它等同于用户所指的独立 Medical / Clinical Portal 示例，不宣称精确复刻。

## Medical 资源

本技能是设计规则、配色、字体和代码建议库，不是人体/器官图片素材库。

| 资源 | 已核对内容 | 适配判断 |
| --- | --- | --- |
| Medical Clinic（products/colors 第58项） | 主色 #0891B2、次色 #22D3EE、背景 #F0FDFA、文字 #134E4A；建议可访问性与极简风格 | 青色可呼应 Logo；高亮青与绿色按钮不宜全站照用 |
| Patient Portal / Health Records（第182项） | 主色 #0284C7、次色 #0891B2、背景 #F0F9FF、文字 #0C4A6E、白色卡片 | 借鉴信息层级和概要到详情结构；不添加患者/预约业务 |
| Medical Clean（typography 第30项） | Figtree 标题 + Noto Sans 正文 | 可作字体对照；已有 Inter 可继续保留，数值优先使用等宽数字 |
| Minimalism & Swiss Style | 网格、无衬线字体、清楚层级、少装饰、明确对比 | 适合科研工具，控制留白避免降低数据密度 |

自动 --design-system 检索两次仍混入销售 CTA、营销结构及 Lora/Raleway 康养字体，未将生成结果持久化为正式 MASTER。产品原始记录和定向字体检索更适合本项目。React 泛检索结果也不能作为已完成性能审查的证据。

## 保留与优化

| 当前部分 | 保留 | 候选优化 |
| --- | --- | --- |
| 导航与总体架构 | 九个科研板块、URL 定位、现有 React/Radix/Motion/API | 统一标题/控件/间距，不增加侧栏或迁移框架 |
| 膜特征与概览 | 来源并列、证据展开、GO 三列、Function 下方 Reactome | 加强膜特征的标题和布局地位，用留白替代重复框线 |
| 序列与结构 | 轨道、残基编号、范围选择、chain 和共享焦点 | 统一工具栏、选中态及帮助入口，不改绘图语义 |
| 变异目录 | 连续滚动、筛选、来源与预测分开、缺失和零区分 | 固定表头与数值对齐，轻背景表头；长列表性能单独按实际规模评估 |
| Expression/QTL | 人体图、可点击组织点、来源/类型筛选、手动阈值 | 精简控件装饰、统一筛选层级；不改显著性判定 |
| Interactions/Diseases | Full/Topic/Mutation 区分、证据详情及滚动 | 分类色保留在徽标和数据，背景统一中性 |
| 品牌与动效 | Logo、自有组织图、细胞定位图、现有 Motion | 统一图标线宽，短促状态反馈，不引入 GSAP 或营销轮播 |

## 候选视觉规则（尚未采用）

中性近白页面、白色内容区、深石墨正文；临床蓝作为主要交互色，青色仅少量呼应 Logo。科学分类色独立于装饰色。控件、正文和密集表格采用分级尺寸，不机械照搬移动端 16px/44pt。序列和表格允许必要的局部横向滚动；不因通用规则删减科研数据。颜色以文本/图例补充，不单靠红绿表达证据。避免整块面板降低 opacity，保持辅助文字可读。

建议下一步：Overview 和变异目录先用真实 P00533/Q12809 做对照样稿，保留全部已确认交互；比较字体、主色、密度与层级后，再归并进现有设计系统并扩展其他模块。本轮只安装和研究，没有改动应用源码、重建数据库或恢复 ngrok。

## 第一版实施（2026-09-23）

用户确认仅优化字体、按钮、背景和外围方框。已在现有 refined-surfaces.css 增加明确限定范围的 Medical shell 样式，标题/导航加载 Figtree，正文 Inter 保留；不覆盖共享科学色阶变量、表格单元格、序列轨道或 Molstar。后续本段状态优先于上文研究阶段的“尚未实施”。

验证：TypeScript/Vite 构建通过；独立 Playwright 在 localhost:8000/protein/P00533 的 1470×950、1230×837 下检查页面与截图，无横向溢出；膜详情打开和 Escape 关闭，结构 canvas 与模型/chain/样式控件存在。表头/单元格/位置数值、序列容器/轨道标签、结构残基区的计算样式（颜色、背景、字体、字号）与改动前逐项一致。Figtree 加载成功。无应用控制台错误，Molstar 有 WebGL ReadPixels 性能警告。内置 Browser 返回空实例列表，沿用此前用户允许的 Playwright 后备验证。截图在 /tmp/memvar-medical-1230.png；未做全量科学颜色逐像素比较或移动端验收。

## 第二版控件与详情统一（2026-09-23）

已获用户授权继续优化：统一概览三级标题 Figtree、底部文字操作的高度/焦点、来源入口与来源卡片的轻背景，保留选中边界及科学类别颜色。Expression/QTL/Interactions/Diseases 与详情内来源工具栏统一标签间距、36px 下拉框和轻边框按钮。共享详情弹窗统一标题栏、36px 关闭按钮、内容留白及独立滚动。仅修改限定容器的 CSS，不修改科研数据/轨道/结构着色。

验证：构建通过；localhost:8000 P00533 在 1230×837 与 1470×950 无横向溢出。膜详情打开/关闭正常，关闭后焦点返回触发按钮；QTL GTEx→QTLbase 下拉切换及 URL 状态更新成功。抽查变异单元格和序列容器/标签字体颜色一致。无应用 console error；WebGL ReadPixels 性能 warning 同前。截图 /tmp/memvar-portal-dialog.png、/tmp/memvar-portal-filters.png。Browser 实例列表仍为空，继续使用此前允许的 Playwright 后备。尚未逐一验收所有详情或移动端。

## 用户指定五色试版（2026-09-23）

上一轮青蓝背景已依用户要求回退。新试版采用用户指定 punch-red #e63946、honeydew #f1faee、frosted-blue #a8dadc、cerulean #457b9d、oxford-navy #1d3557。仅建立独立外围 token：蜜露白与白色混合为页面和工具栏底色，雾蓝与白色混合作边框，钢蓝用于选中/焦点，藏青用于外部标题。红色登记备用，不套用科学状态。内容卡片仍为白底；未更改原有共享科学颜色变量、数据单元格、序列或结构色阶。

验证：TypeScript/Vite 构建通过；P00533 在 1230×837 与 1470×950 无横向溢出；膜详情打开/Escape关闭正常；表格单元格与序列容器/标签的前景、背景、字体抽查与原基线一致。无应用 console error。截图 /tmp/memvar-honeydew.png。内置 Browser 返回空实例，继续使用已授权 Playwright 后备；未做移动端或全量数据状态验收。
