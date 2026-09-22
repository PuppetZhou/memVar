# 蛋白context：PPI、QTL与Expression

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

更新：2026-09-21。用户确认精简表格与字段、保留必要信息和链接。Expression方案见下方入口。已按授权完成精简、构建与PostgreSQL导入验证；科学映射沿用现有正式关系，执行与验收见[本版记录](../../../record/00_initial_preview/20260921_context_v1.md)。

## PPI

- 参考BioGRID的筛选式表格，支持互作方式/实验类型筛选及context场景选择。
- BioGRID、IntAct条目分数据库展示，不生成跨库统一互作结论。表格保留原生关系及来源入口，详情展开证据和上下文。
- context使用已有源集合或记录明确的标签，显示来源含义；不能把专题集合一概称组织/细胞系，也不由基因或文献标题猜场景。
- 精简重复字段，保留参与者身份/物种、实验方法、角色、证据/文献、阴性标记及映射状态。来源全文在上游保留，网站只导入展示与追溯所需列。
- full/context可能包含同一观察，切换集合不等于新增独立实验；不自动跨来源去重或计算支持投票。

### 2026-09-21 PPI overview 与场景入口修正

- 已有35个来源集合完整保存在PostgreSQL：2个full、32个context、1个IntAct mutation。旧API固定`PPI_FULL`，使context/mutation没有浏览入口；本轮只扩展服务查询与展示，不重新入库。
- Overview优先显示IntAct mutation独立卡片、BioGRID/IntAct full入口，以及按来源区分的疾病/研究专题集合卡片。context名字来自原始`context_raw`，可搜索、按来源收窄、查看无记录集合，不把不同数据库同名场景合并。
- 用`dataset`精确选择membership集合，下方表格、类型筛选、分页和环状图保持相同范围；游标绑定dataset，避免跨集合继续旧页。默认仍为full合集；选择空集合返回真实空结果，不回退full。
- 互作类别柱状图替换为紧凑环状图和带数字/百分比的图例，仅作统计展示；入口在集合卡片和筛选器。Mutation选中时显示来源feature type分布。
- Mutation是受影响蛋白关联的来源feature记录。按2026-09-21后续反馈，专用列表依次显示短mutation/Feature ID、醒目的互作影响、来源伙伴、序列替换、文献、证据入口；移除Source range与mutation标签中的UniProt前缀，Interaction AC移到详情外链。详情先显示效应卡片，附加来源证据折叠；API/正式数据仍保留原range和身份。源坐标/序列尚未验证，不关联项目variant或canonical位点，不将feature记录数称为唯一突变数。
- full/context共享原生内容正文，集合计数按distinct record_id；多个context可以重叠，不能相加成独立证据数。部分历史专题包装可能与full包含相同记录，不重新解释其疾病特异性。
- 当前不增加PPI网络。实现及验收见[context交付记录](../../../record/00_initial_preview/20260921_context_v1.md#ppi-overview场景与mutation入口修正2026-09-21)。

## QTL

- 先显示当前基因的各组织数量概览，区分数据库与QTL类型。点击数据库/类型/组织进入对应分页条目表，并联动基因组坐标视图。
- 数量按相同筛选下的关联记录计，明确标签为“关联记录数”；GTEx summary单独保留，不加入pairs数量。不同数据库/研究/组织可能重叠，不把总记录数解释为唯一变异数或独立证据数。
- 保留来源组织标签；eQTLGen按研究级blood/PBMC背景展示，不伪造逐行具体组织；缺失组织单列未知，不填猜测值。
- 本阶段不进行突变mapping：不关联项目variant_id，不做等位基因规范化、liftover或rsID到变异的补齐。继续使用现有HGNC→蛋白身份关系按基因查询。
- 坐标可视化使用来源已有坐标及明确参考版本，叠加同版本基因位置；这只是基因组位置显示，不意味着匹配了项目具体等位基因。不同组装不共用同一轴。
- 保留P值与来源提供的效应、等位基因及表型信息，详情保留FDR/q值、样本量和研究元数据。当前不新增统一显著性门槛。

## Expression

已确认数据集来源→数据类型→组织/细胞类型分开展示，支持折叠与截选，Cancer独立成板块。字段精简、来源保留及基于foundation基因身份的串联见[Expression方案](expression.md)。

## 实施边界

PPI/QTL字段分层与3+5类逻辑服务表已纳入[字段与表方案](context_tables.md)；实际context标签需核对，跨来源生物学归并不在本期范围。PPI/QTL数据来源与规模见[来源研究](../research/context/ppi_qtl.md)。


## 2026-09-21 互作效应与可读标签精修

- 原 feature type 的 increasing/decreasing、strength/rate、disrupting、causing、with no effect 分别以文字、箭头和颜色显示；环图与列表颜色一致，图表仍只作展示。未知类别保留原词；通用 `mutation` 显示 Effect not specified，不能当作无效应或自行猜上/下调。
- 效应针对当前原互作记录，不是基因表达调控方向或临床致病分类。同一 mutation 的不同伙伴/实验记录不合并。
- 所报伙伴仅提取源参与者字符串中的明确 UniProt 标识；不新增蛋白匹配。不因仅剩一个可解析标识就断言同源二聚体/自互作，未明确伙伴时标示 source participant。
- Expression/QTL组织、细胞、项目等可读标签将下划线变为空格；来源ID、filter/context key保持原值。Expression数字分页与测量类型规则见[Expression方案](expression.md#expression-display-refinement)。
- [本轮交付与真实验收](../../../record/00_initial_preview/20260921_expression_ppi_refinement.md)维护验证范围，替代上述旧版默认展开全部来源字段的展示。
