# 代表转录本身份与变异详情入口

2026-09-22。用户要求开始执行主任务及旁支已确认任务。实施前只读核对“Web-优化”任务为空闲，未启动或操作子代理。本批仅调整变异详情前端及本地构建，不改写代表选择、科学数据或数据库。

## 实际改动

- VA-03、VA-05：Variant首屏直接展示代表ENST、ENSP、HGNC、蛋白/编码变化及选择依据；代表详情与首屏复用组件。MANE Select与“基因无MANE Select时采用Ensembl canonical”的项目选择独立于VEP canonical flag解释。来源未提供ID时明确显示，不生成空ID外链；原版本原样保留。
- 删除首屏含混的Association/context_matched显示；不将其解释为UniProt匹配。VA-06的完整序列比较和具体isoform关系尚未实现，页面没有伪造匹配目标或not-match结论。
- VA-07：ClinVar/COSMIC归入Clinical一级入口，各保留来源切换。由原COSMIC入口进入仍保持COSMIC选中，Clinical父标签同时高亮；提示COSMIC来源记录本身不是临床致病结论。
- VA-08：Population一级页签改为Frequency，原频率数据与群体明细保留。

负责文件：[VariantCatalog](../../../frontend/src/components/VariantCatalog.tsx)、[VariantEvidencePanels](../../../frontend/src/components/VariantEvidencePanels.tsx)、[局部样式](../../../frontend/src/components/variant-evidence.css)。本次未增加依赖或额外数据请求。

## 验证与发布

- TypeScript及Vite生产构建通过，候选先输出到`/tmp/memvar-representative-ui-build`。
- 本地真实API样本`GRCh38:7:55191822:T:G`、P00533，返回ENST00000275493.7、ENSP00000275493、Leu858Arg。组件静态渲染核对具体ID/变化、MANE与VEP独立标签、canonical fallback、缺ID及空记录状态均通过；确认没有把context_matched渲染成序列匹配结论。
- 候选静态资源复制至当前dist，旧hash资源保留供已打开页面使用，最后原子替换index。本地8000入口与候选一致，入口JS/CSS均HTTP 200。不重启服务、不恢复公网、不改数据库。
- Browser运行时返回`No browser is available`，按故障指引检查连接列表为空。没有绕过到其他浏览器。**真实桌面点击、视觉截图和浏览器控制台验收未完成**；静态渲染不替代交互验证。

VA-03/05/07/08为“代码及本地静态发布完成，桌面交互验收待补”，不是全阶段完成。VA-06及ClinVar条件级数据、表达汇总热图、结构/选择联动等仍按当前计划推进；本批没有启动对应后台作业。
