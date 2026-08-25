# ADR-005: Publish variant counts with explicit grain

- Status: Accepted
- Date: 2026-08-25

## Context

A variant can affect multiple protein forms, carry multiple consequence terms, and have multiple independent ClinVar assertions. Summing overlapping categories or voting across assertions would create scientifically misleading totals.

## Decision

- The headline total uses distinct `variant_key` grain and non-overlapping membership.
- Protein-form and consequence facets count distinct variant keys within each category and declare that categories overlap.
- Canonical is an explicit protein-form category; isoform identity is retained.
- ClinVar categories represent raw assertion membership mapped into benign, pathogenic, uncertain, conflicting, other, and unclassified display buckets.
- Missing, empty, and `not provided` assertions map to unclassified, never benign.
- Do not create a memVar consensus vote or combine gnomAD frequency with pathogenicity.
- Every summary response exposes `record_grain` and `categories_overlap` metadata.

## Consequences

- Facet counts are intentionally non-additive and the UI must say so.
- Statistical panels and tests share one counting contract.
- Source-scoped evidence remains auditable to its original release and evidence grain.
- Future filters may report filtered result counts separately, but must not silently rewrite the immutable headline summary.
