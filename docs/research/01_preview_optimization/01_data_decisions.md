# 01 数据处理与补充：需要敲定的选择

核对：2026-09-22。用户本轮授权制定55条问题的解决方案，并希望先明确还需敲定的数据事项；视觉方向明确尝试Figma与React Bits。本文件维护科学选择的证据、推荐和未决状态，不直接修改正式规则。工程实现细节由实施任务自行决定。

入口：[问题清单](issues.md) · [逐项解决方案](../../plan/01_preview_optimization/01_solutions.md) · [视觉与动效方案](../../plan/01_preview_optimization/02_figma_motion.md)。D01/D02已确认膜范围与方法；D03已取消全转录本补全，D04已确认保留代表转录本ID与UniProt序列匹配标注。D05～D07已于2026-09-22获用户确认，剩余已列任务授权继续实施；序列比较方法的具体实现另作定向核查，不重开代表转录本选择。

## 已查明的事实

1. foundation来源配置为UniProt **2026_03**，查询`proteome:UP000005640 AND reviewed:true AND keyword:KW-0472`。原始query_manifest记录**7,732**个accession，已有规则排除17个无HGNC引用条目，正式范围为**7,715**。[来源清单](../../../../modules/foundation/data/raw/uniprot/2026_03/query_manifest.json)、[既有排除规则](../../../../modules/foundation/docs/rules.md)。用户已澄清7,741只是方法示例，实际按本地2026_03统计，无需追索该示例来源或比较集合差异。
2. 当前variant仅保留代表SNV、编码/蛋白后果且HGVSp非空集合。正式`variant_vep`也只有代表annotation_id；旧**2,195,301,103**条全VEP后果的衍生产物已按先前授权清理，原始来源、参考和脚本仍保留。[结果](../../../../modules/variant/docs/result.md)、[契约](../../../../modules/variant/docs/data_contracts.md)。用户随后取消全转录本补全，本阶段不重建这些衍生表；现有代表注释足以作为Transcript ID展示和序列关系构建的起点。
3. 本地ClinVar summary为2026-09-06来源，读取表头确认有RCVaccession、PhenotypeIDS、PhenotypeList、VariationID及三类临床标签/SCV引用字段；**不能由这些并列汇总列推断每个疾病对应哪个独立分类/提交**。RCV是variant–condition层级，VCV是variant汇总；条件集合、胚系/体细胞/致癌性需分别处理。[既有方法](../../../../modules/disease/docs/plan.md#clinvar后续归类原则与方法只记录不执行)、[NCBI说明](https://www.ncbi.nlm.nih.gov/clinvar/docs/variation_report/)。本轮只读表头，没有宣称RCV/XML已收集完整。
4. OPM详情已接入服务层；GO服务表保留reference；前端有predictor-guides字典。它们首先是已有字段/关系的接入与解释问题，不应一律立为新采集任务。结构组件已有Conservation/JSD和surface入口，先复现用户体验再修复。

## 已确定方法与待敲定事项

### D01：膜蛋白集合与版本——已敲定（MEM-03）

用户确认其分类数字只是方法论示例；类型保持，本地UniProt2026_03为版本依据，按本地实际数量（可沿用排除后）统计。沿用已确认的17项无HGNC排除规则及当前7,715个正式蛋白，不扩大收录、不采集新版、不把7,741作为验收目标。本项不再提问，也不重开17项排除决定。

### D02：膜分类方法——用户授权Agent制定，已选实施方案（MEM-01～02）

保持指定树：整合膜→跨膜（单次/多次）及脂锚；外周排除整合；其余“膜相关、机制未注释”单列。采用与当前身份及位点对象相容的判据：

- TM用当前canonical上的UniProt Transmembrane feature，按唯一feature计区段，1段为单次、2段及以上为多次。其他isoform的片段不累加到canonical，也不用预测代替来源分类。
- 脂锚用适用的条目通用/canonical定位topology（SL-9901/SL-9902/SL-9920）或canonical Lipidation中明确GPI-anchor；沿用现有证据适用范围。泛脂化关键词不直接推断锚定；保留为原注释，不扩充主类证据。
- 互斥主分支按TM优先、非TM脂锚、排除整合后的SL-9903外周、余项依次赋值；所有原始标签仍作为证据保留。整合是前两分支的父类，不能再与子类相加当总数。
- 单列“膜相关、机制未注释”，不把没有机制证据解释为外周。这一操作选择在用户授予的方法权限内，不再请求决定。

对已发布标签及当前feature做一次有界只读重分组，结果为：

```text
膜蛋白 7,715
├─ 整合膜蛋白 5,654
│  ├─ 跨膜蛋白 5,213
│  │  ├─ 单次 2,380
│  │  └─ 多次 2,833
│  └─ 脂锚定蛋白（非TM）441
├─ 外周膜蛋白（排除整合）1,015
└─ 膜相关、机制未注释 1,046
```

16条目同时命中TM/脂锚，主类归TM；22条目同时命中整合/外周，主类归整合。该层级按canonical/条目通用来源证据定义，页面需说明对象，不能声称涵盖每个isoform的膜类型。计数试算通过后已于2026-09-22正式发布：membrane同时保存互斥主分类与原标签证据，Web/PostgreSQL改用主分类作为筛选和统计入口；位置观测/预测未重算。[正式规则与结果](../../../../modules/membrane/docs/basic_membrane_labels.md)、[Web交付](../../record/01_preview_optimization/20260922_membrane_classification_v1.md)。原[试算脚本](../../../../modules/membrane/runs/20260922_classification_preview_01/preview.py)和[报告](../../../../modules/membrane/runs/20260922_classification_preview_01/report.json)继续作为发布前探索依据。

### D03：全转录本补全——已取消（VA-03～05）

**2026-09-22用户决定：** 放弃全转录本补全，继续以当前选定的代表转录本为注释主体，保留Transcript ID和isoform映射标注。替代本文件此前“对当前变异重建全部转录本后果”的建议。

保留当前10,866,094个variant及既有代表后果范围，沿用MANE Select优先、仅基因无Select才fallback至Ensembl canonical的规则。不重跑全转录本VEP、不新增全后果明细表或“所有转录本”切换，也不恢复此前排除的变异。VA-04保留原问题与取消原因供追溯，不能标为已实现。

### D04：代表转录本与UniProt序列匹配标注——已按保守精确法发布（VA-05～06、ST、MF）

**2026-09-22用户决定：** 代表转录本注释与UniProt序列匹配是两个独立层次。实际注释仍依当前代表ENST；补充说明该ENST所编码蛋白是否匹配UniProt canonical或某个isoform，以及具体目标和状态。匹配多个UniProt序列不表示新增了多个转录本后果；匹配失败不触发更换代表转录本或删除变异。生效边界由[variant规则](../../../../modules/variant/docs/rules.md#代表转录本与uniprot序列关系)维护。

**实施路径：** 从现有代表ENST/ENSP及固定Ensembl116参考取得对应蛋白序列，先按唯一代表序列建立与本地UniProt2026_03候选序列的比较关系，再回连代表后果；不对每个变异重复比较序列。foundation维护序列身份/版本与候选关系，variant维护代表后果关联，Web展示具体ENST、ENSP、选择依据、UniProt accession/isoform及匹配状态。来源提供的版本与由固定参考补充的版本分别记录。

采用全长氨基酸序列精确相等，保留多个满足条件的目标；可比较但不相同、缺少输入序列、尚未比较分别记录。候选基因关系不等于序列匹配；未匹配结果仍有可见入口。不设相似性阈值，也不把序列相等自动用于变异残基投影。

序列级关系和位点级映射分开。只有位置与ref AA核对成立才挂接对应UniProt位点/结构注释；页面保留原代表坐标，若提供目标坐标则另列。转录本相关预测继续按代表上下文解释，不因命中多个isoform而广播评分。2026-09-22已发布[foundation精确关系与状态](../../../../modules/foundation/docs/result.md)，Web独立服务表、PostgreSQL、详情API和页面已接入；[执行与验证](../../record/01_preview_optimization/20260922_parallel_web_execution.md)。实际桌面点击验收待补。

### D05：ClinVar条件专区范围与证据粒度——已确认（DI-03～04）

**2026-09-22用户确认：** ClinVar专区只纳入SNV，采用本次建议的当前入库SNV范围；增加condition列表→关联变异/位置/疾病ID展开，保留全部条件及原临床类别，默认不只挑P/LP；按原条件ID/条件集合检索，来源未指定与非疾病表型单列。补充与当前来源版本相容的RCV/SCV关联资产，能追到具体variant–condition分类再展示为疾病证据。若只能获得新版，独立登记新快照并比较变化，不与9月6日summary静默混合。

**不需要重新决定的原则：** 不把VCV总体分类复制给每个条件；胚系、体细胞临床影响和致癌性分开；多条件集合拆成员供检索不变成各成员独立判断；不按名称自行统一疾病。[模块已记录原则](../../../../modules/disease/docs/plan.md#clinvar后续归类原则与方法只记录不执行)。

**执行边界：** 当前SNV范围＋条件级来源补充已获授权，不扩展indel/CNV或变异实体集合。仅有summary的阶段可呈现原条件线索，但不能标作完整条件级断言。具体下载渠道、解析、分页由实现决定；不再为本项重复确认。生效规则见[disease规则](../../../../modules/disease/docs/rules.md#clinvar-snv条件专区2026-09-22确认)。

**实施结果（2026-09-22）：** 只采集官方同周RCV XML，完整解析后仅按当前SNV的VariationID×AlleleID与summary原accession建立正式RCV/SCV关系；condition成员只作原名/ID导航，分类保留在完整RCV TraitSet与具体SCV。summary accession无版本，XML版本标为观察值；summary未列出的嵌套SCV和原summary无RCV均明确留状态。正式数据见[disease结果](../../../../modules/disease/docs/result.md)，Web服务表、API与页面见[执行记录](../../record/01_preview_optimization/20260922_parallel_web_execution.md)。桌面点击验收待补。

### D06：Expression热图的统计对象——已确认（EX-03～04）

**已确定：** 不能要求读者翻699页样本，需热图和测量类型选择。**推荐：** 默认展示来源已提供的组织/细胞汇总值；对HPA cancer sample RNA保留逐样本热图，按癌种/组织分组导航，hover显示原值、单位、样本和来源。单蛋白界面的一格必须能说明是样本值还是来源汇总值；分类组可按数量展开，不凭空构建跨蛋白矩阵。

**2026-09-22用户确认：** 按建议增加项目计算的组中位数概览，并对非负RNA量采用明确标注的`log1p`显示色标。允许同一来源/测量/单位内的中位数作为单独“项目汇总”视图，逐样本及缺失数仍可查；RNA压缩色标只改变显示，hover保留原值。MS、染色等级等使用各自量纲，不跨来源共用绝对数值色标或默认做z-score。采用新统计后仍保留原始热图。生效规则见[expression规则](../../../../modules/expression/docs/rules.md#表达热图与项目中位数2026-09-22确认)。

### D07：结构展示优化——已确认不做预测（ST-03）

**2026-09-22用户确认：** 不进行口袋预测，诉求仅为结构展示优化。保留Ribbon、完善Surface、模式/配色一致性、序列选区与结构联动。

可展示来源已有结合位点，不新增口袋算法、计算或采集任务，也不把表面凹陷或PeSTo界面评分标成已验证药物口袋。此项不再保留为待用户选择的预测任务。

## 可以直接形成方案、不必逐项重新确认的部分

- 来源标签、字段命名/删除、GO文献外链与代码解释、Reactome证据前置、返回/清除选择、来源勾选和简短说明，用户已有明确要求。
- OPM按现有已验证映射展示原结构/链证据，不重新计算膜几何；未定位记录保留可访问入口。
- PTM统计同时提供独立位置、位置×类型、来源记录，主数字标明“已定位PTM位点”，不会把来源重复当作独立实验；不同层次分别计数，不增加可信度阈值。
- 药理分布主图按现有药理作用记录的type/action统计，并列给独立ligand数；三类record_type分别处理，不能把配对/详情重复计作作用实验。未知action单列，暂不造跨来源统一药理分类。
- 计数色档可先按用户示例做`0 / 1 / 2–4 / 5 / 6 / 7–8 / ≥9`展示原型，明确这是显示分档，保持科学数据不变；原数值可读。
- 预测介绍、范围和方向复用来源依据，不建立新的合议致病评分；缺失与未匹配用清楚状态呈现。

以上是本轮提出的具体实施建议，后续按任务授权实施；若实际字段核查揭示新的科学歧义，只重开对应项，不把每个颜色、SQL或组件选择都交给用户决定。
