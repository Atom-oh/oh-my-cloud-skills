# docs/decisions/ — Architecture Decision Records (ADRs)

Nygard-style ADRs capture **why** a decision was made. Preserve accepted rationale as
dated evidence. Translate prose without changing its meaning; supersede changed
decisions instead of rewriting past behavior as current.

## Conventions
- **Filename**: `ADR-NNN-kebab-title.md` (zero-padded, monotonic). `ADR-001`/`ADR-002`
  predate the slug convention; `ADR-003+` use the descriptive slug. `.template.md` is the
  skeleton (not a real ADR — excluded from numbering scans).
- **Next number**: inspect `rg --files docs/decisions -g 'ADR-*.md' | sort -V` for the highest
  zero-padded `ADR-NNN-*.md` and increment it. ADR-025 is the latest as of
  2026-09-25. The `/add-adr` command auto-numbers; `.template.md` is not an ADR.
- **Sections**: `# ADR-NNN: Title` (English title) → `## Status` → `## Context` →
  `## Options Considered` (optional) → `## Decision` → `## Consequences` → `## References`.
- **Status line**: `Accepted (YYYY-MM-DD)` / `Proposed` / `Deprecated` /
  `Superseded by ADR-NNN`. For a partial reversal, retain the acceptance date and
  name the superseding ADR and affected scope. Use `Accepted (date unrecorded)`
  when the original date is unknown; put later implementation checks in the scope note.
- **Language**: English throughout (title + body); no emojis.
- **Length**: concise (~25–40 lines). Link the implementing files/PRs in References.

## Superseding / reconciling
When a newer decision reverses an older one, update the old Status and have the new
Context cite the conflicting rule. Mark partial supersession explicitly; unaffected
rationale remains historical evidence. The `decision-reconcile` workflow can assist.

[ADR-021](ADR-021-english-docs-current-review-authority.md) records English internal
documentation and review authority; [ADR-023](ADR-023-bilingual-public-guides.md)
defines the Korean/English public-guide exception. Earlier model rosters, plugin totals, timeout
values, coverage rules and review transcripts are snapshots, not current instructions.
Check source for implementation and current policy for requirements; a mismatch does
not authorize a policy exception. Local optional hooks and mandatory PR CI have
different contracts.

> Keep ADRs decision-scoped — operational how-to belongs in `../runbooks/`, and living
> architecture overview in `../architecture.md`.
