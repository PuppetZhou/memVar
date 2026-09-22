# MEM-01～03：膜主分类第一批交付

日期：2026-09-22。公网ngrok保持暂停；本地服务可用。

## 交付

- 上游正式快照：`modules/membrane/data/curated/20260922_membrane_classification_01/`。
- `protein_membrane_classification.parquet`一蛋白一行，保存互斥主类、父类、TM子类、canonical TM feature数、证据标签和规则版本。
- `protein_membrane_label.parquet`继续保存可重叠的原UniProt证据和适用对象；分类优先级没有删除冲突证据。
- Web服务新增`web.protein_membrane_classification`，数据版本为`20260922_membrane_classification_v1`。首页三大互斥分支、搜索的父/子级筛选、Data overview及蛋白概览均读取该表；旧标签表只作证据展示。

正式计数为7,715个蛋白：整合5,654，其中TM 5,213（single-pass 2,380；multi-pass 2,833）及非TM脂锚441；非整合外周1,015；机制未注释1,046。

## 验证

- 上游：7,715个accession唯一且全覆盖；主类互斥；single+multi=TM；TM+非TM脂锚=整合；三大主分支合计7,715。7,753条旧证据标签完整保留。
- Web Parquet：47张表构建通过，含新分类表；全部现有主键、外键、坐标、来源数量及序列验证通过。
- PostgreSQL：事务式导入47张表，完整导入验收通过；主分类计数与Parquet逐类一致。
- API：`/api/catalog/summary`及7种父/子筛选分别返回5,654、5,213、2,380、2,833、441、1,015、1,046；P00533定向核对为single-pass transmembrane。
- 前端：TypeScript和Vite生产构建通过。Web自动测试39项通过、1项因测试自身要求本地PostgreSQL条件而跳过。

内置浏览器在本轮没有可连接实例，因此没有把真实桌面点击或截图验收标为通过；公网恢复前仍需补桌面浏览器验收。

## 实施中修复

- PostgreSQL大PTM验证曾因容器`/dev/shm`不足触发并行哈希失败；验证会话现固定禁用并行worker，同一10项验证通过，未删减检查。
- schema替换后只读API角色权限和疾病跨schema视图会失效；基础导入脚本现会重授最小只读权限并重建variant、disease投影视图。当前数据库已恢复并由只读API健康检查确认。
- 目录重组后的基线审计路径已改为`record/00_initial_preview/`现存位置。

## 限制

分类对象是当前UniProt2026_03 canonical/条目通用适用证据，不声称描述每个isoform。父类与子类不可相加；预测和结构观察未参与主类判定，也未因本次发布重算。

## 首页图标与层级调整（2026-09-22）

按用户提供的[参考图](../../membrane-protein.png)，首页整合膜入口使用第一行左三的插图；展开后的单次/多次跨膜使用第一行左一/左二，脂锚使用第二行左一，外周使用第二行右二。机制未注释图标由同色系SVG绘制，不暗示特定膜附着方式。前端复用原图的精确视窗，不改动原图；公开素材副本为`frontend/public/images/home/membrane-protein-reference.png`。

首页仍保留三个互斥主分支；点整合膜卡片会原位展开单次跨膜、多次跨膜、非TM脂锚三个下级入口，并提供全部跨膜/全部整合膜检索。脂锚441属于整合膜5,654之内，页面不将父子级计数相加。分类数据、API和上游规则未改。

本轮`tsc -b`与Vite生产构建通过（1710模块）；候选构建已发布至本地`frontend/dist/`。本地8000健康检查返回PostgreSQL只读`ok`，新图像资源与入口JS均返回200，`/api/catalog/summary`仍为7,715及正式分类各计数。浏览器控制发现无可连接实例，因此未将桌面截图、实际展开点击和视觉验收记为通过；未运行全站smoke。
