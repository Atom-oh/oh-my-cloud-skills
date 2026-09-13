# docs/ — Internal project documentation

Project context for Claude Code, Codex, other reviewers and contributors. The public
Docusaurus site lives in `../doc-sites/`; keep site content there and internal
decisions, runbooks and implementation context here.

## Layout

- `decisions/`: ADR rationale and status; read its `CLAUDE.md`.
- `runbooks/`: recurring operational procedures; read its `CLAUDE.md`.
- `reference/`: cross-cutting implementation and review guidance.
- `superpowers/`: dated design specs and plans; read its `CLAUDE.md`.
- `architecture.md`: current architecture and derived inventory.
- `onboarding.md`: setup and contributor checks.
- `ci-pr-review.md`, `ci-pr-review-runbook.md`: current CI design and operations.
- `pr-review/review-memory.md`: evidence maintained by the authorized local host.

## Maintenance rules

- Maintain concise English prose in internal docs, README/CHANGELOG and scoped
  instructions. [ADR-023](decisions/ADR-023-bilingual-public-guides.md) makes the public
  guide site a Korean/English exception to ADR-021. User artifact language and
  functional trigger/API/fixture literals remain separate concerns.
- Derive inventory from source files, generated inventories and manifests. Distinguish
  source procedures, Codex entries, plugin hook commands and CI review cells.
  Keep `architecture.md`, the root README and `../doc-sites/docs/intro.md` aligned
  when plugin membership or published counts change.
- Check living claims against source and current policy. Code that violates a
  requirement is a defect to resolve, not permission to weaken that requirement.
- Preserve historical ADR/spec/plan rationale as dated evidence; add a scoped status
  note and a superseding decision when behavior changes.
- Never use historical fail-open or verdict-only rules to accept a PR. Current
  acceptance requires latest-HEAD review, no unresolved Critical/Major issues,
  complete configured coverage, separate Codex validation and required checks.
- `/sync-docs`, `/add-adr`, `/add-runbook` and `/add-reference-doc` supply workflows;
  repository language, ownership and user instructions override template defaults.
