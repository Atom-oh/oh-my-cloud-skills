# Architecture

## System Overview

oh-my-cloud-skills is a Claude Code plugin marketplace providing 7 plugins for AWS cloud content creation (presentations, diagrams, docs, workshops), infrastructure operations/troubleshooting, multi-AI collaboration, and developer tooling.

## Component Structure

### Plugin Layer

| Component | Role | Tech |
|-----------|------|------|
| aws-content-plugin | Content creation (9 agents, 9 skills) | Python, HTML/CSS/JS, Draw.io |
| aws-ops-plugin | Infrastructure ops (10 agents, 6 skills) | MCP servers, AWS CLI |
| kiro-power-converter | Plugin → Kiro Power conversion (1 agent, 1 skill) | YAML/JSON transform |
| agentcore-creator | Claude Code → Bedrock AgentCore conversion (1 agent, 1 skill) | AWS CLI, Python |
| co-agent | Multi-AI collaboration — review/decide/ADR/sync-context/consensus/harness (5 agents, 3 skills, 6 commands) | Kiro/Codex/Antigravity CLI |
| project-init | Project scaffolding & doc management (1 agent, 1 skill, 9 commands, upstream mirror) | Bash, Markdown |
| kiro | Cost-savings delegation — Claude plans/verifies, Kiro CLI implements (1 agent, 1 skill, 4 commands) | Kiro CLI |

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

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                      oh-my-cloud-skills — Plugin Marketplace          │
├────────────────────┬────────────────────┬──────────────────────────┤
│ aws-content-plugin  │ aws-ops-plugin      │ co-agent                 │
│ 9 agents, 9 skills  │ 10 agents, 6 skills │ 5 agents, 3 skills,      │
│ content creation    │ infra operations    │ 6 commands — multi-AI    │
├────────────────────┼────────────────────┼──────────────────────────┤
│ kiro-power-converter│ agentcore-creator   │ project-init             │
│ 1 agent, 1 skill    │ 1 agent, 1 skill    │ 1 agent, 1 skill,        │
│ → Kiro Power        │ → Bedrock AgentCore │ 9 commands (upstream)    │
├────────────────────┴────────────────────┴──────────────────────────┤
│ kiro — 1 agent, 1 skill, 4 commands — delegates implementation to    │
│ Kiro CLI                                                              │
├───────────────────────────────────────────────────────────────────────┤
│ Tools: remarp_to_slides.py · extract_pptx_theme.py · remarp-vscode ·  │
│        eval-skills.py · eval-skill-behavior.py                       │
│ Docs:  doc-sites/ (Docusaurus) · docs/ (ADRs/runbooks/superpowers)    │
└───────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User prompt → Keyword routing (CLAUDE.md) → Agent → Skill/MCP → Artifact → Quality Gate → Deploy
```

## Key Design Decisions

| Decision | Why |
|----------|-----|
| Independent plugin structure | Individual install/update, separation of concerns |
| Keyword-based auto-routing | Users don't need to manually select agents |
| Bilingual KR/EN keywords | Korean-first user support |
| Mandatory Quality Gate | No deployment without content-review-agent pass |
| Single version management | All 7 plugin.json + marketplace.json kept in sync at one version |
| Kiro CLI external review integration | Multi-perspective deep review + adversarial security verification ([ADR-003](decisions/ADR-003-kiro-cli-architecture-deep-review.md)) |
| AgentCore converter as standalone plugin | Claude Code plugin to Bedrock AgentCore deployment conversion ([ADR-004](decisions/ADR-004-agentcore-creator-skill.md)) |
| Rejection Loop | Validate before build — zero CRITICAL issues required to proceed ([ADR-005](decisions/ADR-005-rejection-loop.md)) |
| project-init plugin | Separated project scaffolding/doc sync into standalone plugin ([ADR-006](decisions/ADR-006-project-init-plugin.md)) |
| Remarp ratio enforcement | Prevent VSCode Extension preview aspect ratio breakage ([ADR-007](decisions/ADR-007-ratio-enforcement.md)) |
