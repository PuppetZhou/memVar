# AlphaGenome 新数据接入与存储分析

核对：2026-09-29 13:09香港时间。用户本轮要求先分析讨论；未执行正式mapping、数据库迁移、旧文件删除或网站切换。用户明确旧版AlphaGenome参考轨道可以退役，新版作为后续接入目标；Atlas静态评分属于独立产品，不随参考轨道退役。

## 实际状态

| 对象 | 本轮核对 | 含义 |
| --- | --- | --- |
| PostgreSQL | Docker运行中，17.10；`pg_database_size`显示184 GB（二进制单位，约184 GiB）；实际bind mount为`Web/data/postgres` | 数据位于内置NVMe/ext4；该文件系统余量约1.8 TiB |
| Newsmy_6T | 机械盘，Linux挂载为ntfs3，余量约2.9 TiB | 新参考轨道已有固定位置；没有容量理由把活动数据库迁来 |
| 新参考轨道 | 外盘status为complete、7,750窗口；完成清单报告2.586 TB、7,641基因、11模态/1,517 tracks | 原生HDF5已生成，尚未curated发布或Web接入；未重新全读数值 |
| Web参考轨道 | `Web/config/alphagenome.yaml`仍指向旧项目generated目录；API读取旧DuckDB目录与Parquet展示文件 | 新旧文件格式/目录契约不同，不能仅改路径完成替换 |
| Atlas总分 | `web_variant.variant`已有`alphagenome_avi_raw`、`alphagenome_avi_phred`、`alphagenome_splicing`；只读抽查3行有数值 | 既有总分已经入库，不需从归因包重新求总分 |
| AVI归因ZIP | 本地283,875,513,566字节，ZIP目录与TSV头可读；4列变异键＋18列贡献 | 复制状态为verifying（状态文件12:27），13:09服务active/running；不能认定逐字节校验完成 |

来源位置由根`config/sources.yaml`的`alphagenome_reference`、`alphagenome_atlas`、`alphagenome_avi_attributions_collection`维护。参考轨道完成依据见[模块结果](../../../../modules/Alphagenome/docs/result.md)，归因复制动态状态见[status](../../../../runs/t7-local-copy-20260929/status.json)。本轮容量来自df/lsblk及只读SQL；没有扫描大表计数。

## 推荐存储方案（待讨论）

活动PostgreSQL保留NVMe。Newsmy机械盘适合保存本批大型预测文件和备份；现有ntfs3挂载及机械盘随机I/O没有为活动数据库带来优势，且曾出现轨道写入与ZIP复制争用，见模块结果中的IO优化记录。本判断不是声称PostgreSQL技术上绝对不能使用该盘。

源文件与数据库无需在同一磁盘。现有导入脚本读取Parquet后通过`COPY FROM STDIN`传入数据库，数据库文件仍写到自己的存储目录；见[PostgreSQL COPY](https://www.postgresql.org/docs/17/sql-copy.html)。建议的职责如下：

- PostgreSQL：当前SNV评分、18维归因、映射状态，以及参考轨道的基因/窗口/track/文件定位索引。
- 外盘文件：完整原生参考轨道；后续生成经讨论确定的展示文件或按区间读取所需资源。
- Web：参考序列轨道浏览与SNV归因详情分别展示，保留参考背景预测与变异影响的区别。

2.586 TB压缩HDF5不宜逐碱基展开为SQL行；它当前大于内置盘剩余空间，但无需全部搬入数据库才能展示。原生文件保留全部已确认数据。是否生成多尺度展示副本、如何保留峰值/剪接事件、是否支持原生分辨率缩放，需要独立定义，旧版4096 bins和每track最多200 junction的限制不自动沿用。对象存储不能仅通过替换本地路径就直接接入当前HDF5/API，需适配读取或制作展示资源。

## AVI归因mapping与容量

实读ZIP成员`combined_ag_cond_linear_ensemble_20260417_feature_importance_indels_with_am_snvs.tsv.gz`及TBI；成员名不能充当已核实的官方release版本。18列是特征对AVI的贡献，含剪接、染色质、RNA、AlphaMissense、保守性等，不是18个新的独立致病性评分。官方解释见[DeepMind Atlas公告](https://deepmind.google/blog/alphagenome-atlas-a-predictive-map-of-every-possible-dna-letter-change-in-the-human-genome/)。

建议沿用当前10,866,094个唯一variant范围，GRCh38下按chr/pos/ref/alt精确关联，输出独立的`variant_id`＋18列原值及来源/匹配状态的curated表，再生成Web服务表。缺失与零分开，不能保证每个SNV有值；全量覆盖需mapping后实测。字段名称应显式标注贡献，避免将`ALPHAMISSENSE`贡献误读为AlphaMissense原评分。

若全部SNV保留18列float64，纯数值为10,866,094×18×8＝1,564,717,536字节（约1.56 GB），不含主键、行开销、状态、索引、WAL及临时副本；这是容量量级计算，不是实测最终表大小。独立表可避免为新增归因重写整个105 GiB的web_variant schema。若按常规解出内部BGZF/TBI，需要额外约284 GB；无需展开为全量纯文本。现有1.8 TiB余量支持这一方案的进一步实现与测量，不以原包大小作为最终数据库增量。

已有首100个连续源记录与AVI raw的比较发现`raw - sum(18列)`约−0.049，原因未定。见[来源审查](../../../../docs/alphagenome_plm_review.md#avi解释与证据重叠)。可以保留来源原值及版本未定状态；在基线/近似算法/版本对应未解释前，不重算总分、不加校正常数，不制作声称精确还原总分的瀑布图。候选展示为独立标明来源的18特征贡献条形图，已有AVI总分继续独立呈现。

## 上云与下一步

未来分别迁移PostgreSQL和轨道资源。数据库可通过`pg_dump`/`pg_restore`逻辑迁移至云端；这不要求当前先迁到Newsmy，工具也适用于跨机器架构迁移，见[官方pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html)。迁移时另处理角色权限及配置。轨道文件后续选云文件盘或适配后的对象存储；数据库只保存可重新定位的资源标识，不把本地`/media/...`路径作为云端固定契约。

近期顺序（待本轮讨论确定）：

1. 核实既有ZIP校验任务的最终完成状态，确定归因原值/状态契约及贡献解释边界。
2. 在模块内mapping并验证发布curated，再把归因独立服务表导入当前PostgreSQL，接入SNV详情。
3. 将已验收参考轨道登记为正式资源，定义新版索引和读取/展示方式，接入当前蛋白—HGNC关联，保留66个不可预测基因的状态。
4. 新版网站链路通过必要验收后解除旧展示文件依赖，按用户退役要求清理对应旧轨道资源；不误删Atlas评分。
5. 完成数据接入后按实测服务数据规模制定云端迁移方案。

本轮完成标准为给出可核对的容量、数据含义与部署建议。正式接入的完成标准另包括映射键/状态与源值核对、数据库定向查询、新轨道代表窗口和关键页面验收；本轮未启动这些步骤。
