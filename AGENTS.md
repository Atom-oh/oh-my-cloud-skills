<!-- generated-by: co-agent · source: CLAUDE.md · claude-md-sha: 07279b149e50 · generated-at: 2026-06-26 · DO NOT EDIT — edit CLAUDE.md then run /co-agent sync-context -->
> You are Codex, an external reviewer — project context below. Distilled from CLAUDE.md.

# oh-my-cloud-skills — reviewer context

A **Claude Code _and_ Codex plugin marketplace**: 6 plugins (aws-content, aws-ops, kiro-power-converter, agentcore-creator, co-agent, project-init). Not a runtime app — the deliverables are plugin definitions (Markdown agents/skills/commands) plus Python/Bash/Node helper scripts. Each plugin ships **both** `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`; the root has `.claude-plugin/marketplace.json` (Claude) and `.agents/plugins/marketplace.json` (Codex).

## Stack
- **Python 3** (stdlib-first; `defusedxml` for XML), **Bash**, **Node.js** (PptxGenJS deck scripts), **Markdown** (agents/skills/commands), JSON manifests. Docs site = Docusaurus (`docs/`).
- No app server. "Code" = helper scripts under `plugins/*/skills/*/scripts/` and `scripts/`.

## Build / test / lint (run from repo root)
- `bash tests/run-all.sh` — TAP test suite (hooks, secret-scan regex, plugin structure). Must be **0 failed**.
- `python3 scripts/test-plugins.py` — validates all 6 plugins' Claude manifests + agent/skill/command refs + version consistency. Must PASS.
- `python3 scripts/test-codex-plugins.py` — validates the `.codex-plugin/plugin.json` manifests + `.agents/plugins/marketplace.json`. Must PASS.
- `python3 scripts/eval-skills.py` — skill quality/structure/token eval.
- Diagram skill gates (before exporting a `.drawio`): `validate_drawio.py` (XML/truncation) → `lint_layout.py` (layout score ≥80) → optional `snap_grid.py` (grid align).
- Remarp: `remarp_to_slides.py validate <dir>` before build.
- PPTX (`aws-light-fcd` skill): build with `NODE_PATH=$(npm root -g) node build.js`; finish with `python scripts/embed_fonts.py <deck>.pptx`.

## Architectural boundaries
- Each plugin: `.claude-plugin/plugin.json` (manifest: `agents[]`, `skills[]`, `commands[]`, `hooks`, `mcpServers`) + `.codex-plugin/plugin.json` (Codex interface manifest) + `CLAUDE.md` (routing) + `agents/*.md` + `skills/<name>/{SKILL.md,references/,scripts/}`.
- **Every path in plugin.json must resolve to a real file** (test-plugins.py / test-codex-plugins.py enforce).
- Content plugin → artifacts (HTML/.drawio/.md/.pptx) → **content-review-agent quality gate (≥85)** before "done". Native PPTX is the `aws-light-fcd` skill (PptxGenJS); it references `reactive-presentation`'s 811-icon library in place via `kit.icon()` — don't duplicate icon assets.
- Ops plugin → diagnoses (commands-first runbooks). co-agent → chairs a multi-AI panel (Kiro/Codex/Antigravity — `agy`, falls back to `gemini` when `agy` absent), the host synthesizes (Codex chairs when `CO_AGENT_HOST=codex`).
- A single shared **version** across all `plugin.json` (both `.claude-plugin` and `.codex-plugin`) + both marketplaces + git tag `v{version}` — they must match.

## Conventions
- **Agent/subagent `tools:` frontmatter takes BARE tool names only** (`Read, Grep, Bash`). Scoped `Bash(cmd:*)` is **NOT honored** in a subagent `tools:` field (that belongs to settings.json `permissions`) — don't "fix" an agent by adding `Bash(find:*)`.
- **Plugin script paths in command/SKILL markdown use the plain `${CLAUDE_PLUGIN_ROOT}` token** (render-time substituted). Do NOT use the bash default form `${CLAUDE_PLUGIN_ROOT:-fallback}` — Claude Code doesn't substitute it and doesn't export the var to the Bash tool, so it silently resolves against the wrong cwd.
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
1. Do all plugin.json refs resolve? Version consistent across plugin.json/marketplace.json (Claude + Codex)?
2. Bash: quote vars, `set -e`-safe capture (`v=$(cmd) && rc=0 || rc=$?`), no unquoted `$(...)` injection, no untrusted repo content interpolated into a command line (use STDIN).
3. Python: `with open(...)`, defusedxml/XXE guard, no silent failures.
4. Any AWS security mandate violated? (see Banned patterns)
5. Secrets committed? Tests/validators still pass?

## Known false-positives (don't over-flag)
- Placeholder credentials in `tests/fixtures/` and the secret-scan pattern tests (example AWS keys / tokens) are intentional test data, not leaks — many carry a `# pragma: allowlist secret` marker.
- `width="60"` in `drawio-xml-guide.md` inline examples is illustrative; the canonical icon size is 78 (design-tokens.md).
- Multi-AI panel "verdicts" are advisory — verify against the actual diff, never vote-count.
- `aws-light-fcd` icons resolved via `kit.icon()` live in the sibling `reactive-presentation` skill — a cross-skill relative path (`../reactive-presentation/icons/`) is intentional, not a broken reference.
- A set of pre-existing test failures is environmental (missing local `.claude/hooks/*.sh`, an unrelated reactive-pptx token test) — compare failure counts before/after a diff rather than treating any failure as new.
