# 序列/结构精修与预测interface接入

核对：2026-09-21 04:24，香港时间。范围为用户在本侧对话提出的序列密度、坐标/范围、结构着色及已发布预测数据入库；不替代并行基础信息/Variant Catalog任务的交付状态。[现行方案](../../archive/00_initial_preview/plan/sequence_structure_refinement.md)、[问题追踪](../../archive/00_initial_preview/research/website_v2/issues.md)。

## 当前交付

- Sequence去掉重复Variant Distribution，保留覆盖简报及目录跳转。Catalog已由并行任务按U37改成后果/临床分类总览；本轮未恢复其旧位置图。
- PTM主视图默认dbPTM：全序列显示去重位点覆盖带，≤100 aa局部窗口显示统一圆形位点；下方独立位点/修饰/来源/原记录数/详情表，10条分页，可切换来源和修饰类型。隐藏来源不删除上游或数据库记录。EGFR默认129个位点、134个位点/类型注释。
- Secondary低倍率显示Helix/Beta strand/Turn三条窄覆盖带，≤120 aa显示原区间；重叠注释仍可打开。Function sites并入Domain紧凑子轨。
- 每轨共享1-based inclusive范围，并有独立坐标轴；Start/End、缩放、平移、拖选同步更新全部轨道。局部字母按实际容器宽度显示，修复手机端SVG文字横向压缩。
- **最新用户决定：预测interface主视图不列独立表格。** 已接入Sequence Browser单条原始分数曲线：PeSTo选择分片及五类结合倾向；SPPIDER-seq选择伙伴及query角色。连续原值不做阈值、平滑、跨伙伴/分片汇总；悬停/键盘读数、点击/Enter打开位点证据并联动结构。按需打开的位点证据保留分片/伙伴原分数明细。
- Structure提供Confidence、Domains、Membrane、PTM、Variant count、Conservation、PeSTo、SPPIDER-seq八种lens。类别色与0–1连续量尺分别标注；PeSTo绑定当前结构分片，SPPIDER注明两个head均评分query。返回Confidence恢复原pLDDT配色；选中残基高亮单独保留。只有当前canonical完整序列匹配的模型支持位点映射。

## 数据及可重复入口

输入：[PPI已发布科学快照](../../../../modules/PPI/data/curated/20260921_interface_predictions_01/manifest.json)；科学含义和关联约定由[上游契约](../../../../modules/PPI/docs/interface_predictions.md)维护。Web输入路径/版本集中于[interface.yaml](../../../config/interface.yaml)。

```bash
python -m Web.src.database.import_interface
```

导入器按来源逻辑表断点续传，临时schema内校验后原子发布独立`web_interface`；不替换既有四个schema。已发布schema存在时拒绝隐式覆盖。所有来源表完整保留，另建`web_sequence_link`和构建清单；源Parquet不复制改写，冻结源manifest不因Web接入而变更。

| 项目 | 已验证结果 |
| --- | --- |
| 12张来源逻辑表 | 各表数据库计数与输入Parquet计数一致 |
| PeSTo | 7,611蛋白、8,824结构、5,792,650结构残基行；五类分数为native real |
| SPPIDER-seq | 310,534个query–partner方向、192,078,142个query位置×伙伴；两个real[]合计384,156,284个原分数 |
| 当前Web完整序列映射 | PeSTo 7,594，SPPIDER 6,871；其余状态及来源记录保留，不强制投影 |
| 关系和向量长度 | 结构缺序列、query/partner缺序列、两个向量长度不符均为0 |
| Float32往返 | P00533/Q12809 PeSTo位置1、50、858；P00533与seq_000002的两个向量位置1、50、858、1210均与源Float32相等 |

全表行数、映射类别和时间见[导入报告](../../../data/postgresql_interface_import.json)。原科研分数质量核对已在上游完成，本轮没有重跑模型或重复扩大科学QC。

只读API在`/api/proteins/{accession}/interface/`下提供`summary`、`pesto`、`partners`、`sppider`和`sites/{position}`。记录来自完整序列匹配关系，不能仅凭accession强制投影。伙伴列表按完整序列key返回全部已知accession，不任取一个身份。

P00533代表接口与Q01484 F14接口单次本机HTTP实测7.9–21.3ms，均200；属于热缓存、单请求观测，不是并发容量承诺。越界位置0/1211为422，错误结构归属和不存在伙伴为404。只读数据库角色已获新schema的SELECT权限。

## 浏览器验收

目标流程：P00533 → 序列范围/来源/预测轨道 → 位点证据 → 结构配色；再以Q01484多分片验证坐标范围。环境为`http://127.0.0.1:8000`，桌面1440×1000、手机390×844，独立Playwright会话`memvar-seq-refine`。

内置Browser调用报`No browser is available`，运行时列表为空；询问独立Playwright回退后用户要求直接继续完成。回退未操作主任务标签页。

| 检查 | 结果和证据 |
| --- | --- |
| 构建 | `npm run build --prefix Web/frontend`通过TypeScript和Vite |
| 页面身份/非空/错误覆盖 | 路由与标题正确，蛋白h1存在，无Vite错误覆盖 |
| 控制台 | 无应用错误；Chromium软件WebGL有ReadPixels性能警告，模型正常渲染 |
| PTM | dbPTM↔UniProt、Phosphorylation筛选、原位点详情正常；主表10行 |
| 范围同步 | 700–760时各轨同范围，桌面61个残基字母；缩放起点303，平移606，轴拖选727–968 |
| Interface主轨 | 无表格；PeSTo结合类型及SPPIDER伙伴Q99805/两个query角色切换通过；轴随范围变化 |
| 位点联动 | 键盘选701查看原分数；选残基2后Structure明确显示chain A、2 |
| 结构lens | EGFR domain268、膜拓扑1,186、PTM129、variant/JSD/PeSTo/SPPIDER各1,210个映射位置着色；不是实验阳性计数 |
| 恢复confidence | lens回切后恢复蓝/青/黄/橙pLDDT，截图核对 |
| 多分片 | Q01484 F14：2601–3957、1,357位点；Sequence预测轨与3D模型一致，未把其它分片分数合入 |
| 手机 | 390px页面宽度仍为390，无整页横向溢出；表格自身可横向滚动；坐标按312px实际绘图区正常显示 |

本轮截图在`/tmp/memvar-sequence-refinement-qa/`，避免写入共享源码目录：

- [预测interface轨道](/tmp/memvar-sequence-refinement-qa/interface-track-final.png)
- [SPPIDER伙伴/角色切换](/tmp/memvar-sequence-refinement-qa/interface-sppider-track.png)
- [局部序列与secondary/PTM](/tmp/memvar-sequence-refinement-qa/sequence-zoom.png)
- [PeSTo结构](/tmp/memvar-sequence-refinement-qa/structure-pesto.png)
- [恢复pLDDT](/tmp/memvar-sequence-refinement-qa/structure-confidence.png)
- [F14分片](/tmp/memvar-sequence-refinement-qa/structure-fragment14.png)
- [手机PTM](/tmp/memvar-sequence-refinement-qa/mobile-ptm.png)、[手机预测轨](/tmp/memvar-sequence-refinement-qa/mobile-interface.png)

## 依据与限制

参考CATVariant的蓝色选中态、类别色及按需展开，但PTM采用本项目数据的默认dbPTM覆盖/表格，避免来源堆叠；接口预测展示原连续分数，不借用临床颜色或综合致病结论。PeSTo与SPPIDER语义分别核对[原项目](https://github.com/LBM-EPFL/PeSTo)、[官方模型说明](https://huggingface.co/aporollo-lab/SPPIDER-seq)；结构着色使用本地PDBe Molstar 3.12.0及[官方选择API](https://github.com/molstar/pdbe-molstar/wiki/3.-Helper-Methods)。

未测试所有蛋白/浏览器/视口、并发容量和公网部署；无新增模型生物学准确性或临床有效性验证。预测无分数显示缺失，原真实零保留为零；域重叠保留单独颜色，伙伴不合成唯一interface。临时截图可供本次复核，持久事实以上述Markdown及数据库导入报告为准。

## 追加交付：旧版表面风格（2026-09-21 04:36）

用户提供旧站`/home/xuyzh/memVar/website`。只读核对[旧版展示代码](/home/xuyzh/memVar/website/frontend/components/structure-viewer.tsx:284)：Mol* coarse-surface，Gaussian表面，medium质量，忽略氢原子，pLDDT配色；初始化处开启illumination。当前使用PDBe Molstar封装，因此两者同属Mol*技术体系，主要视觉差异来自表面/带状representation与光照。AlphaFold是结构预测来源，PDB是结构文件格式，两者不指定渲染方式。CATVariant的具体渲染引擎本次未取得充分证据，不以外观推断。

[StructureViewer.tsx](../../../frontend/src/components/StructureViewer.tsx)增加Render style选择，当前默认Ribbon，新增Smooth surface · legacy。使用当前已安装引擎的coarse-surface preset及增强光照复现旧版方法，没有再加载第二套引擎。风格与着色lens独立，切换时保留镜头、坐标映射、注释及选中残基。表面强调外形，Ribbon便于观察螺旋/折叠，两个入口均保留。

验证：TypeScript/Vite构建通过；同一P00533模型在Ribbon→Surface→Ribbon→Surface往返后正常显示；Surface下PeSTo的1,210位着色通过，返回Ribbon仍保留PeSTo，再切Confidence恢复pLDDT。独立Playwright桌面1440×1000与390×844验证，手机整页宽度390、无新alert；控制台无应用错误。未做所有模型/显卡性能测试；表面及增强光照比Ribbon需要更多渲染资源。

对比证据：[Ribbon](/tmp/memvar-sequence-refinement-qa/render-ribbon.png)、[旧版表面](/tmp/memvar-sequence-refinement-qa/render-surface.png)、[表面PeSTo着色](/tmp/memvar-sequence-refinement-qa/render-surface-pesto.png)、[手机表面](/tmp/memvar-sequence-refinement-qa/render-surface-mobile.png)。
