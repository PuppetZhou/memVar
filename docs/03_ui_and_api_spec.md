# 03. 页面、交互与 API 初版规格

## 1. 视觉与交互总则

- 视觉基调：科研、克制、高信息密度，但不模拟电子病历或临床判读工具。
- 来源区分同时使用文字、badge、边框/图标与颜色，不能只靠颜色。
- 主色用于导航和选区；ClinVar、COSMIC、gnomAD、UniProt、dbPTM 等来源色仅在证据标识中使用。
- 数字表格默认右对齐；P value/AF 使用科学计数；tooltip 始终显示原值与单位。
- 每一层先显示摘要，再由用户主动展开原始/精简记录。

## 2. 首页与搜索结果

### 首页

- 页面第一视觉焦点是搜索框；placeholder 给出 `EGFR, P00533, HGNC:3236, ENSG00000146648` 等不同类型例子。
- 搜索建议按 match type 分组，并高亮匹配字段。
- 提供 3–5 个覆盖丰富的 example proteins；第一开发样例建议使用 `P00533 / EGFR`。

### 候选结果

卡片字段：gene symbol、protein name、accession、entry name、membrane class、length、匹配原因。歧义提示写清输入命中了 synonym、gene stable ID 或 transcript，而非含糊地写“multiple results”。

### 无结果

返回可接受 ID 类型，不做编辑距离自动跳转。可以给 prefix 候选，但不把近似 gene name 自动建立事实映射。

## 3. 蛋白页 Header

```text
EGFR  Epidermal growth factor receptor                      P00533
Integral membrane · 1,210 aa · Protein-level evidence · Annotation 5/5
[Overview] [Sequence] [Variants] [Expression] [QTL] [Interactions] [Diseases]
```

右侧显示外部 UniProt link；下方 coverage chips 只表达本站记录量，如 `Variants 12,345`，不表达证据强度。

## 4. Basic info 组件

采用两列 description table：左侧字段名，右侧为 tags/短文本。GO 与 Reactome 默认各显示有限条目：

- GO 先按 namespace 分组；NOT annotation 不进入正向摘要；
- Reactome 默认显示叶级或最具体路径，父路径通过 tree drawer 查看；
- subcellular location 同时显示 location、topology 和 orientation；
- 每组有 `View evidence`，而不是把 evidence code/JSON 堆在首页。

### 4.1 GO evidence drill-down

Gene Ontology 不以等权 label pile 呈现。页面先显示 MF / BP / CC 三个可选择的导航计数，以及术语/GO ID 和 evidence-code 筛选；计数是 annotation record 或 distinct term 的数量，不表示生物学强度、富集或跨来源结论。

- 默认排除 `NOT` / negated annotations，并在界面与响应 filters 中明确说明；用户可显式包含它们。
- term summary 从 source registry 返回 GOA 的 source、release、record grain 与 caveat；界面在标题附近展示这些 provenance，而非复制或硬编码来源 YAML。
- 每个 term 显示 GO ID、名称、aspect、annotation count、distinct reference count 和 evidence-code 摘要，并安全外链到 QuickGO。
- 展开单个 term 后才请求逐条 annotation evidence；显示 qualifier、evidence code、reference、assigned by、date、with/from 与 extension。仅识别 `PMID:<digits>` 的 reference 创建 PubMed 外链。
- term 列表与 evidence rows 都采用有限 page size 和 opaque cursor；不得把单蛋白的全部 annotation rows 直接加载到浏览器。

## 5. Sequence explorer

### 5.1 总体布局

```text
track controls   [Topology] [Domains] [UniProt sites] [PTM] [Variants] [Conservation]

Overview       1 ─────────────────────────────── 1210
Topology         [Extracellular] [TM] [Cytoplasmic]
Domains          [Receptor L] [Furin-like] ... [Protein kinase]
Density          PTM ▂▃▁...      Variant ▃▇▅...
Brush                         [=======]

Detail       680  V P E R T R ...                                   739
Conservation     residue-cell background intensity
Above sequence   UniProt functional sites / dbPTM pins
Below sequence   variant lollipops or clustered count markers
```

### 5.2 轨道语义

| 轨道 | 视觉编码 | 交互 |
|---|---|---|
| Conservation | residue 背景连续色；low-confidence 用 hatch/降低饱和度 | hover 显示 JSD、entropy、WT freq、occupancy、confidence |
| Topology | 连续区间块；inside/outside/TM 用文字和纹理 | 点击区间显示 UniProt feature 描述 |
| Pfam/domain | 独立 lane 的区间块 | 点击打开 Pfam/feature detail |
| UniProt point feature | shape 表示 active/binding/metal/other | hover/click detail |
| dbPTM/UniProt PTM | shape 表示来源，颜色表示 PTM family | 同位点聚合，点击列出 type/PMID/evidence |
| Variant | overview 用 density；detail 用 marker/cluster | 点击带 site filter 打开 variant drawer/table |
| Disulfide | 两端节点和连线 | 不渲染为连续 feature 区间 |

### 5.3 防止信息过载

- 默认窗口约 60–120 aa；overview 始终保留。
- detail 支持按 50 aa wrapped sequence 阅读，并允许在紧凑区段视图与 wrapped view 间切换。
- variant marker 超过阈值时按 residue 聚合显示 count，不为每条 variant 建 DOM 元素。
- 标签只在 hover、focus 或选中时显示；区段名可在空间足够时直标。
- 用户可按 source、consequence、ClinVar significance、PTM type 过滤。
- sequence marker、variant table row 与 site detail 使用同一个 selection state；任一处选中后，其余组件同步定位/高亮。
- 序列内搜索支持单 residue、range、protein variant code 和短 sequence fragment。
- click residue 固定 site drawer，依次显示 conservation、overlapping features、按来源分组的 PTM、canonical variant count，以及 `Filter variant table to this site`。
- 当前 site/range 写入 URL，例如 `?site=640` 或 `?range=620-680`；track/filter 控件提供可见的 Reset。
- Canvas 渲染高密度点；SVG/HTML 渲染坐标轴、区间和可访问控件。
- 键盘可移动 residue focus；tooltip 可由 focus 触发。

## 6. Variant table

### 6.1 默认列

```text
Variant (GRCh38) | Protein effect | Consequence | Source badges |
ClinVar summary | AlphaMissense | gnomAD AF | dbSNP | Actions
```

默认只显示与当前蛋白有关的 variants，canonical effect 优先；可切换 `Canonical`、`Isoform-only` 和 `All protein effects`。

### 6.2 行展开

展开层级：

1. variant-level：REF/ALT、class、impact、joint/exome/genome AF、AC/AN；
2. protein effects：canonical 在前，isoform rows 其后；显示 transcript IDs；
3. ClinVar：每个 RCV/phenotype 一行，显示 significance、review、origin、MONDO/category；
4. COSMIC：sample count 与 disease category；
5. source IDs 和外部链接。

多来源只在主行显示多个 badges；来源独有字段永远放在各自 child section，不创建混合的 `disease label` 列。

初版整行点击即打开详情，不提供复选框。这样避免“点击查看证据”和“勾选做批量操作”产生两种相互竞争的行状态。

### 6.3 筛选与分页

- filters：canonical/isoform-only、consequence、source、ClinVar significance/review、AF range、AlphaMissense class、site range；
- filters 旁显示实时 evidence counts，并固定显示 `Showing X of Y`，避免默认筛选改变分母而用户不知情；
- server-side cursor pagination；默认 page size 50，上限 200；
- 默认排序：canonical first → protein position → genomic position；
- 下载不进入初版，避免无界导出大表。

## 7. Expression matrix

界面保持一致，但四个 modality 不共享色标：

- HPA RNA：连续 nTPM；允许 raw/log10(1+x) 显示切换，tooltip 始终给 raw nTPM。
- HPA MS：连续 intensity；缺失为空心/斜纹格。
- HPA IHC：categorical palette；行可展开到 cell type，tooltip 显示 reliability。
- PaxDB：ppm；一个 organ 对应一个 dataset，tooltip 同时显示 dataset name/ID。

若需要跨来源总览，只用 presence/relative percentile 作为另一个明确命名的视图，不能把标准化颜色解释为绝对量可比。

## 8. QTL

### 摘要

- 第一层 tabs：GTEx、eQTLGen、QTLbase；
- 第二层：QTL type；
- 表/heatmap：row 为 type/source，column 为 tissue/context，cell 为 record count；
- count 范围过大时色标用 `log10(count + 1)`，tooltip 给原始 count；
- eQTLGen 显示 `blood meta-analysis / GRCh37`，不伪造 tissue matrix。

### 明细

公共列固定在左侧，source-specific 列在右侧。点击 summary cell 自动带入 source/type/tissue filters。variant/locus 的 build 与标识始终同列显示。

## 9. Interaction

### 摘要

表格列：source、context class、context、interaction category、evidence records、distinct native IDs、open details。

BioGRID 的 physical/genetic 分开；IntAct 的 negative 标识不隐藏。不能把 evidence rows 直接标为 proteins interacted。

### 明细页

主表显示 partner、species/type、method、interaction type、publication、confidence/score、context。展开显示 raw endpoint IDs、expansion method、feature/qualification。IntAct mutation effects 使用独立 sub-tab。

## 10. Disease evidence

采用来源 cards + source-specific table：

- ClinGen validity：disease、MOI、classification、expert panel、date、report；
- ClinGen dosage：HI、TS、date、report；
- GenCC：disease、classification、MOI、submitter、date、PMID/report；
- OMIM：disease、inheritance、mapping key、relationship status、cytogenetic location；
- HPO：从 disease row 展开 observed 与 explicitly absent phenotype；inheritance aspect 不混入普通 phenotype。

classification badge 颜色只在同一来源内部表达语义。跨来源并排时必须保留 source label，禁止按 badge 颜色“多数表决”。

在 gene–disease validity 中，`Disputed`、`Refuted` 使用独立冲突样式，不能渲染成“较弱的支持”；GenCC 同一疾病的多个 submitter assertion 可分组，但每个 assertion 仍独立显示。

## 11. API 草案

所有 API 只读，版本前缀 `/api/v1`。

| Endpoint | 用途 | 关键参数/规则 |
|---|---|---|
| `GET /search` | 全局蛋白检索 | `q, limit`；返回 match type 与 ambiguity |
| `GET /proteins/{acc}` | header/basic overview | accession 必须 canonical；不存在返回 404 |
| `GET /proteins/{acc}/annotations` | GO/Reactome/location | `section, cursor` |
| `GET /proteins/{acc}/go/terms` | GO term summary | `aspect=MF|BP|CC, q, evidence_code, include_negated, limit<=50, cursor`；默认排除 negated，返回 exact term/annotation counts、带 distinct reference count 的 aspect facets 和 registry-derived GOA provenance |
| `GET /proteins/{acc}/go/terms/{go_id}/evidence` | 一个 GO term 的逐条 annotation evidence | `evidence_code, include_negated, limit<=50, cursor`；term summary 的 evidence-code filter 必须继续约束展开后的逐条记录与 exact count；返回 qualifier、evidence/reference、assigned_by、with/from、extension、date |
| `GET /proteins/{acc}/sequence` | canonical sequence + interval overview | `start, end, tracks`；限制区段长度 |
| `GET /proteins/{acc}/sites` | PTM/feature/variant/conservation detail | `start, end, tracks, filters` |
| `GET /proteins/{acc}/variants` | protein-scoped variant rows | filters + opaque cursor |
| `GET /variants/{variant_key}` | 展开 branches/effects | URL encode key；source children 分组 |
| `GET /proteins/{acc}/expression` | 四模态表达 | `modality` |
| `GET /proteins/{acc}/qtl/summary` | QTL counts | source/type filters |
| `GET /proteins/{acc}/qtl` | QTL details | source-specific filters + cursor |
| `GET /proteins/{acc}/interactions/summary` | context counts | source/category |
| `GET /proteins/{acc}/interactions` | evidence details | source/context + cursor |
| `GET /proteins/{acc}/diseases` | source-specific assertions | `source` optional |

### 响应合同

- 所有列表返回 `items, next_cursor, total_or_estimate, applied_filters`；
- `total_or_estimate` 明确区分 exact/estimated；初版摘要表使用预计算 exact count；
- NULL 保持 JSON null，不转换为 0、`NA` 或空字符串；
- value 与 unit/source/build 一起返回；
- source-specific 数据放在命名对象中，不拼接成不透明文本；
- 外部链接只根据稳定、已知类型的 ID 生成。

## 12. 性能与可访问性目标

- 本地 warm query：overview/search 目标 <300 ms；大表分页目标 <1 s；
- 首屏不加载 variant/QTL/interaction 明细，只加载 summary；
- sequence detail 仅请求可视区段；
- 表格虚拟化但保留可访问的行/列标题；
- 色板满足对比度，所有颜色编码均有 shape/text 冗余；
- hover 功能同时支持 focus/click，移动端可用点击固定 tooltip。
