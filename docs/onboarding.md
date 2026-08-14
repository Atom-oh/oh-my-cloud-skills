# Onboarding Guide

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (for the Docusaurus docs site)
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
cd doc-sites && npm install && npm run build
```

### Verify

```bash
# Validate plugin manifests
python3 scripts/test-plugins.py

# Check version consistency across all 7 plugins
VS=$(for f in plugins/*/.claude-plugin/plugin.json; do python3 -c "import json; print(json.load(open('$f'))['version'])"; done | sort -u)
echo "$VS"   # should print exactly one version
```

## Project Overview

This is a Claude Code plugin marketplace with 7 plugins:

| Plugin | Purpose | Agents | Skills | Commands |
|--------|---------|--------|--------|----------|
| aws-content-plugin | AWS cloud content creation (presentations, diagrams, docs, workshops) | 9 | 9 | — |
| aws-ops-plugin | Infrastructure operations & troubleshooting | 10 | 6 | — |
| kiro-power-converter | Claude Code plugin → Kiro Power format conversion | 1 | 1 | — |
| agentcore-creator | Claude Code plugin → Bedrock AgentCore conversion | 1 | 1 | — |
| co-agent | Multi-AI collaboration (Kiro CLI, Codex, Antigravity) — review, decision support, ADR, consensus/harness pipelines | 5 | 3 | 6 |
| project-init | Project scaffolding & documentation management (upstream mirror) | 1 | 1 | 9 |
| kiro | Cost-savings delegation — Claude plans/verifies, Kiro CLI implements | 1 | 1 | 4 |

See root `CLAUDE.md` → "Plugin Inventory" for the authoritative, always-current per-plugin breakdown.

## Development Workflow

1. Make changes to plugin agents/skills.
2. Test locally: `claude --plugin-dir ./plugins/<plugin>`.
3. Run eval: `python3 scripts/eval-skills.py`.
4. Bump the version in **all** `plugin.json` files + `marketplace.json` (single shared version across all 7 plugins — see root `CLAUDE.md` → "Versioning").
5. Commit, tag `v{version}`, push, release (`docs/runbooks/plugin-release.md`).

## Key Concepts

- **Agents** (`.md` files): YAML frontmatter + markdown body defining capabilities.
- **Skills** (`SKILL.md`): trigger-based knowledge with a `references/` subdirectory.
- **Hooks** (`plugin.json`): automated checks on tool-usage events.
- **MCP Servers**: external tool integrations (AWS docs, APIs, pricing, Playwright).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Plugin not loading | Check `plugin.json` paths resolve to files |
| Skill not triggering | Trigger keywords must live in `SKILL.md`'s `description` field — a `triggers:` key is inert (ignored by the runtime) |
| Version mismatch | Run the version-consistency check above, or the snippet in root `CLAUDE.md` → "Versioning" |
