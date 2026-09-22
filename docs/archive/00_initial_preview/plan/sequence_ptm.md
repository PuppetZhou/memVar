# Sequence PTM：表与信息筛选

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-21。落实本轮从简、只考虑canonical的范围。服务筛选、构建与PostgreSQL导入已完成，物理表名/数量见[版本记录](../../../record/00_initial_preview/20260921_sequence_v1.md)。现有科学映射沿用[PTM契约](../../../../../modules/Site-Region/docs/ptm_tables.md)，不重做映射或跨来源合并。

## 记录选择与链接

- 输入为Site-Region正式`20260915_ptm_native_02`，不是旧mapping或原始全库重解析。
- 位置入口：protein.default_sequence_id → site_index.sequence_id → record_site → annotation_record。仅明确连接canonical的位点进入轨道；成键只连接已确认端点。
- 已明确映射其他isoform的记录不纳入本板块；不删除上游数据或已有共享序列表。
- 未定位记录保留蛋白级来源详情及状态，不转换为canonical位点。候选序列不作为已映射关系；mapping_candidate本轮不导入轨道服务。
- UniProt、dbPTM、ProteomeScout、GlyGen、PTMD2保持独立条目。相同位置或修饰名称不作为跨来源去重依据。
- 上游241,192个位点含非canonical；已发布canonical子集为219,771个位点、7,521条序列。本版验证同为219,771个位点；筛选后来源记录642,233条，位点关系500,825条。来源覆盖汇总继续暂缓。

## 最小服务组织

| 内容 | 选择与精简 |
| --- | --- |
| PTM记录 | annotation_record与一对一annotation_detail投影为一张逻辑记录表，短字段列化，特殊详情结构化保存；四个topic分片统一读取，不按五来源建五套表 |
| 位点 | 复用site_index：site_id、sequence_id、position、residue及参考基准；蛋白名称与完整序列从身份表取得 |
| 记录—位点关系 | 保留record_id、site_id、endpoint_role、mapping_method，不重复保存可恢复的目标位置；成功状态的目标序列/坐标由详情视图恢复，含仅停用证据记录；未定位仍为空，所有记录保留原生位置 |
| 证据 | 保留record_id关联、namespace、identifier、证据类别、current状态、字段路径及有用来源原文；不将证据多条展开为重复PTM记录 |
| 共用来源 | 现在保留dataset_id及最小来源标识，来源统计最后统一。重复的ProteomeScout证据数据集说明按其来源ID只保存一次，记录保留关联及出现语义 |
| UniProt复用 | PTM通过source_record_id/source_object_id引用原feature_id；共用feature详情与证据，不再次保存完整feature副本。PTM特有的位点关系与状态保留；膜脂化入口也复用同一feature |

已落地ptm_record、sequence_site、ptm_record_site、ptm_evidence及ptm_evidence_dataset；共享uniprot_sequence_feature与sequence_dataset。原膜feature入口改为普通视图，详情/证据视图组合关联，不保存副本。

## 信息保留清单

所有记录保留：内部record_id、dataset_id、来源条目ID、原始对象ID、项目蛋白关联、topic、原始修饰类型、位置几何、原生位置/残基、证据与映射状态。只有实际目标位置可以从已确认位点关系恢复时才删其重复列；不能丢弃未连接记录的来源坐标。

| 数据集 | 需保留的来源特有信息 |
| --- | --- |
| UniProt | 原feature_id、修饰说明、坐标修饰符、成键/伙伴说明及ECO/文献；从共用feature读取 |
| dbPTM | 来源条目键、修饰类型、来源位置与残基、原21-aa窗口、文献；窗口保留为现有映射的解释依据 |
| ProteomeScout | 来源protein/modification标识、修饰原文、原始证据数据集编号、引用/链接与Current状态；数据集说明不在每次证据出现中复制 |
| GlyGen | 糖基化类型、site_category、原位置/残基、来源有的糖链标识及相关说明、comment、证据数据库及编号/链接；缺失不补造 |
| PTMD2 | PDAs_id、Type、State、Disease、MutationSite、Source、Residue/Position、Is_experimental_verification、Enzyme、Sentence、CellType及PMID；只保留来源事实，不新建突变映射或推断疾病结论 |

来源ID缺失时保留上游快照条目键，不伪造官方编号或链接。无法解析成标准文献ID的引用保留原文。来源给出的链接保留；确定可由编号重建的链接可统一生成。

## 不重复导入

完整蛋白序列/名称、重复基因名称、原始整包、内部路径及调试字段不逐条进入服务记录。source_file/source_row可留在上游，通过dataset与来源记录键回溯；删除前须保证入口可追溯。抽取字段已覆盖详情后，才省略完整payload，不提前删除尚未核对的特殊信息。

本轮不新增isoform映射、PTMD2定位研究、修饰化学名称归一、跨库证据合并、突变轨道或来源汇总统计。Pfam、JSD、UniProt TOPO按[Sequence计划](sequence.md)独立准备，不因未定位PTM阻塞。

蛋白身份歧义的591条记录保留candidate_accessions候选蛋白导航；这不是位点映射，不创建候选site连接。
