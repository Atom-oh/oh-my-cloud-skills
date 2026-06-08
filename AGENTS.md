<!-- generated-by: co-agent · source: CLAUDE.md · claude-md-sha: 5afa187a28e4 · generated-at: 2026-06-08 · DO NOT EDIT — edit CLAUDE.md then run /co-agent sync-context -->
> You are Codex, an external reviewer — project context below. Distilled from CLAUDE.md.

# oh-my-cloud-skills — reviewer context

A **Claude Code plugin marketplace**: 6 plugins (aws-content, aws-ops, kiro-power-converter, agentcore-creator, co-agent, project-init). Not a runtime app — the deliverables are plugin definitions (Markdown agents/skills/commands) plus Python/Bash helper scripts.

## Stack
- **Python 3** (stdlib-first; `defusedxml` for XML), **Bash**, **Markdown** (agents/skills/commands), JSON manifests. Docs site = Docusaurus (`docs/`).
- No app server. "Code" = helper scripts under `plugins/*/skills/*/scripts/` and `scripts/`.

## Build / test / lint (run from repo root)
- `bash tests/run-all.sh` — TAP test suite (hooks, secret-scan regex, plugin structure). Must be **0 failed**.
- `python3 scripts/test-plugins.py` — validates all 6 plugins' manifests + agent/skill/command refs + version consistency. Must PASS.
- `python3 scripts/eval-skills.py` — skill quality/structure/token eval.
- Diagram skill gates (before exporting a `.drawio`): `validate_drawio.py` (XML/truncation) → `lint_layout.py` (layout score ≥80) → optional `snap_grid.py` (grid align).
- Remarp: `remarp_to_slides.py validate <dir>` before build.

## Architectural boundaries
- Each plugin: `.claude-plugin/plugin.json` (manifest: `agents[]`, `skills[]`, `commands[]`, `hooks`, `mcpServers`) + `CLAUDE.md` (routing) + `agents/*.md` + `skills/<name>/{SKILL.md,references/,scripts/}`.
- **Every path in plugin.json must resolve to a real file** (test-plugins.py enforces).
- Content plugin → artifacts (HTML/.drawio/.md) → **content-review-agent quality gate (≥85)** before "done".
- Ops plugin → diagnoses (commands-first runbooks). co-agent → chairs a multi-AI panel (Kiro/Codex/Gemini), Claude synthesizes.
- A single shared **version** across all `plugin.json` + `marketplace.json` + git tag `v{version}` — they must match.

## Conventions
- **Agent/subagent `tools:` frontmatter takes BARE tool names only** (`Read, Grep, Bash`). Scoped `Bash(cmd:*)` is **NOT honored** in a subagent `tools:` field (that belongs to settings.json `permissions`) — don't "fix" an agent by adding `Bash(find:*)`.
- Prefer `defusedxml`; on stdlib fallback, reject `<!DOCTYPE>`/`<!ENTITY>` (XXE/billion-laughs).
- HTML visualizations: **class-based theming** (`.theme-dark`/`.theme-light`), exact CSS-var names; never `data-theme`.
- Bilingual KO/EN for user-facing docs; no emojis in formal docs.
- Diagram design tokens are canonical in `architecture-diagram/references/design-tokens.md` (icon 78×78; Public subnet green #7AA116 / Private teal #00A4A6) — don't restate divergent values.

## Banned patterns (AWS security — hard rules, flag any violation)
- **No `0.0.0.0/0` inbound** in Security Groups; SGs via CDK/Terraform only (never CLI `authorize-security-group-ingress`).
- Public ALB only via CloudFront prefix list; no Route53 → ALB/EC2 direct.
- No IAM `Principal:"*"`; minimize `Resource:"*"` (require Condition if used).
- No Lambda URL `AuthType: NONE`. No secrets in env vars (use Secrets Manager/SSM).
- PII in DynamoDB needs KMS + TTL. S3 Block Public Access always on. Never delete CloudTrail logs.

## Review checklist
1. Do all plugin.json refs resolve? Version consistent across plugin.json/marketplace.json?
2. Bash: quote vars, `set -e`-safe capture (`v=$(cmd) && rc=0 || rc=$?`), no unquoted `$(...)` injection, no untrusted repo content interpolated into a command line (use STDIN).
3. Python: `with open(...)`, defusedxml/XXE guard, no silent failures.
4. Any AWS security mandate violated? (see Banned patterns)
5. Secrets committed? Tests/validators still pass?

## Known false-positives (don't over-flag)
- Placeholder credentials in `tests/fixtures/` and the secret-scan pattern tests (example AWS keys / tokens) are intentional test data, not leaks.
- `width="60"` in `drawio-xml-guide.md` inline examples is illustrative; the canonical icon size is 78 (design-tokens.md).
- Multi-AI panel "verdicts" are advisory — verify against the actual diff, never vote-count.
