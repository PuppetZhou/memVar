# ClinVar 疾病分类入库与页面接入

2026-09-29。用户授权将已确认Q7分类入库，并用于Variant Catalog的ClinVar展开详情及Diseases的ClinVar展开区。已完成独立服务表构建、PostgreSQL发布、API、页面与定向验证；本地8000服务已更新，公网/用户端转发未在本轮处理。

## 数据与规则

沿用科研工作区`manuscript/analysis/rule/q7_multiaxis_mapping.md`，不重算分类、不筛临床意义、不利用名称/同基因/RCV推断MONDO。输入由[配置](../../../config/classification.yaml)引用科研来源配置`analysis_q7_multiaxis_v1`；快照和上游验证记录进入服务manifest及数据库。MONDO为2026-09-01，KEGG为2026-09-28收集、源更新2026/09/25。

网站服务目录`data/tables/classification/`约8.5 MiB，全部7表已导入`web_classification`：

| 表 | 行数 | 粒度/用途 |
| --- | ---: | --- |
| context_classification_mapping | 33,417 | 对象×体系×层级×类别，含空类别与证据JSON；完整保留四体系 |
| variant_mondo | 760,105 | 当前summary的唯一变异—MONDO对 |
| classification_categories | 97 | 体系×层级×类别字典 |
| disease_location_paths | 11,933 | 疾病定位与继承路径 |
| mondo_kegg_reference_links | 4,432 | MONDO至KEGG参考链接证据 |
| kegg_disease_entries | 3,107 | KEGG条目原始分类与参考 |
| source_tissue_links | 480 | 已确认跨来源组织关系；本轮页面不使用 |

导入报告：`data/postgresql_classification_import.json`。桥表与**当前数据库**ClinVar summary直接MONDO双向比较，缺失0、多余0；无主表对象的MONDO关系0。导入检查全部行数、主键及含NULL的分类自然键唯一性，暂存schema验证后事务切换，失败不覆盖当前schema。只读API账号已授予SELECT权限。

## 页面与统计口径

- Variant Catalog → ClinVar：新增Disease types，按该条来源记录的原始summary MONDO显示身体系统、病因机制、KEGG项目17类。多个MONDO分别列出；未提供MONDO、未分类、服务未加载明确区分。保留原临床意义与条件标识，疾病类别不证明变异致病。
- Diseases → ClinVar：三组横向条形图，按该蛋白现有ClinVar查询范围（基因关联的当前SNV）计算`COUNT(DISTINCT variant_id)`。分母为全部此范围SNV，不随下方条件搜索变化。类别可重叠，同类多疾病只计一次，各体系分别计算；展示无MONDO和有MONDO但该体系未命中的数量。
- 身体系统保留综合征，注明非解剖类别；病因机制不表示LOF/GOF或遗传方式。KEGG明确为参考支持关系、不是疾病身份等价。页面KEGG英文为原项目中文类别的显示译名，API/数据库保留原标签及ID。
- 分类API运行只读PostgreSQL，不回读上游科研Parquet。接口：`GET /api/proteins/{accession}/diseases/clinvar-classification`；原`/api/variants/{variant_id}`的ClinVar source增加`disease_classification`。

## 复现与迁移

完整科研工作区内，从Web目录运行：

```bash
python src/build/build_classification.py
python src/database/import_classification.py
```

云端只需携带本服务表目录（包括manifest）、现有基础/variant服务数据库及网站代码，即可执行导入；不要求携带analysis原始文件。也可随完整PostgreSQL逻辑备份一并恢复`web_classification`，恢复后保证API只读角色有USAGE/SELECT权限。只在重新生成服务表时需要上游Q7文件。

## 验证

- 5项定向测试通过：严格MONDO token、按source记录隔离、EGFR分布对照发布Parquet独立集合统计、空范围、HTTP契约/非法蛋白。
- EGFR：2,977个SNV；1,948带MONDO、1,029无MONDO。身体系统命中1,925、病因机制1,947、KEGG优化类93。类别间确有重叠，未使用饼图或归一化互斥分布。
- 本地首次分布函数调用约1.56秒；TypeScript/Vite构建通过，真实浏览器完成ClinVar来源弹窗标签及Disease展开区三图检查。
- 截图：`output/playwright/clinvar-classification-20260929/distribution.png`、`variant-types.png`。未把局部检查视为全站或用户视觉验收。

测试入口（科研工作区根目录）：`MEMVAR_LIVE_TESTS=1 python -m unittest Web.tests.test_disease_classification -v`。独立克隆不设置该变量时运行纯身份规则测试；实时对照测试需要当前数据库及科研发布Parquet。
