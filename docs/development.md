# 本地部署与开发

更新：2026-10-06。本轮本地代码与数据包整理及独立验收已完成；用户随后授权的T7搬迁验收也已完成；云端发布及现用8000切换未执行。实际结果见[本地整理记录](record/01_preview_optimization/portable_deployment.md)。

## 职责与环境

| 位置 | 职责 |
| --- | --- |
| `src/runtime.py` | 统一数据根目录、资源位置与启动检查 |
| `src/api/` | DuckDB只读查询；保留JSON、float4与排序兼容处理 |
| `src/database/portable.py` | 从确认来源准备完整包、离线重绑定视图 |
| `src/build/` | 科研正式结果到网站表的离线投影；日常部署和启动不调用 |
| `config/packaging.yaml` | 本机已确认的离线打包输入；可能含科研来源路径 |
| `config/duckdb.yaml` | 默认网站包位置；环境变量 `MEMVAR_DATA_ROOT` 可覆盖 |
| `frontend/` | React/TypeScript前端；`package-lock.json`锁定依赖 |
| `tests/portable_acceptance.py` | 保存与比较有界HTTP响应基线 |

使用Python 3.12和Node.js 22（见 `.python-version`、`.nvmrc`）。`requirements-web.txt`列运行依赖，`requirements-lock.txt`锁定依赖版本；离线投影另用 `requirements-build.txt`，测试另用 `requirements-test.txt`。运行环境不需要PostgreSQL、SQLAlchemy或psycopg。

Linux须具备 `en_US.utf8` locale；当前文本排序使用libc兼容现有基线，不用二进制顺序替代。不同系统的libc版本仍需在后续实际部署时核对。本轮没有重写排序规则，也没有重新锁定上游科研计算环境。

## 准备代码与环境

仓库可独立克隆，不要求文件夹名为 `Web`；服务数据另行提供，不随Git发布。

```bash
git clone https://github.com/PuppetZhou/memVar.git
cd memVar
bash prepare-local.sh
```

准备脚本创建仓库内 `.venv`，安装运行依赖并用 `npm ci` 构建前端至 `frontend/dist-portable`。本轮验证保留旧 `frontend/dist`；新启动入口默认读取独立构建产物。可用 `--python /path/to/python3.12` 选择创建环境的解释器；已有有效前端依赖时用 `--skip-npm-install`，只准备Python环境时用 `--skip-frontend`。

## 网站数据包

包内布局、粒度及关联见[数据说明](../data/README.md)。已有完整网站包时，无需读取科研目录；首次从本机确认来源组装包时，检查 `config/packaging.yaml`：

```bash
.venv/bin/python -m src.database.portable plan
.venv/bin/python -m src.database.portable build --output /absolute/new/data-package
```

`plan`核对文件存在、来源身份和容量；`build`只复制清单文件，保留字节内容及科学字段。输出目录必须全新，复制使用旁边的 `.building` 目录，目录就位后才生成绑定最终路径的catalog，验收完成后写入包清单。失败不覆盖现用数据；未完成目录留供诊断，不作为可用包。原来源和溯源绝对路径不全局替换。

也可合并环境准备与打包：`bash prepare-local.sh --data-output /absolute/new/data-package`。该命令会复制完整网站资产，运行前先确认 `plan` 输出；本次约312.38 GB。已有包不能作为新构建输出覆盖。

后续真正改变数据包位置时，在新位置、所有读进程启动前执行：

```bash
.venv/bin/python -m src.database.portable rebind --output /absolute/moved/data-package --replace-offline
```

重绑定只重建DuckDB目录，不重写Parquet、HDF5或结构。不带 `--replace-offline` 时创建 `catalog.rebound.duckdb` 供检查，保留原catalog。当前包内历史 `manifest.json`记录原快照，`package.json`记录200个实际有效视图及AlphaGenome覆盖目录；普通启动不自动重绑定。

## 只读启动

```bash
export MEMVAR_DATA_ROOT=/absolute/data-package
bash start-local.sh
```

默认访问 `http://127.0.0.1:8000`，接口文档 `/docs`。本机并行检验请指定 `MEMVAR_PORT=8001`，不重启或占用现用8000。脚本优先用仓库 `.venv/bin/python`，可由 `MEMVAR_PYTHON`覆盖。`MEMVAR_HOST`、`MEMVAR_PORT`和 `MEMVAR_FRONTEND_DIST`控制监听及前端位置。

数据包缺失或不完整时启动检查失败，不自动回读科研目录或旧库。DuckDB保持只读，每个请求使用独立cursor；默认4线程、4GB内存，可由 `MEMVAR_DUCKDB_THREADS`、`MEMVAR_DUCKDB_MEMORY_LIMIT`调整。多进程资源按实际部署并发重新评估。

前端开发另开终端执行 `cd frontend && npm run dev`，Vite默认在5173，`/api`转发本地8000。前端界面及数据科学规则本轮不调整。

## 验收

在替换当前运行来源前保存有界真实响应：

```bash
.venv/bin/python tests/portable_acceptance.py capture \
  --source-url http://127.0.0.1:8000 \
  --baseline data/portable-validation/baseline.json
.venv/bin/python tests/portable_acceptance.py compare \
  --candidate-url http://127.0.0.1:8001 \
  --baseline data/portable-validation/baseline.json \
  --report data/portable-validation/comparison.json
```

比较完整HTTP状态、字段、类型、值和数组顺序，含真实结构文件、RNA/contact轨道及越界响应；不把容差或删除字段当作“等价”。已有基线默认拒绝覆盖，只有明确重新采集时才用 `--replace`。这组有界案例用于本轮变更，不替代所有蛋白与全部科学记录的验证。

前端检查为 `npm run test:genomic` 和 `npm run build -- --outDir dist-portable`。后端测试依赖用 `.venv/bin/python -m pip install -r requirements-test.txt` 安装。部分历史测试依赖科研工作区，本轮可独立运行的配置/打包测试从仓库根执行 `.venv/bin/python -m unittest discover -s tests -p 'test_runtime.py'` 和 `.venv/bin/python -m unittest discover -s tests -p 'test_portable_package.py'`；实际验证范围以交付记录为准。

## 后续数据更新

`src/build/`保留既有投影和科学处理依据，输入路径由各主题配置维护。部分上游文件已在10-05清理；本轮未重跑或修复raw到网站全流程。更新来源或规则须从负责科研模块确认结果，再按依赖更新网站表、清单、相关视图与统计，形成新包并对照验收。

旧PostgreSQL导入、管理员账号创建及迁移命令已退役，不能按历史文档直接运行；历史源码可从Git基线 `dbb05a1` 查阅。`src/build/catalog_statistics.py`保留原统计构建依据，需要匹配的历史报告和科研manifest；网站部署直接使用已验证统计文件，不调用它。AlphaGenome的模型身份、完整gene＋10 kb保存范围、AVI总分与贡献区别，以及MANE代表选择保持原规则。

## T7 / exFAT试运行

本机T7位置为 `/media/xuyzh/T7_PuppetZ/memVar-website`。exFAT不适合承载依赖符号链接的虚拟环境；本次在主机独立环境目录安装Python依赖，网站代码、已构建前端和完整数据包仍全部从T7读取。该环境不是本机科研或Web目录的环境副本；依赖由T7源码仓库中的锁定清单重新安装。换主机后须在新主机重新准备环境。

```bash
python3.12 -m venv "$HOME/.local/share/memvar/venvs/t7"
"$HOME/.local/share/memvar/venvs/t7/bin/python" -m pip install \
  -r /media/xuyzh/T7_PuppetZ/memVar-website/requirements-web.txt
cd /tmp
MEMVAR_PYTHON="$HOME/.local/share/memvar/venvs/t7/bin/python" \
MEMVAR_DATA_ROOT=data/portable \
MEMVAR_FRONTEND_DIST=frontend/dist-portable \
MEMVAR_PORT=8001 \
bash /media/xuyzh/T7_PuppetZ/memVar-website/start-local.sh
```

相对数据和前端目录从源码仓库根解析；启动脚本先定位自身位置，不依赖调用时的工作目录。使用默认 `config/duckdb.yaml` 时可省略 `MEMVAR_DATA_ROOT`。数据库物理视图在部署准备时绑定实际绝对根目录，因此复制后仍须先执行 `portable rebind --replace-offline`；元数据中的历史来源路径不应全局替换。实际T7结果由[交付记录](record/01_preview_optimization/portable_deployment.md)维护。
