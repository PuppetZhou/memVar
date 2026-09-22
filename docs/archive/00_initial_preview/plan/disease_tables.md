# 疾病服务表：精简与PostgreSQL契约

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-21用户确认：复用已完成的mapping，通过现有基因标识与蛋白编号建立服务查询；保留关键信息后精简，并写入当前PostgreSQL。本轮不重做科学mapping，不新增ClinVar条件推断或旧36类疾病分类。

数据库仍为memvar_web；疾病表使用web_disease schema，避免与同时建设的web_context或既有web表相互覆盖。共享身份通过web.protein_gene及已发布NCBIGene—蛋白关系查询。配置入口：Web/config/disease.yaml；实际行数和验收见[版本记录](../../../record/00_initial_preview/20260921_disease_v1.md)。

## 20张业务表

| 表 | 粒度及字段选择 |
| --- | --- |
| disease_dataset | 六来源版本、来源入口及快照；版本文本不在每条断言重复 |
| disease_entry | 原来源疾病ID/名称/类型/废弃状态/链接，合并OMIM别名、included title、prefix/type及MONDO映射状态；主定义只保存引用 |
| disease_definition | 定义文本、提供者及版本；相同三者只存一次，含MONDO/HPO术语及MedGen来源定义 |
| disease_definition_link | 原疾病—定义关系、原source_record、via、display_eligible；不自行选择新代表定义 |
| disease_label | 同疾病、来源、名称文本保存一次 |
| disease_label_origin | 每一次原始名称出现的source_record；原本重复出现也完整保留 |
| gene_disease_evidence | 全部来源基因—疾病关系，保留分类、遗传方式、机构、日期、文献、报告、关系粒度、OMIM标记及原文；来源版本通过dataset取得 |
| evidence_identifier_check | 合并GenCC原编号及一致性核对；保留原编号、规范化编号、候选集合和冲突状态 |
| gene_dosage | ClinGen现有基因级HI/TS、来源symbol、报告与日期；不赋给每个疾病 |
| gene_protein_ncbi | 仅保存已有NCBIGene—蛋白关系；HGNC部分复用web.protein_gene |
| disease_phenotype | 原HPOA注释，保留NOT/qualifier、aspect、频率、起病、性别、modifier、文献和证据；原疾病名引用来源名称出现，HPO规范名从词典取得 |
| disease_mondo_link | 已有明确等价候选及依据；mapping_status通过疾病条目恢复 |
| disease_medgen_link | 原ID、CUI及替代CUI、原名、关联状态；禁止身份合并为统一规则，不逐行存false |
| medgen_concept | 按resolved CUI组合原生名称、定义引用；保留原CUI、来源、SUPPRESS及display_eligible |
| shared_report_candidates | 原22组共享报告候选，不删断言或合成评分 |
| ontology_term | HPO/MONDO共用术语结构，保留名称、定义引用、原定义限定、废弃及替换/consider |
| ontology_parent | 完整已有父子边，外部BFO/PATO父节点原样保留 |
| ontology_alias | 原alt ID关系，保持一对多可能性 |
| ontology_synonym | 原同义词及scope/原文 |
| ontology_xref | 原外部编号、关系语义及原文，不把普通xref改成等价 |

GenCC和ClinGen断言/活动原生表中的非重复字段放gene_disease_evidence.source_details_json。包括GenCC notes、assertion criteria URL、分类/遗传方式/机构CURIE、来源submitted-as字段和ClinGen活动明细；已与主字段逐行一致的内容不再复制。字段对应维护在disease.yaml的native_field_aliases，原文不同者仍保留。原生行重建验证须通过。

ClinGen基因剂量沿用已发布gene_dosage的CSV来源，不将另一个gene curation TSV或CNV表自动混入同一断言；后者仍为上游来源材料，未新增融合、基因区域重叠或CNV范围。

## 链接与普通视图

- gene_protein_link：HGNC关系由当前protein_gene筛到本板块使用的基因，与gene_protein_ncbi组合。与上游4,746条关系逐条相等，不新增映射。
- protein_disease_evidence：上述关系连接gene_disease_evidence_detail，提供蛋白入口；多基因、多来源断言分别保留，不以蛋白为单位复制断言。
- disease_entry_detail、disease_description：通过定义字典恢复原主定义和全部原定义关系。原主表独有的19条定义保留为原主定义引用，不伪造新的display_eligible关系。
- disease_source_label、disease_phenotype_detail：恢复每次来源名称、HPO术语名称、来源版本和原database_id；保留每条HPOA记录。
- gene_disease_evidence_detail、gene_dosage_detail：恢复来源/版本；medgen_names、medgen_definitions：恢复原始MedGen项目记录。
- disease_mondo_link_detail、disease_medgen_link_detail：恢复被移入实体/规则的状态与恒定属性。

上述12个普通视图不保存关系副本。共享web身份表后续替换时须维护这些依赖视图，不能通过CASCADE无声删除疾病查询入口。

## 输入、执行与验收

使用既有disease_links_02和native_mapping_02快照；上游保持原位。构建脚本build_disease.py只投影字段并复用既有关系；临时Parquet检查通过后发布Web/data/disease_tables。授权重建使用--replace，原目录切换失败可恢复。

导入脚本import_disease.py复用共享COPY/type处理，先导入独立临时schema、建立主键/外键/查询索引。定义、证据、基因关系、HPO注释、MedGen记录及GenCC冲突与原Parquet逐字段重建比较通过后，事务切换web_disease。仅修改自己的schema，不重建web或web_context。

```bash
python Web/src/build/build_disease.py
# 已有本轮产物的授权重建：python Web/src/build/build_disease.py --replace
python Web/src/database/import_disease.py
```

ClinVar条件集合/成员/变异关联留待对应阶段，不把基因所有变异视为该病致病变异。未新增疾病分组阈值、综合评级、来源支持投票或疾病总量汇总。
