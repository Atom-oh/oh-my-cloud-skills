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

A systematic workflow for converting Claude Code plugins into Kiro Power format, including hooks, skills, steering files, and MCP configuration.

## Workflow

### Phase 1: Source Selection

1. **Identify input type** — Ask the user which source to use:
   - GitHub URL (`--git-url`) — Clone a repository and extract the plugin
   - Local path (`--source`) — Use an existing local plugin directory
   - Marketplace (`--marketplace`) — Search and download by plugin name
   - Skill standalone (`--skill`) — Convert individual skills only

2. **Gather parameters** — Collect required info based on source type:
   - Git: URL, optional branch/tag, optional plugin subdirectory path
   - Local: absolute or relative path to plugin root
   - Marketplace: plugin name or search query
   - Skill: path(s) to skill directories

### Phase 2: Plugin Discovery

1. **Git source** — `git clone --depth 1` the repository, navigate to plugin subdirectory
2. **Local source** — Validate that `.claude-plugin/plugin.json` exists
3. **Marketplace source** — Search local `plugins/` and `~/.claude/plugins/` directories
4. **Skill source** — Validate that `SKILL.md` exists in each specified directory

### Phase 3: Target Selection

Ask the user where to output the converted power:

| Target | Path | Use Case |
|--------|------|----------|
| `global` | `~/.kiro/powers/<name>/` | Install for all Kiro projects |
| `project` | `.kiro/powers/<name>/` | Install for current project only |
| `export` | User-specified path | Export for sharing or manual installation |

### Phase 4: Conversion Options

Ask about conversion preferences:

| Option | Flag | Effect |
|--------|------|--------|
| Preserve skills | `--preserve-skills` | Output skills as `.kiro/skills/` format instead of steering |

### Phase 5: Conversion

Run the conversion script:

```bash
python3 {plugin-dir}/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --source <plugin-path> --output <output-path> --target <target> [--preserve-skills]
```

Or perform manual conversion following the rules in `references/conversion-rules.md`.

#### What Gets Converted

| Source | Target | Key Changes |
|--------|--------|-------------|
| `plugin.json` | `POWER.md` | Manifest → frontmatter; keywords aggregated; author preserved |
| `CLAUDE.md` | `steering/routing.md` | Wrapped with `inclusion: always` |
| `agents/*.md` | `steering/<agent>.md` | `tools`/`model` removed; `inclusion: auto` added |
| `skills/*/SKILL.md` | `steering/<skill>.md` | `triggers` merged into description; `inclusion: auto` |
| `skills/*/references/*.md` | `steering/ref-*.md` | `inclusion: manual` or `fileMatch` (auto-detected) |
| `.mcp.json` | `mcp.json` | `type` removed; `autoApprove`/`disabled`/`disabledTools` added; secrets → `${VAR}` |
| `hooks` in plugin.json | `hooks/*.kiro.hook` | JSON hook files with Kiro trigger/action types |
| SessionStart prompts | POWER.md onboarding | Migrated to body since Kiro has no SessionStart event |

### Phase 6: Verification

1. **Structure check** — Verify output contains `POWER.md`, `steering/` directory
2. **POWER.md check** — Confirm frontmatter has `name`, `displayName`, `description`, `keywords`
3. **Body check** — Confirm POWER.md has onboarding section (if MCP/env vars) and steering mappings
4. **Steering check** — Confirm all steering files have valid `inclusion` field
5. **fileMatch check** — Verify `globs` field present when `inclusion: fileMatch`
6. **MCP check** — If source had `.mcp.json`, verify `mcp.json` has no `type` fields, has `autoApprove`/`disabled`/`disabledTools`
7. **Hooks check** — Verify `.kiro.hook` files have `when.type`, `then.type`, and valid JSON
8. **Skills check** — If `--preserve-skills`, verify `skills/*/SKILL.md` has proper frontmatter

### Phase 7: Next Steps

- **Test in Kiro** — Open Kiro IDE and verify the power appears in the powers list
- **Publish to GitHub** — Push to a repository and use "Add to Kiro" import
- **Share** — Distribute the exported directory to other Kiro users

## References

- `references/kiro-power-format.md` — Kiro Power directory structure, format specification, hooks, skills, agents, MCP config
- `references/conversion-rules.md` — Detailed field-by-field conversion rules, hook mapping, fileMatch detection, edge cases
