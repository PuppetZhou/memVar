# 00 首版构建与公网预览：执行记录

截至2026-09-21的实际交付，2026-09-22仅按阶段搬移，原文件名和验证范围保留。当前工作见[01阶段](../../research/01_preview_optimization/README.md)，研究依据见[00归档](../../archive/00_initial_preview/README.md)。

本目录按用户要求记录实际服务数据/数据库交付版本、改动、验证和限制，不保存历史数据副本。当前Parquet由各服务构建入口维护，基础表在Web/data/tables，疾病表在Web/data/disease_tables，PostgreSQL构建清单记录版本与输入。

- [20260921首个公网预览版](20260921_public_preview_v1.md)：用户确认 ngrok 发布、本地数据保留、累计改版摘要与后续迁移/高分辨率 AlphaGenome 方向。

- [20260921网站初版](20260921_website_v1.md)：本地运行入口、实际展示范围、序列/结构及分类筛选浏览器验收、截图和当前边界。
- [20260921基础与Sequence API](20260921_api_core_v1.md)：只读身份、字段/对象语义、启动及输入边界验证。
- [20260921证据API](20260921_api_evidence_v1.md)：Variant/PPI/Expression/QTL/Disease查询与内容审查，ΔΔG单位依据。

- [20260921_basic_info_v2](20260921_basic_info_v2.md)：Basic info去重、统一外链视图、GO slim及四类膜标签。
- [本次迁移前冗余核对](20260921_basic_info_v2_audit.json)：逐字段相等性、原行数及原schema。

早期设计替代依据仍保留在[history](../../history/README.md)；本目录记录已执行结果。

- [20260921_sequence_v1](20260921_sequence_v1.md)：canonical Sequence，46张业务表、10个普通视图；PTM/Pfam/JSD与共用UniProt feature已导入。

- [20260921 Variant精简方案与频率交付](20260921_variant_plan_frequency.md)：方案阶段及频率Parquet交付；后续实际入库见Variant v1记录。

- [20260921_disease_v1](20260921_disease_v1.md)：疾病20张业务表、12个普通视图，精简后导入web_disease，复用已有基因/蛋白mapping。

- [20260921_variant_v1](20260921_variant_v1.md)：五张核心表及六张辅助表，频率与canonical ddG关联已导入web_variant并验证。

- [20260921_context_v1](20260921_context_v1.md)：QTL/PPI/Expression的34张业务表、16个视图已导入web_context，来源数值、关联及实际查询验证完成。

- [20260921 Variant证据面板精修](20260921_variant_evidence_refinement.md)：本轮CATVariant定向调研、六类展示调整、真实样例与桌面/窄屏验收。

- [20260921 Expression与PPI细节精修](20260921_expression_ppi_refinement.md)：数字分页、14数据集/5测量类别说明、IntAct原效应优先和可读标签审查；真实桌面/窄屏验收。

## 其余板块与阶段摘要

- [Full Sequence Atlas精修交付](20260921_atlas_refinement.md)
- [数据总览与Documentation交付](20260921_database_overview.md)
- [首页第一版交付](20260921_homepage_v1.md)
- [Basic Info膜特征补充与证据分层](20260921_membrane_evidence_refinement.md)
- [序列/结构精修与预测interface接入](20260921_sequence_structure_refinement.md)
- [网站第二版交付与验证](20260921_website_v2.md)
- [00阶段实现与验证摘要](implementation_overview.md)
