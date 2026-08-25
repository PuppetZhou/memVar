# 08. Reactome DAG 层级展示计划

状态：已完成（M9.1–M9.4，2026-08-12）  
计划日期：2026-08-12  
适用阶段：M8 完成后的 M9 Reactome pathway hierarchy 展示  
范围：只修改 `website/` 内 Reactome hierarchy 派生表、只读 API、Basic information 展示与测试；`View/` 继续只读。

## 1. 用户目标

1. Reactome pathways 不再按名称排成无法辨认关系的一列。
2. 使用 `View/Annotation/reactome_pathway_hierarchy.parquet` 的直接 parent→child 边展示上下级通路。
3. 默认先显示根级通路摘要，用户可逐层展开；多父通路必须保留共享关系。
4. 页面正文继续只显示 pathway name，不显示 `R-HSA-*` 编号；稳定 ID 只用于数据、key、链接和无障碍关联。

## 2. 数据审计与科学语义

- hierarchy 文件为 2,899 条唯一直接父子边，2,883 个 Human Reactome 节点，无 NULL、自环或环；最大深度 11。
- 该结构是 DAG：34 个节点有多个父节点，最多 6 个父节点，禁止强制转换为单父树。
- `reactome_pathway_membership` 是 protein→pathway membership 事实；hierarchy edge 只表达 pathway 之间的直接上下级关系。
- 不把父节点 evidence 传播给子节点，也不把子节点 evidence 汇总成新的父节点事实。
- 多父节点的 evidence 只返回一次；UI 在一个分支完整展示，在其他父分支显示 shared reference，避免重复事实。
- 所有 protein membership 的直接父节点也存在同 protein membership，因此构建 accession-induced DAG 时无需补造祖先 membership。

## 3. M9.1：Core mart 引入 hierarchy edge

- 在 `etl/build_core.py` 注册 hierarchy 输入 schema。
- 生成 `reactome_hierarchy_edge(parent_pathway_id, child_pathway_id)` 小表。
- 构建时断言 parent/child 非空、无自环、边唯一；不生成独立 QC 文件。
- `reactome_membership` 保持原粒度和字段，不与 hierarchy 做宽连接。

## 4. M9.2：Protein-scoped DAG API

新增只读端点：

`GET /api/v1/proteins/{acc}/reactome-hierarchy`

返回规范化 DAG：

- `nodes[]`：每个 membership pathway 恰好一条，含 id、name、url、evidence codes/count、`parent_ids[]`、`child_ids[]`；
- `roots[]`：该 protein-induced DAG 中没有父节点的 pathway IDs；
- `node_total`、`edge_total`、`root_total`、`shared_node_total`；
- 明确 `edge_semantics=direct_parent_child` 与 `node_semantics=protein_pathway_membership`。

节点与 parent/child ID 数组按 pathway name、再按稳定 ID 确定性排序。响应不嵌套复制节点，不分页切断分支；全站最大 membership 为 425 个节点，受源数据自然上界约束。

## 5. M9.3：分层交互视图

- 新建独立 Reactome hierarchy Client Component，由 Basic information 的 Reactome card 加载专用 DAG endpoint。
- 默认显示根级 summary cards：根 pathway name、该分支 pathway 数量和直接 child 数量。
- 点击根或子通路逐层展开；使用缩进、连接线和层级标记表达 parent→child。
- 多父节点选择一个确定性 canonical branch 完整展开；其他父分支显示 `Shared pathway` reference，可定位/展开 canonical occurrence。
- 外部 Reactome 链接与展开按钮分离，避免一次点击同时导航和改变层级。
- 支持 mouse、keyboard、touch；button 使用 `aria-expanded`、`aria-controls`，状态文本使用可见文案。
- 默认只挂载已展开分支；不一次性渲染 425 节点的重复嵌套 DOM。
- loading、error、空结果和“显示 N 个 pathway / E 条 hierarchy relations”均明确展示。

## 6. M9.4：验收

- P00533：78 nodes、74 edges、5 roots、1 shared node；可见典型链 `Signal Transduction → Signaling by Receptor Tyrosine Kinases → Signaling by EGFR → EGFR downregulation`。
- A0FGR8：2 nodes、1 edge、1 root，稀疏层级正确。
- A0A075B6H7：0 nodes/edges/roots，显示 Reactome 空态。
- API 中每个 membership node 只出现一次，所有 edge 两端都存在于 nodes，多父关系不丢失。
- 页面正文不显示 `R-HSA-*`；pathway name 与 Reactome 外链仍可用。
- 后端相关测试、前端 production build 通过；`View/` 无任何写入。

## 7. 明确不做

- 不把 DAG 静默压成单父树。
- 不推断 pathway 活性、方向、富集显著性或 protein 在父/子 pathway 中的因果作用。
- 不复制或合并不同节点的 evidence。
- 不修改 Reactome 源 parquet，不访问外部 Reactome API，不在运行时扫描 `View/`。

## 8. 实施与验证记录

- Core mart 已加入独立 `reactome_hierarchy_edge`，包含 2,899 条唯一直接父子边；membership 事实保持原表、原粒度。
- 已新增 protein-scoped normalized DAG endpoint；节点只出现一次，parent/child 双向引用、roots、edge/node/root/shared totals 均为精确值。
- Basic information 已改为全宽 Reactome hierarchy card：默认根级摘要、逐层 disclosure、shared reference、独立 Reactome 外链及 loading/error/empty 状态。
- P00533 验收为 78 nodes / 74 edges / 5 roots / 1 shared node；A0FGR8 为 2/1/1/0；A0A075B6H7 为全 0 空态。
- 后端全量测试：`55 passed`；前端 production build 与 TypeScript 检查通过。
- 浏览器像素观感与真实触屏手感保留给本地人工审阅；自动验证不执行未经请求的浏览器点击或截图。
