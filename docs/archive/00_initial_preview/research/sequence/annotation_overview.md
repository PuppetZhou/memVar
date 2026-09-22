# 序列注释：来源、对象与首期轨道建议

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

> 2026-09-21范围更新：本轮仅canonical，突变留到下一板块，来源最后统一统计。下文六轨道/isoform交互为此前讨论，现行范围见[Sequence计划](../../plan/sequence.md)，PTM筛选见[服务方案](../../plan/sequence_ptm.md)。

日期：2026-09-20。序列优先及六组轨道范围已确认，现行规则见[plan](../../plan/sequence.md)；本页维护来源依据与剩余实现建议。读取Site-Region现有契约与结果，没有重新统计全量位点或运行流程。

## 对象先分三类

- site：明确序列的单个位点，例如活性位点、某种修饰或JSD数值。
- region/pair：区段或成键端点，例如domain、膜区段、二硫键。二硫键只连端点，不涂满中间残基。
- substitution/variant：具体ref→alt替换或基因组变异，例如突变效应与ddG。同一位置不同替换的评分不能归为一个固定site属性。

序列视图统一sequence_id、残基和坐标，点击位置后查询这三类相关信息；位置重叠只是共定位，不直接证明突变破坏该功能。

## 当前来源与就绪程度

| 轨道候选 | 来源 | 状态/边界 |
| --- | --- | --- |
| 活性/结合位点 | UniProt Active site、Binding site、Site | 已发布功能位点17,020条来源feature；包括14,569条Binding site，空description不等于无配体 |
| PTM、糖基化、脂化、成键 | UniProt、dbPTM、ProteomeScout、GlyGen | 已有来源记录与site索引；同一位点多来源保留证据，不当作多次独立实验 |
| PTM相关疾病/突变 | PTMD2及其他来源明确关系 | PTMD2当前只有候选关联、没有正式site连接；不能直接画成已验证WT修饰或已证实致病突变 |
| Domain及其他区段 | UniProt Domain/Motif/Repeat/Region等 | 已有正式feature；无序、repeat等不全部改称domain |
| Pfam | 本地旧命中及输入/词典 | 23,662条旧命中已收集，尚无新版正式发布；当前序列关联、补算与轨道边界需落实 |
| 加工/转运 | UniProt Signal、Transit peptide、Chain、Peptide、Propeptide等 | 已在正式region组，保留加工对象和不确定边界 |
| 保守性 | 当前自建JSD流程，UniRef90 2026_02 | 已发布4,364,831残基，覆盖7,715个canonical；不是所有isoform都有 |
| 膜拓扑/接触 | 复用膜方案中的来源及映射 | 默认单一来源拓扑可切换；接触映射就绪后联动，未映射记录不强画 |
| 二级结构/可及性 | UniProt Helix/Beta strand/Turn；历史rSASA | UniProt二级结构97,399条已发布，但不等于当前结构DSSP；rSASA仅旧输入，尚待新版整理 |
| 突变及替换评分 | variant与ddG | 后续叠加，精确匹配当前序列后绘制；不同ref/alt评分不平均为site值 |

UniProt四组共248,721条feature，region包含domain、加工与拓扑，并不表示有91,957个domain。PTM索引241,192个唯一序列位置、673,513条来源记录；包括153,279条未建site连接记录。PTMD2全部103,800条在该未连接集合中。它们仍可按蛋白查看，不能因有数字位置直接投影。

数字引用[Site-Region结果](../../../../../../modules/Site-Region/docs/result.md)、[UniProt表契约](../../../../../../modules/Site-Region/docs/tables.md)、[PTM契约](../../../../../../modules/Site-Region/docs/ptm_tables.md)，不是新统计。

## PTM与突变应如何同时呈现

用户提及“PTM 突变”，这里同时保留PTM位点、自然变异和有明确证据的突变影响PTM三种需求，不直接合并。建议PTM与突变分轨，点位详情再关联：

1. 该残基有什么来源修饰注释。
2. 哪些具体替换位于同一残基。
3. 是否存在来源明确描述该替换导致修饰丢失、获得或变化的证据。

第三项没有证据时只显示重叠，不写“破坏PTM”。周边motif影响与同位点重叠不同，需要明确来源或独立预测。来源中人为Mutagenesis与天然变异分开。PTMD2目前的序列验证缺口不能用残基碰巧一致绕过。

## Domain如何组织

用户已确认Domains组中UniProt与Pfam同轨道组展示，替代此前分来源主轨道的候选建议。来源记录和边界仍独立保留，重叠可在同组堆叠；不按同名或重叠区间合并记录。Pfam alignment/envelope/model坐标不同，展示边界仍需确认。InterPro若后续需要，其身份xref不是现成区间命中，本轮不冒称已具备正式InterPro轨道。

## JSD是否适合展示

适合，作为独立连续数值轨道或热条，供观察不同位置的保守性背景。悬停显示JSD、残基、MSA非gap比例occupancy与序列深度；方法/来源版本放详情。不直接标成致病概率或ConSurf等级。

当前实现是比对列氨基酸分布与固定背景的Jensen–Shannon divergence，残基组成会影响值。正式数据已有no_search_hits、query_only、nonstandard_residue等状态，缺乏同源支持不能解释为可靠的高/低保守；建议显著提示这些状态且保留原值，不用0代替缺失。历史High/Medium/Low是启发式质量标签，不是保守程度。

只有canonical当前有完整正式覆盖，其他isoform显示未计算，不按基因相同继承。沿用现行JSD，不增加新阈值或重跑；方法边界见[JSD专题](../../../../../../modules/Site-Region/docs/conservation_review.md)。

## 当前布局与剩余实现建议

用户最新确认顺序：PTM → Domains（含二级结构、Pfam和UniProt区段）→ Membrane TOPO → Function site → JSD → 突变。PTM五来源完整保留、不跨库去重，PTMD2显示疾病详情，准确site连接仍须解决其原生序列核对缺口。

当前跨膜TOPO集中在Membrane组，不在Domains重复铺设。Domains是展示分类，不改变二级结构、motif、repeat等原始类型。膜接触仍保留按需叠加入口。

字段分层、去除重复加载及待处理清单见[字段保留与整合](field_retention.md)。此前二级结构暂缓和分离Pfam主轨道的候选已被最新决定替代。服务表与记录粒度不随页面六类机械拆成六张宽表。
