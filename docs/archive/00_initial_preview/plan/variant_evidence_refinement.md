# Variant Browser 与证据面板精修

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-21。用户明确授权本轮直接优化：精简 Genomic variant、Position 前置、ClinVar 分层、Population/Prediction/Stability 上色、Transcript 减少默认文字。范围为现有数据的呈现；后续同日追加工具指南，并根据最新反馈恢复独立预测列、收紧布局与复用分布图，API移除12字段展示上限，仍仅允许已发布字典字段。不改变PostgreSQL、正式数据、代表后果、关联范围或来源分类。

## 现行展示方案

| 区域 | 默认内容 | 展开内容与交互 |
| --- | --- | --- |
| Variant 主表 | GRCh38 仅列头标注；单元格为 chromosome:position 与 ref→alt；随后 Position（仅位点数字）、Ref、Alt，不在Position下重复蛋白替换 | 完整 variant ID 在标题提示与详情保留，主列去掉重复 HGVSc |
| ClinVar | 胚系、oncogenicity、somatic impact 分区；原分类与各自 review 星级；origin 标签和提交机构数 | conditions 默认三项；MedGen/MONDO/MeSH/HPO 等按命名空间分组；RCV 与三种 assertion 域的 SCV 分开，超过五个 ID 展开；原始字段可查 |
| Population | overall AF、AC/AN、有 AF 的 ancestry group 数；群体细条 | 色相为固定 log10(AF) 连续尺度，非致病类别；群体条宽按当前变异最高 AF 线性比较。来源、filters 按需打开 |
| Prediction | 主表每个predictor独立纵列，固定紧凑身份列、评分列至少136px；详情保留分数可用性/来源 call 环图、方法组覆盖条和每页九张原分数卡 | 按 call、group、tool/field 搜索，默认隐藏缺失；可查看缺失和翻页。AlphaMissense、SIFT、REVEL、CADD 优先；每卡独立展开 source/scope/transcript/字段定义 |
| Stability | signed ΔΔG、模型、替换、单位与方向；以零为中心的条 | 只有 API 携带已确认 ThermoMPNN convention 才以绿色下降/粉红上升表示稳定化/去稳定化。条长为当前记录局部量尺，跨变异比较读数值 |
| Transcript | 代表后果数、transcript 名、canonical/MANE 原标签、protein change、coding change、exon/intron、consequence | protein ID、selection、mapping、biotype、VEP impact、TSL/APPRIS 折叠；解码 HGVS 的 `%3D` 等转义；不暗示 canonical/MANE 证明 UniProt 残基匹配 |

## 色彩与语义

- 临床红/绿/橙/紫来自已有致病/良性/VUS/冲突分组；其他标签保留原文与中性蓝色，不把 drug response 或 oncogenicity 自动转换为胚系致病分类。
- ClinVar 星级按 NCBI 官方 review status 映射。未知/缺失显示 unknown，不冒充 0 星；aggregate 星级不赋给每个 SCV。
- Prediction 优先使用已匹配原 source call 的类别颜色；已有文档确认的原 0–1 分数保持原条长，连续色调遵循各工具方向，SIFT 低值方向与其他工具区分。Conservation 和 ALoFT 概率使用独立蓝色数值强度。未确认统一量尺的原值不伪造百分比条。
- 不移植 CATVariant 的自定义 prioritization、加权 evidence、PP3/BP4 分档或高低影响合议结果。总览单位是评分输出，不是独立工具票数；61 个字段并非 61 个独立证据。
- AF 的 0 与缺失分开；正值低于 10⁻⁶ 只共用最低显示色，不改原数字。灰色零标记不是无数据。频率色与预测色的图例独立。

## 实现与验收

`VariantCatalog.tsx` 维护表格与面板入口；`VariantEvidencePanels.tsx` 维护分区组件；`variant-evidence-model.ts` 集中维护已有类别语义、官方星级与显示尺度；`variant-evidence.css` 只作用 Variant 区域。

状态与实际浏览器验证见[本轮交付](../../../record/00_initial_preview/20260921_variant_evidence_refinement.md)，调研依据见[网站研究追加](../research/website_v2/analysis.md#variant-evidence-20260921)。本轮采用单执行者与独立浏览器会话，未操作主线程代理或主线程浏览器；保留并行 Sequence、Basic info 等改动。


## 统一预测列与Prediction Toolkit（2026-09-21追加）

最新决定替代本日稍早的统一网格：用户实看后认为大列卡片不如纵列，已恢复每个predictor独立一列。61字段工具说明与无12项人为上限继续保留。

- 每个工具独立表头、分数、原分类与原量尺细条；点击列头直接打开该字段的Toolkit说明，点击分数打开原证据详情。默认AlphaMissense、SIFT、REVEL、CADD PHRED不变。
- 表格身份列固定紧凑尺寸：Genomic 138px、Position 76px、Ref/Alt各42px；评分列至少136px，额外空间分配给评分列。多选时表格内部横向滚动，不扩大页面。白底/浅蓝灰隔行，深色标题，保留已有临床与预测语义色。
- 选择器支持方法组、搜索、已选筛选、批量选择/清除当前结果、恢复默认。可选当前字典全部61字段；API仍对白名单、页长和游标上下文做校验。
- 字段卡默认显示用途、量尺、适用层次；Meaning & criteria按需展开方向、判断依据和链接。61字段不等同于61独立模型，说明不重算source call或生成新的综合致病结论。
- Catalog上方复用Sequence的`VariantDistribution`组件：可调bin、ClinVar原分类展示组、hover/键盘预览、点击筛选。保留Sequence现有显示；不是重建一套统计。
- 分布图随source/consequence/AF/transcript/search等条件改变，但不被自己的canonical_start/end选区裁剪；所选范围高亮，清除仅删除范围并回到第一页。其它筛选保留。未验证位置的变异单独显示数量，不塞入蛋白坐标。

实现：`VariantCatalog.tsx`维护独立列和分布图联动；`PredictionToolkit.tsx`维护选择器，`predictor-guides.ts`维护逐字段说明，`variant-catalog-layout.css`限制本轮样式作用范围。合并网格组件和对应样式已移除。此次恢复无后端改动，沿用此前已开放的全部字段选择能力。

### 来源审查与限制

- 主依据为已核对的[dbNSFP 5.4a原字段字典](../../../../../modules/variant/runs/20260913_field_selection/dbNSFP5.4a_variant.columns.txt)，版本依据见[原审查](../../../../../modules/variant/docs/dbnsfp_context_review.md)；在线[发布页](https://www.dbnsfp.org/releases/)仅作官方入口，不以新版本覆盖当前快照。
- 各工具含义、适用范围、原分值方向及字典所列阈值逐字段核对；例如SIFT采用本版本字典的`<0.05`，PolyPhen明确边界取整空隙，MVP阈值依赖约束分组，ESM1b注明作者不建议通用阈值。PHACTboost/MutFormer/MutScore标明字典中的作者通信依据。
- AlphaMissense补充[官方代码与模型说明](https://github.com/google-deepmind/alphamissense)和[EBI分数解释](https://www.ebi.ac.uk/training/online/courses/alphafold/classifying-the-effects-of-missense-variants-using-alphamissense/understanding-pathogenicity-scores-from-alphamissense/)。低于0.34/高于0.564的解释保留为指南，不用于重新分档。
- AlphaGenome三字段结合[本站已确认审查](../../../../../docs/alphagenome_plm_review.md)、[官方FAQ](https://www.alphagenomedocs.com/faqs.html)及[Atlas说明](https://deepmind.google/blog/alphagenome-atlas-a-predictive-map-of-every-possible-dna-letter-change-in-the-human-genome/)；AVI raw和PHRED是同一模型的不同量尺，merged splicing为无方向的合并效应，不是某组织的PSI。
- CADD/AVI PHRED说明排名分位；保守性、背景选择及ALoFT各类概率保持各自语义。未在本次所核对字典找到通用阈值的工具明确注明该限制，不凭0.5补造判定。

本次验证与尚未完成的浏览器验收见[交付追加](../../../record/00_initial_preview/20260921_variant_evidence_refinement.md#统一预测列与逐工具指南追加)。
