# 本地PostgreSQL服务库

> 00阶段方案基线，2026-09-22归档。保留原方案与当时状态；适用范围、01阶段修订及未替代契约见[现行方案索引](../../../plan/README.md)。旧阶段授权/待执行文字不作为当前指令。

2026-09-20用户明确授权：OPM/MPLID/BioDolphin完成mapping、DeepTMHMM2接入，先保存cleaned，再接入Web，完成后导入PostgreSQL。该授权已完成上一轮33表导入。2026-09-20用户重新审核Basic info，2026-09-21用户已明确授权按当前计划优化并更新数据库，本版执行与最终验证见[版本记录](../../../record/00_initial_preview/20260921_basic_info_v2.md)，不再等待重复确认。

## 本地部署

连接配置唯一维护于[database.yaml](../../../../config/database.yaml)。使用本地已有`postgres:17-bookworm`镜像，项目独立容器`memvar-re-web-postgres`，仅绑定`127.0.0.1:55432`；数据库`memvar_web`，业务schema为`web`。数据目录`Web/data/postgres`。不修改旧项目数据库容器或数据。

随机凭据在首次启动时写入`Web/data/.postgres.env`，权限0600；不写入文档或提交。只在本机连接，不对外开放。

```bash
# Web目录：启动并导入当前全部服务表
python src/database/import_tables.py
# 仅启动
python src/database/import_tables.py --start-only
# 本机容器内连接，无需在命令中写密码
docker exec -it memvar-re-web-postgres psql -U memvar -d memvar_web
```

## 类型、索引与替换

一张Parquet对应一张业务表；冗余属性和统一外链使用普通视图即时关联，不另存关系副本。视图定义由`src/database/service_views.py`维护。整数使用bigint，浮点使用double precision，布尔使用boolean，列表/结构及明确JSON字段使用jsonb，其余使用text；来源复杂列名保留并使用SQL标识符引用。NULL通过COPY显式保留，不转换为0或空字符串。

导入到新临时schema，逐表流式COPY，建立主键、蛋白/序列及位点查询索引，核对全部行数和标量外键，并执行ANALYZE。OPM和接触位点有`mapping_status=mapped`的部分索引，查询必须带状态条件；未匹配行中的候选坐标不能用于显示。

验证完成后在单个事务中将临时schema切换为web，并删除旧服务schema。导入或约束失败只清理本次临时schema，旧web保持可用。schema切换本身由PostgreSQL事务保证回滚；旧数据不作为历史版本保留。

另有一张`web._build_manifest`元数据表，记录对应Parquet构建时间和包含data_version的清单，不计入业务表数量。当前业务表数、行数、数据库大小及导入状态由[data/postgresql_import.json](../../../../data/postgresql_import.json)维护；查询验证另见[data/postgresql_validation.json](../../../../data/postgresql_validation.json)。

重建Parquet后不会自动改变数据库。导入报告的input_built_at必须与当前Parquet manifest的built_at一致，才能认为数据库与本地表同步。API和页面仍未实现，不将本地SQL验证宣称为网站已部署。

## Sequence版本（2026-09-21）

用户后续授权已执行，当前为`20260921_sequence_v1`，46张业务表、10个普通视图。新表、复用关系、输入及验证见[版本记录](../../../record/00_initial_preview/20260921_sequence_v1.md)。导入时额外在临时schema验证canonical、残基、PTM端点及证据恢复、Pfam零命中和JSD覆盖，通过后才切换。

## 疾病独立schema（2026-09-21）

`20260921_disease_v1`已导入同一memvar_web数据库的web_disease，20张业务表、12个普通视图；使用独立临时schema验证及事务切换，不替换web/web_context。详情见[疾病表契约](disease_tables.md)及[验收](../../../record/00_initial_preview/20260921_disease_v1.md)。共享身份视图依赖web.protein_gene，后续基础schema替换须维护依赖。

## Variant独立增量导入（2026-09-21）

`web_variant`已导入并验证，版本20260921_variant_v1；11张业务表、6个普通视图。共用同一数据库，通过web.protein_gene与canonical序列连接基础表，独立构建清单与报告避免覆盖其他板块状态。[交付记录](../../../record/00_initial_preview/20260921_variant_v1.md)维护字段、精度处理、查询与存储实测。
