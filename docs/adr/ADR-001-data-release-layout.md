# ADR-001: Separate source and serving releases

- Status: Accepted
- Date: 2026-08-25

## Context

memVar v1 combines immutable collected source data with derived assets optimized for a read-only website. AlphaGenome alone contributes about 2.764 TB of original data, while the current serving layer is about 57 GB. UI releases must not duplicate or rewrite the source snapshot.

## Decision

Use three independently versioned layers:

- `sources/source-v1.0.0`: immutable original and normalized inputs, including the complete AlphaGenome source copy and gnomAD v4.1 source Parquet.
- `serving/serve-v1.0.0`: rebuildable DuckDB, partitioned Parquet, structure, anatomy, and AlphaGenome display assets.
- Git application releases: code, ETL, tests, documentation, and lightweight configuration only.

Every data release has a `RELEASE.json` manifest. `_READY` is written last, after validation, and is required before runtime access. Runtime code obtains typed release-relative paths only through `ReleaseStore`.

## Consequences

- Later UI changes do not copy the multi-terabyte source snapshot.
- Serving data can be rebuilt and compared without mutating source data.
- Real scientific data never enters GitHub.
- A staging directory without `_READY` is intentionally unusable by the application.
- Initial cutover retains all old source locations for rollback; deletion requires a separate explicit decision.
