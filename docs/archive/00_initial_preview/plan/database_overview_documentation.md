# 数据总览与网站说明

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

确认依据：2026-09-21用户明确要求参考CATVariant Results/Documentation，按本次已确认数据版本制作简化页面；本方案记录授权下的实际实现基线。当前交付与验证见[记录](../../../record/00_initial_preview/20260921_database_overview.md)，[研究与问题](../research/database_overview/analysis.md)保存比较依据及待决项。

## 页面与导航

- `/results`：Data overview。统计摘要卡、独立覆盖率圆环、来源组成环图、纵向比较柱图和分类卡片。按下表选择图形，每图保留计数单位；长列表分类或搜索，不再统一用横条堆叠。膜类型链接现有蛋白检索。
- `/documentation`：简洁介绍、纳入范围、操作指南、证据解读、可搜索/按类型筛选的来源目录、确认版本、真实只读API入口。`/about`保留为说明页兼容入口。
- 首页和蛋白页页头/页脚均提供Data overview与Documentation。白色面板、浅灰分隔、深色正文，类别色用于图标、数字和图条。

## 数据与科学边界

- 蛋白总数按UniProt accession；全部sequence数量另计。膜标签可以重叠，不用饼图暗示互斥。
- UniProt reviewed human Membrane keyword与已确认HGNC关系定义项目集合；TOPDB、HTP、DeepTMHMM2等是注释来源，不宣称它们的并集决定纳入。
- 基因座唯一variant与所选transcript consequence分别统计；来源成员与后果术语可以重叠，不求和充当唯一变异。
- 工具/模型配置数、可选评分字段数分别展示。仅字典存在不等于每变异都有数值，不由工具多数票生成临床结论。
- 疾病来源证据、来源疾病ID、关联蛋白和phenotype分别计数；PTMD关联独立，不混入基因疾病证据总数。
- 网站服务快照单列；上游版本只展示真实已确认release，不用处理日期推断版本。未知字段省略。
- 表达/QTL/PPI说明原数据粒度与筛选范围，不把观测行数称作组织数或独立发现。

## 维护入口

`Web/src/database/build_catalog_statistics.py`根据匹配当前PostgreSQL manifest的导入报告及小型维表生成`Web/data/catalog_statistics.json`。`GET /api/catalog/statistics`提供结果，版本不匹配时返回不可用，不显示过期统计。无需浏览器实时扫描变异/QTL大表。

`Web/config/catalog_sources.json`集中维护来源名称、类型和官方链接；`frontend/src/data/documentation.ts`维护介绍与使用说明。统计数值和已确认版本仅由统计生成器维护。前端`DatabasePages.tsx`与`database-pages.css`负责页面，`DataOverviewCharts.tsx`与`data-overview-charts.css`负责总览专用图表，常规蛋白证据页面保持原职责。

数据更新后先执行导入和既有验证，再运行统计生成器；前端修改后重新build。新版本只有在相关manifest和报告一致时才生成统计。


## 多样化统计展示（2026-09-21追加，当前方案）

用户要求替代逐条横向柱图。此次仅调整展示，既有API、统计JSON、manifest及科学处理不变。

| 板块 | 当前展示 | 分母/分类边界 |
| --- | --- | --- |
| 膜蛋白类型 | 四个独立覆盖率圆环＋分类入口 | 每环分母均为7,715个蛋白，不把可重叠标签相加；类型合计7,753说明其非互斥 |
| 膜注释来源 | Reference、Predicted topology、HTP、Topology & structure、Membrane associations五组来源卡 | 12个来源原计数逐项保留，不合计覆盖蛋白；只是目录呈现分组 |
| 变异来源 | 四色纵向柱图，同一零基线和线性量尺 | 来源成员重叠，不显示构成百分比 |
| Consequence | 替换、start/stop、剪接、其余coding四类可展开组 | 原术语和计数完整保留；不重算后果或把组内总数解释为唯一变异 |
| 预测器 | 评分字段类别环图＋关联层次环图；工具分单字段/多字段标签库 | 两环各自分母61字段；43个工具标签可搜索，工具数不视为独立证据 |
| 疾病 | 四来源记录组成环图 | 25,442条来源证据记录，不是独立疾病关系或结论 |
| QTL | 三来源关联记录组成环图 | 251,055,619行来源关联，不是唯一变异或独立发现 |
| Expression | 四类场景选择卡，点击显示具名数据集、测量类型及原观测行数 | 4/3/2/4个集合，共13个；DVP为MS，FANTOM为CAGE；GTEx median vectors不在此行数比较内 |

环图悬停/键盘聚焦图例高亮并显示原数字和占比；点击可固定，再次点击取消。图例为按钮，可Tab/Enter操作。颜色识别类别，轻底色组织区域；数量仍可通过原数值读取。组成占比不解释为质量、置信度或临床强度。

计数细节进入Counting notes；各板块How these numbers are counted保留。PPI当前发布统计仅提供存储记录总数，保持摘要，不凭空补出来源组成。未知新来源保留Other展示，不静默丢弃。浏览器验收状态见交付记录追加，旧截图不能证明本次图表已验收。
