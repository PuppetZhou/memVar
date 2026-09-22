# 第二部分：序列与位点注释

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

更新：2026-09-21。Sequence本轮仅考虑canonical，取消isoform切换；突变留到下一板块，来源信息最后统一统计。本轮已按后续授权构建并导入PostgreSQL，版本`20260921_sequence_v1`；[表格及验证记录](../../../record/00_initial_preview/20260921_sequence_v1.md)。

## 已确认方向

- 第二部分以具体蛋白序列为基础，开展site/region注释设计。
- 仅使用protein.default_sequence_id指定的canonical；已有映射到其他isoform的记录不纳入本板块，不改挂canonical；膜区段及接触注释与膜信息视图共享，同源轨道可切换，具体规则见[蛋白概览](protein_overview.md)。
- 来源依据和当前交付状态见[序列注释研究](../research/sequence/annotation_overview.md)。轨道范围如下已确认，服务表契约见版本记录，页面几何表现后续实现。

## 轨道组织

按用户文字列举顺序，序列编号下方组织为：

1. PTM。
2. Domains（包括UniProt区段、Pfam及二级结构）。
3. Membrane（专门的跨膜TOPO）。
4. Function site（活性与功能位点）。
5. JSD。

参考用户提供的Variant Density and Protein Features截图采用共同序列坐标与可点击标记，但不照搬截图中突变在最上方的排序、示例数量或分类；二级结构按本次确认归入Domains展示组，不与PTM合轨。

## PTM：多来源完整记录与疾病详情

- 纳入UniProt、dbPTM、ProteomeScout、GlyGen、PTMD2。
- 建立来源记录—明确序列位点—证据/详情关联；暂不做跨来源记录去重或科学合并。同一site多个数据库、同一数据库多条记录均保留，点击后按来源展开/折叠。
- 一个位置可用聚合标记表达多记录，标记必须能访问全部来源记录。单个位点数量与记录数量分别标注；显示聚合不删除记录。
- PTMD2必须保留疾病名称、来源疾病/突变描述、State和引用等可用信息。修饰获得/丢失、突变关联与WT已有修饰分开显示，不将来源描述自动转换为致病结论。
- PTMD2目前没有已验证的正式site连接；后续完成序列和坐标核对再上轨。待定位记录继续在蛋白级详情列示，不丢弃也不强行画到canonical。具体替换/疾病ID关系按对应模块契约建立，不仅凭相同位置生成关系。
- 普通PTM、糖基化、成键等原始类型保留；成键标记端点而不填满两端之间区间。

## Domains：简化展示分类，保留科学类型

- Pfam和UniProt注释在同一轨道组中展示，不按数据库拆成两条主轨道。保留原始类型、名称、边界、来源ID/版本及证据。
- 重叠注释可在组内堆叠/展开，不能用一个合并区间替代不同来源注释。Domain、Motif、Repeat、Region、二级结构等保留原始类型；Domains是页面分组名称，不意味着所有内容科学上都属于结构域。跨膜TOPO移到Membrane组，不在Domains重复铺设。
- UniProt Helix、Beta strand、Turn归入本组，可用组内子行/颜色区分；不作为当前所选结构的重新计算结果。加工/转运区段保留原始类型，先在Domains的其他区段详情访问，不误标为domain。
- Pfam当前canonical整理及增量扫描已发布并入库；alignment/envelope/HMM坐标均保留，主显示边界仍待确定，不阻塞入库。

## JSD、膜注释与功能位点

- JSD独立列举/成轨，保留质量及同源支持信息；不作为致病概率。当前仅canonical已完整计算，不能自动投影到其他isoform。
- Membrane专门展示跨膜TOPO，复用已确认膜方案中的原记录与映射；默认同一来源，可切换。此前已确认的膜接触信息仍可在sequence按需叠加/点击查看，不因本轮范围精简而删除，不混入拓扑区段计数。
- 活性、结合及其他功能位点独立成组，保留配体及作用原文、来源和证据。

## 关联与本轮边界

- 五组共用canonical sequence_id与坐标，不提供isoform切换；foundation已有完整序列与声明表仍保留，不因页面范围缩小而删库。
- PTM复用现有record_site/site_index映射，以site.sequence_id = protein.default_sequence_id筛选。不重新推断序列关系，不将非canonical位置换名挂接。
- 尚未定位且只有蛋白身份关联的记录保留为来源详情，明确未定位；不声称属于canonical位点。已明确属于其他isoform的记录不纳入本板块。
- 突变轨道、变异表接入、替换评分及密度统计移到下一板块。本轮保留PTMD2来源自带MutationSite等原文，但不解析成新的变异关系。
- 来源统计最后统一开展；现在仍保留dataset_id、来源条目编号和证据关联，避免丢失出处。
- PTM具体筛选与字段见[PTM服务方案](sequence_ptm.md)。

## 字段与整合实施原则

五类是展示分组，不是一来源一表或一轨道一张宽表。原始科学类型、证据、对象和位置粒度保留；默认展示、详情、后台关联分别控制。PTM不跨来源去重，domain重叠不合并，膜区段不跨来源求共识。

字段精简与整合已纳入[字段方案](sequence_fields.md)；已完成字段投影与入库，Pfam主显示边界及后续页面计数不改变来源数据。

构建和PostgreSQL验证已完成；本轮未实现API或页面。

