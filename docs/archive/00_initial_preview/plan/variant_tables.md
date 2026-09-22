# 突变服务表与详情方案

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-21。用户确认五张核心表精简方案：VEP、dbNSFP和AlphaGenome统一组织为计算注释与预测结果，按variant与所选transcript后果粒度存储；保留原数值、状态及ClinVar等来源注释。表和字段取舍已收口，本轮已进入授权实施，服务表已构建并导入web_variant，11张业务表及6个普通视图验证通过，交付状态见[版本记录](../../../record/00_initial_preview/20260921_variant_v1.md)。展示原则见[展示方案](variant.md)。现行粒度依据[variant契约](../../../../../modules/variant/docs/data_contracts.md)。

## 五张核心逻辑服务表

表数量不含共享dataset/模型字典、foundation实体及已有蛋白序列映射/ddG服务关系；不能声称五张表已包含整个突变相关数据库。

| 表 | 一行与主要内容 | 整合来源 |
| --- | --- | --- |
| variant | 一个variant_id；GRCh38坐标、REF/ALT、28个变异级dbNSFP数值与状态、AlphaGenome3项与状态 | variant、prediction_variant及dbNSFP状态、AlphaGenome两表；成员/rsID由来源关系查询组合 |
| variant_consequence | 一条(annotation_id,gene_id)代表后果；variant_id、所选ENST/ENSP、MANE/canonical状态、后果、HGVSc/HGVSp、蛋白位置及30个转录本级值/状态 | representative_annotation、对应VEP、prediction_annotation；VEP必要其他字段放详情 |
| variant_source_record | 一条来源快照中的原记录；dataset_id、source_row_id、原生ID、原始临床/肿瘤等字段和链接；来源/版本通过dataset取得 | ClinVar/COSMIC/gnomAD等来源表按带类型的记录入口组织；不同源结构可用有契约的details |
| variant_source_link | 一个variant与一个原记录/ALT的关联，保留variant_id、source_row_id、alt_index及必要匹配证据；source通过记录取得 | variant_source及选定dbSNP来源证据；不靠原生ID猜关系 |
| variant_frequency | 一个variant的正式本地gnomAD频率和状态，总体及群体AC/AN/AF等 | 本地频率正式表已验证发布，按variant_id填充各来源重叠记录，不从缓存补缺 |

dbSNP原始证据若经精简纳入统一record/link，使用真实来源记录键和ALT身份，不伪造成ClinVar式来源。rsID与数据库成员作为普通视图或API的查询投影，不在variant另存数组副本；不能替代可追溯的link。dbSNP若无与通用source_row_id同义的原始行键，复用现有等位基因证据关系并统一查询，不虚构键或强行限制为五张物理表。来源一条多ALT记录保存一次，多个variant通过link指明ALT，不在每个后果复制原文。

变异级与后果级一对一评分分别合入相应实体，减少单独分数表连接。普通查询只投影列；长来源详情不在列表响应返回。58项评分仍保留，不变成全部58项首屏列，也不展开成每variant×每模型海量键值行。来源预测类别pred原文及上下文追溯继续保留，不能只保留数值后丢失用户要求的信息。

variant_consequence不臆造统一sequence_id：序列对应通过已有或后续验证的关系取得，允许多个候选/目标。基因—变异原关联证据按用途保存于关系详情或上游，不能冒充全部有代表蛋白后果。

## 已确认的粒度与链接

VEP、dbNSFP、AlphaGenome属于同一“计算注释与预测”信息组，不按工具各建一套服务表。工具名称只表明来源，不能代替scope：VEP提供后果和上下文注释，dbNSFP汇集评分及背景信息，AlphaGenome提供本批变异级分数；统一分组不把全部字段解释成致病概率。

| 粒度 | 内容 | 关联键 |
| --- | --- | --- |
| variant | DNA身份、dbNSFP变异级28数值与状态、AlphaGenome三数值及两来源独立状态 | variant_id；不因多个基因后果重复存储 |
| transcript后果 | 所选VEP后果及上下文、dbNSFP后果级30数值与状态、对应pred原文及匹配证据 | (annotation_id, gene_id)，同时外键关联variant_id；实际ENST/ENSP不省略 |
| 来源记录 | ClinVar/COSMIC/gnomAD原生记录、dbSNP等位基因证据 | 来源快照与原记录键，通过link连接variant及ALT |
| 频率 | 本地gnomAD总体/群体值和状态 | variant_id，保留实际来源记录/ALT的溯源关系 |
| 蛋白替换 | 已验证的canonical位置和ddG | annotation到实际sequence/position/ref/alt及预测记录的现有关系；不只凭variant_id套用 |

蛋白列表入口为protein → protein_gene（HGNC）→ variant_consequence.gene_id → variant。VEP的Gene（Ensembl）与HGNC gene_id分别保存，不混用。基因关联只用于导航，不证明该后果对应当前canonical。序列联动只使用已验证canonical映射；无映射者仍保留列表。当前MANE优先/无MANE才回退Ensembl canonical的选择不变。

## 字段精简执行契约

| 原表/字段 | 服务层取舍 |
| --- | --- |
| representative_annotation、对应variant_vep、prediction_annotation | 按实际annotation/gene键合并；ENST、ENSP、后果、HGVSc/HGVSp、位置、选择依据只维护一份，其他不重复的VEP注释保留在列或结构化详情 |
| prediction_variant、dbnsfp_status、AlphaGenome数值/状态表 | 按variant_id一对一并入variant；58项dbNSFP数值和3项AlphaGenome数值全部保留，不平均、不择优、不舍入降精度 |
| 后果中的chrom/pos/ref/alt、重复variant身份 | 从variant读取；原始来源坐标与标准坐标不同的含义继续保留，不能当同值冗余删除 |
| variant_database、rsID成员数组 | 从实际来源/rsID关系生成视图；不重复存同一成员关系；dbSNP未命中状态不因简化消失 |
| ClinVar/COSMIC/gnomAD来源分表 | 使用统一记录/关联契约；一条来源记录保存一次，多ALT通过link区分，不能任选一条临床或肿瘤记录 |
| source、version、重复基因/蛋白名称 | 已有身份或dataset键可恢复的通用说明只保存一次；来源原始名称/标签与项目规范值不同则保留原文 |
| 调试字段、内部路径、复制的整包 | 不进入业务字段；保留dataset、记录键和必要溯源入口。原始payload只有在剩余信息已完整投影后才能省略 |

VEP除重复身份外，保留现有选中后果的注释信息，包括IMPACT、BIOTYPE、EXON/INTRON、cDNA/CDS/Protein_position、Amino_acids/Codons、STRAND、HGVS、MANE/CANONICAL、TSL/APPRIS/CCDS及现有其他非重复字段；不按首屏需求删信息，不新增原快照未保留的转录本。

dbNSFP保留全部已选数值、逐字段状态及来源pred/Confidence/机制等非数值注释。prediction_match、ALoFT选定slot证据及必要来源数组保留可追溯关联或服务详情，不能把未选转录本数组任意压成一个值；若无法无损投影则暂留结构化详情，不以只剩数值为验收标准。其他转录本原数组只作为来源证据，不扩展代表后果范围。

ClinVar保留VariationID/AlleleID、RCV与现有SCV汇总引用、PhenotypeIDS/PhenotypeList、ClinicalSignificance、ReviewStatus、Origin、LastEvaluated、提交者数量/类别、SomaticClinicalImpact、Oncogenicity及各自审核状态/日期，以及其他原有非重复注释。不能仅留链接或一个Pathogenic标签。COSMIC保留COSV及现有QUAL/FILTER/INFO里的非重复注释；不凭页面需求假设当前来源具备额外样本信息。gnomAD频率按ALT解析，同时保留FILTER与原有非重复来源注释，不接入VEP/cache频率补缺。

## 推荐列表列组

1. 变异：variant_id可复制、蛋白改变、后果；MANE Select/回退标记及ENST可见或悬停。
2. 来源注释：ClinVar/COSMIC/gnomAD/dbSNP入口，显示收录与可用内容；临床标签只有核实具体语义后显示简述。
3. 人群频率：正式总体AF及gnomAD来源；群体、AC/AN、FILTER等展开。
4. 计算注释与预测：统一包含VEP、dbNSFP、AlphaGenome，注明variant或所选transcript后果层次；AlphaGenome三项保留各自名称和数值，不强并总分。

不需要把所有临床、肿瘤、频率和评分显示在同一单元格。COSMIC原始字段/记录多条均保留；不能将样本/肿瘤背景和gnomAD人群频率混为同一种频率。ClinVar的germline意义、somatic clinical impact、oncogenicity分组查看，不统一压成一个Pathogenic字段。

## 预测展开分类建议

| 展示组 | 例子与范围 | 注意 |
| --- | --- | --- |
| 氨基酸替换效应 | SIFT/SIFT4G、PolyPhen-2、PROVEAN、MutationAssessor等 | 保留所选后果上下文和原值，不能统一按数值大=有害 |
| 综合/致病性预测 | REVEL、MetaRNN、BayesDel、CADD等 | 每字段仍注明variant或transcript层次；模型输出不是临床诊断 |
| 序列模型相关预测 | ESM1b、AlphaMissense、popEVE等 | 是展示分组，不称方法完全相同；不与项目PLM embedding混同 |
| 功能缺失相关 | ALoFT比例与三概率 | 比例不是概率，多个输出不合并为新标签 |
| 保守性/背景 | phyloP、phastCons、GERP、bStatistic等 | 组内注明具体含义；不是JSD蛋白轨道，也不是每项都属于直接保守性分数 |
| AlphaGenome | AVI raw、AVI PHRED、merged splicing | 统一预测组内的来源子类，不按组织或MANE展开不存在的数据 |

模型导航分组已确认，全部58字段的逐项归类和排序需落实；未引入临床阈值。建议模型字典维护display_group、原始字段名、来源版本、scope、含义/量纲与文档入口；不根据截图条形颜色生成统一强弱等级。

ddG作为已交付的“稳定性预测”直接复用现有prediction、variant_prediction及状态关系。通过(dataset, prediction_id)连接，并限定当前canonical sequence_id；canonical位点可查询该位置的不同替换，选中具体变异时再匹配position+ref+alt。位点联动不把ddG简化成每位点单值，不复制评分到每个DNA变异，也不重复推理。当前没有可用MAVE实验来源就不显示实验作用数值。

## 必须保留和可以减少什么

保留：variant_id、实际annotation/gene/ENST/ENSP、来源多记录/ALT关系、原始临床/肿瘤含义、所有已选分数与状态、频率缺失和版本、必要文献及链接、序列映射状态。

减少：一对一服务评分表、重复蛋白/基因名称、重复整条来源记录、列表API长字段、与页面无关的调试/绝对路径。完整上游来源仍作为唯一溯源入口；将服务详情投影为结构化字段前核对没有丢失承诺展开的信息，不直接全删payload。

本期不构建综合优先级分数、多模型投票标签、来源多数致病结论。频率已发布；其覆盖限制与序列对应缺口按[现状报告](../research/variant/current_data.md)处理。主表密度统计以后果/variant/替换哪种粒度计算尚待确认，不使用来源记录数冒充变异数。

## 后续构建验收

仅检查本次合并与去重涉及的关系：variant和代表后果键集不变；一对一合并不扩行；多来源/ALT关系完整；全部数值、零/null、缺失/冲突状态不变；ClinVar等非重复注释可从服务库恢复；既有来源标签和dbNSFP上下文不丢失。可通过连接恢复的重复字段须验证相等后再省略，发生冲突不任选覆盖。已按此标准完成构建与数据库验收，结果见[版本记录](../../../record/00_initial_preview/20260921_variant_v1.md)。

2026-09-21补充授权：落实本地gnomAD频率构建。使用最终variant_source的source_row_id/alt_index连接gnomad_record，解析后按variant_id提供频率；ClinVar/COSMIC与gnomAD重叠者自然复用相同数值，不单独复制频率或重新映射转录本。无本地来源者保留null。运行交付见[variant结果](../../../../../modules/variant/docs/result.md)。

### canonical与ddG的具体连接

已核对正式三表字段：`variant_prediction`带annotation_id、variant_id、gene_id、prediction_id；`prediction`带sequence_id、position、ref_aa、alt_aa、ddg_pred及结构/模型背景。连接使用同一预测快照的prediction_id，变异后果入口同时限定annotation_id、gene_id及variant_id。再以prediction.sequence_id = protein.default_sequence_id限定canonical。

点击canonical位点时，按sequence_id＋position读取所有已预测替换；点击某个变异时沿variant_prediction取得相应prediction_id，不仅凭相同位置匹配。多个DNA变异产生同一蛋白替换时复用同一预测记录；频率仍按各自variant_id独立读取。没有预测则从variant_prediction_status读取原因；现有status只覆盖相应标准错义输入，不能把其他后果不存在状态行解释成预测值0。

## 构建与数据库组织（2026-09-21）

执行入口为`Web/src/build/build_variant.py`和`Web/src/database/import_variant.py`，配置集中于`Web/config/variant.yaml`。服务Parquet位于`Web/data/tables/variant`，有独立manifest；同一PostgreSQL数据库中使用`web_variant` schema，通过`web.protein_gene`连接蛋白页面。增量schema整体验证后切换，不替换已发布的web或web_context。

五张核心表外，保留variant_dbsnp等位基因证据、ddG预测/关联/状态三表、来源字典及预测字段字典，共11张业务表。dbSNP没有伪造source_row_id；数据库成员及rsID列表通过视图提供。dbNSFP原记录进入统一source_record，其原数组和pred/机制说明作为来源证据保留，已选数值则按原粒度列化；这些证据与已选数值用途不同，不能直接删除。

服务层去除的预测transcript_id/protein_id须分别与VEP Feature/ENSP逐条相等，不与去版本的stable_id混比。ClinVar/COSMIC/gnomAD当前非重复来源注释以JSONB完整保留；数据库端不只留外链。后续若进一步解析来源INFO，应在无损字段核对后再去除重复原文。

依赖：现有DuckDB/PyArrow，加psycopg 3.3.6。大表COPY使用驱动数据通道，避免命令行对多行原文特殊结束符的解释；导入前检查空字符串、null、零、负值、Unicode、引号、换行和反斜杠的往返。新schema失败时保持旧schema可用，临时schema及进度可用于恢复。
