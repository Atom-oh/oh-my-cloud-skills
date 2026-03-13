# Kiro Power Converter — Claude Code Configuration

Converts Claude Code plugins to Kiro Power format. Supports multiple input sources (GitHub URL, local path, marketplace, individual skills) and output targets (global, project, export).

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
