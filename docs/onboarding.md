# Onboarding Guide

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for Docusaurus docs site)
- Claude Code CLI (`claude`)
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/Atom-oh/oh-my-cloud-skills.git
cd oh-my-cloud-skills

# Load a plugin locally for testing
claude --plugin-dir ./plugins/aws-content-plugin
claude --plugin-dir ./plugins/aws-ops-plugin

# Build the docs site
cd docs && npm install && npm run build
```

### Verify

```bash
# Validate plugin manifests
python3 scripts/test-plugins.py

# Check version consistency
python3 -c "
import json
V1 = json.load(open('plugins/aws-content-plugin/.claude-plugin/plugin.json'))['version']
V2 = json.load(open('plugins/aws-ops-plugin/.claude-plugin/plugin.json'))['version']
print(f'content={V1} ops={V2} match={V1==V2}')
"
```

## Project Overview

This is a Claude Code plugin marketplace with 3 plugins:

| Plugin | Purpose | Agents | Skills |
|--------|---------|--------|--------|
| aws-content-plugin | Content creation | 8 | 5 |
| aws-ops-plugin | Infrastructure ops | 9 | 5 |
| kiro-power-converter | Format conversion | 1 | 1 |

## Development Workflow

1. Make changes to plugin agents/skills
2. Test locally: `claude --plugin-dir ./plugins/<plugin>`
3. Run eval: `python3 scripts/eval-skills.py`
4. Bump version in all `plugin.json` + `marketplace.json`
5. Commit, tag, push, release

## Key Concepts

- **Agents** (`.md` files): YAML frontmatter + markdown body defining capabilities
- **Skills** (`SKILL.md`): Trigger-based knowledge with references/ subdirectory
- **Hooks** (`plugin.json`): Automated checks on tool usage events
- **MCP Servers**: External tool integrations (AWS docs, APIs, pricing)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin not loading | Check `plugin.json` paths resolve to files |
| Skill not triggering | Verify trigger keywords in `SKILL.md` frontmatter |
| Version mismatch | Run version sync check from CLAUDE.md |
