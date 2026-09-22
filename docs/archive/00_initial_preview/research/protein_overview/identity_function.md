# 身份与序列、功能简介：来源及字段选择审查

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

日期：2026-09-20。状态：身份与序列、功能介绍的展示范围及默认canonical已确认，见[plan](../../plan/protein_overview.md)。本页维护来源统计和剩余设计讨论；实体字段建议见[数据设计](identity_function_data_design.md)。

## 1. 当前来源与统计依据

身份使用foundation UniProt 2026_03六类来源表中的protein_entry、protein_gene_name、protein_isoform、protein_sequence，结合curated protein_gene与gene_ensembl。HGNC来自2026-09-13本地快照；Ensembl116/MANE1.5保留作转录本参考，本轮不另选主序列。

功能使用当前UniProt 2026_03原始comment的无损解析 `Function.sequence_tracks.source_run/prototype/uniprot_comment.parquet`，路径由config/sources.yaml引用。该文件为现有探索性来源解析，不是已发布的功能简介表；正式整理应由负责模块维护后供Web消费。无需重新下载或改用旧UniProt版本。

本轮读取当前项目的身份表及所需comment列，核对目标与输出唯一accession数为7,715。统计脚本：[profile_identity_function.py](scripts/profile_identity_function.py)；机器结果：[identity_function_summary.json](results/identity_function_summary.json)；[缺FUNCTION清单](results/missing_function_accessions.txt)；[少量真实功能例子](results/function_examples.json)。

```bash
python Web/docs/archive/00_initial_preview/research/protein_overview/scripts/profile_identity_function.py
```

## 2. 身份与序列：先明确对象

蛋白条目是页面对象，以accession定位；基因是关联实体，通过HGNC关系连接；序列是具体残基坐标对象，以sequence_id及来源版本定位。三者不合并为同一身份。canonical是UniProt代表序列标记，MANE是转录本参考选择，两者不能因基因相同就当作序列一致。

### 当前覆盖

- 7,715条目全部有推荐蛋白名和可关联canonical序列。
- 5,948条目有替代蛋白名；6,832有secondary accession，主要用于检索/追溯。
- 7,709条目仅一个UniProt主基因名，4条目有两个、2条目有三个；不能把单值便利列为空解释为没有基因名。
- 蛋白—HGNC关系7,724行，7,723条Approved，一条not_in_snapshot；关系数不是基因或蛋白数。Q92681的HGNC缺口保持原状态，不猜补。
- 当前范围的可获取序列16,655条：7,715 canonical、8,940非canonical，含1条明确声明的跨条目序列。
- 来源声明isoform记录13,091条，其中79条不可获取。声明记录与FASTA序列不是同一粒度，不能用两者相减推断漏收。
- 当前7,715条目全部reviewed，但protein_existence仅7,014为蛋白水平证据；其余321为转录本水平、290同源推断、22预测、68不确定。此处不新增收录过滤。

### 可选字段与建议

| 内容 | 已有来源/字段 | 建议默认展示 | 详情或内部用途 |
| --- | --- | --- | --- |
| 蛋白名称 | protein_entry.recommended_protein_name | 显示作为标题 | alternative_protein_names用于别名检索及详情；原完整名称结构保留 |
| UniProt编号 | accession、entry_name、secondary_accessions | accession及官网链接 | entry_name可选显示，secondary accession用于检索；不替代主键 |
| 基因名称与身份 | UniProt primary_gene_names；protein_gene连接gene_ensembl/HGNC symbol | 已确认使用UniProt基因名称，HGNC作为关联标识 | 多基因关系完整保留；HGNC缺失或冲突时显式标记，不默默猜测或覆盖 |
| 物种 | taxon_id、organism_name | 可在页头简洁显示Human | 当前全为人类，不需占独立大卡片 |
| 长度与当前序列 | canonical_sequence_id/canonical_length、protein_sequence.length/sequence | 明确序列ID与对应长度；可提供复制/FASTA入口 | isoform切换后长度和适用注释同步；不能只换序列文字 |
| isoform | protein_isoform及其sequence_ids | 提供可用isoform入口，首屏不铺开全部序列 | 声明但不可获取者列状态；跨条目声明保留原关系 |
| reviewed与存在证据 | reviewed、protein_existence | reviewed可作为来源状态，存在证据放详情 | 不把reviewed等同全部注释实验验证；不因存在证据级别删蛋白 |
| 注释分数、版本与日期 | annotation_score、entry_version、sequence_version及来源版本/日期 | 不建议作为醒目“可信度分数” | 用于来源详情和追溯，annotation_score不等于变异致病或科学准确率 |
| 基因/转录本标识与坐标 | gene_ensembl、transcript_reference、protein_xref | 第一版概览只保留必要外链，可在详情展开 | 大量ENST/ENSP/RefSeq不铺在首屏；身份xref不冒充序列验证 |
| 内部来源定位 | source_file等 | 不显示 | 正式源数据保留，服务库仅加载必要追溯键；不向API暴露内部文件路径 |

已确认页面默认打开UniProt canonical；该展示选择不自动替代上游主要序列研究。保留isoform选择与缺失状态，不能让每个isoform继承canonical全部注释。UniProt官方将canonical与其他蛋白产物分开描述，说明见[canonical/isoforms](https://www.uniprot.org/help/canonical_and_isoforms)。

## 3. 功能简介：来源原文优先，摘要方法另定

FUNCTION为当前最直接的叙述来源，适合回答“这个蛋白做什么”。GO、Reactome属于相邻的功能/通路模块，不宜拼接成来源未作出的因果句。对催化/转运对象可使用CATALYTIC ACTIVITY及已整理的Rhea/GtoPdb作为明确标识的补充，不能把基因/靶点背景自动赋给所有isoform。

### 当前FUNCTION实物统计

| 指标 | 数量 |
| --- | ---: |
| 有非空FUNCTION文本的项目蛋白 | 7,087（91.86%） |
| 缺FUNCTION文本 | 628 |
| 有文本的FUNCTION comment | 8,227 |
| 有多条FUNCTION comment的蛋白 | 673 |
| 明确molecule的FUNCTION comment | 649，涉及351蛋白 |
| 每蛋白来源功能文本合计字符数中位数 / P90 / 最大值 | 477 / 1,541 / 9,247 |
| 合计文本超过1,000字符的蛋白 | 1,767 |

字符长度为每个蛋白全部FUNCTION文本合计，不代表一个固定可直接显示的简介，也不是建议截断阈值。molecule可能指isoform、链或加工肽；不直接将自由文本拼成isoform ID。

### 可用补充与用途选择

| 来源内容 | 当前有该comment的蛋白数 | 推荐用途 |
| --- | ---: | --- |
| FUNCTION | 7,087有文本 | 简介主体；来源段落、限定语、证据与对象范围保留 |
| SIMILARITY | 5,814 | 家族/同源背景，可单独显示；不改写成已实验验证功能 |
| CATALYTIC ACTIVITY | 2,287 | 催化或转运反应详情，并列展示，有内容展示，无内容留空 |
| COFACTOR | 717 | 并列展示辅因子，区分底物和配体 |
| ACTIVITY REGULATION | 1,118 | 并列展示活性调控条件 |
| CAUTION / SEQUENCE CAUTION | 875 / 2,398 | 审查与当前显示内容有关的限制；不能因为不适合首屏而在科研整理中丢弃 |

缺FUNCTION的628个蛋白中，342个有SIMILARITY，11个有CATALYTIC ACTIVITY；两者可重叠。它们是可用补充事实，不等于自动补出了功能简介。建议缺失时显示“来源暂无功能简介”，继续提供已有功能/家族标签；如要人工或模型编写新简介，另行确定引用、审核及不确定性保留方法。

### 推荐的首期呈现

- 保留UniProt英文原文为权威来源内容；页面显示短预览并允许展开，采用视觉折叠而不是在数据中截断。若后续需要中文或人工编辑的短摘要，作为独立有来源字段维护，不覆盖原文。
- 已确认完整保存FUNCTION并支持展开查看其他isoform；默认折叠简介最多选一条；选择时区分无明确molecule的条目级叙述与具名产物叙述，不把所有molecule段落直接拼接后赋给canonical。具体优先级见数据设计建议。
- 展示来源和证据入口；保留may/putative/by similarity等限定语。来源带实验、同源推断等不同证据，不能删掉推断说明后声称全部实验确认。
- 引用来源、PMID/ECO和comment身份用于详情或内部追溯；内部路径/原始大JSON不直接返回概览API。

官方来源概念可参考[UniProt手册](https://web.expasy.org/docs/userman.html)；本轮字段、文本长度与覆盖判断以本地固定输入为准。

## 4. 当前决定与剩余设计

已确认内容以[plan](../../plan/protein_overview.md)为准，替代本页此前HGNC名称优先及功能分组全部展示的候选方案。FUNCTION及四类补充注释完整保存，其他isoform内容展开查看；默认折叠简介最多展示一条，缺失暂不补写。

FUNCTION已确认canonical优先、其次条目通用、同级按来源顺序取第一条；外部标识已确认UniProt、HGNC、Ensembl、RefSeq及疾病标识。四类补充注释按canonical与通用信息分组完整展示，其他isoform折叠查看。工程实体和字段设计见[数据设计](identity_function_data_design.md)，新增[数据总览面板大纲](data_overview.md)留待后续设计；七张服务表已构建；当前输入与交付状态见[本地构建方案](../../plan/local_table_build.md)。

## 5. Basic info复审（2026-09-20）

状态：用户要求重新逐板块讨论，当前建议待确认，不替代plan生效规则；确认后再更新构建与PostgreSQL。用户进一步明确Basic info指整个蛋白概览，本节只记录其中身份、基因、序列及外部标识的首轮核对，不能视为完整Basic info审查。当前讨论聚焦纳入数据与待解决问题，下文展示形式建议不作为本轮待决事项。已阅读Web约定、当前plan、构建代码和五张身份服务表的字段及P00533样本，并对照foundation来源xref。没有重跑构建或入库。

2026-09-20约23:16（Asia/Hong_Kong）进程检查可见PostgreSQL主进程及后台进程，未见build_tables/import_tables/validate_import脚本运行。已有导入报告记录33张业务表入库，绑定2026-09-20T11:27:27.365908+00:00构建；本次未重新执行数据库查询验收。API与页面仍未交付。

建议保留accession页面入口、UniProt名称、HGNC已确认关联、canonical默认及五张身份表。首屏显示名称、accession、基因名/HGNC、human、当前序列身份及长度；别名、其他isoform、外部编号和来源详情折叠。多HGNC关系及not_in_snapshot状态原样保留；不可获取的isoform声明继续展示状态。完整序列按需读取。首期isoform查看/下载仅改变明确的序列对象；全页注释联动须逐轨道限定sequence_id，不自动继承canonical注释。

复审发现与建议：

- P00533的isoform声明P00533-1明确指向sequence_id=P00533、长度1210；P00533-2序列长度405。页面分别说明isoform声明和实际序列身份，不能直接拿isoform_id查序列表，也不能为无声明的canonical虚构-1。
- 当前构建将所有RefSeq外链指向NCBI nuccore。例如NP_005219.2为蛋白编号，应按对象类型生成protein链接；核酸记录使用nuccore。类型含义见[NCBI官方说明](https://support.nlm.nih.gov/kbArticle/?pn=KA-03357)。本轮仅登记，未修改代码。
- 同一来源RefSeq xref的properties_json已保存NucleotideSequenceId=NM_005228.5，但当前Web投影未保留该字段。建议保留显式来源蛋白—转录本配对及各自对象类型，不重新推断关系，也不将其解释为跨库序列相等。
- Ensembl已有完整ENST/ENSP/ENSG字段，建议详情按基因、转录本、蛋白类别展示，保留版本后缀及条目/isoform适用范围。疾病ID继续随疾病关系接入，不作为蛋白自身ID。

取舍：现有拆表能保留一对多关系和对象语义，但API需要组装关系；由后端统一返回Basic info可减少前端负担。首屏折叠降低阅读量，代价是完整列表需展开。先提供isoform查看/下载可减少未经核实的联动，代价是尚不能直接完成跨isoform轨道比较。以上待用户讨论确认后更新plan。
