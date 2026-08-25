# 11. Expression 信息精简与 Structure 序列配色计划

状态：已完成  
计划日期：2026-08-16  
适用阶段：M11 完成后的 M12 展示收敛

## 1. 目标

1. 精简 HPA/PaxDB 与 GEN 区域默认可见文案，建立标题、关键数值、上下文和辅助说明的清晰层级。
2. 避免连续小字号段落；默认卡片只保留做判断所需的信息，来源语义和完整记录继续放在按需展开区域。
3. PDB 默认按 Sequence canonical residue map 的 variant-count 色阶着色，使二维序列与三维结构使用同一图例；AlphaFold pLDDT 保留为可切换的独立模式，不能混淆两种语义。

## 2. Expression 展示合同

- Section intro 限制为一句；重复解释只保留一处。
- HPA/PaxDB overview 强调 modality 名称、单位与主要数值，来源版本和完整记录放入 disclosure。
- GEN dataset 卡片默认只显示 dataset ID、短标题、tissue、disease 与 qualifying contrast 数；project/strategy/sample mapping/source 放入展开后的 metadata。
- Contrast button 默认显示疾病、组织、case/control 数和当前蛋白方向；详细 Ensembl/log2FC/FDR 仅在必要时显示，multi-mapping 必须完整保留。
- 辅助文字不低于 12px；主要标签 13–15px；关键数字/结论用字重、颜色和间距共同区分。
- 不删除原始来源、单位、阈值、mapping ambiguity 或空态语义，只改变默认信息密度。

## 3. Structure 配色合同

- 默认模式为 `Sequence variants`：每个 canonical residue 使用 Sequence residue map 相同的六档 variant-count 色阶。
- 颜色数据来自现有 `/sequence/overview` 的 `variant_site_density.total_counts`，不在结构组件中重新计算变异事实。
- fragment 必须通过 DBREF canonical range 校验后映射 residue；越界或无法映射的 residue 使用明确的 missing 色。
- 保留 `AlphaFold confidence` 切换项与原 pLDDT 图例，避免丢失模型置信度信息。
- 当前图例和说明随模式切换；不得同时用一个颜色表达 variant density 与 pLDDT。

## 4. 验收

- P00533 的 HPA/PaxDB 和 GEN 默认视图不再出现多段连续说明文字，标题、关键值、上下文明显分层。
- GEN 仍保持 summary-first、contrast-click 后才加载火山图；多 Ensembl 映射不丢失。
- P00533 Structure 默认显示 Sequence variant-density 图例，切换 pLDDT 后恢复置信度色阶。
- 稀疏、空态、错误态和窄屏布局可读；前端 production build 通过。

## 5. 实施记录（2026-08-16）

- HPA/PaxDB 默认区域改为紧凑单位图例；尺度、missing 语义和完整来源记录放入 disclosure，tooltip 不再串接全部 records。
- GEN 收起卡片只突出 dataset、tissue、disease、contrast 数与方向；项目、策略、样本、阈值及完整 Ensembl 结果按需展开。
- Expression 辅助字号统一不低于 12px，并通过标题、关键数字、badge、颜色和间距建立层级；窄屏不再通过继续缩字容纳内容。
- Structure 默认按 Sequence 的六档 canonical variant-count 色阶着色，并保留互斥的 AlphaFold confidence 模式。
- AlphaFold fragment 使用 `canonical_start + local PDB residue - 1` 映射；P00533 F1 与 Q14643 F2 的真实 DBREF/local numbering 已验证，无法映射时显示 `Not mapped`。
- 前端 production build、P00533 页面和 1–1210 residue-density 守恒探测通过。
