# 数据总览与Documentation交付

2026-09-21，本地交付。当前方案见[plan](../../archive/00_initial_preview/plan/database_overview_documentation.md)；[研究与问题清单](../../archive/00_initial_preview/research/database_overview/analysis.md)维护CATVariant参考、额外发现和待确认公共发布事项。

## 可用页面

- `/results`：Data overview，5类概要卡、分类横条图、真实膜类型检索入口、计数口径展开。
- `/documentation`：介绍与操作、范围和证据解读、42项来源目录（默认12项，搜索/类型筛选/展开）、5个服务模块当前快照、仅确认的上游版本、4个真实API示例。
- `/about`兼容说明页；页头和页脚新增两个入口，保持现有首页素材和蛋白页面功能。

已核对当前统计：7,715个蛋白accession、16,655个sequence；10,866,094个唯一GRCh38变异，10,881,400条所选transcript注释；43个字典工具/模型配置标签，61个评分字段；25,442条基因疾病来源证据，98,944条phenotype注释。上述单位分别维护，不合并成一个总数据量。

膜标签可重叠；膜来源覆盖保留关联层次；PPI含互作与mutation-feature的存储记录，不等于独立实验数。Expression的小型gene维度核对确认全部在项目HGNC范围，观测行数量不是组织数；QTL按来源关联行统计。PTMD2有来源说明和疾病入口，本轮未另扫全表统计，不计入基因疾病证据总数。分来源数值、版本与口径唯一维护于[统计JSON](../../../data/catalog_statistics.json)。

## 生成与服务

运行`python -m Web.src.database.build_catalog_statistics`，匹配5个当前PG manifest与导入报告，读取小型维表生成统计，约0.5秒；未扫描大型Variant/QTL/Expression事实表。`GET /api/catalog/statistics`检查当前版本，版本失配503，防止过期统计静默展示。网站文字和来源目录可在统计API不可用时继续阅读，数量/版本则显示错误状态。

来源名称/类型/URL集中于`Web/config/catalog_sources.json`，前后端共用；未知来源版本省略。日期式处理run未当作来源release。`config/inputs.yaml`的frequency阶段从过时“未投影”修正为已导入`web_variant`，未修改数据或科学规则。

## 验证

- `npm run build`通过：TypeScript + Vite，1694模块。
- `python -m unittest Web.tests.test_catalog_statistics -v`：4项通过，覆盖当前版本与安全公开响应、计数单位、来源目录/真实分类链接、版本失配。
- 实际服务API返回200；前端统计卡数量与JSON一致，5个section与5组版本正常显示。
- 桌面1440px与手机390px无整页横向溢出。无本轮交互的JS页面异常。
- Integral membrane分类链接到`/search?membrane_class=integral_membrane`；首页Main navigation可进入Data overview。
- 来源目录默认12→展开42；搜索ClinVar得到对应来源与`2026-09-06`，Variants & clinical evidence过滤得到6项。
- 预测工具43项可展开；计数方法details可打开。API示例没有重复`/api`前缀。
- 初次调试时服务尚未重启产生过统计404，随后重启PID1106662并核对200；最终页面无统计错误。未据此声称公网容量或部署验收。

截图：[总览桌面](../../archive/00_initial_preview/research/database_overview/figures/63-data-overview-desktop.png)、[说明桌面](../../archive/00_initial_preview/research/database_overview/figures/62-documentation-desktop.png)、[总览手机](../../archive/00_initial_preview/research/database_overview/figures/65-data-overview-mobile.png)、[来源筛选手机](../../archive/00_initial_preview/research/database_overview/figures/64-documentation-sources-mobile.png)。说明桌面图在统计服务重启前截取首屏，不作为版本表验收依据；版本表随后在交互核对中确认5行，见[确认版本截图](../../archive/00_initial_preview/research/database_overview/figures/66-confirmed-versions.png)；实际`/docs`返回200。

## 更新与边界

版本/正式数据更新后先完成对应既有导入验证，再重建统计JSON；前端文字/样式修改后build。未新增科学汇总分类或重新计算致病性。论文引用、维护机构/联系方式、许可及批量下载政策、公网运维等仍待确认，详见研究文档，不在网站伪造这些信息。


## 统计图形多样化（后续追加）

当前`/results`替代初版全部横向条形：膜类型独立覆盖率圆环、膜来源分家族卡片、变异来源纵向柱图/后果术语折叠组、预测类别与关联层次组成环图/工具搜索标签、疾病和QTL来源记录环图、Expression四场景切换集合卡片。各图保留数字、单位、计数细节，数据库与已发布统计不改；Documentation正文和其它蛋白模块不改。

验证：

- TypeScript/Vite构建通过（1,702模块）。
- 当前statistics API为200；四种组成分母逐项核对：评分类别61、评分关联层次61、疾病记录25,442、QTL关联251,055,619，均与相应已发布指标一致。
- 膜覆盖每项在0–7,715内；标签和7,753不作圆环共同分母。12个来源各归入一个呈现家族；Expression 4/3/2/4分组完整覆盖13集合、无重复。
- 以真实API数据执行五个板块的React静态渲染，全部成功，非当前Expression选区的其余原计数均保留；SVG title警告修复后无React渲染警告或NaN/Infinity。
- 浏览器选择返回`No browser is available`，本次环图悬停/固定、Expression切换、工具搜索及桌面/移动布局尚未完成实际浏览器验收。上文初版横条图的截图和交互记录不作为新版本证据。静态渲染不是浏览器测试。

实现为`DataOverviewCharts.tsx`和局部样式；维护边界、图形与单位见[现行方案](../../archive/00_initial_preview/plan/database_overview_documentation.md#多样化统计展示2026-09-21追加当前方案)。
