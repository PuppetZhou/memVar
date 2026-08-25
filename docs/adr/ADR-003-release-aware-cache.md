# ADR-003: Make caches release-aware

- Status: Accepted
- Date: 2026-08-25

## Context

memVar v1 is immutable after publication, but development middleware historically returned `Cache-Control: no-store`. Unversioned caches could return stale data after a release switch, while disabling all caching wastes repeated DuckDB and Parquet reads.

## Decision

- Include the serving release ID in every server-side cache key and observable request context.
- Generate validators from the release ID, route, and normalized query rather than file modification time.
- Permit immutable caching only for a published release with a valid manifest and `_READY` marker.
- Keep filtered or user-specific responses private when introduced; v1 scientific endpoints are read-only and public.
- Switch releases by changing the pinned release root and restarting, never by mutating published files in place.

## Consequences

- Cached responses cannot cross release boundaries.
- A release switch invalidates data deterministically without scanning individual assets.
- Cache headers and bounded in-process caches remain implementation choices behind the release-aware Interface.
- Performance tests must check both cold and warm behavior and confirm the returned release identity.
