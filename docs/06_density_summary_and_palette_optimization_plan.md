# 06. 密度图、统计总览与统一色系优化计划

状态：已完成（M7.1–M7.5）  
计划日期：2026-08-11  
适用阶段：M6 完成后的 M7 展示优化  
范围：只修改 `website/` 的展示层、必要的只读摘要/选项接口及其测试；`View/` 保持只读，既有来源语义、坐标语义和分页边界不变。

实施验收（2026-08-11）：M7.1–M7.5 已完成；后端测试 47/47 通过，前端 production build 通过。P00533 的 Variant options、三窗口 density 守恒、GTEx 三类型矩阵与 BioGRID/IntAct context 聚合已验证；P43627 GTEx 空态已验证。浏览器像素级和真实触屏手势仍由人工本地审阅确认。

## 1. 目标

本阶段针对 M6 人工审阅中暴露的高密度可视化、筛选方式和视觉一致性问题完成以下改进：

1. Sequence 不再用密集红色圆点展示 variant，而使用按 canonical site/bin 聚合的连续 density 波形；
2. JSD 使用固定 `0–1` 量纲的连续保守性曲线和 min–max 区间带，不再画成柱状；
3. Variant 的 Consequence 与 Source 改为数据驱动的受控选项；
4. GTEx 先展示组织 × apaQTL/eQTL/sQTL 热图，再进入来源明细；
5. BioGRID 与 IntAct 先展示每个 curation context 的 evidence-record 柱状统计，再展开分类明细；
6. Reactome 只显示通路名称，不在页面正文显示 `R-HSA-*` 编号；
7. 全站彩色强调和数据图形统一到用户指定的 11 色色板，并修正数据库专名大小写。

## 2. 不变的科学和数据约束

- Sequence 继续使用 UniProt canonical、1-based closed 坐标；isoform effect 不投影到 canonical 轨道。
- JSD 曲线表示保守性分数，不称为频率；缺失值不当作 0，也不跨缺失区间连线。
- Variant density 高度只表示 unique canonical drawable `variant_key` 的数量，不表示致病性、consequence 或临床优先级。
- 不根据现有字段伪造 CATVariant 的 consequence 堆叠；只有接口真实提供的计数才可展示。
- GTEx 仍标注为 official significant pairs；三类 QTL 的 count 只作记录数量比较，不合并效应值。
- BioGRID/IntAct 柱状图统计 evidence records，不解释为唯一 PPI edge、partner 数或组织/疾病活性。
- `distinct_native_interaction_count` 不跨 category 求和；仅在展开的原始分类行中展示。
- Reactome ID 继续保留在 API、React key 和稳定外链中，只从可见正文隐藏。
- `View/` 不写入、不清洗、不更改。

## 3. 统一色板

彩色 UI 和数据标记只从以下色板取值：

| Token | 色值 | 主要用途 |
|---|---|---|
| `data-1` | `#7b95c6` | JSD 主线、主品牌蓝 |
| `data-2` | `#49c2d9` | QTL 强调 |
| `data-3` | `#a1d8e8` | JSD 区间带、浅蓝背景 |
| `data-4` | `#67a583` | BioGRID/正向类别 |
| `data-5` | `#a2c986` | 辅助绿色 |
| `data-6` | `#d0e2c0` | 浅绿背景 |
| `data-7` | `#fded95` | 低值/提示背景 |
| `data-8` | `#ffc1a6` | Variant density 填充 |
| `data-9` | `#f59c7c` | PTM/中值强调 |
| `data-10` | `#f47254` | selection/高值强调 |
| `data-11` | `#c85e62` | Variant 主线、conflict/negative |

中性色继续用于正文、边框、白色 surface 和可读性。上述 11 色不直接承载白色小字号正文；彩色背景使用深色文字。正文链接、focus ring 和状态色使用由色板与中性色混合得到的高对比语义 token。

## 4. M7.1：Sequence density 与连续曲线

### 全蛋白 overview

- 继续请求 bounded `/sequence/overview?bins=400`；最长返回不超过既有上限。
- JSD lane 使用固定 `0–1` y-domain：bin 中心连接 `jsd_mean`，`jsd_min/jsd_max` 构成半透明 ribbon；缺失 bin 断线。
- Variant lane 将 `variant_count` 经过单调 `log1p` 映射为连续 area/line 波形；0 位于基线，raw count 在 tooltip/可访问摘要中保留。
- PTM 可继续使用独立 site/density 编码，不与 variant wave 混合。
- brush、viewport、pinned site/range 和 URL 语义保持分离。

### Detail window

- 移除 variant 红色圆点/聚类轨，按 residue 聚合 unique canonical drawable `variant_key` 后绘制连续 density area。
- 后端 detail variant 行与 overview 统一为“一条 variant 只锚定一次”的语义，避免 transcript duplicate 放大密度。
- 透明命中区支持 pointer、touch、Arrow 键和 Enter pin；不能为每条 variant 创建 DOM 节点。
- JSD detail 同样使用固定 `0–1` 折线，不随当前窗口自动拉伸。

### 验收

- 每个 JSD bin 满足 `min <= mean <= max`；缺失与 0 可区分。
- overview 各 bin variant count 之和等于 `canonical_drawable_variants`。
- detail 每个 site 只计 unique `variant_key`，窗口内计数守恒。
- P00533 与 Q8WXI7 高密度路径不出现 variant 红点墙，且响应/DOM 仍有界。

## 5. M7.2：Variant 受控筛选与专名

- 新增 `GET /api/v1/proteins/{acc}/variants/options?scope=canonical|isoform|all`。
- 响应返回该蛋白 bucket 内完整的 `consequences[]` 和 `sources[]`，以及明确的 complete/bounds 说明。
- 复合 Consequence 原始值按逗号拆为单一 SO term 作为选项；列表过滤从整串 equality 改为成员包含。原始 Consequence 字段继续原样返回。
- 前端 Consequence、Source 使用 `<select>`，包含 All 选项、loading/error/empty/disabled 状态；不得从当前 50 条页面推导选项。
- 建立集中 source/product 显示字典：`dbSNP`、`AlphaMissense`、`ClinVar`、`COSMIC`、`gnomAD`、`BioGRID`、`IntAct` 保留官方大小写。
- 删除会把表头专名全部转换为 uppercase 的 CSS。

## 6. M7.3：GTEx 三类型组织热图

- GTEx 默认视图固定为 tissue rows × `apaQTL / eQTL / sQTL` columns。
- 使用现有完整 `/qtl/summary`，无需新增 QTL 后端接口。
- cell fill 使用 `log10(record_count + 1)`；格内或 tooltip 显示 raw record count 与 distinct variant/locus count。
- 非零 cell 链接到现有 source/type/tissue 过滤后的详情页；缺失组合显示 `0 / No records` 且不可点击。
- 使用 Apache ECharts 渲染视觉热图，并提供语义 `<table>` 作为屏幕阅读器与无脚本替代；客户端动态加载、dispose、resize。
- eQTLGen 与 QTLbase 保持现有各自语义，不强行套用 GTEx 三列矩阵。

## 7. M7.4：Interaction 柱状总览与 Reactome

- BioGRID/IntAct summary 按 exact `(context_class, context)` 分组，将互斥 category 的 `evidence_record_count` 求和。
- 先按总数降序展示横向柱状图，每条显示 context、context class 和精确 evidence count。
- BioGRID 可分段显示 physical/genetic；IntAct 可分段显示 positive/negative，但文本必须同步给出分类计数。
- 图下使用默认关闭的 disclosure，展开后保留每个原始 category 的 evidence count、distinct native ID 与过滤链接。
- 整体 context 链接只传 source/context，不传 category；分类明细链接继续传 category。
- Reactome 页面正文只显示 pathway name；稳定 ID 继续用于链接、数据和内部 key。

## 8. M7.5：全局色系整合与验收

- 在 `tokens.css` 登记 11 色及语义映射，清理组件中的旧彩色 hex；Canvas 从同一 palette 常量或计算样式读取颜色。
- 统一按钮、tabs、热图、柱状图、Sequence、Expression、Disease 与状态提示的彩色强调。
- 所有图形都同时提供文字、数值、形状或图案，不只依赖颜色。
- 保留 `prefers-reduced-motion`、focus-visible、键盘和触屏操作。
- 检查 1440/1024/768/390 px 响应式布局，不允许页面级横向溢出；图表局部滚动必须有清楚标签。
- 回归 P00533、Q8WXI7、P43627、Q08379、Q12836、SHORT 和 A0A0G2JS06。
- 运行完整后端测试和前端 production build；删除被替换的红点轨与旧彩色规则。

## 9. 文件级任务

| 区域 | 主要改动 |
|---|---|
| `backend/app/m2.py`, `models.py` | Variant options；detail density 去重/锚点语义 |
| `backend/tests/` | options、成员过滤、detail/overview 计数守恒 |
| `frontend/components/sequence-explorer.tsx` | JSD/ribbon 与 Variant density wave |
| `frontend/components/variant-table.tsx` | Consequence/Source select |
| `frontend/components/qtl-summary.tsx` | GTEx tissue × 3 QTL heatmap |
| `frontend/components/interaction-summary.tsx` | context evidence-record 柱状图 + disclosure |
| `frontend/components/protein-overview.tsx` | 隐藏 Reactome 可见编号 |
| `frontend/lib/display-labels.ts` | 官方数据库/产品大小写 |
| `frontend/app/styles/tokens.css`, `globals.css`, module CSS | 统一色板、响应式和 focus |
| `frontend/package.json` | 增加 ECharts（不增加 React wrapper） |

## 10. 明确不做

- 不复制 CATVariant 品牌、源码或像素级布局；只采用 density-first 的信息层级。
- 不展示当前数据无法支持的 consequence-stacked sequence density。
- 不新增综合致病性、QTL、PPI 或疾病评分。
- 不合并不同 QTL 量纲、interaction grain 或 disease assertion。
- 不修改 `View/`、不重做 ETL、不发布外部托管版本；本轮保持本地运行。
