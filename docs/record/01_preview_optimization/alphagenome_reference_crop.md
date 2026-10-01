# AlphaGenome 完整基因＋10 kb 裁剪来源

2026-10-01：完整 gene＋两侧各 10 kb 裁剪副本已发布并成为网站来源。7,750 窗口／11 模态／1,517 tracks 保留原精度与分辨率；HDF5 从 2,585,607,525,831 B（2.586 TB）降至 284,218,757,766 B（284.219 GB），减少 89.01%。原始全窗口 HDF5 已按用户明确授权清理；来源元数据、旧目录和数据库保留，详见 AlphaGenome 结果页的清理记录。

8000 使用只读 DuckDB，原 ngrok 地址保持；仅替换 AlphaGenome 四张目录表及 manifest，其它外部 Parquet 关系保持原定义。页面保留 Saved range 与原始模型上下文的区分；默认、平移和复位均限制在保存范围内，越界请求返回 422。

[上游生效规则](../../../../modules/Alphagenome/docs/rules.md)、[独立代表验收](../../../../modules/Alphagenome/runs/20261001_reference_crop_01/validation_report.md)、[全量验收](../../../../modules/Alphagenome/runs/20261001_reference_crop_01/validation.json)、[容量及发布状态](../../../../modules/Alphagenome/runs/20261001_reference_crop_01/delivery.json)。

运行与回退：`finish_crop.py` 保存切换前两份配置于该 run 的 `rollback/`，用于记录发布时的回退方案。10-01 用户已明确授权删除原始全窗口 HDF5 和旧 AVI partial，不能再直接回退到旧外盘 `reference_root`；当前裁剪数据、来源元数据及 PostgreSQL 保留。删除后原生区间服务检查通过，见[清理与验证](../../../../modules/Alphagenome/docs/result.md#指定旧文件清理2026-10-01-2354)。
