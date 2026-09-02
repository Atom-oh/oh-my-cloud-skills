---
name: kiro-convert
description: "Convert Claude Code plugins to Kiro Power format — hooks, skills, steering files, and MCP config. Supports GitHub URL, local path, marketplace name, and individual skill conversion. Use when the user wants to convert to Kiro ('kiro convert'), build a Kiro Power, or port Claude Code assets to Kiro IDE — '키로 변환', '키로 파워', '키로 설치', 'claude to kiro'."
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---

# Kiro Power Conversion Skill

Converts a Claude Code plugin — or a single skill — into an installable Kiro Power: a `POWER.md` manifest plus `steering/` files, `.kiro.hook` hooks, and Kiro-format `mcp.json` that Kiro IDE loads directly. The consumer is a Kiro user who installs the power globally or per-project, or imports it from GitHub via "Add to Kiro". Excellent output passes Kiro's format contract on first load: a valid `inclusion` field on every steering file, no Claude-only frontmatter keys left behind, secrets sanitized to `${VAR}`, and the plugin's bilingual (English + Korean) trigger keywords aggregated into `POWER.md`.

## Workflow

### Phase 1: Source and Target

Infer the source and target from the request; ask only what the request doesn't answer. Output target defaults to `export`.

| Source | Flag | Discovery |
|--------|------|-----------|
| GitHub repo | `--git-url URL` (+ `--plugin-path`, `--branch`) | `git clone --depth 1`, then the plugin subdirectory |
| Local plugin | `--source PATH` | `.claude-plugin/plugin.json` must exist at the path |
| Marketplace | `--marketplace [NAME]` (`--search QUERY` lists matches) | Searches local `plugins/` and `~/.claude/plugins/` |
| Single skill | `--skill PATH` (repeatable) | Each directory must contain `SKILL.md` |

| Target | Path | Use Case |
|--------|------|----------|
| `global` | `~/.kiro/powers/<name>/` | Install for all Kiro projects |
| `project` | `.kiro/powers/<name>/` | Install for current project only |
| `export` | User-specified path | Sharing or manual installation |

Add `--preserve-skills` when skills should stay in Kiro's `.kiro/skills/` format (frontmatter `metadata` with author/version; `references/` and `scripts/` kept) instead of being flattened into steering files.

### Phase 2: Conversion

Run the converter:

```bash
python3 {plugin-dir}/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --source <plugin-path> --output <output-path> --target <target> [--preserve-skills]
```

Other source types:

```bash
## GitHub repository, plugin in a subdirectory, specific branch/tag
python3 convert_plugin_to_power.py --git-url https://github.com/user/repo \
  --plugin-path plugins/my-plugin --branch v1.2.0 --output /tmp/my-power

## Marketplace: list matches, then convert by name into the global target
python3 convert_plugin_to_power.py --marketplace --search "ops"
python3 convert_plugin_to_power.py --marketplace my-plugin --output /tmp/my-power --target global

## Single skill → one standalone steering file
python3 convert_plugin_to_power.py --skill ./skills/my-skill --output ~/.kiro/steering/my-skill.md
```

The field-by-field mapping — frontmatter transforms, hook trigger mapping, fileMatch glob detection, secret sanitization, large-asset (>10MB) handling — is canonical in `references/conversion-rules.md`; the target format itself is specified in `references/kiro-power-format.md`. For a manual (script-less) conversion, follow those two files directly.

### Phase 3: Verification

Kiro loads what parses and silently skips what doesn't — a malformed file surfaces as a missing feature, not an error — so check the output against `references/kiro-power-format.md`:

- `POWER.md` frontmatter carries `name`, `displayName`, `description`, `keywords`, and none of the invalid keys (`version`, `tags`, `repository`, `license`)
- Every `steering/*.md` has a valid `inclusion`; `fileMatch` files also carry `globs`
- `mcp.json` has no `type` fields, has `autoApprove`/`disabled`/`disabledTools`, and any hardcoded secret became a `${VAR}` reference surfaced in the POWER.md onboarding section
- Each `hooks/*.kiro.hook` is valid JSON with `when.type` and `then.type`
- With `--preserve-skills`: each `skills/*/SKILL.md` carries Kiro skill frontmatter

## Conversion Example

A Claude skill frontmatter and its default steering-file result (`triggers` merged into the description, Claude-only keys dropped, `inclusion: auto` added):

```yaml
# Input: skills/ops-troubleshoot/SKILL.md (Claude Code)
---
name: ops-troubleshoot
description: "Systematic troubleshooting workflow"
triggers:
  - "troubleshoot"
  - "장애 대응"
model: sonnet
allowed-tools: [Read, Bash]
---

# Output: steering/ops-troubleshoot.md (Kiro)
---
name: ops-troubleshoot
description: "Systematic troubleshooting workflow. Triggers: \"troubleshoot\", \"장애 대응\""
inclusion: auto
---
```

## Output

Report what the conversion produced: source and output paths, counts per artifact type (steering files, preserved skills, references, hooks), whether `mcp.json` was generated, and every `${VAR}` the user must set before the power works. Close with next steps — open Kiro IDE and confirm the power appears in the powers list, or push to GitHub and import via "Add to Kiro".

## References

- `references/kiro-power-format.md` — Kiro Power directory structure and format specification (POWER.md schema, steering `inclusion` types, hooks, skills, agents, MCP config)
- `references/conversion-rules.md` — Field-by-field conversion rules, hook mapping, fileMatch detection heuristic, edge cases
