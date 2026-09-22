# 网站 V2：汇总、筛选与精确详情 API

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../README.md)，本文不作为当前执行指令。

2026-09-21；本页维护本轮新增后端契约与定向验证。V1 详情、科学显示边界与 ddG 单位证据见[初版记录](../../../record/00_initial_preview/20260921_api_evidence_v1.md)。页面设计与本轮授权由[网站 V2 研究](website_v2)和现行计划维护。

## 通用约定

- 仅查询已发布 PostgreSQL；本轮没有重新导入、映射、改变正式数据或新增科学阈值。
- 以下 protein 路由前缀均为 `/api/proteins/{accession}`。未知蛋白返回 404。
- 列表继续返回 `{items, next_cursor, filters}`。`limit` 最大 100；cursor 与蛋白及全部筛选绑定，切换条件须清空 cursor。
- 汇总覆盖当前筛选的完整查询结果，不从列表页推算。其 `groups` 各项为 `{dimension,key,label,count,unit,filter,...}`；`filter` 给出可传回列表的条件。`totals` 表示相应单位的全查询汇总。
- 不同 dimension、来源、后果与来源分类可能重叠，不相加当作独立对象总数。计数单位与表达值单位分别维护。
- API 使用现有只读连接池与 15 秒 statement timeout。汇总按 accession/筛选组合缓存小响应（每类最多 96 个，较大的 Expression context 索引仅保留 8 个 dataset），发布新数据后重启服务清缓存。未增加另一套服务/数据库环境。

## Variant

### 查询参数

`/variants` 与 `/variants/summary` 共用以下数据筛选；只有列表接受 `limit/cursor/predictors`。

| 参数 | 含义 |
| --- | --- |
| `source` | ClinVar、COSMIC、gnomAD、dbSNP；空值不限来源 |
| `consequence` | 正式所选 VEP 后果中的单项；按 `&` 拆分后精确匹配 |
| `position` | GRCh38 基因组位置，不能当作蛋白位置 |
| `search` | variant ID、HGVSp、HGVSc、所选转录本、rsID 的文本；支持 R2L、Arg2Leu、R2= 或单独蛋白位置数字。这些蛋白描述属于所选转录本 |
| `canonical_start/end` | 1-based inclusive 当前 canonical 范围；必须有正式 annotation→ddG→sequence 关系。未验证 canonical 的变异仍留在无此筛选的目录中 |
| `clinvar` | 来源原 `ClinicalSignificance` 文本精确匹配，不重分类 |
| `frequency` | overall、afr、amr、asj、eas、fin、mid、nfe、remaining、sas、grpmax；默认 overall |
| `af_min/max` | 所选 AF 的数值边界，范围 0–1；不代表项目新增致病阈值 |
| `af_status` | available、missing、zero、positive、invalid；空值不限 |
| `predictors` | 逗号分隔正式字典字段，最多 12 个；默认 CADD_phred,REVEL_score,SIFT_score；`none` 不读取评分 |
| `transcript_status` | all（默认）、canonical、noncanonical、unknown；仅指所选 Ensembl/VEP 转录本标志，细则见本页新增契约 |

### 汇总响应

`GET /variants/summary`：

```text
totals:
  unique_variants, annotation_rows
  frequency_available, frequency_missing, frequency_invalid
  frequency_zero, frequency_positive
  af_min, af_max, af_quartiles: [q25, median, q75] | null
  canonical_mapped_variants, canonical_unmapped_variants
  canonical_variant_position_associations
groups:
  dimension: consequence | source | clinvar | frequency
  count: distinct variant_id 数；unit: unique_variants
canonical_sites / positions（同一数据的两个键）:
  [{position, count, variant_count, substitution_count, unit:'unique_variants_at_position',
    filter: {canonical_start, canonical_end},
    clinical_counts:{pathogenic,uncertain,benign,conflicting,other,unclassified}}]
clinical_groups: [{key,label,count,unit:'unique_variants'}]
clinical_grouping: 原来源分类显示归组说明
canonical_counting_note: 单位点去重与跨位点累加的计数范围说明
sequence_id, sequence_length
mapping_scope: verified_canonical_ddg_links
frequency: {population,label,source,distribution}
filters: {sources,consequences,predictors,frequency_types}
notes
```

`annotation_rows` 是正式所选转录本后果行数，可能大于 unique_variants。位置 `count` 等于该位点的 unique genomic variant 数；`substitution_count` 是该位点已有关系中的不同 ref/alt 氨基酸组合数，不是预测全部 19 种替换的数目。

临床原分类先通过 distinct variant ID 集合读取，再对每个变异只归桶一次；多个 annotation 不会重复全目录的 clinical_groups。每个位点的 variant IDs 同样 DISTINCT，去掉重复 annotation/prediction 关系。`canonical_mapped_variants` 是跨全部位置去重的变异数；`canonical_variant_position_associations` 是逐位点计数之和。多位点 bin 累加表示变异—位点关联数，不能在未经核实的情况下保证等于 bin 内去重 genomic variant 数；未来同一变异如有多个可靠位置，二者可以不同。

canonical 映射严格读取已有 `variant_ddg_link` 与 `ddg_prediction`，要求当前默认 sequence_id。该图只显示服务中已验证关系的覆盖子集；`canonical_unmapped_variants` 表示缺少这条当前关系，不能描述为“生物学上无法映射”。基因、MANE 或 HGVSp 位点本身都不作为 canonical 证明。前端可用 positions 按整数位置准确聚合计数，不需要按采样比例估计。

频率来源为本地 gnomAD exomes 4.1。available 仅统计有效 0–1 值；0 保留为已观察数值；missing 是所选群体 AF 缺失；invalid 单独保留。四分位数对每个 unique variant 的所选 AF 计算；不跨位点、群体加和，不混用 COSMIC 样本计数。

### ClinVar 原分类的互斥显示计数

2026-09-21 用户新增授权：为序列及目录的多位点 bin 堆叠图整理原分类计数。这里只读取原 `ClinicalSignificance`，不计算致病分、不覆盖原断言、不选择“最高”分类，也不把 Oncogenicity 或 SomaticClinicalImpact 混入。

每个 unique genomic variant 收集其全部 ClinVar 原记录标签；大小写、下划线和空白仅用于匹配。原组合标签按 `/`、`;`、`,` 拆分，识别 Pathogenic/Likely pathogenic、Benign/Likely benign、Uncertain significance 三大类：

1. 任一原标签含 conflict，或一个变异在原记录中同时出现上述至少两大类 → `conflicting`。
2. 只有一大类 → `pathogenic`、`benign` 或 `uncertain`。附带 drug response 等其他标签不会被提升为新判定，原详情继续保留。
3. 其余有实质原标签（例如 drug response）→ `other`。
4. 无来源分类，或仅空值、`-`、`.`、NA、not provided、not specified、none → `unclassified`。

六桶互斥，`clinical_groups` 和等于当前查询 unique_variants；每个位点 `clinical_counts` 和等于 variant_count。图表可逐桶累计多个位点作为 bin；仍须标注这是来源分类的显示归组，而非临床重新判定。未知文本不凭词语片段归为致病；例如“not pathogenic”不会误归 pathogenic。原标签列表与原标签精确筛选均保留，source grouping 不写入正式科学产物。

### 列表与详情增量

列表原字段保留，新增：

- `ref_aa / aa_position / alt_aa / protein_change / aa_scope='selected_transcript'`：解析原 HGVSp 的单一替换/同义形式；复杂形式不强行拆分，继续显示原文本。
- `canonical_positions:[{sequence_id,position,ref_aa,alt_aa}]`：本条所选 annotation/gene 的明确现有关系。
- `clinvar:[{classification,review_status,origin,oncogenicity,somatic_clinical_impact,source_id}]`；`cosmic:{present,source_ids}`。均为原来源信息，不合并成统一致病分。
- `frequency:{af,population,label,status,record_status,source}`；所选群体值缺失时明确 `no_value_for_population`，没有本地行时为 `no_local_frequency_record`。
- `predictions` 按请求字段顺序输出，包含 field/source/scope/tool/group/value/status，以及 `source_pred / source_pred_status / raw_pred_field`。

`/api/variants/{variant_id}?accession=` 的 `prediction_groups` 同样补充 source_pred。仅当原 dbNSFP `_pred` 与正式选取的数值及来源上下文一致时提供：variant 标量数值须匹配；转录本值须通过已保存的 context_matched 关系、dbNSFP 行和同一 transcript/protein/aapos 数组位置。来源类别互相冲突时保留 `conflicting_source_categories`，不挑一项。只核实可明确关联的 `_score`→`_pred` 字段，没有原分类时仅显示数值；不凭连续值推断分类，也不跨模型解释 D/T/B/P 等缩写。

详情仍独立组织来源注释、频率、预测器与 canonical ddG。ddG 只对已核实 ThermoMPNN 默认 checkpoint 返回 `unit=kcal/mol` 及负值稳定化、正值去稳定化的 `effect_convention`；科学值未改变。没有明确原量尺上界的预测器不增加虚构 `range_max`。

## Expression、QTL、PPI、Disease

| 汇总端点 | 参数 | groups dimension / 计数对象 |
| --- | --- | --- |
| `/expression/summary` | source、category（默认 all）、dataset | category/source/dataset；source_observation_records |
| `/qtl/summary` | source、tissue、qtl_type | source/type/tissue；source_association_records |
| `/ppi/summary` | source、interaction_type | source/type；source_interaction_records |
| `/diseases/summary` | source | source；source_evidence_records，另有原 disease ID 数 |

Expression category 固定返回 normal/cancer/cell_line/single_cell 四类（无记录时 count=0）；PPI 固定 BioGRID/IntAct，QTL 固定 GTEx/eQTLGen/QTLbase，Disease 固定 ClinGen/GenCC/HPO/OMIM。0 来自后端当前查询，前端无需猜测缺失组的含义。

Expression：

- dataset group 带 `measurement / measurement_unit / contexts / context_unit / available_values`；`filter` 包含 source/category/dataset，可精确打开该测量的列表。
- 列表新增 `dataset / context_key`，category 新增 all；默认 normal 保留。`filters.datasets` 为 `{value,label}`。source 或 category 改变后清除旧 dataset/context_key；dataset 改变后清除 context_key。context_key 同时进入 cursor 签名。
- `contexts` 在每个 dataset 内按原 context ID 去重；category/source 汇总计算 dataset–context 对，不能称为跨来源统一组织数。
- `available_values` 按原来源缺失标记核对，真实 0 可用。RNA、IHC、MS/CPTAC 等单位不合并；GTEx 仅已选官方基因组织 median TPM，不扩展为个体矩阵。

### Expression 组织／细胞 context 总览

`GET /expression/contexts?dataset=明确数据集名&query=&limit=24&offset=0`。必须选择一个已提供的 dataset；不在此请求中跨全部数据集扫描。

```text
{dataset, source, category, measurement, measurement_unit,
 totals: {records, contexts, available_values},
 groups: [{dimension:'context', key, label, count,
           unit:'source_observation_records', available_values,
           measurement, measurement_unit, context_details,
           filter:{source,category,dataset,context_key}}],
 filtered_contexts, has_more, limit, offset, scope, notes}
```

GTEx key 使用原 sample_id；其余使用原 context_id 的字符串。label 展示该 context 原维度内容；context_details 保留原维度字段。一个癌症样本 context 不重命名为一个独立组织，也不按同名标签跨数据集合并。count 统计所选蛋白关联基因在该原 context 的来源观测行，available_values 按与列表一致的缺失标记核对。

query 大小写不敏感匹配原 label；groups 按 offset/limit 分页（默认100、最大200）。totals 始终为完整所选 dataset，filtered_contexts 单独表示名称搜索后匹配的 context 数；不把当前页条数当总数。完整 context 索引经一次当前蛋白＋dataset 定向查询后短缓存，响应仅发送当前页。

点击组将 filter 原样传给 `/expression`，精确匹配 GTEx sample_id 或其他 context_id；所有参数绑定。context_key 必须搭配合法 dataset，非 GTEx ID 必须为原整数格式。切换 context 时清 cursor，不接受旧条件 cursor。

QTL：

- 从正式 `qtl_context_count` 查询当前蛋白关联基因的各 dataset 计数，再读取来源/组织/type 元信息；不在请求时扫描 2.51 亿关联行。
- 只计 gtex_qtl_pair/eqtlgen_cis/qtlbase_association；GTEx phenotype summary 不重复计入。
- type/tissue group 带 source，filter 一起传 source；同名跨来源组织不自动等价。全来源概览之后选择来源才加载列表。
- 不新增显著性筛选，不做 variant mapping；slope、Zscore、原 P 值文本和组装沿用 V1。

PPI：

- 先按蛋白已建立关系取 distinct record_id，再读 full 原始集合，context membership 不重复复制记录。type 标签与列表完全共用，包含提供者前缀。
- `totals` 包含 records、negative_records、sources、interaction_types。记录数不是独立伙伴对数、独立确认数或相互作用强度。
- 界面预测正式产物已发布，但尚未接入服务库；summary 注明该状态，不声明已展示预测。

Disease：

- `totals` 包含 records/evidence_records（distinct evidence_id）、diseases（distinct 原 disease_id）、sources。source group 同时含 `diseases`。
- `gene_dosage` 独立返回与 V1 列表相同的 gene_id/gene_symbol/haploinsufficiency/triplosensitivity/report_url；仅有剂量信息而无疾病关系时仍有入口。
- 不通过名称或一般交叉引用把不同词表疾病合并；HPO 原 qualifier/证据/频率的按需分页详情接口保持。

### PTMD2 疾病背景独立入口

2026-09-21 按用户要求迁入 Disease 板块。`/diseases/summary.ptmd` 是独立 totals 对象：`{records,protein_associated,candidate_protein_association,disease_labels}`，不计入 ClinGen/GenCC/HPO/OMIM 的证据或疾病总数。

- `GET /diseases/ptmd/summary`：`{source:'PTMD2',totals,groups,scope,notes}`。groups 为 disease/type 两个维度，count 单位 `source_ptm_disease_records`；疾病名称保持原 Disease 文本，不映为标准疾病 ID。filter 分别含 disease 或 source_type。
- `GET /diseases/ptmd?disease=&source_type=&limit=20&cursor=`：`{items,next_cursor,filters:{diseases:string[],source_types:string[]},note}`，最大100。筛选绑定原文本，cursor 与 accession/disease/source_type 绑定。
- items 含 record_id/source_id/source/source_type/description、disease/state/mutation_site/cell_type/enzyme/source_position、source_accession/source_sequence_id/source_start/source_end/source_residue、identity_status/mapping_status/evidence_status/association_status/candidate_accessions，以及 fields/evidence。
- fields 保留 Disease/State/MutationSite/CellType/Enzyme/Position/Source/Is_experimental_verification/Gene name 中已有值；evidence 保留 namespace/identifier/url/kind/is_current。State U/N 等代码不猜测语义。

关联范围直接复用正式 PTMD2 record：accession 精确关联，或 accession 缺失但 candidate_accessions 明确包含当前蛋白。后者单独标 candidate_protein_association，不升级为已确认身份。没有要求已匹配 sequence_site，因而未定位记录仍可阅读。source_position 和 MutationSite 只是原来源描述；不投影到 canonical 序列、不挂接项目 genomic variant，也不重新构建 PTMD2 科学数据。

最终展示迁移审查已在 Sequence 的 unmapped 列表（含默认来源选项）、PTM 轨道、单个位点详情和精确 PTM feature 请求中显式排除 PTMD2。只调整 Web 查询，原记录与关系底表保持原样，Disease 路由不受此过滤影响。

## 精确 feature 详情

`GET /sequence/feature?source=&feature_id=&record_ids=&limit=25&offset=0`

```text
{source, feature: object|null, records: [], evidence: [], has_more,
 sequence_id, coordinate_system, ...PTM分页信息}
```

非 PTM 单个 feature 放在 `feature`，`records=[]`；PTM 使用 `feature=null` 和 `records`，两者互斥，避免重复渲染。

| source | 请求身份 | 返回主要注释 |
| --- | --- | --- |
| UniProt | 轨道原 feature_id | 原类型/说明/来源序列/位置修饰/映射状态、details 与 evidence |
| Pfam | 原 hit_id | family/clan、alignment/envelope/HMM 边界、i/c E-value、score/bias/accuracy、Pfam 链接 |
| DeepTMHMM2 | segment_order 数字字符串 | 本段 start/end/name、原预测/映射状态、protein_type、膜类型与概率 |
| Topology 或具体 dataset 名如 HTP | 原 feature_id | 原方法/角色/类型、来源坐标与目标坐标、chain/coordinate_basis、raw attributes |
| PTM | record_ids 为点击 marker 的原 record_id 逗号列表；聚合 feature_id 可同时传入 | 仅这些记录且必须确实映射当前 sequence；原注释/来源坐标/状态、evidence、映射端点位置与 endpoint_role |

PTM 一次最多 1,000 个明确记录 ID，limit 最大 100，has_more/offset 支持续页；不会把所点 feature 换成整个残基的混合注释。跨蛋白或不存在的记录不返回。每项 `fields` 给出常用可直接展开的标量；原详细对象另保留为结构化内容，避免丢失来源注释。

## 定向验证与已知边界

使用现有 Python、真实 PostgreSQL 与 FastAPI TestClient；仅本轮修改相关的小查询，没有重建/全量 QC。下列耗时是本地单次观察，不能当作负载承诺。

| 核对 | 结果 |
| --- | --- |
| P00533 variant summary | unique_variants=4096，annotation_rows=4096，AF 可用2168/缺失1928，零162；已验证 canonical 关系2773个变异，1120个位点；约0.50秒 |
| canonical 范围2–2 | summary unique=3，与列表3条一致 |
| R2L 搜索、详情与零值 | 找到 GRCh38:7:55019282:G:T；原 AF=0.0，SIFT `_pred=D`，ClinVar 原分类/review 可读；详情61评分分组通过 |
| 同义 AA 搜索与筛选 | R2= 返回3条；ClinVar 原分类+canonical 范围组合通过 |
| ClinVar 显示归组 | P00533 全目录 pathogenic29/uncertain1707/benign974/conflicting217/other10/unclassified1159，总4096；canonical对应16/1666/46/178/10/857，总2773；每个位点六桶和=variant_count，位置2为3个uncertain |
| Expression summary | P00533 11368记录/14 dataset；rna_tissue_hpa 单 dataset 为40记录、40 context；精确列表首行为 adipose tissue，25.9 nTPM；下一页 cursor 有效；汇总约0.35秒 |
| Expression contexts | P00533 GTEx68、HPA组织40、HPA cell type154、癌症RNA样本8384个原context；各首context的列表计数/原key/单位一致；名称搜索保留全dataset totals；癌症context查询约0.065秒且仅返回当前页 |
| context参数及分页隔离 | 缺dataset、伪造整数条件、超出bigint的ID均422；跨context复用旧cursor为400 |
| QTL summary与组织筛选 | P00533 30659原关联记录/281 dataset；QTLbase Stem cell-iPSC 分组14122，可打开同组织列表；汇总约0.02秒 |
| PPI summary | P00533 7523来源记录；BioGRID筛选5076，IntAct卡明确0；约0.26秒 |
| Disease summary | P00533 17证据/6原 disease ID；OMIM筛选4条，其他来源卡0；gene_dosage仍单独返回1条；约0.02秒 |
| PTMD2 Disease | P00533 463原记录/59疾病标签，P00813 73/17；均为原蛋白关联，分别保留映射状态；两页无重复，P00813 Immunodeficiency 筛选26条与summary26一致；P00533 summary约0.008秒 |
| 最终计数审查 | P00533/P13569/P08183 定向查询 mapped distinct variant 与 variant-position association 数分别同为2773/3827/1968；实现仍明确支持二者不同，不把此小样例外推全项目 |
| PTMD2 状态可达与迁移 | P00533 Palmitoylation 的3条记录分别为coordinate_missing_or_invalid、residue_only_unverified_sequence、residue_mismatch_or_sequence_unavailable，均由Disease接口返回；Sequence默认/指定PTMD2列表无PTMD2，PTMD2 feature请求404，Disease记录仍463 |
| PTMD2 查询计划 | EXPLAIN显示accession B-tree与candidate_accessions部分GIN经BitmapOr定位后排序，未先扫描完整PTM表；无需新建索引或改动科学数据 |
| 精确feature | P00533 UniProt/PTM/Pfam/DeepTMHMM2/HTP 各代表请求HTTP200，注释/边界/证据保留 |

新代码入口：[variant_support.py](../../../../src/api/variant_support.py)、[variant_summary.py](../../../../src/api/variant_summary.py)、[evidence_summaries.py](../../../../src/api/evidence_summaries.py)、[feature_detail.py](../../../../src/api/feature_detail.py)、[disease_ptmd.py](../../../../src/api/disease_ptmd.py)，既有列表增量位于 [evidence.py](../../../../src/api/evidence.py) 与 [evidence_context.py](../../../../src/api/evidence_context.py)。

当前限制：canonical 图仅已有可靠关系的子集；原分类的工具缩写不新建统一字典；QTL 位点映射、PPI界面预测入库及完整表达矩阵不属于本轮；已有来源详情上限见V1记录。接口200不代替浏览器渲染验收。服务须由根任务统一重启后才能在8000看到新增路由。

## 2026-09-21 后续：转录本筛选、评分覆盖和 Overview 完整计数

本轮仅修改 Variant 与 Overview API，不改动其他任务维护的 Sequence/Structure 接口，也未重启服务。

### VEP canonical 转录本筛选的证据与边界

正式规则仍为[variant/rules.md](../../../../../modules/variant/docs/rules.md#vep频率与-mane)：固定 MANE1.5 Select 优先；只有该基因没有 Select 时，才选择 Ensembl116 canonical。服务目录保存的是这些**已选代表后果**，不是所有 transcript/isoform 后果。selection_method 是选择依据，不能代替 VEP CANONICAL 的实际状态。

项目[annotate_vep.py](../../../../../modules/variant/scripts/annotate_vep.py)明确启用 `--canonical`，并把 VCF 字段空串保存为 null；[build_views.py](../../../../../modules/variant/scripts/build_views.py)只从 Transcript 后果选取与正式 ENST/参考对应的记录。实际使用的 VEP116 `OutputFactory.pm:1570` 仅在 transcript `is_canonical` 为真时设置 `CANONICAL='YES'`，否则不输出该 flag。对应官方定义见 [VEP CANONICAL 字段](https://jun2026.archive.ensembl.org/info/docs/tools/vep/vep_formats.html)及 [VEP --canonical 选项](https://jun2026.archive.ensembl.org/info/docs/tools/vep/script/vep_options.html)。因此这里的空 flag 与普通“来源未启用该字段”的缺失不同；该解释仅适用于已核实启用此选项的当前快照。

`/variants` 和 `/variants/summary` 新增同一参数 `transcript_status`：

| 值 | 当前快照中的解释 |
| --- | --- |
| all | 默认，不以转录本 canonical 标志限制 |
| canonical | Feature_type=Transcript、有效 ENST，原 CANONICAL=YES |
| noncanonical | Feature_type=Transcript、有效 ENST，原 flag 为 null/空串；显示文字明确为 VEP 未标记 canonical |
| unknown | 非 Transcript、缺少/无效 ENST，或未识别的原 CANONICAL 值；不推断 canonical 状态 |

列表与 detail.consequences 新增 `canonical_raw / feature_type / transcript_status`。列表保留 variant_id/chromosome/position/ref/alt、完整原 HGVSc/HGVSp，并明确 `assembly='GRCh38'`。原 CANONICAL null 不改写成伪造来源 NO；只在独立展示状态中解释。

summary 新增：

```text
transcript_groups: [
  {key:'canonical'|'noncanonical'|'unknown',label,count,
   annotation_rows,unit:'unique_variants',filter:{transcript_status}}
]
transcript_scope: 代表后果范围及与UniProt映射分离的说明
filters.transcript_statuses: [{value,label}]  # 包含all和三种状态
```

三个组固定返回，0 不省略。count 是当前完整筛选内不同 variant ID，annotation_rows 是后果行数；如一个变异具有不同基因的多个代表后果，可能进入不同状态组，不能假定三组 count 总和永远等于独立变异总数。筛选也写入 cursor 签名，跨条件复用 cursor 返回400。

**UniProt canonical 映射另行维护**：canonical_positions、canonical_start/end、verified ddG关系和绘图覆盖均不参与 transcript_status。没有ddG关系不能据此被归为 noncanonical；当前 noncanonical 查询无记录也不代表该蛋白在生物学上没有其他转录本。

### 预测器分组简介与完整查询覆盖

`/variants/summary.predictor_summary`：

```text
{
 field_count, tool_label_count, source_count,
 groups:[{name,description,field_count,tool_label_count,tool_labels,
          fields:[{field,source,scope,tool,group,label?,
                   covered_variants,covered_annotations}]}],
 coverage_scope, tool_count_note
}
```

当前为 61 个数值字段、43 种不同来源工具标签、2 个来源（dbNSFP、AlphaGenome）。同一工具的不同量尺/输出字段不冒称不同方法；AlphaGenome 的3项字段现在共享 tool=AlphaGenome，由label区分输出。43是字典中不同工具标签数，仍不等于43个独立方法或独立证据，相关模型/版本与同一方法家族不进行网站自创合并。

六组分别提供简短含义说明，不构造统一致病性或新阈值。covered_variants 是当前完整查询内至少有该字段有限数值的 distinct genomic variants；转录本字段另给 covered_annotations，variant字段此项为null。0为有效数值，NULL/NaN/Infinity不算覆盖。覆盖统计只增加**一次按当前蛋白及筛选条件的宽聚合查询**，不是61次查询，也不重扫项目全库。此值说明可用字段，不把来源状态改写为已获临床确认。

### GO 分类预览与原注释

`GET /overview/go/summary`：

```text
{
 totals:{annotation_count,term_count,negative_annotation_count,no_data_annotation_count},
 aspects:[{aspect:'F'|'P'|'C',annotation_count,term_count,
           negative_annotation_count,no_data_annotation_count}],
 categories:[{category_id,name,namespace,url,annotation_count,term_count,
              contexts:[{subject_id,form_id,relation,extension}]}],
 scope,notes
}
```

totals/aspects 取当前蛋白完整原 GO 关联；annotation_count 为 distinct annotation_id，不是独立实验数；term_count 为 distinct 非空保存的 go_id，保留来源解析/过时状态，不把所有原注释当成正向功能。总 term_count 独立去重，不用 MF/BP/CC 的小计相加替代总查询。

categories 直接读取已发布 `web.protein_go_slim`，沿用 [Function/generic GO slim 规则](../../../../../modules/Function/docs/go_slim.md)：既有 is_a+part_of 分类桥，排除NOT、ND、根术语、obsolete、未解析及仅父对象背景关联；不新增映射或GO科学网络。类别可重叠，category计数不加到直接注释；声明 isoform 的 subject/form/relation/extension 按原上下文保留，不把聚合类别改称 canonical 专属功能。

`GET /overview/go?aspect=&slim_id=&limit=&offset=` 新增 slim_id 参数，通过已发布桥按原 annotation_id 精确过滤；返回 `total` 和 `count_unit='source_annotation_records'`。无slim_id时原完整列表继续包含NOT/ND等状态；有slim_id时返回支持该正向类别的原注释。原 `/overview.go` 首屏也补完整 total，`overview.go_slim`补同样的 annotation_count/term_count。

### Reactome 完整计数与主题筛选

本轮用户明确要求恢复 Overview 图的完整计数，替代早期“计数暂缓”的前端限制；仅统计既有来源关联，不采集或构建新的通路网络。

`GET /overview/pathways/summary`：

```text
{totals:{association_count,pathway_count},
 topics:[{source,topic_id,name,association_count,pathway_count,
          filter:{topic_id}}],scope,notes}
```

association_count 按原 association_id 去重，pathway_count 按 source＋pathway_id 去重。主题沿用已经发布的 pathway_topic；同一通路可以属于多个主题，主题计数不能直接相加成独立通路数。没有富集、激活、重要性或分子互作推论。`/overview/pathways?topic_id=&limit=&offset=` 返回同一主题筛选的原关联及完整 `total / count_unit='source_pathway_association_records'`；原overview首屏pathways也补完整total。官方Reactome图可按现有pathway_id链接，不需要新采集。

### 本轮小范围验证

| 检查 | 结果 |
| --- | --- |
| VEP原状态 | P00533/P13569/P08183所选后果均CANONICAL=YES、selection_method=mane_select、Feature_type=Transcript；另0.05%受限页样本5543行均YES，不据此推断全库状态分布 |
| transcript过滤 | P00533 all/canonical各4096，noncanonical/unknown为0；list/detail原flag及GRCh38/HGVSc保留；非法状态422、跨状态旧cursor400 |
| 覆盖与性能 | P00533含完整61字段覆盖的summary约0.53秒；CADD_phred可用2872变异，REVEL/SIFT各2779，AlphaGenome AVI raw4096；空查询覆盖为0，未丢弃字段目录 |
| GO全量与首屏 | P00533完整1149注释、93个GO ID；F732/23，P102/43，C315/27；原首屏只有30条，但total=1149 |
| GO分类点击 | P00533 GO:0048856类别annotation_count=1，按slim_id的原列表total=1；P13569/P08183各aspect列表total与summary一致，未知slim_id返回0 |
| Reactome全量与主题 | P00533 82关联/78通路；Developmental Biology主题8关联/8通路；topic筛选limit2仍total8；原首屏15条，total82 |

代码入口新增[prediction_overview.py](../../../../src/api/prediction_overview.py)、[overview_summary.py](../../../../src/api/overview_summary.py)；列表/筛选位于既有 evidence.py/variant_support.py/variant_summary.py，Overview路由位于core.py。验证使用当前只读PG与TestClient，不新增环境、不重导入、不执行全库统计。
