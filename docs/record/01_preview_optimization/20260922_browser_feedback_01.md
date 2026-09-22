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
