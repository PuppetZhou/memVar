# 页面文案与按需帮助

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-21：用户授权精简各板块说明，将术语、统计口径和官方定义放入可点击问号；Variant Browser 临床环图参照 PPI 增加交互。本轮仅呈现层，不改数据库、API查询、科学分类或预测产物。

## 现行规则

- 默认层保留标题、操作入口、数值、单位、图例及影响当前判断的状态；不重复介绍同一个操作或统计原则。
- 说明性文字最多一句短语。统计范围、证据适用范围、术语定义进入就近问号；原始来源说明、错误/空态、缺失与零、坐标未验证提示不作为“冗余”删除。
- 问号为真实按钮，点击打开命名对话框；支持键盘、Escape、关闭按钮与点击背景关闭。帮助使用 Portal，避免嵌在标题或表格结构里；只在打开时挂载，不增加数据请求。
- 官方定义与本站展示约定分开：不得将降采样、上下文标签匹配、display group 等本站规则描述成原数据库规则。

## 分板块审查

| 区域 | 默认层 | 问号 / 按需内容 |
| --- | --- | --- |
| Basic / Function / Location | 蛋白标识、定位标签、功能类别、来源；当前已紧凑的原记录不再删改 | 来源证据维持现有详情 |
| GO / Reactome | 三类 GO 计数、原短预览；删除 GO 图下长说明 | GO 三方面定义、计数重叠及非富集；Reactome主题、官方图及来源链接 |
| Membrane | 原跨膜/膜内/拓扑计数、未验证状态 | 原特征、预测拓扑、来源观测的区别；非独立证据、缺失含义 |
| Sequence / atlas / JSD | canonical标识、轨道单位、图例、原数值；删除重复长尾注 | 映射范围、聚合、无色含义、JSD与0.5参照线 |
| Structure | Ribbon/Surface状态、预测标识、坐标不匹配告警 | 渲染方式与同一结构的关系、链接限制、interface预测语义 |
| Variant | AlphaMissense缩为“Score 0–1 · source call”；组卡只留名称/字段数；去掉上下重复解释 | 原分数、工具分组、非独立投票、转录本/UniProt区别、review含义 |
| Expression | RNA & protein measurements、分类/集合/组织入口；删除用户指出的两段长文 | 数据覆盖而非表达强度、dataset–context计数、RNA/蛋白单位、原API统计范围 |
| QTL | 组织入口与筛选；删除人体导航长脚注 | 来源关联记录、effect/assembly/phenotype、人体仅标签导航 |
| AlphaGenome | 预测标识、模态/组织/轨道选择、坐标与bp/bin | 统一指南：9模态、各自含义/单位、添加步骤、分辨率/截取、数据缺口、上下文匹配、快照 |
| PPI | source/context/mutation入口、ring及表格；删重复介绍 | 集合重叠、来源项目名、mutation feature粒度及坐标限制 |
| Disease / PTMD2 | 来源卡、原分类、PTMD坐标未验证短标签 | gene/disease/variant适用层次、原State/MutationSite含义与统计范围 |

旧 `Evidence.tsx` 中已不在当前页面挂载的历史组件未做无关重构；原科学记录正文不改写。

## 环图交互

`VariantCatalog.tsx` 临床六组保持原 API 统计。悬停环段/图例联动高亮，中心显示该组数量/占比；鼠标离开恢复，点击环段/图例可固定，重复点击取消。图例使用按钮，可用Tab/Enter/Space，aria-pressed标记固定状态；不将近似展示组转换成原分类筛选。窄屏环图与图例上下排列。PPI仍为统计展示而非筛选入口。

## 官方核对与信息清单

核对日期2026-09-21。网页最新说明仅用于术语解释，不代表本地快照已更新。

| 信息 | 官方依据 | 落点 / 状态 |
| --- | --- | --- |
| AlphaGenome 9模态、RNA/CAGE/PROCAP、ATAC、histone、三类splicing、contact单位 | [Model output metadata](https://www.alphagenomedocs.com/exploring_model_metadata.html) | 统一指南已提供；本站仅9模态，DNase/TF ChIP缺失在覆盖说明中 |
| AlphaMissense含义与限制 | [原研究](https://deepmind.google/research/publications/21083/)、[作者说明](https://deepmind.google/blog/a-catalogue-of-genetic-mutations-to-help-pinpoint-the-cause-of-diseases/) | 预测器问号；原分数与source call不变 |
| ClinVar分类域与review | [分类](https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/)、[review](https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/) | 环图/证据问号，星级不解释成概率 |
| GO三方面 | [GO overview](https://geneontology.org/docs/ontology-documentation/) | GO问号；本站slim计数非富集 |
| Reactome通路、反应及浏览 | [官方指南](https://reactome.org/userguide) | Reactome问号及官方diagram入口 |
| HPA RNA/蛋白、组织/细胞数据 | [下载字段说明](https://www.proteinatlas.org/about/download) | Expression问号与来源链接 |
| IntAct突变影响互作记录 | [官方训练：获取数据](https://www.ebi.ac.uk/training/online/courses/intact-quick-tour/getting-data-from-intact/) | PPI问号；本地坐标未验证状态不隐藏 |
| 分数工具各字段方向 | 现有`SCORE_SCALES`及新增`predictor-guides.ts`/dbNSFP 5.4a字典 | 后续追加61字段用途、量尺与判定依据，详见[统一预测列方案](variant_evidence_refinement.md#统一预测列与prediction-toolkit2026-09-21追加)；只解释来源，不新增分类 |
| QTL/定位/疾病的本地计数与映射 | 当前API与已确认模块方案 | 保留项目含义；GTEx/UniProt网页仅返回JS壳，未据此补造新定义 |

## 附带发现：contact负值显示

官方contact单位是相对距离期望的log-fold；旧目录显示名“predicted contact frequency”容易误导，而且旧热图将负值压到零色。EGFR `contact_maps:000` 128×128窗口实读：min −0.763671875，max 1.6416015625，10,526个负单元。已只在前端纠正单位和以0为中心的蓝/白/橙色标；灰色表示缺失。数值、预测、文件和API不改。色标范围取该窗口最大绝对值，跨轨道比较须读原值。

## 验证

- 最终整站 `npm run build --prefix Web/frontend` 通过（TypeScript + Vite，1,683模块）。中途并行新增ContextDisplay的样式尚未写入导致一次构建失败；文件就绪后构建通过，未回退或改写该并行工作。
- EGFR临床摘要6组之和=4,096，与matching variants总数一致；Expression/PPI summary为200。
- 真实EGFR contact接口为200，负值核对见上；旧数据未重跑/导入。
- Browser运行时返回实例列表`[]`，无法做实际hover/click、对话框关闭/焦点、桌面/移动截图和控制台验收；这些仍为待验收项，构建不能替代视觉验证。

维护：共享`HelpGuide.tsx`/`help-guide.css`、各板块就近入口、`AlphaGenomeExpression.tsx`九模态指南。本文件维护本轮文案策略与来源核对；问题索引见`docs/archive/00_initial_preview/research/website_v2/issues.md`。
