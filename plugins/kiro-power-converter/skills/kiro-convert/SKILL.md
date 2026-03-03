---
name: kiro-convert
description: "Convert Claude Code plugins to Kiro Power format. Supports GitHub URL, local path, marketplace name, and individual skill conversion."
triggers:
  - "convert to kiro"
  - "kiro power"
  - "kiro convert"
  - "키로 변환"
  - "키로 파워"
  - "claude to kiro"
---

# Kiro Power Conversion Skill

A systematic workflow for converting Claude Code plugins into Kiro Power format.

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

### Phase 4: Conversion

Run the conversion script:

```bash
python3 {plugin-dir}/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --source <plugin-path> --output <output-path> --target <target>
```

Or perform manual conversion following the rules in `references/conversion-rules.md`.

### Phase 5: Verification

1. **Structure check** — Verify output contains `POWER.md`, `steering/` directory
2. **POWER.md check** — Confirm frontmatter has `name`, `displayName`, `description`, `keywords`
3. **Steering check** — Confirm all steering files have `inclusion` field
4. **MCP check** — If source had `.mcp.json`, verify `mcp.json` has no `type` fields and has `autoApprove`/`disabled`

### Phase 6: Next Steps

- **Test in Kiro** — Open Kiro IDE and verify the power appears in the powers list
- **Publish to GitHub** — Push to a repository and use "Add to Kiro" import
- **Share** — Distribute the exported directory to other Kiro users

## References

- `references/kiro-power-format.md` — Kiro Power directory structure and format specification
- `references/conversion-rules.md` — Detailed field-by-field conversion rules and edge cases
