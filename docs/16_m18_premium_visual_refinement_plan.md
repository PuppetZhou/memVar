# M18 高对比度与科研信息质感优化计划

状态：2026-08-24 已实施并验收。M18 主要调整展示与交互；GO term evidence 接口仅补充与摘要一致的 `evidence_code` 过滤，不改变数据层、证据粒度或科学结论。

## 1. 设计判断

当前页面的主要问题不是缺少更多颜色，而是文字、背景、边框和信息权重过于接近：辅助文字偏浅，多个淡色卡片连续出现，密集字段缺少稳定的阅读起点。参考页面的优势来自深色正文、明确分隔、宽松留白和单一强调色。

M18 采用以下规则：

- 以 Oxford navy/charcoal blue 作为标题和关键数据的高对比基础色；
- 以 cerulean/verdigris 作为链接、选中态和中性科研信息强调；
- 以浅 frosted blue/honeydew 作为少量区域背景，不在每个字段上铺彩色；
- coral/red 仅表达来源明确提供的风险、冲突或 pathogenic classification；
- 绿色仅表达来源明确提供的 benign classification 或成功状态；
- AlphaMissense、ThermoMPNN ΔΔG、COSMIC 计数和来源数量不得被视觉样式转译成临床分类；
- 公开正文不小于 13 px，关键字段优先使用 15–18 px；分区标题、数据值和来源信息形成三个稳定层级。

## 2. 实施范围

### 2.1 全局视觉系统与 GEN

- 提高正文和辅助文字对比度，统一边框、圆角、阴影和交互过渡；
- 增大 section 间距和标题层级，以清晰边界替代连续的淡色块；
- GEN differential expression 的 Tissues、Diseases、qualifying context 与 protein metrics 使用独立纵向 field modules；长疾病列表必须在自己的内容区换行，不得与 label 或分隔线重叠；
- 移除所有面向用户的 Copy/clipboard 操作，但不误删普通文案中作为语义名称的 `copy` CSS 类。

### 2.2 Structure、Anatomy 与 covalent pairs

- Structure 继续读取真实的本地 AlphaFold PDB；停止使用 ribbon/cartoon；改用更清洁的 molecular surface 与必要的 stick/sphere 层，保留 mutually exclusive 的 sequence-variant 与 pLDDT 着色；
- Anatomy 暂停所有器官/组织 marker 与 label overlay，只保留完整人体图、证据层切换、组织索引、证据跳转和 zoom/pan；
- covalent pair 在当前蛋白的全部可见记录均为 disulfide 时只显示一次 `Disulfide bond (S—S)` 类型说明；连接线使用分层 lane/arc，避免所有 pair 共线堆叠；
- 未提供 feature type 时继续显示 `Covalent bond (type not specified)`，不得猜测。

### 2.3 Gene Ontology 与 Variant

- GO 按 Molecular function、Biological process、Cellular component 先展示摘要和数量，默认收起长列表；展开后保留 evidence code、source、reference、NOT 与 provenance；
- Variant 主行减少横向碎片，强化 variant identity、effect、source evidence、prediction 和 population/identifier 的模块边界；
- 只有 ClinVar 独立 assertion 等具有明确 source classification 的记录可使用 pathogenic/benign 背景；冲突记录独立显示；不得把多个 assertions 投票成共识。

### 2.4 科学生物学素材

- BioRender 仅使用一张完整的 memVar evidence overview figure，不提取 standalone icons；
- 页面不得提供该 BioRender 原图下载按钮；
- 通用操作继续使用 Lucide，并必须具有可见文字或 accessible name；
- 完整出处、figure/slide ID 与上线许可动作记录在 `15_m17_asset_provenance.md`。

## 3. 验收标准

- 在桌面中等宽度与窄屏布局中，GEN label/value/长疾病名称无重叠、无越界；
- Anatomy SVG 中无 marker、dot、marker label 或可点击伪坐标；组织索引仍可使用；
- Structure viewer 不调用 ribbon/cartoon 表现形式；variant 与 pLDDT 模式仍能切换并解释颜色；
- 当前蛋白若全部 covalent pairs 为 disulfide，类型标题只出现一次，pair lanes 可区分；
- GO 首屏不再直接铺开全部 annotation；展开后科学字段不丢失；
- Variant 的红/绿临床色只绑定显式 source classification；主行不得产生综合 pathogenicity 结论；
- 页面无 user-facing Copy 控件或 clipboard 调用；
- BioRender 成图以完整 figure 方式嵌入并显示 attribution；
- 前端单元测试、TypeScript 检查、production build 和后端测试全部通过。

## 4. 实施结果与验证

- 全局视觉、GEN/DE、Structure、Anatomy、covalent pairs、GO、Variant 和首页 BioRender overview 已按上述范围完成；
- M18 明确取代 M12/M16/M17 中的 protein ribbon/cartoon 与 Anatomy marker/landmark 方案；
- GO drill-down 会继承当前 `evidence_code`，分页游标与过滤条件绑定，避免摘要数量与展开记录不一致；
- P00533 实测：GO:0005006 的 IDA 过滤返回 7 条且全部为 IDA；25 个 covalent pairs 均为来源明确的 disulfide bond；结构模型可用；
- 前端测试 52/52、TypeScript 检查、Next.js production build 和后端测试 92/92 均通过；首页、P00533 页面和 BioRender 素材请求均返回 HTTP 200；
- 本地前端与后端当前分别运行于 `127.0.0.1:3000` 和 `127.0.0.1:8000`。

## 5. 发布门槛

本地开发与验收不受影响。公开发布前须在 `15_m17_asset_provenance.md` 所列记录中归档 BioRender Publication License 与正式导出凭证；现有 Anatomy illustration 也应一并完成授权核验。
