# 网站数据包

当前维护入口是 [可搬迁部署计划](../docs/plan/01_preview_optimization/05_portable_deployment.md)；本轮只做本地整理与验证，T7搬迁暂缓。原PostgreSQL已于2026-10-05删除，2026-10-06移除旧导入入口；历史源码见Git基线 `dbb05a1`，旧构建依据见[00数据契约](../docs/archive/00_initial_preview/plan/service_data_storage.md)及[DuckDB迁移记录](../docs/record/01_preview_optimization/duckdb_storage_migration.md)。

本地独立包已在 `data/portable/` 完成：24,690个来源文件、200个有效视图，约312.38 GB；默认运行配置指向此包，23个关键HTTP案例与原实例一致。完整验证及现用8000状态见[交付记录](../docs/record/01_preview_optimization/portable_deployment.md)。

## 运行包与来源

运行包保留现用数据库的实体、关系、字段与来源记录；不重清洗、不合成单张宽表。准备入口只复制已确认文件、重建路径绑定、核对元数据，运行入口只查询该包。科研原始来源的恢复与重新整理属于独立任务。

```text
<数据根目录>/
  package.json                    完成标记、有效视图契约和来源文件清单
  catalog.duckdb                  当前查询目录，部署位置改变后需离线重绑定
  data/<schema>/<table>/         Parquet实体、关系和必要物化投影
  manifest.json                  原结构化快照清单及视图定义
  source-metadata.json           原主外键、排序规则与索引的溯源事实
  source-record-files.json        原记录文件定位；包内相对路径
  catalog_statistics.json        与入库版本对应的已验证展示统计
  alphagenome/
    genes.parquet                基因目录
    protein_gene.parquet         蛋白—基因关系
    tracks.parquet               模态／biosample／assay目录
    windows.parquet              已保存窗口与HDF5相对位置
    manifest.json                当前裁剪与模型来源身份
    assets/tiles/*.h5            原精度、原分辨率裁剪轨道
  structures/
    manifest.parquet             模型身份及相对路径
    .../*.pdb.gz                  原生压缩结构文件
```

`manifest.json`保留原迁移事实，其中旧 `web_alphagenome` 五个目录对象由包内当前裁剪目录替代；判断实际入库必须同时核对有效catalog与该覆盖记录，不能仅用旧清单统计。manifest内历史来源绝对路径用于溯源，不作为运行读取地址。基础视图定义来自冻结manifest，AlphaGenome目录来自已验证的完整gene＋10 kb裁剪快照；两者统一在 [portable.py](../src/database/portable.py) 绑定，不在多个脚本分别维护。

## 粒度与关联

2026-10-06按现用catalog核对：12个schema、200个查询视图；基础快照160个Parquet对象、40个逻辑视图，包含原156张物理表及4个完整物化投影。以下为职责摘要；完整字段、类型与主键以包内清单为准，原关联事实见 `source-metadata.json`。

| schema | 查询对象数 | 粒度与主要关联 |
| --- | ---: | --- |
| web | 58 | 蛋白、序列、注释与来源关系；accession、sequence_id及来源记录键 |
| web_variant | 18 | 变异实体、后果、来源原记录、来源链接与ddG；variant_id、annotation_id、record_id、prediction_id |
| web_context | 51 | 表达测量、QTL关联、互作及背景；来源dataset/record与HGNC身份 |
| web_disease | 33 | 疾病实体、标识、证据与关联；disease_id及来源关系键 |
| web_interface | 14 | 结构／序列残基预测与伙伴方向、证据；各来源自身键，保留映射状态 |
| web_classification | 8 | 已确认疾病类别、上下文与变异关系；分类体系、类别及变异键 |
| web_clinvar_snv | 5 | RCV/SCV条件级记录及成员；保留accession、版本、variation_id与成员序号 |
| web_alphagenome | 5 | gene、protein_gene、track、window和来源manifest；基因身份不替代位点映射 |
| web_paxdb | 3 | 数据集、丰度观察、蛋白映射；dataset_id、source_row、来源蛋白身份 |
| web_avi | 2 | 构建manifest与SNV贡献；variant_id，贡献不重建总分 |
| web_variant_sequence | 2 | 代表序列状态及UniProt精确关系；gene_id及已有序列关联 |
| web_mane | 1 | 每基因MANE结构与状态；gene_id，不重新选择代表 |

未定位来源记录、孤儿状态、关联重数、缺失与真实零均保持。QTL内部 `_source_ctid` 用于相同排序键时维持分页顺序，不增加科学字段。索引作为来源事实保留，不机械移植为Parquet索引；现有查询加速文件定位不改变记录范围。

## 准备与维护

操作命令见[本地部署与开发](../docs/development.md)。离线输入集中于 [packaging.yaml](../config/packaging.yaml)，日常运行由 `MEMVAR_DATA_ROOT` 指定完整包。旧 `data/tables/` 和旧导入报告属于历史构建材料，不是当前运行依赖，也不能单独证明现用入库范围。

`src/build/` 保留科研正式结果到网站表的离线投影代码；部分输入已在10-05清理，本轮未重跑这些构建。后续科学版本更新需按实际依赖更新投影、清单和受影响视图，再生成新包及验证；不能把本轮打包当成raw到入库全流程已修复。
