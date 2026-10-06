# 网站架构与独立数据包整理

更新：2026-10-06。本地整理与验收已完成；用户随后授权的T7搬迁与相对路径验收已完成。现用8000保持原位。范围与授权见[计划](../../plan/01_preview_optimization/05_portable_deployment.md)。

## 基线与职责

代码基线 `dbb05a1` 已推送 `PuppetZhou/memVar` 的main，包含10-04已交付的预测器改动、10-05来源位置调整及本轮原计划。主代理统筹，三名GPT-6 sol子代理分别审查/实现运行、数据包、环境与验收。

核对现用 `config/duckdb.yaml` 指向的 `snapshot-20260930T160803Z/catalog.alphagenome-gene10k.duckdb`：12个schema、200个视图；原结构化清单160个Parquet对象与40个逻辑视图，8053个Parquet文件。来源snapshot ID为 `0000001F-0000081E-1`。实际AlphaGenome目录已由 `20261001_reference_crop_01` 覆盖，模型来源为 `20260928_reference_local_01`；原manifest中的旧五个目录对象仅作为历史来源事实保留。结构源为Site-Region所存AlphaFold v6模型。

8000的23个真实HTTP案例已保存于 `data/portable-validation/baseline.json`：22个200响应与一个预期422越界响应；覆盖搜索/分页、蛋白概况、序列、变异筛选与详情、预测极值、QTL及cursor、疾病、表达、真实结构和RNA/contact轨道。未覆盖每个蛋白和每种组合，不宣称全量页面/科学重新验收。

## 实现

- 运行集中于 `src/runtime.py` 与DuckDB只读查询。移除PostgreSQL选择、SQLAlchemy engine、管理员账号准备和对应业务分支；保留SQL AST转换、libc排序、float4表达、JSON/数组处理、原CTID分页语义。
- `src/database/portable.py`统一复制清单、基本视图与当前AlphaGenome覆盖目录、包完成校验和离线重绑定。普通启动不读取 `config/packaging.yaml` 或科研来源。包目录见[数据说明](../../../data/README.md)。
- 删除退役PG导入、专用校验和旧分散目录入口；当前视图定义由冻结manifest与裁剪目录共同维护。旧代码可从Git基线追溯，科研数据、原来源文件及当前服务不删除。
- 历史统计构建移至 `src/build/catalog_statistics.py`，明确其离线输入需求。当前运行直接读取冻结统计，不把科研重建隐入启动。
- Python 3.12与Node 22环境明确，运行／离线构建／测试清单分开，并锁定依赖；`prepare-local.sh`准备环境和独立前端产物，`start-local.sh`统一检查与启动。前端产品代码和页面交互没有修改。
- 本轮检查发现AlphaGenome历史测试仍请求完整模型窗口；测试改为使用catalog返回的保留区间，保留原生HDF5值验证与422边界检查。未扩大轨道保存范围。

## 交付与验证（2026-10-06 11:46，Asia/Shanghai）

完整本地包位于 `Web/data/portable/`，包含24,690个来源文件，312,382,067,942字节（约312.38 GB，另有新catalog及package元数据）。其中8053个源Parquet、7750个裁剪HDF5、结构manifest及8837个模型文件；最终200个有效视图、所有文件存在/大小及AlphaGenome身份/字段/计数核对通过。`package.json`记录完成状态、准备时间、来源代码版本、准备代码基线和dirty状态、来源位置、每视图字段/类型/粒度主键及文件清单；后续实际提交以本记录所在Git版本追溯。

| 核对 | 结果与证据 |
| --- | --- |
| 环境 | 独立Python 3.12.3环境安装、`pip check`及fresh `npm ci`通过；Node 22.23.1 |
| 前端 | 独立 `dist-portable` 构建与6项坐标测试通过，旧 `dist`未替换 |
| 后端 | 默认独立包下51项定向测试通过，涵盖运行配置、DuckDB SQL、统计、AlphaGenome原生轨道、QTL、分页与预测选择；包/数值另3项通过 |
| 包完成验收 | `data/portable-validation/package-finalize.json`；200视图与24,690来源文件通过 |
| HTTP等价 | `data/portable-validation/portable-8001.json`：23/23一致，完整状态、字段、数值及顺序零差异；使用新启动入口及默认数据包 |
| 文件读取 | `data/portable-validation/runtime-path-audit.json`：记录4392个包内路径；三条结构/RNA/contact真实资源请求单独跟踪，未观察到科研modules、旧snapshot或旧项目路径读取 |
| 浏览器 | 首页→EGFR搜索→蛋白页→Variants/Structure导航正常，3D模型实际显示；控制台0 error，4条浏览器警告。截图在 `output/playwright/portable-*.png` |

首次将系统调用跟踪与并发HTTP对比一起运行明显拖慢请求，该次主动停止，未记作通过。随后不带跟踪的响应比较23/23通过，再单独跟踪三条原生资源请求，避免把测量开销混入响应验收。观察到的模型与轨道路径分别为包内 `structures/P00533/AF-P00533-F1-model_v6.pdb.gz`、`alphagenome/assets/tiles/HGNC_3236_tile000.h5`。

默认 `config/duckdb.yaml` 已改为 `data_root: data/portable`；新启动只读此包。验收8001进程结束后停止，原8000进程保持，仍运行原先已加载代码和来源；配置更新不等于已切换该进程。新旧包具有同一确认的数据范围，今后启动采用独立包。全部运行报告/数据/截图均被Git忽略，只发布代码及说明。

## 限制与后续

不改变科学收录、主键/关联、精度、原生格式和可视化。保留完整裁剪HDF5和原生结构，未重跑科研流程，未计算SHA-256。本地阶段未触碰T7；用户后续授权的T7搬迁状态见下节。未启动云端发布、安全升级或网站润色。全量科学raw到入库更新仍需按后续来源与依赖独立推进。

## T7搬迁与路径验收（2026-10-06，已通过）

目标 `/media/xuyzh/T7_PuppetZ/memVar-website`，T7挂载为exFAT，已有原始数据保留。运行代码从版本 `4bb5c40` 独立克隆（不共享Git对象）；数据复制至新临时目录后就位，未使用镜像删除。前端使用该代码版本此前已通过构建的 `dist-portable`，运行环境按T7仓库依赖清单重新安装。复制总量312,385,392,790字节，包括原24,690个来源文件及catalog/package元数据。

Python 3.12.3环境独立安装于 `/home/xuyzh/.local/share/memvar/venvs/t7`，由 `MEMVAR_PYTHON` 选择；该目录只承载运行依赖，网站代码、前端和完整数据均位于T7。exFAT不适合承载依赖符号链接的虚拟环境；换主机须重新准备运行环境，不能把已安装的Linux环境当作跨系统可执行包。

| 验收 | 结果／证据（相对T7仓库） |
| --- | --- |
| 完整复制 | `data/t7-validation/copy-verification.json`：24,690个来源文件名称及字节大小全匹配，无缺失或额外数据文件 |
| 旧路径保护 | `before-rebind.json`：复制来的旧catalog因Parquet绑定在本机而被明确拒绝启动 |
| 离线重绑定 | `after-rebind.json`：200个有效视图、159个Parquet绑定均指向T7包；重绑定及默认配置检查通过 |
| 相对路径 | 从 `/tmp` 调用T7的启动脚本，显式使用 `MEMVAR_DATA_ROOT=data/portable`、`MEMVAR_FRONTEND_DIST=frontend/dist-portable`；进程工作目录及源码均在T7，见 `launch.json` |
| 带空格路径与数值 | T7带空格临时目录下4项定向测试通过：包路径、移动重绑定、float精度/有符号零、NULL/数组/JSON |
| 接口等价 | `http-comparison.json`：23/23通过；完整HTTP状态、字段、数值与顺序一致。单次观察最长约4.19秒，不作为跨磁盘性能基准 |
| 实际资产读取 | `path-audit.json`、`assets-openat.log`：实际PDB、RNA及contact轨道请求均读取T7；没有观察到本机Web、科研modules或旧项目文件读取 |
| 前端 | 首页HTTP字节与T7的index.html完全一致；浏览器首页→EGFR搜索→蛋白页及结构导航正常，控制台0 error；浏览器证据与截图保存在T7忽略目录 |

首次采用短命后台启动未保持服务运行，连接失败的尝试保留于 `before-server-ready.json`，未计作接口通过。改用受管理的试运行进程并确认监听后，完整23例比较通过。没有为通过测试放宽数值或删除字段，也未修改运行科学规则。

本轮未发现需要修改运行源码的路径缺陷；按现有入口重绑定即可正确搬迁。包内相对文件位置和运行根目录可调整，但DuckDB物理视图仍在部署准备时绑定实际绝对路径，**更换挂载点或包位置后必须离线重新绑定**。元数据内的历史来源路径继续作为事实保留。

T7试运行地址为 `http://127.0.0.1:8001`，进程PID记于 `.runtime/t7-api.pid`；这是本地试运行，不是开机自启或云端部署。原8000实例、原本机包、科研文件及T7已有原始文件均保留，未切换公网入口。启动方式见[开发说明](../../development.md#t7--exfat试运行)。复制日志位于本机 `Web/data/t7-validation/copy.log`，其余主要证据集中于T7 `data/t7-validation/`；均不上传Git。
