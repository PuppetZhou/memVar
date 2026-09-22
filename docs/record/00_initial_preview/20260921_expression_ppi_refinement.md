# Expression 与 IntAct mutation 展示精修

2026-09-21，香港时间约05:25。本轮完成用户指定的数字分页、测量类型解释、mutation效应优先和可读标签审查。仅修改前端，复用现有API、PostgreSQL与当前服务进程，未重启服务或重跑数据流程。

现行行为分别维护于[Expression方案](../../archive/00_initial_preview/plan/expression.md#expression-display-refinement)和[PPI/context方案](../../archive/00_initial_preview/plan/context.md)；14个数据集类型核对、原始来源与发现的问题见[专项调研](../../archive/00_initial_preview/research/website_v2/context_review.md#expression-ppi-20260921)。

## 已交付

- Tissue & cell contexts：12项/页，数字页码、当前页、首尾页、省略号和直接跳页；搜索与数据集切换重置页码，真实无结果状态。
- Expression：五类方法介绍（bulk RNA-seq、single-cell/nucleus RNA-seq、CAGE、MS、IHC）与原生context类别并列解释，14个当前数据集均有明确方法badge。记录数不冒充表达量，量值与单位保持原义。
- IntAct mutation：主表为mutation/feature、effect、reported partner、sequence change、publication、evidence；移除Source range和mutation名称中的UniProt前缀。详情用大效应卡片，原分类紧随其后，其他原证据折叠。
- 互作效应：增强青绿、减弱橙、中断粉红、无观察效应蓝、诱发紫、未知灰，配文字/箭头；strength/rate维持独立原词；环图与表格配色一致。普通mutation不伪造成无效应。
- Expression、QTL的组织/细胞名称及PPI项目名称以可读格式显示，GTEx `Brain_Cortex` 显示 `Brain Cortex`。原ID/筛选键不改，查询结果保持一致。

文件：`frontend/src/components/ContextPanels.tsx`、`ContextDisplay.tsx`、`context-detail.css`、`PpiOverview.tsx`。保留并行任务对序列、结构、其他模块的修改。

## 实际验证

构建命令 `npm run build --prefix Web/frontend` 通过 TypeScript 和 Vite。浏览器使用前轮已获准的独立Playwright fallback会话：Browser运行时之前报告“No browser is available”，不操作主线程浏览器。地址 `http://127.0.0.1:8000/protein/P00533`，桌面1440×1000、窄屏390×844。

| 检查 | 结果 |
| --- | --- |
| 页面身份/非空/错误遮罩 | 正确memVar/P00533，真实内容渲染，无框架错误遮罩 |
| 数字翻页 | GTEx 68 contexts共6页；直接选第3页显示25–36，第6页8项且Next禁用 |
| 大页数跳转 | HPA癌症RNA 8384 contexts共699页；输入699直达8377–8384，8项，尾页不能继续 |
| 搜索及原键 | 输入Brain Cortex得到唯一context，打开明细为5.61708 TPM，标题/行/详情无下划线，URL仍使用原Brain_Cortex键 |
| 无结果 | 输入不存在的context后0 contexts，空状态明确，不残留旧页条目 |
| 测量类型 | 14集合分为5/2/1/4/2类方法集合数，P00533记录数9728/1329/46/122/143；卡片单位与现有API一致 |
| QTL名称 | 搜索Brain Cortex，组织条为115记录，点击后表格tissue为Brain Cortex，源filter仍原键 |
| Mutation默认未知 | p.Ala750Pro、feature EBI-9356677：Effect not specified，原mutation标签，伙伴Q16543，不显示Source range或P00533前缀 |
| Mutation增强 | p.Lys745Ala、EBI-11297365：Increased interaction strength；Q86VI4；PMID25594178；详情突出相同效应 |
| Mutation减弱 | p.Tyr1069Phe、EBI-11783375：Decreased interaction；P22681；PMID27059931 |
| Mutation中断 | p.Val948Arg、EBI-15822365：Interaction disrupted；不因可解析参与者只有EGFR而猜自互作 |
| Mutation无效应 | p.Asp855Ala、EBI-21202162：No observed effect；Q05209；PMID28065597；与未知灰色分开 |
| 附加来源证据 | 展开仍可读Figure legend、source participant/organism；保留原API证据，但不重复默认范围/affected accession字段 |
| 窄屏 | Expression页码2可操作，页面clientWidth/scrollWidth均390；mutation详情均356，无横向溢出 |
| 控制台 | 末次实际检查Errors=0、Warnings=0 |

截图位于 `/tmp/memvar-sequence-refinement-qa/`：`expression-assay-overview.png`、`expression-context-pages.png`、`expression-assay-mobile.png`、`expression-pages-mobile.png`、`ppi-mutation-table.png`、`ppi-mutation-detail.png`、`ppi-mutation-mobile.png`。均为本轮真实页面截图；临时截图不代替本MD的长期验证记录。

限制：当前仅对代表蛋白的上述流程做定向浏览器验收，未全库逐记录浏览或并发测试；原source fields仍是来源证据，原始身份键不作全站文字替换。IntAct若未提供效应方向，页面不能补造该信息。
