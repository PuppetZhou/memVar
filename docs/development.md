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
npm run build
```

后端定向检查位于 `tests/`；部分检查需要本地数据库或上游数据，纯代码构建通过不代表完整数据链路已验证。修改影响科学含义的筛选、映射或阈值时，应先确认数据规则，再修改实现。

