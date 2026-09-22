# memVar

**Human membrane protein variants** — 面向人类膜蛋白的序列、结构、变异与多来源证据浏览平台。

本仓库维护 memVar 网站的前端、只读 API、服务表构建与数据库导入代码、设计文档和必要静态素材。2026-09-22 用户确认的当前网站版本为 GitHub 发布基线，后续版本在此基础上持续提交。

## 功能

- 蛋白检索与膜分类浏览，基本身份、膜特征、功能、细胞定位、GO 与 Reactome 通路。
- 蛋白序列注释轨道、残基与片段选择，以及联动的三维结构浏览。
- 变异目录、来源证据、群体频率、预测评分和 ClinVar 分类。
- 组织表达、QTL 关联与组织导航；区分来源显著性判据和手动输入的 P 值参考阈值。
- AlphaGenome 预测信号、蛋白互作、疾病与表型证据。

界面区分来源事实与计算预测、未提供信息与真实零，以及基因关联与经验证的蛋白位点映射。当前主要验收桌面端；移动端完整适配仍待后续工作。

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

日常界面开发无需重跑数据构建。需要重新构建服务表时，先阅读 [数据说明](data/README.md)、[当前方案入口](docs/plan/README.md) 和 `config/` 中的输入配置，再准备对应上游正式产物。构建脚本还依赖 Polars 等数据处理组件；完整运行依赖随具体模块确认，不将 API 依赖清单视为科研环境的完整锁定文件。

常用前端检查：

```bash
cd frontend
npm run build
```

后端定向检查位于 `tests/`；部分检查需要本地数据库或上游数据，纯代码构建通过不代表完整数据链路已验证。修改影响科学含义的筛选、映射或阈值时，应先确认数据规则，再修改实现。

## 文档与版本维护

- [文档索引](docs/README.md)
- [当前优化计划](docs/plan/01_preview_optimization/README.md)
- [当前实现与验证记录](docs/record/01_preview_optimization/20260922_ui_toolkit.md)
- [工作约定](AGENTS.md)

`main` 为发布代码主线。后续修改从当前基线创建提交，记录变更及相关验证；较大改动可使用功能分支。首次发布前的在途开发历史仅在维护者本地保留，不随首次发布上传。不要提交 `data/` 内的数据与环境文件、`.venv/`、`node_modules/`、`dist/` 或运行输出，也不要使用 `git push --all` 发布本地历史备份分支。

本仓库暂未声明统一开源许可证。第三方库及图片仍适用各自许可证，已有素材来源和署名应保留；代码发布不改变原始科研数据的使用条款。
