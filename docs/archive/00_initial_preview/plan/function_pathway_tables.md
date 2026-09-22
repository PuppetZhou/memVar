# 功能与通路：网站服务表与字段方案

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

日期：2026-09-20。用户确认13张逻辑服务表及字段精简方案，并明确Rhea participants、GtoPdb化学结构字符串和完整肽序列保留用于点击详情。展示规则与KEGG后续方向见[蛋白概览](protein_overview.md)。2026-09-21已构建13张本地Web表，新增go_slim_mapping；未修改上游数据；本地PostgreSQL按用户后续授权导入。实际清单见[本地数据](../../../../data/README.md)。来源粒度依据[GO契约](../../../../../modules/Function/docs/go_tables.md)、[Reactome契约](../../../../../modules/Function/docs/reactome_tables.md)、[Rhea/GtoPdb契约](../../../../../modules/Function/docs/molecular_tables.md)。

## 结论与数量边界

本板块采用13张逻辑服务表：GO 3、Reactome 4、Rhea 2、GtoPdb 4。它们是Web/data/tables中未来的Parquet与PostgreSQL逻辑表，不是页面表格数量，不是建议删除科研模块表。上游四类当前共35张curated表继续保留其职责。

13不包括前两模块已建议的7张基础身份/序列/功能简介表，不重复建立protein；也不包括未设计的总览面板统计表、未来KEGG或未定的定位扩展。两部分规划合计20张逻辑服务表；2026-09-21 GO slim已接入，实际构建20张，另加定位和膜信息表。若后来需要在线任意GO层级遍历、参与物反查或配体结构检索，按实际查询需求增表，不为达到固定表数删信息。

## 表清单与一行含义

| 分组 | 表 | 一行含义、主要字段及目的 |
| --- | --- | --- |
| GO | go_term | 一个GO ID：完整名称、aspect、定义、obsolete状态与链接。含被注释和slim分类引用的术语；MF/BP不拆两表 |
| GO | protein_go_annotation | 一条上游annotation—项目蛋白关联：accession、原始subject/isoform、GO ID、relation、qualifier/NOT、extension、evidence、reference、mapping_status及来源键。以(accession, annotation_id)为键，维持原证据陈述粒度 |
| GO | go_slim_mapping | 一个subset版本下的术语—分类对应：term_id、category_id、subset及版本、映射依据。供总览及点击筛选；分类名称复用go_term，不能当作新增直接注释 |
| Reactome | pathway | 一个来源内通路：source、pathway_id、名称、链接、版本、说明及来源疾病清单标记。当前只填Reactome；未来不同来源ID不碰撞 |
| Reactome | pathway_relation | 一条来源内parent—child关系，保留多父关系；层级分类与展开 |
| Reactome | pathway_topic | 一条通路—官方主题对应，主题名称/链接由pathway实体解析；保留官方分组及多主题 |
| Reactome | protein_pathway | 一条上游association—蛋白关联：accession、原始对象、pathway_id、evidence、mapping_level集合及来源键。不将不同证据陈述合并删除 |
| Rhea | rhea_reaction | 一个原始rhea_id：master_id、方向、方程式、is_transport、链接；参与物及必要名称/ChEBI/计量作为有序结构保留 |
| Rhea | protein_rhea_reaction | 一条association—蛋白关联：accession、原始对象、rhea_id、匹配依据与来源键；只从已有蛋白关联产生记录 |
| GtoPdb | gtopdb_target | 一个target_id：名称、类型、源物种、复合体/亚基说明、官网链接；家族名称可作简短数组详情 |
| GtoPdb | gtopdb_ligand | 一个ligand_id：完整名称、类型、官网链接、来源提供的化学结构字符串（如SMILES、InChI）和完整肽序列记录；所选展示所需外部标识 |
| GtoPdb | protein_gtopdb_target | 一个蛋白—靶点—关系类型对应：精确源靶点关系/复合体背景分开，保留支持源记录。无配体数据也能显示已有靶点背景 |
| GtoPdb | gtopdb_record | 一条原生药理作用、内源性配对或内源性详情记录，以(record_type, source_record_key)区分。target_id、ligand_id、作用、参数、测量条件、引用、来源及原关联对象作为结构化详情保留 |

GtoPdb三类记录采用带类型的union，不按靶点+配体合并成一行，不暗示配对与详情有来源未提供的精确一对一关系。保留每条记录原有蛋白关联上下文（如protein_contexts结构），查询不能仅将target桥与所有记录作笛卡尔扩展。必要时索引结构字段；若实际访问复杂再拆关系表，保持语义先于表数。

GO明细表可按相同对象/term/relation/extension组装显示行，引用仍对应原始证据陈述，不将证据和PMID拆成两个失去配对关系的集合。GO实验优先用实际支持记录判断，未解析/父对象背景/NOT等保持状态，不计入正向总览。

所有服务记录保留来源版本和足够的source_record_key/annotation_id/association_id追溯，不复制绝对文件路径。同一字段的原始版本与方便查询的解析版本仅在确有必要时并存。PostgreSQL结构字段可用JSONB；Parquet采用规范嵌套结构或明确的JSON字符串字段，最终导入契约统一约定。

## 哪些表合并或不复制到网站

| 上游内容 | 网站处理建议 | 原因及保留方式 |
| --- | --- | --- |
| GO summary_label/support/redundancy/旧overview | 不原样复制为四张服务表 | 原生注释支持表格组装；新版slim总览用独立映射。旧前三项不再驱动页面 |
| GO完整本体图 | 暂不复制到服务库 | slim派生在上游使用，服务侧保存确认后的映射及必要分类。若需要任意GO层级浏览再增加图边表 |
| 来源桥、蛋白桥、source link表 | 在相应服务关系中合并投影必要字段/来源数组 | 减少在线多层连接，仍保留身份层次及一对多来源，不丢不同源陈述 |
| Reactome说明表 | 按来源记录数组嵌入pathway详情 | 名称和短列表不受影响，来源有多份说明时不取最后一条覆盖 |
| Rhea参与物/compound表 | 有序嵌入reaction参与物详情 | 当前仅按蛋白查看反应，不做全库化合物反查。保留URI、ChEBI、侧别和计量，不损失反应表达 |
| GtoPdb三类关系表 | 带record_type合入gtopdb_record | 页面可分组折叠，数据库保留原生记录边界，不把同配体多实验合并 |
| 四来源coverage表 | 不逐源复制 | 现有关系可判断覆盖；将来统一面板需要预计算时再设计，区分无关联与未接入 |

## 网站服务层不导入的字段

不导入：原始TSV行、完整payload_json/RDF属性大包、内部绝对路径、调试标记、重复的字典名称和旧GO前三项字段。必要的解析/映射状态仍保留。

GtoPdb首期不导入：专利全文或专利号列表、全量跨库xref、Approved/Withdrawn等药物状态。化学结构字符串、完整肽序列及理解该序列所需的来源化学/PTM修饰说明保留在配体详情，点击后查看；不是只保留官网外链。来源原作用说明、参数、测定条件和支持引用继续保留。上游科研数据不删除。

Rhea首期不导入：完整RDF属性、SMILES及与当前展示无关的全量跨库映射。保留方程式、真实方向、参与物、计量和ChEBI链接；不能把复杂参与物强行替换成普通小分子。

GO不删除非实验注释，不仅保存slim类别。Reactome不删除父层级、多主题与多证据关系。不把已确认应保留的isoform记录作为精简对象。

## 只折叠，不从服务数据库删除

- GO术语定义、逐证据来源、条件及适用对象。限制语改变表格含义时显示简短标记，详情展开。
- Reactome长说明、层级、TAS/IEA与来源类别。
- Rhea participants及计量详情、反应级引用（若展示，明确其层次）。点击反应行打开详情，展示完整方程式、真实方向、参与物名称、底物/产物侧别、系数及ChEBI等链接。
- GtoPdb化学结构字符串、完整肽序列及相关修饰说明，点击配体查看；实验条件、原始参数名/值/关系符/单位、文献、Interaction Species、复合体背景。保留pKi等来源量纲，不把不同参数混排比较。

## 点击详情的存储与接口

- Rhea participants作为rhea_reaction中的有序嵌套结构保存；同一化合物在不同侧别/位置出现时保留各自记录，不能按名称删重。无需为点击查看新增参与物表。
- GtoPdb化学结构与肽序列保存在gtopdb_ligand中；同一ligand有多条肽来源记录时采用数组保留各条sequence、修饰说明和来源键，不任选一条。缺失留空，不从项目蛋白序列推断配体序列。
- 列表接口返回简要内容，点击详情时按reaction_id/ligand_id读取服务数据库中的完整信息；不要求列表一次返回全部长字段，也不依赖实时读取上游文件。
- 当前确认的是字符串、序列与反应详情查看，不预设必须实现化学结构绘图或3D功能。是否加入图形渲染可在页面开发时进一步设计。

## KEGG扩展边界

已列入plan为后续考虑来源，本轮不加入空表或占位数据。未来若契约兼容，可复用带source的pathway、protein_pathway等服务结构；不承诺KEGG拥有与Reactome相同的主题/层级结构。优先核实身份映射、来源范围和所需字段，再确定是否需要KEGG专用表。相同名称不作为跨库合并依据。

本页13表及上述字段取舍为既有方案。2026-09-20用户已补齐goslim_generic的140类来源；[正式映射规则与产物](../../../../../modules/Function/docs/go_slim.md)已落实，服务表已构建。Reactome计数继续暂缓。全部13张已按[本地构建方案](local_table_build.md)落盘，不修改上游正式表。
