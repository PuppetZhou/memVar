# AlphaGenome 与 AVI 共轴轨道设计

2026-10-02：保存范围与 MANE 结构采用不同标注；裁剪来源默认/复位取完整保存区间，短基因不再仅按 8% 留白。实现已发布，定向浏览器验证通过，见[四项批注记录](../../record/01_preview_optimization/20260922_browser_feedback_01.md#2026-10-02互作图标保存范围jsd与逐条注释)。

## 2026-10-01 悬停重绘定位与局部优化（已实现并验证）

用户反馈仍不够流畅并询问是否由 DuckDB 读取引起。CFTR 稳定页面的同一 32 步 axis hover 在无已完成 API 请求的情况下出现 30 个约 52–56ms 主线程长任务，纯页面滚动无长任务；载入等待与稳定悬停分别分析。诊断证据见 [performance_diagnosis](../../../data/ui_axis_validation/performance_diagnosis/summary.json)。

已按数据／尺度变化缓存 AVI 完整统计，静态 Canvas 底图只随真实绘图输入更新，悬停、选择及 brush 复制底图后更新动态标记。全部 ALT、原始分数、贡献、缺失／零、图形比例和选择语义保留。相同 CFTR 稳定悬停手势复验的长任务由 30 降至 0，帧间隔 p95 由 83.3 降至 16.8 ms；tooltip、点击详情、Raw/PHRED、类别切换与 Pan 通过。结果为本地定向浏览器样本，不代表所有设备帧率；后续加载性能优化按用户要求暂停。[复验结果](../../../data/ui_axis_validation/performance_diagnosis/after_summary.json)。

## 2026-10-01 区间导航与坐标轴局部优化（已实现并验证）

用户根据 CFTR 截图要求改善拖动卡顿和坐标轴挤压。导航拖动采用局部目标区间预览，完成手势后提交给共轴轨道，减少重复请求；已展示的坐标轴和轨道始终使用同一已提交区间。轴按实际可用宽度绘制文本与刻度，控件在窄屏换行，保留真实基因组比例、MANE 内容及裁剪边界。仅修改前端，不修改后端数据、运行配置或正在执行的裁剪任务。

完成标准为前端构建与已有坐标测试通过，以及 CFTR 宽／窄屏真实拖动、请求次数、最终坐标、exon 定位和 reset 的定向浏览器验收。前端 TypeScript／Vite 构建及 6 项已有坐标测试已通过，22:11 更新预览静态文件，旧 hashed assets 保留。CFTR 宽／窄屏真实 Pan 拖动均由 24 请求降至松手后 1 请求，拖动期间主轴与旧轨道保持同区间；exon、reset、键盘提交、取消及主轴／AVI／ATAC 对齐检查通过。结果维护于既有 [AlphaGenome 交付记录](../../record/01_preview_optimization/20260929_alphagenome_avi.md)。

2026-09-29。状态：用户已授权 AVI mapping、后端接入及依据调研优化前端；本设计先于实现形成。当前科学范围沿用 [AlphaGenome 生效规则](../../../../modules/Alphagenome/docs/rules.md)，数据状态及存储依据见[存储分析](../../research/01_preview_optimization/alphagenome_storage.md)。本文替代旧前端的 modality-first 选择流程和旧展示快照限制，不改变科研收录规则。

## 1. 用户确定项与设计目标

- 蛋白页已经确定 gene，上下文固定；只有正式蛋白—gene 关系确实返回多个 gene 时保留关联上下文切换。
- 先选择 biosample，再选择该 biosample 存在的模态，支持继续加轨道，核心任务是在同一 biosample 下比较不同模态。
- 新增 AVI score 轨道，接入外盘新版参考预测，旧参考展示版本退役。
- 借鉴 Atlas 配色和共轴浏览，增强每条轨道的边界、标签与数值可读性。
- 先设计再优化。下述布局、默认状态及实现方法是项目实现选择，不作为用户逐项指定或官网源码事实。

## 2. 调研证据与采用边界

用户 ZIP 已原样解包至 [atlas_reference](../../research/01_preview_optimization/atlas_reference/docs/sites/alphagenome-atlas/README.md)。包内三份文档和八张截图保留原路径关系，不在 Web 根目录展开。已实际查看 Locus 初始、加轨和 Variant 解释截图。

| 本地证据 | 确认观察 | 项目采用 |
| --- | --- | --- |
| [E006](../../research/01_preview_optimization/atlas_reference/docs/sites/alphagenome-atlas/evidence.md#e006)、[Locus 截图](../../research/01_preview_optimization/atlas_reference/fig/captures/alphagenome-atlas/2026-09-28_locus_initial_03.png) | 共享基因组轴、gene 方向、AVI、信号轨道、蓝色位置参照 | 一条统一横轴和同步区间；AVI 置顶、参考预测在下 |
| [E007](../../research/01_preview_optimization/atlas_reference/docs/sites/alphagenome-atlas/evidence.md#e007) | 加轨表按具体 assay/biosample/strand/TF/mark 选择 | 精确 track ID 加轨、去重、移除和重排；先 biosample 的次序来自用户要求 |
| [E003](../../research/01_preview_optimization/atlas_reference/docs/sites/alphagenome-atlas/evidence.md#e003) | 官网切换指标可能丢弃局部 biosample 筛选 | 项目切换模态始终保持已选 biosample，已加轨道保留 |
| [E008](../../research/01_preview_optimization/atlas_reference/docs/sites/alphagenome-atlas/evidence.md#e008) | 部分密集图为 Canvas，坐标含 SVG | AVI 使用 Canvas 承载全部返回的逐等位 SNV；不依赖官网内部 RPC |
| [调研建议](../../research/01_preview_optimization/atlas_reference/docs/sites/alphagenome-atlas/variant-locus.md#我们的借鉴方案) | 双视图、Top 3、10 条轨道篮属于调研建议或特定官网状态 | 本轮不照搬双视图和 Top 3、不设科学性 Top N；蛋白页直接服务基因座比较 |

官网 AVI 堆叠贡献不直接复制：本项目已有 raw/PHRED 来源，18 列归因之和与 raw 的差异尚未解释。参考轨道属于 reference-sequence predictions，并非 ALT 预测或实验观测；本轮不生成 ref/alt 图。

## 3. 页面结构与选择流程

主区域采用白色连续轨道面板，顶部显示 gene 名称、GRCh38、参考预测标签，去掉旧大面积蓝绿渐变。导航分为定位栏、轨道选择器和共轴轨道栈。

1. 定位栏：gene 身份和方向、当前 chr:start–end、区间宽度。单 gene 不显示冗余选择框；长基因显示明确的窗口切换入口，不把多个上下文窗口求平均或拼成无边界曲线。
2. 添加轨道：`Biosample → Modality → Assay / strand / mark / TF → Add track`。biosample 搜索来自完整本次目录，旁显实际模态数/轨道数；未选择时不自动假定 Lung 等器官是当前基因的首选背景。
3. 模态按钮只在已选 biosample 存在时可用，计数来自该背景，不要求每背景均有 11 模态。切换模态不清空 biosample；加轨后选择器保持当前状态，方便连续加入不同模态。
4. 基于 CURIE 选择保留原 biosample 标签和具体 assay 元数据。CURIE 相同不证明同供体、同发育期、同培养条件；具体轨道不能合并成虚构的单一实验。
5. `splice_sites` 四条共享输出独立标示 `Shared · not biosample-specific`，可从共享轨道入口加入，不把它们复制计入每个 biosample。
6. 默认保留 AVI 轨道，参考轨道由用户选入。来自 Expression 的确切标签匹配只作为选取捷径，继续标明不是样本级匹配。

每条参考轨道采用固定宽度左侧标签栏与右侧图形栏：左栏显示模态、biosample、assay、strand/mark/TF；右栏保留零基线、独立 Y 轴、单位和数值检查。浅灰横线、细色条及交替细微背景增强“轨道感”，避免每条图成为带大留白的独立卡片。上下移动、折叠、移除位于标签栏；原值和说明按需展开。

## 4. 配色（2026-09-30用户批注生效）

科学图形统一使用 `frontend/src/lib/palette.ts` 的用户专属11色：`#7b95c6, #49c2d9, #a1d8e8, #67a583, #a2c986, #d0e2c0, #fded95, #ffc1a6, #f59c7c, #f47254, #c85e62`。这项明确要求替代此前从Atlas截图取样的科学配色；官网图例与结构仍作为调研证据。界面文字、背景和iOS浅蓝选中态沿用全站样式。

| AVI类别 | HEX |
| --- | --- |
| Total impact（菱形） | `#c85e62` |
| Protein impact | `#7b95c6` |
| Conservation | `#67a583` |
| Accessibility | `#fded95` |
| ChIP | `#49c2d9` |
| Transcription / RNA | `#a2c986` |
| Splicing | `#f47254` |
| Contacts | `#a1d8e8` |
| Variant type | `#ffc1a6` |

参考模态与叠加曲线均从该palette分配，图例同步。总分保留独立菱形；默认仅Total，复选框独立控制各类别是否绘制，未勾选类别完全隐藏。Contact保留有符号、零中心的蓝→近白→玫红色标，不截断负值；MANE CDS为蓝色块，stop_codon为玫红块。浅色只用于图形/色块，文字仍用深色。

## 5. 共享坐标与图形

- 内部、API 的 `start/end` 为 GRCh38 0-based half-open；页面显示 1-based inclusive。所有轨道请求同一 viewport，并按 API 返回的真实 `bin_edges` 绘制；固定左标签宽度和图内 margin 保证 X 位置相同。
- 已裁剪来源默认及复位展示该窗口保存的完整 Ensembl gene＋两侧各 10 kb 范围；平移、缩放和 Full saved range 均限制于保存区间。多窗口长基因仍按所选窗口独立展示。未裁剪历史来源沿用 gene 范围加上下文。负链只显示方向，基因组坐标保持递增。
- 信号按照可见区间读取，随缩放细化到原生分辨率，禁止把粗 bin 插值伪装成逐碱基数据。每条图显示实际 bp/bin 或源分辨率；不继续声称新快照只有 4096 个全窗 bins。
- Mean/Maximum 是明确标注的显示统计，非新科学分数；各模态保留独立 Y 轴，不声称跨 assay 绝对高度可比。没有数据时留空，真实零画在零线上。
- 剪接事件以弧线及可检索坐标表显示，按来源顺序分页；展示当前页/总数，并提供翻页，不保留旧 top 200 正值筛选。
- Contact map 使用真实二维区间、实际分辨率、有符号图例，视觉布局不保证它与一维曲线的二维信息完全同构。
- 本轮不绘制不存在于接口的数据：有可用MANE模型时在同一中心线上绘制来源exon轮廓、UTR、CDS及stop_codon，缺少时显示明确状态；没有序列接口时不仿制碱基字母轨道。

## 6. AVI 数据与交互

AVI 顶层常驻、可折叠，不随 biosample/modality 改变。默认 Raw 尺度且仅勾选Total；可独立勾选多个贡献类别，显示Y范围随可见图层更新。提供Select all与Total only快捷操作，全部取消时提示选择分数。PHRED仅显示总分，返回Raw保留已选贡献；在PHRED勾选贡献自动切回Raw。既有 merged splicing 评分独立保留于变异评分体系，不能当成参考剪接轨道或本次归因中的同名贡献。

`GET /proteins/{accession}/expression/alphagenome/avi?gene=&tile=&start=&end=` 返回当前蛋白/基因已关联的项目 SNV 在可见区间内的值。关键字段：`variant_id, position`（1-based）、`ref, alt, raw, phred, status`，以及 `scope, has_more`。真实入库状态由 API 呈现，失败不能退成空值。

- 每个 SNV 保留独立等位基因和分数；Canvas 渲染不以每位置最大值/平均值替代同位点多个 ALT。重叠可通过点击候选列表和键盘检查逐项查看。 总分菱形随屏幕像素拥挤程度缩小（半径0.65/0.95/1.5px），不绘制逐条常驻竖梗；悬停才强调定位。贡献先画、总分后画，保留真实有符号高度；零贡献不填充人为最小高度。有效纵轴高度200px，密集视野提示拖选局部放大；无抽样、聚合或横向抖动。
- 宽窗绘制全部返回点，超过服务分页上限则明确提示加载后续或缩小范围；不默选代表点、不把部分返回标记为完整。
- 轨道说明固定为 `AVI · project SNVs`，显示当前范围数目/缺失状态。无点表示当前项目范围未提供有值记录，不意味着其余基因组位置低风险或无变异。
- 悬停提供 pos/ref/alt 与原值；点击、键盘检查或等价列表可打开 SNV 明细。选中位置用共享蓝线对齐预测轨道，取消后恢复。
- SNV 明细从独立接口读取 18 列原始贡献及 mapping 状态。贡献用零中心横条，保留正负号和来源字段；排序仅用于阅读，不更改原值。总分独立呈现，不以贡献之和生成 raw、PHRED 或“已解释百分比”。
- 单 SNV 归因尚未入库不阻塞已有 AVI 轨道和参考预测加载；显示明确的待接入/未命中/不适用状态。

## 7. 实现契约与验收

后端参考目录保留兼容路径 `/proteins/{accession}/expression/alphagenome`，提供真实 gene/tiles、biosamples、tracks、`shared_modalities=['splice_sites']`、来源快照和不可预测状态。track 请求增加 viewport `start/end` 与 `bins`；signal 提供 `bin_edges, source_resolution_bp`，junction 提供 `total, has_more, offset`，contact 保留实际尺寸。文件路径保留后端，浏览器不依赖 Newsmy 挂载路径。

定向验收：

1. 同一 biosample 连续加入 RNA 与可及性或 ChIP；模态切换保持背景，具体轨道不重复加入，移除/折叠/重排有效。
2. 新版 DNASE 与 CHIP_TF 可选；共享 splice_sites 不标成所选 biosample 专属；无可用模态和无预测 gene 状态可见。
3. AVI 和参考轨道坐标统一，缩放/平移更新同一区间；真实 SNV 的位置、ref/alt 和 raw/PHRED 与服务表一致，同位点多 ALT 不丢失。
4. 归因零、负值和缺失可区别；未完成导入时不以总分或 0 伪造贡献。
5. 有符号 contact 色标正确，junction 分页有完整总数与未展示提示；新快照来源、分辨率及不存在的旧限制不冲突。
6. 构建通过，桌面真实 gene 页面测试添加/缩放/选择 SNV；基本键盘和窄屏布局不阻塞主功能。验收记录在 record，由实施者填写实际结果，不以本文完成视为页面完成。

尚需科学讨论的只有未来扩展：归因与 AVI raw 的分解关系、跨窗口合并、全基因组 SNV 覆盖，以及任何新分组/阈值/衍生分数。它们不阻塞按原值、原关联和独立来源开展本轮接入。

## 8. 本轮实现状态

2026-09-29追加交互修订已实施：模态和指标选中态沿用全站iOS浅蓝；分别提供重选参考轨道、恢复gene视野的reset图标；支持在基因坐标和一维轨道拖选区间后放大。悬停坐标共享到各轨道，当前轨道提供水平数值线、竖直坐标线及就近说明，点击SNV固定线与临时悬停区分。参考信号按真实bin边界绘制阶梯线，避免粗bin中心连线的插值及单bin消失。AVI左侧栏现为复选框多选、默认仅Total（替代09-29的单类别聚焦与淡化）；贡献色现按09-30用户palette，contacts/variant type单列，保留每个ALT。仅Raw尺度展示原值有符号贡献，正负分别堆叠，总分独立绘制且不强求与堆叠高度相等；PHRED不与raw贡献混用轴。归因来源未就绪时明确不可用，不用总分伪造类型。独立AVI组件见[AlphaGenomeAvi.tsx](../../../frontend/src/components/AlphaGenomeAvi.tsx)，[实页验证](../../record/01_preview_optimization/20260929_alphagenome_avi.md#1430交互修订侧栏reset与坐标检查)。

2026-09-29：上述选择器、共轴结构、11 模态、共享 splice sites、原生区间请求、剪接事件显式分页、AVI Canvas/等位记录列表/键盘检查及独立贡献详情已在 [AlphaGenomeExpression.tsx](../../../frontend/src/components/AlphaGenomeExpression.tsx) 与[样式](../../../frontend/src/components/alphagenome-expression.css)中实现。贡献目录额外存在 `contacts`、`variant_type`，现使用专属palette独立呈现，不强行合并到官网六类。选中SNV可定位到当前窗口内200bp，同gene/window缩放保留仍可见的选中项。前端构建、定向接口和真实EGFR桌面流程通过并已本地发布；2026-09-30新包18列贡献已完成mapping和PostgreSQL入库，真实彩色贡献及原值验收通过，实际范围与证据见[交付记录](../../record/01_preview_optimization/20260929_alphagenome_avi.md)。

## 09-30八项页面反馈：已交付

按用户指定改用memVar的11色palette；Add/Added改为可取消的选中按钮；参考信号统一紧凑固定高度，AVI类别区独立滚动，避免图例撑高整行；浮层分开显示坐标、区间/链、模态和数值。同一biosample、同一模态的多条一维信号允许叠加到一个面板，保留独立曲线/颜色/名称/开关与原始共同数值轴，不求和、不归一化；可随时切回分轨。二维contact和junction保持独立。

CDS使用本地MANE1.5原始GTF，按当前variant代表的完整ENST及HGNC→ENSG/染色体核对，先由foundation发布CDS分段、来源exon/UTR/transcript结构和状态，再投影Web/入库。仅MANE Select标记为MANE；467个canonical补充基因明确无MANE，不静默替代。来源exon薄轮廓、UTR灰色薄块、CDS蓝色厚块共享中心线，内含子以方向箭头连接；来源stop_codon单独标示，不将全部gene范围冒充编码区。此标记是基因的MANE基因组结构，不声明与当前UniProt isoform序列完全相同。

上述八项已实现并在本地8000的真实EGFR桌面页验收。MANE正式快照、覆盖状态与科学边界见[foundation结果](../../../../modules/foundation/docs/result.md#2026-09-30-mane-select-cds-基因组结构)；交互、构建、接口和截图证据见[本批记录](../../record/01_preview_optimization/20260929_alphagenome_avi.md#09-30专属配色mane-cds与紧凑叠加轨道)。

## 后续五项页面批注（2026-09-30，已实现并验证）

本轮为展示与交互修订：放大后在坐标轴用滚轮横向平移，增加可拖动的区间导航；强化CDS色块高度/边线，并提供按来源CDS exon直接定位的入口，保持基因组坐标比例和内含子间隔。互作初始页移除重复的Source collections / Interaction evidence / Sources层级，来源入口压缩为紧凑行；Expression的AlphaGenome链接移到末尾说明栏。科学数据、收录范围和代表选择不变；验收覆盖平移边界、缩放宽度、CDS定位、互作来源下钻/返回及Expression链接。

构建、平移边界/宽度保持、CDS定位、来源下钻/返回及底部入口跳转均通过。验证范围与截图见[本批记录](../../record/01_preview_optimization/20260929_alphagenome_avi.md#09-30后续五项批注平移cds可见性与空间压缩)。

## 第三批页面反馈（2026-09-30，已实现并验证）

用户要求AVI默认仅Total，改为可同时勾选/取消多个类别；此要求替代此前单类别聚焦/其余淡化。按当前勾选项绘制和计算显示Y范围，原始总分独立，选中的正负贡献分别堆叠，不重算评分；详情仍可查看完整原始贡献。互作总览以1176×827视口一屏完整展示为验收目标，压缩标题/分类图/来源按钮；QTL底部提示与计数帮助并行排列。本轮仅修改展示，无数据范围和科学规则变更。

本地8000已更新。1176×827实测：互作总览386px高、来源按钮41px高且按内容宽度排列；QTL说明与计数帮助合并为28px一行。构建、AVI实际绘制颜色开关/多选/空选/PHRED/18项明细、两来源下钻返回及帮助弹窗均通过；[验证记录与截图](../../record/01_preview_optimization/20260929_alphagenome_avi.md#09-30第三批反馈avi复选框与互作qtl密度)。

## AVI悬停面板排版（2026-09-30）

用户要求压缩冗余并对齐浮层：顶部一行显示坐标和REF→ALT；Total独立标明Raw/PHRED。贡献按名称/数值两列排列，数值右对齐；零值合并为数量，缺失单独标明。已选类别内按绝对值降序最多展示6个非零原始特征，超出时明确提示；点击仍查看完整18项。仅调整悬停摘要，不改变轨道、数据与评分。

同日修复参考轨道与AVI浮层被轨道容器裁剪的问题：共用独立页面浮层，按实测尺寸限制视口边界，底部空间不足自动向上显示。真实CAGE双链和AVI多类别浮层、移出关闭及构建均验证通过，见交付记录。

## GTEx QTL共轴轨道（2026-09-30，已实现并验证）

用户确认QTL与AlphaGenome同时展示，Add QTL独立入口；GTEx tissue不自动映射AlphaGenome biosample。使用已入库的GTEx v11关联原值，按当前gene、组织及类型添加独立轨道，横轴变异GRCh38坐标、纵轴−log10(P)，保留各phenotype关联及原始slope。明确当前窗口覆盖和分页，不按AVI匹配或CDS过滤。模态与组织文字放大、提高对比度。验收包括真实三类型接口、共轴缩放、选择/移除、浮层组织及数值、构建和浏览器检查。此次不实施跨来源组织映射或AVI等位基因关联。

真实EGFR三类型、单碱基边界、独立选择/移除、缩放后刷新、浮层与AlphaGenome并列已验证；90,884条关联数据集分页查询通过。当前仍限定所选模型窗口，未实现全QTL范围扩展或下方列表跳转；两者作为后续增强，不影响独立添加。详见交付记录。

## 选择器与坐标区信息层级（2026-09-30，已交付）

按用户要求沿用iOS浅蓝操作态：biosample/GTEx tissue使用可点击卡片、箭头与勾选状态，明确选择步骤；基因名22px，CDS色标与Explore CDS导航强化，转录本与方法提示次级呈现。仅调整展示，不改变坐标、数据或匹配语义。构建与真实页面选择/200bp CDS跳转验证通过。

## Atlas式清晰度与全站视觉整理（2026-09-30，已实现并验证）

用户明确允许替代此前浅色iOS/专属配色的界面要求：采用白底、深色文字、清晰坐标线、圆角选择器与明显选中态，优先AlphaGenome并同步全站背景和信息层级。UI语义色集中到design-system，删除覆盖链中的重复定义；AlphaGenome样式按功能重写，精简重复提示并保留Guide及实际覆盖/缺失提示。参考曲线使用同色系较深颜色，AVI总分使用深色菱形；不改变分类、数值或任何科学筛选。范围含选择器、轨道/坐标、全站主要surface/文字/选中态；不重构数据处理或增加假设性抽象。必要验收为构建、真实选择/共轴/CDS/QTL流程、首页/详情主要模块和窄屏可用性。

本轮替代此前的卡片分步选择器与浅蓝层叠背景：biosample/modality与GTEx tissue统一为紧凑下拉，源数值和选择逻辑保留。当前UI token唯一主维护位置为`frontend/src/design-system.css`，AlphaGenome样式在`alphagenome-expression.css`按职责分段，不继续追加历史覆盖。真实桌面/390px选择器、CAGE双链/QTL共存、浮层与CDS跳转、全站主要板块及构建通过，细节见记录。

## 转录本结构与局部清晰度修复（2026-09-30，已实现并验证）

用户要求增加截图中的转录本结构轨道，同时修复长选择项/下拉箭头贴边以及变异表文字偏浅。沿用已确认MANE1.5和完整版本代表ENST，不重新选择转录本；扩展读取同一来源中的exon/UTR/transcript。正式结构与兼容性验证由[foundation结果](../../../../modules/foundation/docs/result.md#2026-09-30-mane-select-cds-基因组结构)维护。Web继续查询原API，新增结构字段向后兼容，源CDS/stop_codon及旧状态保持。

原先分开的gene线和CDS色带合为一条MANE结构线：来源外显子轮廓、灰色UTR、蓝色CDS、玫红stop_codon；箭头只画在外显子间隙，完整转录本端点来自来源transcript记录。保留真实基因组比例、点击片段放大、拖拽框选、滚轮平移和Reset；不因全基因视角的短外显子较细而改变坐标比例。UTR与stop_codon的来源重叠原样保留，stop_codon绘于上层。不将没有CDS的来源外显子推断为UTR。

选择器原生交互保留，统一自绘下拉箭头与38px右侧留白、flex最小宽度与长文本省略；桌面和390px验收无溢出。变异表已按用户后续要求恢复既有科研语义色，撤除局部7.5:1统一压暗；来源标签13px/600与清晰布局保留，review stars独立使用金色。数据数值、分类及图形色带不变。验证与截图见[实现记录](../../record/01_preview_optimization/20260929_alphagenome_avi.md#转录本结构选择器溢出与变异表文字)。
