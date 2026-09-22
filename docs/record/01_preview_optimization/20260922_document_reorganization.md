# 01阶段：反馈登记与文档重新编号

日期：2026-09-22。用户先要求逐项记录全部反馈，随后要求从刚建立的清单开始重新编号，将此前research归为archive，并做好record。本记录只说明已完成的文档工作，不代表55条网站/数据目标已经实施。

## 已完成

1. 原反馈已整理为[14个区域、55条问题](../../research/01_preview_optimization/issues.md)，每条包含分类、描述、现状定位与讨论/验收目标；膜分类树、计数分档示例、13类PTM与两张附图保留，问题ID不变。
2. 新阶段编号为`01_preview_optimization`；此前统一为`00_initial_preview`，不为旧“v1/v2/多轮精修”虚构多个正式阶段。
3. 旧研究整批归档，脚本、结果和图像随主题保留；每份旧研究Markdown增加历史状态说明。旧记录按00收纳，原日期文件名保持；新增01记录入口。
4. 新增[文档总索引](../../README.md)、research/archive/record分层索引和01阶段入口；精简Web README，把原首版进度段落转入[00实现摘要](../00_initial_preview/implementation_overview.md)。首页模块表改为依赖导航，避免重复维护过期进度。
5. 首轮曾保留plan原位；同日用户追加要求“plan方面也要做处理”，现已归档31份旧方案并建立01计划，取代首轮的目录安排，详见下方追加记录。history继续维护决定替代原因；相关约定与导航已同步。

## 路径变化

| 原位置 | 当前位置 | 处理 |
| --- | --- | --- |
| `Web/docs/research/next_stage/` | `Web/docs/research/01_preview_optimization/` | 整体搬移，保留issues和两张附图；增加阶段README |
| `Web/docs/research/`中其余11个主题目录/文件 | `Web/docs/archive/00_initial_preview/research/`下同名主题 | 共53个原文件，其中28份Markdown；原主题内部结构保留，详细入口见[00 archive](../../archive/00_initial_preview/README.md) |
| `Web/docs/record/`原日期文件及原README | `Web/docs/record/00_initial_preview/` | 原20文件搬移，其中19份Markdown和1份JSON；另补00实现摘要及完整索引 |
| `Web/README.md`原首版阶段长列表 | `Web/docs/record/00_initial_preview/implementation_overview.md` | 保留日期、原进度和验证边界，重新计算相对链接 |
| `Web/docs/plan/`原31份方案 | `Web/docs/archive/00_initial_preview/plan/` | 按同日追加要求归档；新计划在`plan/01_preview_optimization/`，未替代契约由plan索引注明沿用 |
| `Web/docs/history/` | 原位 | 继续记录重要决定替代原因，链接到新阶段总索引 |

三个旧研究脚本原来用固定父目录层数找项目根。归档路径增加两层，因此`profile_overview.py`、`profile_identity_function.py`的`parents[5]`改为`parents[7]`；`basic_info_v2/scripts/review.py`的`parents[4]`改为`parents[6]`。只修正根路径，输入/输出逻辑和历史结果没有改变；示例命令同步到归档路径。脚本没有执行，后续若复用应先检查当时输入与当前快照适用性。

## 首轮验证与边界（research/record整理）

- 搬移前记录的1,750个有效本地引用目标均保留；完成后检查Web docs、项目/阶段入口、模块README/docs与三份受影响服务数据说明中的1,856个本地链接，未发现断链。迁移记录中的旧路径作为对照保留，其余受检查文档没有失效旧路径残留。旧记录中一条指向旧项目源码的`:284`行号链接按源码文件核对，不当作普通文件名判错；本次未逐个验证Markdown标题锚点或外部网页可达性。
- 核对55个问题ID完整且不重复、两张用户附图仍在、归档原文件数量保持；旧18份日期交付Markdown和JSON均保留。
- 对三个路径调整脚本做语法解析及父目录定位核对，不运行统计或数据流程。
- 本次仅改文档组织、引用和上述必要脚本路径；没有修改前后端业务逻辑、正式数据、PostgreSQL或运行服务，没有进行浏览器验收。

当前工作入口：[01研究](../../research/01_preview_optimization/README.md)。后续研究沿用本阶段目录；落实决定后更新对应plan/模块规则，实际实现与验证进入01 record，再回写issues状态。

## 同日追加：plan阶段整理

用户明确要求plan也要处理。原31份Markdown（含原索引和site_construction四文档）整体进入`archive/00_initial_preview/plan/`，不再与01计划平铺。所有旧方案增加00基线说明；旧“已授权/待执行”等状态不自动成为当前任务指令。

新增[plan适用索引](../../plan/README.md)与[01阶段计划](../../plan/01_preview_optimization/README.md)。前者按领域关联旧契约和本轮问题，后者明确目标、当前授权、工作包输入输出、依赖及验收方式；没有把55条反馈复制成第二份状态清单，也没有将候选方案伪称全部确认。后续专题确认后按编号加入01 plan，注明替代条款；未改变的规则通过索引继续沿用，不复制全部旧方案。

根README、Web README/AGENTS、文档总索引、research/archive/history/record入口及跨模块引用同步更新。该安排明确替代首轮“plan按主题原位保留、不分阶段”的目录决定；只改文档，不改业务代码、科学规则或正式数据，不运行数据/数据库流程。

追加验证：31份旧方案均在归档，plan顶层仅保留总索引和01目录；55个问题ID保持完整且不重复。搬移前记录的1,964个有效本地引用目标仍存在；对Web文档、受影响项目/模块入口及服务数据说明的1,939个本地链接核对，未发现断链或仍指向原plan平铺文件的链接。新索引表格结构通过检查；未逐个验证标题锚点和外部网页，也未运行网站或数据测试。
