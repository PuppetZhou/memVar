# Basic Info膜特征补充与证据分层

日期：2026-09-21；用户已授权直接调整现有页面。[当前方案](../../archive/00_initial_preview/plan/protein_overview.md#basic-info膜特征重排2026-09-21追加当前实现) · [问题与依据](../../archive/00_initial_preview/research/protein_overview/membrane_views.md#basic-info补充分析与处理2026-09-21)。

## 已交付

- 膜区域位于基础身份之后，独立全宽展示UniProt、HTP、DeepTMHMM2三张紧凑摘要卡（后续反馈已压缩）。默认HTP保留原TM数/reliability；signal、方法和约束概况移入展开Overview。
- 展开Overview内提供来源拓扑顺序示意，Signal/Outside/Membrane/Inside采用不同浅色与文字；显示原坐标、来源、长度，明确不是比例图。
- 来源证据默认折叠；详情按数据库、原记录/链、证据role、预测method筛选，单条再次展开并20条分页。TOPDOM模型侧别/支持值和TOPDB文献、PDB/链可查看。
- 增加`GET /api/proteins/{accession}/overview/membrane/topology`；原summary补`topology_records`。现有PostgreSQL只读查询，无表结构变更、重新入库或新的科学映射。
- 原OPM/MPLID/BioDolphin观测入口、UniProt详情、DeepTMHMM2详情及Sequence Browser链接保留。

## 验证

- `npm run build --prefix Web/frontend`通过TypeScript及Vite生产构建。
- `python -m unittest Web.tests.test_membrane_topology -v`：6项通过。覆盖HTP原父属性去重/来源分数、method过滤和分页、TOPDOM模型关联、TOPDB文献和PDB链解析、identity-only原记录保留且无canonical坐标、跨蛋白来源拒绝、XML缺失/无效及字面零。
- 当前数据只读抽查：EGFR/HTP显示1个TM、94.77原reliability、11种方法、9条约束；原4段坐标与来源一致。关联22个拓扑source对象保留，不只列已映射对象。
- 隔离Playwright会话`memvar-seq-refine`验收1440×1000桌面、390×844手机。EGFR摘要、TOPDB来源切换→对应详情、结构证据PMID 26586721及PDB 4uv7链接、HTP/Hmmtop的6条输出和TOPDOM约束展开通过。
- 手机主页面和弹窗均无页面横向溢出。KCNH2的6个HTP跨膜段、15个综合拓扑区段、PDBTM来源43个原记录选项和分页列表通过；长拓扑示意内部横向浏览。
- 本地8000服务已加载新增API及生产构建。QA截图位于`/tmp/memvar-sequence-refinement-qa/membrane-desktop.png`、`membrane-evidence.png`、`membrane-mobile.png`、`membrane-mobile-evidence.png`（临时验收素材）。

## 保留的边界

HTP可靠性为来源原分数，不是实验验证百分比。方法输出/约束区域/实验结构区域各有不同粒度，未生成跨库支持票数或最终共识。来源原序列拓扑示意不替换canonical序列轨道；未映射对象只显示来源坐标。结构证据可能被多条区域复用，区域数不代表实验或文献数。完整来源字段仍保存在原数据中，页面只解释当前已提供的结构化依据。

## 后续压缩与并排布局（2026-09-21，当前）

用户最新反馈保留膜特征横向宽度、缩短高度，完整细节展开后查看；Cellular location移动到Functional context右侧。

- 默认膜区域仅保留类别、序列、三张来源摘要和两个入口；拓扑图、完整HTP概况与来源集合放入详情Overview。来源摘要可直接打开各自详情。
- 取消Cellular location的`ov-wide`，桌面两块同排同宽，手机单列。
- 生产构建通过；1440×1000的EGFR膜面板实测约234px高（上一版截图约735px），缩短约68%。Function与Cell Location均宽685px、同一纵坐标，右侧空栏已填补。
- 实际点击“Explore membrane features & evidence”→Overview拓扑图→TOPDB→实验/结构证据，PMID 26586721仍可访问；详情完整性保留。
- 390×844下主页面/展开弹窗无横向溢出，DeepTMHMM2详情切换通过。仅调整前端布局和展示层级，无API/数据库变动，本轮不重复接口测试。
- 临时截图：`/tmp/memvar-sequence-refinement-qa/membrane-compact-desktop.png`、`membrane-compact-mobile.png`、`basic-paired-desktop.png`。
