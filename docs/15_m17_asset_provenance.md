# M17 素材来源、许可与可用范围记录

状态：2026-08-24 M17 审核完成；M18 新增一张通过 BioRender 插件生成的完整总览图，见第 8 节。  
目的：为公开发布的 memVar SCI 配套网站保留素材来源、授权范围和上线前核验条件。

## 1. 审核结论

BioRender 不是可将单个图标直接下载、纳入网站资产库并由访客复用的开放素材库。其官方条款仅允许在 BioRender 应用内将图标组合为一张 `Completed Graphic`；不允许把 BioRender Content 作为 standalone asset 提取、再分发，或以可下载、可复制、可复用的形式提供给网站访问者。

因此，本项目**不得**执行以下操作：

- 从 BioRender 图库、模板页或他人已发表图片中下载/裁取单个器官、蛋白、分子或人体图标；
- 将 BioRender 单图标保存到 `frontend/public/assets/scientific-icons/`；
- 对 BioRender 图片做分割、矢量化或其他提取后作为独立网站 icon；
- 绕过登录、订阅、导出或下载限制。

在当前执行环境中没有可供核验的 BioRender 付费账号、导出记录或 Publication License，因此不能合法取得新的 BioRender 成图。即使未来由项目拥有者在符合计划的账号中导出，网站只能嵌入**最终完整图**，并应遵守该图导出时的归属/citation 以及不以素材库形式提供下载的限制。

## 2. 官方依据

| 来源 | 核验日期 | 与本项目的关系 |
|---|---|---|
| [BioRender website usage guide](https://help.biorender.com/hc/en-gb/articles/26139471293597-How-to-use-BioRender-illustrations-in-a-website-non-profit-commercial-and-personal) | 2026-08-24 | 非营利组织网站需要 Academic Individual/Institutional 或更高计划；商业网站需要 Industry Plan；在线使用需标注 `Created with BioRender.com`。 |
| [BioRender Individual Terms](https://www.biorender.com/individual-terms) | 2026-08-24 | BioRender 保留其 Content 的权利；禁止在 BioRender 外将 Content 独立提取、再分发或使其可下载/可复用。 |
| [Publication License terms](https://help.biorender.com/hc/en-gb/articles/17605463719709-Publication-license-Terms-of-use) | 2026-08-24 | 有效 Academic/Industry 许可可发布完成图；不允许销售或下载 BioRender Content 的 standalone 形式，并须恰当署名。 |

网站最终是非营利还是商业/宣传性质尚未被授权人确认；故不能仅以“SCI 配套网站”推断其需要 Academic 还是 Industry 计划。上线前应由项目负责人按实际用途核验计划类型。

## 3. 当前仓库中已存在的 BioRender 文件

| 文件 | 声明来源 | 许可状态 | 当前结论 |
|---|---|---|---|
| `frontend/public/assets/biorender-human-anatomy.svg` | figure `6191fd4843d685255a905b95`，slide `dfb438b2-5e43-5e13-589a-25b10c97a925`；文件内标注生成日期 2026-08-21 | 仓库内无可核验 Premium/Academic/Industry 导出许可或 Publication License | **不得视为已获公开发布授权**；仅保留为本地开发 preview，正式上线前必须由具备相应权限的账号重新导出最终完整图、保留许可记录并校准点位。 |

该文件并非本轮下载或修改。其当前 SVG 还包含嵌入式位图；它不应被拆分为单个器官图标，也不应作为可下载资源宣传。

## 4. 合规获取 BioRender 成图的条件（供项目负责人执行）

1. 由项目授权人登录拥有相应 BioRender 网站发布权限的账户；
2. 在 BioRender 内将需要的元素组合为一张完整的 Anatomy/科研说明图，而非导出单个库存图标；
3. 对目标网站性质选择适用计划：非营利组织站点至少 Academic Individual/Institutional；商业/宣传站点使用 Industry Plan；
4. 从 BioRender 正常导出完整图及可用时的 Publication License/许可凭证；
5. 将导出日期、账号计划类别、图 ID、许可文件位置、要求的署名文字记录在本文件；
6. 在页面紧邻成图处保留 BioRender 要求的 attribution；
7. 新底图进入仓库后，按 M17-E 重新校准全部 anatomy landmark；不得复用旧图坐标。

## 5. 本轮可立即实施、无需 BioRender 新素材的范围

### 5.1 Lucide 通用界面 icon

M17-A 中的 Search、Filter、Reset、Expand/Collapse、Database、External link、Download、Info、Help、Warning、Zoom、Fullscreen、Rotate 和播放控制，可由 `lucide-react` 的内联 SVG 完成。它们不是 BioRender Content，适合实现统一的界面操作语义。应使用命名 import，并保留可见标签或 accessible name。M18 按产品要求移除了 Copy 操作。

候选清单：

| 使用场景 | Icon |
|---|---|
| 搜索/筛选/清除 | `Search`、`ListFilter`、`RotateCcw` |
| 展开/导航 | `ChevronRight`、`ChevronDown`、`ArrowRight` |
| 来源与资料 | `Database`、`BookOpen`、`FileText` |
| 外链与操作 | `ExternalLink`、`Download` |
| 提示与状态 | `Info`、`CircleHelp`、`TriangleAlert` |
| 结构查看 | `ZoomIn`、`ZoomOut`、`Maximize2`、`Rotate3D`、`Play`、`Pause` |

### 5.2 现有本地素材

可继续使用但须保持许可待核验标记的项目仅有当前 Anatomy preview：

- `frontend/public/assets/biorender-human-anatomy.svg`：仅作为已有 navigator 的开发预览底图；不新增下载、不拆分、不再授权给第三方；上线前按第 4 节替换为可证明授权的完整导出图。

本轮没有发现已授权、可独立再分发的生物学 SVG icon。M17-D 的二硫键、M17-C 的 DE、M17-G 的结构图等应先通过排版、标签、颜色 token 与 Lucide 通用操作 icon 改善，不能用未经授权的 BioRender 单图标填充。

## 6. 需要在正式发布前关闭的许可风险

- [ ] 项目负责人确认网站为非营利组织站点或商业/宣传站点。
- [ ] 保存适用 BioRender 账户的计划类型和最终图导出日期。
- [ ] 保存最终图的 BioRender Publication License（若该计划/用途要求）。
- [ ] 将必需的 `Created with BioRender.com` 署名放在上线页面相邻位置。
- [ ] 重新导出的最终完整图已替换 preview，并完成 Anatomy 坐标回归测试。
- [ ] 确认网站未将任何 BioRender Content 作为可下载、可复用的独立文件提供。

## 7. 本轮下载与变更清单

- M17 新下载 BioRender 文件：无。
- 新增 BioRender 单图标：无。
- 修改业务组件/样式：无。
- 新增记录文件：本文件。

## 8. M18 完整总览图增补记录

M18 在项目负责人明确说明其拥有 BioRender 会员资格、并将统一取得出版许可后，通过已认证的 BioRender 插件生成并保存了一张**完整、不可拆分的科学总览图**。该图仅用于 memVar 页面中的整体说明，不作为 icon 素材库，也不提供单元素提取或复用入口。

| 字段 | 记录 |
|---|---|
| 网站文件 | `frontend/public/assets/biorender-memvar-overview.jpg` |
| SHA-256 | `d59bcd9bebc27e53693dc099c0cd6047315e9e283323efe13cf8ebfe0999ea75` |
| 像素与格式 | 2752 × 1536，JPEG |
| BioRender figure | `15782ae5d28b78d158e6580d` |
| BioRender slide | `63e31271-c610-0d18-6d79-e0625fcabe07` |
| 编辑链接 | <https://app.biorender.com/illustrations/15782ae5d28b78d158e6580d?slideId=63e31271-c610-0d18-6d79-e0625fcabe07> |
| 内容范围 | canonical sequence/paired sites、protein variants、independent disease evidence、tissue expression、protein interactions、regulatory genomics 的单张完整构图 |
| 授权状态 | 项目负责人声明拥有会员资格；正式发布前仍需从其账号归档该完成图对应的 Publication License/导出凭证 |

该图不得拆分为 membrane protein、cell、DNA 或其他独立元素，不得在页面提供原图下载按钮。页面相邻位置应保留 `Created with BioRender.com` 署名与编辑/来源说明。此增补不改变第 3 节 Anatomy preview 的许可待核验状态。
