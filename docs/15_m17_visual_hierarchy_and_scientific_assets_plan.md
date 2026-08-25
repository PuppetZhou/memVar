# 15. M17 视觉层级、科研图标与高密度模块优化计划

状态：已实施并完成集成验收；BioRender 新素材因许可限制未获取，现有 Anatomy 图仅作为待授权核验的完整预览图使用  
计划日期：2026-08-23  
适用范围：M16 之后的前端视觉与交互优化；不改变 `View/`、科学事实、来源语义或现有数据粒度  
配套素材需求：[15_m17_biological_asset_prompts.md](15_m17_biological_asset_prompts.md)

> M18 覆盖说明（2026-08-24）：M17 的 Anatomy 坐标 marker 和 cartoon/ribbon Structure 决策已被项目负责人取消；M18 改为零 marker 的人体 orientation background 和非 ribbon 的 molecular surface/backbone 展示。M18 还通过 BioRender 插件新增了一张完整 memVar evidence overview figure，出处见 `15_m17_asset_provenance.md` 第 8 节，当前有效展示合同见 `16_m18_premium_visual_refinement_plan.md`。

## 1. 本轮结论

M17 实施前，网站已经具备较完整的数据层次和交互能力，但视觉质量仍停留在“功能完整的科研原型”。当时的主要问题不是缺少更多颜色，而是：

1. 字体、分隔线、色块和图标没有形成稳定的信息优先级；
2. 数据来源、当前蛋白、关键结论和解释边界经常与普通元数据使用近似视觉权重；
3. Disease differential expression、Variant 等高密度模块仍把过多字段横向并排；
4. Anatomy navigator 的点位坐标没有绑定真实底图变换，组织点与器官错位；
5. Covalent pair 虽保留了 `feature_type`，但 Sequence 图例和部分摘要仍只写“Covalent pair”，没有直接说明 bond 类型；
6. Structure 已使用 cartoon，但画面背景、光照、ribbon 参数、工具栏和图例仍缺少插画式层次；
7. 页面混用文本箭头、加减号、叉号和少量几何标记，缺少唯一的 icon system。

本轮目标是建立一条稳定的阅读顺序：

```text
当前蛋白 / 当前结论
  → 数据来源与 release
  → 关键定量字段
  → 研究上下文
  → 方法、限制与完整证据
```

## 2. 批判性分析

### 2.1 全局字体与颜色

当前 CSS 中仍有大量 `0.62–0.78rem`、`10–12px` 的公开文字。它们单独看似紧凑，但在 P00533 这种信息密集页面中会造成三个问题：

- 重要来源与单位因字号过小被误认为脚注；
- 用户需要频繁改变视觉焦点才能分辨字段名、字段值和解释文字；
- 多列布局为了容纳小字继续横向堆叠，反而降低扫描效率。

颜色问题主要是“权重不明确”，不是“颜色不足”：大量 muted grey 同时承担来源、单位、字段名、方法说明和空态，导致语义混在同一层。部分板块已经有 section accent，但 accent 多停留在标题边框，没有进入来源区、关键结果区和字段分组。

### 2.2 Disease differential expression

当前 DE 已正确突出当前蛋白并保留 tested/qualifying、FDR、log2FC 和多 Ensembl mapping 语义，但排版仍有明显摩擦：

- dataset trigger 同时塞入 identity、tissue/disease、contrast summary、current-protein statistics，四列在中等宽度下互相挤压；
- `Mean / log2FC / FDR` 以连续 inline text 展示，字段之间缺少结构化分隔；
- source、dataset metadata、研究设计和结果没有形成明确的上下层；
- 多个 13px 文本块并排后，字重差异不足，用户难以第一眼找到当前蛋白结果；
- contrast card 与 volcano readout 的字段视觉语法不一致。

需要把它重构为模块化的垂直信息栈，而不是继续缩字：

```text
Dataset header
├── Dataset ID + title
├── Source / release / study context
└── qualifying contrast count

Current protein result
├── direction badge
├── Mean expression
├── log2FC
└── FDR

Contrast context
├── disease
├── tissue
└── case vs control
```

### 2.3 数据来源与 provenance

来源是科研数据库的核心证据，不应只作为小 badge 或灰色尾注。当前 GO 已显示 provenance，但其他区域的 source/release/grain/caveat 仍缺少统一视觉语法。

建议建立一个深的 `Source context` Module：它的 Interface 只接收来源名称、release、record grain、caveat 和可选外链；Implementation 统一处理数据库图标、标题、强调色、缺失 release、长 caveat 和响应式布局。这样可以为 GO、Expression、DE、Disease、Variant source branches 和 AlphaGenome 提供 leverage，并把来源视觉规则集中到一个 locality。

### 2.4 Covalent pair

数据中 P00533 的 `feature_type` 明确为 `Disulfide bond`，但部分 Sequence 入口仍使用泛化标题 `Covalent pair`。用户可能无法判断这是二硫键、交联、硫醚键还是其他共价联系。

优化后每一对必须同时显示：

```text
Disulfide bond (S—S)
Cys 31 ↔ Cys 58
UniProt · canonical 1-based linked endpoints
evidence / description（若来源提供）
```

只依据来源 `feature_type` 命名，不从 residue 或描述猜测 bond。未知类型显示 `Covalent bond · type not specified by source`，不能默认写成 disulfide。

### 2.5 Anatomy navigator

本地 BioRender SVG 的实际 viewBox 是 `2752 × 1536` 横向画布，人体位于中央；前端把它映射到 `200 × 350` 并使用 `preserveAspectRatio="xMidYMid slice"`。当前点位表直接写成假定的 `200 × 350` 坐标，但没有将实际底图裁切矩阵作为可测试的转换。因此，只要底图留白、裁切或导出尺寸变化，所有点位就会整体漂移。

这是坐标模型问题，不是 CSS 微调问题。需要建立 `Anatomy geometry` Module：

- Interface：原图尺寸、可见人物 crop、标准组织 landmark、当前 viewBox；
- Implementation：原图像素 → 显示坐标转换、缩放/平移、marker screen-size compensation；
- 点位配置以原始图像像素或归一化 crop 坐标保存，不能再次手写“看起来差不多”的最终 SVG 坐标；
- 生成一张带编号点位的校准 overlay，逐个核对 organ landmark；
- 系统性 tissue 必须明确写为 representative site，不伪装成精确器官位置；
- `other` 继续不绘点。

### 2.6 Variant table

当前 Variant 主表中所有列基本使用同一白色背景和同一级边框，导致 identity、protein effect、来源、预测、频率和外部 ID 看起来是同一种信息。

建议按字段角色分组，不按“好/坏”着色：

| 字段组 | 列 | 建议视觉 |
|---|---|---|
| Identity | Variant、dbSNP | 冷灰/indigo 极浅背景，monospace ID |
| Protein context | Protein effect、Consequence | cyan/teal 极浅背景，强调 canonical/isoform |
| Evidence source | Sources | 独立 source chips，保留文字与 icon |
| Prediction | AlphaMissense、ΔΔG | amber/blue 分区；颜色只表达各自模型内部语义 |
| Population | gnomAD AF | violet 极浅背景，数字右对齐、tabular nums |

不同列的背景只能帮助扫描，不能暗示 pathogenicity、优先级或跨来源一致性。移动端应从宽表转为保留字段组标题的横向滚动或 row detail，不继续缩小字号。

### 2.7 Protein structure

当前 Structure 已经采用 3Dmol cartoon、variant-density / pLDDT 两种互斥配色和实际 AlphaFold PDB，因此科学数据基础正确。但视觉上仍存在：

- 白色 stage 与页面卡片边界不明显；
- ribbon 参数为 `tubes: false`、`thickness: .3`，与既有 M13 的“更厚、更圆润”合同不完全一致；
- caption、toolbar、color mode、legend 被拆成多个等权横条；
- viewer 缺少插画式背景渐变、柔和地面感和清楚的交互提示；
- 控件仍以纯文字为主，Reset、Spin、Fullscreen、Download 缺少统一 icon。

优化方向是“科学模型 + 插画式舞台”，不是用生成图片替换真实结构：

- 保留实际 PDB 与 residue coloring；
- 调整 cartoon ribbon、tube/arrow、outline、ambient occlusion 与初始 framing；
- 使用很浅的 blue-grey radial background 和内阴影形成画布；
- 工具栏合并为一个明确控制区，使用 Lucide icon + text；
- 当前颜色模式作为主状态，图例紧邻 viewer，不与下载元数据竞争；
- 不增加 molecular surface、ball-and-stick 或无依据的 membrane plane。

### 2.8 Icon 系统

通用界面图标统一使用 Lucide，不再混用字符图标。Lucide React 提供可定制、tree-shakable 的 inline SVG，并采用 ISC License。

首批通用 icon：

| 场景 | Lucide icon 候选 |
|---|---|
| Search / filter / reset | `Search`, `ListFilter`, `RotateCcw` |
| Expand / collapse / navigation | `ChevronRight`, `ChevronDown`, `ArrowRight` |
| Source / database | `Database`, `BookOpen`, `FileText` |
| External / copy / download | `ExternalLink`, `Copy`, `Check`, `Download` |
| Information / warning | `Info`, `CircleHelp`, `TriangleAlert` |
| Zoom / structure | `ZoomIn`, `ZoomOut`, `Maximize2`, `Rotate3D`, `Play`, `Pause` |
| Data modalities | `ChartSpline`, `Activity`, `Network`, `Layers3` |

实施阶段采用 `lucide-react` 命名 import，不采用动态字符串 icon loader，不混入第二套通用 icon 库。装饰 icon 使用 `aria-hidden="true"`；承担含义的 icon 必须有可见文字或 accessible name。

生物学专用 icon 不强行从通用 icon 库拼凑，统一按配套素材需求文档生成。

## 3. 目标视觉系统

### 3.1 字体层级

| 角色 | 桌面建议 | 约束 |
|---|---:|---|
| 页面标题 | 40–64px | 只用于蛋白 identity / 首页 |
| Section 标题 | 24–32px | 保持明显章节边界 |
| Card 标题 | 17–20px | 不使用 13px 冒充标题 |
| 关键结论/数值 | 16–20px | 使用 700–800 字重与 tabular nums |
| 正文 | 15–16px | 行高 1.5–1.65 |
| 字段值 | 14–16px | 不能比字段名更弱 |
| 字段名/来源元数据 | 13–14px | 来源名称不归为普通 caption |
| 最小辅助文字 | 13px | 只有坐标刻度可按图形需要更小 |

### 3.2 颜色角色

- 主文字：`#0F172A`；正文避免大面积浅灰；
- 次要正文：`#475569`；仅真正次级说明使用；
- 来源区：blue/indigo soft block，来源名称用 deep indigo；
- 关键结果：section accent soft block + 深色文字；
- 方法限制：amber soft block，不与 error 混用；
- 空态/缺失：neutral slate，不使用低对比度斜体作为唯一表达；
- Error/conflict：保留现有 crimson 语义；
- 科学数值色：继续由各数据 Module 自己定义，不被全局 section accent 覆盖。

### 3.3 排版规则

- 每个高密度 card 最多保留一个主要横向对比；其余字段改为 vertical stack 或 `dl` grid；
- 字段组之间使用 border、soft background、8–16px gap 建立模块边界；
- ID、HGVS、坐标使用 monospace；普通标题与来源名使用 sans-serif；
- 数字列右对齐并启用 `font-variant-numeric: tabular-nums`；
- source/release 不放在 hover-only tooltip；
- hover 只补充细节，关键字段必须持久可见。

## 4. 实施工作包

### M17-A：视觉基础与 Lucide

1. 安装并锁定 `lucide-react`；记录 ISC license 与用途；
2. 替换文本箭头、加减号、叉号、复制、外链、下载、筛选、重置、缩放和结构控制 glyph；
3. 扩展 typography、source、field-group、data-number tokens；
4. 建立 icon size/stroke 规则：16/18/20/24px，默认 stroke 1.8–2；
5. 禁止 dynamic icon import 与多 icon system。

### M17-B：来源与信息层级

1. 建立 `Source context` Module；
2. GO、Expression、DE、Disease、Variant branches、AlphaGenome 使用统一来源区；
3. 来源名称、release、grain 持久显示；caveat 可展开但入口明显；
4. 将公开正文最小字号提高到 13px；
5. 修订 muted color 和 section soft blocks。

### M17-C：Disease differential expression

1. dataset header 改为两层布局，避免四列压缩；
2. current protein statistics 使用独立 result panel；
3. Mean/log2FC/FDR 各自使用 field tile，并保持 NULL 语义；
4. contrast context 使用 disease/tissue/design 三行或两列 `dl`；
5. volcano readout 与 contrast card 复用相同字段顺序；
6. 768–1024px 使用单列/两列断点，不缩字；
7. source-defined qualifying、tested 与 missing 解释继续保留。

### M17-D：Covalent bond 语义

1. Sequence legend 显示来源 `feature_type`；
2. Disulfide 使用 `Disulfide bond (S—S)` 与专用生物学 icon；
3. pair label 显示 endpoint residue（可验证时）与 `start ↔ end`；
4. Selected Site drawer 把 bond type 放在 endpoints 上方；
5. 未知类型显式标注 source 未指定，不进行推断；
6. 保留同 pair 的确定性颜色、文字与形状冗余。

### M17-E：Anatomy geometry

1. 从本地 BioRender 原始像素建立 crop/transform；
2. 将 tissue landmarks 迁移到独立 typed 配置；
3. 添加 original-pixel → display-coordinate 纯函数；
4. 生成带编号 marker 的校准 overlay；
5. 逐项校准实际器官、代表性系统组织和左右侧位置；
6. 保持 zoom/pan/keyboard/URL/source-layer 行为；
7. 增加 landmark bounds、transform 和 representative-site tests。

### M17-F：Variant 字段分区

1. 按 identity / protein / source / prediction / population 建 column groups；
2. 使用极浅背景和顶部 group marker，不使用颜色表达临床结论；
3. 字段值提升到 14–16px，表头不低于 13px；
4. ID 与 numerical columns 使用各自排版；
5. 详情 branches 使用 source context；
6. 在窄屏保持字段组语义与可访问表头。

### M17-G：Structure illustration stage

1. 校准 3Dmol cartoon ribbon、tube、arrow、outline 与 AO；
2. viewer 使用浅色插画舞台和清楚边框；
3. 合并 toolbar 和 color mode 的视觉层级；
4. Reset/Spin/Fullscreen/Download 使用 Lucide icon + text；
5. 图例紧邻画布，来源/模型版本使用 source context；
6. 保留实际 PDB、variant-density/pLDDT 互斥语义和 WebGL empty/error states。

## 5. 代码组织建议

建议建立以下深 Module，而不是为每个小图标制造浅文件：

| Module | Interface | Implementation 内聚职责 | 判断 |
|---|---|---|---|
| Source context | source/release/grain/caveat/link | icon、视觉层级、缺失状态、响应式布局 | Strong |
| Anatomy geometry | source image/crop/landmark/view | 坐标转换、缩放、平移、marker compensation | Strong |
| Evidence field group | label/value/status/accent | `dl` 结构、数字排版、NULL/empty、移动端 | Worth exploring；至少两个真实调用后再冻结 |
| Structure presentation | model + color mode + controls | viewer styling、legend、control state、download | Strong |

不建议创建：

- 一个接收字符串并动态查找任意 Lucide icon 的 icon registry；
- 一个覆盖 Variant、DE、Disease 所有字段的万能 card；
- 一个把不同生物学来源压成统一 evidence score 的 Module；
- 为了模仿 catVariant 迁移到 Tailwind/Vite。

## 6. 分阶段执行与 subagent 边界

本轮实际使用 `gpt-5.6-terra` subagent 按以下文件边界实施；BioRender 素材因许可限制未下载，不依赖生物学素材的工作包继续完成：

| 波次 | 子任务 | 文件边界建议 |
|---|---|---|
| Wave 1-A | Anatomy geometry 与点位校准 | anatomy navigator、anatomy geometry、anatomy styles/tests |
| Wave 1-B | DE 信息模块化 | differential-expression、expression styles/tests |
| Wave 1-C | Structure illustration stage | structure panel/viewer、structure styles/tests |
| Wave 2-A | Variant column groups | variant table、variant styles/tests |
| Wave 2-B | Covalent type 与 site drawer | sequence/site evidence、sequence styles/tests |
| Wave 2-C | Lucide 与 Source context | UI primitives、tokens、指定调用点 |

总控负责：冻结 tokens、避免 CSS 冲突、审查科学语义、拒绝跨来源颜色误读、整合素材、浏览器复核、全栈测试和文档状态更新。

## 7. 验收标准

### 视觉与信息层级

- 公开正文和关键辅助文字不低于 13px；
- source 名称、release 和 record grain 在相关模块持久可见；
- DE 当前蛋白的 direction、Mean、log2FC、FDR 无需解析连续 inline text；
- Variant 五类字段组可在 3 秒内通过背景/分隔/标题识别；
- 页面只使用一套通用 icon system；
- 生物学 icon 风格、stroke 和配色一致。

### Anatomy

- marker 坐标从真实底图转换，不依赖未经说明的最终画布手写值；
- brain、thyroid、lung、heart、liver、stomach、kidney、colon、bladder 等直接器官点落在对应结构；
- representative site 在 tooltip/label 中说明；
- zoom 1×–4×、pan、Reset、Home、keyboard、URL selection 均保持；
- 替换底图时 transform tests 会失败并要求重新校准。

### Covalent

- 每条 pair 显示 source `feature_type`；
- P00533 明确显示 `Disulfide bond (S—S)`；
- 未指定类型不被猜成 disulfide；
- endpoints、颜色、文字和 evidence 保持一一对应。

### Structure

- 实际 AlphaFold PDB 仍是唯一结构主体；
- variant-density 与 pLDDT 继续互斥；
- cartoon 比当前更厚、更清楚，但不使用 surface/ball-and-stick 遮挡 residue coloring；
- WebGL unavailable、loading、error、download 和 fullscreen 仍可用。

### 工程与回归

- `npm run test:navigator`、`npx tsc --noEmit`、`npm run build` 通过；
- backend/ETL 若未改动仍执行现有完整测试；
- P00533 正常路径、稀疏蛋白、空态、390/768/1024/1440px 均复核；
- 不修改 `/home/xuyzh/memVar/View`；
- 不让生成素材冒充数据库证据或实际蛋白结构。

## 8. 正式公开发布前的剩余条件

代码实施和本地验收已经完成。正式公开发布前仍需要：

1. 明确 BioRender 现有底图是继续使用、由授权账户重新导出，还是替换为其他可公开发布素材；
2. 保存适用的 BioRender 许可或替代素材许可证，并按 [15_m17_asset_provenance.md](15_m17_asset_provenance.md) 关闭许可检查项；
3. 若替换 Anatomy 底图，必须重新校准 source-space landmarks 并重新运行坐标回归测试；
4. 对以后新增的生物学 SVG/PNG 确认公开发布许可、来源记录和无障碍说明；
5. 上线环境再次完成浏览器、WebGL、移动端和空态验收。

## 9. 参考

- [Lucide icon library](https://lucide.dev/icons/)
- [Lucide React official guide](https://lucide.dev/guide/react)
- [catVariant](https://catvariant.com/)
- [现有视觉优化合同](05_visual_design_and_display_optimization_plan.md)
- [Structure cartoon 合同](12_section_palette_and_cartoon_structure_plan.md)
- [M16 Anatomy 与 covalent 合同](14_m16_stability_covalent_and_anatomy_visual_mapping.md)

## 10. 实施记录

实施日期：2026-08-24

- M17-A/B/C：接入 `lucide-react`，建立统一 `SourceContext`，重排 Disease differential expression，并将 Expression 公开文字提高到可读层级；
- M17-D/F/G：明确 covalent `feature_type`，为 Variant 建立字段角色分组，优化真实 AlphaFold PDB 的 cartoon stage、图例和控制区；
- M17-E：建立 Anatomy source-space landmark、`xMidYMid slice` crop transform 与校准测试；`other` 不绘制，系统性组织明确标记 representative site；
- AlphaGenome：明确为 GRCh38 reference-sequence model prediction，按来源/位点、筛选、轨道、比较和图例组织，保留独立尺度与 shared-scale opt-in；
- 来源信息：GO、Expression、DE、Disease、Variant ClinVar 与 AlphaGenome 已接入持久来源上下文；异构 release/grain 不合并，缺失值显式显示；
- 全站字体：公开正文、字段、按钮和辅助信息最低 13px；仅图形坐标刻度和纯 hover tooltip 保留更小字号；
- 素材结论：未下载、拆分或再分发 BioRender 独立图标，许可结论与上线前条件见 [15_m17_asset_provenance.md](15_m17_asset_provenance.md)。

集成验收结果：前端 navigator 测试 40/40、TypeScript、Next.js production build、后端全量 pytest 91 项通过；P00533 页面、Anatomy、AlphaGenome、covalent、DE 与 AlphaFold PDB 接口已做实际请求核验。
