<p align="center">
  <img src="frontend/src/assets/memvar-logo.png" alt="memVar" width="240" />
</p>

# memVar · Human membrane protein variants

**面向人类膜蛋白的变异与多来源证据数据库。**

memVar 将膜蛋白的序列、膜拓扑、三维结构、遗传变异和生物学背景组织到统一的蛋白页面中。研究者可以从基因或蛋白出发，定位感兴趣的变异，结合功能位点、组织表达、调控关联及疾病证据理解其背景，并追溯原始数据来源。

## 在 memVar 中可以探索什么？

| 内容 | 主要功能 |
| --- | --- |
| 蛋白概览 | 查看蛋白身份、膜分类、功能注释、细胞定位、GO 与 Reactome 通路 |
| 膜特征 | 浏览跨膜区段、拓扑注释、结构中的膜接触观察及 DeepTMHMM2 预测 |
| 序列与结构 | 在对齐的序列轨道中查看结构域、功能位点、翻译后修饰和保守性，并结合三维结构浏览残基；可按独立预测器的位点极值着色 |
| 变异目录 | 检索与筛选变异，查看变异后果、来源记录、群体频率、ClinVar 分类及可选预测评分 |
| 表达与丰度 | 按 RNA 或蛋白测量浏览组织、细胞及肿瘤背景；PaxDB 保留原始 ppm 丰度，并将组织与细胞分开呈现 |
| 调控与预测 | 独立选择GTEx组织添加QTL关联轨道；先选biosample再选模态，将AlphaGenome参考预测、QTL与项目SNV的AVI分数放在共享基因组轴上比较，结合MANE Select外显子、CDS与UTR定位，并可叠加同模态信号 |
| 互作与疾病 | 查看蛋白互作、基因—疾病关系、表型及来源证据 |

## 从蛋白到证据

1. **查找蛋白**：通过基因名称、蛋白名称或 UniProt ID 搜索，例如 EGFR / P00533。
2. **了解背景**：在概览中查看膜特征、分子功能和细胞定位。
3. **定位变异**：结合序列轨道、三维结构和变异目录，检查位点及其注释。
4. **追溯证据**：展开来源记录，查看表达、疾病或预测结果的具体背景，并访问原始数据库。

## 多来源数据，保留各自含义

memVar 汇集 UniProt、GO、Reactome、Pfam、ClinVar、gnomAD、dbSNP、COSMIC、GTEx、Human Protein Atlas、PaxDB 等来源的相关信息。不同模块按适用对象组织记录，不同蛋白的覆盖范围可能不同。

- **来源可追溯**：保留来源名称、记录标识及适用的原始链接，支持查看具体证据。
- **注释与预测分开**：实验观察、来源注释和计算预测分别展示；不同预测工具保留各自的量纲与方向。
- **关联层次明确**：区分基因关联、蛋白身份关联和经过核对的序列位点映射。
- **保留测量背景**：组织、细胞、测量类型与数据集共同限定数值含义，缺失信息不作为零值。

## 关于本仓库

本仓库提供 memVar 网站的前端、DuckDB只读查询、网站数据包准备与离线数据投影代码。前端使用 React 和 TypeScript，查询使用 FastAPI。2026-10-06 已完成[本地架构与独立数据包整理](docs/plan/01_preview_optimization/05_portable_deployment.md)：运行只依赖网站代码、完整数据包和统一环境，数据包保留Parquet实体／关系、AlphaGenome原生HDF5与结构文件；本轮暂不进行T7搬迁或搬迁试运行。旧PostgreSQL已于10-05删除，对应运行和导入入口已退役；科学字段、关联与现有页面保持。实际验证与限制见[本地整理记录](docs/record/01_preview_optimization/portable_deployment.md)，此前迁移依据见[DuckDB验收记录](docs/record/01_preview_optimization/duckdb_storage_migration.md)。

- [本地部署与开发](docs/development.md)
- [服务数据说明](data/README.md)
- [技术文档索引](docs/README.md)
- [AlphaGenome 完整 gene＋10 kb 裁剪来源与进度](docs/record/01_preview_optimization/alphagenome_reference_crop.md)

科研数据集、数据库文件及访问凭据不随源码发布；完整运行需要准备相应服务数据。仓库目前未声明统一开源许可证，第三方代码、素材及原始数据仍适用各自的许可和使用条款。
