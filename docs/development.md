# 本地部署与开发

本文介绍 memVar 网站源码的安装、运行及服务数据准备。数据库功能介绍见[项目首页](../README.md)。

## 技术栈

| 层次 | 实现 |
| --- | --- |
| 前端 | React 19、TypeScript、Vite、TanStack Query/Table |
| 界面与可视化 | Radix、Motion、Lucide/Tabler、Nightingale、PDBe Molstar |
| API | Python、FastAPI、SQLAlchemy、psycopg |
| 服务数据 | PostgreSQL；Parquet 服务表与来源配置 |

## 仓库内容与数据边界

```text
frontend/           前端源码、静态资源和依赖锁文件
src/api/            只读查询 API
src/build/          服务表构建代码
src/database/       PostgreSQL 导入与验证代码
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

建议使用 Node.js 22、Python 3.11+；当前数据库部署配置为 PostgreSQL 17。现有启动脚本按 `Web` 包路径启动 API，因此克隆目录使用 `Web`：

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

随后配置一个已导入 memVar 服务表的 PostgreSQL 数据库。API 使用只读账号，可通过环境变量提供连接信息：

```bash
# 替换为本地连接信息；不要将真实凭据写入提交。
export MEMVAR_DATABASE_URL='postgresql+psycopg://READ_ONLY_USER:PASSWORD@127.0.0.1:55432/memvar_web'
bash start-local.sh
```

默认访问 `http://127.0.0.1:8000`，API 文档位于 `/docs`。启动不会自动构建或导入科学数据。已有维护环境也可以使用忽略规则排除的 `data/.api.env`；自动创建只读账号需要现有数据库和本地管理员配置。

前端开发在另一个终端运行：

```bash
cd Web/frontend
npm run dev
```

默认开发地址为 `http://127.0.0.1:5173`，`/api` 转发到本地 8000 端口。实际端口以 Vite 输出为准。`MEMVAR_HOST`、`MEMVAR_PORT` 可调整后端监听配置。

## 数据维护与验证

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

AlphaGenome运行时从PostgreSQL读取gene/window/track目录，从配置指定的文件系统读取原生HDF5区间。`config/alphagenome.yaml`中的`reference_root`须指向已验收的预测快照；`source_run_id`和`checkpoint_revision`必须与库内manifest一致。目录导入来源由`catalog_path`指定，当前来源为科研模块正式Parquet；网站运行不回读该Parquet路径。读取依赖h5py和NumPy，已列入`requirements-web.txt`。

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

迁云需同时准备数据库和HDF5资源，并按实际挂载位置调整配置。当前后端使用本地文件随机读取；对象存储URL不能直接替换`reference_root`，需要另行适配。已有本地部署和归因接入证据见[交付记录](record/01_preview_optimization/20260929_alphagenome_avi.md)。


### MANE Select CDS服务模型

配置 `config/mane_cds.yaml` 绑定已发布科研快照和服务目录。科研入口为项目根 `python run.py foundation build_mane_cds`（已交付快照不重复覆盖）；Web投影与入库从科研工作区根执行：

```bash
python -m Web.src.database.import_mane_cds
```

该命令将正式Parquet复制到Web服务目录，按HGNC组装模型并事务导入 `web_mane.gene_cds`，不在Web重选代表或处理新的CDS规则。运行时API `/api/proteins/{accession}/expression/alphagenome/cds?gene=ENSG...` 仅查询PostgreSQL，校验当前蛋白的真实gene关联；提供完整版本ENST、来源状态、0-based half-open CDS/stop_codon片段。当前模型快照 `20260930_mane_cds_01`。导入及真实API核对证据见 `data/postgresql_mane_cds_import.json` 与 `data/mane_cds_live_validation.json`；云端迁移需包含 `web_mane` schema。
