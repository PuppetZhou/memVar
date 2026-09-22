# Variant Browser 与证据面板交付

2026-09-21，香港时间约 05:05 核对。用户明确授权直接完成本轮显示优化；[现行方案](../../archive/00_initial_preview/plan/variant_evidence_refinement.md)维护行为，[调研](../../archive/00_initial_preview/research/website_v2/analysis.md#variant-evidence-20260921)维护 CATVariant 实际观察和官方来源依据。

## 已交付

- 主表首列仅基因组位置与核苷酸替换，GRCh38 只在列头出现；随后为 Position、Ref、Alt。完整 ID/HGVS 在详情可查。
- ClinVar 三类 assertion 独立展示原 classification 与 review 星级，origin 为独立标签。条件名称与各数据库 ID 分组、默认少量展开；RCV 与不同 assertion 的 SCV 分开，原始字段保留。
- Population 的 AF 百分比使用连续色阶、群体对比条和 AC/AN；零/缺失分开。
- Prediction 新增来源 call 分布和方法组覆盖总览，字段搜索、组/call 筛选、缺失开关与九卡分页；默认先看 AlphaMissense/SIFT/REVEL/CADD，颜色与原分数方向/原 source call 一致，每卡可展开 provenance。
- Stability 保留原 signed ΔΔG，按已确认模型 convention 显示方向箭头、颜色与零中心条。Transcript 改为核心变化卡片，次要字段折叠，HGVS 转义正确解码。

修改位置：`frontend/src/components/VariantCatalog.tsx`、`VariantEvidencePanels.tsx`、`variant-evidence-model.ts`、`variant-evidence.css`。本轮没有修改 API、PostgreSQL、Parquet 或科学产物。共享目录的并行 Sequence/Basic info 修改保留。

## 验证结果

`npm run build --prefix Web/frontend`：TypeScript 与 Vite 均通过。复用当前本地 8000 服务读取真实 PostgreSQL；使用与主线程隔离的 Playwright 会话，不操作其浏览器。桌面 1440×1000，窄屏 390×844。

| 检查 | 实际结果 |
| --- | --- |
| 首列及排序 | L858R 第一格为 `7:55191822` 与 `T → G`；表头顺序 Genomic variant、Position、Ref、Alt；第一格不重复 GRCh38、variant ID、HGVSc |
| ClinVar 原 review | L858R Variation 16609：germline 3 星、oncogenicity 1 星、somatic impact 2 星，原 review status 独立可见 |
| 条件/ID 展开 | L858R conditions 从默认三项展开至九项；MedGen 从五项展开至九项；MONDO URL 去掉重复命名空间；RCV/SCV 链接目标不同且按其来源分组 |
| Prediction 覆盖 | 61 个原字段中 55 个分数、6 个缺失；17 个原 damaging/pathogenic call，38 个无已解释 call。没有生成综合致病分 |
| 筛选与分页 | 搜索 SIFT 返回 SIFT/SIFT4G，原分数 0/0.001 与低分方向正确；Sequence models 筛到六卡；No score 筛到六项；清除后可翻到第 2/7 页；不存在的搜索显示明确空状态 |
| 原评分上下文 | AlphaMissense 卡展开可见 dbNSFP、transcript consequence、ENST00000275493.7、matched source category 与官方字段链接；分数显示字号 25px，原类别为粉红 |
| Population 非零 | R521K overall AF 0.271633 → 27.1633%，AC/AN 397092/1461872；九个 ancestry groups 有 AF，最大 EAS 57.665%；grpmax 保留来源选择组，不算额外群体 |
| Population 零与缺失 | `GRCh38:7:55019281:C:A` 原 AF=0，overall+九群体有灰色零标记，grpmax 缺失显示 No AF；L858R 缺 AF 显示 —、无条且最大值为 not available |
| Stability 双方向 | L858R -0.033615… kcal/mol → 绿色稳定化；R521K +0.2168（显示精度）→ 粉红去稳定化。原 convention 明示；条轴为局部尺度 |
| Transcript | L858R 的 p.Leu858Arg / c.2573T>G / exon 21/28 默认可见；次要元数据展开有效。同义变异 `p.Arg2%3D` 正确显示 `p.Arg2=` |
| 窄屏 | 上述同义变异与 L858R 的 ClinVar/Population/Predictions/Transcripts/Stability 五面板均 clientWidth=scrollWidth=356；页面宽度/滚动宽度均 390，无页面水平溢出；原主表保持内部横向滚动 |
| 控制台 | 本轮末次页面检查 Errors=0、Warnings=0 |

## 截图与边界

独立浏览器截图保存在 `/tmp/memvar-sequence-refinement-qa/`，为本地验收证据，不作为科学数据版本：

- `catvariant-catalog-reference.png`：实际参考页表格。
- `variant-browser-desktop.png`：新版主表。
- `variant-clinvar-desktop.png`、`variant-clinvar-mobile.png`：分类、星级及 ID 分组。
- `variant-predictions-desktop.png`、`variant-predictions-mobile.png`：预测总览及卡片。
- `variant-population-desktop.png`、`variant-stability-desktop.png`：群体频率、ΔΔG 方向。

本轮是前端定向验收，不代表全数据库逐记录复核或并发容量测试。外部链接核对了组成和目标，没有逐个访问全部 SCV/RCV。截图存于临时目录，长期留存以本记录中的样例和实际结果为准；代码仍从现有 API 返回的原来源字段渲染。


## 统一预测列与逐工具指南（追加）

2026-09-21侧会话追加交付：Variant主表统一预测列、8项预览/展开、无12项人为上限；Prediction Toolkit支持批量选择和61字段的用途、方向、量尺、判断依据。原分值与source call不变，判定解释不生成新类别。来源与实现维护在[现行方案](../../archive/00_initial_preview/plan/variant_evidence_refinement.md#统一预测列与prediction-toolkit2026-09-21追加)。

验证：

- `npm run build --prefix Web/frontend`通过，TypeScript与Vite共1,689模块。
- `python -m unittest Web.tests.test_predictor_selection -v`三项通过：全部字段与四字段选择的原分值/分类/匹配状态逐项一致；顺序、分页无重复；重复去重/清空/未知字段拒绝；游标不能跨选择复用。
- 指南与当前发布字典集合完全一致，61/61；每项含名称、用途、量尺、方向、解释和来源链接。
- 重载本地API后，真实P00533查询20行×61字段返回200，约0.108秒（单次本机观察，不是容量基准）。未修改PostgreSQL表、权限或正式科学产物。
- 本侧会话浏览器运行时列表为空；本次新增网格/选择弹窗/移动样式的真实渲染、键盘及点击验收待补。上文05:05的浏览器验收属于原版本，不代表本次新增交互已实测。


## 恢复独立预测列与Catalog分布图（后续追加）

2026-09-21：根据05:47/05:48截图反馈替代统一大列，恢复predictor各自纵列；保留全部字段选择与工具指南。缩减身份/单字母列的留白，将剩余宽度分配给评分列，取消每分数的卡片边框。新增Catalog上方分布图，直接复用Sequence已有组件与summary数据；点击bin筛选、选区高亮、清除范围均接URL筛选状态。

调研：重新访问[CATVariant KCNH2](https://catvariant.com/genes/KCNH2#variants-table)。网页提取可核实目录包含变异、预测及来源证据；具体表格视觉依据用户提供的05:48截图：紧凑评分、轻隔行背景、深色标题、类别着色。本站遵从用户最新决定采用独立纵列，没有沿用截图的综合agreement/prioritization结论。前轮统一网格是已替代方案。

核对与边界：

- TypeScript + Vite构建通过，1,690模块。
- P00533全部来源：1,120个有映射位点、2,773个mapped variants；ClinVar：977个位点、1,947个mapped variants。逐位点六类clinical_counts总和与variant_count相等。
- 分别请求601–625和626–650区间，各返回15条注释；每行至少一个已验证canonical位置位于选区内。仅查询既有只读API，未重算数据或改变分类。
- 无选区时图与摘要复用同一查询缓存；有选区时图保留相同其它筛选下的全序列概览，列表继续按选区查询。未定位数据不画入图。
- 本侧会话浏览器选择返回`No browser is available`，实例列表`[]`。未进行新界面的真实点击/滚动、移动端或截图验收；以上构建与接口核对不等于视觉验收。未调用其他浏览器绕过连接限制。
