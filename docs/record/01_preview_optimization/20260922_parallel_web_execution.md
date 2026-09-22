# 01 Web 优化并行执行批次

2026-09-22。承接[55项问题清单](../../research/01_preview_optimization/issues.md)和[逐项方案](../../plan/01_preview_optimization/01_solutions.md)。本批以三个独立组件/API工作包并行实现，根任务统一集成、构建与本地发布；仅验收桌面端，未重新启动公网 ngrok。科学对象及范围沿用[已确认数据决定](../../research/01_preview_optimization/01_data_decisions.md)，没有引入新的收录阈值。

## 交付与状态

| 范围 | 本批实际结果 | 当前状态 |
| --- | --- | --- |
| UI-01/03 | 全站字体、底色、边框、焦点、标签和局部过渡统一为轻量科研工作台取值；首页保留科学图像，减少装饰层；支持减少动态效果。 | 代码已构建并本地发布；真实桌面观感/操作待验收。 |
| LOC-01/02、GO-01～05、MF-01/02、PH-01～03、RE-01～03 | 细胞区室多来源图、GO证据/文献、膜序列与已映射/未映射OPM、药理分布、Reactome扁平条目及来源入口。 | 代码/API已构建并本地发布；桌面验收待补。 |
| SQ-01/02、AT-01～07、ST-01～04、VA-01/02、VA-09～11 | 多来源勾选、计数色档/PTM统计、显式JSD与结构选区、区段筛选清除/返回、预测工具按组连续比较。结构仅展示surface和已有binding-site，不声称口袋预测。 | 代码/API已构建并本地发布；序列→变异→结构桌面点击验收待补。 |
| EX-01～04、PP-01/02、DI-01/02 | 表达来源/测量联动及完整数据范围矩阵，原值与同组中位数、非负RNA log1p色标；PPI来源→主题→有效分类级联；疾病关系字段精简、来源/分类/证据标签分层。 | 代码/API已构建并本地发布；桌面验收待补。 |
| DI-03/04 | 已接入当前 `variant_summary` 的SNV条件集合列表、关联变异/位点；正式补充同周RCV/SCV原条件、各自分类、版本与来源关系，保留多条件集合语义、summary未列SCV和无RCV状态，不广播variation总体分类。 | 当前SNV范围的数据、PostgreSQL、API及页面代码已发布；桌面点击验收待补。 |
| UI-02 | 已有Figma/React Bits设计brief；本批选择不引入GSAP或大动效依赖，用现有React/CSS完成可复用视觉基础。 | Figma画布/真实设计样稿未交付：本会话无可调用的Figma工具。 |
| VA-06 | foundation正式发布代表ENSP→UniProt全长精确关系及每基因状态；Web投影独立服务表并导入PostgreSQL，详情API核对代表身份后展示所有匹配accession/isoform或明确未匹配/缺输入状态。 | 数据、API、页面代码已发布；真实桌面验收待补，不以gene关联宣称isoform匹配。 |

之前完成的MEM-01～03状态不变；VA-03/05/07/08的已有代码及本地发布在本批复核，仍待桌面点击验收；VA-04全转录本补全继续为用户取消，不记作完成。

## 有限验证及样本

- 统一候选构建：`npm exec tsc -- -b`及`npm exec vite build -- --outDir /tmp/memvar-web-build.OhEAq4`通过（1709模块）。发布到`Web/frontend/dist/`，重启本地Uvicorn 8000；`/api/health`返回PostgreSQL、只读、ok，主页与dist一致，入口JS/CSS均200。
- 修改的7个API文件通过`py_compile`；`test_ppi_collections.py`、`test_predictor_selection.py`、`test_sequence_prediction_coverage.py`合计13 tests及5 subtests通过。只做相关定向测试，没有跑全量smoke。
- 临时8001对真实样本核对：P00533药理170记录/117独立配体；Q12809 OPM 566映射位置、9未映射结构/链组；P00533序列同时选择UniProt和DeepTMHMM2返回200，选择不存在的OPM topology返回422；HPA cancer sample RNA矩阵8384记录/31组；PPI 7523条当前集合记录；ClinVar当前summary为186条件集、2977变异。临时服务已停止。
- 本地浏览器控制接口未提供可连接的桌面实例，故**没有**完成真实点击、截图、视觉或键盘验收；静态构建和API响应不替代这些验收。
- VA-06数据运行`20260922_representative_sequence_match_01`发布7707个代表基因状态、16665候选序列关系，7242个全长精确匹配、297个精确未匹配、168个代表蛋白输入缺失；重建入口`python run.py foundation build_representative_sequence_links`。Web小服务表导入后orphan为0，精确匹配数与状态表一致。新增前端/API后再次完成TypeScript/Vite候选构建；本地8000重启后健康、入口JS/CSS均200。真实详情样本P00533返回canonical `P00533`，P49758返回isoform `P49758-3`，Q9HCK4返回`exact_unmatched`且无假匹配；三者API均200。
- DI-03/04源包经完整gzip流式读取和根`Dated=2026-09-05`核对；[disease正式报告](../../../../modules/disease/data/curated/20260922_clinvar_snv_conditions_01/report.json)记录当前SNV来源行1,353,893、精确关联RCV 1,812,773及嵌套SCV 2,073,487，原条件成员1,970,800。summary中的RCV/SCV accession均按VariationID×AlleleID＋ID匹配；186,856条XML嵌套SCV未列于summary、205条summary来源行原本无RCV，分别保留状态。Web独立五表服务投影/导入`web_clinvar_snv`，来源行孤儿0；新增代码再次通过TypeScript/Vite生产构建及相关Python语法核对。本地8000的P00533 T790M条件样本返回12条RCV/16条SCV，Q5T011来源无RCV样本返回`summary_no_rcv_accession`，两者API均200；主页与入口JS/CSS均200。

## 保留的科学与工程边界

- ClinVar条件专区只覆盖当前2026-09-06 `variant_summary` SNV。旧RCV/SCV资产标2026-06/07，未与当前汇总拼接。官方同周RCV XML `ClinVarRCVRelease_2026-0905.xml.gz`（6,005,638,621字节）保存在`modules/disease/data/raw/ClinVar/2026-0905/`；以完整来源中的VariationID×AlleleID和summary原accession严格连接。summary accession无版本，因此RCV/SCV版本是同周XML的**观察值**，不是“summary同版本已证明”；RCV分类属于完整TraitSet，条件成员仅作导航，SCV保持具体提交的原分类。只下载RCV包（已包含嵌套SCV），不额外下载VCV大包。[NCBI FTP说明](https://www.ncbi.nlm.nih.gov/clinvar/docs/ftp_primer/)、[发布周期](https://www.ncbi.nlm.nih.gov/clinvar/docs/release_cycle/)。
- VA-06的exact全长蛋白序列关系只证明全长序列相同，不自动证明变异位点映射或临床效应；没有精确匹配并不证明生物学上无关系。多匹配全部保留，输入缺失、未比较与精确未匹配分开。基因身份关联只限定候选，不代替序列证据。详见[foundation规则](../../../../modules/foundation/docs/rules.md)与[结果](../../../../modules/foundation/docs/result.md)。
- Figma文件及桌面体验验收未完成。移动与390px验收仍按用户决定延后。

验证恢复：原末尾重复外键查询被DuckDB优化为病态的blockwise嵌套循环；精确终止该验证进程后保留8张已闭合的run-local候选表，改用哈希等值连接续验并原子发布，**没有重读XML或重建候选表**，差异与恢复说明见正式报告。下一步仅剩UI-02画布和各项真实桌面主路径验收；不无故重复已通过的整批构建/全量扫描，后续变化只定向复核受影响链路。
