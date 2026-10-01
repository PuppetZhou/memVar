# DuckDB＋Parquet 迁移与网站验收

更新：2026-10-01。本轮授权范围已完成：完整存储构建与核验、API 适配、桌面关键流程和现有预览切换。旧 PostgreSQL、旧网站 Parquet、科研数据及外部 HDF5／结构文件均原位保留，等待用户审查网页后再决定清理。

## 来源、布局与重建

统一入口：[migrate_duckdb.py](../../../src/database/migrate_duckdb.py)。来源配置继续集中在 `config/database.yaml`；候选位置见 [duckdb.yaml](../../../config/duckdb.yaml)。从 PostgreSQL `REPEATABLE READ READ ONLY` 导出一个 snapshot，所有导出连接导入相同 snapshot。来源元数据、当前代码提交、库内 build manifest、全部字段、原视图 SQL、约束源表／目标表及键列保存在候选 `manifest.json` 与 `source-metadata.json`。

逐对象机器清单以 `manifest.json` 为唯一维护位置：156 张物理表全部 Parquet；40 个普通视图维持原 SELECT／JOIN／DISTINCT／UNION 逻辑，避免数亿行明细重复保存；4 个 PG 专有 JSON／正则逻辑视图（`ppi_record`、`medgen_names`、`medgen_definitions`、`protein_external_reference_all`）绑定同一 snapshot 材料化。仅 `ptm_evidence_all` 的 `jsonb_array_elements` 需要与 API 共用的 SQL AST 转译。

布局使用 Zstandard level 3、65,536 行文件，均保存统计。一般表为 65,536 行 row group；宽 JSON 数组的 `expression_gtex_gene_tpm` 与 `expression_gtex_transcript_tpm` 为 256 行 row group。大 QTL 表按 `hgnc_id,dataset_id` 排序，支持蛋白→gene 筛选裁剪；其他有主键的表按原主键前两列排序，其余保持完整来源读出内容。原 QTLbase／eQTLGen 分页依赖 PG `ctid`，额外隐藏 `_source_ctid` 保存 `block*65536+offset`，维持原排序 tie-break；它不是科学字段或新关联。当前不保存重复 DuckDB 原生表／索引；是否增加查询结构由全量查询实测决定。两张宽表全量候选重写后逐字段、逐行直接比较通过；旧候选布局保存在 `_pre_layout/`，不进入部署包。

在科研工作区根目录运行：

```bash
python -m Web.src.database.migrate_duckdb build --workers 3
python -m Web.src.database.migrate_duckdb catalog /new/snapshot/root
python -m Web.src.database.migrate_duckdb verify-views /new/snapshot/root
python -m Web.src.database.migrate_duckdb record-locator /new/snapshot/root
```

独立 Web 仓库内可用 `python -m src.database.migrate_duckdb`。`catalog` 仅依赖 snapshot 内的 manifest 与 Parquet，重新绑定新目录，不读取 PostgreSQL。`record-locator` 仅读取当前 snapshot 的来源记录 Parquet footer 重建相对路径定位；它不重导数据、不改变布局或标签。默认源码按目前采用布局重建（两张宽 JSON 表 256 rowgroups，其他 65,536），其执行 profile 与本次实际旧版 text transport 在 manifest 和本报告分别维护。候选先独立生成；任何失败不覆盖已有可用目录，metadata 原子替换。完整目录可重新绑定并部署，数据不随源码上传。`catalog_statistics.json` 作为现有服务必需 sidecar 同步复制；原 HDF5 和结构资源按部署配置指定根目录，不在本轮重压缩。

## 完整性证据及边界

每张导出表全量读取所有字段并严格映射 PG 类型：int4/int8、real/double precision、boolean、text、jsonb、text[]、real[]。JSON 保持来源文本，DuckDB 查询投影为 JSON；数组映射 typed LIST。原基线没有 decimal 或需要降低精度的类型。导出每个 batch 均 Arrow→Parquet→Arrow 全字段直接回读比较，并在相同 PG snapshot 核对整表行数。

执行中的第二轮候选采用上述精确类型映射与 Parquet 全值回读。默认现行源码重建入口额外采用 PG binary cursor 与逐字段 PG→Arrow 精确位模式比较（float4 使用 binary32、float8 使用 binary64），保留 signed zero、NULL、空数组及嵌套 NaN；不把尚未在第二轮运行版本执行的增强核验宣称为已执行。真实 PG 类型边界链与重建回归见 [test_migration_storage_regression.py](../../../tests/test_migration_storage_regression.py) 和候选核验报告。

40 个逻辑视图已从同一 snapshot 保存全量行数、字段类型与 16 条全字段代表值；完整 catalog 的 `verify-views` 已全部通过这些字段契约、全量行数及完整代表记录核验。物理表全内容保留与原 JOIN 逻辑共同证明关联记录、键值及已有孤立状态没有被重筛或补 link；逻辑视图代表值核验不等同逐行重导出其全部值，不将局部 API 成功冒充全部逻辑内容逐行比较。

20260930T160427Z 首轮候选因发现 QTL 原 ctid 分页契约而中断，metadata 标为 `superseded_interrupted`，由 `snapshot-20260930T160803Z` 替代。初轮候选文件保留作过程依据；不作为当前服务数据。

## 当前结果

`snapshot-20260930T160803Z/manifest.json` 当前状态为 `storage_validated`。逐表完整清单、原字段与主外键入口、实际行数和文件映射仅在 manifest 及 source metadata 维护，不另重复逐表目录。

- 156 张物理表共 **519,366,173 行**；4 个材料化视图共 **1,360,448 行**；40 个逻辑视图字段、全量计数与完整代表值核验通过。
- 8,053 个当前服务 Parquet：**27,330,447,487 B（27.330 GB）**。
- 部署必要 Parquet＋catalog＋statistics／record locator sidecars＋manifest＋source metadata：**27,332,500,996 B（27.333 GB）**；对交付时只读实测保留 PG **200,435,783,347 B（200.436 GB）**，结构化持久部署体积减少约 **86.363%**。外部 AlphaGenome 约 **2.586 TB** 未优化、不纳入此减容比例。
- 本机当前候选目录约 **29.925 GB**，包含不部署的旧宽表布局约 **2.592 GB**；首轮中断候选约 **2.211 GB** 另行保留。核验样本、报告与试验记录属于重建／审查材料，不是运行依赖。全部原 PG 与旧服务 Parquet 继续保留；本机共存占用不能只按部署包计算。

容量证据见候选 `capacity.json`，全部视图核验见 `view-verification.json`。新增 `source-record-files.json` 为 **93,242 B** 的 record_id 定位辅助：仅读取 390 文件 footer，保留每文件真实 binary UTF-8 min/max、相对文件名及行数；所有重叠范围均返回，缺失统计回退而不丢记录。footer 合计与全快照行数一致，12 个头／中／尾真实 min/max 边界 ID 正确定位原记录。它避免点查反复绑定全部 glob，没有重复存储任何原 JSON。

完整部署搬迁试验使用只读硬链接把全部 8,053 服务 Parquet 放入新临时根目录，在禁止 PostgreSQL 的情况下重建全部 200 关系 catalog 与 record locator，通过新根读取真实来源边界记录与蛋白计数；临时硬链接已移除。证据为 `package-relocation-verification.json`。相对 locator 文件路径与纯 Parquet catalog 重绑定不依赖开发机原数据库位置。PG read-only snapshot 全量导出约 42.6 分钟；最后仅旧 catalog 翻译不支持 `jsonb_array_elements`，随后以当前纯 Parquet 入口重建，未重导来源或修改 PG。

实际布局试验：transcript JSON 点查 0.350–0.395 s → 0.026–0.028 s，新增约 130 KB；gene JSON 点查 0.999–1.120 s → 0.065–0.093 s，体积少约 9 KB。改写两张表全部值直接核对。65k rowgroup 的 gnomAD 来源 JSON 前缀点查为 0.035–0.049 s，未见整组解压退化，巨表保留原布局；这项前缀试验不代替主任务完整 source-detail API 验收。原值 JSON 文本及数组始终保留，无科学内容处理。

来源性能剖析：P00533 25 条真实 ClinVar ID 的显式 IN 为 0.144 s，实读约 1.35 MB，证明大 JSON 点查可选择性读取；同蛋白全部 2,977 条 ClinVar ID 的 metadata-scope JOIN 约 0.45–0.51 s。DuckDB 此版本动态 OR filter 默认阈值 50，过阈值可能只下推 min/max；查询必须先收窄关联 ID／来源范围。主任务定位 summary 广分类聚合读取不适用来源 JSON 的热点后，以等价的 metadata-only 来源总数与 ClinVar-only 分类查询修复，不引入原值窄副本或科学重分类。最终 API 成果由主验收报告维护。

所有原始数据继续保留，供用户审查网页后决定后续清理；存储核验完成未授权删除任何旧数据。

## API 兼容与查询实现

数据存储、接口适配、独立等价与网页验收分别由三名 GPT6.1 sol subagent 负责，主任务维护架构边界、资源配置、启动与最终发布。前端源码和现有静态构建没有修改，查询结果继续服务同一套展示与交互。

[db.py](../../../src/api/db.py) 支持显式选择查询后端。DuckDB 以只读共享 catalog 连接运行，每个请求使用独立 cursor，默认共享 4 GB 内存限制、4 个查询线程；进程初始化加锁，不为并发请求重复创建连接。[duckdb_sql.py](../../../src/api/duckdb_sql.py) 用 SQL AST 转译实际 PostgreSQL API 查询，保持 JSON／数组、聚合 FILTER／ORDER BY、原列标签、空数组、NULL 及 LIKE 转义；不对参数值做字符串替换。float4 的存储仍是 binary32，API 恢复原 psycopg 最短十进制表达，避免扩大为 binary64 后改变网页数值。

[duckdb_collation.py](../../../src/api/duckdb_collation.py) 保留原 `en_US.utf8` libc 文本与 DISTINCT 数组排序。来源 PG 容器 glibc 2.36、当前主机 glibc 2.39；22,473 条实际蛋白、GO、通路与 dataset 字符串的完整排序和 PG 相同，原二进制／ICU 候选未通过。部署需要该 locale；不同系统或 libc 版本应复核原排序，未将本机验收泛化为任意平台保证。

实际大表查询修复均只调整执行范围，保留原结果：EXISTS 内的固定 LIMIT 1／OFFSET 0 去掉 DuckDB 的巨型窗口执行障碍，LIMIT 0 或正 OFFSET 保留；后果 ANY 改为原 NULL／空数组语义的行内判断；变异来源先取真实关联 ID，再通过 footer locator 按匹配文件组读取完整原记录，恢复全部 link multiplicity 和原来源／记录排序。来源名称复用完全相同 inner join 的来源证据，dbSNP 另行查询。摘要拆为只读 metadata 的来源总数和只读取 ClinVar 原分类的查询，避免为被排除的 gnomAD 分类加载 JSON；没有新分类、代表项选择或窄 JSON 数据副本。

locator 首次加载同时核对原 snapshot ID 和来源记录行数，拒绝混包。SQL／locator 16 项与原 SPPIDER／topology／分页 13 项，共 29 项相关回归通过；独立严格比较器与存储类型、失败保护、搬迁回归另见验收报告及 [test_migration_equivalence.py](../../../tests/test_migration_equivalence.py)。已经通过的数据不重新全量扫描。

结构与统计资源位置集中在 [resources.yaml](../../../config/resources.yaml)，HDF5 沿用 AlphaGenome 配置和环境变量。运行时不读取上级科研配置；统计 sidecar 随完整快照部署。启动脚本从自身目录加载 `src.api.main`，独立克隆可以自行命名。在工作区外启动且故意提供不可用 PG 连接时，DuckDB health 与完整静态首页仍返回成功，证明新运行链路无需旧 PG。数据、结构和 HDF5 可迁到新根目录，重绑定 catalog 后按部署环境设置路径；外部 HDF5 仍需要文件系统挂载，未新增对象存储读取支持。

## API、网页与性能验收

完整证据以 [migration_validation/README.md](../../../data/migration_validation/README.md)、`comparison.json` 和 `benchmark.json` 维护；这些本地原值与浏览器记录不提交 GitHub。三代表蛋白为 P00533、P13569、A0A075B6H7，共 **524／524** HTTP 案例通过。严格比较状态码、字段存在、类型、全部值、数组顺序与 PDB 原文；JSON 对象键序不影响语义。唯一预期差异是 health 的数据库标识从 PostgreSQL 改为 DuckDB，同时要求正常且只读。覆盖全部主要 API 板块、来源／后果／预测／AF／区间筛选、offset／游标、未知对象与非法输入、未定位／未匹配／无模型状态及全部 11 种原生 HDF5 modality。真实零与 NULL 不混淆，QTLbase 实际同键记录及跨 tie 分页通过。

浏览器核对完整候选的九个原板块、搜索与总览、来源详情、AF=0、ClinVar 原字段、疾病分类、RCV／SCV 层次与翻页；已完成表的独立候选另核对 PeSTo 三维着色、QTL 切换与滚动分页、HepG2 ATAC 添加及 AVI 位点选择／归因。对应完整 API 全值均通过，不重复读取已验证的全部 HDF5。最终完整服务导航的 console 为 **0 errors／0 warnings**，截图及快照见上述本地报告。验收使用独立 Playwright session，没有操作用户浏览器；本轮沿用桌面验收范围，没有重新验收移动端全部布局。

公平性能在完整快照和固定查询结构上采集，无构建竞争。13 条真实路径分别记录首访，再按相同顺序各执行 26 请求、4 并发，完整响应零差异、零失败：

| 观测 | PostgreSQL | DuckDB |
| --- | ---: | ---: |
| 首次 P00533 默认 20 条列表 | 0.029 s | 0.767 s |
| 首次 P00533 ClinVar 20 条列表 | 0.133 s | 0.824 s |
| 首次 P13569 来源详情 | 0.039 s | 0.471 s |
| 首次 P00533 摘要 | 0.029 s | 1.764 s |
| 首次 P13569 摘要 | 0.036 s | 1.747 s |
| warm 26 请求总耗时 | 0.662 s | 2.094 s |
| warm p50／p95 | 0.046／0.338 s | 0.103／0.853 s |
| warm 最大单请求 | 0.374 s | 0.952 s |

DuckDB 在该工作负载比原 PG 慢，当前默认列表、详情及摘要已恢复可交互响应；初版约一分钟的来源筛选及 19–28 s 摘要已修复。保留旧 PG 与原 8000 服务期间不清 OS 缓存、不重启 PG，首访不是严格冷盘／冷 PG 缓存；候选重启后未预热摘要，记录的是应用首次请求，不能据此声称纯引擎冷启动倍速。26 样本的 p95 为经验分位，不是长期并发保证。

该批次后的候选进程观测 VmHWM 为 2,562,716 KiB（约 2.44 GiB），当时 RSS 约 1.64 GiB。DuckDB 的 4 GB 限制不等同整个 API 进程内存上限，未来不同硬件、进程数或负载须按部署情况核对；本轮不追加无关压力测试。

## 当前预览与保留边界

2026-10-01 香港时间 **01:38**，8000 已从旧 API 进程切换到 `start-local.sh` 的 DuckDB 默认入口，查询同一完整已验收快照。原 ngrok 进程和地址 [memVar 预览](https://renewably-ashy-undiluted.ngrok-free.dev) 保持；仅在 API 重启时短暂中断。发布前候选及发布后现用服务的默认 ClinVar 20 条整份响应相同。localhost 和公网 health 均为 HTTP 200、`database=DuckDB`、`read_only=true`；前端原静态构建正常提供。

**01:40** 独立浏览器复核原公网蛋白页面，EGFR 身份、九板块、序列与三维展示正常，console 0 errors／0 warnings。ngrok 新浏览器仍会出现其原生 Visit Site 提示，点击后正常进入。发布证据为 `data/migration_validation/publication.json`、`publication_health_independent.json` 及验收 README 的发布段。候选 8001 已停止，原 PostgreSQL Docker 容器仍运行，任何旧数据都没有清理。

当前部署位置见 `config/duckdb.yaml`；manifest 保持 `storage_validated`，网站发布事件另由上述 publication 记录维护。当前包虽然仍保留 `duckdb-candidate/` 目录名，已作为验收通过的现用只读快照，不把该目录名当作未验收状态。未来更新先在另一目录完成构建与验收，再切配置并重启，禁止原地改写现用 Parquet。回退入口是明确选择 `MEMVAR_QUERY_BACKEND=postgresql`，使用保留的原只读连接；启动不设置角色、不导入数据。

本轮没有云端上传或旧数据删除。下一步由用户审查网页；旧库、旧 Parquet、过程候选与原生外部资源的后续清理另行决定。科研模块的 raw／cleaned／curated 和科学规则未因本次网站存储迁移改变。
