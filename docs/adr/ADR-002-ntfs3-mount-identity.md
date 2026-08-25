# ADR-002: Gate releases by NTFS3 volume identity

- Status: Accepted
- Date: 2026-08-25

## Context

The v1 data root is `/media/xuyzh/Newsmy`, a stable NTFS3 volume with UUID `9894627C94625D2E`. A mount path alone is insufficient evidence that the intended disk is present, and NTFS3 does not provide the same ownership, mode, or symlink assumptions as a native Linux filesystem.

## Decision

- Keep NTFS3 as the single target filesystem Implementation.
- Require both an explicit release root and expected filesystem UUID at startup.
- Resolve and validate the mounted filesystem identity before opening catalogs or facts.
- Reject missing manifests, missing `_READY`, missing required assets, and paths escaping the release root.
- Publish by a same-volume directory rename after validation; do not use an NTFS symlink as `CURRENT`.
- Do not depend on POSIX owner/mode preservation or runtime directory scans.

## Consequences

- A disconnected or incorrectly mounted disk fails closed instead of creating or reading partial local data.
- Release paths are explicit deployment configuration.
- Cold- and warm-read budgets must be measured on the real NTFS3 disk.
- Staging can be resumed safely, but it cannot serve traffic until signed ready.
