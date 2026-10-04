# P00533 桌面批注：序列、定位与表达修订

2026-09-22。承接用户在 P00533 页面的五条浏览器批注；本次只修 Web 呈现与交互，不更改上游快照、来源范围、数值或膜/变异规则。

| 批注 | 本次修改 | 验收边界 |
| --- | --- | --- |
| 1、3 · Atlas Variant/JSD 配色 | Variant 保持 `0/1/2–4/5/6/7–8/9+` 档位，按用户上一版截图恢复蓝→靛→紫的高对比色；旧 Variant 精确色值未找到。JSD 复用旧 `sequence-v2.css` 的淡紫→深紫端点，Atlas、结构视图与图例一致，缺失仍为灰色。 | 映射位点、计数及 JSD 原值不变；真实桌面观感待验收。 |
| 2 · 细胞定位图 | 自绘区域新增鼠标悬停高亮、其他区域弱化、键盘焦点高亮与可选区域说明；原有点击查看来源标签、来源/对象筛选和无映射状态保持。 | 仅参考[UniProt 对 SwissBioPics 交互图的说明](https://www.uniprot.org/help/subcellular_location)，不复制其图形；真实 hover/focus 待验收。 |
| 4 · 表达测量入口 | “What was measured?” 卡片可点击切换实际可用集合；卡片列出数据源，选中后展示来源、测量、单位和记录数，并联动 Source/Measurement 选择器。 | 不将不同来源或测量直接合并。 |
| 5 · 表达数值图 | 原来每组一个细小色块且称“热图”的区域改成进入 Expression 即展开的横向条形比较。单值组显示原值和单位、点击可看详情；多值组使用已确认的同组中位数，点击组可展开全部原始值；分类值用分段条，缺失与零分开。非负 RNA 的条长用明确标注的 log1p，相对大小只在当前集合内比较。 | 不把 log1p 变换后的长度当原值，不做跨来源共用刻度或新科学聚合。 |

修改集中于 `frontend/src/components/sequence-model.ts`、`FullSequenceAtlas.tsx`、`StructureViewer.tsx`、`OverviewLocations.tsx`、`ContextDisplay.tsx`、`ContextPanels.tsx`、`ExpressionMatrix.tsx` 及相应 CSS。

定向验证：`npm exec tsc -- -b`及 Vite 生产构建通过（1,711 模块）；候选前端已发布到本地 `frontend/dist/`。8000 服务 `/api/health` 为只读 PostgreSQL `ok`，主页指向新 JS/CSS，入口 JS 返回 200。P00533 的 GTEx 中位 TPM 接口返回 68 个单值组、0 缺失，范围 0.05314–70.1852，供横条按 log1p 显示；本轮未重复全量数据或全站 smoke。

浏览器控制接口仍未给出可连接实例，故以上不记作真实桌面截图、悬停、点击、焦点或图表视觉验收通过。用户批注截图是问题证据，不是修改后验收证据。

## 2026-10-02：互作图标、保存范围、JSD 与逐条注释

按 CFTR／EGFR 页面四项浏览器批注更新前端。科学来源、注释范围、坐标、数值与后端数据保持原值；仅修呈现和命中交互。

| 批注 | 已发布行为 |
| --- | --- |
| 互作记录图标过多 | 去掉记录表参与者类别、物种、外链和 View evidence 的装饰图标；名称、类别、物种、UniProt/项目链接和证据入口保留。 |
| AlphaGenome 展示范围 | 当前裁剪来源默认/复位使用保存区间，即完整 Ensembl gene 加两侧各 10 kb 与所选原模型窗口的交集；不再对短基因默认仅加 8% 留白。页面明确轴范围与 MANE Select 转录本结构的区别，不拉伸 MANE 冒充完整 gene。 |
| JSD source support | 删除图中悬停提示的 Source support 行，保留 JSD 原分值、逐残基选择及缺失状态。 |
| domain 不能逐条查看 | Domain/region 与截图对应的 membrane 每条来源注释各有独立悬停、点击和键盘目标；重叠命中区域分行，真实残基范围、来源筛选与原始注释顺序保留。PTM 原有显示分箱和选择语义继续沿用。 |

修改为 `ContextPanels.tsx`、`ConservationPlot.tsx`、`AlphaGenomeExpression.tsx` 与 `CompactAnnotationTracks.tsx`。TypeScript/Vite 构建和 6 项已有坐标测试通过；00:36 更新静态文件，入口 `index-DfBbJfEF.js`，保留旧 hashed assets。8000 与 ngrok 持续运行。

验证状态：00:40 四项实际浏览器验收通过。CFTR 默认/复位/Full saved range 均为 `chr7:117,277,120–117,725,971`；短基因 SSR4/P51571 均为 `chrX:153,783,516–153,808,510`，包含两侧各 10 kb。互作记录表 SVG 数为 0，内外链接保留；EGFR JSD 图及 L606=0.467264 原值保留，Source support 文本为 0。不同 Pfam domain、UniProt region 及膜注释可独立悬停、点击/Enter 打开对应单条详情；来源选择仍为原 UniProt/Pfam。控制台 0 错误、0 警告。本轮未扩大为全站或数据扫描。[验收结果](../../../data/ui_axis_validation/annotation_gene_ui/summary.json)、[CFTR 截图](../../../data/ui_axis_validation/annotation_gene_ui/cftr_saved_range.png)、[注释交互截图](../../../data/ui_axis_validation/annotation_gene_ui/egfr_annotation.png)。


## 2026-10-04：预测器字体与 ThermoMPNN 接入

首次发布完成三项页面批注的前两项，以及第三项的原始记录查询；用户随后确认极值规则，结构着色也已交付，见下节。本节保留首次交付范围。

- Prediction toolkit 主标题 19px／650，分组标题 14px／600，AlphaMissense 卡片重点文字 15px；说明与计数维持次级层次。
- 新增 Protein stability 分组和 `ThermoMPNN_ddg` 选择项，可显示变异表列并进入 Predictions 详情。保留 Stability 专页；仅投影当前入库 `variant_ddg_detail` 中 ThermoMPNN 默认 checkpoint，按 variant／annotation／gene／accession 关联，不由 gene 推断位点。单值保持原值，多记录逐条展示，不求平均或最大值。零值、正负、缺失和多记录分别保留；单位和符号沿用已确认规则。
- 当前选择器 62 个字段、44 个工具标签；全库总览按当前服务字典投影这部分计数，原快照 Parquet 和统计 sidecar 不改写。覆盖仍按完整当前筛选计算，EGFR 有 2,773 个带 ThermoMPNN 的唯一变异；CFTR 为 3,827，低覆盖案例 A0A075B6H7 为 0。
- 新增 `/api/proteins/{accession}/structure/predictor-records` 只读分页查询：AlphaMissense、ESM1b、ThermoMPNN、AlphaGenome AVI raw／PHRED／merged splicing。每条保留原始变异、注释、替换和分数，仅使用已发布 current canonical ddG links，无逐残基汇总。当时结构上色的同残基多替换规则待确认，仅为接口准备；后续已获用户确认，以下节已交付状态为准。

验证：`MEMVAR_QUERY_BACKEND=duckdb python -m unittest Web.tests.test_stability_predictors Web.tests.test_predictor_selection -q` 共 7 项通过，包括与现用库原 Stability 数值一致、关联身份不串接、真零／缺失／多记录、选项与总览一致及结构原记录分页。EGFR／CFTR／低覆盖蛋白定向覆盖查询成功；TypeScript／Vite 候选构建通过。独立 Playwright 在 1414×827 下点击 Protein stability、勾选 ThermoMPNN、应用列、打开 R2Q 的 Predictions 并筛选该分组成功；实际显示 +0.0892 kcal/mol，与原始 0.08915859460830688 一致。主标题／分组 computed style 为 19px／14px。截图与发布信息在 `output/playwright/prediction-toolkit-20261004.png`、`thermompnn-detail-20261004.png`、`predictor-publication.json`。

候选初次启动误用历史 PostgreSQL 默认，AlphaGenome 裁剪元数据检查返回 503；候选已改为显式 DuckDB，正式发布使用 `start-local.sh` 与 `MEMVAR_QUERY_BACKEND=duckdb`，本地 AlphaGenome 查询成功。初次候选日志不作为正式服务错误。原 ngrok 地址保留，当前后端健康检查为 DuckDB／read_only。未做移动端或整站扩展验收。

发布后公网浏览器已复核新静态版本，显示 62 selectable fields／44 source tool labels，ThermoMPNN URL 选列生效；页面控制台 0 errors，浏览器警告另见本地日志。8001 候选服务已停止，8000／ngrok 继续运行。


## 2026-10-04：结构 Predictor 按模型极值上色

用户确认采用位点极值，完成之前暂缓的第 3 项。现行科学展示规则主要维护于 [variant 规则](../../../../modules/variant/docs/rules.md#结构预测器逐残基极值展示2026-10-04)，不再等待分数汇总确认；原始入库表与逐变异预测不改写。

- Structure coloring 新增 **Predictor**，可独立切换 AlphaMissense、ESM1b (ESM)、ThermoMPNN 和 AlphaGenome；选择 AlphaGenome 后显示 AVI raw／AVI PHRED／Merged splicing 选项。
- `/structure/predictor-extrema` 对本蛋白完整已映射项目变异集合计算逐残基极值，复用已确认 canonical links。保留原始 `/structure/predictor-records` 分页接口；新的汇总不从已分页列表取值，也不受变异表临时筛选影响。
- AlphaMissense／AlphaGenome 取最大；ESM1b 取最小；ThermoMPNN 取绝对值最大并保留符号。保留全部并列来源记录，正负等幅并列显式标识。零保留、非有限值不参与、无值不填零。
- 上色与原生量尺同步，未评分位置灰色；ThermoMPNN 以零为中心展示稳定化与去稳定化，AlphaMissense 固定 0–1，其余用本蛋白极值及零构成量尺。悬停残基显示极值、模型、覆盖数量、所有产生极值的具体替换和原始变异链接；保留原 ClinVar 证据区。

实现：`src/api/structure_predictors.py`；`StructurePredictor.tsx`、`structure-predictor.css`、`StructureViewer.tsx`、`StructureSiteInspector.tsx`。统一服务查询，不重新推理、重建数据或修改位点映射。ESM 采用现用数据的 ESM1b，未引入其他 ESM 版本。

验证：`MEMVAR_QUERY_BACKEND=duckdb python -m unittest Web.tests.test_structure_predictor_extrema Web.tests.test_stability_predictors -q` **8 项通过**；覆盖极值方向、并列来源、正负绝对值并列、真零／缺失／NaN／Infinity、注释重复、六字段全部 EGFR 位点与原始记录一致、无覆盖与非法输入。TypeScript／Vite 构建通过。独立 Playwright 1414×827 实测四模型切换及 AlphaGenome 三字段选择，三维渲染更新，L858 悬停随模型切换为：AlphaMissense 0.9968（L858R）、ESM1b −11.7751（L858R）、ThermoMPNN 0.0524 kcal/mol（L858M）、AVI raw 1.47（L858R）、AVI PHRED 28.4759（L858R）、Merged splicing 0.0553（L858R）。切换保持选中位点与原始变异身份；连续图例实测宽度 200px。

本机 EGFR 六种字段首次单次查询约 0.09–0.30 s，均有 1,120 个有分 canonical 位点；这是一次定向观测，不是并发性能保证。A0A075B6H7 无映射分数且无本地结构，保持原无结构提示。无分数据不显示虚构量尺。截图见 `output/playwright/structure-alphamissense-20261004.png`（早期图例样式）、`structure-thermompnn-extrema-20261004.png`（最终色条修订）。未扩展为手机端或整站验收。

发布：候选构建已同步到 8000，原 ngrok 地址保持；本地与公网健康检查均为 DuckDB／read_only，公网 ESM1b 极值接口复核 L858=−11.775072。公网真实页面已复核 Predictor → AlphaGenome → AVI PHRED，模型选择、子字段、色条和渲染更新正常。发布信息见 `output/playwright/structure-predictor-publication.json`；旧 hashed assets 保留，候选 8001 停止。
