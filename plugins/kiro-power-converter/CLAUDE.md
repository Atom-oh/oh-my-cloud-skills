# Kiro Power Converter — Claude Code Configuration

Converts Claude Code plugins to Kiro Power format. Supports multiple input sources (GitHub URL, local path, marketplace, individual skills) and output targets (global, project, export).

---

## Auto-Invocation Rules

When the following keywords are detected, automatically invoke the corresponding agent.

### Plugin Conversion

| Keywords | Agent | Description |
|----------|-------|-------------|
| "convert to kiro", "kiro power", "kiro convert", "export to kiro", "키로 변환", "키로 파워", "claude to kiro" | `kiro-converter-agent` | Convert a Claude Code plugin to Kiro Power format |
| "install kiro power", "kiro install", "키로 설치", "키로 파워 설치" | `kiro-converter-agent` | Convert and install as a Kiro Power |

---

## Agents

| Agent | Purpose |
|-------|---------|
| `kiro-converter-agent` | Converts Claude Code plugin structure to Kiro Power format |

## Skills

| Skill | Purpose |
|-------|---------|
| `kiro-convert` | Interactive workflow for plugin-to-power conversion |

---

## Workflow

```
User request → Source detection (git/local/marketplace/skill)
             → Validation → Parsing → Conversion → Target selection
             → Installation or export → Verification report
```
