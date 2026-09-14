# ADR-024: Remarp source-first authoring and compiler-backed preview

## Status

Accepted (2026-09-14)

## Context

Remarp carries block structure, speaker notes, fragments and review annotations.
The compiler, editor and guides disagree about project discovery, generated
output and whether HTML is authored independently. Literal code examples are
misparsed, incremental builds leave merged output stale, and multi-block IDs
collide. These defects undermine the format's intended editing workflow.

## Options Considered

1. Preserve independent Markdown/HTML editing: cheap now, recurring source drift.
2. Switch to HTML-first decks: flexible visuals, but requires replacing the
   existing block, note and source-review workflow.
3. Keep Remarp with one compiler/build contract: retains useful authoring units
   and fixes the boundaries responsible for the observed failures.

## Decision

Choose option 3. Remarp is the source for new reactive presentations; HTML is
generated output. The framework contract describes the renderer's DOM/CSS API,
not a replacement for the compiler. Explicit legacy/manual HTML mode remains.
Use existing HTML/script/Archify source blocks for complex visuals; do not grow a
general-purpose layout DSL. VS Code integration will use a compiled preview of saved source
alongside its approximate text preview. Visual writeback remains unsupported.

## Consequences

Build and validation share source discovery and reject critical errors. Merged
identities are unique, and sync must refresh every dependent artifact. Full
regeneration is acceptable until a dependency-aware cache has equivalent tests.
The approach favors repeatable training decks over arbitrary WYSIWYG layouts.

## References

- [Authoring workflow](../../plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md)
- [Block parser decision](ADR-001.md)
- [Validation gate](ADR-005-rejection-loop.md)
