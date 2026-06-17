# docs/decisions/ — Architecture Decision Records (ADRs)

Nygard-style ADRs capturing **why** a decision was made. One file per decision; never
edit a decision's rationale after acceptance — supersede it with a new ADR instead.

## Conventions
- **Filename**: `ADR-NNN-kebab-title.md` (zero-padded, monotonic). `ADR-001`/`ADR-002`
  predate the slug convention; `ADR-003+` use the descriptive slug. `.template.md` is the
  skeleton (not a real ADR — excluded from numbering scans).
- **Next number**: `find docs/decisions -name 'ADR-*.md' -not -name '.template.md' | sort | tail -1`. The `/add-adr` command (project-init) auto-numbers.
- **Sections**: `# ADR-NNN: Title` (English title) → `## Status` → `## Context` →
  `## Options Considered` (optional) → `## Decision` → `## Consequences` → `## References`.
- **Status line**: `Accepted (YYYY-MM-DD)` / `Proposed` / `Deprecated` / `Superseded by ADR-NNN`.
- **Language**: English title; **Korean body with English technical terms** (repo bilingual style); no emojis.
- **Length**: concise (~25–40 lines). Link the implementing files/PRs in References.

## Superseding / reconciling
When a newer decision reverses an older one: set the old ADR's Status to
`Superseded by ADR-NNN`, and the new ADR's Context cites the superseded number + the
conflicting quote. The `decision-reconcile` skill (project-init) detects contradictions
across accumulated ADRs and drafts the superseding ADR.

> Keep ADRs decision-scoped — operational how-to belongs in `../runbooks/`, and living
> architecture overview in `../architecture.md`.
