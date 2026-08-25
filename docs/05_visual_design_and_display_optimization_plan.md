# 05. 网站美化与科研数据展示优化计划

状态：已完成（M6.1–M6.5）  
调研日期：2026-08-11  
适用阶段：M1–M5 完成后的 M6 视觉与交互增强  
范围：只优化 `website/` 的展示层和必要的只读摘要接口；`View/` 继续保持只读，不改变既有科学语义。

实施验收（2026-08-11）：M6.1–M6.5 已完成；后端测试 43/43 通过，前端 production build 通过。已回归 P00533（正常/高密度）、P43627（稀疏）、SHORT（歧义）和 A0A0G2JS06（空数据）路径。当前执行环境未提供浏览器自动化或触屏实机，因此 1440/1024/768/390 px 的结论来自响应式 CSS、可访问替代内容和 HTTP 路径审查；最终像素级与真实触屏手势仍需人工浏览器复核。

## 1. 本阶段目标

本阶段不是重新建设网站，而是在现有可运行版本上完成四件事：

1. 建立统一、现代且适合科研数据库的视觉语言；
2. 让按钮、链接、标签页、卡片和展开操作具有清晰的点击反馈；
3. 将机器字段转换为人能直接理解的页面语言；
4. 重点升级 Identifiers、Sequence、Expression 和 Disease 四个信息密集模块。

最终页面应从“功能型科研原型”提升为“可用于论文配套发布的数据库门户”，同时保持现有搜索、坐标、来源、单位和证据粒度不变。

## 2. CATVariant 调研结论

### 2.1 已确认的实现方式

CATVariant 的公开源代码显示，其前端使用 React、Vite、TypeScript 和 Tailwind CSS，并使用 Radix UI primitives、Lucide icons、`class-variance-authority`、`react-window` 等成熟组件或工具。它并不是依靠复杂的全站动画框架，而是把以下方法稳定地组合在一起：

- 以白色和 slate 灰阶作为大面积背景；
- 以蓝色作为基础交互色，以紫色渐变作为品牌强调；
- 不同分析模块使用蓝、紫、青、绿、橙、玫红等局部强调色；
- 导航使用半透明背景、模糊和轻阴影形成悬浮层次；
- 卡片使用统一圆角、浅边框和低强度阴影；
- 图标放入彩色圆形底座，hover 时底色与图标颜色反转；
- hover、active、展开、加载和选中状态都具有短而明确的动画；
- 对复杂表格和长列表使用摘要优先、详情展开以及虚拟化思路；
- 代码包含 `prefers-reduced-motion`，允许用户关闭非必要动画。

CATVariant 当前可确认的主要颜色包括：

| 用途 | CATVariant 色值/形式 | MemVar 的借鉴方式 |
|---|---|---|
| 页面底色 | `#EEF4F7`，叠加低透明度 cyan/indigo/teal 径向光晕 | 保留安静浅底；只在首页使用更弱的环境光晕 |
| 基础主色 | `#2563EB` | 用于链接、focus 辅助和局部交互，不覆盖科学数据色 |
| 紫色强调 | `#7C3AED`、`#8B5CF6`、`#A855F7` | 用于品牌渐变、当前标签页和重点入口 |
| Hero 渐变 | `#6D28D9 → #7C3AED → #0EA5E9`；源码中也有 `#8E2DE2 → #4A00E0` | 改为更克制的蓝紫渐变，避免直接复制品牌 |
| 页面深色文字 | `#0F172A`、`#1E293B` | 作为 MemVar 主文字和标题色 |
| 次级文字 | `#64748B`、`#94A3B8` | 用于来源说明、单位和辅助字段 |
| 边框/浅背景 | `#E2E8F0`、`#F8FAFC` | 用于页面背景、卡片和表格分隔 |
| 数据强调色 | teal、cyan、green、amber、rose 等 | 固定到明确的数据轨道或来源，不随机分配 |

### 2.2 它的“点击感”来自什么

CATVariant 的交互反馈主要来自以下组合，而不是夸张动画：

- 可点击元素在 `180–300 ms` 内改变颜色、边框、阴影和位置；
- 卡片 hover 轻微上移约 `2 px`；
- 标签页 hover 轻微上移，按下时缩小到约 `0.98`；
- 展开内容使用淡入和小幅位移；
- 当前状态通过底部边线、图标底色和文字颜色同时表达；
- 选中位点使用描边、光晕或定位线持续提示；
- loading 使用 shimmer 或 progress，而不是让页面无反馈地等待。

### 2.3 MemVar 应借鉴和不应照搬的部分

应借鉴：

- 统一的颜色、间距、圆角、阴影和动效变量；
- 明确的 hover、active、focus 和 expanded 状态；
- 图标、文字、形状和颜色共同表达状态；
- 卡片摘要、展开详情和模块化数据视图；
- 对长列表和高密度位点使用聚合或虚拟化。

不应照搬：

- 不为模仿 CATVariant 而把现有 Next.js/CSS 整体迁移到 Vite/Tailwind；
- 不在科研数据表格中使用持续漂浮、脉冲或大面积光晕；
- 不用渐变色表达 pathogenicity、证据强度或跨数据库共识；
- 不复制 CATVariant 的品牌 logo、页面文案或专属视觉资产；
- 不引入 CATVariant 的 variant priority score。MemVar 继续禁止跨来源打分或投票。

## 3. MemVar 目标视觉系统

### 3.1 视觉定位

关键词：`protein-centric`、`scientific`、`calm`、`layered`、`interactive`。

- 页面背景安静，信息卡片清晰，不模拟电子病历；
- 品牌层使用蓝紫色，膜蛋白和拓扑层保留 teal；
- 数据色只表达固定的数据类型或来源；
- 首屏强调蛋白身份和证据覆盖，装饰不能与科学信息竞争；
- 默认采用紧凑密度，但保持足够行距和点击面积。

### 3.2 建议的全局颜色变量

| Token | 建议值 | 用途 |
|---|---:|---|
| `--color-ink` | `#0F172A` | 标题、主要正文 |
| `--color-muted` | `#64748B` | 辅助文字、来源、单位 |
| `--color-canvas` | `#F8FAFC` | 页面背景 |
| `--color-surface` | `#FFFFFF` | 卡片、表格、drawer |
| `--color-border` | `#E2E8F0` | 分隔线和默认边框 |
| `--color-primary` | `#4F46E5` | 主按钮、当前选区 |
| `--color-primary-hover` | `#4338CA` | 主按钮 hover |
| `--color-accent` | `#8B5CF6` | 品牌强调、标签页 |
| `--color-link` | `#2563EB` | 页面链接 |
| `--color-teal` | `#14B8A6` | 膜拓扑和结构语义 |
| `--color-focus` | `#F59E0B` | 键盘 focus ring |
| `--color-conflict` | `#B42318` | Disputed、Refuted、明确冲突 |
| `--color-success` | `#047857` | 明确成功状态，不表示跨来源证据共识 |

品牌渐变只用于首页 hero、小面积图标底座和主入口：

```css
linear-gradient(135deg, #2563EB 0%, #7C3AED 58%, #A855F7 100%)
```

禁止把品牌渐变应用到数据热图、连续数值图例或 classification badge。

### 3.3 科学数据固定色

| 数据层 | 主色 | 形状/辅助编码 |
|---|---:|---|
| Transmembrane topology | `#36B7A2` | 实心区段 |
| Cytoplasmic/extracellular | `#E8ECEF` / `#EEF4F6` | 浅色背景带并直标文字 |
| Pfam domain | `#6E82B7` | 圆角矩形和深色边框 |
| UniProt functional site | `#374151` | 短棒；active site 使用菱形 |
| JSD conservation | `#7D9FD6` | 连续折线和淡面积填充 |
| PTM | `#D99A2B` | 三角或棒棒糖；类型用图例细分 |
| Variant | `#D95F68` | 圆点棒棒糖或密度条 |
| 当前选择 | `#F47A52` | 垂直定位线和描边 |
| 缺失 | `#CBD5E1` | 斜纹，不当作数值 0 |

Variant 默认颜色仅表示“此处存在 variant”，不能默认表示致病性。

### 3.4 字体、间距、圆角和阴影

- 正文继续使用 Inter/system sans-serif；UniProt、Ensembl、HGVS、坐标和氨基酸序列使用 monospace；
- 正文基准 `16 px`，紧凑表格 `13–14 px`，辅助信息不低于 `12 px`；
- 间距采用 `4/8/12/16/24/32/48 px` 序列，避免组件各自使用任意值；
- 控件圆角 `8 px`，卡片 `12 px`，badge/pill 使用完整圆角；
- 默认卡片只使用浅阴影；只有弹层、drawer 和 hover 中的可点击卡片增加一级阴影；
- 静态信息卡片不应在 hover 时移动，避免误导用户认为可以点击。

## 4. 动效和交互反馈规范

### 4.1 通用动效变量

| 场景 | 时间 | 建议效果 |
|---|---:|---|
| hover 颜色/边框 | `160 ms` | `ease-out` |
| 按钮/标签按下 | `100–120 ms` | `translateY(1px) scale(.98)` |
| 卡片 hover | `180 ms` | 可点击卡片上移 `1–2 px` 并增加浅阴影 |
| disclosure 展开 | `220–260 ms` | 高度/opacity/小幅 `translateY` |
| drawer 打开 | `240 ms` | 淡入并从右侧或下方移动 `8 px` |
| 页面内容首次出现 | `300–450 ms` | 只播放一次的轻量 fade-up |

实现时只 transition 实际发生变化的属性，不统一使用 `transition: all`。

### 4.2 Link、Button 和 Tab

- 文本链接：颜色渐变 + 下划线从左到右出现；外部链接箭头 hover 时移动 `2 px`；
- 主按钮：蓝紫实色，hover 加深并上移 `1 px`，active 回落并缩小；
- 次按钮：白底浅边框，hover 出现淡紫背景；
- 标签页：当前项同时具有底部边线、文字色和 icon 背景，不只依赖颜色；
- 所有交互都保留清晰的 `:focus-visible`；
- touch 设备不依赖 hover；点击必须产生固定选择或展开状态。

### 4.3 动效边界

- 数据表格、JSD 曲线和热图不做无意义的持续呼吸动画；
- selected residue 可以短暂 pulse 一次，之后保持静态描边；
- loading shimmer 只在加载期间存在；
- 在 `prefers-reduced-motion: reduce` 下关闭平滑滚动、位移、缩放和持续动画，保留即时状态变化。

## 5. 全站字段显示规范

### 5.1 问题

当前多个组件会直接显示 `start_lost`、`gene_primary`、`explicitly_absent`、`site_parse_status` 等机器值。简单执行 `replaceAll("_", " ")` 只能得到 `start lost`，不能正确处理专业缩写、标点和固定术语。

### 5.2 解决方案

在前端建立唯一的展示转换层，例如：

```text
frontend/lib/display-labels.ts
├── FIELD_LABELS
├── BIOLOGICAL_TERM_LABELS
├── ACRONYM_RULES
├── formatFieldLabel()
└── formatTermLabel()
```

规则：

- 原始 API 值、筛选参数和数据文件继续保留机器格式；
- 只在页面最后一步转换显示名称；
- 筛选控件显示友好名称，但提交原始值；
- 字典中未登记的值使用安全 fallback：下划线转空格、首词大写、保留已知 acronym；
- 科学 ID、HGVS、数据库 accession、基因符号和蛋白序列绝不做格式化；
- 详情 tooltip 可按需显示 `Source value: start_lost`，方便追溯。

首批至少覆盖：

| 原始值 | 页面显示 |
|---|---|
| `start_lost` | Start lost |
| `stop_gained` | Stop gained |
| `missense_variant` | Missense variant |
| `splice_donor_variant` | Splice donor variant |
| `gene_primary` | Primary gene name |
| `isoform_synonym` | Isoform synonym |
| `explicitly_absent` | Explicitly absent |
| `p_value` | P value |
| `qtl_type` | QTL type |
| `genome_build` | Genome build |
| `moi` | Mode of inheritance |

验收时扫描所有公开页面，不允许把可控机器枚举以下划线形式直接展示给用户。

## 6. Identifiers and aliases 重构

### 6.1 当前问题

P00533 当前返回 38 条 identifier。页面将 UniProt、gene、alias、isoform、transcript 和 protein ID 平铺在同一三列网格中，重复的 Ensembl gene ID 也会出现多次，用户难以判断编号之间的关系。

### 6.2 新的信息层级

```text
Identifiers and aliases
├── Primary identity
│   ├── UniProt accession
│   ├── UniProt entry name
│   └── Gene symbol
├── Gene identifiers
│   ├── HGNC
│   ├── NCBI Gene
│   └── Ensembl Gene
├── Gene aliases
│   ├── Primary gene name
│   └── Synonyms
└── Isoforms and transcripts
    └── Isoform group
        ├── UniProt isoform ID / synonym
        ├── Ensembl transcript / protein
        └── RefSeq transcript / protein
```

### 6.3 展示与交互

- Primary identity 和 Gene identifiers 默认展开；
- Gene aliases 默认紧凑显示为 chips，超过 8 个后使用 `Show all`；
- Isoforms and transcripts 默认折叠，并按 `isoform_id` 分组；
- 编号按数据库和完整 ID 去重，不能丢失一对多映射；
- 每个稳定编号提供复制按钮；能可靠构造链接时提供外部数据库链接；
- 复制成功使用短暂 check 状态和 `aria-live` 提示；
- 组标题显示数量，例如 `Isoforms and transcripts · 12`。

当前 overview API 已包含初版分组所需字段。第一轮优先在前端分组，不修改 ETL；只有发现无法可靠关联 transcript 与 isoform 时，才设计窄的后端 view。

## 7. Canonical sequence explorer 升级

### 7.1 目标布局

用户概念图中的核心是所有数据共享一条蛋白坐标轴。MemVar 应在 CATVariant 序列视图基础上补充 JSD、PTM 和更强的密集数据处理：

```text
Track toolbar        range · zoom · reset · legend · track toggles

Sequence minimap     full protein + draggable brush
Topology             cytoplasmic / transmembrane / extracellular
Pfam                 domain intervals
UniProt sites        active / binding / metal / other
Conservation (JSD)   continuous line + confidence indication
PTM                  lollipops / clustered sites
Variants             density → clusters → individual lollipops
Coordinate axis      canonical protein position (aa)
Residue row          only shown when sufficiently zoomed in

Pinned drawer        evidence at selected residue or range
```

### 7.2 多尺度显示规则

- 全蛋白尺度：Topology/Pfam 显示区间；JSD、PTM 和 variant 显示有界分箱结果；
- 中等尺度：相邻 PTM/variant 聚类，圆点显示记录数；
- 约 `100–300 aa`：显示单个位点和棒棒糖；
- 约 `50–100 aa`：显示氨基酸字母、精确坐标和 residue JSD 色阶；
- JSD 缩小时保留每个像素区间的 mean 与 min–max 范围，不能简单抽样丢失峰值；
- Pfam/feature 重叠时分配 2–3 条子 lane，超出后显示 `+N overlapping annotations`；
- 取消当前 variant 120 项和其他轨道 80 项的静默截断，改为完整计数下的聚合显示。

### 7.3 交互

- hover/focus：结构化 tooltip 显示类型、位置、描述、来源和原始值；
- click/Enter：固定选区、绘制垂直定位线并打开 Site evidence drawer；
- 单击 density bin：自动放大到该区段；
- 单击 Pfam：高亮 domain，并提供只看重叠 PTM/variant；
- 单击 variant：显示 HGVSp、记录来源数和 `View in variant table`；
- brush、数字区间、URL `site/range`、residue、drawer 和 variant table 使用同一 selection state；
- 键盘使用左右键移动 residue、`+/-` 缩放、Enter 固定、Esc 关闭 drawer；
- tooltip 同时支持鼠标、键盘和触屏点击。

### 7.4 推荐实现

- React 管理筛选、选区、URL 和 drawer 状态；
- D3 scale/brush 只负责坐标计算、缩放和 brush；
- SVG 绘制坐标轴、Topology、Pfam、UniProt sites 和可访问的选中标记；
- Canvas 绘制高密度 JSD、PTM 和 variant；
- 保留隐藏的结构化摘要或列表供屏幕阅读器使用；
- 不为 10,000 个 variant 创建 10,000 个 DOM button。

为了支持全蛋白 minimap，可以增加一个有界只读摘要接口：

```text
GET /api/v1/proteins/{accession}/sequence/overview?bins=400
```

返回内容仅包括完整 Topology/Pfam 小型区间、JSD bin 的 mean/min/max、PTM/variant bin count 和总数。`bins` 设置上限，禁止返回完整 variant fact set。

### 7.5 Sequence 验收标准

- 所有轨道严格对齐 canonical 1-based 坐标；
- 1,500 aa 和约 10,000 个 variant 时仍可流畅缩放、hover 和点击；
- 缩小只改变呈现粒度，不丢失记录计数；
- JSD 有独立连续轨道，tooltip 显示原始 JSD 和 confidence；
- 当前选区同步到 drawer、URL 和 variant filter；
- 鼠标、键盘、触屏和 reduced-motion 模式均可完成核心操作。

## 8. Expression 总览热图与折叠明细

### 8.1 页面结构

```text
Expression
├── Source-faceted expression overview
│   ├── HPA RNA row
│   ├── HPA MS row
│   ├── HPA IHC row
│   └── PaxDB row
└── Source details
    ├── HPA RNA accordion
    ├── HPA MS accordion
    ├── HPA IHC accordion
    └── PaxDB accordion
```

二维总览的列是经过 display crosswalk 排序的 tissue/body-system。这个 crosswalk 只用于导航和显示分组，必须保留原始 source tissue/organ，不能宣称不同来源的组织术语或数值可以直接比较。

### 8.2 四行独立尺度

| Modality | 色阶/形式 | 规则 |
|---|---|---|
| HPA RNA | `#E6F5F2 → #0F766E` | 行内 `log10(1+nTPM)`，tooltip 给 raw nTPM |
| HPA MS | `#EDF2FB → #315A9D` | 独立 intensity scale，明确标注显示变换 |
| HPA IHC | amber categorical palette | Not detected/Low/Medium/High，不能作为连续数值 |
| PaxDB | `#F3EFF9 → #6B4FA1` | 独立 ppm scale，明确标注显示变换 |

不得使用一个覆盖四行的共同连续色标，也不得生成跨 modality 的总表达分数。

### 8.3 多记录、缺失和折叠规则

- PaxDB 同一 organ 有多个 dataset 时，不静默平均；cell 显示 `n datasets` 或细分小条，tooltip 列出 dataset 和 ppm；
- HPA IHC 同一 tissue 有多个 cell type 时，cell 显示分类分布，不用最大值代表整个 tissue；
- NULL 使用斜纹；数值 0 使用最低色阶；IHC `Not detected` 使用明确分类，三者视觉不同；
- 热图默认约 `20–24 px` 一格，固定左侧 modality 标签，tissue 较多时水平滚动；
- 四个 modality 明细默认折叠；
- 展开后先显示 `10–12` 个 tissue，按钮写明 `Show all 40 tissues`；
- 展开全部后按 body system 分组，并提供名称/数值排序；
- 点击热图 cell 自动展开对应 modality 并定位到 tissue；
- accordion summary 显示来源、单位、记录数、tissue 数和 missing 数。

可使用 Apache ECharts 绘制总览，同时保留可访问的表格替代视图。初版先并行复用四个现有小型 expression 请求；只有当 payload 或延迟超出目标时，再增加专用 summary endpoint。

### 8.4 Expression 验收标准

- 第一屏可以同时看到四类 expression 覆盖；
- 每一行具有独立单位、色标和解释；
- tooltip 含 raw value、unit、source、release、原始 tissue/organ 和 PaxDB dataset；
- 40 个 tissue 不再默认形成超长纵向页面；
- NULL、0 和 IHC Not detected 不混淆；
- 多 dataset 和多 cell type 不被静默平均。

## 9. Disease evidence 摘要与展开

### 9.1 新的两级 disclosure

```text
Disease source overview
└── Source card
    ├── source badge + 一句话语义
    ├── 记录数 / disease 数 / source-specific summary
    ├── 最多 2–3 条预览
    └── Expand source
        └── assertion rows
            └── HPO phenotype disclosure
```

首屏应在一个常见桌面屏幕内浏览所有来源概况，不再默认铺开全部 assertion 字段。

### 9.2 各来源预览

- ClinGen validity：记录数、疾病数、来源内部 classification 分布；预览 disease、classification、MOI；
- ClinGen dosage：HI/TS 概况；预览 disease、HI、TS 和日期；
- GenCC：assertion 数、独立 disease 数、submitter 数；相同疾病可以分组，但 assertion 独立；
- OMIM：疾病数；预览 disease、inheritance、mapping key 和 relationship status；
- HPO：作为具体 disease 的 phenotype 下钻；Observed、Explicitly absent 和 Inheritance 分开。

### 9.3 显示和交互规则

- 每个来源定义固定字段顺序，不再使用 `Object.entries()` 原样铺开；
- source card summary 使用真实 button，并提供 `aria-expanded`；
- 允许同时展开多个来源，但每块始终显示 source label；
- 展开状态写入 anchor/query，返回页面时可恢复；
- 每个 source 独立 loading/error/empty，单一来源失败不影响其他来源；
- HPO 只在具体 disease 展开后请求；
- report、PMID、MONDO、OMIM 等可靠 ID 转为外部链接；
- `Disputed`、`Refuted` 使用 `#B42318`、冲突图标和明确文字；
- classification badge 的颜色只在同一来源内部解释；
- 严禁跨 ClinGen、GenCC、OMIM 生成投票条、一致性分数或总可信度。

### 9.4 Disease 验收标准

- 默认折叠状态可在一屏浏览全部来源；
- 每张卡都有来源语义、总数和有意义的预览；
- 展开后显示来源专属字段，而不是一个大型 nullable 表；
- GenCC submitter assertions 不合并；
- Disputed/Refuted 与弱支持状态明显不同；
- HPO observed、NOT 和 inheritance 完全分开；
- 键盘和触屏可完成展开、分页和关闭。

## 10. 前端组织方式

保留现有 Next.js + React + TypeScript 架构，不进行 Tailwind 迁移。先从真实重复需求中提取少量组件：

```text
frontend/
├── app/
│   ├── globals.css
│   └── styles/
│       ├── tokens.css
│       └── motion.css
├── components/
│   ├── ui/
│   │   ├── action-link.tsx
│   │   ├── button.tsx
│   │   ├── disclosure.tsx
│   │   ├── source-badge.tsx
│   │   └── tooltip.tsx
│   ├── sequence/
│   ├── expression/
│   └── disease/
└── lib/
    └── display-labels.ts
```

约束：

- 不构建通用插件系统或庞大的内部组件库；
- 只有按钮、链接、tooltip、source badge 和 disclosure 等真实重复元素才抽取；
- 首选现有 CSS 和浏览器能力；
- 仅为 sequence 引入所需 D3 modules，为 heatmap 引入 ECharts；
- 如果统一图标确实减少复杂度，可以评估 `lucide-react`；不能同时混用多套图标；
- 添加依赖前记录用途并检查包体积、维护状态和现有 Next.js 版本兼容性。

## 11. 分阶段实施顺序

### M6.1：视觉基础和术语转换

- 建立 colors、spacing、radius、shadow、motion tokens；
- 实现 Button、ActionLink、Disclosure、Tooltip 和 SourceBadge；
- 实现 `display-labels.ts`；
- 替换公开页面中的机器枚举和裸下划线；
- 增加 reduced-motion 规则；
- 不改变数据接口。

验收：全站基本交互风格一致，`start_lost` 等不再直接展示。

### M6.2：Overview、Identifiers 和 Disease

- 对 Identifiers 分组、去重和折叠；
- 添加复制和可靠外部链接；
- Disease 改为 source preview → source detail → HPO 的两级展开；
- 固定每个 disease source 的字段顺序。

验收：P00533 的 38 条 identifier 可以理解其层级；Disease 首屏不再被完整 assertion 淹没。

### M6.3：Expression 总览

- 一次加载或并行缓存四个 modality；
- 构建独立色标的二维总览；
- 增加 tissue display crosswalk 和原始术语 tooltip；
- 详情默认折叠并限制首批行数；
- 完成 NULL、0、IHC Not detected 和多 dataset 处理。

验收：四类数据可以同时总览，但不会被误解为同量纲。

### M6.4：Sequence explorer

- 先实现全蛋白 bounded overview API；
- 将 overview 改为共享坐标的 SVG/Canvas 多轨道；
- 增加 draggable brush、JSD 曲线、domain/topology、PTM 和 variant density；
- 再连接 detail residue、drawer、URL 和 variant table；
- 删除旧的截断式绘图路径，不保留双实现。

验收：P00533 等高密度蛋白和稀疏蛋白均不丢计数、不失去交互。

### M6.5：全站抛光与验收

- 统一 loading、empty、error、partial-data 和 no-match 状态；
- 核对桌面、平板和手机布局；
- 增加关键组件和键盘交互测试；
- 运行生产构建和现有后端测试；
- 对正常、稀疏、歧义和空结果路径进行人工回归。

## 12. 文件级任务清单

| 当前文件/区域 | 主要任务 | 是否预计改后端 |
|---|---|---|
| `frontend/app/globals.css` | 拆分 tokens/motion，统一交互状态 | 否 |
| `frontend/lib/display-labels.ts` | 新建字段和枚举展示字典 | 否 |
| `frontend/components/protein-overview.tsx` | identifiers 分组、去重、折叠 | 初版否 |
| `frontend/components/variant-table.tsx` | consequence 和字段 label 统一转换 | 否 |
| QTL/Interaction components | 删除裸下划线和不一致的 label 逻辑 | 否 |
| `frontend/components/disease-panel.tsx` | source preview、固定字段和两级 disclosure | 一般否 |
| `frontend/components/expression-panel.tsx` | 四行热图和折叠明细 | 初版否 |
| `frontend/components/sequence-explorer.tsx` | 拆分为多轨道组件并更换渲染方法 | 是，增加 bounded overview |
| `backend/app/m2.py` | sequence overview summary endpoint | 是 |
| `backend/tests/` | overview bounds、计数和坐标测试 | 是 |

## 13. 全阶段验收清单

### 视觉一致性

- 所有链接、按钮、tabs 和 disclosure 具有 hover、active、focus 状态；
- 颜色、圆角、阴影和间距来自 tokens，不继续增加散落硬编码；
- 只有可点击卡片才有 hover lift；
- 页面不依赖持续动画维持吸引力。

### 科学语义

- View 未被修改；
- canonical 1-based 坐标、来源、单位和原始 tissue 术语完整保留；
- 不合并 isoform 与 canonical 坐标；
- 不合并 expression 量纲；
- 不跨疾病来源投票；
- 不使用颜色暗示未由数据支持的临床结论。

### 可用性和无障碍

- 可控机器字段不以下划线形式展示；
- tooltip、tabs、drawer 和 disclosure 支持鼠标、键盘和触屏；
- 不只通过颜色传达信息；
- `prefers-reduced-motion` 生效；
- 在 `1440/1024/768/390 px` 宽度检查关键页面；
- 表格和图形都具有文字摘要或可访问替代内容。

### 性能和回归

- 高密度 sequence 不创建与 variant 总数相同数量的 DOM 节点；
- summary API 有明确 bins/page-size 上限；
- 首次打开蛋白页不加载完整 variant/QTL/interaction 明细；
- 使用 P00533、一个稀疏蛋白、一个歧义 ID 和一个空结果路径回归；
- 后端自动化测试和前端 production build 均通过；
- 删除被替换的旧 CSS 和旧渲染路径，不保留临时兼容层。

## 14. 本阶段明确不做

- 不修改或重新清洗 `View/`；
- 不新增 SHA、独立 QC 报告或来源评分；
- 不为美化而更换 Next.js/FastAPI/DuckDB/Parquet 架构；
- 不实现暗色模式，除非后续有明确用户需求；
- 不实现 3D structure、跨来源 disease score 或 variant clinical score；
- 不在同一阶段重写所有表格为一个通用表格系统；
- 不复制 CATVariant 品牌资产或直接照搬其完整页面。

## 15. 调研依据

- [CATVariant 官方网站](https://catvariant.com/)
- [CATVariant 2026 Nucleic Acids Research 论文](https://academic.oup.com/nar/article/54/W1/W226/8693974)
- [CATVariant 公开源代码（Zenodo，MIT License）](https://zenodo.org/records/19121409)
- 用户提供的 ATP7B 多轨道概念图：用于确定 Topology、Pfam、UniProt sites、JSD 与 variants 共用坐标轴的布局方向。

调研中关于技术栈、依赖和基础 design tokens 的描述来自公开源代码；关于“为何显得美观”和 MemVar 应如何转化的部分属于针对本项目的设计分析，而非 CATVariant 官方设计规范。
