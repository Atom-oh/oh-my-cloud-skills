# docs/runbooks/ — Operational Runbooks

Step-by-step operational procedures (the **how-to**, vs ADRs' **why**). Each runbook is a
self-contained, copy-paste-ready procedure for a recurring operational task.

## Conventions
- **Filename**: `kebab-task.md` (e.g. `plugin-release.md`).
- **Copy-paste ready**: commands must reference real scripts/paths in this repo; verify
  they resolve before committing (a runbook with stale paths is worse than none).
- **Bilingual** (KO/EN) where user-facing; no emojis; match the repo prose style.
- Cross-link the relevant ADR (`../decisions/ADR-NNN`) and scripts when a step encodes a
  decision or runs a helper.

## Coverage
This is a Claude Code **plugin marketplace** (no Dockerfile/Terraform/CDK/DB migrations),
so deployment/migration/incident runbooks are largely N/A. Current runbook(s):
- `plugin-release.md` — version bump across all `plugin.json` + `marketplace.json`, tag `v{version}`, push.
  > Known gap: the current steps (and the root `CLAUDE.md` version-consistency snippet)
  > only bump/check 3 of the 6 plugins (content/ops/converter) + marketplace. The
  > single-version invariant covers **all six** — `agentcore-creator`, `co-agent`,
  > `project-init` must bump too. Fix the runbook before the next release.

Add a runbook only for a genuinely repeated operational procedure; one-off steps belong in
the PR description or the relevant skill, not here. The `/add-runbook` command (project-init)
scaffolds from a template.
