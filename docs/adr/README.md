# memVar architecture decision records

This directory records durable architecture decisions for the v1 pre-release. The detailed execution plan remains in [`../17_v1_pre_release_data_architecture_refactor_plan.md`](../17_v1_pre_release_data_architecture_refactor_plan.md).

An ADR describes a decision and its consequences; it is not a claim that every implementation task is complete. A superseded decision is retained and linked to its replacement.

| ADR | Status | Decision |
|---|---|---|
| [ADR-001](ADR-001-data-release-layout.md) | Accepted | Separate immutable source snapshots from rebuildable serving releases |
| [ADR-002](ADR-002-ntfs3-mount-identity.md) | Accepted | Identify the NTFS3 data volume by UUID and publish with a readiness marker |
| [ADR-003](ADR-003-release-aware-cache.md) | Accepted | Key immutable caches by release identity |
| [ADR-004](ADR-004-selection-ownership.md) | Accepted | Give linked-view selection one URL-backed owner |
| [ADR-005](ADR-005-variant-counting-grain.md) | Accepted | Expose variant counts with explicit grain and overlap semantics |
