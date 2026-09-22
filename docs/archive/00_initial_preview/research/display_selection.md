# 前端展示数据审查

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../README.md)，本文不作为当前执行指令。

2026-09-21开始。用户要求依据已导入PostgreSQL的服务表，以选择题逐轮确认值得展示、折叠查看及不展示的信息，先选数据，再确定具体展示形式。本页维护待决项、确认进度和依据；按用户追加要求，从Basic info开始，每次讨论一组信息，一个板块确认完成后即整理对应现有plan，不等待全站讨论结束，不把建议写成生效规则。

## 当前授权与完成标准

- 原逐题审查停在身份补充信息第1题，尚未收到该题答案。用户随后授权初版并已提出第二版明确修改要求；当前直接按[第二版方案](../plan/website_v2.md)实施，问题/调研状态见[第二版清单](website_v2/issues.md)。本页保留早期问题背景，不作为等待用户选题的执行限制，也不将后续自主实现记成原题已回答；不重跑科学处理或导入。
- 保留已有科学规则与已确认内容范围，逐项细化可见字段及默认/展开层次。涉及调整已确认展示规则时明确指出。
- 每组确认后记录字段、所属对象、来源表/视图、显示层次及必要限定信息；全部相关组确定后进入具体形式和API设计。
- 默认展示、展开查看、不在页面展示分别记录；后者不删除数据库字段，API/导出范围另行确定。
- 可解释性所必需的来源、对象、单位、映射状态和缺失语义不能仅因精简而消失；内部工程键不自动成为页面字段。

## 入库核对

2026-09-21 01:41香港时间（数据库返回UTC 2026-09-20 17:41）再次只读查询pg_class、pg_stat_activity和四个_build_manifest，并读取各板块导入/验证报告，结果与01:35核对一致：

| schema | 当前版本 | 业务表 | 普通视图 |
| --- | --- | ---: | ---: |
| web | 20260921_sequence_v1 | 46 | 10 |
| web_variant | 20260921_variant_v1 | 11 | 6 |
| web_disease | 20260921_disease_v1 | 20 | 12 |
| web_context | 20260921_context_v1 | 34 | 16 |

共111张业务表、44个普通视图，另有各schema的构建元数据表。查询时未见活动导入，只有autovacuum；这是当时状态，不作为持续监控。未重复全量扫描；导入与验证依据分别见[Sequence](../../../record/00_initial_preview/20260921_sequence_v1.md)、[Variant](../../../record/00_initial_preview/20260921_variant_v1.md)、[疾病](../../../record/00_initial_preview/20260921_disease_v1.md)、[Context](../../../record/00_initial_preview/20260921_context_v1.md)。后续API、前端及代表性本地联调已完成，详见[网站交付](../../../record/00_initial_preview/20260921_website_v1.md)；该实施状态不表示本页字段选择题已获回答。

## 参考依据

采用本地2026-09-20资料快照，未重新在线审计参考网站：

- [CATvariant数据组织](../../../../Web-research-reference-2026-09-20/docs/sites/catvariant/02-data-organization.md)：概览、具体对象与来源证据分层。
- [ProtVar学习总结](../../../../Web-research-reference-2026-09-20/docs/sites/protvar/04-lessons.md)：主行保留比较所需信息，其他注释按需展开，isoform对象明确。
- [项目既有采用决定](../plan/site_construction/reference_lessons.md)：不照搬参考站的科学代表项、评分或计数规则。

当前只借鉴信息层次；卡片、表格、图形及布局在选定内容后讨论。

## 入库完成后的建议顺序

2026-09-21入库后曾确定以下推进顺序，沿用[已确认架构](../plan/site_construction/architecture.md)。后续初版已在自主构建授权下落实主要链路；此表保留方法与逐题审查依赖，不替代尚未回答的展示选择题。

| 步骤 | 本步确定或交付什么 | 与数据库优化的关系 |
| --- | --- | --- |
| 1. 按研究任务选展示数据 | 从Basic info开始；逐组确定默认字段、展开详情、仅后台字段、适用对象及来源/状态限定；同时列出搜索、筛选、排序需求 | 先获得真实查询目标，不凭列数或表数决定删列、拆表或加索引 |
| 2. 确定信息组织和接口契约 | 在该板块字段确认后选择列表/详情组织，定义REST请求、返回字段、稳定分页与缺失状态；不要求全站讨论完才开始一个板块 | 将页面需要转成有边界的SQL查询，避免全字段/全量返回 |
| 3. 完成第一条真实链路 | 蛋白检索→身份/功能/定位→来源详情；沿用既有canonical和注释适用对象规则，以真实库数据验证 | 检查查询计划、接口响应大小与延迟；仅对瓶颈调整SQL、索引或已确认口径的预计算 |
| 4. 按板块扩展 | Basic info之后沿用Sequence优先等已确认计划，接入Variant及其他已入库内容，复用对象与详情 | 对变异/QTL等大表重点验证实际过滤、排序、计数与深分页；不能只测LIMIT首页 |
| 5. 联调与上线准备 | 关键路径和跨板块一致性、代表性并发负载、部署与恢复 | 再依据真实负载决定连接池、资源配置或缓存；不将本地SQL样例耗时视为网站性能承诺 |

理由：已交付库已有字段去重、主键/部分外键、查询索引、普通视图和定向SQL验收。当前证据没有显示必须先做全库重构才能开展展示设计；后续是否需要新索引、物化结果或缓存，应由已选查询和实际瓶颈决定。性能优化不得改变科学筛选、缺失语义或返回对象。

具体技术组合仍由架构文档唯一维护：Python/Parquet→PostgreSQL；FastAPI/Pydantic/SQLAlchemy Core/psycopg的单体模块化API；React/TypeScript/Vite/React Router前端。参考CATvariant的对象概览和证据层次、ProtVar的紧凑结果与补充注释，不推定两站使用本项目技术栈。序列/结构组件按实际可用数据与映射适配，导入完成不等于结构展示条件全部就绪。

## 第一轮：Basic info身份与序列（待用户选择）

当前从第1题开始逐题询问，既有三道题尚未得到选择。Basic info沿用已确认的五组范围：身份与序列、功能简介、功能与通路、细胞与膜定位、膜关联特征与收录依据；数据总览另按既有指标待决边界处理。完成该板块审查后，整理protein_overview.md及相应字段专文中的展示契约，写清数据库字段/视图对应、默认/展开/不展示、对象与缺失状态；具体样式及布局留下一阶段。

已有[身份展示规则](../plan/protein_overview.md#身份与序列已确认展示规则)继续有效：蛋白名称、UniProt accession、UniProt gene names、HGNC关系、human、当前序列身份/canonical及对应长度；真实多关联保留，不能构造isoform编号。这里不重新询问是否收录这些信息。

| 待决组 | PostgreSQL依据 | 建议 | 取舍 |
| --- | --- | --- | --- |
| 补充名称和历史编号 | web.protein.entry_name / alternative_protein_names / secondary_accessions | entry name、其他蛋白名称展开查看；次级accession不在页面展示，保留后台 | 帮助认名但控制历史编号占用；次级编号并非当前isoform编号 |
| Ensembl/RefSeq交叉引用 | web.protein_external_reference_all及其底表 | UniProt/HGNC默认展示；Ensembl/RefSeq编号及来源配对关系展开查看 | 避免长编号清单；展开仍区分基因、转录本、蛋白及核酸，交叉引用不宣称序列匹配 |
| 完整序列与其他isoform | web.protein_sequence / protein_isoform | 默认保留当前序列身份和长度；完整序列及其他isoform声明、可获取状态展开查看 | 便于确认对象；不把完整序列或全部isoform清单占满基础信息。Sequence注释仍按本期canonical范围 |

真实样例：库内EGFR（P00533）为1,210 aa，entry_name=EGFR_HUMAN，有2个其他蛋白名称、13个次级accession、4条isoform声明；外链底表有4条Ensembl transcript和4条RefSeq protein记录。仅定向查询该蛋白，不将其分布推广到全库。

选择题：

1. 补充身份信息：A 推荐层次；B 全部展开可查（包含次级accession）；C 三类补充信息均不在页面展示。
2. 外部编号：A 推荐层次；B 四类外部库的全部编号默认展示；C 页面只保留UniProt/HGNC，Ensembl/RefSeq不展示（将修改既有外链可见范围）。
3. 序列内容：A 推荐层次；B 其他isoform身份/长度/状态默认展示，完整序列展开；C Basic info只保留当前序列摘要，完整序列和其他isoform信息转到独立序列信息入口；不自动扩大Sequence注释范围。

状态：三题均待回答，尚未确认任何候选层次。后续建议按功能简介与通路、定位与膜、Sequence、Variant、疾病、Expression/QTL/PPI逐组审查；顺序可由用户调整。数据总览只在指标与计数口径明确后讨论具体数值。


## 科学数据补充：PeSTo / SPPIDER-seq（2026-09-21）

用户已确认将映射至序列的预测纳入科学数据集。**已验证发布，可作为PostgreSQL服务数据补充；当前尚未导入PostgreSQL，不计入现有111张业务表和44个视图。**

- 正式快照：[20260921_interface_predictions_01](../../../../../modules/PPI/data/curated/20260921_interface_predictions_01)。[字段与科学关联契约](../../../../../modules/PPI/docs/interface_predictions.md)、[验收结果](../../../../../modules/PPI/docs/result.md#界面预测科学数据集2026-09-21)为主要维护位置。
- PeSTo保留结构分片、canonical位点、五类连续分数与pLDDT；SPPIDER-seq保留query序列位点、伙伴及receptor/peptide两个预测头。通过原sequence_content和canonical/foundation关系解释位点，不将partner分数或结构编号混作query坐标。
- 5,792,650条PeSTo结构残基记录和310,534个SPPIDER方向全部保留，后者对应192,078,142个query位点—伙伴记录。物理存储为完整向量，不等于独立位点数或实验界面数。
- 本次未新增阈值、分片代表选择、跨伙伴汇总、二值标签或实验支持投票，也未重跑模型。SPPIDER冻结输入包括不同来源证据类型，不能把每个方向当成已确认的物理互作。
- 下一步在Sequence/位点及PPI展示审查时决定展示哪些分数、结构和伙伴上下文，再设计服务表、查询/API并按后续授权接入。科学数据已可用，不再以“仅有runs预测、未正式发布”阻塞服务数据选择。

此补充不改变上方Basic info选择题状态，也不自动确认界面预测的首屏布局、阈值和默认伙伴。
