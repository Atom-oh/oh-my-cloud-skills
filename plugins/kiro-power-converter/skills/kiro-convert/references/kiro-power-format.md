# Kiro Power Format Reference

Kiro Powers are modular capability packages for the Kiro IDE, similar in concept to Claude Code plugins but with a different structure and configuration format.

---

## Directory Structure

```
<power-name>/
├── POWER.md          # Power manifest (required)
├── mcp.json          # MCP server configuration (optional)
└── steering/         # Steering files directory (required)
    ├── routing.md    # Always-loaded routing/context (inclusion: always)
    ├── <agent>.md    # Auto-activated agent steering (inclusion: auto)
    ├── <skill>.md    # Auto-activated skill steering (inclusion: auto)
    └── ref-*.md      # Manually-included references (inclusion: manual)
```

---

## POWER.md Specification

The `POWER.md` file serves as the power manifest. It uses YAML frontmatter followed by a markdown body.

### Frontmatter Fields

```yaml
---
name: power-name                    # Required. kebab-case identifier
displayName: Power Display Name     # Required. Human-readable name
description: "Brief description"    # Required. What the power does
keywords:                           # Required. Discovery and activation keywords
  - "keyword1"
  - "keyword2"
  - "한국어키워드"
---
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique kebab-case identifier |
| `displayName` | Yes | Human-readable display name |
| `description` | Yes | One-line description of the power's purpose |
| `keywords` | Yes | Array of trigger keywords for discovery and auto-activation |

### Body

The markdown body provides an overview of the power, its capabilities, and usage instructions. This content is shown in the Kiro powers panel.

---

## Steering Files

Steering files guide Kiro's AI behavior. Each is a markdown file with YAML frontmatter specifying activation rules.

### Inclusion Types

| Type | Behavior | Use Case |
|------|----------|----------|
| `always` | Loaded into every conversation | Routing rules, global context |
| `auto` | Loaded when content matches keywords in description | Agent behaviors, skill workflows |
| `fileMatch` | Loaded when working with matching file patterns | File-type-specific guidance |
| `manual` | Only loaded when explicitly referenced | Reference documentation, detailed specs |

### Steering Frontmatter

```yaml
---
name: steering-file-name     # Required. Identifier
description: "What this does" # Optional. Used for auto-matching
inclusion: auto               # Required. One of: always, auto, fileMatch, manual
globs:                        # Required if inclusion: fileMatch
  - "*.py"
  - "src/**/*.ts"
---
```

### Steering Body

The markdown body contains the actual guidance content — instructions, rules, examples, decision trees, etc. There is no restriction on markdown features used in the body.

---

## mcp.json Format

The `mcp.json` file configures MCP (Model Context Protocol) servers that the power requires.

### Structure

```json
{
  "mcpServers": {
    "server-name": {
      <server-config>,
      "autoApprove": [],
      "disabled": false
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
      "env": { "API_KEY": "..." },
      "autoApprove": [],
      "disabled": false
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
      "autoApprove": [],
      "disabled": false
    }
  }
}
```

### Required Fields

| Field | Description |
|-------|-------------|
| `command` or `url` | Server connection method (one required) |
| `autoApprove` | Array of tool names that skip user confirmation (default: `[]`) |
| `disabled` | Whether the server is disabled (default: `false`) |

### Optional Fields

| Field | Description |
|-------|-------------|
| `args` | Command arguments (for command-based servers) |
| `timeout` | Connection timeout in milliseconds |
| `env` | Environment variables for the server process |

**Note:** Kiro `mcp.json` does NOT have a `type` field. The server type is inferred from whether `command` or `url` is present.

---

## Installation Paths

| Scope | Path | Behavior |
|-------|------|----------|
| Global | `~/.kiro/powers/<power-name>/` | Available in all Kiro projects |
| Project | `.kiro/powers/<power-name>/` | Available only in the current project |

### Installing from GitHub

Powers can be imported directly from GitHub repositories using the "Add to Kiro" button or by cloning and copying to the appropriate installation path.

---

## Comparison with Claude Code Plugins

| Aspect | Claude Code Plugin | Kiro Power |
|--------|-------------------|------------|
| Manifest | `.claude-plugin/plugin.json` | `POWER.md` |
| Agent format | `agents/*.md` (with tools/model) | `steering/*.md` (with inclusion) |
| Skill format | `skills/*/SKILL.md` (with triggers) | `steering/*.md` (triggers in description) |
| MCP config | `.mcp.json` (with type field) | `mcp.json` (no type field) |
| Global install | `~/.claude/plugins/` | `~/.kiro/powers/` |
| Project install | `.claude/plugins/` | `.kiro/powers/` |
| Activation | Keywords in description field | `inclusion` type in frontmatter |
