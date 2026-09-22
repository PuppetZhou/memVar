# 蛋白概览：内容、来源与膜分类审查

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

日期：2026-09-20。状态：概览小模块和五类膜标签已获用户确认，见[当前方案](../../plan/protein_overview.md)；具体来源判定与字段展示继续审查。本页保留此前来源统计与定义依据，未修改正式数据或生成服务表。目标为膜蛋白突变的“UniProt”，此目标以当前用户要求为准。

## 1. 建议的概览小模块

| 小模块 | 问题与实体 | 建议呈现 | 当前来源与可用性 |
| --- | --- | --- | --- |
| 身份与序列 | 这是哪个蛋白？查看哪条序列？蛋白条目、基因、序列为独立关联对象 | 推荐蛋白名、UniProt accession及链接、主基因名/别名、物种、当前序列ID与长度、isoform入口 | foundation的protein_entry/protein_gene_name/protein_sequence/protein_isoform已在cleaned；protein_gene/gene_ensembl为curated。正式概览仍需在上游确认后组织，不能把cleaned直接称为已发布概览表 |
| 功能简介 | 蛋白主要做什么？一条带出处的功能描述 | UniProt FUNCTION为主要叙述来源，短段落及展开原文；保留适用对象、来源和不确定性 | 本地原始JSON已收集，Function有来源解析/探索产物；正式功能摘要尚未构建 |
| 功能与通路标签 | 执行什么分子功能、参与什么过程或通路？蛋白/isoform—术语/通路关系 | GO MF、BP分别呈现，Reactome为通路，名称可展开来源证据 | Function GO和Reactome已发布；代表标签/通路选择仍需讨论，不按来源数量声称“主要” |
| 细胞与膜定位 | 在哪里发挥作用？带对象与条件的定位断言 | UniProt定位为主，GO CC补充；HPA实验定位按来源展开。质膜/细胞器膜及可能的非膜状态保留 | UniProt SUBCELLULAR LOCATION在raw及解析产物；GO已发布；HPA subcellular_location已有expression curated，统一定位摘要未构建 |
| 膜关联特征与收录依据 | 为什么收录、以何方式与膜关联？来源证据及项目分类分别组织 | 纳入依据、膜关联方式、跨膜区段/数量或脂锚类型、证据来源与方法，链接到site详图 | foundation收录规则、UniProt定位/feature及Site-Region正式表；membrane精确区间已发布，DeepTMHMM2完成但未发布curated |

这些是概览内部小模块，不新增顶层信息板块。概览复用功能和位点层数据，不维护另一套证据。表达、QTL和PPI仍从详细板块进入，避免概览首屏堆积大表。后续可加简洁数据可用性导航，但不把缺记录解释为没有功能、变异或疾病。

GO CC表示细胞组分，也可能是复合物，不全部等同膜定位。UniProt定位、GO CC和HPA可共同服务定位卡片，但来源间一致不自动构成独立实验证据。FUNCTION缺失时显示缺少来源功能说明，GO标签不能自动拼成未经确认的机制性叙述。

## 2. 纳入依据与膜类型是两个问题

当前收集查询为 `proteome:UP000005640 AND reviewed:true AND keyword:KW-0472`，UniProt 2026_03得到7,732个条目；按已确认HGNC范围排除17条后为7,715。不是DeepTMHMM2预测选出的集合，也不代表全体人类膜蛋白已完整收录。

官方KW-0472覆盖膜结合或膜相关蛋白；这支持广义膜相关集合，不要求每个条目都有跨膜区段。[UniProt Membrane关键词定义](https://rest.uniprot.org/keywords/KW-0472.json)。收录规则见[foundation规则](../../../../../../modules/foundation/docs/rules.md)，实际query及版本见根config/sources.yaml。

页面可简洁写为“纳入依据：UniProt reviewed human reference proteome，Membrane注释”，方法详情说明查询与项目HGNC范围。分类另列，不用“因预测为跨膜蛋白而纳入”替代真实来源。

## 3. 本轮实际统计

脚本：[profile_overview.py](scripts/profile_overview.py)。结果：[summary.json](results/summary.json)、[逐蛋白标记](results/protein_annotation_flags.tsv)。从配置读取原始UniProt页目录和当前项目目标表，全量读取当前来源中的comment/feature；输出仅在本research。输入目标、输出accession数与唯一性核对一致。

```bash
python Web/docs/archive/00_initial_preview/research/protein_overview/scripts/profile_overview.py
```

| 来源注释存在性 | 当前项目条目数 |
| --- | ---: |
| 总范围 | 7,715 |
| 有FUNCTION非空文本 | 7,087 |
| 有SUBCELLULAR LOCATION comment | 7,715 |
| 有Transmembrane feature | 5,214 |
| 有Intramembrane feature | 238 |
| 有Lipidation feature | 702 |
| 定位topology明确包含Lipid-anchor（含GPI/GPI-like复合值） | 473 |
| 定位topology明确为Peripheral membrane protein | 1,067 |

以上为accession级“存在该来源注释”计数，允许不同isoform、加工产物和定位上下文并存；未按实验证据限定，不能称为实验确认分类数。473个脂锚条目中17个同时有TM feature。所有分组非互斥，不能直接相加。

没有TM feature的2,501个条目中：456个有显式脂锚topology、1,042个有显式peripheral topology、23个有Intramembrane feature；另13个有单次/多次跨膜topology文字注释而没有TM feature。没有TM feature且没有显式脂锚topology者2,045个，其中仅1,030个明确标注peripheral，另1,015个没有这项明确注释。即便改用任意Lipidation feature作为脂锚代理，剩余1,997个也只有995个明确peripheral，且该代理本身尚未成立。

因此“没有TM feature且没有脂锚 → peripheral”不能由本轮数据直接推出。当前5,214是feature口径，并非所有来源对跨膜身份的最终裁决。个别例子O95197/Reticulon-3有Multi-pass定位注释与Intramembrane feature，却无Transmembrane feature，说明需核对证据而不能从缺feature反推类别。

## 4. 五类标签的依据与已替代候选

用户已确认采用跨膜、脂质锚定、外周膜蛋白、膜内嵌入、膜相关（不明确），暂不采用integral/peripheral简单二分类。原候选及替代原因见[历史记录](../../../../history/20260920_protein_overview.md)。以下保留科学依据，具体判定仍需按对象和来源落实。

1. **跨膜与脂锚分别保留。** 当前来源分别维护这两种拓扑；已确认方案采用对应标签，不再合并为integral。
2. **Lipidation不自动等于膜锚定。** 官方Lipid-anchor定义要求通过脂质/脂肪酸修饰与膜脂双层关联；原生Lipidation是修饰记录，应优先读取明确锚定注释，再审查其他脂化记录的作用。[UniProt Lipid-anchor定义](https://rest.uniprot.org/locations/SL-9901.json)。
3. **膜内嵌入需要保留。** UniProt区分跨膜与位于膜内但未贯穿的INTRAMEM；这部分还可能与peripheral或TM注释重叠，不能一概归integral或peripheral。[UniProt手册](https://web.expasy.org/docs/userman.html)。结构研究也有monotopic膜酶实例，说明“非跨膜”不等于“无膜内嵌入”。[Yeh等原始结构研究，2008](https://pmc.ncbi.nlm.nih.gov/articles/PMC2265192/)。
4. **外周膜关联需正向依据。** UniProt将其定义为与膜表面脂质头基或其他膜蛋白相互作用的膜相关蛋白，并允许浅层插入；来源明确注释可作为分类依据之一，缺少其他类型不能代替它。[Peripheral定义](https://rest.uniprot.org/locations/SL-9903.json)。
5. **证据不足保留“膜相关，方式未明确”。** 不排除这些项目蛋白，不强行补齐二分类。来源冲突或不同isoform/加工形式分开显示，多标签不自动判为错误。[定位对象说明](https://www.uniprot.org/help/subcellular_location)。

已确认标签允许有依据的机制并存，未明确状态不作为外周膜蛋白的替代名称。17个TM与脂锚重叠只是accession层注释并存，须核对具体对象后决定展示，不能任意优先一类。

## 5. 来源采用建议与完成状态

- 身份、序列、名称：foundation来源表及正式基因关系；主基因名来源要明确，UniProt名称不冒充HGNC批准符号。
- 功能简介：UniProt FUNCTION为主，必要时以已发布Rhea/GtoPdb补充明确分子功能；摘要选择和语言处理需后续确认，保留限定语及证据。
- GO：当前GO实体/证据/层级/概览表；MF、BP、CC分开。已有默认标签预览不是主要功能排名，最终展示选择待讨论。
- 通路：Reactome97关联、层级和说明，已有4,921个项目蛋白覆盖；通路成员不代表某组织中通路已激活。
- 定位：UniProt SUBCELLULAR LOCATION为主要结构化来源，GO CC与HPA为带来源补充；不无条件合并成一致定位。
- 膜概览：优先用UniProt定位及原生features建立基线，结合membrane已有序列验证区间作详情；DeepTMHMM2及其他预测独立标明，不能把模型Globular输出解释为非膜相关或外周。不能将不同来源区段直接相加成一个跨膜数。

当前审查转入[身份与序列、功能简介](identity_function.md)，包含字段及文本覆盖统计和待确认展示选择。膜标签词表已确认，来源对象、证据冲突及逐条判定仍待对应专题落实；本页统计不代表已完成正式打标。

本地依据：[foundation表说明](../../../../../../modules/foundation/docs/tables.md)、[GO契约](../../../../../../modules/Function/docs/go_tables.md)、[Function来源审查](../../../../../../modules/Function/docs/source_review.md)、[膜来源与覆盖](../../../../../../modules/membrane/docs/integration_and_coverage.md)、[当前Site-Region结果](../../../../../../modules/Site-Region/docs/result.md)。网络来源访问于2026-09-20；官方API定义与本地2026_03注释统计分开，不以当前API全库统计替代项目分母。
