# AlphaGenome 新数据接入与存储分析

2026-10-01当前状态：已按[DuckDB＋Parquet后端迁移计划](../../plan/01_preview_optimization/04_duckdb_parquet_migration.md)完成迁移、网站验收及现有预览切换，保留全部数据、关联和前端行为，原PostgreSQL保持不动；AlphaGenome大型资源未优化。当前证据维护于[迁移记录](../../record/01_preview_optimization/duckdb_storage_migration.md)。下述初次讨论保留为历史依据，旧PostgreSQL部署与AlphaGenome重压缩建议不作为当前迁移要求。

随后用户要求先分析 AlphaGenome 预测文件的体积与压缩空间。该独立只读分析和局部无损小试已完成，主要结论与证据维护于 [Alphagenome 压缩分析](../../../../modules/Alphagenome/docs/storage_compression_review.md)；未重写正式 HDF5，不改变现用网站资源。

初次核对：2026-09-29 13:09香港时间。以下容量与进程状态保留该核对时点。用户随后授权AVI mapping入库、新版轨道/AVI后端前端接入，并要求依据已有官网调研先设计；当前状态见[执行计划](../../plan/01_preview_optimization/README.md)与[共轴轨道设计](../../plan/01_preview_optimization/alphagenome_atlas.md)，本页不再构成“仅讨论”限制。用户明确旧版参考轨道可退役；Atlas静态评分属于独立产品，不随参考轨道退役。

## 2026-09-30：Newsmy统一打包与上云再讨论（尚未执行）

用户希望把数据库备份与Newsmy6T上的AlphaGenome一起组织，后续传至云端；本轮授权为可行性讨论，未启动dump、文件复制、数据库迁盘或云端上传。

本次只读核对：PostgreSQL容器17.10，`memvar_web`的`pg_database_size`为200,435,496,627字节（200.4GB / 186.7GiB），活动目录仍为NVMe上的`Web/data/postgres`。`web_avi`为2,667,388,928字节（含表/索引/manifest），`web_alphagenome`为6,856,704字节，`web_mane`为8,724,480字节。Newsmy6T仍为机械盘/ntfs3，df余量约2.9TiB；内置ext4余量约1.5TiB。HDF5总量采用已有[完成验收](../../../../modules/Alphagenome/docs/result.md)的2,585,607,525,831字节，本轮没有重扫全部数值。

当前API已统一关联PostgreSQL目录与HDF5区间数据，AVI总分及18项贡献已在库内。建议候选方案为**统一迁移清单与后端交付包**：

- 在Newsmy保存PostgreSQL逻辑备份，优先目录格式`pg_dump -Fd`，云端用`pg_restore`恢复；另外准备角色/权限重建说明、扩展与运行配置。备份可在活动库继续位于NVMe时生成，不要求先迁动PGDATA。压缩备份大小须实际导出后测量，不能以数据库物理大小作为承诺。
- 已在Newsmy的完整AlphaGenome快照直接纳入迁移清单，保留tiles及metadata关系，避免再造一份TB级副本。现有相对资源路径与`MEMVAR_ALPHAGENOME_REFERENCE_ROOT`允许云端重新指定文件根目录；同时保留source_run_id/checkpoint一致性验证。
- 一并列出网站运行依赖的结构模型/manifest、API代码、前端构建及配置。特别是`src/api/structures.py`仍读取科研配置指定的本地PDB gzip与Parquet清单，需要部署化处理；仅迁PostgreSQL与AlphaGenome仍不等于全站运行依赖已齐。
- 云端为PostgreSQL配置数据库磁盘，为HDF5准备后端可按区间读取的文件系统。当前代码不能直接将对象存储URL作为HDF5根目录。总体组织为一套网站后端，不要求每种数值都存为SQL行或数据库blob。

不建议为了传输方便将2.586TB完整HDF5改存PostgreSQL：逐碱基/track展开可能显著放大规模，具体倍数未测试；作为二进制分块保存也需重写区间读取与备份方式。科学值不必改动，但目前没有必要承担此重构。现有约0.200TB数据库与2.586TB轨道的合计约2.786TB仅是两个主要运行数据量的量级，未计其他资源、恢复临时空间与WAL，也不是最终压缩上传量。

普通文件打包不能直接用于正在写入的PGDATA。逻辑备份和恢复规则依据[PostgreSQL 17 pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html)、[SQL dump](https://www.postgresql.org/docs/17/backup-dump.html)及[文件系统备份](https://www.postgresql.org/docs/17/backup-file.html)。最终迁移包需以独立恢复和代表页面/接口核对作为可交付依据。

待后续执行前明确的部署信息：云端为自建还是托管PostgreSQL、目标版本、文件盘容量与传输带宽。本轮建议不改变此前已采用的活动库NVMe/原生轨道外盘架构。

## 2026-09-30：数据库减容审查（建议，尚未实施）

本次只读存储审查提供容量与查询依赖证据，当时未执行重写、删表／删索引、导出或迁移。后续用户确认并授权DuckDB＋Parquet路线，见[正式迁移计划](../../plan/01_preview_optimization/04_duckdb_parquet_migration.md)；该计划替代全量PostgreSQL入库的技术要求，审查时的实际运行基线为PostgreSQL。以下未采用的候选仅作比较依据，最新交付见上方迁移记录。

核对时间为2026-09-30 19:32:23北京时间。实际容器为PostgreSQL 17.10，挂载仍为`Web/data/postgres`；FastAPI通过SQLAlchemy只读连接池查询数据库，React/TypeScript前端经API取数据。新版AlphaGenome由PostgreSQL提供目录、h5py按区间读取外部HDF5。结构文件同样由独立文件接口提供。维护入口分别为`config/database.yaml`、`src/api/db.py`、`src/api/alphagenome.py`与`src/api/structures.py`。

容量来自只读事务内的`pg_database_size`、`pg_table_size`、`pg_relation_size`及`pg_indexes_size`，Parquet来自文件长度与一份来源表footer；没有全表扫描或重新核对科学数值。GB为十进制。数据库为200,435,783,347字节（200.44 GB / 186.67 GiB），业务schema共156张物理表（含manifest表）、44个普通视图、233个索引，登记118个外键约束。行数如引用`reltuples`应视为统计估计，不能替代精确计数。

| 对象 | PostgreSQL含索引GB | 对应当前服务Parquet GB | 判断 |
| --- | ---: | ---: | --- |
| web_variant全部 | 112.256 | 14.836 | 主减容对象，保留原范围与字段 |
| web_context全部 | 65.439 | 6.788 | QTL及表达大表适合进一步研究列式存储 |
| web_variant.variant_source_record | 71.036 | 11.876 | `details_json`为JSONB；TOAST及辅助文件约58.818 GB，完整来源详情值得优先研究 |
| web_context.qtlbase_association | 23.094 | 1.548 | 大量重复文本标识和来源坐标文本；不能未经解析验证改变其含义 |
| web_context.gtex_qtl_pair | 15.362 | 1.209 | 保留测量、组织、来源与基因关联；列式候选 |

业务表索引合计23.084 GB，约为数据库大小的11.52%；即便优化索引也不能解决全部体积差异。当前WAL文件合计1.040 GB，位于数据库大小口径外；本次未测量全部PGDATA目录、备份或历史产物占用。来源Parquet抽查为ZSTD，列式跨记录压缩与PostgreSQL行式、TOAST、索引的存储方式不同，不能据上述差异认定数据库损坏或承诺同等在线减容比例。

初次比较的备选（当前执行方向以正式迁移计划为准）：

1. **仅减传输量**：压缩逻辑备份保留表、关系约束、视图与索引定义，云端恢复时重建索引；角色及外部资源单列。上传量和恢复后运行占用分别测量。尚未生成备份，不能承诺压缩比例。
2. **维持PostgreSQL架构**：优先小规模试验来源JSONB与保留查询列后的文本/压缩载荷存法；抽取确实共用的描述/数据集维表；长文本内部关联键可研究整数代理键，同时保留原ID及唯一约束。基础导入器`src/database/import_tables.py:sqltype`将整数/浮点统一拓宽为bigint/double precision，可按来源类型及范围研究无损类型映射；context/interface已有不同类型策略，不能全库机械改写。索引依据真实筛选、连接、排序和约束需求审查。普通视图不保存查询结果，本次没有业务物化视图，删普通视图不是减容方向。
3. **需要明显降低在线占用时**：候选为PostgreSQL保留实体、来源记录登记、桥表、查询列与资源目录，独立Web服务Parquet保留完整来源详情，API按稳定`record_id`及快照目录取回。QTL/表达大表可在后续比较按基因/来源组织的Parquet＋DuckDB查询。独立服务文件必须随网站部署，不在运行时回读科研模块；不可只保留本地绝对路径或依赖全文件扫描来完成记录详情查找。

第三项需保留数据库内记录登记及外键，文件中的ID、版本与分区定位由构建检查确保一致；跨文件关系无法由普通PostgreSQL外键直接强制。`src/api/variant_support.py`当前用JSONB提取ClinVar分类、review/origin和dbNSFP来源评分，疾病与summary接口也有依赖。因此外置前必须完整盘点查询字段，保留等价投影/获取路径，不得只删除`details_json`或把评分分类改成另一来源值。QTL关系属于各自来源及坐标版本，不可为节省空间强行转成当前项目SNV外键。

后续用户明确：目标是降低PostgreSQL与AlphaGenome合计的后端数据包容量，最终与前后端代码一并部署云端；保留当前数据库的全部记录、字段及关系，未在前端展示的列同样保留，前端内容不增删。这替代本节初次建议中以上传量和在线占用分开选方向的讨论重点；压缩备份仍是迁移工具，不能作为最终数据包减容的主要答案。当前PostgreSQL逻辑内容应作为后续迁移验收基线，现有Parquet不能未经逐表对应就被认定涵盖全部数据库字段。

用户已确定使用DuckDB＋Parquet完成后端减容与重构。后续agent逐表决定外部Parquet、DuckDB原生表及视图／查询结构，不预先规定关系表必须入库；生产迁移尚未执行。Parquet须承接当前PostgreSQL完整逻辑内容，不回退到raw、不重做科学筛选、不删未展示列。原生表与Parquet保存同一完整内容会产生副本；仅注册外部视图不复制完整数据，外部表也可以JOIN。阶段、边界与验收统一由正式迁移计划维护。

PostgreSQL＋Parquet FDW属于初次比较的备选，不是当前执行方向。读取旧库可用于迁移，但不等于减少旧库物理存储。原PostgreSQL只读保留、不修改；前后端适配与检查完成后再由用户决定是否删除旧数据，验证通过不自动授权清理。

蛋白—gene—序列—site可通过现有稳定ID、版本与JOIN表达，关系不要求全部落成独立link表；已有有含义的桥表及映射状态仍保留。无需为了压缩将所有表实际合成宽表；一对多/多对多展开可能重复数值或放大行数。分区、排序和row group围绕实际gene/variant/sequence/site查询设计，保持同序列位点、来源坐标和未匹配状态的原契约。API适配须验证现有筛选、分页、排序、计数、来源JSON、数组和返回类型，不能只替换驱动。

本次文件长度核对：`Web/data/tables`227份Parquet共15,804,097,633字节，`context_tables`34份共6,787,680,498字节，`disease_tables`20份共18,459,063字节，三处合计22.610 GB。此数未包括从科研模块直接导入的全部界面预测文件、数据库内新构建关系/JSON模型、最终索引/布局及结构资产；不能承诺完整新后端仅22.610 GB，也不执行数据删除。

两项主要数据200.44 GB＋2.586 TB合计约2.786 TB，PostgreSQL占7.19%、AlphaGenome占92.81%。即使假设前者减少180 GB，总量也仅减少约6.46%。这是本轮后端减容的容量边界，不能承诺整个包降至非TB量级；用户已明确AlphaGenome大型数据暂不优化。

AlphaGenome保存规则为gzip1/shuffle与主要float16，有限值超范围的窗口／模态保留模型原生dtype。只读抽查`HGNC_3236_tile000.h5`（318,095,029字节）的RNA／ATAC／CHIP_TF／contact数组确认gzip1、shuffle与float16；本次仅打开metadata，未全读数值或重压缩。此前比较gzip4/9与chunk布局的建议已暂缓，本轮不改原生资源、精度或窗口组织。

本次审查提出按正式迁移计划盘点完整数据库、关系与API依赖，再判断逐表存储方式及查询适配；该后续迁移已于2026-10-01完成，不开展AlphaGenome重压缩，未进行云端上传。最终部署文件与资源根目录可重新定位，现有HDF5读取仍不能仅把根目录替换为对象存储URL。

原理与迁移依据：[PostgreSQL页与行布局](https://www.postgresql.org/docs/17/storage-page-layout.html)、[容量函数](https://www.postgresql.org/docs/17/functions-admin.html)、[数值类型](https://www.postgresql.org/docs/17/datatype-numeric.html)、[JSON类型](https://www.postgresql.org/docs/17/datatype-json.html)、[普通视图](https://www.postgresql.org/docs/17/sql-createview.html)、[pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html)、[DuckDB Parquet读取与投影/过滤下推](https://duckdb.org/docs/current/data/parquet/overview)。Parquet只保存列与键值，不提供文件间外键约束；DuckDB适合本项目分析候选，但不能未经真实分页/并发验证就当作PostgreSQL在线替代品。

本次补充依据：[PostgreSQL物理文件](https://www.postgresql.org/docs/17/storage-file-layout.html)、[DuckDB PostgreSQL扩展](https://duckdb.org/docs/current/core_extensions/postgres/overview)、[DuckDB只读并发](https://duckdb.org/docs/current/connect/concurrency)、[h5py无损压缩与chunk](https://docs.h5py.org/en/stable/high/dataset.html)。AlphaGenome现行dtype与范围契约由[模块规则](../../../../modules/Alphagenome/docs/rules.md#新版参考轨道已确认部分2026-09-28)维护，不因Web存储讨论自动改写。

### 外部/原生查询及大型生物数据库公开实践（2026-09-30）

外部Parquet与原生DuckDB表都由同一个DuckDB执行SQL、筛选和JOIN，二者都按需读取，不是外部每次必须全读或原生一次全装RAM。外部仅指数据在`.duckdb`以外，可与API位于同一云盘；Parquet通过列投影、分区和row group统计减少扫描，通常没有原生表的持久ART索引。原生表有更丰富的优化器统计，可建立约束和索引，但持久保存全部导入记录；索引不会自动加速所有JOIN。仅把关系表放入原生库不保证关联的外部明细可快速定位。跨外部Parquet的键与关系由构建检查维护，不能宣称原生外键自动覆盖外部视图。依据：[格式/统计/查询比较](https://duckdb.org/docs/current/guides/performance/file_formats)、[索引适用范围](https://duckdb.org/docs/current/guides/performance/indexing)、[原生约束](https://duckdb.org/docs/current/sql/constraints)。

先前实测`variant_source_link`有25,494,421条发布记录，Parquet合计164,517,993字节，PostgreSQL含索引6,693,445,632字节（数据库行数当次为统计估计）。这说明短字段关系表也可能拥有大量行，不以“关系表”推定“小表”或承诺DuckDB原生表大小；可先保留Parquet，并以真实ID查询/分页决定是否物化必要查询列。轻量候选包括蛋白—HGNC、序列身份、来源字典/目录；关系规则和未匹配状态均保留。

以下是截至本次检索可核对的公开实现，不视为生产环境全部最新细节或统一行业规范：

| 资源 | 证据范围与实现 | 对本项目的意义 |
| --- | --- | --- |
| Ensembl | [官方API文档](https://mart.ensembl.org/info/docs/api/general_instructions.html)说明通过MySQL关系库及API访问；不采用写于2013年的硬件机器数量作当前部署证据 | 基因/序列身份与关系可由关系数据库承载；不能据文件下载格式推断网站后端 |
| UniProt | [团队2025年API论文](https://academic.oup.com/nar/article/53/W1/W547/8126256)描述Solr检索返回ID，再从Voldemort获取完整条目 | 查询入口与完整内容可分别优化；本文不是证明UniProt采用Parquet/DuckDB |
| gnomAD主浏览器公开代码 | [数据管线](https://github.com/broadinstitute/gnomad-browser/blob/main/data-pipeline/README.md)使用Hail；[GraphQL依赖](https://github.com/broadinstitute/gnomad-browser/blob/main/graphql-api/package.json)含Elasticsearch客户端，Lite说明将Elasticsearch列为gnomAD生产风格基线 | 科研处理与网站查询实现分工；代码证据不保证线上所有服务保持同一部署细节 |
| gnomAD Browser Lite | [Broad公开项目README](https://github.com/broadinstitute/gnomad-browser-lite)明确支持DuckDB直接查询本地Parquet，`xpos`物理列用于区域/点查询裁剪；文档将Hail/DuckDB定位于本地开发，其他引擎含基准用途 | 是压缩文件服务基因/区域/变异查询的可行实现参考，不能将Lite等同主站或宣称已获其生产并发验证 |

项目判断：借鉴按查询用途拆分入口、完整内容与多维信号的组织，暂不引入大型搜索集群。推荐先比较蛋白检索、变异筛选/详情与QTL分页在Parquet/原生布局下的响应、峰值资源和数据包大小，再确定哪些表需物化；不以别人的架构替代本项目性能验收。AlphaGenome大型资源减容暂不开展。

## 初次核对状态（2026-09-29）

| 对象 | 本轮核对 | 含义 |
| --- | --- | --- |
| PostgreSQL | Docker运行中，17.10；`pg_database_size`显示184 GB（二进制单位，约184 GiB）；实际bind mount为`Web/data/postgres` | 数据位于内置NVMe/ext4；该文件系统余量约1.8 TiB |
| Newsmy_6T | 机械盘，Linux挂载为ntfs3，余量约2.9 TiB | 新参考轨道已有固定位置；没有容量理由把活动数据库迁来 |
| 新参考轨道 | 外盘status为complete、7,750窗口；完成清单报告2.586 TB、7,641基因、11模态/1,517 tracks | 原生HDF5已生成，尚未curated发布或Web接入；未重新全读数值 |
| Web参考轨道 | `Web/config/alphagenome.yaml`仍指向旧项目generated目录；API读取旧DuckDB目录与Parquet展示文件 | 新旧文件格式/目录契约不同，不能仅改路径完成替换 |
| Atlas总分 | `web_variant.variant`已有`alphagenome_avi_raw`、`alphagenome_avi_phred`、`alphagenome_splicing`；只读抽查3行有数值 | 既有总分已经入库，不需从归因包重新求总分 |
| AVI归因ZIP | 本地283,875,513,566字节，ZIP目录与TSV头可读；4列变异键＋18列贡献 | 复制状态为verifying（状态文件12:27），13:09服务active/running；不能认定逐字节校验完成 |

来源位置由根`config/sources.yaml`的`alphagenome_reference`、`alphagenome_atlas`、`alphagenome_avi_attributions_collection`维护。参考轨道完成依据见[模块结果](../../../../modules/Alphagenome/docs/result.md)，归因复制动态状态见[status](../../../../runs/t7-local-copy-20260929/status.json)。本轮容量来自df/lsblk及只读SQL；没有扫描大表计数。

## 新版接入时采用的存储方案（迁移前运行基线）

以下记录新版接入时的实际部署；后续迁移目标与原库保留边界以[正式迁移计划](../../plan/01_preview_optimization/04_duckdb_parquet_migration.md)为准，不将此处PostgreSQL职责作为继续入库的要求。

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

## 新版接入时的上云与下一步讨论（历史）

以下为接入阶段的讨论及执行顺序，当前后端减容方向以正式迁移计划为准，实际接入进度见交付记录。

未来分别迁移PostgreSQL和轨道资源。数据库可通过`pg_dump`/`pg_restore`逻辑迁移至云端；这不要求当前先迁到Newsmy，工具也适用于跨机器架构迁移，见[官方pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html)。迁移时另处理角色权限及配置。轨道文件后续选云文件盘或适配后的对象存储；数据库只保存可重新定位的资源标识，不把本地`/media/...`路径作为云端固定契约。

后续已授权的执行顺序（当前进度由执行计划维护）：

1. 核实既有ZIP校验任务的最终完成状态，确定归因原值/状态契约及贡献解释边界。
2. 在模块内mapping并验证发布curated，再把归因独立服务表导入当前PostgreSQL，接入SNV详情。
3. 将已验收参考轨道登记为正式资源，定义新版索引和读取/展示方式，接入当前蛋白—HGNC关联，保留66个不可预测基因的状态。
4. 新版网站链路通过必要验收后解除旧展示文件依赖，按用户退役要求清理对应旧轨道资源；不误删Atlas评分。
5. 完成数据接入后按实测服务数据规模制定云端迁移方案。

初次分析以可核对的容量、数据含义与部署建议交付。随后正式接入已获授权，其完成标准包括映射键/状态与源值核对、数据库定向查询、新轨道代表窗口和关键页面验收；不可用初次分析状态代替当前执行状态。
