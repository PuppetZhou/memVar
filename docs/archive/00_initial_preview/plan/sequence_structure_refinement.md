# 序列与结构精修：2026-09-21

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

本次用户明确要求实现展示优化并纳入已发布预测interface数据。替代website_v2中双份完整Variant Distribution和默认PTM多来源密集轨道；科研原值、关联与其他模块不改变。

1. 最新04:28后反馈：Sequence恢复唯一的Variant density轨道，与其余七类注释共享坐标；Catalog继续后果/临床统计，不恢复重复位置图。当前完整界面方案见[website_v2](website_v2.md#3-序列与结构)。
2. PTM默认dbPTM紧凑位点轨道，密集位置按显示像素聚合，保留原类型色标及原位置选择；注释表移入View table按需打开。来源可独立筛选，其他来源不删除，PTMD2仍在Disease。
3. Secondary按最新可读性反馈改为单条较高的彩色原区间轨道；Domain默认UniProt+Pfam及已发布Region/Repeat/Motif，Function sites单独紧凑行。八类轨道在同一面板纵向对齐。
4. 统一1-based inclusive坐标，面板首尾共享坐标轴及位置导线；全长导航提供可见拖选框、左右手柄、键盘调整和双击复位；局部窗口显示真实残基字母，Start/End、Zoom/Pan及拖选均调整同一范围，不改变数据。
5. Structure增加pLDDT/domain/membrane/PTM/variant count/JSD/PeSTo/SPPIDER-seq lens。缺数据灰色；类别和连续分数有独立图例；选中位点高亮保留。PeSTo绑定结构分片及所选分数，SPPIDER明确伙伴、query角色，不生成统一interface标签。
6. 用户后续明确：预测interface不单独列主表。Sequence Browser增加单条原始分数折线轨道，共用范围与面板坐标；可选PeSTo分片/结合类型或SPPIDER伙伴/query角色。悬停、方向键读数，点击/Enter打开位点证据并联动结构；原始分数小表仅保留在按需打开的位点证据中。
7. 输入为modules/PPI/data/curated/20260921_interface_predictions_01。以Web/config/interface.yaml维护位置和版本，独立web_interface暂存schema导入后发布，不替换其他schema。PeSTo用real原分数；SPPIDER用real[]原向量，1-based SQL下标就是query残基位置。全部来源关系保留。
8. 完整序列相等才建立当前Web映射；outside/mismatch仍保存。无新预测、阈值、跨分片/伙伴汇总。仅做导入计数/向量shape/关系与代表位点往返核对。

依据：[正式interface契约](../../../../../modules/PPI/docs/interface_predictions.md)、[PeSTo](https://github.com/LBM-EPFL/PeSTo)、[SPPIDER-seq](https://huggingface.co/aporollo-lab/SPPIDER-seq)、[PDBe Molstar着色API](https://github.com/molstar/pdbe-molstar/wiki/3.-Helper-Methods)。本地安装版本接口支持visual.select按已验证残基上色以及clearSelection恢复原模型配色，选中高亮与背景lens要独立处理。

验收：P00533真实PTM表筛选、每轨坐标与范围同步、结构各lens/伙伴切换、保留pLDDT回切；另一蛋白和390px布局；数据库完整计数及代表Float32值保持。

当前状态：实现、12张来源逻辑表导入及代表性浏览器验证均完成。04:56追加的共享坐标面板与PTM表格按需入口也已完成；本次没有再次导入，追加验收见[网站迭代记录](../../../record/00_initial_preview/20260921_website_v2.md)。手机坐标轴按容器宽度绘制，残基字母按空间密度显示；不压扁字体。详细证据、实测范围和限制见[交付记录](../../../record/00_initial_preview/20260921_sequence_structure_refinement.md)。

## 结构风格追加（2026-09-21）

用户要求加入`/home/xuyzh/memVar/website`旧版展示方法。旧版`frontend/components/structure-viewer.tsx`实际使用Mol*、`coarse-surface` Gaussian表面、medium质量、`illumination.enabled=true`及pLDDT主题；当前PDBe Molstar同属Mol*，主要差异是representation和光照，而不是AlphaFold/PDB标签。

已增加独立Render style：Ribbon（当前默认）/ Smooth surface（legacy）。表面模式复用旧版preset和光照参数；带状模式用polymer-cartoon，关闭表面模式的增强光照。切换复用已加载结构、保持镜头及现行注释lens，在同一串行更新中重建representation并重涂当前注释/选中残基。结构来源、坐标、序列映射和八种数据着色均不改变。

## Full Sequence Atlas细化（2026-09-21 06:16后反馈）

Atlas独立显示完整canonical序列；PTM来源/类型过滤独立于上方compact track，默认全部已映射来源。残基采用等宽等高方格，按可用宽度调整每行数量，PTM点位于方格内；不以容器裁切减少可见位点。每种实际存在的PTM用独立类型色与图例，最多三个点加“+”表示更多类型，完整证据仍可打开。类型过滤淡化无匹配位点、不删除序列。

模式为Variants（数量/原ClinVar标签组）、Predictor coverage、PTM types、Secondary structure和JSD。Predictor coverage首期AlphaMissense/REVEL/SIFT，只按有finite原值的distinct DNA variant数上色，0为有效值，缺失/NaN/Infinity不计；不平均或取最大值生成位点效果。沿用已发布canonical ddG links关联，关联范围与Variant目录相同；有评分不代表致病性。多个ClinVar标签组以条纹示意，不合并为位点分类。

残基详情改为模式对应的标签页前置：PTM显示类型/来源/记录数/原证据对齐表，支持来源与类型筛选；Secondary优先结构注释；JSD显示原值/0–1表针和简要alignment context；Variant列出实际基因座替换/临床标签；Predictor前置各实际替换原评分并保留选择器。其它特征/结构观测通过标签页进入，Interface为按需展开补充，不再把全部原始字段与轨道摘要双份铺开。源记录仍经View source访问，无上游删减。

实现：`FullSequenceAtlas.tsx`、`ResidueEvidence.tsx`，`sequence_prediction_coverage.py`提供只读覆盖接口。科学关联/预测规则保持原样，不新增预测或致病判断。实际验证与边界见[Atlas交付](../../../record/00_initial_preview/20260921_atlas_refinement.md)。
