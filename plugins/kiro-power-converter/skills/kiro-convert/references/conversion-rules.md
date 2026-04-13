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
model: opus
---
```

### Output (Kiro Steering)

```yaml
---
name: eks-agent
description: "EKS cluster operations... Triggers on \"keyword1\", \"keyword2\" requests. (Advanced reasoning)"
inclusion: auto
---
```

### Rules

| Field | Action | Details |
|-------|--------|---------|
| `name` | Keep | Unchanged |
| `description` | Keep/Modify | If model was `opus`, append `(Advanced reasoning)` |
| `tools` | Remove | Kiro determines tool access from context |
| `model` | Remove | Kiro steering has no model field; note capability level in description |
| `skills` | Remove | Referenced skills are converted separately |
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
model: sonnet
allowed-tools:
  - Read
  - Bash
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
| `model` | Remove | No model field in steering |
| `allowed-tools` | Remove | Tools determined by context |
| — | Add `inclusion: auto` | Steering activates based on description match |

### Alternative: Preserve as Kiro Skill

When `--preserve-skills` is used, skills are output as `.kiro/skills/` instead of steering:

```yaml
---
name: ops-troubleshoot
description: "Systematic troubleshooting workflow. Triggers: \"troubleshoot\", \"장애 대응\""
metadata:
  author: "<plugin-author>"
  version: "<plugin-version>"
---
```

Output path: `.kiro/skills/<skill-name>/SKILL.md` with `references/` and `scripts/` preserved.

---

## Reference File Conversion

### Input

Plain markdown files at `skills/<skill>/references/<name>.md` with no frontmatter.

### Output (Default: manual inclusion)

```yaml
---
name: ref-<skill>-<name>
inclusion: manual
---

<original content>
```

### Output (File-pattern match)

When reference content is specific to certain file types, use `fileMatch` instead:

```yaml
---
name: ref-<skill>-<name>
description: "Terraform patterns and best practices"
inclusion: fileMatch
globs:
  - "**/*.tf"
  - "**/*.tfvars"
---

<original content>
```

### fileMatch Detection Heuristic

Apply `fileMatch` inclusion when the reference file name or content strongly implies a file type:

| Reference Name Pattern | Detected Globs |
|-----------------------|---------------|
| `*terraform*`, `*tf-*` | `["**/*.tf", "**/*.tfvars"]` |
| `*python*`, `*py-*` | `["**/*.py"]` |
| `*typescript*`, `*ts-*` | `["**/*.ts", "**/*.tsx"]` |
| `*css*`, `*style*` | `["**/*.css", "**/*.scss"]` |
| `*docker*`, `*container*` | `["**/Dockerfile*", "**/docker-compose*.yml"]` |
| `*k8s*`, `*kubernetes*` | `["**/*.yaml", "**/*.yml"]` |
| `*sql*`, `*database*` | `["**/*.sql"]` |

Default: `inclusion: manual` when no file-type pattern is detected.

### Rules

- Add YAML frontmatter with `name` and `inclusion`
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
- Keep content concise — `always` files load in every interaction

---

## Hooks Conversion

### Input (Claude Code plugin.json)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "node /path/to/check.js"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Plugin loaded. Welcome."
          }
        ]
      }
    ]
  }
}
```

### Output (Kiro .kiro.hook files)

**PostToolUse → postToolUse:**
```json
{
  "enabled": true,
  "name": "post-bash-check",
  "description": "Checks Bash output for errors after execution",
  "version": "1",
  "when": {
    "type": "postToolUse",
    "toolName": "shell"
  },
  "then": {
    "type": "runCommand",
    "command": "node /path/to/check.js"
  }
}
```

**SessionStart → prompt (no direct equivalent):**
SessionStart hooks with `type: prompt` become part of POWER.md onboarding section instead.

### Hook Event Mapping

| Claude Code Event | Kiro Trigger Type | Notes |
|-------------------|-------------------|-------|
| `PreToolUse` | `preToolUse` | `matcher` → `toolName` field |
| `PostToolUse` | `postToolUse` | `matcher` → `toolName` field |
| `SessionStart` | — | No direct equivalent; content goes into POWER.md onboarding |

### Hook Matcher Conversion

| Claude Matcher | Kiro toolName | Notes |
|---------------|---------------|-------|
| `Bash` | `shell` | Kiro uses category names |
| `Read` | `read` | |
| `Write`, `Edit` | `write` | Combined in Kiro |
| `Glob`, `Grep` | `read` | File search = read category |
| `*` (wildcard) | `*` | Match all tools |
| `AskUserQuestion` | `@builtin/askUser` | Specific tool reference |

### Hook Action Mapping

| Claude Hook Type | Kiro Action Type | Notes |
|-----------------|-----------------|-------|
| `type: command` | `runCommand` | Direct mapping, command preserved |
| `type: prompt` | `askAgent` | Prompt text → `prompt` field |

### Output Path

Each hook becomes a separate file: `.kiro/hooks/<name>.kiro.hook`

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
| `env` | Keep/Convert | Unchanged; note `${VAR}` syntax for secrets |
| `headers` | Keep | For URL-based servers (pass through if present) |
| `autoApprove` | Add if missing | Default: `[]` (empty array) |
| `disabled` | Add if missing | Default: `false` |
| `disabledTools` | Add if missing | Default: `[]` (empty array) |

### Environment Variable Syntax

Claude Code uses bare values; Kiro supports `${VAR}` for system environment variable resolution:

```json
// Claude Code
"env": { "API_KEY": "hardcoded-value" }

// Kiro (if value looks like a token/secret, convert to ${VAR})
"env": { "API_KEY": "${API_KEY}" }
```

**Detection heuristic:** If an env value matches `^(xoxb-|sk-|ghp_|AKIA)` or the key name contains `SECRET`, `TOKEN`, `KEY`, `PASSWORD`, convert to `${KEY_NAME}` syntax.

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
author: <plugin-author>
---

# <Plugin Name Title Case>

<plugin description>

## Onboarding

<setup instructions if MCP servers require configuration>

## When to Load Steering Files

<workflow → steering file mapping>
```

### Display Name Generation

- Replace hyphens with spaces
- Apply title case
- Example: `aws-ops-plugin` → `Aws Ops Plugin`

### Author Field

Extracted from `plugin.json` → `author.name` or `author` (if string). Omitted if not present in source.

### Body Generation Rules

The POWER.md body is generated with structured sections:

1. **Header** — `# {displayName}` + plugin description
2. **Onboarding** — Generated from:
   - MCP server requirements (list configured servers and their env vars)
   - Script dependencies (Python, Node.js requirements found in skills)
   - SessionStart hook prompts (migrated here since Kiro has no SessionStart event)
3. **Steering Mappings** — Generated from:
   - Agent descriptions → `Agent workflow → steering/{agent}.md`
   - Skill descriptions → `Skill workflow → steering/{skill}.md`
   - Reference files → `Detailed reference → steering/ref-{name}.md`

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

**Problem:** Kiro steering files do not have a `model` field.

**Solution:**
1. Remove the `model` field
2. Append `(Advanced reasoning)` to the description
3. This signals to Kiro that the steering may benefit from advanced model routing

### Script Dependencies

**Problem:** Plugins may contain scripts (Python, Bash) that are part of the workflow.

**Solution:**
1. Copy scripts to the power output if they are referenced by steering files
2. Update path references from `{plugin-dir}/...` to power-relative paths
3. Note any external dependencies in the POWER.md onboarding section

### Nested Path References

**Problem:** Agent/skill files may reference paths like `{plugin-dir}/skills/ops-troubleshoot/references/commands.md`.

**Solution:**
1. Replace `{plugin-dir}/skills/<skill>/references/<file>.md` with `steering/ref-<skill>-<file>.md`
2. Replace `{plugin-dir}/agents/<agent>.md` with `steering/<agent>.md`
3. Replace `{plugin-dir}/CLAUDE.md` with `steering/routing.md`

### Missing .mcp.json

**Problem:** Not all plugins have MCP server configurations.

**Solution:** Skip `mcp.json` generation entirely. The POWER.md body notes that no MCP servers are required.

### Multiple Plugins in One Repository

**Problem:** A git repository may contain multiple plugins in subdirectories.

**Solution:** Use `--plugin-path` to specify the subdirectory containing the target plugin.

### Hooks with No Kiro Equivalent

**Problem:** Claude Code `SessionStart` hooks have no direct Kiro equivalent.

**Solution:**
- `type: prompt` hooks → Migrate content to POWER.md onboarding section
- `type: command` hooks → Create `promptSubmit` hook as closest approximation, with `enabled: false` and a comment noting the original trigger

### Environment Secrets in MCP Config

**Problem:** Claude Code `.mcp.json` may contain hardcoded secrets.

**Solution:** Detect potential secrets using pattern matching and convert to `${VAR}` syntax. Add setup instructions to POWER.md onboarding section listing required environment variables.
