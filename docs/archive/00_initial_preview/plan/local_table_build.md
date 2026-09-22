# 四板块本地服务表构建

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-20用户授权开始清洗和保存本地表；按已有plan从简实施，Reactome计数暂不考虑，随后用户追加授权：膜来源mapping及DeepTMHMM2先整理至cleaned，再接入Web并导入PostgreSQL。本页记录本轮实现口径，实际行数及状态集中在[数据目录](../../../../data/README.md)。

## 身份与输入

- 蛋白身份采用foundation的UniProt2026_03 cleaned表；范围沿用已确认protein_gene中的7,715个accession。cleaned中已排除的17条不重新纳入。
- 不等待跨数据库序列映射；保留原始isoform声明、不可获取状态及跨条目序列关系。canonical仅为页面默认。
- 已发布的功能关系、HPA和膜位置数据直接投影；来源字段在配套cleaned中时，按既有身份/记录键连接，不新增科学映射。
- UniProt功能与定位从同版原始JSON直接选择已确认comment类型并机械解析，避免消费探索runs。完整保存选中comment的文本和结构化证据，不导入整条UniProt payload。这是本轮本地服务投影，不代表上游正式注释模块已发布。
- 注释对象只按来源明确isoform ID、alias、名称或`Isoform + 名称`精确关联；不能唯一解析的具名对象保留unresolved，不猜测加工产物或canonical。
- 输入目录、来源自身版本及层次见[inputs.yaml](../../../../config/inputs.yaml)。HPA以实际本地快照标识，不凭官网版本推断该文件精确版本。

## 表组织

| 分类目录 | 数量 | 内容 |
| --- | ---: | --- |
| identity | 7 | 原建议的身份、序列、isoform、基因、外链、完整功能及默认FUNCTION引用 |
| function_pathway | 13 | GO三表、Reactome四表、Rhea两表、GtoPdb四表 |
| localization | 2 | UniProt原生定位comment、HPA基因级定位；GO CC共用GO表 |
| membrane | 12 | 来源序列/链、原生拓扑feature、已定位区段、TOPDOM约束；接触身份桥、BioDolphin配体实例/位点mapping、MPLID残基mapping、OPM观察mapping、DeepTMHMM2预测/区段；四类膜标签 |
| sequence | 12 | 共用UniProt feature、来源字典、PTM五表、JSD两表及Pfam三表；详见[版本记录](../../../record/00_initial_preview/20260921_sequence_v1.md) |

2026-09-21 Sequence版本共46张业务表、10个普通视图。原membrane_uniprot_feature改为共用feature上的同名视图，保留原膜范围；Sequence视图仅canonical。

2026-09-21 go_slim_mapping已按Function新发布分类桥接入，不沿用旧前三项代表功能。Reactome保存关系和主题，不生成计数。

膜信息以原生描述和来源记录为准：膜概览直接复用UniProt定位comment中的topology/orientation；本版新增四类膜标签，读取膜模块curated；生效规则见[膜标签](../../../../../modules/membrane/docs/basic_membrane_labels.md)。脂化feature不自动解释为膜锚定。拓扑只纳入本轮确认来源，AFTM和MemProtMD排除；方法预测、综合拓扑和约束保留role/method。

`membrane_topology_feature`保存原坐标，`membrane_topology_location`只保存既有正式exact映射。来源序列/链表保存链号、native_id和身份背景；映射以位置表为准。TOPDOM模型说明嵌入约束关系，不复制整库。

接触与OPM已按用户授权完成当前来源记录的mapping处理，先保存至膜模块`data/cleaned/20260920_site_mapping_01`再投影到Web。源行完整保留，只有`mapping_status=mapped`可用于目标序列坐标查询；身份桥仍不是坐标映射。BioDolphin两套编号分别保存，不能计作独立位点。OPM旧连续几何保留为来源观察，旧共识、膜类别与2Å标签不进入服务表。DeepTMHMM2直接读取已完成runs，经输入序列相等及区段核对后进入同一cleaned快照。

权威mapping方法及数量变化见[膜模块交付](../../../../../modules/membrane/docs/site_mapping_result.md)，Web不重复维护科学规则。四类标签已在09-21按当前计划接入；Basic info疾病xref按用户要求不纳入。

## 字段与实现

- 主键、粒度、字段类型、输入来源、行数与文件大小由构建生成的[manifest](../../../../data/tables/manifest.json)维护。
- 多条证据、反应参与物、肽来源记录与蛋白上下文采用Parquet原生list/struct；异构UniProt选中comment结构采用明确命名的JSON字符串字段，证据与原文本保持配对。PostgreSQL将list/struct及明确JSON字段映射为JSONB，其他列保留标量类型。
- 外部链接范围为UniProt、HGNC、Ensembl、RefSeq；本轮已取消Basic info疾病链接。编号/链接修复和存储去重按[本版记录](../../../record/00_initial_preview/20260921_basic_info_v2.md)交付。身份xref不代表序列匹配。
- 默认FUNCTION执行已确认的canonical→条目通用→来源顺序规则，保留全部FUNCTION及四类补充信息。其他isoform及未解析对象不会因默认选择被删除。
- HPA保留来源位置角色和可靠性各列，蛋白关系嵌套；不以顶层可靠性替代逐位置可靠性，不投影到各isoform。
- 不复制旧GO预览、完整本体图、覆盖统计、GtoPdb药物状态/专利和无关完整payload。

## 构建与验证

在Web目录运行`python src/build/build_tables.py`；依赖polars、pyarrow、PyYAML。Web构建脚本不写上游、不访问数据库；独立导入入口见[PostgreSQL方案](postgresql.md)。先写临时目录，验证完成后替换当前目录；正常替换异常恢复旧目录，不保留历史数据副本。若进程在目录切换中被强制终止，下一次构建检测`.tables-previous`并报错，人工检查恢复后重跑。

检查主键、蛋白范围、关键外键、序列长度、isoform引用、默认FUNCTION归属、已映射区段边界、来源记录与嵌套证据数量守恒，以及P00533实际关联查询。Parquet验证不代表API、页面或PostgreSQL性能验收。

全量2,115,852行拓扑位置表上执行了一次P00533位点过滤查询，返回37行，约0.019秒；查询进程峰值约95MiB。该结果只说明本地Parquet局部读取可用，不代表数据库并发或分页性能。记录见[local_query_check.json](../../../../data/local_query_check.json)。
