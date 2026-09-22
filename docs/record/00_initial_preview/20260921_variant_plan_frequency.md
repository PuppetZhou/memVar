# Variant精简方案与频率交付

2026-09-21。五张核心逻辑服务表及无损字段精简已确认，VEP/dbNSFP/AlphaGenome统一归入计算注释与预测，按variant与所选transcript后果粒度关联。现行契约见[Variant表格](../../archive/00_initial_preview/plan/variant_tables.md)，不复制规则。

本地gnomAD频率实际构建、验证并发布至`modules/variant/data/curated/20260921_local_frequency_01`，Web输入已登记。63字段按variant_id共用，真实零与缺失分别保留；数据与验证见[频率交付](../../../../modules/variant/docs/frequency_result.md)。ddG采用既有prediction_id关系与canonical序列/位点联动，并保持ref/alt。

本轮修改方案、频率构建代码和上游Parquet；尚未构建Variant五张Web服务表，未修改PostgreSQL。当前数据库版本仍以现有导入报告为准。

后续执行：Variant服务表已于同日构建并导入，当前结果见[20260921_variant_v1](20260921_variant_v1.md)；上文未导入为本记录当时的阶段状态。
