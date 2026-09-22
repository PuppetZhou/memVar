# 突变板块：当前数据规模、来源与注释层次

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

核对日期：2026-09-21。读取当前正式快照交付报告、现行规则和后续集成证据；数值复用2026-09-16/17已验证统计，变异与评分统计沿用已验证结果；09-21实际构建并验证本地频率，未改变收录范围。Web字段与分类已确认，见[五表方案](../../plan/variant_tables.md)；本页仅维护来源现状。

## 当前范围与来源

正式入口为variant/data/curated/20260916_final_snv_v2。GRCh38规范化DNA变异10,866,094个，代表后果10,881,400条；2,086个变异涉及多个基因代表条目，因此后果行数多于变异数。按基因MANE Select优先、无MANE时Ensembl116 canonical；这里不是UniProt默认canonical选择。

最终范围是SNV、允许编码/蛋白后果（包含同义）且同条代表记录HGVSp非空。非SNV不在当前集合，不能用旧全量frameshift/inframe计数描述现状；纯剪接/UTR/内含子不独立收录。HGVSp非空不证明已匹配当前UniProt序列。

| 来源 | 固定来源 | 最终唯一variant数 | 比例 |
| --- | --- | ---: | ---: |
| ClinVar | variant_summary 2026-09-06 | 1,353,893 | 12.46% |
| COSMIC | v104 GenomeScreens Normal GRCh38 | 2,196,739 | 20.22% |
| gnomAD | exomes4.1 | 9,277,804 | 85.38% |
| dbSNP（补充标识） | build157 | 8,014,881 | 73.76% |

前三来源有交集，不求和；dbSNP不增加dbSNP-only变异。COSMIC Targeted Screens仍待补充。三来源互斥分类：ClinVar-only345,620，COSMIC-only1,211,694，gnomAD-only7,550,875，ClinVar+COSMIC无gnomAD30,976，ClinVar+gnomAD无COSMIC772,860，COSMIC+gnomAD无ClinVar749,632，三者共有204,437。

## 后果构成

| 后果 | 代表条目数 |
| --- | ---: |
| missense | 7,377,066 |
| synonymous | 3,114,407 |
| stop_gained | 350,665 |
| start_lost | 23,915 |
| stop_lost | 11,162 |

复合标签可重叠。另有356,849条splice_region标签，是已入选编码/蛋白后果上的并列标签，不是额外收录纯剪接。没有frameshift或inframe indel条目。

## 注释分层

1. DNA变异实体：variant_id、组装、chr/pos/ref/alt；来源记录及ALT对应、rsID、原生频率均属这一层。
2. 代表转录本后果：variant×目标gene×选定ENST，含ENSP、HGVSc/HGVSp、后果和选择依据；保留入选后果完整VEP字段。
3. 评分：dbNSFP变异级28数值字段与所选转录本级30字段，分别关联；AlphaGenome为variant级汇总，不当作特定isoform/组织预测。
4. 蛋白序列和具体替换：明确sequence_id、position、ref/alt，需核对序列；ddG绑定具体替换及结构模型，不能用一个位点平均值替代不同替换。
5. 位点背景：PTM、domain、膜区段、JSD等通过已验证sequence/site连接，坐标重叠不自动推出效应。
6. 疾病与临床解释：保留ClinVar原始germline/somatic/oncogenicity及疾病含义；疾病模块的基因—疾病背景不能赋给每个变异，统一variant—disease关系及SCV/RCV等补充尚待推进。

## 已有注释覆盖

| 注释 | 数量/覆盖 | 分母与说明 |
| --- | --- | --- |
| dbSNP | 8,014,881唯一变异，73.76%；8,021,330条rsID关系 | 10,866,094唯一variant |
| dbNSFP至少一项数值 | 7,762,691唯一变异，71.44% | 不表示58字段全部齐全 |
| 所选转录本级至少一项值 | 7,659,969代表条目，70.40% | 10,881,400代表后果 |
| missense至少一项dbNSFP值 | 98.72% | 7,377,066错义代表后果 |
| synonymous至少一项dbNSFP值 | 3.57% | 3,114,407同义代表后果 |
| stop_gained至少一项dbNSFP值 | 98.58% | 350,665终止获得代表后果 |
| AlphaGenome AVI | 10,863,110唯一变异，99.9725% | 当前全部DNA变异；MT未覆盖 |
| AlphaGenome merged splicing | 10,762,279唯一变异，99.0446% | 不证明实际剪接改变 |
| ThermoMPNN ddG | 6,292,698条UniProt替换评分，关联6,430,696个DNA变异 | 不同粒度，不作为全部错义完整映射率 |

错义代表后果中具体工具覆盖：CADD_phred98.69%、REVEL82.37%、AlphaMissense91.78%、ESM1b98.70%、popEVE48.29%。58字段不等于58个独立模型。缺失、冲突、来源未收录、所选转录本不匹配各有状态，不换另一ENST补分。

ClinVar原ClinicalSignificance的既有统计：B/LB组344,089，P/LP组60,961，原文恰为VUS857,476，冲突55,328；复合、低外显率等另列。它们不是全项目致病性分类或独立病例数，来源标签尚不等于Web统一分类规则。

## 频率：2026-09-21已正式构建

已确认只用本地gnomAD exomes4.1，不使用VEP/cache、genomes或1000 Genomes补缺。最终集合9,277,804个有gnomAD来源关系（85.38%），1,588,290个无本地来源（14.62%）。前者是当前本地输入可供解析的对象范围上限，不等于AF已非空覆盖；后者不是证明完整gnomAD没有这些位点。

总体和群体AC/AN/AF、nhomalt、FAF、grpmax/fafmax、FILTER及版本已规划从原始INFO按alt_index提取，variant_frequency已发布：总体AF非空9,277,645，有本地来源但总体AF缺失159，无本地来源1,588,290；真实零1,787,812。群体逐字段覆盖、产物与验收见[频率结果](../../../../../../modules/variant/docs/frequency_result.md)。

现存VEP cache exomes总体AF非空4,672,339个、genomes2,176,302个、1000 Genomes358,859个，仅历史缓存统计，不进入当前正式取值。旧70,121,838个gnomAD变异集合的98.8776%原生AF非空覆盖也不是当前10,866,094集合的覆盖率。

频率按DNA等位基因保存；多个DNA变异即使产生同一蛋白替换，也不能相加AF或任选一个。缺失不填0；gnomAD人群AF不等于COSMIC肿瘤发生率、样本VAF或疾病外显率。

## 当前最需要推进的缺口

- 本地频率正式表已完成，Web已按variant_id接入web_variant，不重复构建。
- 完成/复核面向当前UniProt序列的变异关系；不能因为页面默认canonical就改动代表ENST或投影坐标。
- 区分ClinVar疾病/临床证据与基因疾病背景；选定Web展示的原生标签和证据字段。
- dbNSFP_gene约束、COSMIC Targeted Screens等仍待处理；DMS/人工Mutagenesis不是当前三来源自然变异集合的一部分。

## 证据入口

- [variant现行规则](../../../../../../modules/variant/docs/rules.md)、[当前结果](../../../../../../modules/variant/docs/result.md)
- [最终集合交付](../../../../../../modules/variant/runs/20260916_final_snv_v2/report.md)、[来源组合](../../../../../../modules/variant/runs/20260916_final_source_dbsnp_review/report.md)
- [dbSNP后续完成报告](../../../../../../modules/variant/runs/20260916_dbsnp_mapping/report.md)、[dbNSFP覆盖](../../../../../../modules/variant/runs/20260916_final_dbnsfp_coverage/report.md)
- [频率计划及缓存核对](../../../../../../modules/variant/docs/frequency_result.md)
- [AlphaGenome](../../../../../../modules/Alphagenome/docs/result.md)、[ddG当前交付](../../../../../../modules/Site-Region/docs/result.md#ddg正式预测交付20260917_ddg_thermompnn_01)

部分早期交付报告保留“dbSNP未完成”等历史文字，本页按后续实际集成记录更新判断；不混用旧77百万全量范围或已清理数据。当前不新增正式科学规则。

2026-09-21服务层交付：Variant已构建并导入PostgreSQL，频率和canonical ddG已联动，见[实际版本记录](../../../../record/00_initial_preview/20260921_variant_v1.md)。上文上游范围与来源限制继续适用。
