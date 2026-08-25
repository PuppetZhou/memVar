# 10. COSMIC CGC 注释与 GEN 差异表达火山图计划

状态：已完成  
计划日期：2026-08-16  
适用阶段：M10 完成后的 M11 Variant/Expression 增强  
范围：只读取 `View/Variant/cosmic_branch.parquet`、`View/Basic_info/protein_basic.parquet` 与 `Mapping-data/GEN/results/by_dataset/`；所有派生数据、API、UI 和测试均写入 `website/`。

## 1. 用户目标

1. 在 COSMIC evidence 中加入 `CGC tier` 和 `CGC role (oncogene/TSG/fusion)`。
2. 从 GEN 每个 disease-vs-normal contrast 中，按 gene symbol 找出当前膜蛋白显著差异表达的数据集。
3. Expression 首先展示数据集背景：编号、组织、疾病、研究 metadata；默认不加载火山图。
4. 用户展开数据集并选择 contrast 后，加载该 contrast 的全体可绘制基因火山图；所有膜蛋白通过颜色、形状和描边突出，hover/tap 显示 gene symbol 与表达信息。

## 2. COSMIC 科学语义

- 源表约 2,400 万物理行、762.8 万 distinct variant keys；新增字段为 `CGC_TIER:int32` 与 `ONC_TSG:string`。
- `CGC_TIER` 值为 1/2/NULL；`ONC_TSG` 是逗号分隔的 `oncogene`、`TSG`、`fusion` 组合。
- 二者是 Cancer Gene Census 的 gene-level 注释，不代表该 variant 的 pathogenicity、clinical significance 或 functional impact。
- 禁止用 CGC tier/role 改变 ClinVar P/LP 红色、Variant 排序、Consequence 或 AlphaMissense/VEP 解释。
- 源表有约 1,638 万完全重复行。ETL 先按全部 6 个源字段 `SELECT DISTINCT`；13 个 variant key 的不同 sample-count facts 分别保留，不求和、不覆盖。
- API 将 role 拆分、trim、按 `oncogene → TSG → fusion` 规范排序并去重；NULL 不生成 chip。

## 3. GEN 数据与映射合同

- 目录含 151 个 dataset metadata；42 个数据集具有 142 个合格 DE contrast。
- 一个 dataset 可以包含多个 contrast，最多 25；不能混合不同 case/control 比较。UI 以 dataset 聚合背景，但火山图以 `contrast_id` 为唯一粒度。
- protein→contrast 发现使用 `protein_basic.gene_symbol` 与 DE `gene_symbol` 的 `trim + casefold exact` mapping；保留同一 symbol 对应多个 accession，禁止 first-match。
- 当前 protein 只在源字段 `is_significant_with_effect=true` 时进入 summary：该字段代表通过 expression filter、FDR<0.05 且 |log2FC|>=1。
- 不在浏览器重新计算显著性或 membrane mapping。全图膜蛋白标识直接使用 DE 成品 `is_membrane_mapped`；方向直接使用 `de_direction`。
- NULL log2FC/FDR 不是 0，不能绘制；detail 返回 tested/plotted/unplottable exact counts。
- x 为 disease/case vs normal/control 的 `log2FC`；y 为 `-log10(FDR)`。FDR=0 仅为绘图钳制到 1e-300，tooltip 保留原始 0。

## 4. M11.1：离线派生数据

新增独立 GEN DE 构建器：

- 校验 dataset、contrast、DE schema 与 dataset/contrast IDs 一致性；拒绝路径穿越、重复 contrast 或混合粒度。
- 生成小型 `memvar_de.duckdb`：dataset metadata、contrast metadata、protein→qualifying contrast、目标蛋白 DE 值及精确 totals。
- 生成每 contrast 独立 ZSTD Parquet，保留所有具有有限 log2FC/FDR 的点：gene_symbol、Ensembl ID、mean_expression、log2FC、FDR、source significance/direction flags、is_membrane_mapped。
- details 以生成 manifest 白名单定位；API 不扫描 `Mapping-data/GEN`，也不接受任意路径/glob。
- 输出只写 `website/data/generated/differential_expression/`，构建采用临时目录与原子发布。

## 5. M11.2：API

### Protein summary

`GET /api/v1/proteins/{acc}/differential-expression/summary`

- 返回 gene symbol、mapping semantics、dataset/contrast exact totals。
- dataset 只出现一次，含 dataset ID/name、project/BioProject、source page、strategy、tissues、disease conditions、sample metadata。
- contrasts 含 contrast ID、tissue、disease、case/control definitions 和 n、目标 gene 的 mean expression/log2FC/FDR/direction。
- 只返回当前 protein 的 source-defined `is_significant_with_effect=true` contrasts。

### Volcano detail

`GET /api/v1/differential-expression/contrasts/{contrast_id}/volcano`

- 只由 manifest 精确命中；返回 metadata、阈值说明、tested/plotted/unplottable counts。
- 使用 columnar/tuple point payload，维度固定为 log2FC、-log10FDR、gene symbol、Ensembl ID、mean expression、raw FDR、direction、source significance flags、membrane flag、current-target flag。
- 单次响应只包含一个 contrast，受源数据自然上界约束；不分页切断火山图。

## 6. M11.3：火山图 chart contract

- 分析问题：当前蛋白在哪些 disease-vs-normal contrast 中显著差异表达，以及它相对于全体基因和膜蛋白处于何处。
- 图形：ECharts Canvas scatter；每个 contrast 约 6 万 tested genes、约 1.68 万有坐标点，足以支持 scatter；若 plotted=0 则显示空态而不造图。
- 参考线：x=±1，y=-log10(0.05)；标题/副标题明确 contrast、组织、case/control、样本量和 plotted/tested denominator。
- 背景非膜基因：小型浅灰 circle、低透明度。
- 膜蛋白：较大 diamond + 深色描边；up 使用 `#f47254`，down 使用 `#7b95c6`，not-significant 使用中性 open fill。颜色之外必须保留 diamond/outline。
- 当前蛋白：更大 star + 深色粗描边并置顶，避免仅靠颜色识别。
- tooltip/readout：gene symbol、mean expression、log2FC、FDR、direction、membrane status、Ensembl ID；使用 richText，不把 gene 文本插入 HTML。
- `animation:false`、progressive rendering；不默认启用会削弱逐点交互的 large mode。

## 7. M11.4：Expression 交互

- 现有 HPA/PaxDB 模态保持不变；在 Expression 下新增 `Disease differential expression` 子板块。
- 页面初始只加载 summary metadata，不 import/初始化 ECharts、不下载 contrast points。
- dataset card 默认折叠，显示编号、tissue、disease、study name/project、strategy 和 qualifying contrast 数。
- 点击 dataset 后显示 contrast buttons；点击具体 contrast 才 fetch volcano 与动态 import ECharts。
- 同时只展示一个活动火山图；已加载 contrast 可缓存，accession 改变时 abort 并清空。
- hover 更新 readout，click/tap 固定 readout，Escape 取消固定或收起；原生 button 使用 aria-expanded/controls。
- 为 Canvas 提供可聚焦文字摘要和膜蛋白点的有界浏览列表，使键盘用户能读取等价信息。
- 明确 loading、retryable error、无 qualifying contrast、无可绘点状态。

## 8. M11.5：COSMIC UI

- Variant drawer 的每条 COSMIC fact 显示 Genome screen sample count、MONDO/disease categories、CGC tier 与 CGC role chips。
- 固定说明：`CGC tier and role describe the gene, not the pathogenicity of this variant.`
- API 使用显式 COSMIC evidence model，不依赖 generic raw-dict label fallback。
- P00533 重复 COSMIC facts 去除；真实 sample-count 差异 facts 保留为独立行。

## 9. 验收

- COSMIC：新 6 列 schema 被强校验；重复事实去除；P00533 的 CGC Tier 1/oncogene 正常显示；P43627 空态；CGC 不影响 P/LP 与 Variant 排序。
- GEN：151 dataset metadata、42 有 DE 数据集、142 contrasts 的构建守恒；gene-symbol 一对多 mapping 不丢 accession。
- P00533 正常 summary/volcano；另验证稀疏蛋白和无 qualifying contrast 蛋白。
- 每个 volcano 的 plotted+unplottable 与 tested 合同一致；NULL 不转 0；FDR 0 clamp 只影响 y 坐标。
- 页面初始不请求 volcano endpoint；点击 contrast 后只加载该 contrast。
- 所有膜蛋白为 diamond/outline，当前蛋白为 star；tooltip/tap/键盘 readout 字段完整。
- 后端全量测试、DE ETL 测试、前端 production build 通过；`View/` 与 `Mapping-data/` 未修改。

## 10. 明确不做

- 不把不同 contrast 合并成一个火山图，不计算跨研究 meta-analysis。
- 不用 CGC tier/role 推断 variant pathogenicity。
- 不重新运行 GEN 差异表达统计，不更改源阈值或方向结论。
- 不把 gene symbol fuzzy mapping 当生物学事实，不静默选择一对多中的第一个 protein。
- 不在请求时扫描 1.5 GB GEN 原始目录或 2,400 万行 COSMIC 源表。

## 11. 实施与验证记录（2026-08-16）

- COSMIC 已按完整 6 字段事实去重并重建；API/UI 显式展示 `CGC tier` 与规范化 `oncogene / TSG / fusion`，且固定说明这些字段是 gene-level CGC 注释，不代表 variant pathogenicity。
- GEN 已离线生成 151 个 dataset metadata、42 个具有 DE 数据的数据集、142 个独立 contrast；运行时不扫描源目录。
- protein summary 使用 gene symbol 的 trim+casefold exact mapping。P00533/EGFR 命中 6 个数据集、15 个唯一 contrast。
- 同 symbol 多 Ensembl 行不会合并方向或重复 contrast；P19440/GGT1 的冲突示例保留 2 条 target result。
- Expression 初始只加载 summary；展开 dataset 只显示 metadata，选择 contrast 后才按 manifest 加载该 contrast 的 volcano points 与 ECharts。
- 火山图使用背景基因 circle、膜蛋白 diamond、当前蛋白 star，并提供 hover/tap readout、键盘可访问的膜蛋白列表、空态、重试、缓存和请求清理。
- 验证通过：后端测试 74 项、ETL 测试 9 项、前端 production build。
