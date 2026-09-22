# Full Sequence Atlas精修交付

2026-09-21，响应06:16后的Atlas反馈；本地实现与定向验收完成。[现行方案](../../archive/00_initial_preview/plan/sequence_structure_refinement.md#full-sequence-atlas细化2026-09-21-0616后反馈)与[问题清单](../../archive/00_initial_preview/research/website_v2/issues.md#full-sequence-atlas2026-09-21-0616后反馈)维护设计和原因。

## 可见变化

- 新`FullSequenceAtlas.tsx`：正方形残基格，响应式每行数量；1440px下50/行，390px下10/行。PTM点置于格内，不再受旧row content-visibility裁剪。
- PTM图例区分实际13类（随当前蛋白/来源变化），类型按钮可筛选，来源菜单独立于上方dbPTM轨道；默认全部已映射来源。多类型点和底色条纹保留类别，不合并来源记录。
- 新`ResidueEvidence.tsx`：当前lens对应标签页前置，PTM按类型、来源、记录数、Evidence对齐；筛选从Atlas带入。原始证据按View source打开，其余features、JSD、结构观测通过标签访问。Interface为按需加载，不默认展开全部信息。
- Variants支持数量及原ClinVar标签组；Predictor coverage支持AlphaMissense/REVEL/SIFT。默认展示有评分的distinct变异数，位点详情前置具体替换的原始评分，可选其它已发布字段。没有位点均值/最大值或新致病判断。
- JSD原值、刻度/表针、occupancy/gap/non-gap/source status集中展示。Secondary模式将secondary注释排序到前面。

## 数据接口与边界

`GET /api/proteins/{accession}/sequence/prediction-coverage`由`sequence_prediction_coverage.py`维护；沿用Variant目录已发布的canonical ddG links，提供site variant_count/scored_variant_count与annotation counts。评分字段白名单，排除缺失/NaN/Infinity，真实0保留。多annotation不重复计变异，全局计数跨position去重。来源、consequence、transcript_status可过滤。P00533首次定向查询约0.11秒，未全库扫描、未重算预测。

PTMD2仍属Disease，不重新加入Atlas序列映射。轨道隐藏/上方PTM默认来源不再无声改变Atlas；页面明确两个面板筛选独立。源feature和score数据未删减。

## 验证结果

- 最终`npm run build`通过（TypeScript + Vite，1702模块）。
- `python -m unittest Web.tests.test_sequence_prediction_coverage -v`：5项通过；覆盖真实ClinVar细目一致性、SIFT零、非finite/缺失、重复annotation/跨position、非法参数及空数据。
- Browser连接发现返回空列表，沿用当前任务既有Playwright会话验证本地`http://127.0.0.1:8000/protein/P00533`及`Q12809`；没有用户显式限定浏览器。服务已重启接通新接口。

| 检查 | 实际结果 |
| --- | --- |
| 页面身份/非空/无错误覆盖层 | 蛋白页标题、Atlas及详情正常，代表交互无JS pageerror |
| 位点PTM | K867含5条position/type/source摘要；dbPTM筛选2条；ProteomeScout+Acetylation筛选1条并带入详情 |
| 预测详情 | T790S=0.8207、T790K=0.9969、T790M=0.966（AlphaMissense），预测列前置，ClinVar原标签独立 |
| JSD与模式 | T790 JSD=0.79464，occupancy=1、gap=0、non-gap=200；Secondary点击默认Sequence features |
| 方格/标记 | 窄屏21.5×21.5px；K867三个5px点边界均在tile内；桌面/窄屏无整页横向溢出 |
| 第二蛋白/键盘 | Q12809长度1159，SIFT覆盖可用；方向键从501移动到502 |
| 原证据 | PTM View source仍请求原feature/record IDs详情，不删证据 |

初次窄屏每行5格导致页面过长，已调整实际容器计算为10格；三类型点在最窄格存在半像素外溢，已缩为5px并复核三个点完全在格内。以上是本次实际发现并修复的问题。未据代表验收声称覆盖所有蛋白、所有预测器或浏览器；Atlas覆盖着色目前只提供3个已确认字段，详情仍可选现有预测器字典。

截图保存于`/tmp/memvar-v2-qa/`：`68-residue-ptm.png`（来源表格）、`69-atlas-predictor-details.png`（逐替换原分数）、`72-atlas-ptm-mobile.png`（窄屏来源筛选）、`74-atlas-mobile-final.png`（最终窄屏方格）、`75-atlas-final.png`（最终完整图例）。调研参考为用户本轮CATVariant截图及已有网站参考记录，不新增科学分类阈值。
