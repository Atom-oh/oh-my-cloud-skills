# docs/ — Internal, Claude-facing project documentation

Documentation Claude (and contributors) read while working on this repo — decisions, ops
runbooks, cross-cutting reference material, and superpowers-workflow specs/plans. **Not**
the public documentation site — that's the separate Docusaurus project at `../doc-sites/`
(published to GitHub Pages). Don't add site content here, and don't add internal docs there.

## Layout
```
docs/
├── decisions/            # ADRs (ADR-NNN-*.md) — see decisions/CLAUDE.md
├── runbooks/              # Operational runbooks — see runbooks/CLAUDE.md
├── reference/             # Cross-cutting reference docs (e.g. review-routing.md)
├── superpowers/           # specs/ + plans/ from the superpowers workflow — see superpowers/CLAUDE.md
├── architecture.md        # System architecture — keep in sync with plugin inventory
├── onboarding.md          # New-contributor onboarding
├── ci-pr-review.md        # CI multi-AI PR review — design notes
└── ci-pr-review-runbook.md # CI multi-AI PR review — operational runbook
```

## Conventions
- `architecture.md` carries **plugin counts** (agents/skills/commands) — update it when a
  plugin's component count changes (the `/sync-docs` skill audits this; `doc-sites/docs/intro.md`
  carries the same counts for the public site — keep both in sync).
- Bilingual (KO/EN) where user-facing; no emojis; match the repo's clear-prose style.
- Each subdirectory has its own `CLAUDE.md` with filename/section conventions — read it
  before adding a file there (`decisions/`, `runbooks/`, `superpowers/`).

> Per-directory scaffolding commands: `/add-adr`, `/add-runbook`, `/add-reference-doc`
> (project-init). Keep this consistent with `../CLAUDE.md`.
