
# AGENTS.md

- Choose the simplest implementation that fully meets the current requirements. Avoid speculative abstractions, configuration, indirection, defensive checks, hashes, checksums, or other QC unless they address a concrete requirement or realistic failure mode.
- Grow the system in layers from the smallest end-to-end version that works. Keep components modular, prefer existing well-maintained libraries and project dependencies, and use database/type-system guarantees instead of duplicating them in application code.
- Do not preserve obsolete paths or add compatibility, fallback, migration, or temporary architecture without an explicit requirement. Make changes for the current system and remove superseded code.
- Treat rejected ideas as absent from the design. If the user says not to use an approach, simply omit or remove it; do not add comments, documentation, configuration, or explanations stating that the approach is not used unless that fact is itself an important persistent requirement.
- Keep code, schemas, tests, comments, and documentation proportional to the actual problem. Every added abstraction, state, validation, table/column/index, dependency, or mechanism should have a clear current purpose; otherwise leave it out.
- Use the  gpt-5.6-`Terra` model as subagent for focused investigation, review, or separable technical work when it can reduce uncertainty or context load. Give it a narrow task, use its findings as input, and keep the final implementation as simple as if the work had been done directly.
