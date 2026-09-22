# 字体、信息层级与展示必要性审查

审查日期：2026-09-22。状态：**审查与整改建议，不是界面已修改或验收完成的记录。**

本专题细化现有[问题清单](issues.md)中的 UI、SQ、AT、ST、VA、EX、LOC 等条目，不另建一套阶段计划，不重编号原55项。依据为用户提供的9处页面批注/截图、关于图注与 `No source category` 的补充、13:47/13:48 的 GenCC 与互作表截图，以及当前前端源码。仅维护本文；未修改界面、数据或主任务计划，未暂存或提交Git变更。新增表格与展开注释专项审查见第8节。

主任务正在并行修改界面，本次读取已发现来源Popover、Expression有限预览、细胞图标签独立绘制等在途改动。因此区分：

- **截图问题**：用户提供的画面可直接观察，但可能已被在途代码修订。
- **代码确认**：读取时仍存在的文本、条件分支或CSS声明。
- **待实页核对**：源码可见结构风险，但没有本次运行态截图/计算样式证明。

本文未另开浏览器、未操作正在验收的页面。下列现状字号均是指定CSS的声明值，不代表覆盖、媒体查询、缩放之后的最终计算值；不能据此声称所有字段“实际字号完全相同”。审查覆盖首页、搜索、蛋白页各主模块及主要证据详情、数据概览/文档入口；不是对所有蛋白、数据状态、弹窗及响应式断点的穷举验收。

## 1. 核心结论

当前问题不是单纯“字小”或“边框浅”，而是**没有先判断信息对当前研究任务的作用，再分配视觉权重和空间**。

1. 读图必需的图例、单位、类别名，与“Hover to inspect”等操作提示接近同一层级。
2. 来源和对象类型经常被压成小标签；记录数、工具数等覆盖统计反而占用较大的独立卡片。
3. 空字段的解释在每行反复出现，增加行高，制造与真实结果相近的视觉密度。
4. 多层卡片、色框、标签将各类信息都包装成“值得注意”，削弱了真正的重点。
5. 一些科学限定虽不能删，却被写成冗长、重复的小字段落；读者容易整体跳过。
6. **用户追加确认：整体字体偏小，同时容器留白偏多。** 大框、小字、反复分隔造成“页面很长，读起来仍费力”。不能把这归因于科研数据天然需要小字号，也不能把空白多直接等同于清爽。

整改顺序应为：**删除无必要内容 → 合并重复内容 → 确定默认可见层 → 调整位置与分组 → 调整字号/字重 → 最后调整边框和颜色。** 不能通过把不重要内容缩到9px来代替删减。

## 2. 信息角色：哪些必须关注，哪些只是提示

重要程度由具体任务决定。例如数据库来源在多来源证据对照中是核心信息；在一个来源固定的长表中可只在表头出现，不必每行重复。

| 角色 | 读者需要回答的问题 | 例子 | 默认处理 |
| --- | --- | --- | --- |
| 研究对象与当前结果 | 我在看什么对象、什么结果？ | EGFR、具体变异、残基648、RNA abundance、表达值 | 保留并突出；对象名称、类型和结果优先，不由记录数替代 |
| 读图/读数必需信息 | 颜色、位置、数值具体代表什么？ | 临床类别图例、量尺范围和方向、单位、坐标、数据类型 | 与对应图表紧邻，持续可见且清晰；不是普通辅助小字 |
| 改变解释的状态/边界 | 这个结果能解释到什么程度？ | 预测/实验、匹配失败、当前筛选范围、缺失/真零、来源冲突 | 保留简短明确的状态；异常或限制出现时提高权重 |
| 来源与context | 来自哪里，测的什么组织/细胞？ | ClinVar、GTEx、组织/细胞类型、样本、来源方法 | 在当前选择与证据入口清楚呈现；固定信息上移到组级 |
| 操作控件 | 我可以改变什么？ | Source、Bin size、Clear selection、模式切换 | 与科学解释区分位置；当前值比控件标签更醒目 |
| 操作提示 | 我如何使用它？ | Hover to inspect、click to pin、drag to select | 简短、低权重；优先空态/首次使用/按需帮助，不反复占一整行 |
| 方法与来源详情 | 如何产生、如何追溯？ | 方法定义、字段代码、原始记录ID、完整出处 | 按需展开；不隐藏直接影响当前读数的单位、方向和关键限制 |
| 无独立信息价值的占位 | 这句话是否只在说“没填这个字段”？ | 有分数时的No source category、重复source value | 删除默认占位或合并到组级说明，保留真实数据和必要缺失语义 |

“字号较小”不等于“不重要”。坐标、单位、图例可以小于主标题，但必须有足够的可读性、位置关联和层级差异。

## 3. 字体与排布建议基线

下表是实施起点，需真实桌面页面核对，不是逐元素机械套用的硬规则。保留现有模块顺序与科学操作路径。

| 信息角色 | 建议字号/字重 | 排布要求 |
| --- | --- | --- |
| 页面研究对象 | 26–30px / 600 | 一个清楚的主对象，不把来源、数量同时做成同级标题 |
| 模块标题 | 20–22px / 600 | 同级一致；通过模块间距区分章节 |
| 图表标题、数据类型或当前context | 15–17px / 600 | 标题说明“表达什么”，避免只写通用View/Overview |
| 图例类别、关键性质、当前选择值 | 14–15px / 500–600 | 对比度充分，紧邻数据；不能与提示用相同字号、颜色和独立行高 |
| 正文 | 15–16px / 400 | 说明段落以正常阅读距离清楚可读为先；行高约1.5–1.65 |
| 主要表格内容、来源入口、数据标签 | 14px左右 / 400–500 | 密集比较视图必要时用13px，但需实页证明；长表靠列对齐和删减控制密度，不先缩字 |
| 表头 | 13–14px / 500–600 | 允许自然换行；慎用全大写长标签，不压到10px |
| 单位、短范围说明、辅助字段标签 | 12–13px / 400–500 | 单位贴近数值；尺度/方向放在列或图级，不每格重复长句 |
| 操作提示、补充文字 | 12px左右 / 400 | 可低于图例；不承担关键科学含义，不通过整段透明度隐藏 |

字体家族保持统一；序列、必要坐标/标识可用等宽字体，数值用等宽数字。不要让正文、说明、标签都使用600字重。边框优先明确可操作控件与当前选中状态；静态信息更多使用留白、分组标题和轻分隔线。删除占位后相应收紧留白，不为每行维持“空说明行”。

### 字号与留白必须一起审查

用户补充后，上表调高常规阅读基线；后文个别条目的13px等为局部候选，不得用作全站继续小字化的理由。先在真实内容中尝试较清楚的字号，再决定哪些密集局部确实需要较小文字。

- **优先利用现有空白放大关键文字。** 不是只放大模块标题，仍把图例、数据库来源、组织名和单位留在9–11px。
- **检查容器而非一律压缩间距。** 重点排查固定/min-height、叠加padding、多层卡片、为不存在副标题保留的空间，以及删去占位后仍保留的高度。
- **区分有用与无用留白。** 模块之间需要分隔；同一图的标题、图例、坐标和数据应靠近。同一记录的名称、值、单位不能因宽大容器被拆散。
- **表格与表达行优先使用对齐关系。** 放大文字后仍可减少重复说明和每行独立卡片造成的空隙，不能靠压低行高挤文字，也不为填满空白添加无关指标。
- **大幅纵向空白不靠全站缩放修复。** 浏览器zoom或全局transform会一起放大框、图和间距；应调整对应字号与容器布局，保留序列坐标、viewer和控件的准确性。
- **可验证目标：** 在100%桌面缩放下，主要来源、类别、图例、context和数值无需贴近屏幕辨认；与整改前相同区域相比，关键文字更清楚，空白占用更合理，整页不因单纯加字号进一步无谓拉长。不规定所有模块统一变矮。

## 4. 优先案例：Variant distribution的阅读顺序

依据：用户最新举例及[VariantDistribution](../../../frontend/src/components/VariantDistribution.tsx)、[distribution-v2.css](../../../frontend/src/components/distribution-v2.css)。代码中toolbar、legend、axis、preview均有12px声明，note为11px；即使颜色略有区别，整体仍集中在相近的小字层级。

建议顺序：**图表主题 → 颜色对应的临床类别 → 分布及坐标 → 当前选区读数**。Bin size作为侧边操作，鼠标用法作为辅助提示。

| 当前文字 | 信息角色 | 问题 | 建议 |
| --- | --- | --- | --- |
| Variant distribution | 图表标题 | 单独不能说明柱子按什么分类 | 保留15–17px标题；附近清楚呈现“ClinVar source classifications” |
| ClinVar labels | 图的分类含义 | 与后半句、工具标签挤在一行普通小字中 | 提升为13–14px/500的副标题或合入标题 |
| verified canonical positions | 统计对象边界 | 必要，但不应与类别图例争同一行主位 | 保留12px简短说明；更完整映射定义放帮助，不删除范围限制 |
| Current filters · full sequence | 当前范围 | 无筛选时是常态元信息，却持续占一行 | 与其他范围摘要合并；有实际筛选/子区间时提高状态权重 |
| Pathogenic / likely pathogenic、VUS、Benign… | 读图必需图例 | 与提示/工具标签视觉接近，完整类别名难扫读 | 13–14px/500＋清楚色块；邻近柱图，合理换行，首次提供VUS释义 |
| Bin size；Auto · 25 aa | 操作标签；当前值 | 操作与图注混在同一视觉层 | 右侧独立控件，标签12px、值13px；关闭时只显示当前值，不把全部选项常驻铺开 |
| Hover / click提示 | 操作说明 | 不应比临床类别占用更多视觉空间 | 首次/无悬停时简短提示；有选区时让位于实际范围与结果 |
| Residues 1026–1050、选区类别计数 | 当前结果 | 与普通提示同一小字条时不够明确 | 范围13–14px/600；计数与类别配对；清除按钮紧邻选区 |
| mapped / without verified positions | 覆盖状态 | 数字缺少明显角色区分容易当成同一总量 | 保留两类及单位，说明图仅展示可映射部分，不把未映射记录从总体静默删掉 |

不建议为每种图例加独立卡片或厚边框。图例是一个整体解释单元，应该与图紧密关联。

## 5. 逐区清单

标记：**P1**＝影响读图、关键识别或大量重复，应优先；**P2**＝整洁与扫读优化。以下均为未关闭的审查项；“已有在途改善”仅说明代码方向，不表示已验收。

### 5.1 Variant catalog、预测与详情

维护入口：[VariantCatalog](../../../frontend/src/components/VariantCatalog.tsx)、[VariantEvidencePanels](../../../frontend/src/components/VariantEvidencePanels.tsx)、[variant-v2.css](../../../frontend/src/components/variant-v2.css)、[variant-catalog-layout.css](../../../frontend/src/components/variant-catalog-layout.css)、[PredictionToolkit](../../../frontend/src/components/PredictionToolkit.tsx)、[ResidueEvidence](../../../frontend/src/components/ResidueEvidence.tsx)。

| ID/优先级 | 问题与证据 | 必须关注的信息 | 提示/可减内容及处置 |
| --- | --- | --- | --- |
| T01 / P1 | **代码确认：** PredictionValue在有分数但无`source_pred`时输出`No source category`，每格重复 | 工具名、真实分数、尺度/方向；有来源分类时显示该分类 | **删除默认单元格这行占位**。必要时详情解释“来源未提供类别标签”；不删除分数、不补造分类、不把它当成数据库缺失 |
| T02 / P1 | **截图反馈＋代码确认：** 来源按钮声明10px，T01占位9px；二者虽非严格同字号，却均落在微小辅助文字层 | ClinVar/gnomAD等真实来源及可进入证据的性质 | 来源入口建议12–13px，文字与点击性明确；无需靠增加彩色标签数量突出。删除无效占位优先于进一步缩小它 |
| T03 / P1 | **代码确认：** 主表表头有10px、预测列辅助信息9px声明；长标题换行后密而碎 | 每列字段意义、预测工具名、频率所属人群、代表转录本身份 | 表头12–13px；尺度/方向用短语保留；字段机器代码移到详情/复制入口，不用全大写和小号字硬塞 |
| T04 / P1 | **代码确认：** 每个预测单元格可同时包含分数、小量尺、0/1端点、类别/空类别 | 分数＋真实分类；同工具量尺说明 | 尺度端点/方向可在列头或固定图例解释一次，删除空类别；保留不同工具的独立尺度，不把所有工具归一到同一色条 |
| T05 / P1 | **代码确认：** FrequencyValue逐行重复人群名，表外也有当前population选择 | AF、当前人群、缺失与真零 | 若整列人群一致，将人群固定在列头；只有行级不同或特殊状态才逐行标注。单位/百分比表达保留，不能把缺失显示为0 |
| T06 / P1 | **代码确认：** ResidueEvidence无ClinVar标签时逐行写`No source label`；ConsequencePills无值写`No consequence` | 真实分类/后果；读者不能把未知当成benign或无后果 | 固定列可用统一`—`并在列级说明，详情提供缺失原因；不需要每行完整句子。不能删除实际未知类别所占的统计记录 |
| T07 / P2 | **代码确认：** ReviewStars缺失时可同时输出Review unknown、Unknown review status、No source review status | 已有review等级，或明确“未提供”，不是0星 | 合并为一次状态；缺失不能画成零星级，详解仅在帮助/详情出现一次 |
| T08 / P1 | **截图＋代码确认：** Prediction toolkit的字段数、工具数、Featured卡片占据较大面积，真实变异结果在更下方 | 当前选中的工具、工具类别、适用对象；真实结果 | 覆盖数降为辅助摘要；工具介绍按需展开。审查Featured是否过度抢占主结果，不能仅凭大卡片暗示某工具普遍更权威 |
| T09 / P2 | **代码确认：** PredictorPicker卡片同时常驻名称、组别、字段代码、含义、尺度、覆盖数及展开说明 | 工具名称、适用对象、尺度/方向、选择状态 | 机器字段代码/完整出处按需展开；同组类别无需每卡重复；覆盖数保留但不能比工具用途醒目 |
| T10 / P1 | **截图＋代码确认：** distribution的图例与toolbar文字均为相近小字 | 颜色分类、坐标、选区结果 | 按第4节重排；保留临床组含义，操作提示不再与图例等权 |

### 5.2 Sequence、Atlas与Structure

维护入口：[SequenceViewer](../../../frontend/src/components/SequenceViewer.tsx)、[SequenceRangeNavigator](../../../frontend/src/components/SequenceRangeNavigator.tsx)、[FullSequenceAtlas](../../../frontend/src/components/FullSequenceAtlas.tsx)、[full-sequence-atlas.css](../../../frontend/src/components/full-sequence-atlas.css)、[StructureViewer](../../../frontend/src/components/StructureViewer.tsx)、[viewers.css](../../../frontend/src/components/viewers.css)。

| ID/优先级 | 问题与证据 | 必须关注的信息 | 提示/可减内容及处置 |
| --- | --- | --- | --- |
| T11 / P1 | **原截图问题；已有在途改善：** Topology方法及来源平铺成多行。读取时已改Popover＋Details | 当前启用的来源/层数、注释或预测性质、是否关闭 | 保留紧凑当前选择；未选来源按需打开；方法/溯源再展开。验收摘要不可只剩一个无意义总数，也不能把所有来源名塞回摘要 |
| T12 / P1 | **原截图问题；在途修改需复核：** Sequence拖动时读者需远处找起止输入框或刻度 | 指针残基编号、当前起止区间、选择长度 | 拖动附近固定可读数字；坐标13px左右且等宽数字；“Drag to select”属于次要提示，不能比实际坐标更醒目 |
| T13 / P1 | **截图＋代码确认：** Atlas模式说明、Colour by、色阶及PTM summary密集排布；色阶存在11/12px声明 | 当前主量尺、档位/方向、单位、独立PTM/Domain/Topology含义 | 主色阶邻近序列、13px左右；边界/标记图例另成一组。解释长句折叠，PTM数量摘要不挤占主量尺标题 |
| T14 / P1 | **代码确认：** 灰色在不同模式分别表示无评分/无注释，选择描边也有独立含义 | 当前模式的灰色/零值含义，选中轮廓含义 | 这些图例不能因“没数据就不写”而删；切换时同步更新，不常驻列出其他模式所有规则 |
| T15 / P2 | **代码确认：** Atlas有模式解释、来源独立性、hover提示等多层文字 | 只保留会改变当前解读的短限定，如来源独立/条纹为多类标签 | 常规点击/hover说明收敛到首次空态或帮助；长期页面保留结果优先，不反复教育已完成操作的用户 |
| T16 / P1 | **原截图问题；在途修改需复核：** Structure滑条主视觉是长色带，具体残基不够直观 | 预览范围、已提交范围、canonical坐标及model映射状态 | 当前范围靠近滑条，必要时显示残基字母；预览与已应用结果用清楚文字区分。不要以相同小字混写所有操作说明 |
| T17 / P1 | **代码确认：** Structure同时有Ribbon状态、Applying colors/已应用提示、selected residue、底部图例 | model、表示方式、科学着色模式、真实映射和选区 | “应用成功”常态句可以合并到模式摘要；loading/error要保留。科学图例、missing与选区样式始终可见，不能因为界面整洁而移入帮助 |

### 5.3 Expression与AlphaGenome

维护入口：[ContextDisplay](../../../frontend/src/components/ContextDisplay.tsx)、[ContextPanels](../../../frontend/src/components/ContextPanels.tsx)、[ExpressionMatrix](../../../frontend/src/components/ExpressionMatrix.tsx)、[expression-assay.css](../../../frontend/src/components/expression-assay.css)、[expression-matrix.css](../../../frontend/src/components/expression-matrix.css)、[AlphaGenomeExpression](../../../frontend/src/components/AlphaGenomeExpression.tsx)。

| ID/优先级 | 问题与证据 | 必须关注的信息 | 提示/可减内容及处置 |
| --- | --- | --- | --- |
| T18 / P1 | **原截图问题；已有在途改善：** HPA nTPM/pTPM等被当成并列数据集身份。当前代码已出现RNA/Protein与context导航 | 数据类型→数据库/集合→组织、细胞或样本context | 单位归测量说明，不充当分类名；来源12–13px，当前context14–16px。本文不据缩写臆断定义，不授权不同单位合并比较 |
| T19 / P1 | **代码确认：** 新collection按钮仍有strong11px/small9px声明，数据库名12px | 能区分相同数据库下的正常组织、癌症样本、细胞系、单细胞等 | context名称提升为清楚的13–14px主行；方法/单位次行。结构改对不等于字体层级已解决 |
| T20 / P1 | **原截图问题；已有在途改善：** 旧版68条数值全部展开；当前INITIAL_GROUPS=10且有Show more/all/fewer | 代表性可见记录、当前已显示/总量、完整数据入口 | 保留有限预览，明确不是只有10条数据；扩展前后量尺应保持全集合一致。需实页验收后才关闭此项 |
| T21 / P1 | **代码确认：** 表达行context与数值各11px，单位9px；条形图视觉上比名称/单位更强 | context、真实值、单位及原始/项目汇总身份 | 名称13px、值13–14px、单位12px左右；条形为比较辅助。不要用加粗大数字掩盖“测的是什么” |
| T22 / P2 | **代码确认：** 多行重复source value，头部/说明/footer多次交代原值/来源；每条又包边框 | 原始值与project median区别，缺失状态 | 同质单值列表将source value移到组标题；project median、n和缺失等特殊身份保留在对应组。多层说明合并，行容器可用轻分隔替代同等卡片 |
| T23 / P1 | **代码确认：** ex-scale及ex-value-note有10px声明，承载log1p、线性/发散、原单位等解释 | 条长量尺、方向、单位、当前比较范围 | 提炼为12–13px可见短图注，如“Bar length: log1p · values: original TPM”；公式/方法详解再展开，不把全部关键规则放成微小长段 |
| T24 / P1 | **代码确认、待实页：** AlphaGenome有Start here、What is shown、resolution、context matching、Mean/Maximum及Predicted等多层信息 | 预测性质、modality、biosample/context、坐标/分辨率、单位和具体信号 | 预测身份不可隐藏；保留当前轨道读数与必要范围。常态教学、完整方法和重复统计按需展开；Mean/Maximum不能比轨道身份更先吸引注意 |

### 5.4 Overview、细胞定位、GO、通路与药理

维护入口：[Overview](../../../frontend/src/components/Overview.tsx)、[OverviewLocations](../../../frontend/src/components/OverviewLocations.tsx)、[OverviewOntology](../../../frontend/src/components/OverviewOntology.tsx)、[OverviewEvidence](../../../frontend/src/components/OverviewEvidence.tsx)、[overview-v2.css](../../../frontend/src/components/overview-v2.css)。

| ID/优先级 | 问题与证据 | 必须关注的信息 | 提示/可减内容及处置 |
| --- | --- | --- | --- |
| T25 / P1 | **截图问题：** 概览身份信息有主标题，但后续多个小计数入口、卡片边框与类型信息竞争注意 | 对象身份、膜蛋白类型、主要功能与定位 | 类型/性质建立稳定位置与清楚文字，计数留作覆盖摘要。Basic information等泛标签可弱化，不为每个属性铺标签底色 |
| T26 / P1 | **原截图问题；已有在途改善：** 细胞区域文字受底图/淡化影响。当前已独立绘制标签并加表面 | 区域名称、所选区域、有无当前来源注释 | 标签优先保证可读，绘制于形状之上；“未注释”不等于生物学不存在。读取代码不能代替缩放后标签碰撞/字体的实际核验 |
| T27 / P2 | **代码确认：** 原始label计数、注释可点提示、display group说明可能同时出现 | 来源与applies-to范围、区域名、真实原始标签 | 计数保留为辅助；hover/click教学收敛。基因层来源与蛋白/isoform范围差别必须保留，不能只剩数据库Logo |
| T28 / P1 | **代码确认：** GO evidence badge有10px声明，术语、分类、来源计数和证据code易混成标签集合 | GO术语含义、MF/BP/CC类型、实验/计算等证据性质 | 术语13–14px；证据性质可读而紧凑。代码及完整文献按需查看；不能把计数大字做成“功能强弱” |
| T29 / P2 | **代码确认：** Reactome pathways数量可达28px声明，ID/类别/来源记录说明较小 | 通路名称与当前主题，关联不是活性/富集 | 数量次于通路识别；短限定保留一次。ID作为辅助/复制项，完整层级按需，不反复重复Reactome来源 |
| T30 / P1 | **代码确认：** 药理action标签10px，与来源计数/记录类型等多种小标签并列 | 配体、靶标、作用性质、亲和力类型/值/单位及关系符号 | 作用性质需更清楚；覆盖数量降权。空字段可不渲染，但真实未指定机制不得推成无作用；完整assay和出处放详情 |

### 5.5 QTL、Interactions与Diseases

维护入口：[ContextPanels](../../../frontend/src/components/ContextPanels.tsx)、[ContextDisplay](../../../frontend/src/components/ContextDisplay.tsx)、[PpiOverview](../../../frontend/src/components/PpiOverview.tsx)、[ClinvarConditions](../../../frontend/src/components/ClinvarConditions.tsx)、[context-v2.css](../../../frontend/src/components/context-v2.css)。本组主要为源码审查，缺少本次新截图，需真实页面复核实际视觉权重。

| ID/优先级 | 问题与证据 | 必须关注的信息 | 提示/可减内容及处置 |
| --- | --- | --- | --- |
| T31 / P1 | **代码确认、待实页：** QTL入口以来源记录数量卡、tissue导航、QTL type按钮逐层展开 | 来源、QTL类型、组织context，记录的效应类型与值/显著性 | 来源计数降权；实际类型/context比导航提示更醒目。Effect类型不是可随意删的小备注；必须与数值一起读，不能只突出P值 |
| T32 / P1 | **代码确认、待实页：** PPI有来源/collection/topic/记录数和多层选择提示 | 互作对象、物理/其他证据性质、检测方法、条件；突变记录的作用方向 | 保留数据类型；Step/Choose教学在选择完成后收敛。普通互作和突变效应不能因统一样式被当作同一证据 |
| T33 / P1 | **代码确认：** PPI存在Negative evidence、Non-protein participant及canonical mapping unverified | 会改变结果解释的真实状态 | **不得作为“负面/缺失文案”一起删除**。这些是实质证据或限制，需清楚显示；一般source字段缺失可以不列空行 |
| T34 / P1 | **代码确认、待实页：** Disease来源入口伴随计数及不同证据类型；ClinVar/PTMD2关系不同 | 疾病/条件名称、来源断言性质、review/conflict、对象关联层次 | 疾病名称和性质优先；condition sets、SNVs only、候选蛋白关联等关键口径保留简短标注。不能将不同来源都只包装成Disease标签 |
| T35 / P2 | **代码确认：** ClinvarConditions无标识时逐项写No source condition identifier supplied | 条件名称、实际可用标识、相关记录入口 | 标识为空则不显示该副行，或详情说明一次；保留有效名称和计数，不制造虚构ID。与review未知的科学限制分别处理 |

### 5.6 首页、搜索、数据概览与共享详情

维护入口：[HomePage](../../../frontend/src/components/HomePage.tsx)、[HomeEvidence](../../../frontend/src/components/HomeEvidence.tsx)、[ProteinSearch](../../../frontend/src/components/ProteinSearch.tsx)、[DatabasePages](../../../frontend/src/components/DatabasePages.tsx)、[ui.tsx](../../../frontend/src/components/ui.tsx)、[design-system.css](../../../frontend/src/design-system.css)。

| ID/优先级 | 问题与证据 | 必须关注的信息 | 提示/可减内容及处置 |
| --- | --- | --- | --- |
| T36 / P2 | **代码确认、待实页：** 首页7层入口以大数字和小单位构成强视觉，容易先读规模而忽略可做什么 | 数据类型、研究入口、不同计数单位 | 类别名称不能弱于计数单位到难扫读；规模保留但不暗示可相加。Choose a layer等提示低权重，完整计数口径在帮助中 |
| T37 / P2 | **代码确认：** 搜索结果有Gene not assigned、Length unavailable占位；过滤旁长期展示分类口径长句 | 蛋白名、基因名（如有）、accession及必要长度 | 无基因名可省副行；长度固定列可统一`—`。搜索结果数、筛选条件保留；复杂分类口径放按需说明，不抢主结果 |
| T38 / P1 | **代码确认、待实页：** 数据概览并列多种规模数字；文档还有memVar snapshot与upstream versions | 指标类型、计数对象、来源版本与构建时间区别 | 单位/指标标题是读数必需信息，不能比数字弱到无法辨认；版本分别明确标签，不能合成模糊“updated” |
| T39 / P2 | **代码确认：** 共享Fields已过滤空值，但专用组件仍大量手写No…；各弹层容易产生不同空值规则 | 用户主动查看的结果是否存在、错误/加载状态、科学限制 | 沿用“空属性不列出”的合理模式；用户主动请求却无结果时保留一次整区空态。避免同一弹窗标题、正文、字段三次声明未知 |
| T40 / P1 | **代码确认：** CSS存在多轮覆盖和`!important`，同一信息角色缺少统一字号入口 | 跨页面同类信息具有可预测的视觉层级 | 先按语义建立title/legend/value/source/control/hint角色，再定向收敛样式。不要继续追加全站small统一缩小规则；本审查不授权大规模CSS重写 |
| T41 / P1 | **用户追加反馈＋原截图：** 普遍小字与大容器留白并存，信息密度不高却难阅读 | 正文、图例、来源、context、数据标签与数值的直接可读性 | 按第3节同步调整字体与容器；先放大关键字，再清理重复padding、固定高度与空副行。保留模块分隔和合理点击区域，不以全面压缩或全页缩放代替设计 |

## 6. 删除、收敛与必须保留的边界

“删除展示”不等于删除数据库字段、过滤记录、改变分类或隐藏科学限制。

| 情况 | 建议处置 | 不允许的误改 |
| --- | --- | --- |
| 有数值、无来源类别：No source category | 默认单元格不渲染占位；详情必要时解释 | 不把有分数误写成无来源数据，不生成项目自己的类别标签 |
| 可选标识/附加描述为空 | 不渲染整条空副行 | 不删除仍有效的对象、名称或记录 |
| 每行重复同一来源/人群/单位说明 | 在组/列级显示一次；发生差异的行保留 | 单位或人群切换后未同步标题；把不同来源/单位合并 |
| 固定列的数值缺失 | 使用一致`—`并提供列级说明，详情保留原因 | 缺失替换为0、画成低值，或把不匹配伪装为来源本身缺失 |
| 临床图中真实Unclassified计数 | 存在这类数据时保留灰色类别与可理解名称 | 删除图例但保留灰色柱段；从总数移除记录；视作benign |
| 当前图中计数为0的非交互类别 | 可考虑只显示当前存在的类别；固定比较图例或筛选选项按场景保留 | 改变分类全集/筛选能力，让颜色在更新时改义 |
| 无可用评分、未映射、冲突、预测/实验身份 | 简短而明确地保留；必要时提升权重 | 因“减少No…”一律删掉，导致用户误判证据性质 |
| 完整方法介绍、原始字段代码、长出处 | 默认折叠，保留可键盘访问入口 | 把读当前图必需的量尺、单位、方向也藏进去 |
| 加载、接口失败、用户主动查询无结果 | 整区保留一次明确状态，必要时有重试/恢复 | 默默留白，让用户以为结果为0或尚未操作 |

## 7. 建议整改顺序与验收清单

先处理Variant catalog和distribution：它们同时暴露了字号、信息角色和必要性问题，适合作为统一规范的真实样例。随后应用于Sequence/Structure、Expression，再检查Overview与其余证据模块。源代码已有改善项先复核，不重复重做。

- [ ] **删减**：默认预测单元格不再重复No source category；可选空属性不渲染空副行；真实分数、记录数和记录集合不变。
- [ ] **图例**：不打开帮助就能识别颜色对应的类别、单位/方向与坐标范围；图例明显高于鼠标操作提示的阅读优先级。
- [ ] **来源**：ClinVar/gnomAD等入口清楚可读，视觉地位高于空属性说明；可操作与静态标签可区分。
- [ ] **表格**：无需逐行读重复解释即可比较数值；列头能说明对象、工具、人群与量尺；横向滚动只限必要表格区域。
- [ ] **类型/context**：Expression第一眼能辨认RNA/Protein、数据库、集合context；不依赖nTPM/pTPM等缩写猜类型。
- [ ] **选择状态**：拖动时就能读残基位置与区间；范围变化不会只更新远处的小字；清除后能够理解恢复了什么。
- [ ] **缺失边界**：真零、无数值、未匹配、无分类、无记录分别核对；不能以删文案为由合并状态。
- [ ] **空间**：重要信息靠位置和邻近关系组成阅读单元；删除文案后不保留无意义高度；不通过全面加深边框制造更多同级区块。
- [ ] **字号与留白比例**：同区域整改前后对照，检查关键文字是否增大、容器多余空间是否收敛；不能只增大标题而保留小号图例，也不能盲目压缩必要分隔。
- [ ] **字体**：1440级桌面与1280宽度下核对计算样式；尤其检查9–11px承载关键图注/来源/单位的情况，记录实际覆盖规则。
- [ ] **键盘与缩放**：按需内容有明确入口、可键盘访问；放大文字后不截断类别、单位和当前值。必要解释不能只有鼠标title。
- [ ] **验证方式**：同一真实数据截取整改前后区域，明确要求读者识别“对象/类型、来源/context、图例与当前结果”；不要仅以字体变大或构建成功关闭问题。

尚待补充的证据：在主任务本批代码稳定后，对QTL、PPI、Diseases、AlphaGenome以及数据概览进行新截图和计算样式检查；核对所有依赖PredictionValue的目录/详情是否一致。本文列出的是待落实/复核清单，没有将这些页面标为视觉验收通过。

## 8. 表格与展开注释专项复审

### 8.1 范围与证据

2026-09-22 追加。逐项检索当前前端入口依赖中的 `DataTable`、原生 `table`，并检查条件列分支、弹层、Disclosure、原生details及用卡片排布的证据记录。下面B编号是表格/列表审查位置，D编号是展开详情位置，不替代T编号和原阶段问题编号。

**覆盖的是当前代码中的呈现入口与字段，不是逐个点击后的运行态验收。** 两张用户截图直接证明 GenCC 与普通互作表的视觉问题；其余条目根据代码提出整改或复核要求。组件文件中的条件分支不一定当前可达：`Overview.tsx` 的旧pathways表分支单独标记；当前Reactome入口检查 `OverviewOntology.tsx`。未接入当前入口依赖的 `Evidence.tsx` 旧表不冒充实际在用页面。共享 `ui.tsx` 的表格渲染器作为统一规范维护点，不另计一张科研表。

### 8.2 两张截图：最值得先改的细节

#### GenCC evidence

**直接观察：** 数据库来源GenCC与分类结果都用紫色描边标签；Definitive、Strong、Moderate、Limited、Supportive仅靠单词辨别。遗传方式也用粗字标签，整行多个标签竞争；重复的Not available占满Relationship列。行高偏大，主要用于容纳标签和padding，未换来更多有效解释。

**代码确认：** `ContextPanels.tsx` 中 `ContextTag(kind='classification')` 统一使用 `#6d28d9`；疾病主表未列Submitter，详情才显示。`Source report` 无URL时仍将 `View report` 传入LinkOut，因此存在外观像操作、实际无链接的文字。

| 信息 | 阅读优先级 | 建议表达与必要性 |
| --- | --- | --- |
| 疾病名称 | 首要对象 | 15–16px、适度半粗，保留完整名称和详情入口；长名称换行，不能为对齐强制裁掉辨别词 |
| Source classification | 首要判断 | 14–15px半粗；按来源定义区分结论，保留完整名称与简短解释入口，不再所有类别同一种紫色 |
| 提交机构/断言身份 | 解释重复行所必需 | 提交机构宜在行内可见。若API尚未提供，标为显示依赖；不得凭疾病名称合并记录。日期/断言ID在详情可查 |
| 遗传方式 | 重要性质 | 14px、清晰文字；AD/AR是类别差异，不是优劣或强弱。完整名称优先，可用紧凑中性标签，不必和分类结果一样粗重 |
| GenCC | 来源溯源 | 单一来源视图可在标题处清楚显示一次；混合来源表逐行保留。来源身份不应与证据强度共用颜色含义 |
| Relationship中的Not available | 空属性 | 若当前所选集合在契约上不提供此字段，可不显示该列；不能仅凭当前页全空隐藏后续页真实关系。需要固定列时用`—`和一次说明 |
| Source report | 辅助操作 | 有URL时显示明确链接；无URL不显示伪操作。若原报告不可用是用户正在追查的问题，在详情说明一次 |
| Selected records、单页分页器 | 导航辅助 | 降低标题前缀权重；已知仅一页时无需整套禁用前后页和跳页框，保留记录数即可 |

**分类不等于统一分数。** Definitive、Strong、Moderate、Limited表达不同支持程度；Supportive是用于未按细粒度等级整理的较宽类别，不能擅自放在Moderate与Limited之间作为数值等级。Disputed、Refuted、Animal Model Only、No Known Disease Relationship也不能塞进同一条由低到高的色阶。依据：[ClinGen对GenCC分类的说明](https://clinicalgenome.org/docs/gencc/)、[基因—疾病有效性分类定义](https://www.clinicalgenome.org/docs/gene-disease-validity-classification-information/)。GenCC FAQ直接打开返回403，本节使用可访问的官方ClinGen说明核对，未声称成功读取FAQ全文。

建议先按“支持程度／争议或反驳／仅动物证据／未建立关系”区分语义，再为已定义的支持程度提供可辨认的文字及辅助颜色。Supportive单独解释。配色仅编码来源已有分类，不生成memVar自己的证据评级；不用临床Pathogenic红色直接表达Definitive。

#### Interaction evidence

**直接观察：** 小分子ID、蛋白名称、物种、实验方法、互作性质的区分不够；非蛋白参与者被塞进Evidence列。重复的IntAct标签、机械重复的chemical synthesis文本占空间，而PTK2来自chick这一重要差异仅在小字副行。

| 信息 | 阅读优先级 | 建议表达与必要性 |
| --- | --- | --- |
| 参与者名称/标识 | 首要对象 | 名称15–16px半粗；没有可靠名称时保留规范ID，不臆造名称。`chebi:"CHEBI:16761"` 的包裹格式可在展示层清理，原值在详情保留 |
| 对象类型：protein、small molecule、peptide | 必须区分的性质 | 在参与者旁用明确类型文字或图标＋文字；将Non-protein participant从“证据等级”的视觉位置移回对象身份位置 |
| 物种 | 判断适用范围所必需 | 非人类及不同参与者物种应直接可见，不能与无关元数据同为极小灰字。不是风险等级，不一律套警告色 |
| Interaction category | 首要科学性质 | 14–15px；明确reaction、association等来源类别，不能将所有行暗示为直接物理结合 |
| Detection method | 重要证据方法 | 14px正常字重；方法名称可读，细节按需展开。protein kinase assay与enzymatic study不建立未经定义的高低分 |
| Negative evidence | 改变解读的状态 | 出现时显著保留，不能当作No…冗余删除；与“没有证据记录”严格区分 |
| IntAct | 来源 | 单一来源集合可提升到组标题一次；混合来源保留行级来源，不与方法或对象类别混用颜色 |
| 重复同义文本 | 可收敛 | 同一字段的重复大小写/别名可精简显示；先确认确属同义，不把生产方式、物种与来源角色误合并 |
| View evidence | 辅助操作 | 统一尾列，提供间距；不能紧贴对象类型标签造成一串文字。展开后优先呈现方法、参与者、方向和文献 |

重复参与者不证明重复记录。不同实验、参与者角色、文献或来源记录应保留；应帮助读者发现差异，而不是为了缩短表格静默去重。

### 8.3 不同“evidence”需要不同视觉语法

| 字段体系 | 应区分的内容 | 不应做的处理 |
| --- | --- | --- |
| GenCC classification | 基因—疾病有效性的来源分类；支持、争议、反驳、证据对象差异 | 全紫色；把所有类别换成统一星级；解释成变异致病性 |
| ClinVar classification / review | 分类结论与审核状态分别表达；germline、oncogenicity、somatic impact明确领域 | 仅用领域色导致同一领域不同结论全同色；把星数当致病程度 |
| GO evidence code | 代码＋可读方法名称，实验、系统发育、计算、作者陈述、整理者陈述、自动注释等证据来源性质 | 按字母顺序或个人判断打强弱分；自动注释等于错误；NOT等于缺失 |
| Reactome evidence | 当前关联记录的证据代码及来源含义 | 因出现TAS就声称展示了具体实验或本地已有逐条PMID |
| Interaction method / negative | 检测方法、对象类型、正/负证据分别表达 | 把non-protein当弱证据，把未提供方法当阴性结果 |
| Inheritance / context / object type | 非有序类别，通过名称和必要图标区分 | 红绿高低等级；每个普通类别都套饱和彩色大标签 |
| Mapping / availability | 已验证、未验证、无法比较、未匹配、缺失的实际状态 | 统一灰色“无数据”，或让身份关联看起来就是残基映射 |

GO代码说明的是注释获得支持的方法，官方列出六类；当前 `OverviewEvidence.tsx` 已有代码＋全称及family样式，但将IEA与computational放在同一family，仍需使“自动生成”与其他计算支持在文字上清楚可辨，不能凭颜色认定相同。依据：[GO evidence codes](https://geneontology.org/docs/guide-go-evidence-codes/)。ClinVar review status表示对分类的审核支持，且不同分类领域的聚合规则存在差异，不能套用统一的“可靠性分数”。依据：[NCBI review status](https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/)。

### 8.4 表格与记录列表逐项清单

以下“收敛”均只指展示。重要字段已存在时要求复核其权重，不代表要求重复开发。优先级P1：可能影响科学解读或主路径扫读；P2：主要影响阅读效率。

#### Overview、身份与膜注释

维护入口：[Overview](../../../frontend/src/components/Overview.tsx)、[OverviewOntology](../../../frontend/src/components/OverviewOntology.tsx)、[MembraneOverview](../../../frontend/src/components/MembraneOverview.tsx)。

| 编号 | 表格/列表 | 最值得凸显 | 值得明确区分 | 可收敛与待核对 |
| --- | --- | --- | --- | --- |
| B01 / P1 | GO原始注释表 | 术语名称、NOT、证据代码及方法 | MF/BP/CC、relation、过时术语；NOT必须贴近术语 | 单一category可在标题显示一次；GO ID次于名称，但仍可读；已有EvidenceLabel，不应重新退化成裸代码 |
| B02 / P1 | Reactome关联列表 | pathway名称、关联证据性质 | pathway与topic、TAS与IEA | 当前为OverviewOntology卡片列表；ID、来源链接次要；旧Overview的pathways表分支只列为代码残留，未证明当前入口调用 |
| B03 / P1 | Rhea反应表 | 反应式、方向、transport性质 | 反应ID与生化内容 | 不把化学方程式压小以迎合统一行高；来源ID不与方程式争夺首位 |
| B04 / P1 | Rhea参与者子表 | 参与者、化学计量系数、方程式侧 | 反应左右侧与方向 | side_order若是内部序号，核实契约后显示人类可读名称；不可猜测0/1对应底物/产物 |
| B05 / P1 | Pharmacology表 | ligand、action、affinity及量尺/单位 | record category、assay、Ki/Kd/IC50等原始测量性质 | Type为None的逐行Not stated可收敛；不能只留裸数值；亲和性数值不应跨量尺比较强弱 |
| B06 / P1 | External identifiers | 标识及其实际适用对象 | entry/gene/isoform等object type、source pairing | 来源整列重复可按组呈现；重要的是ID对应谁，不能把applies to压成可忽略小字 |
| B07 / P1 | Isoforms | isoform ID/名称、序列可用性、长度 | 默认序列与其他isoform；不可获取与不存在 | 长度列保留aa；不因序列缺失隐藏isoform；可选名称空时不重复No name |
| B08 / P1 | DeepTMHMM segment表 | segment类型、起止位置 | 原始序列坐标与canonical映射、预测性质 | 来源方法在表头说明一次；Start/End数字右对齐；不能默认源坐标就是当前蛋白坐标 |

#### Sequence、Structure与Variants

维护入口：[SequenceAnnotations](../../../frontend/src/components/SequenceAnnotations.tsx)、[ResidueEvidence](../../../frontend/src/components/ResidueEvidence.tsx)、[InterfaceAnnotations](../../../frontend/src/components/InterfaceAnnotations.tsx)、[VariantCatalog](../../../frontend/src/components/VariantCatalog.tsx)。

| 编号 | 表格/列表 | 最值得凸显 | 值得明确区分 | 可收敛与待核对 |
| --- | --- | --- | --- | --- |
| B09 / P1 | PTM explorer | residue、modification、来源 | 修饰类型、来源记录数与位点数、证据性质 | 残基及修饰名称14–15px；来源不是微小脚注；同一原始记录的多个字段不重复算支持数 |
| B10 / P1 | Residue FeatureEvidence：PTM分支 | 当前残基、修饰及证据 | Source records与独立实验支持不同 | 弹窗已给残基时避免每区重写长提示；来源短名可重复，不能缩到难读 |
| B11 / P1 | Residue FeatureEvidence：annotation分支 | 注释名称、span | domain/topology/其他注释类型、预测/注释性质 | span不是强度，不采用等级色；原始证据展开，固定来源可组级显示 |
| B12 / P1 | Residue variants/predictions | 氨基酸替换、基因组变异、当前模式结果 | consequence、ClinVar类别、不同评分工具 | 模式改变列位置时仍保留工具名称/方向；不要将所有分数统一成蓝色数字而丢失尺度 |
| B13 / P1 | 残基结构接触表：OPM/MPLID等来源分支 | PDB、chain、source residue及观测量 | OPM depth/boundary Å、source contact、lipid是不同字段体系 | 按来源保留量尺；身份次序固定；不能把多种来源变成一个无单位“contact score” |
| B14 / P1 | PeSTo每结构片段表 | 结构片段、当前binding类别结果 | 不同binding类别、片段范围、预测身份 | 动态列需解释类别；空值与0分开；不能把最大值自动当临床风险 |
| B15 / P1 | SPPIDER-seq每partner表 | partner sequence、两种角色的结果 | query作为receptor或peptide | 角色是解读必需信息，列头不能压缩成看不懂的简称；缺失不能画成零长度有效值 |
| B16 / P1 | Variant catalog主表 | 变异身份、consequence、临床结论、选定工具分数 | genomic/protein位置、代表转录本、来源、AF人群与评分量尺 | 重点沿用T01–T09；删重复No source category；避免每单元格重复量尺刻度和固定人群名 |

#### Context、疾病及公共数据说明

维护入口：[ContextPanels](../../../frontend/src/components/ContextPanels.tsx)、[ClinvarConditions](../../../frontend/src/components/ClinvarConditions.tsx)、[AlphaGenomeExpression](../../../frontend/src/components/AlphaGenomeExpression.tsx)、[DatabasePages](../../../frontend/src/components/DatabasePages.tsx)。

| 编号 | 表格/列表 | 最值得凸显 | 值得明确区分 | 可收敛与待核对 |
| --- | --- | --- | --- | --- |
| B17 / P1 | QTL记录表 | variant、tissue/context、P值及effect | eQTL/sQTL、effect_type、assembly | effect measure不能藏成极小字；核对小P值格式是否被通用number格式近似成0，尚未用数据复现；同assembly可组级标记 |
| B18 / P1 | 普通互作表 | partner、类型/物种、interaction性质 | method、negative evidence、来源 | 按8.2处理；重复IntAct不应强于方法；对象类型离开Evidence列 |
| B19 / P1 | IntAct mutation表 | mutation、effect on interaction、partner | sequence change、实验作用与临床分类 | feature ID和publication为次要溯源；generic mutation不等于增强/削弱；已有MutationEffect需复核视觉而非重建 |
| B20 / P1 | PTMD疾病记录表 | disease原名、PTM类型、cell context | State原始代码、candidate association、未验证canonical位置 | State不能凭直觉转红绿；MutationSite保留源文本；无需空CellType长句，但映射限制必须可见 |
| B21 / P1 | GenCC及其他疾病来源表 | disease、source classification、inheritance | 各来源断言体系、提交者 | 单独见8.2；固定紫色是代码确认问题；疾病名相同的多条断言不可自动合并 |
| B22 / P1 | Disease detail内HPO phenotype表 | phenotype、qualifier、frequency | 疾病层级注释、否定/限制、onset及原始evidence | HPO ID次于名称；频率编码核对解释后再格式化；不能把疾病表型推成每个变异的表型 |
| B23 / P1 | ClinVar condition展开SNV表 | genomic SNV、来源分类、protein position | 仅transcript change与verified UniProt位置；variation/RCV/SCV层级 | 内部variant ID可降低权重；完整condition set不可拆成独立判断；领域色不足以区分类别结论 |
| B24 / P1 | AlphaGenome splice junction表 | genomic interval、strand、predicted signal | 基因组1-based位置与蛋白残基、预测量尺 | 单位/预测性质不能只放远处介绍；不要把strand或分值做成临床风险等级 |
| B25 / P2 | 数据文档VersionTable | module、memVar snapshot、upstream version | 本地快照与上游版本 | 路径/长版本按需换行或详情；不能缩成极小字，也不能合成一个Updated日期 |

### 8.5 展开注释逐项审查

展开不意味着把所有字段恢复为同级表单。每个详情首先回答“这条记录是什么、得到什么结论、依据什么、适用于谁”，然后才是原始字段。

| 编号 | 详情入口及源码 | 展开后必须首先看到 | 第二层/按需信息与具体问题 |
| --- | --- | --- | --- |
| D01 / P1 | GO/功能注释：[Overview](../../../frontend/src/components/Overview.tsx) | 术语/功能、relation、NOT、代码＋方法、引用 | subject/form/extension与mapping有各自标签；内部状态不应全挤同一Fields网格。false布尔状态不必各成醒目标签；真实NOT与obsolete显著保留 |
| D02 / P1 | Rhea与pharmacology：同上 | 方程式/方向；或ligand、action、测量结果及单位 | 原始relation、measure、范围与来源作为第二层；不能把原始nM与变换后的affinity同字号无标题并列 |
| D03 / P1 | location：[OverviewLocations](../../../frontend/src/components/OverviewLocations.tsx) | 原始location、来源、applies to、reliability | 映射到示意图的region不是新生物学定位；isoform/topology在相关时直接可见；source notes折叠，避免重复卡片每条又宣读作用域长句 |
| D04 / P1 | 膜来源：[MembraneOverview](../../../frontend/src/components/MembraneOverview.tsx)、[MembraneTopology](../../../frontend/src/components/MembraneTopology.tsx) | 来源性质、segment/观测对象、原始与canonical区间、映射状态 | method/constraint/ID有明确分组；OPM geometry与预测segment不能同名“evidence”；来源不匹配限制不能藏到底部 |
| D05 / P1 | 序列FeatureDetails/RecordEvidence：[SequenceAtlas](../../../frontend/src/components/SequenceAtlas.tsx) | annotation名称、当前范围、来源方法、主证据 | 通用原始字段递归展示容易产生同级label/value堆叠；先做摘要，嵌套Source annotation与长参考文献后置，避免每个字段都加小标题 |
| D06 / P1 | 残基与interface：[ResidueEvidence](../../../frontend/src/components/ResidueEvidence.tsx)、[InterfaceAnnotations](../../../frontend/src/components/InterfaceAnnotations.tsx) | 当前残基、所选科学模式的结果、结构/partner身份 | 原始span、source residue、chain和量尺保留；不同模式的证据分组不能看起来是一份统一质量评分 |
| D07 / P1 | Variant ClinvarEvidence：[VariantEvidencePanels](../../../frontend/src/components/VariantEvidencePanels.tsx) | 分类结果、领域、review状态、condition | origin、submitter、ID和原始字段次级；三个领域不要仅以色彩区分；不将所有RCV/SCV ID简单并列成同级“结论” |
| D08 / P1 | PredictionDashboard：同上 | 工具名称、真实分数、来源类别（有时）、量尺方向 | method/provenance折叠；Featured是界面选择，不能比Scored/Context not matched更像科学质量认证；No source category不重复 |
| D09 / P1 | PopulationDetail：同上 | AF、AC/AN、当前population与scope | source filters和字段代码第二层；条长/色阶如非同一变换需解释；grpmax不是一个普通人群；缺失与真实0清楚区别 |
| D10 / P1 | TranscriptEvidence：同上 | 代表转录本、protein/coding change、sequence relation | MANE/APPRIS/TSL等来源字段后置；全长相等不证明变异坐标正确的限定简短可见；不要把全部unmatched/missing统称No data |
| D11 / P1 | StabilityEvidence：同上 | model、ΔΔG、单位、来源符号约定、方向 | 当前已有方向与原始约定说明；复核单位字号，不重复全局讲解；按当前最大绝对值缩放的轴需明确，不能用跨变异条长比较 |
| D12 / P1 | Expression/QTL RowDetails：[ContextPanels](../../../frontend/src/components/ContextPanels.tsx) | 数据类型、数据库、context、值＋单位；QTL effect measure＋effect/P值 | 原始字段代码后置；当前位置将多字段平铺，应分对象/测量/出处。原始缺失不变成0；关键context不藏在Source details |
| D13 / P1 | PpiDetail：同上 | 参与者、对象类型/物种、interaction/method、阴性或mutation effect | participant roles与source features按需；文献入口明确；source collection membership属于归属信息，不当证据等级 |
| D14 / P1 | DiseaseDetail/DiseaseSourceDetails：同上 | 分类＋提交者＋遗传方式，逐断言区分 | 原始phenotype、mapping key、references分层；同病不同分类不能只显示相同紫框；仅前100条提示属于完整性限制，应可读 |
| D15 / P1 | PTMD详情：同上 | 原始disease/PTM、cell context、association及坐标未验证 | State/source code保留，不解释成项目评级；source sequence/位置/引用后置；重复字段可收敛，未验证警告保留一次显著位置 |
| D16 / P1 | ClinVar RCV/SCV：[ClinvarConditions](../../../frontend/src/components/ClinvarConditions.tsx) | RCV完整condition-set分类；各SCV提交者及判断 | 当前EvidenceTag按领域统一色，需使类别结论也可区分。版本匹配、XML日期、评估日期不同；SCV review不缩成难辨脚注；TraitSet成员是导航，不能各继承整组分类 |
| D17 / P1 | ClinGen dosage Disclosure：[ContextPanels](../../../frontend/src/components/ContextPanels.tsx) | gene、haploinsufficiency、triplosensitivity各自来源结论 | 不能合成“dosage evidence score”；来源报告次级，未知代码仅原样显示并待核定义，不能凭数字大小上红绿 |
| D18 / P2 | AlphaGenome轨道卡/帮助：[AlphaGenomeExpression](../../../frontend/src/components/AlphaGenomeExpression.tsx) | modality、context、坐标、signal及prediction身份 | Start here/Modalities等介绍可按需；track来源和量尺不是可删除教学提示；contact map与junction不能统一成RNA表达量 |

### 8.6 具体排版约束与增补验收

以下为建议起点，继承第3节字号基线，不是已验证的CSS参数。

- **主对象与主结果**：表格内15–16px对象名，14–15px科学结果；通常500–600字重。单行不把名称、来源、结果、辅助链接全部加粗。
- **重要性质**：类型、context、遗传方式、检测方法通常14px；次级ID/来源13–14px。对于单一来源标题，来源仍须可读，而非缩成9–10px角标。
- **提示**：12px正常字重适用于纯操作说明；单位、否定、方向、映射限制不能仅因“说明文字”归入弱提示。
- **行高与留白**：可先以单行44–48px、双行60–68px作为桌面试排参考，内容需要时自然增高；减少重复padding和空副行，不固定高度裁文字，不牺牲点击区域。
- **列宽**：优先让疾病名、参与者、方法等长文本占空间；不让重复来源和空属性占同等宽度。数据列对齐以便比较，不用增加宽大卡片替代排版。
- **边框**：重点用行分隔和列对齐建立结构；移除多余的单元格内标签边框。强边框只留给选择/焦点等状态，不能给每一类信息都加框。
- **颜色**：来源身份多用中性；结果按明确语义编码；重要文字不必蓝色，蓝色首先保持操作可识别。分类名称、图例和状态文字仍可独立解释颜色。
- **原始详情**：固定“对象与结果→证据/方法→适用范围→出处与原始字段”的阅读层次，在现有模块和弹层内部实现，不要求重排整页。

新增验收项：

- [ ] GenCC各类可快速区分；Supportive没有被擅自量化；同名疾病多条记录能识别各自断言来源。
- [ ] 互作表无需展开即可辨别protein/small molecule/peptide、物种、方法及阴性证据；非蛋白对象不被表达为弱证据。
- [ ] ClinVar领域与结论、结论与review各自明确；variation、RCV、SCV不混层。
- [ ] GO保留代码与全称，NOT独立可见；自动注释性质清楚，不以色阶虚构通用强弱等级。
- [ ] 每个B/D位置逐项留下“保留/提升/弱化/折叠/不渲染”的实施选择；未出现的数据分支注明未验收。
- [ ] 无URL不显示伪链接；固定空属性不逐行占据高权重；移除冗余展示后记录数、筛选和数据含义不变。
- [ ] 同一截图同时核对字体增大与无效留白收敛；正常桌面缩放下读得出类型、单位、方法和主要结果。

**当前交付仅为审查补充。** B01–B25与D01–D18均尚未在本支线逐项实页验收；主线程已有改动需以最新页面重新核对。优先处理B21/B18两张有截图证据的表，再以B16和D16检查同类问题是否贯穿目录与详情。

## 9. 参考数据库对照：板块辨识、背景与操作引导

**最新实施补注（2026-09-22）：** 上一批GO移入Functional下方的理解已被用户纠正：实际移动Reactome，GO恢复原三列；搜索命中新增独立状态，清除搜索保留共享选择，结构Reset保留搜索及Variant筛选。Expression/QTL采用内部滚动、来源卡进一步分色。详见[最新记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#序列缩略图与局部版面)。本节持续审查边界不变。

**上批验收补注（2026-09-22）：** 用户再评指出等高空白、控件对齐、端点易用性和Reset辨识；已按本节四状态边界修订。Sequence窗口Reset保留结构选区；Structure Reset清范围和共享焦点、恢复本地残基窗口起点，保留Variant筛选。主标题、证据表列分组和GenCC浅底标签在真实页面验证，详见[本批记录](../../record/01_preview_optimization/20260922_ui_toolkit.md#空白reset与阅读层级)。原12类问题为持续审查框架，并非已全部关闭。

**后续实施状态（2026-09-22）：** 下文保留本次审查时的证据边界。主任务后续已用独立本机浏览器取得CATVariant EGFR真实字体/色表/截图，按U系列状态边界落实局部重设计并发布本地；实际覆盖、素材许可、交互验证及未完成项见[最新UI record](../../record/01_preview_optimization/20260922_ui_toolkit.md#catvariant对照与五条局部重设计)。这不代表下列全部审查任务已关闭。

2026-09-22继续补充，仅审查。此轮尝试使用Browser技能连接参考网站，返回`No browser is available`，按连接指引查询可用列表为空。没有操作本地验收标签页、没有启用公网。下面外站结论依据公开页面的可读取内容及官方交互文档，**不等于已亲自验证当前页面的布局、颜色或手势**；不能从网页文本解析结果推断实际字号和背景。

### 9.1 参考什么，以及哪些设计不照搬

| 参考入口/证据 | 可核实的做法 | 对memVar的启发 | 批判性取舍 |
| --- | --- | --- | --- |
| [UniProt Feature Viewer官方教程](https://www.ebi.ac.uk/training/online/courses/uniprot-exploring-protein-sequence-and-functional-info/exploring-a-uniprotkb-entry/exploring-the-protein-feature-viewer/)；教程含示例图，本轮核对其文字说明 | 用生物学类别组织轨道，点击展开子轨道，选择位点后查看同位置注释及结构对应位置 | 默认首先看到Domains、PTM、Topology及已选来源摘要；详细来源/方法和原始证据逐层展开 | 不把“渐进展开”变成看一个证据必须连续点四次；当前图例、来源摘要和关键限制不折叠 |
| [RCSB Sequence Annotations Viewer](https://www.rcsb.org/docs/sequence-viewers/sequence-annotations-viewer) | 区分缩放、平移与选择；提示中解释当前坐标、原始坐标及来源 | 明确视野和选择各自作用；残基提示同时表达canonical位置与来源映射 | 官方描述包含滚轮缩放、右键区域选择；memVar长页面不宜照搬会拦截滚动或不易发现的手势 |
| [RCSB Sequence Annotations in 3D](https://www.rcsb.org/docs/sequence-viewers/sequence-annotations-in-3d) | 序列和结构选择/取消联动；定义选区清除方式和chain作用范围 | 选中后在两端显示同一对象与作用范围，取消后也给出可理解反馈 | 双击、点空白等可作快捷方式，不能成为唯一清除入口；不承诺memVar已有相同双向联动 |
| [Ensembl官方region walkthrough](https://training.ensembl.org/text_module/human_region_walkthrough) | 区分Drag/Select、Jump to region与Mark region；轨道配置独立，支持按需查找 | 明确“调整显示窗口”和“选中研究对象”不同；来源选择从常驻大面板收敛为按需配置 | 不必复制完整多级配置菜单；常用单残基/区间定位要保持直接 |
| [CATVariant首页](https://catvariant.com/)、[KCNH2示例](https://catvariant.com/genes/KCNH2)；仅可读取页面内容 | 页面按变异分析、临床/人群、结构/实验与来源组织内容，列出可跟进的变异入口 | 借鉴以研究对象和证据类型为主的命名，而不是让UI配置名主导阅读 | 本轮未取得浏览器渲染，不能据此声称核实其多色方案、留白、按钮或动效；此前用户认可的明亮、多色方向仍作为设计偏好 |

这些参考的价值在于信息与操作组织，不代表每个旧式科研数据库的视觉细节都值得复制。此轮不引入它们的组件或素材，不下载图片进入项目；引用教程不等于取得其全部软件或图片再分发许可。

### 9.2 读者能否区分板块？

**判断：主模块名称已经可辨，模块内部的层级与操作归属仍不够清楚。** 用户截图有固定导航、标题、图标和外框；源码也有当前导航高亮。因此不能笼统说“没有分区”。问题是相邻工具栏、模式选择、来源选择、图例、状态条反复使用近似浅底＋细框，读者难以判断哪个是数据、哪个会改变结果、哪个只是说明。

| ID/优先级 | 当前问题与依据 | 审查建议 |
| --- | --- | --- |
| U01 / P1 | 全页外框、内部卡片、工具栏均似独立板块；截图可见层层嵌套 | 保留现有模块顺序；用标题等级、稳定间距和区域用途区别层次。主模块保留一个明确边界，内部普通分组优先用小标题/分隔线 |
| U02 / P1 | 概览、来源、科学图与操作区易同权 | 每块先回答研究问题：Sequence看位点注释，Structure看模型与映射，Variants看变异与证据；短副标题解释任务，不重复空泛“Explore…” |
| U03 / P2 | 导航已有active/aria-current，但长模块中读者可能失去局部位置 | 保留全局吸顶导航；在长模块必要处保持局部标题/工具栏可见。先实测顶部总遮挡高度，避免再增加一整排永久吸顶条 |
| U04 / P1 | Overview内多个子卡片与独立模块视觉相近 | 同级统一标题/图标尺寸；子卡片标题降低一级。不能仅靠每卡不同背景色表示结构层级 |

### 9.3 背景是否需要修改？

**建议调整背景的职责，而不是增加装饰背景。** 当前CSS已采用Slate画布和白色表面，并清除了全页background-image；这一方向保留。问题在于局部浅蓝框使用过多，使“普通容器”和“当前选中状态”不易区分。

| 背景/边界层 | 建议作用 | 应避免 |
| --- | --- | --- |
| 页面画布 | 很浅的Slate，用于衬托白色科研模块 | 渐变大底、纹理、水印、按模块铺满六色 |
| 模块表面 | 白色＋适量中性边界，标题与内容之间有明确节奏 | 每个内层继续套白色卡片、阴影和彩色顶线 |
| 控件区 | 必要时用一层浅Slate，使其与结果区分开 | 所有说明、图例、表格都染成相同浅蓝 |
| 当前选中/焦点 | Radix Blue轮廓、局部浅底；作用对象有文字说明 | 蓝色底既表示选中，又表示默认容器，使两者无法区分 |
| 科学图/序列 | 保留数据颜色和图例；选区优先用轮廓/边界 | 用选中填色覆盖变异数量、PTM或其他科学编码 |
| 表格行 | 白色为主，必要时极浅交替底；hover与选中分别处理 | 靠很高行距和浓斑马纹分行；鼠标悬停看起来像已提交选择 |

U05 / P1：一次实页比较“模块白底、控件浅灰、选区蓝轮廓”三种角色是否不读文字也能辨认。U06 / P2：边框先减少层数，再只提升主要边界对比；不全站加粗边框。以上是memVar的设计建议，不冒充对外站CSS的实测结论。

### 9.4 序列选择为何仍模糊：四种状态不应共用一个“range”概念

本轮代码核对入口：[SequenceViewer](../../../frontend/src/components/SequenceViewer.tsx)、[SequenceRangeNavigator](../../../frontend/src/components/SequenceRangeNavigator.tsx)、[SequenceAnnotations](../../../frontend/src/components/SequenceAnnotations.tsx)、[StructureViewer](../../../frontend/src/components/StructureViewer.tsx)、[VariantCatalog](../../../frontend/src/components/VariantCatalog.tsx)、[VariantDistribution](../../../frontend/src/components/VariantDistribution.tsx)、[App](../../../frontend/src/App.tsx)。

| 实际状态 | 当前代码行为 | 读者容易产生的误解 | 建议用户可见名称与出口 |
| --- | --- | --- | --- |
| Sequence显示窗口 | Navigator和RangeControls更新局部viewRange，调整对齐轨道显示 | “Select protein sequence range”让人以为选择了要分析/筛选的残基 | `Visible window: 700–900`；操作叫`Apply window`、`Show full sequence` |
| 共享单残基选择 | App维护selectedPosition，Sequence与Structure接收；Variant状态条也显示它 | 看见Variants中的Selected residue，以为列表已自动限制到该位置 | `Selected residue: L858`；显示`Clear residue selection`。目录请求参数当前不包含selectedPosition，不应仅凭状态条声称已筛选 |
| Structure局部范围 | 本地selectedRange/committedRange；提交同时把一个端点写入共享selectedPosition | 以为整个范围已同步给Sequence和Variant，而其他模块可能只看到端点 | `Structure selection: 850–870`与`Focused residue: …`区分；保持局部范围语义，不擅自实现全局范围联动 |
| Variant目录范围筛选 | URL canonical_start/end限制列表；distribution查询特意保持全长，但保留其他筛选 | 图仍全长，以为点击无效；清除残基后以为范围筛选也清除了 | `Catalog filter: residues 1026–1050`；`Clear range filter`，图旁说明`Full sequence · selected range filters the table` |

这不是要求把四种状态全部合并。先把名称、反馈和取消作用域说清楚，保持现有科研操作语义；是否增加新的范围联动另作明确设计。

| ID/优先级 | 核对结果 | 下一步应优化什么 |
| --- | --- | --- |
| U07 / P1 | Navigator已经加入指针残基号、范围/长度、拖动预览、Escape回退和键盘手柄 | 不再登记“完全没有编号”；改审显示窗口语义是否明确、拖动后持久状态是否可读。浮层消失后仍应知道当前窗口 |
| U08 / P1 | Navigator提示仍为Drag to select；Apply range同时出现在不同用途控件中 | 按上表改成带对象的动词；双击恢复只作为快捷方式。`Full sequence`和`Reset 1–length`重复入口可同名，不能一处像缩放一处像清除 |
| U09 / P1 | Structure已提供输入区间、Clear selection、Escape、映射计数 | 分开“恢复相机”与“清除选择”；Reset view建议明确camera。预览选区与已提交选区用文字/轮廓区别，0 mapped也有明确反馈 |
| U10 / P1 | Sequence清除共享残基会使Structure联动清除；Variant范围可独立存在 | 清除按钮文字必须说明对象；选区状态放在对应控件附近，跨模块显示来源与作用范围。不要用一个模糊Reset处理所有状态 |
| U11 / P1 | Variant的`Reset all`调用clear并清除残基，但clear保留frequency，预测列配置也未重置 | 应命名为实际操作，如`Clear filters and residue selection`，或明确其保留项；不要为符合“all”而擅自重置更多用户状态 |
| U12 / P1 | 目录跳转有不同入口：普通Variant catalog只滚动，残基详情入口会设置范围 | 区分`Go to variant catalog`与`View variants at residue …`；不能让相近按钮外观与文案掩盖是否改变筛选 |

**建议完整操作闭环（界面文案示意，不是新的数据结果）：**

1. 操作前：显示`Visible window: 1–1210`或`No residue selected`，说明该控件用途。
2. 拖动中：就近显示`Preview 700–900 · 201 aa`，并说明松开应用；Escape恢复拖动前状态，不清掉已有选择。
3. 提交后：保留对象明确的状态条，如`Structure selection: 700–900`，展示实际映射数量；不要求读者记住已经消失的tooltip。
4. 下游动作：只有执行明确的`View variants in …`时才建立相应目录筛选；普通浏览窗口调整不静默增加筛选。
5. 清除/恢复：清除当前对象后显示恢复状态，保留无关来源、模式和筛选；按钮消失时焦点回到相关控件。

### 9.5 列表展开、按钮和引导是否容易理解

维护入口：[ui.tsx](../../../frontend/src/components/ui.tsx)、[ExpressionMatrix](../../../frontend/src/components/ExpressionMatrix.tsx)、[design-system.css](../../../frontend/src/design-system.css)。已有shadcn/Radix Collapsible及Motion进出支持，不因审查另换一套组件。

| ID/优先级 | 问题/风险 | 建议 |
| --- | --- | --- |
| U13 / P1 | 来源选择、行详情、长列表“更多”容易都表现为文字链接 | `Select sources (2 selected)`、`Show 10 more`、`View evidence`分别表示配置、增量展示、详情；使用明确动词和对象 |
| U14 / P1 | 只有chevron而无摘要时，读者不知道值得不值得展开 | 折叠头保留名称、条数/已选数和重要状态。比如`Topology · UniProt selected · 3 annotations`；数量须来自当前真实数据 |
| U15 / P2 | 全行既点击展开又嵌套来源链接可能误触 | 展开触发区和独立操作分清；键盘焦点、aria-expanded与可见箭头方向一致。此为逐组件验证要求，不宣称所有行已有该缺陷 |
| U16 / P1 | Expression当前已有限预览、Show more/all/fewer，源码有折叠后焦点处理 | 验收展开后仍能在附近收起、收起不丢来源/context；Show all不作为同权主按钮。不要把已完成的有限预览重新记作未开发 |
| U17 / P1 | 多个outline小按钮外观相同，操作优先级不明显 | 每局部操作组最多突出一个主动作。清除是次要但可发现的按钮，不能细小到只剩角落X；不同作用域用不同完整名称 |
| U18 / P2 | 图标存在不代表引导清晰 | Chevron用于展开、X用于清除、RotateCcw用于恢复、ExternalLink用于外链；主路径保留文字。无需给每个普通标签都加图标 |
| U19 / P1 | 常驻长解释和弱提示竞争注意力 | 必须读懂当前结果的对象/量尺/作用域直接显示；手势提示在控件旁简短显示；术语解释按需打开，不用多个大“Start here”框占据首屏 |
| U20 / P1 | 动效可能只告诉用户“有东西动了”，没有解释变化对象 | Motion用于展开/收起、模式指示器、选区状态进退；CSS用于轻量hover/pressed。状态文字同步变化；减少动效时仍能完成同一理解任务 |

### 9.6 本轮优先级与可执行验收任务

优先解决U07–U12选择语义与取消边界，再调整U01–U06视觉分层，最后逐项核对U13–U20展开和引导。字体/信息层级沿用前8节，不用再建一套尺寸和颜色规范。

| 验收任务 | 应看到/理解的结果 | 失败信号 |
| --- | --- | --- |
| 从Overview跳到Sequence，再到Variants | 当前模块与标题明确，不被吸顶导航遮挡 | 只靠模块颜色猜位置；滚动后导航与可见模块不一致 |
| 将序列窗口调到700–900 | 明确这是显示窗口，201 aa；其他筛选不被改变 | 读者以为结构已选中整个范围或目录已筛选 |
| 拖动中Escape；提交后恢复全序列 | 前者恢复旧窗口，后者显示全序列 | Escape清空无关选择；恢复后原筛选无故丢失 |
| 选择一个残基并查看结构 | 两端显示同一canonical对象；无映射时说明原因 | 用蓝色变化代替位置说明；无映射静默无反馈 |
| 结构选范围后查看Sequence/Variant状态 | 看得出局部范围与共享焦点残基的区别 | 把端点显示误认为完整范围已经同步 |
| 选择Variant distribution区间，再清除范围 | 表格限制和图中选区都清楚；其他筛选保留 | 目录仍限制却无可见状态；清除范围同时重置来源 |
| 展开来源/证据，再关闭 | 关闭入口就近、焦点可恢复、选项不丢失 | 需要回到很远处才能关闭；收起改变默认值 |
| 不用鼠标完成定位和清除；减少动效模式复核 | 数字输入、Tab/方向键、明确按钮可完成 | 只有拖动、右键、双击才能操作；无动效时没有状态反馈 |

**限制：** 外站本轮为官方资料对照，CATVariant配色与真实布局仍待浏览器可用时补看；本地为截图和源码审查，以上任务未实际运行。本轮只增加文档，不修改交互行为、不恢复公网、不干扰主任务。
