# 12. 板块差异化配色与卡通结构展示计划

状态：已完成  
计划日期：2026-08-16  
适用阶段：M12 完成后的 M13 视觉增强

> M18 覆盖说明（2026-08-24）：第 3 节及第 4/5 节中的 cartoon/ribbon 展示合同已被项目负责人明确取消。当前有效合同见 `16_m18_premium_visual_refinement_plan.md`：真实 AlphaFold PDB 使用半透明 molecular surface、backbone sticks 与 CA nodes，不再使用 cartoon/ribbon。

## 1. 参考系统

采用 Radix Colors 官方的 scale anatomy 作为 UI 角色参考：浅色用于页面/组件背景，中档用于边框与交互状态，实色用于强调，深色用于文字。MemVar 不引入新的运行时依赖，而是将现有统一色板整理为 semantic section tokens。

参考：

- https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale
- https://www.radix-ui.com/colors/docs/palette-composition/composing-a-palette

## 2. 板块色彩合同

- Basic/Identifiers：indigo/cyan，表达蛋白身份与导航。
- Sequence：indigo，Structure：cyan，使二维序列与三维结构相关但可区分。
- Variants：coral，Expression：jade，QTL：amber，Interactions：leaf，Diseases：crimson。
- 每个板块使用同一色相的 soft background、border、solid accent 和 deep text，不用随机色。
- 科学数据本身的颜色语义保持不变；section accent 只用于标题、边框、卡片层次和交互状态。
- Error/conflict/P/LP 等既有语义色不被 section accent 覆盖。

## 3. PDB 卡通风格合同

- 保留 Sequence variants / AlphaFold confidence 两种互斥配色模式。
- 3Dmol cartoon 使用更厚、更圆润的 secondary-structure ribbon，开启 helix tubes、beta arrows。
- 开启全局 outline 与适度 ambient occlusion，形成清晰的插画式边缘和体积；不添加表面模型或原子球棒，以免遮挡 residue 配色。
- 保留旋转、缩放、重置、全屏和下载功能。

## 4. 验收

- 蛋白页各主要板块在统一色系中可快速区分，标题与卡片不会全部呈现同一种蓝色。
- section accent 不改变热图、sequence variant density、pLDDT、P/LP 或 conflict 的科学含义。
- PDB 呈现更厚的 cartoon ribbon，具有 tube/arrow、outline 与柔和体积阴影。
- 前端 production build 和 P00533 页面响应通过。

## 5. 实施记录（2026-08-16）

- 参考 Radix Colors 的 scale roles，为蛋白页主要板块建立独立 semantic accent；浅色背景、中档边框、实色强调和深色文字来自同一板块色相。
- 新增统一 section theme 层，Basic、Identifiers、Annotation、Sequence、Structure、Variants、Expression、QTL、Interactions 与 Diseases 使用可辨识但协调的颜色。
- 科学数据色未被覆盖；Sequence density、pLDDT、P/LP、error/conflict 继续使用原语义。
- 3Dmol cartoon 改为 oval ribbon，开启 helix tubes、beta arrows，增加厚度，并启用 outline + ambient occlusion。
- 前端 production build、P00533 蛋白页与 structure metadata 在线响应通过。
