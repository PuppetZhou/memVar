# 00阶段实现与验证摘要

2026-09-22从Web README迁入，保留原日期及当时验证范围，未重新运行或核验服务。当前工作见[01阶段](../../research/01_preview_optimization/README.md)；旧“当前/待开展”以实际后续记录和生效方案为准。

2026-09-21：**首个公网预览版已发布（用户确认）**。通过 ngrok 分享本机网站，PostgreSQL 与结构/AlphaGenome 等资源仍留在本地，未进行数据迁移。当前作为初次公网展示基线，后续收集导师反馈、补充细节，并研究更高分辨率 AlphaGenome 与长期迁移方案。[发布摘要与后续方向](20260921_public_preview_v1.md)。

2026-09-21：**Basic Info膜特征与来源证据已补充**。全宽紧凑UniProt/HTP/DeepTMHMM2摘要，完整概况/拓扑示意移入展开面板；Cellular location与Functional context并排。数据库→原记录→role/method→证据展开已接通；HTP原reliability/方法/约束可见，TOPDB文献和PDB链可读，未映射来源保持原坐标。构建、6项接口测试及EGFR/KCNH2桌面/390px交互通过。[现行方案](../../archive/00_initial_preview/plan/protein_overview.md#basic-info膜特征重排2026-09-21追加当前实现) · [问题与依据](../../archive/00_initial_preview/research/protein_overview/membrane_views.md#basic-info补充分析与处理2026-09-21) · [验证记录](20260921_membrane_evidence_refinement.md)。

2026-09-21：**Home数据概览已精简**。七个主数字入口＋三类内容预览和EGFR示例，移除完整来源柱图/长清单；Expression主数字改为13个列示数据集，细统计仍在Data Overview。构建与七层React静态检查通过；侧会话浏览器不可用，实际布局/点击待验收。[方案](../../archive/00_initial_preview/plan/homepage.md#首页精简概览2026-09-21后续反馈当前) · [验证](20260921_homepage_v1.md#首页数据概览精简后续追加)。

2026-09-21：**Full Sequence Atlas已精修**。PTM分类图例与独立来源筛选、正方形响应式残基格、模式对应详情前置、PTM来源对齐表，以及Variants原标签/Predictor coverage已接通。预测只展示覆盖数与各替换原值，不生成位点致病分数。构建、5项后端测试、P00533/Q12809与桌面/390px交互通过。[方案](../../archive/00_initial_preview/plan/sequence_structure_refinement.md#full-sequence-atlas细化2026-09-21-0616后反馈) · [问题](../../archive/00_initial_preview/research/website_v2/issues.md#full-sequence-atlas2026-09-21-0616后反馈) · [交付](20260921_atlas_refinement.md)。

2026-09-21：**Data overview统计展示已重新分层**。独立覆盖率圆环、来源组成环图、纵向比较柱图、分组工具标签和Expression场景切换替代统一横条清单；原统计和科学口径不变。构建、分母/分组完整性及React静态渲染通过；当前侧会话浏览器不可用，新交互与视觉验收待补。[方案](../../archive/00_initial_preview/plan/database_overview_documentation.md#多样化统计展示2026-09-21追加当前方案) · [验证记录](20260921_database_overview.md#统计图形多样化后续追加)。

2026-09-21：**首页交互式七层数据总览已交付**。蛋白/变异/预测/表达/调控/互作/疾病切换、真实规模与来源分布、计数说明及完整统计跳转已接入；新增无字蓝色膜背景及三种手动切换，采用浅蓝紫配色。七层、13来源/43配置展开、背景键盘操作、503恢复及桌面/390px通过。[首页方案](../../archive/00_initial_preview/plan/homepage.md) · [调研与素材](../../archive/00_initial_preview/research/homepage/design.md) · [实际验证](20260921_homepage_v1.md)。

2026-09-21：**全库Data overview与Documentation已交付**。新增膜蛋白类型/注释来源、变异/预测/疾病与context分类统计，42项可搜索来源目录、确认版本和使用/API说明；首页及蛋白页导航已接通，About兼容保留。统计绑定当前服务manifest，未知来源版本省略。构建、4项统计测试、桌面/390px及来源筛选/分类跳转通过。[当前方案](../../archive/00_initial_preview/plan/database_overview_documentation.md) · [调研与缺项](../../archive/00_initial_preview/research/database_overview/analysis.md) · [交付验证](20260921_database_overview.md)。

2026-09-21：**首页素材与膜定位入口已更新**。用户绿色蛋白素材用于淡背景和三类插图，补同色Membrane-related符号；新增UniProt原始膜定位浏览（8个常见具体位置、82项完整菜单），支持类型/定位/关键词组合检索。构建、计数与桌面/390px交互已验收。[现行首页方案](../../archive/00_initial_preview/plan/homepage.md) · [素材及问题记录](../../archive/00_initial_preview/research/homepage/design.md)。

2026-09-21：**滚动、PPI顺序及页码跳转已完成**。Regulatory人体图随页面滚动；PPI类别总览提前，IntAct/BioGRID优先于mutation。活动记录分页统一提供页码输入，7类cursor API支持直接offset，保留过滤和稳定排序。10项相关后端测试、构建与桌面/390px代表性交互通过。[方案](../../archive/00_initial_preview/plan/website_v2.md) · [交付与边界](20260921_website_v2.md#滚动ppi优先级与全站页码跳转2026-09-21)。

2026-09-21：根据最新实看反馈，Variant Browser已恢复predictor独立纵列，收紧身份/单字母列间距；Catalog上方复用Sequence Distribution，可按bin筛选并清除选区。61字段工具指南与多选能力保留。构建与真实区间/分类计数核对通过，侧会话浏览器无连接，新增布局实际验收待补。[当前方案](../../archive/00_initial_preview/plan/variant_evidence_refinement.md) · [验证](20260921_variant_evidence_refinement.md#恢复独立预测列与catalog分布图后续追加)。

2026-09-21：**首页第一版已完成**。总搜索、四类膜蛋白真实统计与分类检索、EGFR/KCNH2/AQP4案例入口已接通；结果支持组合查询和数字分页。构建、只读API核对及桌面/390px交互通过。[打开首页](http://127.0.0.1:8000/) · [设计与问题记录](../../archive/00_initial_preview/research/homepage/design.md) · [交付验证](20260921_homepage_v1.md)。

2026-09-21：**Basic及Expression/QTL/Disease配色精修已验收**。沿用整体色系，Basic改白底/深灰标题/彩色图标与关键值；三个证据模块采用中性表格及来源/类型小标签，原测量、分类在详情突出。DeepTMHMM2仍为默认预览重要来源。构建、P00533桌面/390px和详情交互通过。[调研依据](../../archive/00_initial_preview/research/website_v2/analysis.md#information-colors-20260921) · [交付与验证](20260921_website_v2.md#中性背景与信息级着色2026-09-21)。

2026-09-21 05:25（香港时间）：**Expression与IntAct mutation细节精修已验收**。Context数字分页与跳页、RNA-seq/CAGE/MS/IHC测量介绍、mutation互作效应优先、原范围/身份展示精简及GTEx组织可读标签已实现。真实6页/699页、四类效应、桌面与390px通过；仅前端改动。[调研](../../archive/00_initial_preview/research/website_v2/context_review.md#expression-ppi-20260921) · [交付记录](20260921_expression_ppi_refinement.md)。

2026-09-21：页面文案精简与问号帮助已实现，Variant临床环图新增高亮/占比/固定选择；AlphaGenome九模态统一指南并修正contact负值显示。最终构建及浏览器限制见[本轮方案与官方核对](../../archive/00_initial_preview/plan/ui_help.md)。

2026-09-21：AlphaGenome已调整为Expression、QTL之后的独立章节，新增导航入口；保留Expression已选组织的场景提示。仅调整布局和状态传递，数据/API及PPI保持现有范围。[当前方案](../../archive/00_initial_preview/plan/expression_alphagenome.md)。

2026-09-21 05:05（香港时间）：**Variant Browser与证据面板精修已完成**。首格与AA列精简重排，ClinVar分类/review星级/来源ID分层，Population频率色阶，Prediction可筛选总览与分数卡，Stability方向及Transcript重点展示。真实零/缺失、来源星级、55个评分、双方向ΔΔG及390px五面板交互验收通过。[方案](../../archive/00_initial_preview/plan/variant_evidence_refinement.md) · [交付与验证范围](20260921_variant_evidence_refinement.md)。

2026-09-21：PPI overview已补充疾病/专题context集合与IntAct mutation独立入口，类别柱图改为环状统计，dataset筛选贯通目录、列表和分页，mutation使用专用字段与详情。未改变数据库或AlphaGenome。PPI后端五组测试通过；后续独立章节调整时整站TypeScript与Vite构建也已通过，浏览器验收待补。[实现与验证记录](20260921_context_v1.md#ppi-overview场景与mutation入口修正2026-09-21)。

2026-09-21：此前Expression已接入旧版AlphaGenome（现已移至独立章节） 降采样预测接口与独立轨道浏览器，复用原位 Parquet/小型只读目录；不修改 PostgreSQL 表、不重跑预测。默认 RNA-seq / Lung，支持无数量上限添加、组织标签导航、共享窗口缩放和九模态展示。API测试与前端构建通过；浏览器实例不可用，实际渲染/点击验收待补。[方案、来源和验证边界](../../archive/00_initial_preview/plan/expression_alphagenome.md)。

2026-09-21 01:41（香港时间）只读复核：当前已确认范围的PostgreSQL导入全部完成，四个schema共111张业务表、44个普通视图，版本与各板块交付记录一致；各自导入/验证报告通过。查询时未见活动导入，仅有后台autovacuum。该结论不包含暂缓来源或尚未确定的科学处理，也不代表API、页面与并发性能已验收；详细版本与复核范围见[展示审查中的入库核对](../../archive/00_initial_preview/research/display_selection.md#入库核对)。

2026-09-21 02:31（香港时间）：**可运行的网站初版已交付**，使用既有四部分PostgreSQL数据，完成FastAPI与React/TypeScript真实链路、字段分层、序列多轨道、结构及列表筛选的代表性浏览器验收。[打开本地网站](http://127.0.0.1:8000)，[API文档](http://127.0.0.1:8000/docs)，[交付与验证记录](20260921_website_v1.md)。一个8000端口提供前端和API，没有另建测试数据库。

2026-09-21 03:56（香港时间）：**网站第二版已完成本地构建与代表性交互验收**。重新调研CATVariant、VarSome和PTMD：独立基础摘要、精简序列轨道与全残基彩色网格、原ClinVar标签分箱、61个评分字段可选/34字段原量尺细条与频率、Expression覆盖介绍、QTL人体组织导航、PPI只读统计加常驻筛选表、PTMD2独立疾病来源已实现。[打开网站](http://127.0.0.1:8000/protein/P00533) · [交付与实际验收](20260921_website_v2.md)。[问题清单](../../archive/00_initial_preview/research/website_v2/issues.md)、[调研分析](../../archive/00_initial_preview/research/website_v2/analysis.md)、[现行方案](../../archive/00_initial_preview/plan/website_v2.md)同步更新。已有科学规则继续有效，默认展示精简不删除正式来源；初版为历史基线。架构见[网站构建策划](../../archive/00_initial_preview/plan/site_construction/README.md)。

2026-09-21 04:24（香港时间）：**序列/结构精修与预测interface入库已完成**。PTM默认dbPTM独立表格、紧凑secondary覆盖、逐轨坐标/范围调整，以及八类结构着色已接入；结构另可切换Ribbon与旧版平滑表面/光照风格。预测interface按最新要求直接放在Sequence Browser的连续分数轨道，主视图不另列预测表；PeSTo/SPPIDER完整科学快照导入独立`web_interface`，保留分片、伙伴和两预测角色。[现行方案](../../archive/00_initial_preview/plan/sequence_structure_refinement.md) · [交付和验收](20260921_sequence_structure_refinement.md) · [导入报告](../../../data/postgresql_interface_import.json)。本轮保留并行任务对Catalog分类总览的调整。

2026-09-21 04:30（香港时间）：**第三轮展示优化及定位/通路精简已验收**。Variant Browser改为后果/临床总览，增加GRCh38替换列、代表转录本筛选、预测工具分组介绍与默认AlphaMissense；FUNCTION长文删除，GO三类完整统计可点查，JSD具备原值/刻度/键盘交互。Cellular location改为简洁标签、Reactome改短预览，细节按需打开。[本轮交付和验证](20260921_website_v2.md#第三轮及定位通路精简2026-09-21-0430) · [问题与状态](../../archive/00_initial_preview/research/website_v2/issues.md)。

2026-09-21 05:12（香港时间）：**共享坐标Sequence Browser及膜特征面板已交付**。八类轨道纵向对照；PTM/density放大、Secondary单行彩色原区间，显式拖选和手柄伸缩，保留完整网格与原证据。Membrane association展示真实跨膜/膜内/拓扑计数，按需打开UniProt、DeepTMHMM2和各来源观测；05:19追加DeepTMHMM2默认预测预览，含简介、原蛋白类型、TM螺旋数和信号肽摘要，桌面/390px入口已验收。最终构建、P00533/Q12809、桌面/390px、鼠标/键盘/触摸及来源分页已验收。[方案](../../archive/00_initial_preview/plan/website_v2.md) · [问题及修复](../../archive/00_initial_preview/research/website_v2/issues.md) · [实际交付](20260921_website_v2.md#可读性范围操作与膜特征面板2026-09-21-0512)。

从项目根目录运行 `Web/start-local.sh`；前端改动后先在`Web/frontend`运行`npm run build`。首次安装前端可用`Web/start-local.sh --build`；Python依赖见[requirements-web.txt](../../../requirements-web.txt)。启动复用已运行PostgreSQL和配置的本地结构文件，不执行重新导入。当前已通过 ngrok 提供临时公网预览；尚未进行并发容量验收，发布状态见上方摘要。

2026-09-21：**`20260921_sequence_v1`已构建、导入本地PostgreSQL并通过Sequence验证**。`web` schema含46张业务表、10个普通视图和1张构建清单元数据表；Sequence仅canonical，复用共享身份与膜数据。[本版修改与验收记录](20260921_sequence_v1.md)维护差异；[数据清单](../../../data/README.md)维护表和字段。

本轮去除功能概览/反应关联中的可恢复属性、BioDolphin嵌套位点副本及派生汇总、UniProt/HGNC外链关系副本。外链实体表68,085行，`protein_external_reference_all`普通视图仍提供83,524条完整外链；编号缺失留空，RefSeq蛋白、RNA及NC_核酸编号分别处理。Basic info不纳入疾病标识。

GO slim已接入Function的[正式分类桥](../../../../modules/Function/docs/go_slim.md)，四类膜标签已接入膜模块的[正式派生](../../../../modules/membrane/docs/basic_membrane_labels.md)。默认canonical的膜区段使用UniProt Feature；功能具名对象无法对应isoform时不补给canonical；定位不生成跨来源最终结论。既有膜mapping及DeepTMHMM2保持原来源结果，不重跑预测。

本地数据库`memvar_web`、主schema `web`，仅监听`127.0.0.1:55432`。[导入报告](../../../data/postgresql_import.json)及[查询验证](../../../data/postgresql_validation.json)已与当前构建/版本一致；事务切换、全部表行数/外键、外链组合、JSONB往返及位点分页通过。API与前端本地初版的代表性联调已完成，范围与限制见网站交付记录；现已通过 ngrok 临时对外预览，数据库仍在本地。

仍暂缓：Reactome计数、KEGG采集和跨来源膜区段聚合；已交付全库总览仅复用明确统计口径，不解除上述科学处理限制。Variant、Sequence及本轮QTL/PPI/Expression均已导入；疾病基础表已导入独立schema，ClinVar条件关联暂缓。API局部验证见[基础接口记录](20260921_api_core_v1.md)和[证据接口审查](20260921_api_evidence_v1.md)；字段可见层次正在逐板块复核。[整体方案](../../archive/00_initial_preview/plan/overall.md)、[当前构建方案](../../archive/00_initial_preview/plan/local_table_build.md)维护数据边界；候选列精简研究见[第二轮审查](../../archive/00_initial_preview/research/basic_info_v2/tables.md)，未采纳建议不表示已删列。

2026-09-21：**Variant `20260921_variant_v1`已构建、导入同一数据库的`web_variant`并验证**，11张业务表（五张核心＋六张辅助）、6个普通视图。VEP/dbNSFP/AlphaGenome按variant与所选transcript后果粒度整合，保留原值和来源注释；本地gnomAD频率、canonical ddG已连接。[字段与关联契约](../../archive/00_initial_preview/plan/variant_tables.md)、[版本验收](20260921_variant_v1.md)、[独立导入报告](../../../data/postgresql_variant_import.json)。

[蛋白概览](../../archive/00_initial_preview/plan/protein_overview.md)、[身份字段](../../archive/00_initial_preview/plan/identity_function_tables.md)、[功能通路字段](../../archive/00_initial_preview/plan/function_pathway_tables.md)、[PostgreSQL方案](../../archive/00_initial_preview/plan/postgresql.md)维护当前契约。[序列](../../archive/00_initial_preview/plan/sequence.md)、[变异](../../archive/00_initial_preview/plan/variant.md)、[context](../../archive/00_initial_preview/plan/context.md)、[Expression](../../archive/00_initial_preview/plan/expression.md)、[疾病](../../archive/00_initial_preview/plan/disease.md)分别维护后续范围；已完成Basic info、canonical Sequence及Variant服务数据。

2026-09-21：疾病`20260921_disease_v1`已导入同一数据库的`web_disease` schema，20张业务表、12个普通视图；复用现有mapping，保留来源证据并精简重复字段。[服务表契约](../../archive/00_initial_preview/plan/disease_tables.md)、[版本与验收](20260921_disease_v1.md)。

2026-09-21：QTL/PPI/Expression已精简、导入并验证（34张业务表、16个普通视图，版本`20260921_context_v1`），采用独立`web_context` schema和`data/context_tables`，避免与并行Variant/Sequence整库替换互相覆盖。当前执行与验收统一见[Context版本记录](20260921_context_v1.md)，不计入上方主schema表数。
