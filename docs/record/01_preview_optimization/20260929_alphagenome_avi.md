# AlphaGenome 新版与 AVI 共轴展示

核对：2026-09-30（香港时间）。新版参考轨道与AVI总分、18列归因均已接入本地8000。新下载AVI包完成mapping、正式Parquet发布及PostgreSQL导入，真实贡献页面验收通过。此前旧ZIP故障保留在末节，已解除当前阻塞。

## GitHub当前版本发布检查

用户授权提交当前网站版本至`PuppetZhou/memVar`的`main`，包括AlphaGenome/AVI、MANE CDS和工作区已完成的界面优化。发布前18项AlphaGenome/AVI测试及TypeScript/Vite构建通过；补齐新部署只读账号初始化时对`web_mane`的授权。原始数据、数据库、凭据、构建输出、Atlas调研导出和本地`.agents`工具不纳入提交。本次仅发布网站源码、配置与文档，不执行数据库迁移或云端部署。

## 09-30第三批反馈：AVI复选框与互作/QTL密度

已更新本地8000静态构建。此次只修改展示与交互；未重跑数据或改变评分、收录及计数口径。当前AVI交互替代下文历史记录中的类别聚焦/淡化与Show all。

- AVI分类改为原生复选框多选，默认仅Total impact score；勾选才绘制对应贡献，取消后完全隐藏。Y范围仅由可见图层决定，正负贡献仍分别堆叠、总分仍独立取来源值。真实零保留基线短线，缺失不填零。分类列表独立滚动，Select all/Total only置于列表外，避免遮挡末项；SNV详情保留全部18项原值。
- PHRED仅展示Total；返回Raw保留已有贡献选择，在PHRED勾选贡献会切回Raw。允许全部取消并显示明确提示。
- 互作标题与副说明同行，分类图标题/范围提示同行，缩小环图和列表行距。Sources与两个按内容宽度排列的入口同行；保留全部10类数量/比例、full-collection标签、来源下钻/返回及计数帮助。
- QTL底部导航提示与Counting scope合并一行，撤除分隔线与大段上下留白，原计数说明继续在帮助弹窗内。

验收使用独立Chromium访问本地8000的真实EGFR（P00533），1176×827视口：互作总览高386.125px，置于y=90后底部约477px，一屏完整；来源入口约298/311px宽、40.8px高。QTL底部提示行28px高。AVI依次勾选Conservation与Protein，再取消Total，Canvas采样证实默认只有总分色、两类勾选后同时出现、取消Total后总分色像素为0；未采用淡化替代隐藏。全选9项、Total only、全空选择、PHRED/Raw恢复流程通过；键盘打开55,019,278 A→T后读取18项原始贡献。IntAct/BioGRID均能进入collection并返回，计数仍2,447/5,076，两个Counting scope弹窗内容正常。

TypeScript/Vite构建及差异空白检查通过，浏览器console error为0；已有Molstar性能warning未归因于本批。仅验收受影响桌面流程，未重跑后端/数据或扩大为全站回归。当前批注地址51136无法从此环境访问，验收使用同一项目的实际8000服务。

截图：[默认仅Total](../../../output/playwright/avi-checkbox-total-default-1176.png)、[多选贡献并关闭Total](../../../output/playwright/avi-checkbox-contributions-1176.png)、[一屏互作总览](../../../output/playwright/interactions-one-screen-1176.png)、[QTL紧凑页尾](../../../output/playwright/qtl-compact-footer-1176.png)。

## 09-30后续五项批注：平移、CDS可见性与空间压缩

已更新本地8000，限展示与交互变更，不重跑或更改科学数据。实现位置为 `AlphaGenomeExpression.tsx`、`alphagenome-expression.css`、`PpiOverview.tsx`、`ppi-overview.css`、`ContextPanels.tsx` 与 `context-v2.css`。

- 坐标轴支持纵向滚轮和触控板横向滚动平移；当前区间宽度保持不变，边界限制在所选预测窗口内。使用非passive局部监听与动画帧合并，轴上浏览不触发页面滚动；Ctrl/Meta滚轮保留浏览器行为。其他页面区域继续正常纵向滚动。
- 轴下新增Pan导航条，可拖动、左右键微调、Home/End定位窗口两端；Full window时禁用。原有拖选缩放、Reset及箭头平移仍保留；指针在越过拖动阈值后才捕获，避免吞掉CDS色块的单击定位。
- CDS高度从10增至22，增加浅蓝独立底带和边线，保持基因组线性坐标及原始边界。放大且色块足够宽时显示外显子编号；可点击色块或使用CDS exon菜单直接聚焦，留适当上下文。菜单仅提供与当前模型窗口重叠的来源CDS，负链编号沿用来源。
- 互作初始页移除Source collections / Interaction evidence及无效的单项Sources面包屑；帮助入口并入分类图标题。来源下钻后仍保留面包屑返回。IntAct/BioGRID改为名称、记录数及箭头的紧凑行，保留full-collection计数说明。
- Expression的AlphaGenome入口移到末尾，与Counting scope共用一行；标题下直接显示表达选择器。

TypeScript/Vite构建和差异空白检查通过。1414×827真实EGFR桌面流程核对：CDS exon1聚焦200bp；滚轮后从55,019,222–55,019,421平移到55,019,255–55,019,454，宽度仍200bp、页面scrollY不变。导航条Home/End到达实际min/max；exon2定位55,142,240–55,142,483（244bp），包括完整来源CDS。IntAct/BioGRID均可进入collection并返回，full记录数仍2,447/5,076；来源入口实测由177px压到52px，初始重复标题61px与32px面包屑及间距撤除。Expression底部链接可定位到#alphagenome。浏览器无console error；未扩大为全站或移动端验收。

截图：[增强CDS与平移导航](../../../output/playwright/alphagenome-cds-visible-navigation.png)、[CDS exon聚焦](../../../output/playwright/alphagenome-cds-exon-focus.png)、[紧凑互作区](../../../output/playwright/interactions-compact-sources.png)、[Expression末尾入口](../../../output/playwright/expression-compact-footer.png)。

## 09-30专属配色、MANE CDS与紧凑叠加轨道

八项用户批注已实现，本地8000静态构建及API已更新。当前批注浏览器51136无法连接，内置浏览器运行时列表为空；使用独立Chromium在同一真实服务的1414×827桌面页完成验证，没有把截图当作交互验收。

- 科学图形改用用户指定11色palette，AVI总分菱形及各类别、参考模态、叠加曲线、contact色标均已更新；操作选中态保留iOS浅蓝。
- Add/Added为可往返切换的按钮，aria-pressed、勾号、颜色及轻微动效随选择变化；再次点击取消后可以重新加入。
- 参考一维图固定110px绘图区。实测Splice usage/Histone ChIP叠加面板各199px、junction203px、AVI294.5px；AVI分类栏153px高、内容277px，独立滚动，不再撑高整个轨道。展开记录/详情时仍允许显示完整内容。
- 同biosample、同模态、同显示单位的一维信号默认叠加，保留每条原始曲线/名称/strand/mark/原值，使用共同原值Y轴；图例逐条隐藏/恢复、逐条移除；曲线颜色按来源目录固定，移除/重加/分轨切换保持不变。Overlay same modality可切回独立面板。不同模态/背景不合并，junction/contact独立。不求和、不归一化、不翻转负链数值；不同assay的来源尺度差异仍需按来源解释。
- 新数值浮层340px宽，区分模态、坐标、bin与每条曲线Mean/Maximum。Junction显示完整来源区间、strand和junction signal；弧形高度只作视觉引导。小数Y轴使用足够精度，避免正值刻度显示成0。
- MANE CDS先在foundation构建正式Parquet，再投影Web并事务导入`web_mane.gene_cds`，API不读取科研目录。来源、覆盖与限制由[foundation结果](../../../../modules/foundation/docs/result.md#2026-09-30-mane-select-cds-基因组结构)维护；不重新选择代表或把基因关联推断为UniProt序列匹配。

验证：TypeScript/Vite构建通过；参考接口9项（含新增CDS）和AVI9项测试通过，另有MANE解析定向测试。真实API正链P00533、负链A0A087WXS9、无MANE A0A075B6H7逐字段/片段与来源一致，未关联gene返回404，见[报告](../../../data/mane_cds_live_validation.json)及[入库报告](../../../data/postgresql_mane_cds_import.json)。

桌面流程：2条skeletal muscle splice usage（018/079）及3条Histone ChIP（052/053/054）加1条junction共6条信号，叠加为3面板，关闭叠加后为6面板；开关图例只影响目标曲线。ChIP悬停chr7:55,158,497时，来源bin55,158,360–55,158,615，三条Mean为114.25/79.5/262，Maximum为116/86.5/296，分别显示。Junction键盘检查示例chr7:54,759,391–55,198,716、正链、8.25e-5，保留超出视野的完整来源区间。

EGFR显示28段CDS与单独stop codon；200bp视野下首段55,019,278–55,019,365，与SNV55,019,278的蓝色定位线同为SVG x=512，编码块宽404.8，内含子没有涂为CDS。已有全gene4,096及局部206个SNV仍可用。浏览器console error为0。未扩大为全站/移动端或全量HDF5回归。

截图：[MANE轴与紧凑轨道](../../../output/playwright/alphagenome-mane-overlay.png)、[ChIP多曲线读数](../../../output/playwright/alphagenome-chip-inspector.png)、[Junction读数](../../../output/playwright/alphagenome-junction-inspector.png)、[200bp CDS与SNV共轴](../../../output/playwright/alphagenome-mane-cds-200bp.png)。

## 09-30正式归因交付与真实页面验收

输入来自T7重新下载包及[整包完整性报告](../../../../modules/Alphagenome/runs/20260929_avi_redownload_integrity_01/validation.json)。流程绑定新包路径/大小/mtime/成员CRC和提取来源，直接提取到新raw目录并fsync；没有重建已删除本地ZIP、复用旧partial或依赖旧失败cmp。科学规则保持原值、精确GRCh38/POS/REF/ALT匹配及全项目variant范围。

| 层次 | 交付与验收 |
| --- | --- |
| 科研正式快照 | `20260930_avi_attribution_01`；评分及状态各10,866,094行；10,863,110完整匹配、2,984个MT来源未覆盖；键集、逐列零/负/null和72个跨染色体原值抽样通过，见[模块结果](../../../../modules/Alphagenome/docs/result.md) |
| Web服务数据 | `Web/data/tables/avi/attribution.parquet`；全部18列＋variant_id＋状态，绑定已发布科研快照；构建拒绝未发布来源 |
| PostgreSQL | `web_avi`原子事务导入10,866,094行；主键、行数、现有variant关联及11个抽样值回读通过，孤立variant为0；表及索引2,666,668,032字节，33.20秒；[导入报告](../../../data/postgresql_avi_import.json) |
| 实际API | 72个跨染色体样本的18值一致；EGFR全部4,096个SNV的73,728值与原始BGZF完全一致，含22,578个零和3,090个负值；同位点不同ALT分页、空页版本、仅总分模式通过；[证据](../../../data/avi_live_validation.json) |
| 前端 | 真实彩色正负堆叠、独立总分菱形、18项原值详情、类别聚焦/Show all、200bp SNV定位、共轴悬停、拖选放大和两个reset通过；修正实际ChIP浮层标签挤压换行 |

本轮6项科研mapping/发布门控测试、9项AVI接口测试、8项真实参考接口测试和TypeScript/Vite生产构建通过。实际77个API请求观察耗时0.002–0.449秒；这是本地功能验收，不代表冷盘或并发压测。没有重新全扫2.586TB参考数据或重跑模型。

Playwright真实页：EGFR/lung连续添加ATAC与H3K27ac；iOS选中态浅蓝底/深蓝字；选择`chr7:55019278 A>G`显示raw 1.293、PHRED 26.14866及全部18贡献，定位`55,019,178–55,019,377`的200bp范围，206个SNV均有贡献。选择ChIP时其他类别opacity=0.28、18项详情中16项淡化，Show all恢复。拖选200bp中的一段后显示100bp；视野reset恢复223,659bp且保留两条参考轨道，轨道reset清空参考轨道并重新打开biosample选择，AVI保留。没有浏览器console error；已有Molstar WebGL性能warning不属于此次AVI错误。

当前实页截图：[完整贡献与共轴读数](../../../output/playwright/avi-real-all-contributions.png)、[ChIP聚焦](../../../output/playwright/avi-real-chip-focus.png)。原始归因贡献的和与既有AVI raw存在来源差异，仍不求和重建总分；来源无biosample维度，切换组织只影响参考预测轨道。当前本地功能交付完成，云端迁移未在本批执行。

## 09-29 14:30交互修订（历史验收，彼时归因尚未入库）

按用户截图与六项反馈完成第二轮优化，并更新本地8000：

- 模态和Mean/Maximum、Raw/PHRED选中态统一为全站iOS浅蓝底/深蓝字，保留科研色条。实页计算颜色为`rgb(234,243,255)`与`rgb(22,60,101)`。
- 顶部reset图标清空参考轨道和选择条件、重新打开选择器；坐标栏另设reset图标恢复gene范围并保留轨道。基因轴、AVI和一维参考轨道支持水平拖选，浅蓝区域反馈，松开后放大；Esc取消。指针按下即捕获，移到区外再松开不遗留拖动状态。
- 轴和各轨道共享临时悬停位置，区分点击固定的SNV线；参考信号提供水平值线、垂直坐标线、浮层和明确bin区间。鼠标所在碱基与显示bin保持区别，粗分辨率不插值伪装成逐碱基值。信号按真实bin_edges画阶梯线并裁剪，单个128bp bin在32bp viewport内也可见。Contact矩阵提供自身X/Y十字线；junction浮层说明具体事件区间和值，不把弧高冒充数值轴。
- AVI左侧栏提供Total、官网六类贡献及Contacts/Variant type；点击类别聚焦、其余淡化、Show all恢复。Raw默认，正负贡献分别堆叠，独立总分用菱形；不缩放贡献使其之和等于总分。PHRED仅显示总分，选择贡献类别自动切回Raw。未提供贡献时保留现有总分和明确不可用说明，不画假彩条。
- 区间API增加可选18列贡献/逐行状态及顶层可用状态/来源版本；先限定当前SNV页，再用一次SQL关联贡献与manifest，无逐SNV反查。`include_contributions=false`可只取总分。原始raw/PHRED、ALT范围和分页键不变。

验证：前端TypeScript/Vite构建通过；后端AVI现为9项针对性测试通过，真实PostgreSQL临时表验证已安装分支、同位点ALT分页、零/负/null和空页版本，不写生产归因表。贡献叠条函数以明确的内存夹具验证正负分离、原总分独立、18个真零/部分缺失及输入不变；真实归因绘制仍待源包修复后验收。

Playwright实页验证EGFR/lung的ATAC与H3K27ac：拖选从223,659bp变为74,516bp；视野reset恢复223,659bp，轨道reset保留AVI并重新打开未选biosample的选择器。Esc取消及区外松开无残留。悬停`chr7:55,089,666`的轴/浮层/读数一致，竖线横向差约0.012px；当前bin mean 0.02703、maximum 0.54297，未误认作单碱基原值。点击`chr7:55,019,365 G>T`的详情与悬停一致（raw 1.572、PHRED 30.06956），定位200bp及继续放大32bp通过；后者平移后单个ChIP原生bin仍有横线。PHRED→ChIP自动切Raw、侧栏淡化和总分保留通过；无浏览器console error。

当前截图：[侧栏与200bp共轴轨道](../../../output/playwright/alphagenome-crosshair-sidebar.png)；[最终页面状态](../../../output/playwright/alphagenome-final-lung.yml)。截图中的彩色参考轨道是真实值，AVI彩色贡献仍不可用。归因故障和恢复依赖见本页末节，不因交互交付改变数据状态。

## 设计与实际行为

依据用户提供的官网调研ZIP，先形成[共轴轨道设计](../../plan/01_preview_optimization/alphagenome_atlas.md)，再实现前后端。蛋白页固定当前gene，按 `Biosample → Modality → 具体assay/strand/mark/TF → Add` 选择；切换模态保留biosample，可连续加轨、去重、重排、折叠和移除。共享splice sites独立标示，不虚构组织归属。

AVI置顶并独立于biosample，支持PHRED/Raw、逐等位SNV检查、详情和200bp定位。所有轨道共用区间和选中位置参照，各有独立Y轴。左侧固定标签、细色条和分隔加强轨道边界；配色参考调研截图，不声称提取了官网CSS。新版读取原生区间，缩放至来源分辨率；contact保留正负值，junction按源事件分页，不沿用旧top 200筛选。

## 已发布的数据与接口

| 对象 | 当前结果 |
| --- | --- |
| 参考科研目录 | `modules/Alphagenome/data/curated/20260929_reference_catalog_01/`：genes 7,707、windows 7,750、protein_gene 7,724、tracks 1,517；不可预测状态保留 |
| PostgreSQL | `web_alphagenome`目录及索引共6,856,704字节；[导入记录](../../../data/postgresql_alphagenome_reference_import.json) |
| 原生参考数据 | Newsmy_6T的`20260928_reference_local_01`，统一ALL_FOLDS，11模态/33 biosample/1,517 tracks；HDF5按viewport读取，不展开为逐碱基SQL行 |
| AVI总分 | 沿用`web_variant.variant`既有raw/PHRED；限定当前gene关联的项目SNV，不扩大全基因组收录范围 |
| AVI贡献 | 已从`20260930_avi_attribution_01`导入全部18列与状态，详情和区间轨道读取真实贡献；验收见页首 |

参考API保持 `/api/proteins/{accession}/expression/alphagenome` 与 `/track`；新增同目录 `/avi` 返回区间内SNV，`/api/variants/{variant_id}/avi` 返回独立总分/贡献详情。API区间采用0-based half-open，页面坐标为1-based inclusive。AVI以位置和variant_id分页，同位点不同ALT保留；游标绑定蛋白、gene、window和区间。

活动PostgreSQL继续位于NVMe，HDF5保留外盘。迁云时两类资源分别迁移，不能仅迁数据库就获得参考轨道。配置、导入命令与文件部署边界见[开发说明](../../development.md#alphagenome与avi服务数据)。旧参考展示依赖已替换；本批不执行云部署。

## 09-29首轮验证范围（归因入库前）

- 8项参考轨道测试通过：完整目录、全部11模态、当前HGNC关系和错误区间、原生源值、零/负值、contact及128bp边界、junction分页、不可预测gene状态、禁止跨窗口混合。真实完整1,048,576bp窗口的11模态请求通过，[接口证据](../../../data/alphagenome_reference_validation.json)。缓存未强制清空，不代表冷盘或并发压力性能。
- 5项AVI接口测试通过：坐标与游标范围、同位点多ALT、零/负/缺失、贡献不重算总分、版本与行同快照读取。7个float64边界样本经真实Arrow CSV→PostgreSQL临时表路径位级一致；这不是全量归因导入验收。
- 前端TypeScript/Vite构建通过；本地服务已更新。Playwright在EGFR/P00533的1440×1000桌面页实际验证：先lung再RNA-seq/DNase并连续加轨；全gene AVI 4,096个SNV；同位点A>G/A>T分开；PHRED/Raw与库一致；选中`chr7:55019278 A>G`显示PHRED 26.14866、raw 1.293。
- `Zoom to variant`将范围变为`chr7:55,019,178–55,019,377`（200bp），保留选中SNV和详情；该范围206个SNV全部返回。lung ATAC、DNase显示原生1bp/bin，选中蓝线对齐；实测重排、折叠、展开、移除有效。定向浏览器检查无console error。已有Molstar WebGL性能warning未归因于本次轨道。
- 截图：[gene范围多轨道](../../../output/playwright/alphagenome-new-tracks.png)、[200bp选中SNV与DNase](../../../output/playwright/alphagenome-selected-snv-200bp.png)。[重排/折叠状态](../../../output/playwright/alphagenome-reorder-collapse.yml)保留在本地验证目录。

本批验证限于受影响接口及真实EGFR桌面流程；没有全量扫描2.586TB数值、重跑模型、全站浏览器回归或移动端全面验收。归因正负贡献的组件实现及接口测试不能替代真实正式数据接入后的验收。

## 归因输入故障历史（已由新下载及09-30交付解决）

2026-09-29 23:55更新：用户重新下载的T7归因包已通过两成员ZIP CRC及全部18,958,690个BGZF块完整性校验，错误0；[验证报告](../../../../modules/Alphagenome/runs/20260929_avi_redownload_integrity_01/validation.json)。当时源包完整性阻塞已解除；后续准备/mapping/发布/入库已于09-30完成，见页首。以下故障记录保留历史证据；不再等待旧包下载URL或执行旧包修复。

运行`20260929_avi_attribution_01`于13:42完整解包至EOF时触发ZIP原CRC失败，mapping未开始。既有逐字节比较在ZIP第190,402,240,513字节发现差异；附近4MiB内，本地和T7各有23个无效BGZF块。独立gzip验证及O_DIRECT复读复现，不能直接从T7回填后认定完整。该局部结果不是全包损坏清单，不能据此判断其他所有区域完好。

旧T7 ZIP后来被用户重新下载替代，本地ZIP已按用户要求删除；失败partial和运行记录保留；错误重复执行的旧复制任务已停止并修正脚本命名/主入口。具体证据、范围与恢复步骤由模块的[故障与恢复入口](../../../../modules/Alphagenome/runs/20260929_avi_attribution_01/diagnostics/README.md)统一维护。

当时待可信来源后恢复mapping；用户随后选择重新下载，新包完整验收与正式交付见页首。没有跳过坏区、填零或把输入故障写成未命中。18列贡献之和与既有raw的差异仍未解释，继续保留原值，不以归因重算AVI总分。
