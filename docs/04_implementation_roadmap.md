# 04. 技术架构与实施路线

## 1. 推荐技术路线

初版本地栈：

- 数据构建：Python + DuckDB，直接只读扫描 Parquet；
- core store：DuckDB 文件，保存搜索、蛋白、annotation、expression、disease 与 summary；
- 大事实层：ZSTD Parquet，按 source/type/accession bucket 分区并在桶内排序；
- API：FastAPI + Pydantic，多个 read-only DuckDB connection；
- 前端：Next.js + TypeScript；
- 浏览器网络：只访问 Next.js 同源 `/api/v1`；Next.js 使用仅服务端可见的 upstream adapter 转发到 loopback FastAPI，浏览器不直接依赖后端 host、port 或 CORS 白名单；
- 表格：TanStack Table + virtualized rows；
- heatmap：Apache ECharts；
- sequence explorer：React + D3 scales/brush，SVG/Canvas hybrid。

选择这一组合的原因是它与现有 Parquet/Python 工作流一致，能够在本地完成 2 亿级事实层的离线预聚合，同时避免把所有 QTL 装入浏览器或一个超宽关系表。

生产部署时可以先保持同一只读 API；只有并发与数据量证明必要时，再把 core store 迁移到 PostgreSQL/全文检索服务。初版不提前引入双数据库同步。

## 2. 计划目录

```text
website/
├── docs/                         # 本轮交付
├── config/
│   ├── source_registry.yaml      # 来源显示名、单位、链接模板、解释边界
│   └── feature_track_map.yaml    # UniProt feature → UI track group
├── etl/
│   ├── build_core.py
│   ├── build_variant_index.py
│   ├── build_qtl_index.py
│   ├── build_interaction_index.py
│   └── sql/
├── data/
│   └── generated/                # 只放可重建产物，不写 View
├── backend/
│   ├── app/
│   └── tests/
└── frontend/
    ├── app/
    ├── components/
    └── tests/
```

构建脚本通过命令行接收 `--view-root` 与 `--output-root`，启动时拒绝 output 位于 View 内或与 View 相同。默认输出固定在 `website/data/generated/`。

## 3. 里程碑

### M0：契约冻结（本轮）

- 冻结 protein-centric scope、路由和层次；
- 冻结数据子集、映射优先级和来源解释边界；
- 冻结 API 与序列轨道概念；
- 明确不进入初版的 MaveDB 统一 score、AlphaGenome、结构三维和用户上传。

完成条件：本目录四份规划文档与 `AGENTS.md` 能够直接约束并拆分开发任务，且没有要求修改 View。

### M1：Core data mart + Search + Overview

1. 建 `protein_search_index`、`protein_overview`、identifier、sequence、GO/Reactome/location 表；
2. 建 FastAPI skeleton 与 search/protein/annotation endpoints；
3. 建首页、候选结果页、protein header/basic info；
4. 使用 `P00533/EGFR` 验证 accession、symbol、HGNC、ENSG、ENST/ENSP/isoform 多入口；
5. 对 ambiguous alias 返回候选列表。

完成条件：用户能从任一支持 ID 到达正确蛋白页面，并看到 Basic info。

### M2：Sequence explorer + Variant

1. 建 feature/PTM/Pfam/conservation 区段索引；
2. 建 `variant_core`、`variant_protein_effect`、ClinVar/COSMIC branches；
3. 解析 canonical HGVSp，生成可画 site/range；
4. 完成 sequence overview、brush、detail、track toggles 与 tooltips；
5. 完成 variant 主表、source branch、isoform expansion、filters/cursor pagination。

完成条件：canonical 序列、各类 site/interval 与 variant table 对同一位置使用一致的 1-based 坐标；无法可靠定位的 effect 只进表格、不画 marker。

### M3：Expression + QTL

1. 建四模态 expression API 与矩阵；
2. 建 GTEx/eQTLGen/QTLbase accession 映射和 summaries；
3. 输出按 accession bucket 分区的 QTL details；
4. 完成 QTL summary heatmap/table 与来源专属分页明细；
5. 界面中固定展示 unit、build、significant/association 语义。

完成条件：任何 protein 页面不扫描整张 QTLbase eQTL 表；点击摘要能在保留筛选条件的情况下打开明细。

### M4：Interaction + Disease

1. 建 BioGRID/IntAct protein membership、summary 与 detail；
2. 建 mutation effect sub-tab；
3. 建 ClinGen/GenCC/OMIM source cards；
4. 建 HPO disease→phenotype 展开与 MONDO 分类导航；
5. 完成来源说明页。

完成条件：interaction count 清楚区分 evidence/native ID；疾病 assertion 不被跨来源合并或投票。

### M5：整体验收与本地发布候选

1. 贯通空数据、超密集数据和一对多映射状态；
2. 检查移动端、键盘操作、色觉冗余与长文本；
3. 检查分页上限、超时、缓存和错误信息；
4. 固定数据来源说明、术语和页面文案；
5. 提供一键本地启动说明。

本阶段不生成 SHA/QC 报告；验收结果体现在测试和用户场景是否通过。

### M14：AlphaGenome predicted regulatory landscape（已批准）

以 `alphagenome.md` 为唯一详细契约，按 A→D 顺序执行：

1. 注册只读 AlphaGenome source root，建立全蛋白 coverage/tile/track catalog；
2. 先以代表性 tiles 验证 256/1024/4096-bin display pyramid 的压缩率与延迟；
3. protein 页面增加 summary-first AlphaGenome 板块，并通过同源 `/api/v1` 懒加载一维 tracks；
4. 在容量和响应上限通过后加入 junction top-K 与 `128 × 128` contact map；
5. 页面始终标记 reference-sequence model prediction，不把现有 archive 写成 REF/ALT variant effect。

完成条件：全蛋白 availability 可重复；普通页面请求不扫描原始 HDF5；单 track 不超过 4,096 bins；one-to-many Ensembl gene 映射可选择；无映射、未准备和无预测为空态明确；现有板块不受子图失败影响。

### M15：ThermoMPNN stability、Sequence navigator 与 anatomy navigator（已完成）

以 `13_thermompnn_stability_sequence_navigation_and_anatomy_plan.md` 为唯一详细合同：

1. 将只读 ThermoMPNN canonical single-substitution ΔΔG 构建为 website-owned source branch 与 site summary；
2. Variant 主表/详情增加窄 stability prediction，并保持与 AlphaMissense/ClinVar/COSMIC 语义独立；
3. Sequence 增加多尺度 ΔΔG distribution track；
4. 将 range selector 改为始终保留完整 canonical length 的双手柄 navigator；
5. 建立显式 anatomy crosswalk 和跨 Expression/GEN/QTL 的人体组织导航，不生成跨模态总分。

完成条件：7,376,098 条当前 release 预测按 `variant_key + accession` 无串联接入；同一 Ref→Alt 在 site 分布中只计一次；负/正方向和 `kcal/mol` 单位贯穿全栈；缩短 viewport 后可拖回全长；人体图只表达 availability/selection 或单一 modality，不合并不同来源量纲。

### M16：Stability、Covalent pair 与 BioRender anatomy 视觉优化（已完成）

以 `14_m16_stability_covalent_and_anatomy_visual_mapping.md` 为唯一详细合同：

1. 将 Variant ΔΔG 移到次级证据列；
2. 将 Sequence stability 改为红/灰/蓝连续波形并提供逐替换 site tooltip；
3. 让每个 covalent pair 使用独立、可追踪的端点与连接色；
4. 使用本地 BioRender 人体素材，并为 Expression、GEN、QTL 建立独立来源模式；
5. 将当前 release 的组织词汇全部纳入显式、标准命名的 crosswalk，保留 raw terms 且不使用 fuzzy mapping。

## 4. 第一条纵向实现切片

先完整实现一个有丰富证据的蛋白，而不是同时铺开所有空组件。推荐 `P00533 / EGFR`：

1. accession、EGFR symbol、HGNC:3236、ENSG00000146648 均能检索；
2. Header 与 Basic info；
3. canonical sequence + topology/domain/conservation/PTM/variant window；
4. 50 条 variant 分页及 ClinVar/COSMIC/isoform 展开；
5. expression 四模态；
6. QTL、interaction、disease summary 与少量明细。

完成这一切片后，再对全部 7,728 proteins 批量构建索引，可更早发现数据合同和交互问题。

## 5. 初版验收标准

### 数据边界

- View 下文件的修改时间和内容不因构建发生变化；
- 所有派生数据均位于 website；
- stable ID 一对多时完整返回候选；
- NULL 不被显示或统计为 0；
- canonical/isoform、GRCh37/GRCh38、significant/association、evidence/edge 的语义不混淆。

### 功能

- 支持已列出的 protein/gene/ID 搜索类型；
- Basic、Sequence、Variant、Expression、QTL、Interaction、Disease 七层均有真实数据状态、空状态与来源说明；
- sequence marker 可反向打开已筛选 variant/site 明细；
- variant source branch 与 isoform expansion 独立工作；
- QTL/interaction summary cell 可带条件打开详情页；
- 所有大表均为服务端分页。

### 可用性

- 用户无需知道 View 文件名即可理解每个字段；
- 任意 badge、颜色和 count 都有文字语义；
- tooltip 在 mouse、keyboard 与 touch 下可访问；
- 长蛋白和高密度 variant 不导致页面冻结；
- 外部链接只在 stable ID 足够明确时生成。

## 6. 风险与应对

| 风险 | 后果 | 设计应对 |
|---|---|---|
| `represent_variant` 只选一个蛋白 | 蛋白页漏变异 | 以 `isoform_view` 建完整 `variant_protein_effect` membership |
| HGVSp 无显式 position 列 | site marker 错位 | 分类型解析；canonical 范围/ref AA 通过才绘制 |
| 2 亿 QTL runtime join | 超时、内存峰值 | 离线映射、预聚合、按 accession bucket 分区 |
| 同位点 annotation 过多 | 序列不可读 | overview density、detail 聚合、track toggle、Canvas |
| 表达量纲不同 | 错误跨来源比较 | 分 tab/独立 legend，raw value + unit tooltip |
| interaction membership 被当 PPI | 计数误读 | 同时显示 evidence records 与 distinct native IDs |
| disease classification 被投票 | 过度临床解释 | 来源独立 cards，保留 submitter/panel/date |
| UI 擅自生成 priority score | 被误解为临床分类 | 初版只呈现 View 内原始指标和来源结论，不计算综合分 |
| gene alias 一对多 | 错蛋白跳转 | 候选页，永不 silent first-match |
| 来源字段缺失/版本不在表内 | 无法完整追溯 | `source_registry` 只记录现有 manifest 中明确的信息，不猜测 |

## 7. 开发顺序的导师建议

优先级应是：正确映射与蛋白页面集合 → 序列坐标 → 变异来源分支 → 大表性能 → 视觉润色。若先做完整 UI 再处理 effect membership 和 QTL 分桶，后续会迫使页面与 API 同时返工。

下一次实施任务建议严格限定为 M1，不同时启动全量 sequence/QTL 开发。M1 完成后先审阅真实 protein page，再冻结 sequence explorer 的最终视觉细节。
