# 网站领域词汇

用于定位网站 Module 的职责；科研规则仍由上游负责模块维护，当前网站范围见 [README](README.md)。

- **Protein（蛋白条目）**：以 UniProt accession 定位的页面对象；页面下的基因关联不等于 isoform 位点匹配。
- **Gene context（基因上下文）**：当前蛋白关联的 HGNC / Ensembl gene 身份，用于限定 MANE、参考预测、AVI 与 QTL 查询。
- **Genomic viewport（基因组视窗）**：内部采用 0-based half-open 区间，面向用户的坐标采用 1-based；轨道共享横轴，保留各自纵轴和记录粒度。
- **MANE transcript structure（MANE 转录本结构）**：来源 MANE Select 转录本的 exon、CDS、UTR 和 stop codon 区段，保留来源链方向与坐标。
- **Reference track（参考预测轨道）**：AlphaGenome 对参考序列的预测，限定模型窗口、biosample、模态及具体 assay/strand；不是某个 SNV 的效应分数。
- **AVI record（AVI 记录）**：项目 SNV 对应的来源总分及特征贡献；同坐标不同等位基因保持独立，不以贡献和重建总分。
- **GTEx QTL track（GTEx QTL 轨道）**：指定基因、组织和 QTL 类型的来源关联记录；独立于 AlphaGenome biosample 选择，保留 phenotype、原始 P 值和效应，不按 AVI 或 CDS 匹配过滤。
- **Scientific color（科研语义色）**：表达来源分类、分数方向或类别的颜色，与按钮、背景等 UI 状态色分开维护。
