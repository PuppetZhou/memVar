# AlphaGenome：独立的多模态预测板块

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-21 当前决定：复用旧网站降采样数据，AlphaGenome作为独立板块，位于Expression与QTL之后、PPI之前，并有独立章节导航。替代此前嵌入Expression的布局，因为预测涵盖表达、染色质、剪接等多种模态；它不是实测Expression和QTL记录的合并结果。默认一个模态和一个场景，可自行添加轨道，不设轨道数上限。不改变其他数据库数据或科研处理。

## 存储与后端决定

本轮不导入新的 PostgreSQL 表，也不重跑预测/API。PostgreSQL 继续提供当前蛋白身份及 HGNC 关联；已有只读 DuckDB 小目录提供轨道和窗口元数据，Parquet 提供密集信号。约 49.71 GiB 展示文件原位复用，不复制到数据库。它们是已降采样的历史 Web 资产，不能称为完整原始预测矩阵。

- 配置：`Web/config/alphagenome.yaml`；部署可用 `MEMVAR_ALPHAGENOME_ASSETS` 覆盖根目录。环境变量指向同一结构的已构建目录，不触发构建。
- 来源：旧网站 `data/generated/alphagenome`，manifest 时间 `2026-08-17T07:39:30.492989+00:00`，schema version 1，GRCh38。
- 历史目录覆盖 7,637 个基因、7,746 个窗口、9 模态、492 轨道。本轮复核 manifest、目录元数据和 EGFR 九模态文件；没有全量重验所有信号文件。
- 身份关联：历史明确 accession→Ensembl 关系同时满足 has_prediction/display_ready，且其 HGNC ID 必须存在于当前 PostgreSQL 蛋白 HGNC 关系。保留多基因选择；不凭 gene symbol 新配对，不宣称 isoform 匹配。
- 只读接口：`GET /api/proteins/{accession}/expression/alphagenome` 返回匹配基因、窗口、轨道目录、来源/限制；`GET .../alphagenome/track?gene=...&tile=...&track_id=...&bins=...` 按一个轨道读取。
- 信号返回 mean/maximum，档位 256/1024/4096；contact 返回 128×128 矩阵；junction 返回旧资产保留的至多 200 条。每个请求有界，不限制用户累计选择的轨道数量。
- 非有限信号转 null，不伪装成零。请求校验当前蛋白关联、gene/tile/track/分辨率及资产路径；元数据缺失或不可读有独立错误态，不拖垮实测 Expression。

## 界面与科学含义

页面顺序为Expression → QTL → AlphaGenome → PPI。AlphaGenome使用独立`#alphagenome`锚点、二级标题与章节导航；Expression只保留跨板块跳转入口，实测来源、组织浏览器和筛选表维持原位。选中实测组织的标签通过页面级状态传入独立预测区，继续提供场景导航提示。旧`#expression-predictions`锚点保留为兼容定位。仅对标签做大小写/分隔符标准化后的相等匹配；使用元数据中的 `gtex_tissue` 或 `biosample_name`。它是导航候选，不证明同一样本、队列或测量可比较；不做模糊组织推断。无匹配时明确提示，允许自主浏览其他场景。

默认一条 RNA-seq / Lung 轨道（优先目录中的 GTEx Lung 标签；不可用时退回首个 RNA-seq/首轨道），其来源场景在轨道标题可见。已选实测组织不会静默替换当前轨道，用户通过 Explore this context 打开匹配场景库并显式添加。

- 模态卡片提供类别与轨道数；用途/单位说明统一收纳于问号指南，场景下拉和搜索按真实目录过滤，保留 assay/strand/histone mark/ontology 和 source。
- 添加无数量上限，同一轨道不重复添加；支持排序、折叠、移除、清空。接近视口的展开轨道才请求，使用 React Query 去重与缓存；不预取全部 492 轨道。
- 所有轨道共享 GRCh38 窗口，支持基因区域、放大/缩小、平移、恢复全窗口与分辨率选择；多窗口逐个浏览，不加总重叠窗口。
- 连续信号使用模态语义色、明确 y 轴、均值/最大值切换、鼠标/键盘逐 bin 查看。各轨道独立 y 轴，不将跨模态数值归一成统一表达量。
- Junction 弧线附坐标/值表，明确最强 200 条的截取；contact 使用独立热图，鼠标/键盘查看两个轴区间和值。
- 明确标为参考序列预测，不是实测 TPM、变异 REF/ALT 差值或致病结论，与 Variant Browser 中 Atlas 分数区分。
- 1 Mb 窗口最细展示为 256 bp/bin；放大不能恢复碱基级细节。DNase / TF ChIP 不在该历史快照。

## 验证与当前限制

2026-09-21：`python -m unittest Web.tests.test_alphagenome_expression -v` 五组测试通过，涵盖 EGFR 九模态、三档分辨率、窗口/轨道/身份越界、不匹配身份及非有限值。`npm run build --prefix Web/frontend` 的 TypeScript 和生产构建通过。运行中 8000 端口接口已返回新目录。

浏览器技能连接返回 `No browser is available`，按故障指引检查可用实例为 `[]`。因此本轮未执行截图、真实点击、控制台与移动视口验收；不能把构建通过表述成视觉验收通过。未做全蛋白资产逐文件核查或公网并发压力测试。运行中 HTTP 验证：EGFR 目录返回 492 轨道，九模态请求均为 200，单次本地观测约 18–41 ms（非负载基准）；现有 health、Expression summary、GTEx contexts 均为 200。

代码维护入口：`Web/src/api/alphagenome.py`、`Web/frontend/src/components/AlphaGenomeExpression.tsx` 和同名样式文件；共享代码包含router注册、独立页面章节挂载/导航与Expression组织标签回传。API保留既有`/expression/alphagenome`路径以兼容现有调用；本轮布局移动不改存储或预测处理。

2026-09-21 布局调整：独立章节移动、导航及组织联动已实现；整站`npm run build --prefix Web/frontend`通过（TypeScript与Vite）。浏览器实例仍为`[]`，未补充真实点击/视觉验收。

2026-09-21 文案精修：移除常驻三步介绍与重复长脚注，标题和轨道库共用九模态指南；原降采样/截取/缺口/快照说明集中保留。Contact单位改为log-fold over distance-based expectation，保留负值的0中心蓝/白/橙色标，灰色表示缺失；仅前端显示修正。[来源核对与验收](ui_help.md)。
