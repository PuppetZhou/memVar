# 首页调研与设计核对

> 00阶段历史研究，2026-09-22归档。保留当时依据与状态；当前任务、规则和交付入口见[归档说明](../../README.md)，本文不作为当前执行指令。

2026-09-21；范围：网站总入口、膜蛋白分类检索、代表案例。用户要求先完成一版，可继续调整。

## 参考与项目区别

参考 [CATVariant 首页](https://catvariant.com/)。已用网页读取和独立浏览器查看：实际页面突出“Translate protein variants into biological meaning”、Start Analysis / Example / Paper、分析统计与结果案例，导航含 Analyze / Results / Documentation。静态抓取与动态页面文字存在差异，以实际浏览器为布局观察依据。不能把它描述为一个原本已有本项目大搜索框的页面。

本项目采纳蓝色重点控件、宽留白、分区卡片和案例引导。用户明确要求主搜索，因此改为搜索优先的已收录蛋白检索入口，不引入未实现的提交分析/任务管理流程。统计与案例全部来自本项目服务库，不照搬参考站统计。

## 数据依据

分类规则见 [膜蛋白标签定义](../../../../../../modules/membrane/docs/basic_membrane_labels.md)。读取 `web.protein_membrane_label`，按 accession 去重计数；搜索用 EXISTS 关联，不把一个蛋白展开成多行。

| 标签 | 核对数量 | 页面含义 |
| --- | ---: | --- |
| Integral membrane | 5,213 | canonical 跨膜注释支持 |
| Peripheral membrane | 1,037 | 膜表面相关 |
| Lipid-anchored | 457 | 脂锚连接 |
| Membrane-related | 1,046 | 未得到上述更具体标签的膜相关条目 |

总蛋白 7,715；标签并不互斥，分类之和不能当作总数。前端从 API 读取数字，本表仅为本次核对证据。案例 EGFR/P00533、KCNH2/Q12809、AQP4/P55087 的现行 overview 均可访问。案例说明是浏览方向，不承诺每项注释完整。

## 工作草图与呈现核对

[生成的工作草图](concept.png)是本轮实施参考，并未声称已获用户视觉定稿。实现使用 HTML/CSS、原生控件和线条图标；草图不作为网页背景图。

第一版曾在同一检查轮次通过图像查看工具同时检查草图及桌面、手机实页。以下表格描述第一版；截图已更新为下方素材与定位补充后的[桌面实页](desktop.png)和[手机实页](mobile.png)：

| 核对项 | 结果及有意差异 |
| --- | --- |
| 层次 | 标题搜索、四类入口、三个案例与简洁页脚均保留 |
| 搜索 | 大搜索栏、蓝色按钮、Try 快捷入口一致；按钮增加方向箭头 |
| 配色 | 白底、浅蓝分类区、深蓝标题、四类蓝紫橙青图标一致 |
| 容器 | 桌面四列/三列卡片；边框与圆角、列间距保持同一层级 |
| 字体 | 使用网站现有字体，正文提高到13–15px；实际字形和草图略有差异 |
| 图标 | 膜分类用轻量SVG，案例用既有线条图标；不复制草图示意结构为真实科学结构 |
| 统计与CTA | 真实计数与 Browse 在同一行，减少重复纵向占位；页脚居中 |
| 手机 | 390px单列重排、搜索和导航可用、无横向溢出；长占位文本在输入框内自然裁切，可访问名称保留全文 |

## 问题清单

- HOME-01：根路径跳到EGFR，没有总入口。已替换为首页。
- HOME-02：没有通过现行膜标签辅助查找的入口。已加入四类统计与组合筛选。
- HOME-03：旧搜索只显示前30条。已加总数、数字页码、稳定排序和URL分页。
- HOME-04：多标签关联可能重复显示蛋白。API采用EXISTS，已核对前两页无重复。
- HOME-05：分类总和大于蛋白总数易被误解。页面明确提示标签可重叠。
- HOME-06：首页统计加载失败不能误报零。显示不可用提示，搜索入口仍可使用。
- HOME-07：首页缺少具体案例。已加入三个真实蛋白入口。

不添加新的蛋白分类科学规则；未开展公网部署与容量测试。

## 用户素材与定位入口迭代（2026-09-21）

用户补充：裁切docs素材用于主页背景；三类采用素材，Membrane-related补同色logo；增加按膜定位浏览。替代上文第一版分类区浅蓝底和线条图标的设计，保留主搜索、类型检索与案例。

素材处理：原PNG不变，复制到 `Web/frontend/public/images/home/membrane-original.png` 后用CSS cover/position裁切主页背景并加渐变淡化，保证搜索区对比度。内置image_gen读取原图后整理四格图，输出复制到 `Web/frontend/public/images/home/membrane-categories.png`；CSS按四个象限裁切，180px正方形保持比例。绿色为主体蛋白、灰色为膜/伙伴、红色为脂锚；第四格以虚线表示一般关联，不宣称穿膜或特定锚定机制。

生成工具：内置image_gen，未使用CLI/API fallback。生成来源：`/home/xuyzh/.codex/generated_images/01a0c05f-e4c7-7b62-8002-a591cffabe0a/exec-06ef627f-eb8a-48f2-9f0b-6d921c7c22ab.png`。

提示词（最终请求）：

> Create a production website illustration sprite from the supplied image. Output a perfectly square image arranged as four equal square tiles in a 2x2 grid on pure white background, with NO text, labels, border, dividing lines or watermark. Each tile contains one centered illustration with comfortable white margins and same visual size, cannot cross tile boundaries. Preserve supplied lime green protein ribbons, pale grey membrane slab style, clean flat scientific illustration. TOP LEFT: crop/extract/recompose the LEFT integral multipass membrane protein from supplied image, green helices crossing grey slab. TOP RIGHT: crop/extract/recompose the RIGHT illustration focusing on the green peripheral protein sitting on membrane surface through interaction with a grey membrane-spanning partner, preserving green-versus-grey distinction, compact. BOTTOM LEFT: crop/extract/recompose the CENTER lipid-anchored green protein and red zigzag lipid anchor into grey slab, REMOVE COOH text. BOTTOM RIGHT: design matching membrane-related category symbol, generic green folded ribbon beside pale grey membrane patch, a small dotted grey association line but no depiction of green spanning membrane or lipid anchor; represents unspecified membrane relationship, a symbolic logo not a mechanistic claim. Precisely equal 2x2 tile placement, centered with consistent margins for CSS sprite cropping. No UI or page mockup. Use only lime green, grey, white and the original small red anchor.

定位审查：现行服务表具有entry 7,432行、isoform 1,075行、unresolved 286行；这是来源记录数，不是蛋白数。首页采用entry字段中的原始膜定位，82个标签；不混合HPA gene-level定位。当前Cell membrane 3,517个蛋白、ER membrane 903、Golgi apparatus membrane 445、Mitochondrion inner membrane 335。父子标签不做自动并集；例如Cell membrane和Apical cell membrane分别保留来源含义。

新增问题及处理：

- HOME-08：示意图色系与素材不一致。已用用户图重整三类及新绘第四类，绿色分类背景。
- HOME-09：没有定位维度。已接入原始SL标签、数量与筛选；默认8个具体位置，全部82项可选择。
- HOME-10：可能将泛称Membrane当作具体细胞器。默认具体卡片排除该泛称，下拉明确unspecified，仍可检索全部记录。
- HOME-11：位置多标签/亚型记录可能重复或升级含义。统计distinct accession、筛选EXISTS，明确entry级别，保留亚型注释在蛋白详情。
- HOME-12：裁切可能拉伸或遮挡文本。图片区域使用正方形象限、背景低透明度；桌面及390px实际截图已核对。

## 多层次总览与CATVariant复核（2026-09-21）

本轮重新读取 [CATVariant](https://catvariant.com/) 的网页文本，并在独立Playwright页核对实际渲染。其首页采用浅蓝/青到淡紫渐变、浅色胶囊导航、统计数字、功能分步切换和案例画廊；统计数字具有进入动画，抓取中间帧的值不能作为真实稳定总量。网页静态文本与动态计数不同，本项目未引用其数字。借鉴配色、轻边框、彩色小图标和选择后展开的信息组织，不引入分析提交、自动轮播或与本项目无关的说明。

### 素材选择

用户提供两张截图：`Screenshot 2026-09-21 at 06.08.18.png` 是膜蛋白结合方式总图，文字与箭头密集；`Screenshot 2026-09-21 at 06.08.39.png` 是连续双层。直接试用双层截图发现OH/HO文字仍出现在标题附近，因此最终两种蓝色背景都采用基于这两张图生成的无字衍生图，分别全景/中段放大裁切；原截图仍完整保存。绿色分类插图不被替换。

最终资产：`Web/frontend/public/images/home/membrane-landscape.png`。原图备份副本同目录 `lipid-bilayer-original.png`、`membrane-diversity-original.png`。使用内置image_gen，未用CLI；生成源 `/home/xuyzh/.codex/generated_images/01a0c05f-e4c7-7b62-8002-a591cffabe0a/exec-82c8f0c6-f6b2-4c9e-8101-0b7cbaaa57fe.png`。

最终提示词：

> Edit supplied scientific membrane illustrations into ONE wide 3:1 landscape website background image. Image 1 supplies protein shapes and original sky-blue protein palette; Image 2 supplies continuous lipid bilayer. Preserve their clean scientific educational illustration style and lipid bilayer anatomy, pastel yellow phospholipid tails and pastel sky-blue/pink/purple heads. Remove ALL text, captions, arrows, chemical-letter labels and surrounding page/screenshot chrome. Recompose into a single elegant horizontal bilayer across the lower half; one multipass blue protein on far left and one peripheral blue protein with membrane partner on far right, small lipid-anchored blue protein near far right edge. Keep central upper 70% quiet near-white with a very pale cool-blue atmospheric wash for live website search heading and input. No typography, no UI, no decorative particles, no new molecular mechanisms, no large saturated shapes behind central text. Flat clean soft vector-like textbook art, softened detail suitable as landing hero background. 3:1 wide image.

### 统计与解读

直接复用已有统计接口及其活跃服务版本校验；统计构建依据仍由 `src/database/build_catalog_statistics.py` 与数据文档维护。

| 首页层次 | 本轮主数字 | 含义与限制 |
| --- | ---: | --- |
| Protein & sequence | 7,715 | 独立蛋白accession；16,655个序列单独展示，不相加 |
| Genetic variation | 10,866,094 | GRCh38变异ID；来源成员可重叠 |
| Prediction scores | 43 | 命名工具/配置；61个可选字段不等于61种独立算法 |
| Expression context | 13 | 当前首页显示已列数据集数；原83,921,729观测行不再作为首页主数字，GTEx median vectors不在此目录内 |
| Genetic regulation | 251,055,619 | 来源QTL关联行数，不是独立变异数 |
| Protein interactions | 1,267,236 | 储存的互作/突变feature记录，不是唯一蛋白对；不加预测interface记录 |
| Disease & phenotype | 25,442 | 来源gene–disease evidence ID；疾病ID、表型数单独展示 |

后续精简版本已移除首页分布条、来源菜单和重复Ask the data问句，改为七层主数字和三类内容预览。不同层次数字仍不相加，完整来源分布移交Data Overview；记录数不解释为强度或覆盖率。

### 新问题与处理

- HOME-13：新背景原图文字干扰。无字衍生图与中央淡化处理，三种手动背景均可键盘切换。
- HOME-14：主页缺少数据多样性与规模。七层交互导航、指标、来源分布、选择提示已接入既有统计接口。
- HOME-15：不同单位大数可能误导。显示各自粒度，不加总；表达明确是来源记录，不比较混合测量值。
- HOME-16：Full coverage只更新hash未定位内容。修复目标异步出现后的滚动，已实际复验。
- HOME-17：接口不可用可能展示假零。使用明确错误状态，503模拟与恢复已验收。

视觉对照：采用参考站浅蓝紫气氛及彩色层次控件；保留项目绿色膜分类插图和搜索优先布局。默认无自动动画计数/轮播；鼠标悬停、按下高亮和来源条选择提供反馈。1440px与390px验证；最终截图见本目录desktop/mobile/evidence/hero。


### HOME-18：首页概览不再罗列完整统计

用户反馈：Home同样存在来源柱图密集、数字清单过长问题，但应以精简直观为主。现行方案采用七个紧凑数字入口＋单层主题预览，每层三项具名内容、短介绍与真实示例链接。使用类别色和深浅表现层次，不把装饰图形包装成定量统计。

Expression优先展示13个列示数据集，避免首页用不同测量的83.9M来源行数作为主视觉；数据集列表与排除GTEx median vectors的范围来自原API，不新增数据筛选。预测工具仍是43个命名配置，与61评分字段区分。

页面职责：Home帮助选择研究入口，Data Overview提供分类统计，Documentation维护来源与科学解读。旧首页来源柱图及展开交互是被本决定替代的历史样式；新实现和验收边界见交付记录追加。
