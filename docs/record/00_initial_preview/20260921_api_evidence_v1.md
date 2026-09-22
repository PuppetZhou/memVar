# 2026-09-21：变异与背景证据 API 初版

范围：从已发布 PostgreSQL 读取 Variant、PPI、QTL、Expression、Disease/HPO；按初版网站“主要信息从简、详情分来源/类别展开”的授权组织响应。不重新采集、映射或修改科学数据。本记录维护 API 交付与本次定向核对，页面验收由网站交付记录维护。

代码：[evidence.py](../../../src/api/evidence.py)、[evidence_context.py](../../../src/api/evidence_context.py)、[evidence_disease.py](../../../src/api/evidence_disease.py)、[evidence_common.py](../../../src/api/evidence_common.py)。连接池、只读角色与启动入口复用[基础 API 记录](20260921_api_core_v1.md)。

## 接口与显示取舍

列表使用 `items / next_cursor / filters`，默认每页 20 条，最大 100 条；Expression 默认 30 条。前端可自行按 20 条请求。无全表精确计数，不把当前页大小声明为总记录数。

| 接口 | 主要内容与筛选 |
| --- | --- |
| `/api/proteins/{accession}/variants` | 原 GRCh38 身份、所选转录本后果、来源、gnomAD exomes AF、CADD PHRED/REVEL/SIFT 三项代表评分；`source / consequence / position / limit / cursor`。position 是基因组位置，不是蛋白残基。 |
| `/api/variants/{variant_id}?accession=` | 所选转录本后果、58 项 dbNSFP 与 3 项 AlphaGenome 分六组、总体/群体频率、ClinVar/COSMIC/gnomAD 来源详情、已有 canonical ddG 关系和状态。 |
| `/api/proteins/{accession}/ppi` | 伙伴/原标识、真实来源互作类别、方法、文献、阴性及非蛋白对象标志；`source / interaction_type / limit / cursor`。默认只读 BioGRID/IntAct full 集合，context membership 不复制正文。 |
| `/api/ppi/{record_id}?accession=` | 参与者角色与来源 feature、宿主/条件/置信度等选定字段、context 与文献。`project_entry` 表明确有本站蛋白入口；其他 accession 应使用 UniProt 外链。 |
| `/api/proteins/{accession}/qtl` | 来源变异、分子表型、组织、QTL 类型、P 值、原效应和组装；`source / tissue / qtl_type / limit / cursor`。默认 GTEx；另支持 eQTLGen、QTLbase。 |
| `/api/proteins/{accession}/expression` | `source / category / limit / cursor`；category 为 normal、cancer、cell_line、single_cell。保留 GTEx 官方基因 median TPM 与所选 HPA/FANTOM/CPTAC 来源测量，不合并单位。 |
| `/api/proteins/{accession}/diseases` | 来源疾病断言与原 classification/inheritance/relationship_status；`source / limit / cursor`。ClinGen 基因剂量独立返回，不能赋给每条疾病。 |
| `/api/diseases/{disease_id}?accession=` | 疾病定义、原基因—疾病证据、按需 HPO phenotype 分页；`limit / cursor` 作用于 HPO，NOT/qualifier、原频率、起病、性别、文献与证据保留。 |

页面无需展示日期、内部路径、整包 JSON 或导入元数据。稳定记录键可能包含来源版本，继续保留为关联键。前三项预测只是首屏字段选择，不生成新阈值、投票或致病分类。

## 科学含义与分页边界

- 基因关联用于蛋白导航；所选 MANE 后果不自动等于 UniProt canonical。评分保留 variant/transcript_consequence 粒度、转录本身份、数值和原状态。
- `ddg` 返回 `model / ddg_pred / sequence_id / position / ref_aa / alt_aa`，由正式 annotation→prediction 关系连接，限定当前默认 canonical。状态键是 `sequence_status / prediction_status`。仅已核实的 ThermoMPNN 默认 checkpoint 补充 `unit=kcal/mol` 与 `effect_convention`（负值预测稳定化、正值预测去稳定化）；未知模型不套用该单位/符号。保持连续数值，不新增分类阈值。证据链见下文。
- 频率只使用正式本地 gnomAD exomes 4.1，AF=0 与无频率记录分开；群体 AC/AN/AF 保持原值。COSMIC 样本计数不作为人群频率。
- PPI 类别保留提供者前缀，例如 `BioGRID: physical`、`IntAct: association`，不宣称跨来源等价。来源 feature/突变描述不声明已映射到 canonical 位点。
- QTL 保持 GTEx GRCh38、eQTLGen GRCh37、QTLbase 原有 hg19/hg38 两套坐标；不做 variant mapping、liftover 或新显著性阈值。eQTLGen 的 Zscore 和效应等位基因、GTEx slope、QTLbase 缺少效应的事实分别保留。
- QTL 的精度敏感来源文本保留字符串；前端不能将极小 P 值字符串转换成下溢的 0。QTL 与 Expression 按固定数据集顺序分页；原表无唯一源行键时只以当前冻结快照的 `ctid` 打破重复行排序并列，不把它公开成科学身份。重新发布数据库后应重启 API 并重新开始分页。
- Expression 首版选择上述基因/组织/细胞级测量；转录本样本矩阵、完整逐样本 GTEx 矩阵、预后统计等继续存库，本版不提供全矩阵或预后推断。
- 疾病详情最多展示 100 条基因证据，变异详情最多展示 100 条选定来源记录；分别返回 `evidence_has_more / sources_has_more`，前端有截断时应说明。HPO 自身支持继续分页，不借 MONDO 一般交叉引用扩展来源范围。

## 实际定向验证

使用现有 Python、真实 PostgreSQL 与 FastAPI TestClient，没有另建环境或测试数据库。以下是本次实现阶段的少量代表核对，不是全站负载保证，也未重新运行上游流程。

| 检查 | 结果 |
| --- | --- |
| P00533 五类列表及 Variant/PPI/Disease 详情 | HTTP 200；真实数据可读 |
| 变异来源/后果与分页 | ClinVar、missense_variant 筛选及下一页通过，前后页无重复 |
| 预测详情 | 6 个类别，共 61 项输出；零值、缺失状态保留 |
| canonical ddG | `GRCh38:7:55019282:G:T` → P00533:2 R→L；ThermoMPNN 原值 0.07232671976089478，来自已有关系 |
| PPI 筛选和参与者 | IntAct association、BioGRID 与 source-only 筛选通过；来源角色和引用可读取；`project_entry` 与 web.protein 定向核对一致 |
| QTL | P00533 的 GTEx/QTLbase 有结果；P00533 eQTLGen 无记录保持为空。Q5QGZ9 的 eQTLGen 有结果，GRCh37、Zscore、效应等位基因/FDR 保留 |
| Expression | GTEx TPM、HPA nTPM/IHC、FANTOM tags per million、CPTAC logFC，以及 cancer/cell_line/single_cell 分组读取通过 |
| HPO | OMIM:616069、OMIM:211980 有 phenotype；P00813→OMIM:102700 的 HPO 分页有后续页 |
| 非法请求 | 无效 cursor 为 400，未知蛋白为 404，非法来源为 422 |

查询优化只调整当前 API SQL。Variant 先取当前页再关联评分/频率，P00533 默认列表约 0.08 秒；PPI 先按 accession 取已关联记录再读取正文，20 条 IntAct/BioGRID/全部分别约 0.33/0.12/0.13 秒，避免 ORDER BY/LIMIT 诱使执行器先扫描来源全表。未在本子任务新增数据库索引。

### ThermoMPNN 单位与符号核实

2026-09-21 补充显示元数据，不修改预测结果：[现行规则](../../../../modules/Site-Region/docs/rules.md#ddg预测输入与发布2026-09-17)明确沿用旧默认权重与计算；[发布 provenance](../../../../modules/Site-Region/data/curated/20260917_ddg_thermompnn_01/model_provenance.json)的模型 commit 与只读模型目录实际 HEAD 均为 `2b04fd370e399911b1fa5848112cc9013f084110`，checkpoint 为 `thermoMPNN_default.pt`。[预测脚本](../../../../modules/Site-Region/scripts/ddg/predict_fragments.py)的 `ddg_matrix` 是 mutant raw score 减 WT raw score，与该 commit 的 `transfer_model.py` 中 `subtract_mut=True` 路径一致；[发布脚本](../../../../modules/Site-Region/scripts/ddg/run_prediction.py)直接保留 `ddg_pred`，没有缩放或翻号。保留的[旧实现说明](../../../../modules/Site-Region/data/raw/ddG/legacy_thermompnn_code/README.md)明确负值表示预测稳定化。

项目此前规则未明确单位，本轮再核对原模型论文：[Dieckhaus et al., PNAS 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10861915/)，其 ThermoMPNN 预测结果以 kcal/mol 表达，稳定化方向为负。因此 API 仅对上述明确模型/checkpoint 增加单位与方向说明，不将论文中的筛选阈值引入本项目，不泛化到其他 ddG 模型。

PPI 界面预测的当前状态更正为：正式产物已发布，但尚未接入 Web 服务库，展示选择/查询仍待定；[context.yaml](../../../config/context.yaml)已修正过时的“尚未正式发布”原因。本次未扩大 PPI 服务范围。

## 前端契约审查

2026-09-21 已对照当前 Evidence.tsx/api.ts 向前端实现任务指出并移交：ddG 实际键与 canonical 对象、变异概览空字段、按转录本区分评分、PPI 角色/非蛋白对象/站外伙伴、QTL 分子表型与极小 P 值、来源切换时清除依赖筛选、必选类别的默认值、蛋白切换重置分页、HPO 原证据与 resolved ID。API 本次补充 `project_entry` 并定向验证；页面修复完成情况与渲染证据须由前端联调记录确认，不能以 API 200 代替。
