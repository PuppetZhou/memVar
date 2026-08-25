# 01. 产品蓝图与信息架构

## 1. 产品定位

memVar 是一个面向膜蛋白的 protein-centric evidence portal。用户从蛋白、基因或稳定数据库 ID 出发，在同一个 canonical protein 页面中查看：

- 蛋白身份、膜类别、功能、定位和通路；
- canonical 序列上的 topology、domain、PTM、UniProt feature、变异与保守性；
- canonical 优先、isoform 可展开的变异证据；
- 多模态组织表达；
- QTL、互作与疾病证据的摘要和明细。

网站的主问题不是“这个突变是什么”，而是“这个膜蛋白有哪些可追溯的分子、变异、表达和疾病证据”。因此，变异键不作为首页主入口。

## 2. 目标用户与首要任务

| 用户 | 首要任务 | 网站应给出的结果 |
|---|---|---|
| 基础研究者 | 快速了解一个膜蛋白及其功能位点 | 身份摘要、序列轨道、功能/通路/定位 |
| 变异研究者 | 判断变异落在哪个蛋白区段及有哪些来源证据 | canonical effect、isoform effect、来源分支、保守性/PTM/topology 上下文 |
| 疾病遗传研究者 | 查看 gene–disease assertion 与表型 | ClinGen、GenCC、OMIM 分来源展示，HPO 作为疾病明细 |
| 组学研究者 | 查看组织表达、QTL 和互作语境 | 分量纲表达矩阵、QTL/interaction 摘要及可筛选明细 |

## 3. 检索入口

首页保留一个主搜索框，支持：

1. UniProt accession、entry name、isoform ID；
2. protein name；
3. primary gene symbol、gene synonym、ORF name；
4. HGNC、NCBI GeneID、Ensembl gene ID；
5. ENST、ENSP、RefSeq transcript/protein ID。

排序优先级：

```text
exact UniProt accession
  > exact stable database ID / isoform ID
  > exact primary gene symbol / entry name
  > exact synonym
  > prefix match
  > token match in protein name
```

返回项至少显示 `gene symbol · protein name · UniProt accession · membrane class · length`。一个输入命中多个 accession 时进入候选页，而不是直接跳转。候选页解释“该 gene/alias 对应多个 reviewed protein entries”，允许用户明确选择。

当前数据库冻结范围是 reviewed human membrane proteins，因此初版不提供物种切换；页面来源说明固定写明 Homo sapiens。不要因为 Basic_info 中缺少 taxonomy 列而在候选卡上留一个无意义的空物种字段。

## 4. 页面与路由

```text
/
├── /search?q=...
├── /protein/{uniprot_accession}
│   ├── #overview
│   ├── #sequence
│   ├── #variants
│   ├── #expression
│   ├── #qtl
│   ├── #interactions
│   └── #diseases
├── /protein/{uniprot_accession}/variants
├── /protein/{uniprot_accession}/qtl
├── /protein/{uniprot_accession}/interactions
└── /about/data-sources
```

蛋白主页面承载摘要和有限明细；variant、QTL 与 interaction 在记录过多时使用专门的全屏表格路由。用户从主页面点击某个摘要单元格时，筛选条件原样带入明细页。

页内导航显示当前模块，Sequence 之后的重型模块延迟加载；不能让超长 Variant/QTL/Interaction 数据阻塞 Basic info 首屏。

## 5. 蛋白结果页的信息层级

### 5.1 Header 与页内导航

首屏显示：gene symbol、protein name、UniProt accession、entry name、canonical length、膜类别、protein existence、annotation score，以及各层记录数徽标。搜索框保持可见；左侧或顶部使用 sticky anchor navigation。

### 5.2 Basic information

使用紧凑的分类表，而不是大段无结构文字：

| 分组 | 初版内容 |
|---|---|
| Identity | accession、entry name、protein/gene name、aliases、stable IDs |
| Membrane classification | primary class、全部 class labels、TM/intramembrane/lipidation counts |
| Localization | UniProt subcellular location、topology、orientation |
| Function | GO Molecular Function 与 Biological Process；详细 evidence 在抽屉中 |
| Cellular component | GO Cellular Component，与 UniProt localization 分开展示 |
| Pathways | Reactome membership；默认去除层级重复后显示最有信息量的路径 |

当前 View 没有 UniProt free-text Function comment，因此初版不能伪造“UniProt 功能简介”。可展示 protein name、GO、Reactome、subcellular location 和 feature；若未来确需原文功能摘要，应在后续数据版本中明确加入来源字段。

### 5.3 Sequence & site

使用两级视图：

- overview：全长坐标、TM/topological domain/Pfam/UniProt interval、variant density、PTM density；可拖动 brush。
- detail：被选区段的氨基酸字符、保守性背景、点位 feature、PTM 与具体 variant marker。

默认 canonical；isoform 只在变异表中展开。详细轨道定义见 `03_ui_and_api_spec.md`。

### 5.4 Variant

一个 genomic variant 在蛋白页只占一条主行。主行使用 `represent_variant` 的 variant-level 字段；当前蛋白对应的 effect 来自网站派生的 `variant_protein_effect`。展开后依次显示：

1. 当前蛋白的 canonical effect；
2. 其他 canonical/isoform effects；
3. ClinVar source branch；
4. COSMIC source branch；
5. gnomAD frequency 与 dbSNP identifiers。

这样既满足 canonical 优先，也避免 `represent_variant` 的“每个变异只选一个代表蛋白”规则让其他合法蛋白关系消失。

### 5.5 Expression

采用同一种矩阵交互，但分成 HPA RNA、HPA MS、HPA IHC 和 PaxDB 四个 tab/row group。每组保留自己的单位、色标和缺失状态；不把 nTPM、MS intensity、IHC level 与 ppm 放到同一连续色标中。

### 5.6 QTL

摘要按 `source × QTL type × tissue/context` 展示 record count。点击单元格进入分页明细。GTEx 标记为 official significant pairs；QTLbase 标记为 associations，不能因出现在 QTL 表中就统一称为 significant。

### 5.7 Interaction

摘要按 `source × context class × context` 展示 evidence records 和 distinct native interaction IDs。点击进入独立明细页。专题 context 只说明数据策展归属，不宣称该互作在相应组织或疾病体内活跃。

### 5.8 Disease

按来源建立独立证据卡片：ClinGen gene–disease validity、ClinGen dosage、GenCC assertion、OMIM gene–disease。HPO phenotype 作为 disease row 的展开内容。不同来源不投票、不合并 classification；MONDO 只用于分组和导航。

用户原思路中的 `clinCC` 在现有 View 中没有同名表；初版按 `GenCC` 解释，并与 ClinGen 明确分开。

## 6. 参考产品转化为 memVar 的设计原则

### CATVariant 可借鉴的部分

- 蛋白/基因为入口，结果页按蛋白上下文组织；
- 序列与区段/位点注释同屏，用户可从总览缩放到局部；
- 区间与点位采用不同视觉语法。
- 序列图、可搜索变异表和其他证据面板联动；选中 residue/variant 后，其他区域进入同一上下文。
- 对同一蛋白提供 variant prevalence、estimated impact 等不同 lens，而不是把所有指标同时编码到一条序列上。
- residue/range/variant 搜索、全蛋白 density navigator 和固定 site selection 适合直接转化为 memVar 的序列工具。

memVar 不能直接照搬单轨序列：本站同时拥有百万级 conservation/site 与高密度 variant，需要 overview、轨道开关、聚合 marker 和局部渲染。

### ProtVar 可借鉴的部分

- 把 genomic variant、protein consequence 与 isoform consequence 分层；
- 默认展示代表/canonical 结果，其他 transcript 或 isoform 通过展开查看；
- 变异级事实和蛋白效应分离，避免重复基本字段。

ProtVar 2.0 当前支持从 UniProt、gene、Ensembl、RefSeq 和 PDB 等对象浏览；其 canonical-first、isoform-expand 模式与 memVar 的蛋白入口一致，但 memVar 的主坐标必须明确写作 UniProt canonical protein，而不是含糊地写“canonical transcript”。

### VarSome 可借鉴的部分

- 来源分区、折叠卡片、证据 badge 与外部链接；
- 每个来源保留自己的字段和解释语境；
- 用摘要引导用户，而不是把所有原始列一次性铺开。

memVar 不采用跨来源自动分类器，也不将来源颜色误当作证据强弱。

## 7. 调研依据

- [CATVariant](https://catvariant.com/)、[KCNH2/hERG 公共结果页](https://catvariant.com/genes/KCNH2)、[官方文档](https://catvariant.com/documentation) 与 [Nucleic Acids Research 论文](https://academic.oup.com/nar/article/54/W1/W226/8693974)：蛋白入口、canonical sequence map、可搜索变异表及联动证据视图。
- [ProtVar 2.0 release](https://www.ebi.ac.uk/ProtVar/release) 与 [ProtVar help](https://www.ebi.ac.uk/ProtVar/help)：当前检索对象与功能说明。
- [ProtVar publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC11223857/)：canonical mapping 与 isoform 展开模式。
- [VarSome Clinical Cards](https://docs.varsome.com/en/clinical-cards)：来源卡片、compact view 与证据展开模式。
- [VarSome custom transcript](https://docs.varsome.com/en/custom-transcript-for-annotation)：transcript 选择模式；memVar 仅借鉴层级，不照搬临床分类优先级。
- [ClinGen classification definitions](https://www.clinicalgenome.org/docs/gene-disease-validity-classification-information/)：gene–disease validity 分类语义。

参考产品用于交互和信息层级调研，不作为 memVar 数据来源；网站运行时只读取本地 View 的派生产物。

## 8. 明确不进入初版的内容

- 以 genomic variant 为首页入口的全站 variant search；
- 用户账户、上传、批量注释和临床判读；
- 在线修改或回写 View；
- 将 AlphaGenome 作为主结果层；
- 将 MaveDB 异构 assay score 合并成统一数值列；
- 自行生成跨来源 variant priority/clinical score；
- 结构三维展示和 isoform-to-canonical 序列对齐。

这些功能可在蛋白中心 MVP 稳定后单独立项。
