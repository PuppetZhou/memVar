# ADR-004: Give linked-view selection one owner

- Status: Accepted
- Date: 2026-08-25

## Context

Sequence, Structure, and Variant are linked views of the same protein evidence. When each component writes its own URL and transient selection rules, deep links, keyboard navigation, touch interaction, and hydration can drift.

## Decision

- Treat the URL as the durable source of truth for shareable site, range, variant, and evidence selection.
- Give the protein evidence workspace one selection owner and expose a small typed Interface to child views.
- Keep hover and focus inspection local to each viewport; do not serialize transient pointer state.
- Normalize selection once, preserve accession and isoform identity, and never project isoform positions onto canonical coordinates implicitly.
- Sequence, Structure, and Variant adapters consume the same canonical selection and emit intents rather than independently rewriting URL semantics.

## Consequences

- Deep links and browser navigation remain reproducible.
- Local hover no longer causes unrelated track renders.
- Selection changes require Interface tests covering URL hydration, keyboard, touch, and cross-view linkage.
- Migrating existing writers is incremental, but temporary duplicate ownership must not become a permanent compatibility layer.
