# 本版规则与待解决问题的处理方案

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

本页不讨论展示控件。用户已确认方向见[本版入口](README.md)；以下保留第二轮拟定过程与局部试算。2026-09-21用户授权落实当前计划后，正式规则及产物已分别进入[Function GO slim](../../../../../../modules/Function/docs/go_slim.md)与[膜标签](../../../../../../modules/membrane/docs/basic_membrane_labels.md)；本页原“待收口”不再作为执行限制。

## 1. 膜分类：四标签、单一来源

用户已明确将旧五类改为外周膜蛋白、Integral membrane protein、脂锚定蛋白、膜相关，标签可以重叠；有跨膜区段者统一使用UniProt Feature注释。

建议使用下列确定性规则，不训练模型、不设数值阈值、不引入多来源投票：

| 标签 | 建议判定依据 | 不据此推断的情况 |
| --- | --- | --- |
| Integral membrane protein | 当前canonical序列有至少一条UniProt `Transmembrane` feature | 不用Signal、Topological domain、单独Intramembrane、OPM或DeepTMHMM2预测补判 |
| 外周膜蛋白 | UniProt SUBCELLULAR LOCATION明确含`Peripheral membrane protein`（SL-9903），对象为条目通用或已明确对应canonical | 没有Transmembrane不等于外周膜；具名但无法定位的对象不补给canonical |
| 脂锚定蛋白 | 同样适用对象的UniProt拓扑含`Lipid-anchor`（SL-9901）、`Lipid-anchor, GPI-anchor`（SL-9902）、`Lipid-anchor, GPI-like-anchor`（SL-9920）；或canonical的Lipidation feature明确注明GPI-anchor | 不把全部Lipidation、普通脂质结合或MPLID/BioDolphin接触直接算为脂锚定 |
| 膜相关 | 当前默认对象没有命中以上三类的项目蛋白 | 是分类未明确的兜底，不表示非膜蛋白，也不改变项目收录范围 |

为从简，Integral在本版采用“有来源Transmembrane注释”的操作定义，不宣称完整覆盖所有生物学意义上的膜内嵌入机制。`Intramembrane`原生区段继续保留，不单列第五类，不仅凭该feature将蛋白强分Integral；若需要把它纳入Integral，须单独确认该扩大口径。

Feature不能独自完成四类判定：UniProt已经将外周膜和脂锚定明确写在其定位comment的topology中。这仍是同一个UniProt来源，不需要引入其他数据库。官方定义与字段含义：[SUBCELLULAR LOCATION](https://www.uniprot.org/help/subcellular_location)、[外周膜](https://www.uniprot.org/locations/SL-9903)、[脂锚定](https://www.uniprot.org/locations/SL-9901)。

### 对象、缺失与重叠

- Feature必须连接当前canonical的真实sequence_id；其他isoform的feature不参与当前默认标签。注释仅说明类型时可支持标签；精确绘制位点仍必须通过坐标状态检查，不猜边界。
- 条目通用comment可作为蛋白背景支持，但不改写为canonical专属实验结论。已明确对应canonical的comment可使用；其他isoform、加工产物、未解析对象均保留原注释，不填给canonical。
- 三个具体标签各自独立判断；同一蛋白可同时满足两类。`膜相关`只在三类均未命中时产生，不与具体标签同时泛化标注。
- 每个具体标签保存支持它的feature_id或annotation_id、来源原词和对象范围；不抹去条件说明。重叠不视为错误，也不自动代表同一分子在同一条件下同时具有两种机制。
- UniProt无TM注释时不以其他来源补成默认跨膜区段。其他来源现有数据仍作为独立记录保留。

### 局部试算

按上述建议，在7,715个默认canonical对象上得到：Integral 5,213、外周膜1,037、脂锚定457、仅膜相关1,046；38个蛋白具有多个具体标签。因此前三类数量不能直接相加解释为唯一蛋白数。

这里的5,213限定canonical，不能与先前“条目拥有任一UniProt TM注释”的5,214分母混用。逐蛋白依据见[预览TSV](results/membrane_rule_preview.tsv)，概况见[预览JSON](results/membrane_rule_preview.json)。全部为探索结果，未改写正式膜模块、服务表或数据库。

### 正式关联方案

建议由membrane维护派生标签与规则，再投影为`protein_membrane_label`：每行一个`accession + sequence_id + label`，支持记录存为带`source_table/source_record_id/scope`的数组。兜底标签注明`no_specific_uniprot_label`，不能伪造来源明确断言。此表只存标签及其依据，不复制TM区段。Web通过现有`membrane_uniprot_feature`和`protein_uniprot_location`查询原始证据。

## 2. GO slim：类别已就绪，映射待落实

已读取用户指定TSV及同目录manifest：140类别（MF 40、BP 72、CC 28）；配套OBO与本体subset成员一致，来源状态不是待下载。Web输入入口在config/inputs.yaml的go_slim。

建议处理方案：

1. 从完整go-basic的现有`go_term_relation`沿child→parent映射，只走`is_a`与`part_of`；不走`regulates`、`has_part`，不把调节某过程解释为参与该过程。
2. 包括类别本身的自映射，保留同aspect下所有可达slim类别，允许多对多；不任取一个类别，也不重新生成蛋白直接注释。
3. MF/BP用于功能分类，CC继续用于细胞组分分类；术语名称从`go_term`连接，未在当前字典中的slim类别补入字典。
4. `NOT`、ND、根术语、obsolete或未解析术语不进入正向分类；同一注释原有对象、relation、extension仍保留。只能作为父对象背景的关联不进入canonical正向功能。
5. 没有匹配类别时记录`no_slim_category`，保留完整原注释，不补猜类别；类别覆盖不足不是来源数据丢失。
6. 在Function负责的派生层计算`go_slim_mapping(term_id, category_id, subset, mapping_rule)`，Web通过`protein_go_annotation.go_id → term_id → category_id → go_term.go_id`使用；来源信息可集中在数据集元数据，不在每条蛋白注释重复类别名。

官方支持`is_a`与`part_of`用于注释分组，但不支持把`has_part`或`regulates`等同使用：[GO关系说明](https://geneontology.org/docs/ontology-relations/)。GO subset本身是类别集合，不能替代映射表：[GO subset说明](https://geneontology.org/docs/go-subset-guide/)。

有界比较：当前服务字典12,334个term，仅走is_a时5,131个可归类；加入part_of后6,697个可归类，产生10,335个term—category对应。其余5,637个term保持无类别状态。这是术语级图可达性比较，尚未应用蛋白对象及正向注释筛选，不能当作蛋白功能覆盖率。结果见[GO预览](results/go_slim_preview.json)。

建议采用is_a+part_of；代价是同一term可能落入多个相互嵌套类别，本版不为此再增加“最重要类别”或最短路径排名。正式映射方法尚待本版讨论收口。

## 3. 已取消或不再阻塞的事项

- 疾病标识：从Basic info移除，不再等疾病关系构建；不删除独立疾病板块。
- 功能无法对应isoform：保留NULL/未解析状态，不继续猜测匹配，不以补齐率为验收要求。
- 定位最终结论、共识和来源冲突裁决：本版不做。
- 定位版本研究：不新增工作；已有来源元数据内部保留或集中维护即可。
- 折叠、颜色、布局：不在本轮讨论范围。
- Reactome计数、KEGG新增采集、数据总览计数：维持原暂缓安排。

## 4. 当前真正剩余的决策与执行

| 事项 | 本轮给出的方案 | 下一步 |
| --- | --- | --- |
| 四类膜标签细则 | 本页规则、对象限制、支持关系和预览 | 本版收口后由膜模块正式维护和构建 |
| GO slim映射 | is_a+part_of、同aspect、多对多、保留未归类 | 本版收口后由Function正式构建 |
| 列精简 | tables.md列出可直接移除冗余、需要拆出的内容及必须保留字段 | 按选定清单实现投影，不修改上游原数据 |
| PostgreSQL更新 | 保留现有33表直到新服务数据验收；最终事务替换 | 当前不导入，不声称本轮规则已在数据库生效 |
