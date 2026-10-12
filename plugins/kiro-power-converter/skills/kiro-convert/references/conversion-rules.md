# Conversion Rules Reference

Detailed field-by-field conversion rules for transforming Claude Code plugins into Kiro Power format.

## Output Safety and Recovery

Conversion and installation refuse equal paths, either containment direction, and
symlink aliases between a source and destination. Symlinks anywhere in the
output path, filesystem roots and their top-level directories, the home/current/
temporary directory itself, and Kiro configuration/power container roots are also
refused. Select a distinct child directory or a standalone output file. Names in
source metadata must be single path components.

A full power output or installation target may be absent, empty, or an existing
power export containing `POWER.md`. Nonempty unrelated directories are refused.
Preserved-skill conversion replaces only that skill's output tree; standalone
conversion replaces only its requested file. A repeated `--skill` request uses one
output directory, rejects duplicate skill names, and retains unrelated existing
files there. `--target` and `--preserve-skills` apply to full plugin conversion.

Safe publication requires POSIX `dir_fd` operations, `O_NOFOLLOW`, and a
kernel-backed `/proc/self/fd` or `/dev/fd` directory path. Missing filesystem
capabilities fail before output mutation rather than falling back to path-only
replacement. No additional Python package is needed.

The converter securely opens each parent component without following symlinks,
retains directory descriptors, and builds in private sibling temporary storage
through a descriptor-backed path. Export and installation are staged together.
Rename, rollback and recursive cleanup use those retained descriptors and check
entry identities. Before build/copy, each destination's absence or identity and
subtree content is captured without following links. Publication rechecks that
snapshot and refuses a destination created, replaced or edited during the build,
preserving the new content. Standalone folder copies use the same preflight
snapshot so files added after copying cannot be silently discarded.
These checks detect build-time changes; they do not lock out every malicious
writer racing the final rename window. Parent replacement during a run cannot
redirect descriptor-based writes or cleanup into an outside directory; a changed
parent path aborts publication. A conversion, copy,
or publication failure returns nonzero and preserves the previous destinations
and input. Publication errors roll back prior replacements. If an operating-system
error also prevents rollback, retain the `.kiro-backup-*` directory for manual
recovery rather than deleting the previous content. The procedure does not add an
interactive confirmation or grant target hook trust. After successful publication,
cleanup errors are reported as retained temporary-directory warnings; cleanup does
not follow a replaced directory link or turn a committed valid output into a
conversion failure.

## Scalar Encoding

Generated string metadata uses a shared JSON-quoted scalar serializer, which is
valid YAML and preserves quotes, colons, backslashes, Unicode and line breaks.
It applies to agent steering, skill steering, preserved skills, standalone files,
reference metadata and `POWER.md`, including author/version and keyword fields.
Trigger text is merged before serialization rather than pre-escaped. The source
reader supports plain and quoted string scalars, literal/folded block descriptions,
and simple lists without adding a third-party YAML dependency.

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
SessionStart hooks with `type: prompt` become part of POWER.md onboarding section.
They are static instructions, not session-start execution. SessionStart command
handlers remain explicit manual gaps; no `promptSubmit` approximation is generated
because its execution timing would change the handler's meaning.

Every input handler has an indexed status in `conversion-report.json`, the CLI
summary and POWER.md's Hook Conversion Coverage section: `generated`, `onboarding`,
or `manual`. Unsupported events/actions remain visible. Malformed hook structures
fail conversion instead of silently dropping handlers. Command/prompt actions must
contain a nonempty string; an empty action is never reported as generated. Generated hook filenames
include matcher/handler indices so tool-category aliases cannot overwrite another
handler. A generated mapping still requires checking Kiro support, command paths,
payload compatibility and target trust before activation.

### Hook Event Mapping

| Claude Code Event | Kiro Trigger Type | Notes |
|-------------------|-------------------|-------|
| `PreToolUse` | `preToolUse` | `matcher` → `toolName` field |
| `PostToolUse` | `postToolUse` | `matcher` → `toolName` field |
| `SessionStart` | — | Prompt becomes onboarding text only; command remains a manual gap |
| `Stop` | — | Manual gap recorded; no executable target hook generated |
| `Notification` | — | Manual gap recorded; no executable target hook generated |

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

## Manifest / .mcp.json → mcp.json Conversion

The converter reads inline manifest `mcpServers`, a plugin-relative manifest MCP
configuration path, and standalone `.mcp.json`. It merges server names in a
deterministic order. When the same name has different declarations, `.mcp.json`
replaces the entire inline server declaration; the server name is warned and
recorded in `conversion-report.json` as an `mcp_conflicts` entry. Identical duplicate
declarations need no warning. An invalid declaration fails without replacing
existing output. Inline AWS Content Playwright configuration is retained.

### Per-Server Rules

| Field | Action | Details |
|-------|--------|---------|
| `type` | Remove | Kiro infers type from `command` vs `url` presence |
| `command` | Keep | Unchanged |
| `url` | Keep | Unchanged |
| `args` | Keep | Unchanged |
| `timeout` | Keep | Unchanged |
| `env` | Keep/Convert | Unchanged; note `${VAR}` syntax for secrets |
| `headers` | Keep/Convert | Preserve placeholder references; replace detected literal credentials |
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

**Detection heuristic:** Secret-shaped values and credential-bearing key names
become `${KEY_NAME}`. Header placeholder names use uppercase underscores. Existing
`${EXISTING_NAME}` and scheme-prefixed templates such as `Bearer ${EXISTING_NAME}`
and `Basic ${EXISTING_NAME}` are retained, including
references whose name differs from the configuration key. Required variable names
are collected from the resulting server configuration, deduplicated and sorted;
reports contain names without printing credential values.

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

**Solution:** Check the manifest's inline/path declarations as well. Skip `mcp.json`
only when all supported sources contain no servers; an absent standalone file does
not mean that the plugin has no MCP configuration.

### Multiple Plugins in One Repository

**Problem:** A git repository may contain multiple plugins in subdirectories.

**Solution:** Use `--plugin-path` to specify the subdirectory containing the target plugin.

### Hooks with No Kiro Equivalent

**Problem:** Claude Code `SessionStart` hooks have no direct Kiro equivalent.

**Solution:**
- `type: prompt` hooks → Include static content in POWER.md onboarding and report `onboarding`; no session execution is claimed.
- `type: command` hooks → Report `manual` with the original indexed handler. Generate no approximation and do not claim migration or execution.

### Environment Secrets in MCP Config

**Problem:** Claude Code `.mcp.json` may contain hardcoded secrets.

**Solution:** Detect potential secrets using pattern matching and convert to `${VAR}` syntax. Add setup instructions to POWER.md onboarding section listing required environment variables.
