# 09. AlphaFold v6 膜蛋白结构筛选、下载与 3D 查看计划

状态：已完成（M10.1–M10.4，2026-08-12）  
计划日期：2026-08-12  
适用阶段：M9 完成后的 M10 Structure 纵向功能  
范围：只读取 `structure/UP000005640_9606_HUMAN_v6.tar` 与 `View/Basic_info/protein_basic.parquet`；所有筛选产物、索引、API、前端和测试均写入 `website/`。

## 1. 用户目标

1. 从全人类 AlphaFold v6 归档中筛出 memVar 的 canonical 膜蛋白 PDB。
2. 在每个 protein 页面提供对应 PDB 下载。
3. 新增 Structure 板块，交互展示 AlphaFold 预测结构，采用与 CATVariant/ProtVar 相近的“结构优先、置信度分色、下载与查看并列”模式，但不复制品牌布局。
4. 长蛋白的 AlphaFold fragments 可以明确切换、分别查看和下载。

## 2. 源数据审计与恢复边界

- 膜蛋白全集以 `View/Basic_info/protein_basic.parquet.uniprot_accession` 为唯一网站范围，当前 7,728 个且 accession 唯一。
- 用户归档大小为 5,177,506,304 bytes。文件开头不是标准 tar；有效、连续、512 对齐且有正确结束零块的主 tar 从 byte offset `5,696,512` 开始。
- 主 tar 含 47,016 members：23,508 个 CIF.gz 与 23,508 个 PDB.gz，二者 fragment 集合完全配对；覆盖 20,477 个 accession。
- 与膜蛋白集合交集为 7,624 accession（98.6542%），筛选得到 8,837 个 PDB.gz；104 个 accession 无模型。
- 81 个膜蛋白有多个 fragment；`F<n>` 是同一 canonical protein 的 AlphaFold 长序列分片，不是 isoform。Q8WXI7 有 67 个分片；P00533 只有 F1。
- 不修改或“修复”原 tar。构建器必须验证并显式使用有效主段；若主段起点、header checksum、路径格式、gzip CRC、结束块或预期配对不满足合同，立即失败，不静默接受部分结果。

## 3. M10.1：可重复的膜蛋白 PDB 筛选

新增 `etl/build_structure.py`：

- 从 `protein_basic.parquet` 读取 canonical accession allowlist，不从 tar 文件名反推网站全集。
- 默认拒绝非标准 tar；本次数据通过显式 `--recover-prefix` 模式扫描并验证连续主 tar 起点。审计值 `5,696,512` 只作断言/错误提示，不把损坏前缀当成员；构建日志必须标明 recovered archive 与缺失数。
- 只提取严格匹配 `AF-{ACCESSION}-F{positive integer}-model_v6.pdb.gz` 且 accession 位于 allowlist 的成员。
- 防止路径穿越、重复 `(accession, fragment)`、fragment 间断、symlink/hardlink 和覆盖；仅接受普通文件。
- 每个选中 gzip 完整读取以验证 CRC，再原样写入：
  `website/data/generated/structure/alphafold/v6/{ACCESSION}/AF-{ACCESSION}-F{n}-model_v6.pdb.gz`。
- 生成 `manifest.parquet`：accession、fragment number/label、filename、relative_path、compressed/uncompressed bytes、gzip/PDB SHA-256、由 PDB `DBREF` 解析的 canonical start/end、model_version、source。
- 生成 `missing_accessions.parquet`，明确记录 104 个无模型的 canonical accession；这是产品空态清单，不是额外评分或 QC 报告。
- 使用临时输出目录构建，验证完成后原子替换目标；绝不写入 `View/` 或 `structure/`。

## 4. M10.2：Structure API 与安全下载

新增：

- `GET /api/v1/proteins/{acc}/structures`
  - 先用 canonical protein registry 校验 accession；
  - 返回 `availability`、source=`AlphaFold DB`、model version=6、fragment 总数；
  - fragments 按数字排序，每项含 fragment label、compressed/uncompressed bytes、viewer/download URL。
- `GET /api/v1/proteins/{acc}/structures/{fragment}/pdb`
  - 仅从 manifest 精确匹配，不直接拼接用户输入路径；
  - 返回原始 `.pdb.gz`，文件名保持 AlphaFold 官方命名；
  - `Content-Disposition: attachment`，版本化资产使用 immutable cache；
  - 支持 HEAD/Range，并验证 `206`、`Content-Range`、`Accept-Ranges`。

空结构是 `200 + availability=unavailable + fragments=[]`；不存在的 protein 为 404；不存在/非法 fragment 为 404/422。API 不扫描源 tar、不访问外部网络、不允许路径越界或 symlink 逃逸。

## 5. M10.3：Structure panel 与 3D viewer

- 在 protein 页新增 `Structure` 导航和全宽 Structure 板块，放在 Sequence 后、Variants 前。
- 使用 `3dmol@2.5.5`；Viewer 作为独立 Client Component，通过 `next/dynamic(..., {ssr:false})` 延迟加载，且仅在板块进入视口或用户请求查看时初始化。
- 浏览器 fetch PDB.gz ArrayBuffer，3Dmol 以 `pdb.gz` 加载；不在 API 服务器重复解压。
- 默认 cartoon 表示，按 PDB B-factor 中的 AlphaFold pLDDT 四档分色：
  - Very high `>90`：`#0053D6`
  - Confident `70–90`：`#65CBF3`
  - Low `50–70`：`#FFDB13`
  - Very low `<50`：`#FF7D45`
- 图例必须说明这是 predicted confidence，higher is better，不是实验 B-factor。
- 支持 fragment selector、Reset view、Spin、Fullscreen、Download PDB；鼠标旋转，滚轮/双指缩放。
- 分片切换时中止旧请求、清空旧模型并重新 fit；显示当前 fragment、文件大小、AlphaFold v6 和预测模型免责声明。
- 分片 canonical range 必须来自 `DBREF`；不得把每个 PDB 分片内从 1 开始的 residue number 直接当作 canonical coordinate。
- 无 WebGL、加载失败或无模型时仍显示清晰空态/错误态与可用下载链接；Canvas 不是唯一信息来源。
- viewer 卸载时停止 spin、清理模型/ResizeObserver/fetch，避免页面切换后资源泄漏。

## 6. M10.4：验收

- 数据：7,624/7,728 accession available，8,837 PDB fragments，104 missing；所有 gzip CRC、文件大小、manifest 路径和 fragment 连续性正确。
- P00533：available、只有 F1；list/download/viewer 数据一致，gzip magic、官方文件名与响应头正确。
- Q8WXI7：67 fragments，按 F1…F67 数字排序，切换和下载不会按字典序错成 F1/F10/F2。
- 缺失 accession（如 O43687）：明确 unavailable，不渲染空 viewer。
- 非法 accession/fragment、编码斜线、路径穿越、根外路径与 symlink 均被拒绝。
- Range、HEAD、immutable cache、CORS 所需 GET/HEAD header 正确。
- Viewer 支持 loading/error/no-WebGL/empty、Reset/Spin/Fullscreen/Download 和键盘/触屏操作。
- 后端全量测试与前端 production build 通过；确认 `View/` 和源 tar 未改动。

## 7. 明确不做

- 不把 AlphaFold 预测结构称为实验结构，不推断配体、复合物、膜朝向或功能状态。
- 不将不同 F fragments 拼接成伪造的单一 3D 模型。
- 不在首版将 Variant residue 强行投影/高亮到 structure；后续必须先定义 fragment residue mapping 合同。
- 不暴露整个 4.9 GB tar，不在请求时线性扫描 tar，不提供任意文件路径下载。
- 不把 CIF 一并复制进网站；当前下载和 viewer 合同只使用 PDB.gz。

## 8. 实施与验证记录

- 已通过显式 damaged-prefix recovery 构建网站结构资产；源 tar 与 `View/` 未修改。
- 正式产物为 7,624 个可用蛋白、8,837 个 PDB.gz fragments、104 个缺失 accession，磁盘约 840 MB；manifest 与 missing 清单已生成。
- 每个选中 PDB 已验证 tar header checksum、PDB/CIF pairing、gzip CRC、gzip/PDB SHA-256、DBREF canonical range、fragment 连续性及路径安全。
- 发现 8 个 AlphaFold v6 fragment 的 DBREF end 超过当前 UniProt 2026 registry length；这是跨 release 差异，已忠实保留 PDB DBREF 坐标且未篡改。
- Structure API 已支持清单、显式空态、安全下载、官方文件名、GET/HEAD/Range、immutable cache 和 CORS Range headers。
- Protein 页面已加入延迟加载的 3Dmol viewer、fragment selector、pLDDT 四档、Reset/Spin/Fullscreen/Download 及 WebGL/error/empty 降级。
- 后端全量测试 `68 passed`，结构 ETL 测试 `5 passed`，前端 production build 与 TypeScript 检查通过。
- 浏览器的真实旋转、缩放、全屏与视觉观感保留给本地人工审阅；自动验证不执行未经请求的浏览器点击或截图。
