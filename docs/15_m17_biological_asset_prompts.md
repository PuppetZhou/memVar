# 15. M17 生物学图标与科研插画素材需求

状态：等待生成与交付  
用途：为 memVar SCI 配套数据库生成统一风格的生物学专用 SVG icon / illustration  
注意：通用 Search、Download、External link、Copy、Filter、Zoom、Reset、Fullscreen 等界面图标不在本文件生成，后续直接采用 [Lucide](https://lucide.dev/icons/)。

## 1. 全套统一母提示词

以下母提示词应附加到每一项素材提示词前：

> 为面向生命科学研究者的膜蛋白数据库 memVar 设计一套统一的科研矢量图标。风格为现代 scientific editorial、简洁扁平、轻微双色填充、圆润但专业的 outline，不写实、不拟物、不使用 3D 渲染。使用一致的 2px 圆角描边、清楚的负空间和几何比例，在 24px 小尺寸仍可辨认。主描边使用深 navy `#0F172A`；主要强调色使用 indigo `#4F46E5`、cyan `#0891B2`、teal `#0F766E`；辅助强调仅使用 amber `#D97706`、coral `#E05F5F` 和 violet `#7C3AED`。每个图标最多使用 2 个强调色，不使用大面积渐变、荧光色、黑色厚块或复杂阴影。背景透明，不包含文字、数字、logo、水印、坐标轴或品牌标识。构图居中，四周保留约 10% 安全留白。生物学结构应准确但采用 schematic 表达，不暗示临床结论、致病性、证据强弱或跨数据库综合评分。

## 2. 统一交付规格

每个 icon 请交付：

- 原生 SVG，固定 `viewBox="0 0 64 64"`；
- 透明背景 PNG：256×256 与 512×512；
- 彩色版和单色版各一份；
- SVG 不嵌入位图、字体、外部 URL、脚本或滤镜；
- path 尽量精简，stroke-linecap / stroke-linejoin 使用 round；
- 不把文字转换为 path，因为本套素材禁止文字；
- 文件名使用下表建议的 kebab-case；
- 同一套图标的 stroke、圆角、留白、观察角度和配色严格一致。

建议目录：

```text
frontend/public/assets/scientific-icons/
├── membrane-protein.svg
├── sequence-site.svg
├── disulfide-bond.svg
├── stability-ddg.svg
├── protein-variant.svg
├── gene-ontology.svg
├── tissue-expression.svg
├── regulatory-qtl.svg
├── protein-interaction.svg
├── disease-evidence.svg
├── alphagenome-regulation.svg
└── protein-structure-ribbon.svg
```

## 3. 核心生物学 icon 提示词

### 3.1 Membrane protein

文件名：`membrane-protein.svg`

> 绘制一个跨膜蛋白 schematic icon：两排简化的磷脂头部和短尾形成水平脂质双层，一条具有 3 个圆润 alpha-helical 跨膜段的蛋白穿过膜层，并在膜外有一个小型结构域。蛋白使用 indigo/cyan，膜层使用浅 teal。突出“protein-centric membrane database”，不要画细胞、受体配体、信号箭头或文字。

### 3.2 Canonical sequence and selected site

文件名：`sequence-site.svg`

> 绘制一条简化的 canonical amino-acid sequence ribbon，由连续小圆角单元构成；其中一个 residue 使用 coral 定位环和短垂直指针突出，旁边有一个很小的 coordinate tick。表达“序列上的精确 1-based site”，不要出现氨基酸字母、数字或 DNA 双螺旋。

### 3.3 Disulfide bond / covalent pair

文件名：`disulfide-bond.svg`

> 绘制两个 cysteine side-chain 的极简化学 schematic，由两个 sulfur 节点通过一条清楚的 S—S 双端连接形成 disulfide bond。两个 endpoint 使用同一种 coral 强调色，连接线使用 amber；外侧以简化 peptide ribbon 接入。重点表达“两个配对端点和明确的二硫键类型”，不要写 Cys、S、化学式、位置数字或使用泛化链条 icon。

### 3.4 Thermodynamic stability ΔΔG

文件名：`stability-ddg.svg`

> 绘制一个蛋白 ribbon 与中心平衡基线：左侧蓝色柔和向下波形表示 predicted stabilizing，右侧 coral 向上波形表示 predicted destabilizing，中间为 slate neutral band。图标只表达蛋白热力学稳定性变化，不出现火焰、盾牌、健康/疾病符号、药物或文字。

### 3.5 Protein variant

文件名：`protein-variant.svg`

> 绘制一个短 protein sequence ribbon，其中一个 residue 单元发生替换：原单元以细虚线轮廓表示，新单元以 coral 实心小菱形或圆角块突出，并带一个小型 directional swap cue。表达 amino-acid substitution，不使用 DNA 双螺旋作为主体，不出现致病、警告或临床十字符号。

### 3.6 Gene Ontology annotation

文件名：`gene-ontology.svg`

> 绘制一个小型三分支 ontology graph：中心 protein node 连接三个不同形状的节点组，分别暗示 molecular function、biological process、cellular component。节点使用 indigo、teal、violet，连接关系清楚、对称。不要写 GO、MF、BP、CC 或任何术语，不要表现统计富集或显著性。

### 3.7 Tissue expression

文件名：`tissue-expression.svg`

> 绘制一个简化器官轮廓与三条独立的表达 signal bars；三条 signal 具有不同长度但不共享总分，旁边保留小型 molecule dots。使用 teal/cyan，强调“组织表达与独立 modality”。不要使用完整人体、热图坐标、排行榜、上/下调箭头或文字。

### 3.8 Regulatory QTL

文件名：`regulatory-qtl.svg`

> 绘制一个 genomic locus 点通过弧形连接到 gene transcription start 区域，下方有一条轻量 regulatory signal curve。variant locus 使用 violet，gene region 使用 cyan，连接弧使用 indigo。表达 locus–gene regulatory association，不表现因果确认、疾病风险或单一 genome build，不写 SNP、QTL、基因名称或坐标。

### 3.9 Protein interaction

文件名：`protein-interaction.svg`

> 绘制两个形状不同的 protein ribbon nodes，通过一个明确的 evidence link 相连，外围有两个小型 source-record markers。使用 teal 与 amber，表达 protein interaction evidence/context membership。不要画社交网络头像、握手、链条、细胞或暗示一定存在直接物理结合。

### 3.10 Disease evidence

文件名：`disease-evidence.svg`

> 绘制一个 protein node 连接到两个彼此独立的 evidence document cards，每张卡具有不同的边框形状和小型 phenotype dots，表达“多个来源各自提供 gene–disease evidence”。使用 indigo、coral 与 muted amber。不要使用红十字、诊断锤、患者人物、危险三角、投票条、星级或统一可信度分数。

### 3.11 AlphaGenome regulatory landscape

文件名：`alphagenome-regulation.svg`

> 绘制一个 reference genome window，包含多条平行的一维 regulatory tracks、一个 splice arc 和一个很小的 contact-map grid。使用 indigo/cyan/violet 的有限双色组合，所有轨道共享横向 genomic axis 但保持独立尺度。表达 reference-sequence model prediction，不出现 REF/ALT 对比、变异效应箭头、AI 大脑、芯片或文字。

### 3.12 Protein structure ribbon

文件名：`protein-structure-ribbon.svg`

> 绘制一个非写实的 protein cartoon ribbon icon：一段圆润 alpha helix、一段 beta arrow 和一个 connecting loop，具有清楚 outline 和轻微双色层次。使用 indigo/cyan，整体像科学期刊中的结构 schematic。不要使用 ball-and-stick、molecular surface、真实 PDB 细节、原子字母或文字。

## 4. Anatomy navigator 底图需求

这不是 64×64 icon，而是独立科研插画资产。若计划替换当前 BioRender preview，请使用以下提示词：

文件名建议：`human-anatomy-front.svg`

> 为科研数据库的交互式 Anatomy navigator 绘制一张正面、站立、中性人体解剖示意图。画面必须严格正面、左右对称、从头顶到脚完整可见，人体占画布高度约 90%，四周留白均匀。清楚但克制地显示 brain、thyroid、lungs、heart、liver、stomach、spleen、pancreas、kidneys、colon、small intestine、bladder，以及女性或性别中性的主要生殖器官；皮肤、骨骼肌、脂肪、骨与骨髓可通过浅色局部区域表达。整体为扁平 scientific editorial vector，不写实、不血腥、不使用照片质感。器官之间轮廓清楚，颜色低饱和，人体外轮廓使用浅 slate，器官使用统一的 muted teal/coral/amber/violet palette。背景透明，不包含标签、引线、数字、点位、logo 或水印。所有器官位置必须符合基本人体解剖比例，适合后续在图上叠加可点击圆点。

交付额外要求：

- SVG viewBox 固定且记录原始宽高；建议 `0 0 1000 1800`；
- 人体在 viewBox 中不可被裁切；
- 同时提供一张带 landmark 编号的校准预览 PNG，但正式 SVG 不包含编号；
- 提供每个器官大致中心点的原始 SVG 坐标表；
- 不改变人物姿态生成多个不一致版本；
- 明确素材许可允许 SCI 配套网站公开展示与长期托管。

## 5. 可选的小型状态素材

仅当核心 12 个 icon 风格稳定后再生成：

### 5.1 Observed phenotype

文件名：`phenotype-observed.svg`

> 一个 phenotype node 与实心 evidence dot 连接，使用 teal；只表达 observed，不使用 checkmark 作为医学确认。

### 5.2 Explicitly absent phenotype

文件名：`phenotype-absent.svg`

> 与 observed icon 使用完全相同的 phenotype node，但 evidence dot 为空心并有一条细斜杠，使用 slate/coral；表达 source 中明确的 NOT/absent，不表示数据缺失。

### 5.3 Predicted evidence

文件名：`evidence-predicted.svg`

> 一个 protein/track node 外围带细虚线 prediction halo，使用 indigo/violet；不使用 AI brain、sparkle、机器人或“magic”符号。

### 5.4 Curated source evidence

文件名：`evidence-curated.svg`

> 一个 evidence document 与小型 database cylinder 连接，使用 indigo/teal；不使用奖章、星级或权威认证徽章。

## 6. 负面提示词

将以下内容作为全套通用 negative prompt：

> photorealistic, 3D render, glossy, skeuomorphic, neon, cyberpunk, medical cross, hospital logo, warning sign, danger symbol, patient portrait, blood, surgery, DNA as a generic decoration, AI brain, robot, sparkle, magic, ranking, stars, score gauge, voting, pathogenicity claim, clinical diagnosis, drug capsule, text, letters, numbers, watermark, logo, gradient mesh, heavy shadow, black background, inconsistent stroke width, mixed perspective, cropped object, excessive detail

## 7. 交付检查清单

- [ ] 12 个核心 icon 均有 SVG、256px PNG、512px PNG；
- [ ] 所有 icon 使用一致 viewBox、stroke、圆角和安全留白；
- [ ] 没有文字、logo、水印或未授权数据库商标；
- [ ] 生物学含义与本文件描述一致；
- [ ] 未使用颜色暗示 pathogenicity 或跨来源证据强弱；
- [ ] Disulfide icon 清楚表达 paired endpoints，而不是泛化 chain link；
- [ ] AlphaGenome icon 不暗示已有 variant-effect prediction；
- [ ] Disease icon 保留多个来源独立，不表现投票或统一结论；
- [ ] Anatomy 底图提供稳定 viewBox 和 landmark 坐标；
- [ ] 素材许可允许公开 SCI 数据库长期使用；
- [ ] 文件名与目录结构符合约定。
