# docs/runbooks/ — Operational procedures

Keep recurring tasks as self-contained procedures with real script paths and explicit
verification. Use `kebab-task.md` filenames, concise English prose, and links to the
relevant ADR and helper. User-requested artifact language is independent of maintained
documentation language ([ADR-021](../decisions/ADR-021-english-docs-current-review-authority.md)).

This repository ships eight plugins for Claude Code and Codex. It has no application
server or database migration lifecycle. `plugin-release.md` covers releases; CI review
operations live in `../ci-pr-review-runbook.md`. Kiro startup, no-tools-agent and
quota diagnostics are in `pr-review-panel.md`.

Release procedures must cover all eight Claude manifests, all eight Codex manifests,
both marketplaces, generated-output freshness and the shared `v{version}` tag.
Run the required tests and host-specific checks; do not hardcode an old test count or
treat optional local hooks as mandatory CI evidence.

Use `/add-runbook` for scaffolding, applying this repository's instructions over
template defaults. One-off actions belong in the PR description or owning skill.
