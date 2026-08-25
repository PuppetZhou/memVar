# 07. 单面板 Sequence、位点柱状 Variant 与注释交互计划

状态：已完成（M8.1–M8.5，2026-08-11）  
计划日期：2026-08-11  
适用阶段：M7 完成后的 M8 Sequence explorer 重构  
范围：只修改 `website/` 的 Sequence 展示、必要的 protein-scoped 只读摘要/缩略接口和测试；`View/` 继续只读。

## 1. 用户目标

1. Sequence 只保留一个 panel，默认显示 canonical 全长；用户可平移、缩放或输入 start/end 查看任意范围。
2. Variant 不再画连续波形：每个 canonical site 一根独立柱，柱高表示该位点 unique canonical drawable variants 数量。
3. 柱中红色部分表示具有明确 ClinVar Pathogenic/Likely pathogenic evidence 的 variant 占比。
4. Function、Topology、Pfam 和 PTM 按类别合理分色；Function/PTM 支持鼠标、键盘和触屏可见 tooltip。
5. 同一 panel 下方显示序列残基网格，背景色按该位点 variant 数量分档；点击位点显示最多 6 条蛋白变异缩略信息并可跳转完整 Variant 表。

## 2. 科学语义

### Variant anchor

- 只使用 `effect_scope='canonical' AND is_drawable` 的 effect。
- 每个 `variant_key` 在全蛋白取最小 `protein_start` 作为唯一 anchor。
- 每个 variant 只进入一个 site、一个柱子和一个缩略列表。

### P/LP 红色部分

- 唯一来源是 ClinVar branch 的 `ClinicalSignificance`。
- 使用仓内既有 strict allowlist：Pathogenic、Likely pathogenic、Pathogenic/Likely pathogenic、明确 low-penetrance 组合，以及这些分类后的 `; drug response` 等附加说明。
- Conflicting、Benign/Likely benign、VUS、NULL、not provided、VEP IMPACT、AlphaMissense、COSMIC 不得用于红色判定。
- 同一 variant 多个 RCV 只计一次；只要存在一条 strict P/LP 记录即标为 `has explicit ClinVar P/LP evidence`。
- 红色表示 evidence presence，不表示跨疾病、跨 RCV 共识或综合致病性。

## 3. M8.1：Overview API 扩展

扩展 `/api/v1/proteins/{acc}/sequence/overview`：

- `canonical_sequence`：完整 canonical sequence 字符串；长度必须等于 `canonical_length`。
- `variant_site_density`：
  - `start=1`、`end=canonical_length`；
  - `total_counts[int; canonical_length]`；
  - `clinvar_plp_counts[int; canonical_length]`；
  - 明确 anchor 与 P/LP semantics；
  - 不返回 variant fact rows、RCV rows 或 variant keys。
- `ptm_sites[]`：按 position 聚合，返回 `total_count` 与 `types[{ptm_type,count}]`；不丢原始类型。
- `ptm_type_counts[]`：完整蛋白的类型计数，用于跨 viewport 稳定配色和 legend。
- `covalent_pairs[]`：保留单 panel 中完整 endpoint pair 展示。

计数必须满足：

- `sum(total_counts) == canonical_drawable_variants`；
- 对每个位点 `0 <= clinvar_plp_counts[i] <= total_counts[i]`；
- `sum(clinvar_plp_counts)` 等于 unique anchored variants with strict ClinVar P/LP evidence；
- `sum(ptm_sites.total_count) == ptm_drawable_records`。

## 4. M8.2：Site variant preview API

新增 bounded endpoint：

`GET /api/v1/proteins/{acc}/variants/site-preview?position={1-based}&limit=6`

返回：

- site 的 exact total 与 strict ClinVar P/LP variant count；
- 最多 `limit<=12` 条 preview items；
- `variant_key`、HGVSp、raw consequence、source badges、`has_clinvar_plp_evidence`；
- `showing X of Y` 和跳转完整 Variant 表所需位置；
- 使用与 overview 完全相同的 global minimum anchor 语义。

缩略接口不返回 ClinVar assertion 明细；完整证据继续通过 Variant 展开层查看。

## 5. M8.3：单一 Sequence panel

- 删除 `sequence-overview-panel + sequence-detail-panel` 双卡结构和旧连续 `VariantDensityTrack`。
- 初始 viewport 为 `1–canonical_length`；URL pinned site/range 与 viewport 继续分离。
- 同一 panel 依次显示 axis、Topology、Pfam、Functional、JSD、PTM、per-site Variant bars、Covalent pairs、residue grid 和选中位点 preview。
- 全长/大范围使用 overview summary；viewport `<=500 aa` 时可请求 conservation detail，在原位置提升 JSD 精度，但不得生成第二个 panel。
- 支持：拖动/点击选择范围、start/end 精确输入、pan、`+/-` zoom、Full length、Home、Arrow、Enter、Escape 与触屏。
- 主绘图使用 Canvas/SVG path；不得为每条 variant 建 DOM。

## 6. M8.4：每 site Variant 柱与 residue grid

### Variant bars

- 一个位点一根独立柱，不连接相邻位点。
- 总高度对 raw total 使用单调 `log1p` 显示变换；tooltip 保留 raw total。
- 柱底为非 P/LP count，柱顶红色段高度严格按 `plp_count / total_count` 比例。
- 0 count 不画柱；点击或键盘选择最近有数据 site，加载 preview。
- Legend 明确写出 `All canonical variants` 与 `Has explicit ClinVar P/LP evidence`。

### Residue grid

- 使用 canonical sequence；按当前 viewport 排列，容器内部滚动，不扩散页面宽度。
- 颜色分档固定为 `0 / 1 / 2 / 3–5 / 6–9 / 10+ variants`，格内仍显示 residue 与 1-based position。
- P/LP 位点增加红色角标/边框，不能只靠背景色。
- Canvas 或有界渲染保持 Q8WXI7 长蛋白可用；容器支持 pointer hit-test、Arrow inspect 与 Enter select。
- 点击 site 显示最多 6 条 preview，包含 HGVSp、Consequence、sources、P/LP evidence 标记。

## 7. M8.5：动态分类配色和 tooltip

分类键：

- Topology：Topological domain 使用标准化 description；Transmembrane/Intramembrane 使用 feature type + 去编号 description；
- Functional：使用 `feature_type`，description 作为具体实例说明；
- Pfam：`pfam_type`，再回退 `pfam_id/accession`；
- PTM：使用 `ptm_type`。

配色规则：

- 从现有 11 色中，按完整蛋白类别集合确定性分配；同一类别在 pan/zoom/re-render 后颜色不变。
- 前 11 类颜色不重复；超过 11 类时颜色可复用，但必须增加实心/斜纹/轮廓模式。
- 每轨提供文字 legend；浅色背景使用深色文字。

Tooltip：

- Function/Topology/Pfam：类别、description、canonical coordinates、source；
- PTM：position、每种 `ptm_type × count`、source/evidence count；
- Variant：position、total、strict P/LP count 与非共识说明。
- hover/focus/touch/click 均可见；Escape/blur 可关闭；活动元素与 tooltip 使用 `aria-describedby` 关联。

## 8. 验收

- P00533：4381 canonical drawable variants、1190 occupied sites、87 strict P/LP variants；site 746 为 22 total / 4 P/LP，747 为 20 / 5，773 为 16 / 5。
- Q8WXI7：14507 aa，API 数组长度正确，响应不含 variant/ClinVar fact rows，前端无逐 variant DOM。
- P43627：全 0/空态正确。
- Function、Topology、Pfam、PTM 在 hover/focus/touch 下显示可见 tooltip；分类颜色在 viewport 改变后稳定。
- 默认只出现一个 Sequence panel，初始范围为全长；Full length、range、pan、zoom 和 pinned selection 工作正常。
- 后端完整测试与前端 production build 通过。

## 9. 明确不做

- 不把 AlphaMissense、VEP IMPACT 或 consequence 当作临床 P/LP。
- 不显示 CATVariant 的 consequence stack，除非未来有单独批准的数据合同。
- 不跨 ClinVar phenotype/RCV 计算共识。
- 不修改 `View/`、不重做 ETL、不添加临床综合评分。
- 不复制 CATVariant 品牌或完整布局。

## 10. 实施与验证记录

- Overview 与 site preview API 已完成，并共享同一 canonical minimum-anchor 与 strict ClinVar P/LP 语义。
- Sequence explorer 已合并为单一 panel；默认全长，并保留 range、pan、zoom、Full length、键盘与触屏操作。
- Variant 已改为逐 site 独立柱，红色柱段按 explicit ClinVar P/LP 比例绘制；Residue grid 已按数量分档并支持位点缩略预览。
- Topology、Pfam、Function 与 PTM 已使用完整蛋白类别集合进行稳定分色，并支持显式 tooltip。
- 后端全量测试：`51 passed`；前端 production build 与 TypeScript 检查通过。
- 自动验收覆盖 P00533、Q8WXI7、P43627、P/LP 分类陷阱、长蛋白响应上界及 preview 边界；最终像素观感与触屏手感保留给本地浏览器人工审阅。
