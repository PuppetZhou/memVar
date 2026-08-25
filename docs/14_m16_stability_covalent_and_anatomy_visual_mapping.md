# 14. M16 Stability、Covalent pair 与 Anatomy 视觉及组织映射合同

状态：M16 已实施（2026-08-21）  
范围：Variant 列优先级、Sequence ΔΔG 波形与逐替换交互、Covalent pair 配色、BioRender Anatomy navigator，以及 Expression/GEN/QTL 的显式 tissue crosswalk。

> M18 覆盖说明（2026-08-24）：第 2 节所有 Anatomy landmark/marker/dot/label overlay 合同已被项目负责人明确暂停。当前页面只把完整人体图作为 orientation background，并通过文字 tissue index 选择标准区域；不得绘制或暗示精确组织坐标。Covalent 连接同时升级为分层弧线路由；当当前蛋白全部显式记录均为 disulfide 时，类型只汇总显示一次。当前有效合同见 `16_m18_premium_visual_refinement_plan.md`。

## 1. 冻结的展示决策

### 1.1 Variant 列顺序

Variant 表按以下顺序展示：

1. Variant (GRCh38)
2. Protein effect
3. Consequence
4. Sources
5. AlphaMissense
6. gnomAD joint AF
7. Predicted stability ΔΔG
8. dbSNP

ThermoMPNN 是蛋白稳定性模型证据，不是变异身份或主要临床结论，因此不得放在 Protein effect 后的第三列。详情中的 ThermoMPNN card 仍与 ClinVar、COSMIC、AlphaMissense 分离。

### 1.2 Stability ΔΔG 波形

- 负值（`≤ -0.5 kcal/mol`，predicted stabilizing）：`#1B75BC`；
- 中间带（`-0.5 < ΔΔG < +0.5`，small predicted change）：`#7A838C`；
- 正值（`≥ +0.5 kcal/mol`，predicted destabilizing）：`#D94949`。

Sequence 使用中位数的连续平滑波形，不使用永久散点。曲线只是相邻可用 site/bin 的视觉连接，不进行缺失位点插值，也不把波形解释为连续实验测量。完整蛋白尺度仍显示有界 bin；viewport `≤ 500 aa` 时显示逐位点数据。

鼠标、键盘焦点或触摸选择一个逐位点波形位置后，浮层必须展示：

- canonical site；
- 当前位点 `ddg_min`–`ddg_max`；
- median 与 distinct substitution count；
- 每一种实际预测的 `Ref + position + Alt`、ΔΔG 和方向。

逐替换明细由 `/api/v1/proteins/{acc}/stability/sites/{position}` 按蛋白和单个位点读取，最多 19 种标准氨基酸替换；不向浏览器发送整个蛋白的 ThermoMPNN 事实表。

### 1.3 Covalent pair

每一对 linked endpoints 的连接线、两个端点和文字图例必须使用同一种颜色。基础色按顺序循环：

`#CC247C`, `#E95351`, `#F7A24F`, `#FBEB66`, `#4EA660`, `#79CAFB`, `#5292F7`, `#AA77E9`。

超过八对时以同一基础色的确定性深浅变体继续编号。颜色之外必须同时显示 `start ↔ end`，因此色觉缺陷用户仍可识别 pair。

## 2. BioRender 素材合同

Anatomy navigator 直接放大展示 BioRender 生成的正面人体器官图。网站不再使用椭圆或器官轮廓圈选人体区域，只在对应器官/富集部位叠加可点击的数据圆点。

交互视口合同：

- 桌面端人体图列宽为 `430 px`，图像视口高度为 `36–46 rem`；窄屏改为单列但保留可用高度；
- 鼠标滚轮以指针所在位置为锚点缩放，最大放大 `4×`；放大后可拖拽平移；
- 提供 `+`、`−`、`Reset` 和当前缩放百分比；双击或 `Home` 恢复完整人体图；
- 键盘可用 `+`/`−` 缩放，并在放大后用方向键平移；
- 圆点保持近似固定的屏幕尺寸，避免放大后遮挡器官；hover/focus 显示标准组织名称，click 后在右侧显示该组织的来源卡片；
- 当前来源没有数据的组织不在人体图上绘点；`other` 为非解剖/未映射汇总，只保留在文字列表中，不在人像上放置误导性坐标。

- 参考模板：[Human Internal Organs](https://app.biorender.com/biorender-templates/details/t-62ce1bec6af3c9dd2a464f54?source=mcp)
- BioRender figure ID：`6191fd4843d685255a905b95`
- slide ID：`dfb438b2-5e43-5e13-589a-25b10c97a925`
- [可编辑 BioRender figure](https://app.biorender.com/illustrations/6191fd4843d685255a905b95?slideId=dfb438b2-5e43-5e13-589a-25b10c97a925)
- 网站本地资产：`frontend/public/assets/biorender-human-anatomy.svg`

本地资产保留 figure 元数据，不依赖会过期的 signed URL。正式公开发布前应在拥有相应 BioRender 发布许可的账户中导出最终素材，并在保持路径和交互坐标不变的前提下替换本地 preview。

### 2.1 BioRender 图上点位

M17 起，点位的唯一真源为 `frontend/lib/anatomy-geometry.ts` 中的 `ANATOMY_LANDMARKS`：坐标存为原 BioRender SVG `2752 × 1536` viewBox 像素，并由 `anatomySourcePointToDisplay` 按当前 `<image preserveAspectRatio="xMidYMid slice">` 纯转换到 `200 × 350` navigator frame。器官 tissue 直接落在对应器官上；系统性 tissue 使用 `kind: "representative"` 记录有明确解剖含义的代表性位置；`other` 没有 landmark，绝不在人体图上绘制。下表保留为可读校准摘要，其显示坐标不得作为实现真源。

| 标准区域 | 坐标 | 图上位置 |
|---|---:|---|
| `brain` | 100, 34 | 脑 |
| `pituitary` | 104, 38 | 脑内垂体区 |
| `eye` | 100, 56 | 眼/面部 |
| `oral_cavity` | 100, 68 | 口腔 |
| `salivary_gland` | 91, 69 | 唾液腺区 |
| `tonsil` | 106, 72 | 扁桃体区 |
| `upper_airway` | 100, 80 | 上呼吸道 |
| `thyroid` | 100, 101 | 甲状腺 |
| `parathyroid` | 106, 104 | 甲状旁腺区 |
| `lymph_node` | 67, 137 | 腋窝淋巴结代表点 |
| `thymus` | 100, 132 | 胸腺区 |
| `lung` | 128, 147 | 肺 |
| `breast` | 137, 139 | 乳腺区 |
| `heart` | 101, 158 | 心脏 |
| `vasculature` | 96, 147 | 心脏/主动脉代表点 |
| `blood` | 106, 151 | 心血管代表点 |
| `spinal_cord` | 94, 126 | 脊髓轴线代表点 |
| `esophagus` | 100, 119 | 食管 |
| `liver` | 77, 191 | 肝脏 |
| `gallbladder` | 88, 204 | 胆囊 |
| `stomach` | 116, 201 | 胃 |
| `spleen` | 140, 210 | 脾 |
| `pancreas` | 104, 213 | 胰腺 |
| `adrenal_gland` | 132, 201 | 肾上腺区 |
| `kidney` | 132, 216 | 肾 |
| `colon` | 100, 247 | 结肠 |
| `small_intestine` | 100, 259 | 小肠 |
| `smooth_muscle` | 114, 258 | 肠道平滑肌代表点 |
| `appendix` | 78, 276 | 阑尾 |
| `uterus` | 100, 291 | 子宫区 |
| `ovary` | 87, 292 | 卵巢区 |
| `fallopian_tube` | 114, 288 | 输卵管区 |
| `placenta` | 100, 283 | 子宫/胎盘代表点 |
| `bladder` | 100, 301 | 膀胱 |
| `prostate` | 100, 311 | 前列腺区 |
| `vagina` | 100, 321 | 阴道区 |
| `testis` | 100, 338 | 睾丸区 |
| `male_reproductive_tract` | 110, 326 | 男性生殖道代表点 |
| `peripheral_nerve` | 49, 220 | 上肢外周神经代表点 |
| `skin` | 39, 202 | 上肢皮肤边界代表点 |
| `skeletal_muscle` | 146, 267 | 大腿骨骼肌代表点 |
| `adipose` | 153, 241 | 髋/大腿脂肪代表点 |
| `bone_marrow` | 142, 319 | 股骨骨髓代表点 |
| `bone` | 145, 304 | 股骨代表点 |
| `cartilage` | 151, 283 | 膝/下肢软骨代表点 |
| `connective_tissue` | 139, 252 | 髋/大腿软组织代表点 |
| `other` | 不绘点 | 非解剖或未映射条目只保留在列表 |

相近组织允许在完整视图中邻近显示；用户放大后可分辨并逐点点击。替换 BioRender 底图时，必须重新按实际导出画面校准这张表，不得沿用旧图坐标。

## 3. Anatomy 来源模式与颜色

Anatomy 支持四种独立模式：

| 模式 | 颜色 | 含义 |
|---|---:|---|
| All sources | `#52606D` + 三色标记 | 仅显示各来源是否存在，不计算总分 |
| Expression | `#1B75BC` | HPA RNA、HPA MS、HPA IHC、PaxDB availability |
| GEN | `#D94949` | GEN disease-vs-normal qualifying contrasts availability |
| QTL | `#AA77E9` | GTEx、QTLbase、eQTLGen availability |

颜色只表达当前来源有无记录或当前选择。禁止把三种来源的 record count、效应大小、显著性或量纲混合成一种人体填色强度。All sources 模式用三个独立小标记表达来源组成，不使用混色总分。

## 4. Tissue mapping method

### 4.1 输入粒度

- Expression：`expression_hpa_rna.tissue`、`expression_hpa_ms.tissue`、`expression_hpa_ihc.tissue`、`expression_paxdb.organ`；
- GEN：`differential_expression.contrast.tissue`，只统计 `protein_contrast.is_significant_with_effect = TRUE` 的 protein–contrast membership；
- QTL：`qtl_summary.tissue_or_context`，保留 `source_database` 和 `qtl_type`。

每个来源的原始 tissue/context 始终保存在 `raw_filter_terms` 中。映射只产生导航用 `body_region_id`，不改写原始来源记录。

### 4.2 标准化和匹配

匹配前只执行确定性字符串规范化：

1. Unicode 字符原样保留并 case-fold；
2. `_` 和 `-` 转为空格；
3. 首尾空白删除；
4. 连续空白折叠为一个空格；
5. 对规范化结果执行 exact lookup。

禁止 substring、编辑距离、embedding 或其他 fuzzy matching。一个规范化 raw term 只能对应一个 `body_region_id`；配置冲突会让 anatomy build 失败。新出现且未配置的词进入 `other`，并标记 `unmapped_other`，不会静默猜测。

### 4.3 当前 release 覆盖

当前配置覆盖：

- Expression：153/153 个 distinct raw terms；
- GEN：25/25 个 distinct raw terms；
- QTL：125/125 个 distinct raw terms。

其中 cell type、培养细胞、体液和无法安全定位到单一器官的 context 被显式映射到 `other`；“全部覆盖”不等于把所有词强行解释为器官。

## 5. 标准组织与完整 alias mapping

以下表中的 alias 是完成上述规范化后的 exact terms。机器可读唯一真源为 `config/anatomy_crosswalk.json`。

| body_region_id | 标准显示名 | Ontology | 规范化 raw tissue/context aliases |
|---|---|---|---|
| `brain` | Brain | UBERON:0000955 | brain; cerebral cortex; frontal cortex; brain cortex; brain frontal cortex; brain temporal cortex; brain amygdala; brain caudate; brain cerebellum; brain cerebellar hemisphere; brain hippocampus; brain hypothalamus; brain nucleus accumbens; brain pons; brain prefrontal cortex; brain putamen; brain substantia nigra; central nervous system; dorsolateral prefrontal cortex (ba46); caudate; cerebellum; choroid plexus; dorsal raphe; hippocampus; hypothalamus; substantia nigra; brain anterior cingulate cortex; brain anterior cingulate cortex ba24; brain caudate basal ganglia; brain frontal cortex ba9; brain nucleus accumbens basal ganglia; brain putamen basal ganglia |
| `thyroid` | Thyroid | UBERON:0002046 | thyroid; thyroid gland |
| `lung` | Lung | UBERON:0002048 | lung; bronchus; airway smooth muscle |
| `heart` | Heart | UBERON:0000948 | heart; heart muscle; heart atrial appendage; heart left ventricle; aortic endothelium |
| `liver` | Liver | UBERON:0002107 | liver |
| `stomach` | Stomach | UBERON:0000945 | stomach |
| `pancreas` | Pancreas | UBERON:0001264 | pancreas |
| `spleen` | Spleen | UBERON:0002106 | spleen |
| `kidney` | Kidney | UBERON:0002113 | kidney; kidney cortex; renal glomerulus; proximal tubule |
| `small_intestine` | Small intestine | UBERON:0002108 | small intestine; small intestine duodenum; small intestine ileum; small intestine terminal ileum; duodenum; ileum; jejunum |
| `colon` | Colon / rectum | UBERON:0001155 | colon; rectum; large intestine; large intestine colon; large intestine rectum; colon sigmoid; colon transverse |
| `bladder` | Bladder | UBERON:0001255 | bladder; urinary bladder |
| `skin` | Skin | UBERON:0002097 | skin; dermis; epidermis; hair; skin not sun exposed suprapubic; skin sun exposed lower leg; skin (upper arm flexural left) |
| `skeletal_muscle` | Skeletal muscle | UBERON:0001134 | skeletal muscle; muscle; muscle skeletal |
| `adipose` | Adipose | UBERON:0001013 | adipose; adipose tissue; adipose subcutaneous; adipose visceral; adipose visceral omentum; brown adipose tissue |
| `bone_marrow` | Bone marrow | UBERON:0002371 | bone marrow |
| `blood` | Blood | UBERON:0000178 | blood; whole blood; whole blood derived whole blood cell; peripheral blood; plasma; serum; platelet; blood thrombocytes; blood derived macrophages; peripheral blood cd14+ monocytes; blood b cell; blood b cell cd19+; blood erythroid; blood macrophage; blood monocyte; blood monocytes cd14+; blood natural killer cell; blood neutrophils cd16+; blood t cell; blood t cell cd4+; blood t cell cd4+ activated; blood t cell cd4+ naive; blood t cell cd8+; blood t cell cd8+ activated; blood t cell cd8+ naive; lymphocyte; blood meta analysis |
| `breast` | Breast | UBERON:0000310 | breast; breast mammary tissue; lactating breast |
| `uterus` | Uterus / cervix | UBERON:0000995 | uterus; endometrium; cervix; uterine cervix |
| `ovary` | Ovary | UBERON:0000992 | ovary |
| `testis` | Testis | UBERON:0000473 | testis |
| `prostate` | Prostate | UBERON:0002367 | prostate; prostate gland |
| `adrenal_gland` | Adrenal gland | UBERON:0002369 | adrenal gland |
| `appendix` | Appendix | UBERON:0001154 | appendix; vermiform appendix |
| `esophagus` | Esophagus | UBERON:0001043 | esophagus; esophagus gastroesophageal junction; esophagus mucosa; esophagus muscularis |
| `fallopian_tube` | Fallopian tube | UBERON:0003889 | fallopian tube |
| `gallbladder` | Gallbladder | UBERON:0002110 | gallbladder |
| `eye` | Eye / retina | UBERON:0000970 | eye; retina |
| `lymph_node` | Lymph node | UBERON:0000029 | lymph node |
| `oral_cavity` | Oral cavity / tongue | UBERON:0000167 | oral mucosa; tongue |
| `placenta` | Placenta | UBERON:0001987 | placenta |
| `parathyroid` | Parathyroid gland | UBERON:0001132 | parathyroid gland |
| `pituitary` | Pituitary gland | UBERON:0000007 | pituitary; pituitary gland |
| `salivary_gland` | Salivary gland | UBERON:0001044 | salivary gland; saliva secreting gland; minor salivary gland |
| `spinal_cord` | Spinal cord | UBERON:0002240 | spinal cord; brain spinal cord; brain spinal cord cervical c 1 |
| `thymus` | Thymus | UBERON:0002370 | thymus |
| `tonsil` | Tonsil | UBERON:0002372 | tonsil |
| `vagina` | Vagina | UBERON:0000996 | vagina |
| `vasculature` | Vasculature / artery | UBERON:0002049 | blood vessel; artery; artery aorta; artery coronary; artery tibial |
| `peripheral_nerve` | Peripheral nerve | UBERON:0001021 | nerve tibial; peripheral nervous system |
| `bone` | Bone / intervertebral disc | UBERON:0001474 | bone; intervertebral disc |
| `cartilage` | Cartilage | UBERON:0002418 | cartilage |
| `smooth_muscle` | Smooth muscle | UBERON:0001135 | smooth muscle; muscle smooth |
| `connective_tissue` | Connective / soft tissue | UBERON:0002384 | soft tissue |
| `male_reproductive_tract` | Male reproductive tract | UBERON:0000079 | efferent ducts; epididymis; seminal vesicle |
| `upper_airway` | Upper airway | UBERON:0001004 | nasopharynx |
| `other` | Other / non-anatomical | — | n/a; whole organism; astrocyte; keratinocyte; skin fibroblast; fibroblast; cells cultured fibroblasts; cells ebv transformed lymphocytes; stem cell ipsc; brain derived ipsc neural progenitors; egg cell; amniotic fluid; cerebrospinal fluid; urine; saliva; mouth saliva; mouth sputum; synovial tissue; valve interstitial cell; dendritic cells; epithelium |

## 6. Build 与运行时边界

`etl/build_anatomy.py` 在离线阶段完成 exact crosswalk 和 protein-scoped aggregation，输出 `data/generated/anatomy/anatomy_summary.parquet`。普通 protein 页面只按 accession 查询该 summary；不得在请求时扫描 Expression、GEN 或 QTL 大表。

Anatomy API 返回每个标准区域下分离的 `layer/source_database/modality_or_type/record_count/raw_filter_terms`。前端可以按 layer 筛选可用性，但不得创建跨 layer 的 magnitude、排名或统一显著性。

## 7. 验收

- EGFR/P00533 在 Blood、Heart、Kidney、Skin 或 Breast 中能看到独立 GEN card；
- Expression、GEN、QTL 模式颜色不同，All mode 不合成强度；
- raw tissue/context 可在 card 中追溯；
- Stability 在 R252 显示 6 种替换及精确 ΔΔG；
- Covalent pair 的两个端点、连接线和 `start ↔ end` 图例同色；
- Variant 表中 ΔΔG 不位于第三列；
- BioRender 底图不依赖运行时外部 URL；
- 人体图不存在椭圆覆盖层，可滚轮缩放、拖拽平移、恢复完整视图，并能从组织圆点选择区域。
