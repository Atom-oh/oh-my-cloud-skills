# Kiro Power Format Reference

Kiro Powers are modular capability packages for the Kiro IDE. They bundle knowledge, MCP integrations, and steering guidance into a single installable unit with progressive, on-demand context loading.

---

## Directory Structure

```
<power-name>/
├── POWER.md          # Power manifest (required)
├── mcp.json          # MCP server configuration (optional)
└── steering/         # Steering files directory (optional)
    ├── routing.md    # Always-loaded routing/context (inclusion: always)
    ├── <agent>.md    # Auto-activated agent steering (inclusion: auto)
    ├── <skill>.md    # Auto-activated skill steering (inclusion: auto)
    ├── <pattern>.md  # File-pattern-activated steering (inclusion: fileMatch)
    └── ref-*.md      # Manually-included references (inclusion: manual)
```

### Three Structure Patterns

| Pattern | When to Use | Structure |
|---------|-------------|-----------|
| **Simple** | Small power (<500 lines total) | Everything in POWER.md, no steering/ |
| **Multi-Workflow** | Multiple distinct workflows | POWER.md + steering/ with separate workflow files |
| **Knowledge Base** | Documentation-only, no MCP | POWER.md + steering/ with reference files only |

### Two Power Types

| Type | Has mcp.json | Description |
|------|-------------|-------------|
| **Guided MCP** | Yes | MCP tool connections + workflow documentation |
| **Knowledge Base** | No | Pure documentation and guidance |

---

## POWER.md Specification

The `POWER.md` file serves as the power manifest. It uses YAML frontmatter followed by a markdown body.

### Frontmatter Fields

```yaml
---
name: power-name                    # Required. kebab-case, must match directory name
displayName: Power Display Name     # Required. Human-readable name (Title Case)
description: "Brief description"    # Required. What the power does (max ~3 sentences)
keywords:                           # Required. Discovery and activation keywords
  - "keyword1"
  - "keyword2"
  - "한국어키워드"
author: Author Name                 # Optional. Creator identification
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique kebab-case identifier, must match directory name |
| `displayName` | Yes | Human-readable display name |
| `description` | Yes | One-line description of the power's purpose |
| `keywords` | Yes | Array of trigger keywords for discovery and auto-activation |
| `author` | No | Power author name or organization |

**Invalid fields** (do NOT use): `version`, `tags`, `repository`, `license` — these are not part of the schema.

### Body Sections

The markdown body has two key sections:

#### 1. Onboarding Section

Runs once when the power first activates. Used for initial setup validation.

```markdown
# Onboarding

Before using this power, ensure:
1. The MCP server is configured (`mcp.json`)
2. Required CLI tools are installed: `aws`, `kubectl`
3. Environment variables are set: `AWS_REGION`, `KUBECONFIG`
```

#### 2. Steering Mappings Section

Maps user workflows to steering files. This tells Kiro which steering file to load for each type of task.

```markdown
# When to Load Steering Files

- Setting up infrastructure → `infra-setup.md`
- Troubleshooting cluster issues → `troubleshooting.md`
- Reviewing security configuration → `security-audit.md`
- Working with Terraform files → `terraform-patterns.md`
```

---

## Steering Files

Steering files guide Kiro's AI behavior. Each is a markdown file with YAML frontmatter specifying activation rules.

### Inclusion Types

| Type | Behavior | Use Case |
|------|----------|----------|
| `always` | Loaded into every conversation | Routing rules, global context |
| `auto` | Loaded when description keywords match user input | Agent behaviors, skill workflows |
| `fileMatch` | Loaded when working with matching file patterns | File-type-specific guidance (CSS, Terraform, etc.) |
| `manual` | Only loaded when explicitly referenced via `#name` in chat | Reference documentation, detailed specs |

### Steering Frontmatter Examples

**Always (routing):**
```yaml
---
name: routing
inclusion: always
---
```

**Auto (agent/skill):**
```yaml
---
name: eks-agent
description: "EKS cluster operations, troubleshooting, and management"
inclusion: auto
---
```

**FileMatch (file-type-specific):**
```yaml
---
name: terraform-patterns
description: "Terraform coding patterns and best practices"
inclusion: fileMatch
globs:
  - "**/*.tf"
  - "**/*.tfvars"
---
```

**Manual (reference):**
```yaml
---
name: ref-ops-commands
inclusion: manual
---
```

### Key Rules

- `auto` inclusion uses the `description` field for keyword matching — include relevant trigger words
- `fileMatch` requires the `globs` field with glob patterns (array)
- `manual` files are loaded only when the user types `#file-name` in chat
- `always` files should be kept small — they load in every conversation

---

## mcp.json Format

The `mcp.json` file configures MCP (Model Context Protocol) servers.

### Structure

```json
{
  "mcpServers": {
    "server-name": {
      <server-config>,
      "autoApprove": [],
      "disabled": false,
      "disabledTools": []
    }
  }
}
```

### Server Types

**Command-based (stdio):**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["package-name@latest"],
      "timeout": 120000,
      "env": {
        "API_KEY": "${MY_API_KEY}",
        "DEBUG": "true"
      },
      "autoApprove": [],
      "disabled": false,
      "disabledTools": []
    }
  }
}
```

**URL-based (HTTP/SSE):**
```json
{
  "mcpServers": {
    "my-server": {
      "url": "https://mcp.example.com/sse",
      "headers": {
        "Authorization": "Bearer ${TOKEN}"
      },
      "autoApprove": ["*"],
      "disabled": false,
      "disabledTools": []
    }
  }
}
```

### Fields Reference

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `command` | One of command/url | — | Executable command (stdio server) |
| `url` | One of command/url | — | Server endpoint URL (HTTP/SSE server) |
| `args` | No | `[]` | Command arguments (command-based only) |
| `timeout` | No | — | Connection timeout in milliseconds |
| `env` | No | `{}` | Environment variables (`${VAR}` syntax for secrets) |
| `headers` | No | `{}` | HTTP headers (url-based only, `${VAR}` syntax supported) |
| `autoApprove` | Yes | `[]` | Tool names that skip user confirmation (`["*"]` for all) |
| `disabled` | Yes | `false` | Whether the server is disabled |
| `disabledTools` | No | `[]` | Specific tools to disable on this server |

**Key differences from Claude Code `.mcp.json`:**
- No `type` field — server type inferred from `command` vs `url`
- `disabledTools` field for selective tool disabling
- `headers` field for remote server authentication
- Environment variables use `${VAR}` syntax (resolved from system env)

### Server Name Namespacing

When powers are installed, server names are auto-prefixed: `stripe` in power `my-power` becomes `power-my-power-stripe` at the system level. This avoids naming conflicts across powers.

---

## Skills Format

Kiro supports standalone skills at `.kiro/skills/*/SKILL.md` (separate from powers).

### Structure

```
my-skill/
├── SKILL.md           # Required entry point
├── scripts/           # Optional executable code
├── references/        # Optional documentation
└── assets/            # Optional templates/resources
```

### SKILL.md Frontmatter

```yaml
---
name: pr-review
description: "Review pull requests for code quality, security, and test coverage"
license: MIT
compatibility: "Requires git CLI"
metadata:
  author: "Team Name"
  version: "1.0"
---
```

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | Lowercase + numbers + hyphens, max 64 chars, must match folder name |
| `description` | Yes | Max 1024 chars, used for activation matching |
| `license` | No | License name or file reference |
| `compatibility` | No | Environment requirements description |
| `metadata` | No | Arbitrary key-value pairs (author, version, etc.) |

### Installation Paths

| Scope | Path |
|-------|------|
| Workspace | `.kiro/skills/<skill-name>/` |
| Global | `~/.kiro/skills/<skill-name>/` |

### Progressive Disclosure

Skills use a 3-stage loading model:
1. **Discovery** — Only `name` and `description` are loaded at startup
2. **Activation** — Full SKILL.md content loaded when description matches user input
3. **On-demand** — Scripts and references loaded only when explicitly needed

---

## Hooks Format

Kiro hooks are JSON files in `.kiro/hooks/` with the `.kiro.hook` extension.

### Structure

```json
{
  "enabled": true,
  "name": "Hook Name",
  "description": "What this hook does",
  "version": "1",
  "when": {
    "type": "<trigger-type>",
    "patterns": ["glob/patterns/**/*.ts"]
  },
  "then": {
    "type": "<action-type>",
    "prompt": "Instructions for the agent..."
  }
}
```

### Trigger Types (`when.type`)

| Type | Description | Extra Fields |
|------|-------------|--------------|
| `promptSubmit` | User submits a prompt | — |
| `agentStop` | Agent finishes responding | — |
| `preToolUse` | Before agent invokes a tool | `toolName` (string, supports categories/regex) |
| `postToolUse` | After agent invokes a tool | `toolName` (string, supports categories/regex) |
| `fileCreated` | New file is created | `patterns` (glob array) |
| `fileSave` | File is saved | `patterns` or `filePattern` (glob) |
| `fileDeleted` | File is deleted | `patterns` (glob array) |
| `preTaskExecution` | Before a spec task starts | — |
| `postTaskExecution` | After a spec task completes | — |
| `userTriggered` | Manual trigger by user | — |

**Tool name filtering** (preToolUse/postToolUse): Supports tool names, categories (`read`, `write`, `shell`, `web`, `spec`, `*`), prefixes (`@mcp`, `@powers`, `@builtin`), and regex patterns.

### Action Types (`then.type`)

| Type | Description | Cost |
|------|-------------|------|
| `askAgent` | Send prompt to AI agent | Consumes credits |
| `runCommand` | Execute shell command | No credits |

**runCommand behavior:**
- Exit code 0 → success (stdout added to agent context)
- Exit code non-zero → error (stderr sent to agent)
- For `preToolUse`: exit code 2 → **blocks** the tool execution
- Default timeout: 60 seconds (set `0` to disable)

### Hook File Location

| Scope | Path |
|-------|------|
| Workspace | `.kiro/hooks/<name>.kiro.hook` |

---

## Agents Format

Kiro supports two agent definition formats:

### IDE Subagents (`.kiro/agents/*.md`)

```yaml
---
name: code-reviewer
description: "Expert code review assistant"
tools: ["@builtin", "@context7"]
model: claude-sonnet-4-6
includeMcpJson: true
includePowers: true
---

System prompt and instructions here.
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | Yes | Filename | Agent identifier |
| `description` | No | — | Agent purpose description |
| `tools` | No | No tools | Tool access list |
| `model` | No | Chat LLM | Model override |
| `includeMcpJson` | No | `false` | Include MCP server tools |
| `includePowers` | No | `false` | Include power tools |

**Tool identifiers:** `read`, `write`, `shell`, `web`, `spec`, `@builtin`, `@<server>`, `@<server>/<tool>`, `*`

### CLI Custom Agents (`.kiro/agents/*.json`)

```json
{
  "name": "my-agent",
  "description": "Agent description",
  "prompt": "System prompt",
  "tools": ["read", "write", "@git"],
  "allowedTools": ["read", "@server/*"],
  "resources": ["file://README.md", "skill://.kiro/skills/**/SKILL.md"],
  "mcpServers": { "server": { "command": "npx", "args": ["pkg"] } },
  "hooks": {
    "agentSpawn": [{"command": "echo init"}],
    "preToolUse": [{"command": "validate.sh", "matcher": "write"}],
    "postToolUse": [{"command": "audit.sh"}],
    "stop": [{"command": "cleanup.sh"}]
  },
  "model": "claude-sonnet-4-6",
  "includeMcpJson": true,
  "keyboardShortcut": "ctrl+r",
  "welcomeMessage": "Hello!"
}
```

### Agent Installation Paths

| Scope | Path | Priority |
|-------|------|----------|
| Workspace | `.kiro/agents/` | Higher (overrides global) |
| Global | `~/.kiro/agents/` | Lower |

---

## Installation Paths

| Scope | Path | Behavior |
|-------|------|----------|
| Global | `~/.kiro/powers/<power-name>/` | Available in all Kiro projects |
| Project | `.kiro/powers/<power-name>/` | Available only in the current project |

---

## Power Activation Lifecycle

Powers follow a 6-stage progressive activation model:

1. **Discovery** — Keywords from POWER.md frontmatter evaluated against conversation
2. **Activation** — Full POWER.md content + steering file list loaded
3. **Learning** — Agent reads documentation, understands workflows
4. **Steering** — Specific steering files loaded on-demand based on task
5. **Tool Use** — MCP server tools invoked as needed
6. **Iteration** — Stages 4-5 repeat until task completion

**Key properties:**
- **Zero baseline context** — Installed but inactive powers consume no tokens
- **Auto-deactivation** — Switching topics unloads irrelevant powers
- **Progressive disclosure** — Metadata first, full content on demand

---

## Configuration Precedence

From highest to lowest priority:

1. **Power-specific** — `power-name/mcp.json`, `power-name/steering/`
2. **Workspace** — `.kiro/settings/mcp.json`, `.kiro/steering/`
3. **User (global)** — `~/.kiro/settings/mcp.json`, `~/.kiro/steering/`
4. **System** — `~/.kiro/powers.mcp.json` (auto-generated, read-only)

---

## Comparison with Claude Code Plugins

| Aspect | Claude Code Plugin | Kiro Power |
|--------|-------------------|------------|
| Manifest | `.claude-plugin/plugin.json` (JSON) | `POWER.md` (YAML frontmatter + markdown) |
| Agent format | `agents/*.md` (tools/model in frontmatter) | `steering/*.md` (inclusion modes) or `.kiro/agents/*.md` |
| Skill format | `skills/*/SKILL.md` (triggers array) | `steering/*.md` (description matching) or `.kiro/skills/*/SKILL.md` |
| MCP config | `.mcp.json` (with `type` field) | `mcp.json` (no `type`, has `disabledTools`) |
| Hooks | `hooks` in plugin.json (3 events) | `.kiro/hooks/*.kiro.hook` (10 trigger types) |
| Global install | `~/.claude/plugins/` | `~/.kiro/powers/` |
| Project install | `.claude/plugins/` | `.kiro/powers/` |
| Activation | Always loaded (keyword routing via CLAUDE.md) | Progressive: keyword → on-demand → auto-deactivation |
| Context loading | All plugin context loaded at once | Progressive disclosure (discovery → activation → steering) |
| Custom instructions | `CLAUDE.md` | `.kiro/steering/*.md` with inclusion modes + `AGENTS.md` |
