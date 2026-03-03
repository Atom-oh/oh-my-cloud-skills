# Conversion Rules Reference

Detailed field-by-field conversion rules for transforming Claude Code plugins into Kiro Power format.

---

## Agent Frontmatter Conversion

### Input (Claude Code)

```yaml
---
name: eks-agent
description: "EKS cluster operations... Triggers on \"keyword1\", \"keyword2\" requests."
tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
model: sonnet
---
```

### Output (Kiro Steering)

```yaml
---
name: eks-agent
description: "EKS cluster operations... Triggers on \"keyword1\", \"keyword2\" requests."
inclusion: auto
---
```

### Rules

| Field | Action | Details |
|-------|--------|---------|
| `name` | Keep | Unchanged |
| `description` | Keep/Modify | If `model: opus`, append `(Advanced reasoning)` |
| `tools` | Remove | Kiro determines tool access from context |
| `model` | Remove | Kiro uses its own model routing |
| — | Add `inclusion: auto` | Agent activates when description keywords match user input |

---

## Skill Frontmatter Conversion

### Input (Claude Code)

```yaml
---
name: ops-troubleshoot
description: "Systematic troubleshooting workflow"
triggers:
  - "troubleshoot"
  - "장애 대응"
---
```

### Output (Kiro Steering)

```yaml
---
name: ops-troubleshoot
description: "Systematic troubleshooting workflow. Triggers: \"troubleshoot\", \"장애 대응\""
inclusion: auto
---
```

### Rules

| Field | Action | Details |
|-------|--------|---------|
| `name` | Keep | Unchanged |
| `description` | Modify | Append trigger keywords as `Triggers: "kw1", "kw2"` |
| `triggers` | Remove/Merge | Merged into description string |
| — | Add `inclusion: auto` | Steering activates based on description match |

---

## Reference File Conversion

### Input

Plain markdown files at `skills/<skill>/references/<name>.md` with no frontmatter.

### Output

```yaml
---
name: ref-<skill>-<name>
inclusion: manual
---

<original content>
```

### Rules

- Add YAML frontmatter with `name` and `inclusion: manual`
- Name format: `ref-{skill-name}-{file-stem}`
- Output path: `steering/ref-{skill-name}-{file-stem}.md`
- Content is preserved unchanged

---

## CLAUDE.md → routing.md Conversion

### Input

Plugin `CLAUDE.md` with auto-invocation rules and routing tables.

### Output

```yaml
---
name: routing
inclusion: always
---

<original CLAUDE.md content>
```

### Rules

- Wrap entire content with `inclusion: always` frontmatter
- Content is preserved unchanged
- The `always` inclusion ensures routing context is available in every conversation

---

## .mcp.json → mcp.json Conversion

### Per-Server Rules

| Field | Action | Details |
|-------|--------|---------|
| `type` | Remove | Kiro infers type from `command` vs `url` presence |
| `command` | Keep | Unchanged |
| `url` | Keep | Unchanged |
| `args` | Keep | Unchanged |
| `timeout` | Keep | Unchanged |
| `env` | Keep | Unchanged |
| `autoApprove` | Add if missing | Default: `[]` (empty array) |
| `disabled` | Add if missing | Default: `false` |

---

## POWER.md Generation

### Keyword Aggregation Algorithm

Keywords are collected from multiple sources and deduplicated:

1. **Plugin name** — Both hyphenated (`aws-ops-plugin`) and spaced (`aws ops plugin`)
2. **Agent descriptions** — Extract quoted strings from `Triggers on "..." requests` patterns
3. **Skill triggers** — All entries from `triggers:` arrays
4. **CLAUDE.md tables** — Quoted strings from keyword columns in routing tables
5. **Deduplication** — Case-preserving set, sorted alphabetically
6. **Filtering** — Remove entries shorter than 2 characters or longer than 50 characters

### POWER.md Template

```yaml
---
name: <plugin-name>
displayName: <Plugin Name Title Case>
description: "<plugin description from plugin.json>"
keywords:
  - "<keyword1>"
  - "<keyword2>"
---

# <Plugin Name Title Case>

<plugin description>
```

### Display Name Generation

- Replace hyphens with spaces
- Apply title case
- Example: `aws-ops-plugin` → `Aws Ops Plugin`

---

## Edge Cases

### Large Asset Directories (>10MB)

**Problem:** Some plugins contain large asset directories (e.g., `icons/` with 4,224 files).

**Solution:**
1. Detect directories exceeding 10MB threshold
2. Generate `scripts/download-assets.sh` with copy instructions
3. Add directory name to `.gitignore`
4. Do NOT copy the large directory into the power output

### Bilingual Keywords (Korean/English)

**Problem:** Plugins may have keywords in both Korean and English.

**Solution:** Include all language variants in the `keywords` array. Kiro's matching is language-agnostic.

### Opus Model Agents

**Problem:** Kiro does not have a `model` field in steering files.

**Solution:**
1. Remove the `model` field
2. Append `(Advanced reasoning)` to the description
3. This signals to Kiro that the steering may benefit from advanced model routing

### Script Dependencies

**Problem:** Plugins may contain scripts (Python, Bash) that are part of the workflow.

**Solution:**
1. Copy scripts to the power output if they are referenced by steering files
2. Update path references from `{plugin-dir}/...` to power-relative paths
3. Note any external dependencies in the POWER.md body

### Nested Path References

**Problem:** Agent/skill files may reference paths like `{plugin-dir}/skills/ops-troubleshoot/references/commands.md`.

**Solution:**
1. Replace `{plugin-dir}/skills/<skill>/references/<file>.md` with `steering/ref-<skill>-<file>.md`
2. Replace `{plugin-dir}/agents/<agent>.md` with `steering/<agent>.md`
3. Replace `{plugin-dir}/CLAUDE.md` with `steering/routing.md`

### Missing .mcp.json

**Problem:** Not all plugins have MCP server configurations.

**Solution:** Skip `mcp.json` generation entirely. The POWER.md body should note that no MCP servers are required.

### Multiple Plugins in One Repository

**Problem:** A git repository may contain multiple plugins in subdirectories.

**Solution:** Use `--plugin-path` to specify the subdirectory containing the target plugin. The converter validates that `.claude-plugin/plugin.json` exists at the specified path.
