# 01 公网预览后优化

起始日期：2026-09-22。当前阶段；从用户刚提出的完整反馈开始重新编号。

## 目标与状态

通过视觉、交互、信息组织及数据补全改善当前公网预览。**[issues.md](issues.md)** 是本阶段唯一完整问题清单，含14个区域、55项；既有问题ID保持不变，避免后续讨论和验收失去对应关系。

当前已完成逐项描述、定位、分类及[逐项解决方案](../../plan/01_preview_optimization/01_solutions.md)。55项中MEM-01～03正式交付、VA-03/05/07/08此前已发布但待桌面验收、VA-04取消；剩余47项中的46项已[并行构建数据/组件/API并本地发布](../../record/01_preview_optimization/20260922_parallel_web_execution.md)，UI-02尚未交付Figma画布。代码发布不等于真实桌面验收。科学边界由[数据决定](01_data_decisions.md)维护。

## 按问题进入

后端减容：2026-09-30确认[DuckDB＋Parquet迁移计划](../../plan/01_preview_optimization/04_duckdb_parquet_migration.md)，2026-10-01已完成存储、网站验收与预览切换。保持全部信息、关联与前端行为，原PostgreSQL保留不动，AlphaGenome大型资源未优化；当前证据见[迁移记录](../../record/01_preview_optimization/duckdb_storage_migration.md)。历史容量与技术比较见[存储审查](alphagenome_storage.md#2026-09-30数据库减容审查建议尚未实施)。

新增数据接入：[AlphaGenome新版、AVI归因与存储分析](alphagenome_storage.md)（2026-09-29，含实测容量与上云建议）；已按后续授权形成[轨道设计](../../plan/01_preview_optimization/alphagenome_atlas.md)并接入新版参考与AVI总分，归因原包损坏的依赖见[交付记录](../../record/01_preview_optimization/20260929_alphagenome_avi.md)。

| 工作范围 | 清单ID |
| --- | --- |
| 全站视觉、模板与动效 | UI |
| 膜分类、定位、GO、膜注释、反应药理、通路 | MEM、LOC、GO、MF、PH、RE |
| 序列、Atlas、结构和变异浏览 | SQ、AT、ST、VA |
| 表达、PPI和疾病 | EX、PP、DI |

当前安排见[01计划](../../plan/01_preview_optimization/README.md)，具体实施和验证见[01 record](../../record/01_preview_optimization/README.md)，问题状态回链实际记录。专题按需新增，不复制整份清单。

参考资料：[前一阶段归档](../../archive/00_initial_preview/README.md)、[当前有效方案](../../plan/README.md)、[文档总索引](../../README.md)。两张用户附图继续保存在本目录`assets/`。

本轮数据决定见[01_data_decisions.md](01_data_decisions.md)，视觉路线见[已选UI工具方案](../../plan/01_preview_optimization/03_ui_toolkit.md)。D03全转录本补全已取消；D04～D07均已确认，当前范围的代表序列关系和ClinVar条件证据已发布，后续只对新增科学差异重新讨论。
