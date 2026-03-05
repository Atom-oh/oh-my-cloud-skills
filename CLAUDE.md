# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Code plugin marketplace containing three plugins for AWS cloud work:
- **aws-content-plugin** — Content creation (presentations, diagrams, docs, workshops)
- **aws-ops-plugin** — Infrastructure operations & troubleshooting (EKS, networking, IAM, observability)
- **kiro-power-converter** — Convert Claude Code plugins to Kiro IDE Power format

All plugins are installed via `/plugin marketplace add` or loaded locally with `--plugin-dir`.

## Development Commands

```bash
# Load plugins locally for testing
claude --plugin-dir ./plugins/aws-content-plugin
claude --plugin-dir ./plugins/aws-ops-plugin

# Validate plugin manifests
python3 -c "import json; d=json.load(open('plugins/aws-content-plugin/.claude-plugin/plugin.json')); print(f'content: {len(d[\"agents\"])} agents, {len(d[\"skills\"])} skills')"
python3 -c "import json; d=json.load(open('plugins/aws-ops-plugin/.claude-plugin/plugin.json')); print(f'ops: {len(d[\"agents\"])} agents, {len(d[\"skills\"])} skills')"

# Verify all plugin.json references resolve to existing files
cd plugins/aws-ops-plugin && python3 -c "
import json, os
d = json.load(open('.claude-plugin/plugin.json'))
for a in d['agents']:
    assert os.path.isfile(a.lstrip('./')), f'Missing agent: {a}'
for s in d['skills']:
    assert os.path.isfile(s.lstrip('./') + '/SKILL.md'), f'Missing skill: {s}'
print('All references OK')
"
```

## Plugin Architecture

Each plugin follows the same structure:

```
plugins/<plugin-name>/
├── .claude-plugin/plugin.json    # Manifest: lists agents[] and skills[]
├── .mcp.json                     # MCP server config (ops-plugin only)
├── CLAUDE.md                     # Auto-invocation keyword → agent routing rules
├── agents/<name>.md              # Agent definitions (YAML frontmatter + markdown body)
└── skills/<name>/                # Skill directories
    ├── SKILL.md                  # Entry point (YAML frontmatter with triggers)
    ├── references/               # Distilled knowledge docs
    └── templates/                # Templates (content-plugin only)
```

### Agent File Format

Every agent `.md` file has YAML frontmatter with exactly three fields:

```yaml
---
name: eks-agent
description: "Description with trigger keywords."
tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
---
```

The body contains: Core Capabilities, Diagnostic Commands, Decision Tree (Mermaid), Error→Solution mapping, MCP Integration, Reference Files, Output Format.

### Skill File Format

Each `SKILL.md` has frontmatter with `name`, `description`, and `triggers` (keyword list). The `references/` subdirectory holds distilled operational knowledge extracted from source docs.

### MCP Configuration

Only `aws-ops-plugin` has `.mcp.json` with 5 AWS MCP servers:
- `awsknowledge` (HTTP) — Architecture recommendations
- `awsdocs` (stdio/uvx) — Official AWS documentation search
- `awsapi` (stdio/uvx) — Direct AWS API calls
- `awspricing` (stdio/uvx) — Pricing data
- `awsiac` (stdio/uvx) — CloudFormation/CDK validation

### Auto-Invocation

Each plugin's `CLAUDE.md` defines keyword→agent routing tables. Keywords include both English and Korean terms. When a user prompt matches keywords, the corresponding agent activates automatically.

## Versioning

All plugins share a single version tracked in their `plugin.json` → `"version"` field, mirrored in `marketplace.json`. Git tags **must** match this version.

- **Single source of truth**: `plugin.json` `"version"` in all plugins + `marketplace.json` (keep them in sync)
- **Git tag format**: `v{version}` (e.g., `v1.1.0`) — created on the release commit
- **Release process**: bump `"version"` in all `plugin.json` files + `marketplace.json` → commit → `git tag v{version}` → push with `--tags`
- **Validation**: `git describe --tags` should match all `plugin.json` and `marketplace.json` versions

```bash
# Verify version consistency
V=$(python3 -c "import json; print(json.load(open('plugins/aws-content-plugin/.claude-plugin/plugin.json'))['version'])")
V2=$(python3 -c "import json; print(json.load(open('plugins/aws-ops-plugin/.claude-plugin/plugin.json'))['version'])")
V3=$(python3 -c "import json; print(json.load(open('plugins/kiro-power-converter/.claude-plugin/plugin.json'))['version'])")
MV=$(python3 -c "import json; vs=set(p['version'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']); print(vs.pop() if len(vs)==1 else 'MISMATCH')")
TAG=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//')
echo "content=$V ops=$V2 converter=$V3 marketplace=$MV tag=$TAG"
[ "$V" = "$V2" ] && [ "$V" = "$V3" ] && [ "$V" = "$MV" ] && [ "$V" = "$TAG" ] && echo "OK: all match" || echo "MISMATCH"
```

## Key Conventions

- Content plugin agents produce artifacts (HTML, .drawio, .md); ops plugin agents produce diagnoses with commands
- Content goes through `content-review-agent` quality gate (100-point scale: PASS ≥85, REVIEW 70-84, FAIL <70)
- Ops plugin reference files are commands-first, with Mermaid decision trees and error→solution tables
- Korean/English bilingual keywords in all auto-invocation rules
- AWS icons live in `aws-content-plugin/skills/reactive-presentation/icons/` (4,224 files)

## Plugin Inventory

### aws-content-plugin (7 agents, 5 skills)

| Agent | Creates |
|-------|---------|
| `presentation-agent` | Interactive HTML slideshows via reactive-presentation framework |
| `architecture-diagram-agent` | Draw.io XML → PNG/SVG |
| `animated-diagram-agent` | SVG + SMIL animation HTML |
| `document-agent` | Markdown technical documents |
| `gitbook-agent` | GitBook documentation sites |
| `workshop-agent` | AWS Workshop Studio content |
| `content-review-agent` | Quality gate for all content types |

### aws-ops-plugin (9 agents, 5 skills)

| Agent | Domain |
|-------|--------|
| `eks-agent` | EKS cluster management, node groups, upgrades, add-ons |
| `network-agent` | VPC CNI, ALB/NLB, DNS, Security Groups |
| `iam-agent` | IRSA, Pod Identity, RBAC, aws-auth |
| `observability-agent` | CloudWatch, AMP, AMG, ADOT, Prometheus/Grafana |
| `storage-agent` | EBS/EFS/FSx CSI drivers, PVC binding |
| `database-agent` | RDS/Aurora, DynamoDB, ElastiCache |
| `cost-agent` | Cost analysis via awspricing MCP |
| `analytics-agent` | OpenSearch, ClickHouse, Athena, QuickSight, Kinesis |
| `ops-coordinator-agent` | Multi-domain incident coordination |

Ops skills: `ops-troubleshoot`, `ops-health-check`, `ops-network-diagnosis`, `ops-observability`, `ops-security-audit` — each with `references/` subdirectory containing distilled runbooks.

### kiro-power-converter (1 agent, 1 skill)

| Agent | Purpose |
|-------|---------|
| `kiro-converter-agent` | Converts Claude Code plugins to Kiro Power format |

Skill: `kiro-convert` — interactive workflow for plugin-to-power conversion with `references/` subdirectory containing format specs and conversion rules.

## Workflows

```
Content:   presentation-agent → content-review-agent → GitHub Pages
           architecture-diagram-agent → .drawio → PNG
           animated-diagram-agent → .html (SVG+SMIL)
           document-agent → content-review-agent → .md
           gitbook-agent → content-review-agent → git push
           workshop-agent → content-review-agent → Workshop Studio

Ops:       User issue → auto-routed agent → Diagnose → Resolve → Verify
           Incident → ops-coordinator → specialist agents (7) → aggregate → root cause → fix
```
