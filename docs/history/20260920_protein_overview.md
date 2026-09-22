# 蛋白概览与膜关联标签决定

日期：2026-09-20。当前方案见[protein_overview](../archive/00_initial_preview/plan/protein_overview.md)。

本页早期五类标签和疾病xref讨论已被同日[Basic info第二轮优化](../archive/00_initial_preview/research/basic_info_v2/README.md)替代，不能作为当前实施指令。

问题：如何概览蛋白基本信息，并说明7,715个膜相关条目为何只有5,214个具备UniProt跨膜feature。

此前用户提出“跨膜及lipid-linked归integral，其余归peripheral”的候选方案，尚未作为正式规则执行。本地统计发现脂化与明确脂锚不等价，非TM集合包含膜内区段和定位/feature差异，剩余集合也并非都有外周膜注释。统计依据见[研究](../archive/00_initial_preview/research/protein_overview/analysis.md)。

用户随后确认五个概览小模块，以及跨膜、脂质锚定、外周膜蛋白、膜内嵌入、膜相关（不明确）五类标签；暂不采用integral/peripheral简单二分类。该决定替代旧二分类候选，不改变已有科研数据或项目范围。具体来源判定和对象上下文仍需审查，不能把来源存在性计数作为已经完成的正式分类。

## 功能完整保存与默认展示分离

同日后续澄清：此前服务表建议只保存一条选中FUNCTION，其他FUNCTION仅在上游保留。用户明确其他isoform功能及补充信息也应保存，并可展开查看。当前方案改为五类注释完整进入所选服务数据，默认canonical及单条预览仅影响折叠展示。数据设计改用完整注释表，默认概览只引用选中记录；此前没有构建数据，无需迁移或重算。当前规则见[方案](../archive/00_initial_preview/plan/protein_overview.md)，字段建议见[数据设计](../archive/00_initial_preview/research/protein_overview/identity_function_data_design.md)。

## 默认FUNCTION选择顺序

此前研究文档提出通用FUNCTION优先，随后用户要求canonical优先，并确认同一优先级按UniProt原始顺序取第一条。现行顺序为明确canonical → 条目通用 → 默认留空，完整注释继续保存。该决定替代此前候选顺序，未执行过数据筛选，无需重算；规则统一维护于[当前方案](../archive/00_initial_preview/plan/protein_overview.md)。

## GO与分子功能展示调整

用户提供UniProt分类总览截图，明确GO采用总览加完整MF/BP注释表、文献链接与实验优先排序，替代此前单标签代表/FUNCTION辅助编选候选；未运行过代表项筛选。Rhea和GtoPdb同时明确纳入function，以条目表格折叠展示，替代此前暂作扩展内容的建议。Reactome保留官方主题及上下层级分类计数。当前规则见[方案](../archive/00_initial_preview/plan/protein_overview.md)，技术细节见[研究文档](../archive/00_initial_preview/research/protein_overview/function_pathway.md)。

## 本地表构建从简启动

用户随后授权以cleaned身份为主，按现有plan清洗并保存本地表，Reactome计数暂不考虑，不导入PostgreSQL。替代此前等待全部正式输入后才构建的执行顺序：维持7,715个已确认膜蛋白范围，复用当前正式关系；UniProt选中comment作机械投影，接触来源坐标明确标识，未验收映射与预测不冒充正式结果。当前实施口径见[本地构建方案](../archive/00_initial_preview/plan/local_table_build.md)，实际产物见[数据清单](../../data/README.md)。上游文件未修改。

## 结构mapping、预测接入及本地PostgreSQL

用户追加要求：DeepTMHMM2直接从已完成runs接入，不等待curated；OPM/MPLID/BioDolphin先完成mapping，并与预测结果一样先保存cleaned，再接入Web，汇报数量变化后导入PostgreSQL。该决定替代此前暂缓预测/结构接入及不入库的边界。膜标签规则、疾病继续不处理。当前方法及数量见[膜模块交付](../../../modules/membrane/docs/site_mapping_result.md)，数据库实施见[PostgreSQL方案](../archive/00_initial_preview/plan/postgresql.md)。

## Basic info第二轮优化

同日用户要求先重新敲定方案，再更新导入。Basic info指整个蛋白概览，本轮仅讨论数据与关联，不讨论折叠等形式。疾病标识从本部分取消；缺失编号允许NULL，功能具名对象无法对应isoform时不猜配；GO slim来源已补齐，不再列为待下载；定位不求最终结论，也不新增版本研究。

膜标签改为外周膜蛋白、Integral membrane protein、脂锚定蛋白、膜相关四类，前三类可重叠；默认canonical膜区段用UniProt Feature。四类词表替代此前五类词表，具体判定方案与GO映射方案保存在[本版规则](../archive/00_initial_preview/research/basic_info_v2/rules.md)，局部预览未发布为正式产物。外链修复代码已验证，但现有33张服务Parquet与数据库仍是上一轮交付，本版尚未更新入库。

## 2026-09-21执行收口

用户进一步明确授权冗余精简并更新已存PostgreSQL，不再等待重复确认。UniProt/HGNC外链由已有身份关系组合，移除BioDolphin嵌套位点副本及可派生属性；GO slim和膜标签落实当前计划。版本与真实执行结果见[20260921_basic_info_v2](../record/00_initial_preview/20260921_basic_info_v2.md)。
