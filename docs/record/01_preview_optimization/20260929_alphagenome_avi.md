# AlphaGenome 新版与 AVI 共轴展示

核对：2026-09-30（香港时间）。新版参考轨道与AVI总分、18列归因均已接入本地8000。新下载AVI包完成mapping、正式Parquet发布及PostgreSQL导入，真实贡献页面验收通过。此前旧ZIP故障保留在末节，已解除当前阻塞。

## 恢复清爽配色与当前网站版本提交

2026-09-30：用户反馈米色背景不合适，要求恢复12:57提供两组新颜色之前一版的清爽配色并提交GitHub。已完整撤销这一轮品牌色、来源入口装饰色与互作类别色变更；全站白底/冷灰、蓝色交互态、AlphaGenome原操作/选中颜色恢复。未回退此前完成的功能、排版、科研分类或评分颜色。

本次提交覆盖`a7f7c68`之后已完成的网站工作：独立GTEx组织的QTL共轴轨道和API、MANE外显子/CDS/UTR结构及服务表导入、浮层portal避让、AVI密集绘图修复、选择器精简、全站文字清晰度和科研星级配色。下文“未提交GitHub”描述各项完成当时的状态，此批统一纳入网站版本。上游正式Parquet及PostgreSQL数据仍保留本地，未随网站代码上传。

验证：22项既有AVI、AlphaGenome和QTL测试通过，TypeScript/Vite构建与`git diff --check`通过；新构建CSS/JS产物恢复至试色前的同一版本，浏览器确认背景`#f5f6f8`、阅读面白色、AlphaGenome操作蓝`#075bd8`及中性绘图区。仓库提交仅含源码、配置与文档。截图保存在本地`output/playwright/palette-reverted-alphagenome.png`。

## AVI密集绘图去除黑块遮挡

2026-09-30用户指出AVI总分与贡献叠成黑块。实际EGFR全基因窗口223,659bp包含4,096个SNV、2,709个位点；在850px有效绘图区中只占39个像素列，一列最多248条。旧版5.6px直径总分菱形、逐条常驻竖梗和117px有效高度放大了遮挡。参考截图不能证明其窗口跨度与当前全基因视野相同。

`AlphaGenomeAvi.tsx`修复为200px有效高度（Canvas总高246px）；贡献先画、总分后画，菱形半径按所在像素列的记录数调整为0.65/0.95/1.5px，并在一个路径中绘制，避免重复抗锯齿加深。去掉逐SNV常驻灰梗，仅悬停/选中保留定位线和放大标记。贡献保留原正负堆叠，真实零不填0.4px伪高度，小贡献按真实亚像素高度绘制。当前类别色与默认仅Total不变。密集视野提示拖拽放大，悬停显示同坐标ALT数；所有记录保留原始x/y和值，无最大值/均值替代、抽样或横向抖动。

验收：构建和git diff检查通过；真实EGFR全基因仍4,096/4,096条，局部200bp（55,019,222–55,019,421）仍206/206条，Canvas密度状态从dense变为resolved，彩色贡献与总分小标记可分辨。多选类别、逐等位键盘/详情、Raw/PHRED仍沿用原语义。此修复不承诺在全基因有限屏幕宽度上分开每个SNV，局部需放大。

本地8000已更新，未提交GitHub。截图：[原始全基因绘图](../../../output/playwright/avi-density-before.png)、[调整后全基因](../../../output/playwright/avi-density-after.png)、[调整后200bp局部](../../../output/playwright/avi-density-local.png)。

## 变异表恢复科研语义配色

2026-09-30用户进一步明确：变异表的star、consequence、不同评分程度继续沿用既有科研配色。撤除前一轮`VariantCatalog`的表内7.5对比度token覆盖，以及compact评分/AF的二次压暗；主表与详情回到同一`scientificCssVariables`、`scoreVisual()`和`frequencyStyle()`，不回退此前已废弃的独立八色。字体尺寸、来源字重和清晰中性背景保留。

星级此前被`.ve-stars .filled`绑定到frameshift色，现改为`palette.ts`独立reviewColors（实心#b88210、空心#7b8490），表格和详情共用；星级只表示ClinVar review status。ClinVar红/绿/黄/蓝分别沿用致病/良性/不确定/冲突分类；consequence保持各类型原颜色。评分优先来源分类，没有来源分类时仅按既有方向连续着色；SIFT反向、REVEL正向逻辑不变。AF蓝色深浅仅为频率幅度；零与缺失仍区分。无数据重跑或规则/阈值更改。

验证：TypeScript/Vite构建与git diff检查通过；真实EGFR表格核对金色实心星、红色Damaging、绿色Tolerated、consequence和连续评分色值。截图[科研配色恢复](../../../output/playwright/variants-scientific-colors.png)。本地8000已更新，未提交GitHub。下节7.5:1为已撤回的视觉试行记录，不再作为当前颜色要求。

## 转录本结构、选择器溢出与变异表文字

2026-09-30：根据用户NAGS参考截图，新增真实MANE转录本结构显示。先从同一MANE1.5原始GTF补充来源exon/UTR/transcript，经foundation正式发布与Web投影后导入PostgreSQL；当前`web_mane.gene_cds`模型保持原API和segments，追加exons/utrs与transcript端点。快照`20260930_mane_structure_02`；上游原值、负链和缺失核对见[验证报告](../../../../modules/foundation/runs/20260930_mane_structure_02/validation.json)，未更改代表选择和既有CDS/stop_codon。

- 同轴中心线：exon薄轮廓、UTR灰色14px、CDS蓝色24px，独立stop_codon绘于最上层；方向箭头仅在内含子处。各片段hover显示来源范围，点击或键盘Enter/Space放大；Explore CDS仍专门定位编码段。没有来源CDS的模型不把exon涂为CDS/UTR。
- 下拉统一留出38px右侧空间并使用内置箭头；不再让原生箭头贴着圆角边缘。长选项保持原始完整文字供展开选择，收起时省略；选择底色保留明确浅青色。
- 变异表局部文字使用同色相较深色：评分、AF、分类/后果/来源及REF/缺失标记。评分渐变各101点最小白底对比度7.500、hover底6.923；来源标签13px/600。原评分、阈值、关联、图条填充色均未变。

验收：TypeScript/Vite构建、git diff空白检查通过。真实EGFR API返回28个exon与2个UTR，transcript chr7:55,019,017–55,211,628；CDS exon1显示55,019,278–55,019,365，定位窗口仍为200bp。外显子、UTR、CDS中心均在SVG y=66；点击UTR得到418bp窗口55,018,938–55,019,355，滚轮平移后55,019,008–55,019,425，跨度不变；拖拽能放大到55,190,001–55,212,500并显示末端8个exon。桌面最长biosample选项peripheral blood mononuclear cell正常；390px选择控件client/scroll均304px，容器均334px。实际表格link为rgb(49,87,111)、零AF为rgb(73,85,101)。浏览器0错误，仅原蛋白查看器WebGL性能warning。鼠标拖拽后SVG默认黑色focus框已移除，键盘focus-visible仍保留蓝框。

本地页面已更新，未提交GitHub。截图：[转录本局部](../../../output/playwright/mane-transcript-structure.png)、[CDS/UTR交界](../../../output/playwright/mane-cds-focus.png)、[桌面选择器](../../../output/playwright/mane-selector-long-desktop.png)、[窄屏选择器](../../../output/playwright/mane-selector-mobile.png)、[变异表](../../../output/playwright/variants-stronger-ink.png)。

## Atlas式清晰度：AlphaGenome优先与全站视觉整理

2026-09-30用户明确授权替代旧配色/界面要求，以截图中坐标、数值和操作的清晰度为目标。实施的是呈现与样式架构调整，不重跑数据、不修改值、阈值或关联规则。

- AlphaGenome/QTL选择器由大块卡片列表改为紧凑圆角下拉。AlphaGenome仍先biosample后modality，GTEx tissue仍独立；禁用、未选、已选区分。默认选择区域约162px高，选中后显示实际信号列表及可往返Add按钮。
- 白色轨道标题列、浅中性灰绘图区、深色12px坐标与数值标签、6px轨道间隔；合并重复说明，科学解释集中Guide，缺失/不完整数据提示保留。参考曲线同色系加深以增强辨认，CDS蓝块与色标同步；AVI总分改深色菱形，贡献分组与原始值不变。
- 全站UI token集中`design-system.css`，删除refined/ios中的旧重复根定义；正文#202124、辅助#4b515a、操作蓝#0757c9、选中底#cce8ff。导航、菜单、弹窗背景不透明；没有重写各科学图形颜色。移除SectionNav跨栏目滑动的背景层，当前项直接着色，避免动画经过其他文字时遮挡。
- `alphagenome-expression.css`重整为基础/选择器/坐标/轨道/AVI/浮层/响应式分段，删除旧卡片选择器和多轮覆盖；保留实际共用GenomeInspector的portal/视口定位，未引入假设性数据抽象。

验证：TypeScript/Vite构建与git diff检查通过。1414×827真实EGFR页选择skeletal muscle/CAGE并添加双链，同时添加Adipose Subcutaneous eQTL37条；浮层BODY独立层完整显示两链Mean/Maximum（top560.2,bottom731.2），CDS exon1仍定位55,019,222–55,019,421（200bp），删除QTL不影响参考轨道。坐标/AVI类别实测12px；选择下拉有明确浅青选中背景。390px视口workspace364px/scroll364px、选择器334px/scroll334px，无区域横向溢出。概览、变异、表达、互作桌面宽度与scrollWidth一致；首页1414px无横向溢出，导航最终active底色rgb(204,232,255)，无滑动遮字。浏览器无console error；蛋白页曾记录WebGL GPU ReadPixels性能warning，未出现交互错误。未扩大为全站全部数据状态的验收。

本地8000已更新，未提交GitHub。截图：[选择器](../../../output/playwright/atlas-clear-selected.png)、[轨道](../../../output/playwright/atlas-clear-tracks.png)、[数值浮层](../../../output/playwright/atlas-clear-signal-inspector.png)、[窄屏](../../../output/playwright/atlas-clear-mobile.png)、[互作](../../../output/playwright/site-clear-interactions.png)、[首页](../../../output/playwright/site-clear-home.png)。旧截图中导航的移动色块已由最终静态选中态替代。

## iOS选择器与基因/CDS信息层级

2026-09-30：biosample改为边框卡片、hover反馈、浅蓝选中背景与勾号；步骤标题15px，候选名称14px，模态与Add按钮强化蓝色操作态。QTL组织选择沿用同一层级。基因名称22px深蓝突出，CDS图例与实际蓝色块呼应，Explore CDS选择器强调可操作；链方向/转录本/方法说明降为辅助。保留键盘焦点与减少动态效果偏好。未更改任何来源数值或坐标比例。

已检查Figma工具，设计库查询需要具体fileKey，本次未提供Figma文件；依据用户网页截图和现有站点样式直接修改代码，未创建或写入Figma文件。TypeScript/Vite构建、git diff空白检查通过；1414×827真实EGFR页核对biosample唯一选中态、基因22px、CDS exon1定位200bp（55,019,222–55,019,421）。浏览器console error为0。截图：[选择器](../../../output/playwright/agx-hierarchy-picker.png)、[基因与CDS](../../../output/playwright/agx-hierarchy-cds.png)。本地8000已更新，尚未提交GitHub。

## GTEx QTL共轴轨道与字体调整

2026-09-30用户授权同时展示QTL与AlphaGenome，独立选择GTEx组织。新增Add QTL入口、组织搜索和eQTL/sQTL/apaQTL添加/取消；每条轨道明确显示类型、完整tissue、GTEx v11及关联证据属性。模态15px、组织14px、主要辅助信息12px，深蓝主标题/深灰蓝正文；独立来源配色使用专属palette。

`AlphaGenomeQtl.tsx`绘制各条来源关联，横轴为variant坐标（1-based显示），纵轴−log10(P)，原始P/slope及phenotype保留在浮层与明细。同位点关联不合并、不按项目SNV/CDS筛选；零/缺失/非法P不伪造成有限log值，明确计数且保留原始明细。按gene/组织数据集/区间查询`web_context.gtex_qtl_pair`，复用已有gene/dataset索引，参数绑定，验证当前protein→gene及数据集关联。每页2,000条来源顺序记录，显式计数与翻页；纵轴依当前页原值显示。没有重跑科研流程或修改数据库原值。

验证：EGFR当前视野Adipose Subcutaneous eQTL37条、sQTL3条，Skin Not Sun Exposed Suprapubic apaQTL5条；三类型单碱基区间边界正确，反向区间422。较大数据集P10321/皮肤sQTL共90,884条，两页各2,000条且source_row无重叠，查询约0.69/0.13秒。1176×827真实浏览器验证三类添加、独立组织、浮层原值、放大后eQTL变29条/其他两类当前区间空、恢复gene视野、移除sQTL保留其他选择。AlphaGenome cortex of kidney RNA-seq同时添加并实际读出；首次外置盘读取较慢，未将其视作QTL查询失败。构建、差异空白检查通过，浏览器无console error。

当前仅展示所选模型窗口中的QTL，轨道明确提示范围；未做全QTL范围扩展、下方列表定位联动或自动GTEx→AlphaGenome组织对应，未建立AVI等位基因匹配。已更新本地8000，未推送GitHub。截图：[三类QTL](../../../output/playwright/qtl-three-tracks.png)、[QTL与AlphaGenome并列](../../../output/playwright/qtl-with-alphagenome.png)。

## AVI悬停面板排版修订

2026-09-30：用户反馈贡献名称和值拼接成段落、换行错乱。已改为320px面板，坐标与REF→ALT同一行；总分标明尺度，原始特征按名称/数值两列展示，保留类别色点。零值压缩成数量提示、缺失单列提示；已选类别最多显示绝对贡献值最大的6项非零特征，超出明确标注，详情仍保留完整18项。本轮仅更改悬停摘要，不改变原值、轨道或数据库。

TypeScript/Vite构建通过。1176×827真实EGFR验证：单类Protein impact显示Protein termination 1.546与3个零值提示；多类显示Total与6项贡献，各数值右边界均为1093px，面板320×334px，完整详情18项。截图：[单类别](../../../output/playwright/avi-tooltip-protein-aligned.png)、[多类别](../../../output/playwright/avi-tooltip-multiple-aligned.png)。已更新本地8000；此修订发生于a7f7c68发布之后，尚未提交GitHub。

## 参考轨道与AVI浮层裁剪修复

2026-09-30：真实CAGE双链叠加轨道复现浮层超出轨道容器23.5px，被`overflow: hidden`裁剪。共享GenomeTooltip改用body portal和fixed定位，按实际面板尺寸限制视口边界，底部空间不足时向上显示；滚动、缩放及面板尺寸变化后重新定位。参考信号、junction、contact与AVI共用此定位层，保留轨道容器边界及原始数值。

TypeScript/Vite构建、差异空白检查通过。1176×827真实EGFR页面验证CAGE双链面板完整展示；靠近底部时面板自动上移至y=534.25–691.75。AVI多类别333.6px高面板同样位于视口内且无裁剪祖先，移出轨道后正常消失；浏览器console无error或warning。截图：[常规位置](../../../output/playwright/genome-tooltip-unclipped-400.png)、[底部自动上移](../../../output/playwright/genome-tooltip-unclipped-700.png)。已更新本地8000，尚未提交GitHub；未扩大为全站或所有轨道数量的回归。

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
