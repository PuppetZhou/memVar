# 本地部署与开发

本文介绍 memVar 网站源码的安装、运行及服务数据准备。数据库功能介绍见[项目首页](../README.md)。

## 技术栈

| 层次 | 实现 |
| --- | --- |
| 前端 | React 19、TypeScript、Vite、TanStack Query/Table |
| 界面与可视化 | Radix、Motion、Lucide/Tabler、Nightingale、PDBe Molstar |
| API | Python、FastAPI、DuckDB；SQLAlchemy／psycopg 用于旧库对照和只读迁移 |
| 服务数据 | 一致快照中的完整 Parquet、DuckDB 查询目录及原生外部资源 |

## 仓库内容与数据边界

```text
frontend/           前端源码、静态资源和依赖锁文件
src/api/            只读查询 API
src/build/          服务表构建代码
src/database/       DuckDB迁移／重绑定与历史PostgreSQL导入代码
config/             表、来源和部署配置（不含凭据）
tests/              定向验证
docs/               当前方案、研究依据与实现记录
data/README.md      服务数据说明；数据本身不随代码发布
start-local.sh      本地启动入口
requirements-web.txt
```

**仓库不包含科研数据集、数据库文件、凭据、调研导出表、运行缓存和前端构建产物。** 克隆仓库可以安装依赖并构建前端，但完整查询功能需要另行准备服务数据库及结构等资源；不提供模拟数据代替真实结果。

本仓库对应科研工作区中的 `Web/` 子项目，上游 `modules/` 不在本仓库内。部分构建配置、历史文档引用了该工作区的路径；这些引用用于说明来源，独立克隆后不会自动获得上游文件。数据构建前须按实际环境配置输入路径，不能直接照搬维护者的绝对路径。

## 本地运行

建议使用 Node.js 22、Python 3.11+ 和 Linux `en_US.utf8` locale。文本排序兼容 PostgreSQL 基线的 libc 规则，不使用 DuckDB 默认二进制顺序或 ICU 近似替代；部署前用 `locale -a` 确认可用，数据验收记录注明源与服务端 libc 版本。启动脚本从自身目录加载 API，克隆目录可以自行命名：

```bash
git clone https://github.com/PuppetZhou/memVar.git Web
cd Web
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-web.txt
cd frontend
npm ci
npm run build
cd ..
```

准备已经验证的 DuckDB 服务快照及外部资源。`config/duckdb.yaml` 维护默认查询目录，也可通过环境变量指定；相对目录从 `Web/` 解析。启动入口默认选择 DuckDB，运行时不读取 PostgreSQL 凭据：

```bash
# 示例：替换为实际部署文件和资源目录。
export MEMVAR_DUCKDB_PATH='/srv/memvar/snapshot/catalog.duckdb'
export MEMVAR_STRUCTURE_ROOT='/srv/memvar/structures'
export MEMVAR_ALPHAGENOME_REFERENCE_ROOT='/srv/memvar/reference_tracks'
bash start-local.sh
```

默认访问 `http://127.0.0.1:8000`，API 文档位于 `/docs`。启动不会构建、导入数据或创建旧库账号。当前快照已完成迁移与网站验收，现有预览使用新后端，证据与限制见[迁移记录](record/01_preview_optimization/duckdb_storage_migration.md)；快照不存在时，API 返回配置不可用，不使用模拟记录。

原 PostgreSQL 保留供对照，可明确回退：`MEMVAR_QUERY_BACKEND=postgresql bash start-local.sh`。该模式使用既有 `data/.api.env` 或 `MEMVAR_DATABASE_URL` 中的只读连接，不修改角色、权限或索引；不要在迁移过程中运行历史 `--setup-reader` 或导入命令。

默认 DuckDB 查询线程数为 4、共享连接内存限制为 4 GB，可用 `MEMVAR_DUCKDB_THREADS`、`MEMVAR_DUCKDB_MEMORY_LIMIT` 调整。每个请求使用独立 cursor；部署以只读进程运行，更新构建使用独立目录，禁止原地改写正在提供查询的文件。多进程各有资源限制，须按实际部署并发复核。

`config/resources.yaml` 和上述资源环境变量控制结构与统计文件位置；AlphaGenome 配置仍校验参考快照与 checkpoint。DuckDB 默认读取与目录同位置的 `catalog_statistics.json`，可用 `MEMVAR_CATALOG_STATISTICS` 显式覆盖。迁移后将快照搬到另一目录，在本仓库内执行 `python -m src.database.migrate_duckdb catalog /srv/memvar/snapshot` 重绑定 Parquet 路径，该操作不连接原 PostgreSQL。原生结构和 HDF5 内容保持原状，需随部署挂载；对象存储 URL 尚不能直接代替本地文件根目录。

前端开发在另一个终端运行：

```bash
cd Web/frontend
npm run dev
```

默认开发地址为 `http://127.0.0.1:5173`，`/api` 转发到本地 8000 端口。实际端口以 Vite 输出为准。`MEMVAR_HOST`、`MEMVAR_PORT` 可调整后端监听配置。

## 数据维护与验证

完整迁移入口是项目根目录的 `python -m Web.src.database.migrate_duckdb build --workers 3`，使用 `config/database.yaml` 的旧库连接读取一个 `REPEATABLE READ READ ONLY` 逻辑快照；各导出 worker 导入同一快照，保留物理表全部字段、JSON／数组和关联元数据。目标目录必须不存在，候选写完并验证后再发布；具体存储、发布入口及全量验证证据以[迁移计划](plan/01_preview_optimization/04_duckdb_parquet_migration.md)与构建代码为准。

完整快照的 `manifest.json` 管表／字段／文件映射与行数，`source-metadata.json` 管原主外键、索引和排序规则；原索引不机械复制到 Parquet。逻辑视图通过等价定义重建，特殊 JSON 视图保留完整物化结果。QTL 的原 `ctid` 排序以内部 `_source_ctid` 保存，用于保持同排序键记录的分页顺序，不加入科学字段。`source-record-files.json` 仅读取 Parquet footer 建立相对路径定位；可在仓库内用 `python -m src.database.migrate_duckdb record-locator /srv/memvar/snapshot` 重建，不连接 PostgreSQL、不重新筛选原记录。

搬迁或重新生成目录使用离线 `catalog` 子命令；原库内容更新后用新的输出目录构建一致快照并对照验证，避免混入旧版本。当前迁移不改科研模块 raw／cleaned／curated 及其科学构建入口；现有科学服务表投影与旧导入脚本保留作为维护依据，不由日常启动自动调用。源旧库未来是否清理、清理后新科学版本的逐表更新接入，须按届时来源变更明确执行。

日常界面开发无需重跑数据构建。需要重新构建服务表时，先阅读 [数据说明](../data/README.md)、[当前方案入口](plan/README.md) 和 `config/` 中的输入配置，再准备对应上游正式产物。构建脚本还依赖 Polars 等数据处理组件；完整运行依赖随具体模块确认，不将 API 依赖清单视为科研环境的完整锁定文件。

常用前端检查：

```bash
cd frontend
npm run test:genomic
npm run build
```

`test:genomic` 使用 Node.js 22.6+ 的类型剥离执行坐标契约测试，无需数据库；覆盖半开区间、SVG/Canvas 对齐、指针定位和双向刷选。AlphaGenome 前端职责与坐标约定见 [CONTEXT.md](../CONTEXT.md)。

后端定向检查位于 `tests/`；部分检查需要本地数据库或上游数据，纯代码构建通过不代表完整数据链路已验证。修改影响科学含义的筛选、映射或阈值时，应先确认数据规则，再修改实现。

在 `Web` 的父目录运行基因轨道的后端回归检查：`python -m unittest Web.tests.test_avi Web.tests.test_alphagenome_expression Web.tests.test_qtl_significance Web.tests.test_qtl_tracks`。这些检查需要已安装的服务数据库和参考预测文件，包含来源数值、身份关联、区间边界及分页。

## AlphaGenome与AVI服务数据

AlphaGenome运行时从当前查询引擎读取gene/window/track目录，从配置指定的文件系统读取原生HDF5区间。`config/alphagenome.yaml`中的`reference_root`须指向已验收的预测快照；`source_run_id`和`checkpoint_revision`必须与快照manifest一致。科学目录投影来源由`catalog_path`指定；网站运行不回读科研模块。读取依赖h5py和NumPy，已列入`requirements-web.txt`。

下列 PostgreSQL 导入是旧服务基线的构建方法，迁移和普通启动均不执行；DuckDB 快照已经包含相同目录、AVI 与 MANE 结构化内容。

在`Web`的父目录执行参考目录导入（需要配置本地数据库管理员连接）：

```bash
python -m Web.src.database.import_alphagenome_reference
```

AVI总分沿用`web_variant`现有列。18列特征贡献独立于总分，由`config/avi.yaml`指定正式科研输入和Web服务目录；2026-09-30已从`20260930_avi_attribution_01`完成以下构建/导入，全部10,866,094行可用（后续重建仍须绑定已发布科研快照）：

```bash
python -m Web.src.build.build_avi
python -m Web.src.database.import_avi
```

归因导入使用独立`web_avi`schema，检查主键、行数、当前variant关联和样本原值后在事务内替换；失败回滚。尚无贡献库时已有AVI总分和参考轨道仍可查询，详情返回不可用状态。定向检查为`python -m unittest Web.tests.test_alphagenome_expression Web.tests.test_avi -v`；真实参考测试需要现有服务数据库和预测文件。

迁云需同时准备完整快照和HDF5资源，并按实际挂载位置调整配置。当前后端使用本地文件随机读取；对象存储URL不能直接替换`reference_root`，需要另行适配。已有本地部署和归因接入证据见[交付记录](record/01_preview_optimization/20260929_alphagenome_avi.md)。


### MANE Select CDS服务模型

配置 `config/mane_cds.yaml` 绑定已发布科研快照和服务目录。科研入口为项目根 `python run.py foundation build_mane_cds`（已交付快照不重复覆盖）；Web投影与入库从科研工作区根执行：

```bash
python -m Web.src.database.import_mane_cds
```

该历史命令将正式Parquet复制到Web服务目录，按HGNC组装模型并事务导入 `web_mane.gene_cds`，不在Web重选代表或处理新的CDS规则。运行时API `/api/proteins/{accession}/expression/alphagenome/cds?gene=ENSG...` 查询当前引擎中完整保留的模型，校验当前蛋白的真实gene关联；提供完整版本ENST、来源状态、0-based half-open CDS/stop_codon片段。当前模型快照 `20260930_mane_cds_01`。旧基线核对证据见 `data/postgresql_mane_cds_import.json` 与 `data/mane_cds_live_validation.json`；部署快照须包含 `web_mane` schema。
