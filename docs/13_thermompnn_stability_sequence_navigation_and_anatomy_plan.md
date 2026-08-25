# 13. ThermoMPNN 稳定性、Sequence navigator 与人体组织导航计划

状态：M15 已实施（2026-08-21）  
范围：ThermoMPNN ΔΔG 数据接入、Variant/Sequence 展示、全长序列范围选择修复，以及 Expression/GEN/QTL 的 anatomy navigator。

实施验收：全量 variant branch 保留 7,376,098 条预测和 7,234 个蛋白；其中 31 条预测涉及当前 canonical sequence reference mismatch，仍保留在蛋白特异 Variant branch，但依照既有 canonical drawable 规则不进入 Sequence track。因此 Sequence summary 包含 7,376,067 个 genomic predictions、7,192,298 个 distinct substitutions 和 3,432,453 个 drawable canonical sites。P00533/N338H 为 `-0.0606794357 kcal/mol`。Anatomy 使用 website-owned exact crosswalk，生成 926,903 行 protein-scoped source summary；未显式映射术语保留原词并进入 `other`。后端普通请求只读上述 website-generated branches，不访问只读上游。

## 1. 目标与非目标

### 1.1 目标

1. 将只读的 ThermoMPNN canonical single-amino-acid substitution 预测纳入网站生成数据。
2. 在 Variant 主表与详情中展示每个可用预测的 ΔΔG，同时保留明确的模型、单位、符号与适用范围。
3. 在 Sequence 中增加多尺度 stability track，正确表达一个 canonical site 上多个氨基酸替换的分布。
4. 将现有“只能继续缩短”的 range selector 改为始终以完整 canonical sequence 为坐标底图的双手柄 navigator。
5. 为 Expression、GEN differential expression 与 QTL 增加共享的人体组织导航入口，同时保持来源词汇和测量量纲分离。

### 1.2 非目标

- 不把 ThermoMPNN ΔΔG 称为 fitness、function、pathogenicity 或 clinical score。
- 不把 ThermoMPNN 与 AlphaMissense、ClinVar、COSMIC 或保守性合成一个 variant priority。
- 不为 synonymous、stop、frameshift、indel、isoform-only effect 或结构参考残基不一致记录伪造预测。
- 不执行 site-saturation mutagenesis；M15 只展示当前已计算的 observed canonical variant substitutions。
- 不跨 HPA RNA、HPA MS、HPA IHC、PaxDB、GEN 与 QTL 计算统一 tissue score。
- 不在代码中嵌入远程 BioRender 模板或许可未确认的导出物。

## 2. 已冻结的 ThermoMPNN 语义

当前只读上游：

```text
/home/xuyzh/memVar/MPNN-predict/result/
├── thermompnn_variant_predictions.parquet
└── variant_targets.parquet
```

当前 release 口径：

| 项目 | 数量 |
|---|---:|
| genomic variant predictions | 7,376,098 |
| distinct protein substitutions | 7,192,328 |
| canonical sites | 3,432,470 |
| proteins | 7,234 |

`thermompnn_variant_predictions.parquet` 的身份为
`variant_key + uniprot_accession`。网站不得只按 `variant_key` 连接预测。

`ddg_pred` 的公开语义固定为：

- 名称：`ThermoMPNN predicted stability change (ΔΔG)`；
- 单位：`kcal/mol`；
- 负值：predicted stabilizing；
- 正值：predicted destabilizing；
- `NULL`：not predicted，绝不解释为 0；
- 模型预测不是实验测量或临床结论。

首版显示分组是展示规则，不创建新的科学结论：

| 范围 | 显示标签 |
|---|---|
| `ddg <= -0.5` | Predicted stabilizing |
| `-0.5 < ddg < 0.5` | Small predicted change |
| `ddg >= 0.5` | Predicted destabilizing |

## 3. 数据构建合同

### 3.1 数据边界

M15 builder 可将 `/home/xuyzh/memVar/MPNN-predict/result` 配置为版本化、只读上游。不得修改、重排或向该目录写缓存。所有网站派生物仍只写入：

```text
/home/xuyzh/memVar/website/data/generated/
```

Production runtime 只读取网站生成数据，不直接读取 `MPNN-predict`。

### 3.2 输入契约检查

Builder 必须在发布前验证：

1. 两个输入 Parquet 存在且包含冻结字段；
2. `variant_key`、`uniprot_accession`、`pdb_name`、`ddg_pred` 非 NULL；
3. `ddg_pred` 是有限数值；
4. `variant_key + uniprot_accession` 在最终预测中唯一；
5. 最终预测能一对一连接 `variant_targets`，且 PDB 文件名一致；
6. `canonical_position` 是 1-based 正整数，Ref/Alt 为不同的标准氨基酸；
7. 预测只连接到相同 `uniprot_accession` 的网站 canonical membership；
8. 输出路径不在 `View/` 或 `MPNN-predict/` 内。

### 3.3 网站派生产物

新增 source-specific branch：

```text
data/generated/variant/source/thermompnn/
└── accession_bucket=000..127/*.parquet
```

字段：

```text
page_accession, accession_bucket, variant_key,
canonical_position, ref_aa, alt_aa,
ddg_pred, unit, pdb_name, model_name
```

新增 sequence site summary：

```text
data/generated/sequence/stability_site/
└── accession_bucket=000..127/*.parquet
```

每个 `uniprot_accession + canonical_position` 一行：

```text
uniprot_accession, accession_bucket, canonical_position, ref_aa,
distinct_substitution_count, genomic_variant_count,
ddg_min, ddg_q25, ddg_median, ddg_q75, ddg_max,
stabilizing_count, small_change_count, destabilizing_count
```

位点聚合必须先按
`uniprot_accession + canonical_position + ref_aa + alt_aa` 去重。多个 genomic variant 产生相同 amino-acid substitution 时只进入分布一次，但保留 `genomic_variant_count` 供详情解释。

### 3.4 来源注册

`source_registry.yaml` 新增 `thermompnn_stability`，包含模型名、输入结构为 AlphaFold DB v6、本地计算 release、record grain、单位、符号和“not fitness / not clinical evidence” caveat。

## 4. Variant 展示合同

### 4.1 主表

在 Protein effect 后增加 `Predicted stability ΔΔG` 列：

- 数字使用符号和两位小数，例如 `+1.24 kcal/mol`；
- 数字旁显示以 0 为中心的短条；
- stabilizing 使用冷蓝，small change 使用中性灰，destabilizing 使用琥珀；
- 不使用 ClinVar P/LP 的红色；
- 缺失显示 `— Not predicted`；
- compact 与 full variant browser 使用相同语义。

主表项目增加窄模型：

```text
stability_prediction: {
  source, ddg, unit, direction, model_name
} | null
```

### 4.2 详情

Variant detail 新增独立 `ThermoMPNN stability prediction` card，展示：

- exact ΔΔG；
- display direction；
- canonical substitution；
- AlphaFold PDB fragment；
- 模型与来源说明；
- “prediction is not functional or clinical evidence” caveat。

不得把 ThermoMPNN 记录放入 ClinVar/COSMIC branch，也不得改变 source badge 的原始事实语义。

### 4.3 站点预览

Sequence site preview 的每个有预测 substitution 可显示 ΔΔG。相同 Ref→Alt 对应多个 genomic variants 时，可显示一次 substitution summary，并保留打开完整 Variant 表的入口。

## 5. Sequence stability track

### 5.1 全长概览

在 Variant track 下方增加 `Stability ΔΔG`：

- 0 是固定中心基线；
- 全长使用与现有 overview 相同的 bounded bins；
- 每个 bin 返回 observation/substitution count、min、Q25、median、Q75、max；
- 默认以 median 折线和 Q25–Q75 半透明带表达波动；
- 缺失 bin 断开，不连接到 0；
- display y-domain 固定为 `-3..+3 kcal/mol`，越界使用端点三角，tooltip 返回真实值。

### 5.2 放大视图

当 viewport 不超过现有 detail window 上限时，按 residue 返回：

- `min–max` vertical whisker；
- median dot；
- Q25–Q75 band；
- distinct substitution count；
- stabilizing/small-change/destabilizing counts。

点击位点后，drawer 按 ΔΔG 排序列出 distinct Ref→Alt substitutions；缺失位点显示明确空态。

### 5.3 颜色与可访问性

- stabilizing：蓝；destabilizing：琥珀；near zero：灰；
- 所有状态同时使用文字或形状；
- tooltip、键盘focus和click/touch行为一致；
- 不把正负方向描述为 beneficial/deleterious。

## 6. Full-length sequence navigator

现有 range selector 的错误原因已经冻结：pointer coordinate 和高亮几何都相对当前 viewport，而不是完整 canonical length。

M15 navigator 必须：

1. 底轨始终代表 `1..canonical_length`；
2. 当前 viewport 按完整长度比例显示为窗口；
3. 左右手柄分别调整 start/end；
4. 拖动窗口主体进行 pan；
5. 在空白底轨拖动可创建新窗口；
6. 扩大选择可恢复到完整长度；
7. `Home`、双击和 `Full length` 都恢复 `1..length`；
8. `+/-` 和方向键继续支持 zoom/pan；
9. 所有操作使用 1-based closed canonical coordinates；
10. navigator viewport 与 site/range selection 是不同状态，不互相静默重写。

回归用例至少覆盖：

- length 1210、viewport 300–500 时，底轨两端仍映射为 1 和 1210；
- viewport 300–500 的 thumb 左侧约 24.7%，宽约 16.6%；
- 从缩短窗口可以拖回 1–1210；
- EGFR `?site=338` 不改变 navigator 的全长坐标底图；
- 长蛋白、触屏pointer cancel和键盘Home。

## 7. Anatomy navigator

### 7.1 产品位置

在 Expression 前增加 protein-scoped `Anatomy navigator`。人体图是跨证据导航，不是新的综合证据层。

选择 body region 后显示三个来源独立的 summary：

1. Expression：HPA RNA、MS、IHC、PaxDB，各自保留单位与颜色标尺；
2. GEN：匹配组织的 datasets/contrasts 数量与入口；
3. QTL：GTEx/QTLbase 按 source/type 的记录数；eQTLGen 保留 blood meta-analysis context。

人体图默认填色只表达 `has data / no data / selected`。只有用户进入单一 modality 模式时，才可用该 modality 自己的数值标尺着色。

### 7.2 Anatomy crosswalk

新增 website-owned 显式配置，替代 substring matching 作为科学映射依据：

```text
source_database, raw_term, display_label,
body_region_id, ontology_id, mapping_status, mapping_note
```

规则：

- 原始 tissue/organ/context 始终随记录返回；
- 允许多个来源词汇映射到同一 display region，但不宣称测量生物学等价；
- cell line、cultured cell、whole organism、无法定位的 context 进入明确的 non-anatomical/other 分组；
- 不用 fuzzy matching 自动创建映射；
- one-to-many anatomy mapping 必须明确列出，不静默取第一个。

首版 `body_region_id` 至少覆盖：brain、thyroid、lung、heart、liver、stomach、pancreas、spleen、kidney、small_intestine、colon、bladder、skin、skeletal_muscle、adipose、bone_marrow、blood、breast、uterus、ovary、testis、prostate 与 other。

### 7.3 SVG 与 BioRender

- 首版交互使用本地、可访问、带稳定 `body_region_id` 的原创 schematic SVG；
- 每个可点击 path 有键盘focus、文字label和非颜色选中状态；
- BioRender `Human Internal Organs` / `Organs with Callout` 只作为视觉参考；
- 用户后续提供许可明确的导出素材时，可替换 SVG implementation，但 organ ID、crosswalk 与交互合同不变。

### 7.4 URL 与联动

选择状态写入 URL，例如 `?anatomy=lung`。点击来源卡片时滚动到相应 section，并应用来源原始 tissue filters；清除 anatomy selection 不清除 sequence site selection。

## 8. 接口与响应上限

新增或扩展的 HTTP interface 必须保持 summary-first：

- Variant list 每行最多返回一个窄 stability object；
- Sequence overview 不返回 variant/substitution事实行；
- residue-level stability 只在 bounded window 返回；
- anatomy summary 返回聚合与可用 filter keys，不返回全部 Expression/QTL/GEN facts；
- 所有 source、unit、coordinate、mapping_status 与 count grain 必须显式。

## 9. 实施顺序

### A. Data vertical slice

1. 增加 builder 输入参数与只读路径保护；
2. 生成 ThermoMPNN branch 与 stability site summary；
3. 注册来源；
4. 用 P00533/N338H 验证 `ddg = -0.060679`。

### B. Variant vertical slice

1. 扩展后端模型与 list/detail/site-preview；
2. 增加表格列、短条、详情卡；
3. 验证 predicted、not-predicted 与错误 accession join。

### C. Sequence vertical slice

1. 扩展 overview bins 与 bounded site response；
2. 增加 stability track 和site drawer；
3. 保持现有 variant/ClinVar/JSD count conservation。

### D. Navigator fix

1. 提取 full-length geometry pure functions；
2. 先写失败回归测试；
3. 实现双手柄、pan、create-window与reset；
4. 验证 mouse、keyboard、touch。

### E. Anatomy vertical slice

1. 建显式 crosswalk 和contract tests；
2. 生成 protein-scoped anatomy summaries；
3. 增加原创 SVG、source cards、URL状态和section联动；
4. 用 lung、brain、blood、other 和无记录蛋白验收。

## 10. 验收标准

### 数据正确性

- 预测只从配置的只读 MPNN source 读取；
- `variant_key + accession` join 不串蛋白；
- current release 的 7,376,098 行预测无丢失或重复；
- site aggregation 对相同 Ref→Alt 去重；
- NULL 不显示为 0；
- 负/正 ΔΔG 方向、单位和模型来源贯穿 ETL→HTTP→UI。

### UI

- Variant 表能区分 predicted 与 not predicted；
- Sequence track 对多替换显示分布，不伪造单值；
- range navigator 缩短后可通过拖动恢复全长；
- anatomy map 不能生成跨模态统一强度；
- 所有颜色都有文字/形状冗余；
- P00533 `site=338` 的 sequence、variant table 和 stability detail 保持联动。

### 性能与回归

- 普通 protein overview 不扫描全量 ThermoMPNN 输入；
- long-protein overview 响应仍有界；
- Variant、Sequence、Expression、GEN、QTL 现有测试继续通过；
- 新增 ETL、HTTP、navigator geometry、anatomy mapping 测试；
- backend pytest、full-stack verification 与 frontend production build 通过；
- `View/` 与 `MPNN-predict/` 没有被修改。

## 11. 推荐视觉参考

BioRender 搜索中与本任务最接近的模板：

- Human Internal Organs；
- Human Organs with Callout；
- Internal Organs with Callouts；
- Human Body with Organs Comparison。

它们仅用于构图和视觉密度参考。交互实现不依赖 BioRender runtime。
