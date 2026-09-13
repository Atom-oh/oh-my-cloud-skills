# Architecture

## System Overview

oh-my-cloud-skills is a Claude Code and Codex plugin marketplace providing 8 plugins for AWS cloud content creation (presentations, diagrams, docs, workshops), infrastructure operations/troubleshooting, multi-AI collaboration, and developer tooling.

## Component Structure

### Plugin Layer

| Component | Role | Tech |
|-----------|------|------|
| aws-content-plugin | Content creation (9 agents, 9 skills) | Python, HTML/CSS/JS, Draw.io |
| aws-ops-plugin | Infrastructure ops (10 agents, 6 skills) | MCP servers, AWS CLI |
| kiro-power-converter | Plugin → Kiro Power conversion (1 agent, 1 skill) | YAML/JSON transform |
| agentcore-creator | Claude Code → Bedrock AgentCore conversion (1 agent, 1 skill) | AWS CLI, Python |
| co-agent | Multi-AI collaboration — review/decide/ADR/sync-context/consensus/harness (5 agents, 3 skills, 6 commands) | Configured peer CLIs; current host excluded |
| project-init | Project scaffolding & doc management (1 agent, 1 skill, 9 commands, upstream mirror) | Bash, Markdown |
| kiro | Cost-savings delegation — the current host plans/verifies, Kiro CLI implements (1 agent, 1 skill, 4 commands) | Kiro CLI |
| atlas | Documentation drift detection and optional host-aware repair (1 agent, 1 skill, 5 commands) | Python, Markdown, optional Claude CLI |

### Tool Layer

| Component | Role |
|-----------|------|
| remarp_to_slides.py | Markdown → HTML slide converter (stack-based parser) |
| extract_pptx_theme.py | PPTX → theme-manifest.json + CSS variable extraction |
| remarp-vscode | VSCode extension (preview, visual editing, prompt bar) |
| eval-skills.py | Skill quality evaluation |
| eval-skill-behavior.py | E2E skill behavior testing |

### Documentation Layer

| Component | Role |
|-----------|------|
| doc-sites/ | Docusaurus demo/docs site (published to GitHub Pages) |
| docs/ | Internal docs — ADRs, runbooks, superpowers specs/plans (this file) |
| marketplace.json | Plugin registry |

## Host surfaces

The table above lists all eight plugins. Each has Claude and Codex manifests and a
marketplace entry. Codex projections contain 74 entry skills covering 76 source
procedures (23 skills, 24 commands, 29 agents), plus 25 plugin hooks. Project-init's
three project-hook templates are installed separately and are not plugin hooks.

## Data Flow

```
User prompt → Keyword routing (CLAUDE.md) → Agent → Skill/MCP → Artifact → Quality Gate → Deploy
```

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Independent plugin structure | Individual install/update, separation of concerns |
| Keyword-based auto-routing | Users don't need to manually select agents |
| Literal invocation aliases | Preserve supported user phrases while maintaining English documentation |
| Mandatory Quality Gate | No deployment without content-review-agent pass |
| Single version management | All eight plugins' Claude/Codex manifests and both marketplaces share one release version |
| Kiro CLI external review integration | Multi-perspective deep review + adversarial security verification ([ADR-003](decisions/ADR-003-kiro-cli-architecture-deep-review.md)) |
| AgentCore converter as standalone plugin | Claude Code plugin to Bedrock AgentCore deployment conversion ([ADR-004](decisions/ADR-004-agentcore-creator-skill.md)) |
| Rejection Loop | Validate before build — zero CRITICAL issues required to proceed ([ADR-005](decisions/ADR-005-rejection-loop.md)) |
| project-init plugin | Separated project scaffolding/doc sync into standalone plugin ([ADR-006](decisions/ADR-006-project-init-plugin.md)) |
| Remarp ratio enforcement | Prevent VSCode Extension preview aspect ratio breakage ([ADR-007](decisions/ADR-007-ratio-enforcement.md)) |
