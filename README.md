# oh-my-cloud-skills

<div align="center">

<a href="README.md"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="README.ko.md"><img src="https://img.shields.io/badge/lang-한국어-lightgrey.svg" alt="한국어"></a>

[![version](https://img.shields.io/github/v/tag/Atom-oh/oh-my-cloud-skills?label=version&color=green)](https://github.com/Atom-oh/oh-my-cloud-skills/tags)
[![license](https://img.shields.io/github/license/Atom-oh/oh-my-cloud-skills?color=yellow)](LICENSE)
[![stars](https://img.shields.io/github/stars/Atom-oh/oh-my-cloud-skills?logo=github)](https://github.com/Atom-oh/oh-my-cloud-skills/stargazers)
[![forks](https://img.shields.io/github/forks/Atom-oh/oh-my-cloud-skills?logo=github)](https://github.com/Atom-oh/oh-my-cloud-skills/network/members)
[![docs](https://img.shields.io/github/actions/workflow/status/Atom-oh/oh-my-cloud-skills/deploy-docs.yml?branch=main&label=docs&logo=githubpages)](https://www.atomai.click/oh-my-cloud-skills/)

</div>

AWS cloud plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — content creation and infrastructure operations.

**[Documentation](https://www.atomai.click/oh-my-cloud-skills/)** | **[Release Notes](https://github.com/Atom-oh/oh-my-cloud-skills/releases)**

**What you can do:**

*Content Creation (aws-content-plugin):*
- **Interactive HTML/CSS/JS presentations** — Canvas animations, quizzes, presenter view, deployed to GitHub Pages
- **Native PowerPoint (.pptx) decks** — AWS Light-theme slides via the `aws-light-fcd` skill (PptxGenJS, Pretendard typography, embedded fonts, AWS architecture-diagram kit)
- **AWS architecture diagrams** — Draw.io XML with auto-layout, exportable to PNG/SVG
- **Animated traffic flow diagrams** — SVG + SMIL animations with interactive legends
- **Technical documents** — Professional Markdown reports and comparisons
- **GitBook documentation sites** — Structured docs with navigation and components
- **AWS Workshop Studio content** — Hands-on labs with multi-language support
- **Single-page online brochures** — Self-contained responsive landing pages with embedded architecture diagram, deployed to GitHub Pages

*Infrastructure Operations (aws-ops-plugin):*
- **EKS troubleshooting** — Node issues, upgrades, add-ons, 5-minute triage
- **Network diagnostics** — VPC CNI, ALB/NLB, DNS, IP exhaustion
- **IAM & security** — IRSA, Pod Identity, RBAC, policy validation
- **Observability** — CloudWatch, Container Insights, Prometheus, X-Ray
- **Cost optimization** — Pricing analysis, savings plans, right-sizing

*Well-Architected Review (aws-ops-plugin):*
- **6-pillar assessment** — Cost, Security, Reliability, Performance, Operational Excellence, Sustainability
- **100-point scoring** — Quantitative scoring with AS-IS/TO-BE roadmap
- **Specialist delegation** — Pillars scoring below 60 delegated to specialist agents

*Plugin Conversion (kiro-power-converter):*
- **Claude Code → Kiro Power** — Automatically convert plugins for use in Kiro IDE
- **Multiple input sources** — GitHub URL, local path, marketplace search, individual skill
- **Zero dependencies** — Python 3.8+ standard library only

*AgentCore Deployment (agentcore-creator):*
- **Bedrock AgentCore** — Convert Claude Code plugins to AgentCore Runtime, Gateway, Memory
- **5-phase workflow** — Discovery, Design, Skill-First Build, Convert, Deploy
- **Strands Agent framework** — Generates deployable Python agents with BedrockModel

*Multi-AI Collaboration (co-agent):*
- **4 modes** — multi-AI review, decision support, ADR co-authoring, and `sync-context` (distill `CLAUDE.md` -> `AGENTS.md`/`GEMINI.md`)
- **Panel of installed CLIs** — fan the same prompt to Kiro/Codex/Antigravity in parallel; Claude chairs and synthesizes consensus vs. dissent (degrades gracefully if none installed). The Gemini-family slot prefers Antigravity (`agy`) and **falls back to the `gemini` CLI when `agy` is absent** — skipped if neither is installed
- **`/co-agent:configure`** — tune per-AI model, Codex effort, enable/disable, timeout, and `autosync` (regenerate AI context on `CLAUDE.md` change)

*Project Scaffolding (project-init):*
- **10 slash commands** — /init-project, /sync-docs, /add-adr, /add-module, /add-runbook, /add-reference-doc, and more
- **Documentation quality scoring** — CLAUDE.md quality assessment on 100-point scale
- **Auto-sync workflows** — Keep documentation in sync with code changes
- **ADR contradiction review** — `decision-reconcile` finds conflicting ADRs (and ADR-vs-reality drift) with a diverse multi-agent panel and drafts a superseding ADR

---

## Installation

Every plugin ships **both** a Claude Code manifest (`.claude-plugin/plugin.json`) and a
Codex manifest (`.codex-plugin/plugin.json`), so the same marketplace installs on either
host. Pick your host below.

### Claude Code

```bash
# Add the marketplace
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills

# Install plugins
/plugin install aws-content-plugin@oh-my-cloud-skills
/plugin install aws-ops-plugin@oh-my-cloud-skills
/plugin install kiro-power-converter@oh-my-cloud-skills
/plugin install agentcore-creator@oh-my-cloud-skills
/plugin install co-agent@oh-my-cloud-skills
/plugin install project-init@oh-my-cloud-skills
```

For local development:
```bash
# Load plugins from local directory
claude --plugin-dir ./plugins/aws-content-plugin
claude --plugin-dir ./plugins/aws-ops-plugin
claude --plugin-dir ./plugins/kiro-power-converter
claude --plugin-dir ./plugins/agentcore-creator
claude --plugin-dir ./plugins/co-agent
claude --plugin-dir ./plugins/project-init
```

Uninstall:
```bash
# Uninstall plugins
/plugin uninstall aws-content-plugin@oh-my-cloud-skills
/plugin uninstall aws-ops-plugin@oh-my-cloud-skills
/plugin uninstall kiro-power-converter@oh-my-cloud-skills
/plugin uninstall agentcore-creator@oh-my-cloud-skills
/plugin uninstall co-agent@oh-my-cloud-skills
/plugin uninstall project-init@oh-my-cloud-skills

# Remove the marketplace
/plugin marketplace remove oh-my-cloud-skills
```

### Codex CLI

This repo is also a **Codex plugin marketplace** — the manifest lives at
[`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json) (`name: oh-my-cloud-skills`)
and each plugin's `.codex-plugin/plugin.json` exposes its skills to Codex. Requires a recent
Codex CLI with plugin support.

```bash
# Register this repo as a marketplace (GitHub shorthand, or a git/SSH URL)
codex plugin marketplace add Atom-oh/oh-my-cloud-skills

# Browse & install from the interactive plugin picker
#   → switch to the "Oh My Cloud Skills" source, then install the plugins you want
codex /plugins
```

For local development, the **repo-scoped** marketplace is auto-discovered when you run Codex
from inside a clone (Codex reads `$REPO_ROOT/.agents/plugins/marketplace.json`). You can also
register the local path explicitly:

```bash
# From the repo root
codex plugin marketplace add ./
codex /plugins
```

Manage / remove the marketplace:
```bash
codex plugin marketplace list                       # list registered marketplaces
codex plugin marketplace upgrade oh-my-cloud-skills # pull the latest plugin versions
codex plugin marketplace remove oh-my-cloud-skills  # unregister (uninstall via `codex /plugins`)
```

> **co-agent on Codex** — when the host is Codex, **Codex chairs** the panel and Claude / Kiro
> / Agy become the advisory peers (the mirror of Claude-hosted mode). The skill detects this via
> `CO_AGENT_HOST=codex`. The Claude Code-only hooks (e.g. the PR consensus gate) don't run under
> Codex by design.

---

## Reactive Presentation

The core feature. Tell Claude what training or presentation you need, and it builds a complete interactive HTML slideshow — no PowerPoint, no Reveal.js config, no npm install.

### What gets created

Each presentation is a set of standalone HTML files with a shared framework:

```
your-repo/
├── index.html                      # Hub page linking all presentations
├── common/                         # Shared framework (copied once)
│   ├── theme.css                   # Dark theme, Pretendard font, 16:9 layout
│   ├── slide-framework.js          # Keyboard/touch nav, progress bar, hash routing
│   ├── presenter-view.js           # Presenter view with draggable splitters
│   ├── animation-utils.js          # Canvas primitives, AnimationLoop, easing
│   ├── quiz-component.js           # Quiz auto-grading and feedback
│   ├── export-utils.js             # PDF/PPTX export and ZIP download
│   └── aws-icons/                  # AWS Architecture Icons (optional)
└── eks-autoscaling/                # One directory per presentation
    ├── index.html                  # Table of contents
    ├── 01-fundamentals.html        # Block 1 (20-35 min)
    ├── 02-karpenter.html           # Block 2
    └── 03-advanced.html            # Block 3
```

### Slide types

| Slide Type | What It Does |
|---|---|
| Canvas Animation | Animated architecture diagrams with Play/Pause controls |
| Compare Toggle | A vs B side-by-side comparison with toggle buttons |
| Tabs | Tabbed content panels (e.g., YAML config variants) |
| Timeline | Horizontal step-by-step process visualization |
| Checklist | Click-to-toggle best practices with optional YAML expand |
| Quiz | Multiple-choice questions with auto-grading |
| Code Block | Syntax-highlighted YAML/JSON/HCL with semantic spans |
| Slider | Range input with live computed output |
| Agenda | Session agenda with numbered dots, time labels, and break markers |
| Prompt | AI prompt workflow display with copy button |
| Pain Quote | Customer problem statement with challenge list |

### Remarp VSCode Extension

A dedicated VSCode extension for authoring and previewing Remarp presentations. Install from VSIX or build from source.

**Install:**
```bash
code --install-extension tools/remarp-vscode/remarp-vscode-0.1.0.vsix
```

**Features:**
- **Syntax highlighting** — Remarp directives (`@type`, `@layout`, `@animation`), block tags (`:::canvas`, `:::notes`), click attributes (`{.click}`), Canvas DSL, frontmatter
- **Live preview** — Side panel with auto-update, dark mode, slide navigation, cursor sync
- **HTML preview** — Renders Remarp-generated HTML with full CSS/JS (slide framework, animations, fonts)
- **IntelliSense** — Auto-complete for directives, values, block types, Canvas DSL, click attributes
- **Visual edit** — Drag/resize elements in preview, changes written back to `.remarp.md` source
- **Build** — One-click HTML generation via `remarp_to_slides.py` (auto-discovered)
- **Document outline** — Slide tree view in Explorer sidebar
- **Auto-detection** — Recognizes Remarp HTML via `<meta name="generator" content="remarp">`

**Source:** `tools/remarp-vscode/` | **Docs:** [VSCode Extension Guide](docs/docs/remarp-guide/vscode-extension.md)

### VSCode extension shortcuts

| Key | Action | Available in |
|-----|--------|-------------|
| `Ctrl+Shift+V` | Open Preview | `.remarp.md`, Remarp HTML |
| `Ctrl+Shift+E` | Toggle Visual Edit Mode | `.remarp.md`, Remarp HTML |
| `Ctrl+Shift+B` | Build HTML | `.remarp.md`, Remarp HTML |

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| `←` `→` | Previous / Next slide |
| `↑` `↓` | Previous / Next slide (alternative) |
| `Space` | Next slide |
| `F` | Toggle fullscreen |
| `P` | Open presenter view (new window) |
| `Esc` | Exit fullscreen |
| `Home` / `End` | First / Last slide |
| `N` | Toggle slide numbers |
| `O` | Overview mode (slide grid) |
| `S` | Speaker notes |
| `B` | Black screen (pause) |
| `1`-`9` | Jump to slide 10%-90% |

### How it works

1. **Plan** — Claude asks about topic, audience, duration, language, and optional PPTX/PDF source for corporate branding
2. **Author** — Writes Remarp markdown as the content source of truth
3. **Generate** — Builds HTML via `remarp_to_slides.py` with Canvas animations and interactive elements inline
4. **Review** — Interactive feedback loop: edit Remarp directly, preview/edit generated HTML in VSCode (extension auto-detects Remarp HTML via meta tags), or request changes via prompt
5. **Enhance** — Adds Canvas animations, extracts AWS icons, tests presenter view
6. **Deploy** — `git push` to GitHub Pages. No build step required

### Creating a Presentation

#### Getting Started

Start by describing what you need. Here are some example prompts:

```
"Create a training presentation on EKS autoscaling"
```

```
"Create a presentation on AWS Lambda cold starts"
```

```
"Build hands-on slides for Karpenter migration"
```

```
"Make training materials on S3 security best practices"
```

The agent activates automatically when it detects presentation-related keywords in your prompt.

#### What Claude Asks

Before generating content, Claude asks 8 planning questions to tailor the presentation:

| # | Question | Description | Default |
|---|----------|-------------|---------|
| 1 | Topic and audience | Technical depth, pain points, learning objectives | — |
| 2 | Duration | Total length — determines block count and slide count | — |
| 3 | Blocks | 20-35 min per block with 5 min breaks between blocks | Auto-split based on duration |
| 4 | Target repo | GitHub repo for deployment | `~/reactive_presentation/` |
| 5 | Language | Korean or English (technical terms always in English) | Korean |
| 6 | PPTX/PDF source | Corporate `.pptx`/`.pdf` for theme extraction or full conversion | None (dark theme) |
| 7 | Speaker info | Name and affiliation for the cover slide (stored for reuse) | — |
| 8 | Quiz inclusion | Whether to include quiz slides for knowledge checks | Yes |

After gathering answers, Claude writes Remarp markdown content and generates interactive HTML slides.

#### Review and Iteration

After Claude generates the initial content, you enter a review loop with three options:

1. **Edit Remarp directly** — Open the `.remarp.md` file in your editor, make changes, then say "done". Claude reads your edits and updates the HTML to match.

2. **Request changes via prompt** — Describe what to change (e.g., "add a quiz after slide 5", "reduce the timeline to 3 steps"). Claude updates both the Remarp source and HTML files.

3. **Proceed** — If the content looks good, approve it and move to the enhancement phase where Canvas animations and interactive elements are added.

This loop repeats until you are satisfied. Remarp markdown stays in sync with the HTML at all times — Remarp is the content source of truth, HTML adds interactivity on top.

#### Deploy to GitHub Pages

Once the presentation is finalized:

```bash
git add common/ {slug}/ index.html
git commit -m "feat: add {presentation-name} interactive training"
git push origin main
```

Then enable GitHub Pages: Settings -> Pages -> main branch / root.

No build step is required — the HTML files are served directly.

### PPTX theme extraction

If you have a corporate PowerPoint template, provide the `.pptx` file and the agent extracts colors, fonts, and logos into CSS overrides — applying your brand to the dark theme framework automatically.

---

## Architecture Diagrams

Static AWS architecture diagrams as Draw.io XML. The agent places AWS icons, groups resources into VPC/subnet boundaries, and auto-layouts connections.

**Output**: `.drawio` files — export to PNG or SVG for embedding in presentations, documents, or GitBook pages.

**Supports**: Auto-layout, AWS icon placement, VPC/subnet/region grouping, multi-tier architectures.

```
"Draw an EKS with ALB architecture diagram"
```

```
"Create a 3-tier VPC architecture diagram with public/private subnets"
```

---

## Animated Diagrams

Dynamic traffic flow diagrams with SVG + SMIL animation. Each diagram is a standalone HTML file with play/pause controls and an interactive legend.

**Output**: `.html` files with embedded SVG animations — no dependencies, works in any browser.

**Supports**: Request routing flows, data pipeline visualization, multi-service traffic patterns, color-coded service tiers.

```
"Create an animated API Gateway → Lambda → DynamoDB flow"
```

```
"Build a traffic flow animation showing EKS pod-to-pod communication"
```

---

## Documents

Professional Markdown technical documents — reports, solution comparisons, architecture documentation, and guides. Integrates with `architecture-diagram-agent` for inline diagrams.

**Output**: `.md` files with tables, code blocks, and diagram references.

```
"Write an EKS vs ECS comparison document"
```

```
"Create a technical report on S3 security best practices"
```

---

## GitBook Sites

Structured documentation sites with navigation, components, and cross-references. Generates a complete GitBook project with `SUMMARY.md`, code tabs, hints, and expandable sections.

**Output**: GitBook project directory — push to a GitBook-connected repo for automatic deployment.

**Supports**: Multi-page navigation, code tabs (multi-language), hint/warning blocks, embedded diagrams.

```
"Create a GitBook documentation site for our API"
```

```
"Build a GitBook knowledge base for EKS operations"
```

---

## Workshops

AWS Workshop Studio content with hands-on lab modules. Generates complete workshop structures including CloudFormation templates, step-by-step instructions, and multi-language support (Korean + English).

**Output**: Workshop Studio content with `contentspec.yaml`, module directories, and bilingual `.ko.md` / `.en.md` file pairs.

**Supports**: Lab modules with prerequisites, CloudFormation infrastructure templates, Workshop Studio directives (not Hugo shortcodes).

```
"Create an EKS hands-on workshop"
```

```
"Build a serverless workshop with Lambda and DynamoDB labs"
```

---

## Content Review

Quality gate for all content types. The `content-review-agent` inspects layout, terminology, hallucination, language, PII/sensitive data, readability, accessibility, and structural completeness — scoring on a 100-point scale.

Used automatically at the end of content creation workflows (presentations, documents, GitBook, workshops). Can also be invoked directly:

```
"Review the presentation for quality"
```

See [Quality Gate](#quality-gate) for scoring details.

---

## AWS Ops

Infrastructure operations and troubleshooting for AWS/EKS environments. Describe your issue — node crashes, network problems, IAM errors, cost spikes — and the right agent activates automatically.

### Agents

| Agent | Domain | Example Prompt |
|-------|--------|----------------|
| `eks-agent` | EKS clusters | "My node is NotReady, troubleshoot" |
| `network-agent` | Networking | "Pod can't reach external service" |
| `iam-agent` | IAM/RBAC | "Getting AccessDenied on S3 from pod" |
| `observability-agent` | Observability | "Set up Container Insights for EKS" |
| `storage-agent` | Storage | "PVC stuck in Pending state" |
| `database-agent` | Database | "Aurora connection timeout from EKS" |
| `cost-agent` | Cost | "Analyze my EKS cluster costs" |
| `analytics-agent` | Analytics | "OpenSearch cluster health is red" |
| `ops-coordinator-agent` | Incidents | "Production outage, coordinate response" |
| `wellarchitected-agent` | Well-Architected | "Run a Well-Architected review on my infra" |

### Skills

| Skill | Trigger | What It Does |
|-------|---------|--------------|
| `ops-troubleshoot` | "troubleshoot", "debug" | Systematic 5-min triage → investigate → resolve → postmortem |
| `ops-health-check` | "health check" | Full 6-domain infrastructure assessment |
| `ops-network-diagnosis` | "network issue" | VPC CNI, Load Balancer, DNS deep diagnosis |
| `ops-observability` | "monitoring setup", "opentelemetry", "devops agent" | CloudWatch/Prometheus/logs + OSS stack (OpenTelemetry, Grafana, Loki, Tempo, ClickHouse) + AWS DevOps Agent incident escalation |
| `ops-security-audit` | "security audit", "penetration testing" | IAM/network/CIS posture + AWS Security Agent (design/code review, on-demand pentest) |
| `ops-wellarchitected-review` | "well-architected" | 6-pillar assessment, 100-point scoring, AS-IS/TO-BE roadmap |

### MCP Integration

The ops plugin connects to AWS MCP servers for real-time infrastructure data:

| Server | Purpose |
|--------|---------|
| `awsknowledge` | Architecture recommendations and regional availability |
| `awsdocs` | Official AWS documentation search |
| `awsapi` | Direct AWS API calls (describe, list resources) |
| `awspricing` | Service pricing and cost analysis |
| `awsiac` | CloudFormation/CDK validation and troubleshooting |

### Incident Response

```
User report → ops-coordinator (triage + severity)
                ├── Network → network-agent
                ├── Cluster → eks-agent
                ├── Auth    → iam-agent
                ├── Storage → storage-agent
                ├── Logs    → observability-agent
                └── Search  → analytics-agent
              ← Aggregate → Root cause → Resolve → Verify
```

All agents activate automatically when Claude detects matching keywords.

---

## Kiro Power Converter

Convert any Claude Code plugin into [Kiro IDE](https://kiro.dev) Power format — automatically. The converter handles structure translation, frontmatter transformation, MCP configuration migration, and keyword aggregation.

### Why

Claude Code plugins and Kiro Powers share a similar concept (agents + skills + MCP servers) but differ in folder structure, file format, and configuration. This plugin bridges the gap so you can reuse Claude Code plugins in Kiro without manual rewriting.

### How It Works

| Claude Code | Kiro Power | What Changes |
|-------------|------------|--------------|
| `.claude-plugin/plugin.json` | `POWER.md` | Manifest → YAML frontmatter with aggregated keywords |
| `CLAUDE.md` | `steering/routing.md` | Wrapped with `inclusion: always` |
| `agents/*.md` | `steering/<agent>.md` | `tools`/`model` removed, `inclusion: auto` added |
| `skills/*/SKILL.md` | `steering/<skill>.md` | `triggers[]` merged into description, `inclusion: auto` |
| `skills/*/references/*.md` | `steering/ref-*.md` | `inclusion: manual` frontmatter added |
| `.mcp.json` | `mcp.json` | `type` removed, `autoApprove`/`disabled` added |

### Usage

#### Using the Agent (Interactive)

Just describe what you want in natural language — the agent activates on keywords like "convert to kiro", "kiro power", "키로 변환":

```
"Convert aws-ops-plugin to Kiro Power format"
```

```
"키로 파워로 변환해줘"
```

#### Using the Script (CLI)

The conversion script supports 4 input sources and 3 output targets. No external dependencies — Python 3.8+ standard library only.

**From a local plugin:**
```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --source ./plugins/aws-ops-plugin \
  --output /tmp/aws-ops-power \
  --target export
```

**From a GitHub repository:**
```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --git-url https://github.com/Atom-oh/oh-my-cloud-skills \
  --plugin-path plugins/aws-ops-plugin \
  --output /tmp/aws-ops-power \
  --target global
```

**From marketplace (name search):**
```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --marketplace aws-ops-plugin \
  --output /tmp/aws-ops-power \
  --target global
```

**Search available plugins:**
```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --search "aws"
```

**Convert individual skills:**
```bash
# Single skill → standalone steering file
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --skill ./plugins/aws-ops-plugin/skills/ops-troubleshoot \
  --output ~/.kiro/steering/ops-troubleshoot.md

# Multiple skills at once
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py \
  --skill ./skills/ops-troubleshoot \
  --skill ./skills/ops-health-check \
  --output ~/.kiro/steering/
```

### Output Targets

| Target | Flag | Install Path | Use Case |
|--------|------|--------------|----------|
| **export** | `--target export` (default) | `--output` path | Share, review, or manually install |
| **global** | `--target global` | `~/.kiro/powers/<name>/` | Available in all Kiro projects |
| **project** | `--target project` | `.kiro/powers/<name>/` | Current project only |

### Example Output

Converting `aws-ops-plugin` (9 agents, 5 skills, 5 MCP servers) produces:

```
aws-ops-power/
├── POWER.md                      # Manifest with ~96 aggregated keywords
├── mcp.json                      # 5 AWS MCP servers (type field removed)
└── steering/
    ├── routing.md                # Always-loaded routing context
    ├── eks-agent.md              # Auto-activated agent steering files
    ├── network-agent.md
    ├── iam-agent.md
    ├── observability-agent.md
    ├── storage-agent.md
    ├── database-agent.md
    ├── cost-agent.md
    ├── ops-coordinator-agent.md  # "(Advanced reasoning)" in description
    ├── ops-troubleshoot.md       # Skill with triggers merged
    ├── ops-health-check.md
    ├── ops-network-diagnosis.md
    ├── ops-observability.md
    ├── ops-security-audit.md
    └── ref-*.md                  # 15 reference files (manual inclusion)
```

### Edge Cases

| Scenario | Handling |
|----------|----------|
| Large assets (icons/, 4,224 files) | Download script generated, directory skipped |
| Opus model agents | `model` removed, "(Advanced reasoning)" added to description |
| Korean + English keywords | Both languages included in POWER.md keywords |
| Missing `.mcp.json` | `mcp.json` generation skipped |
| Nested path references | Converted to power-relative paths |

---

## Quick Start

### Content Agents

| Agent | Creates | Example Prompt | Output |
|-------|---------|----------------|--------|
| `presentation-agent` | Interactive HTML slides | "Create an AWS training presentation" | `.html` (GitHub Pages) |
| `architecture-diagram-agent` | AWS architecture diagrams | "Draw a VPC architecture diagram" | `.drawio` -> `.png` |
| `animated-diagram-agent` | Animated traffic flow | "Create a traffic flow animation" | `.html` (SVG+SMIL) |
| `document-agent` | Technical documents | "Write an EKS vs ECS comparison document" | `.md` |
| `gitbook-agent` | Documentation sites | "Create a GitBook documentation site" | GitBook project |
| `workshop-agent` | Workshop content | "Create an EKS workshop" | Workshop Studio |
| `brochure-agent` | Single-page online brochure | "Make a landing page for our platform" | `.html` (GitHub Pages) |
| `content-review-agent` | Quality review | "Review the presentation" | Review report |

### Operations Agents

| Agent | Domain | Example Prompt | Output |
|-------|--------|----------------|--------|
| `eks-agent` | EKS clusters | "Node NotReady, troubleshoot" | Diagnosis + fix |
| `network-agent` | Networking | "VPC CNI IP exhaustion" | Diagnosis + fix |
| `iam-agent` | IAM/RBAC | "Pod can't access S3" | Policy fix |
| `observability-agent` | Observability | "Set up Container Insights" | Config + queries |
| `storage-agent` | Storage | "PVC stuck in Pending" | Diagnosis + fix |
| `database-agent` | Database | "Aurora timeout from EKS" | Diagnosis + fix |
| `cost-agent` | Cost | "Analyze cluster costs" | Cost report |
| `analytics-agent` | Analytics | "OpenSearch cluster red" | Diagnosis + fix |
| `ops-coordinator-agent` | Incidents | "Production outage" | Coordinated response |
| `wellarchitected-agent` | Well-Architected | "Run a WAF review" | 100-point score + roadmap |

### Conversion, Review, and Scaffolding Agents

| Agent | Plugin | Example Prompt | Output |
|-------|--------|----------------|--------|
| `kiro-converter-agent` | kiro-power-converter | "Convert aws-ops-plugin to Kiro" | Kiro Power directory |
| `agentcore-creator-agent` | agentcore-creator | "Deploy agent to AgentCore" | Strands Agent + deploy script |
| `co-agent` | co-agent | "second opinion" / "help me decide" / "co-author ADR" | Multi-AI review / decision / ADR |
| `doc-sync-checker` | project-init | "/sync-docs" | Doc quality scores |

All agents activate automatically when Claude detects matching keywords in your prompt.

---

## Skills

### Content Skills

| Skill | Provides |
|-------|----------|
| `reactive-presentation` | Presentation framework (CSS/JS), Remarp conversion, PPTX→Remarp converter, AWS icon extraction, slide pattern reference |
| `architecture-diagram` | Spec-driven `layout_aws.py` engine (YAML → Draw.io), embedded shared AWS icons, `.excalidraw` generator, layout/design lint gate |
| `animated-diagram` | SMIL animation guide, HTML wrapper templates, traffic flow patterns |
| `slide-fix` | Apply Remarp slide issue annotations (`<!-- issue: -->`) and rebuild |
| `gitbook` | GitBook structure guide, component patterns, navigation templates |
| `workshop-creator` | Workshop Studio directives, module templates, CloudFormation references |
| `brochure` | Single-page responsive brochure (self-contained HTML), editorial design system, embedded architecture SVG, public GitHub Pages deploy |

### Operations Skills

| Skill | Provides |
|-------|----------|
| `ops-troubleshoot` | Systematic troubleshooting framework, incident response procedures |
| `ops-health-check` | Infrastructure health assessment across 6 domains |
| `ops-network-diagnosis` | VPC CNI, Load Balancer, DNS deep diagnosis references |
| `ops-observability` | CloudWatch, Prometheus, log analysis configuration |
| `ops-security-audit` | IAM audit, network security, compliance scan procedures |
| `ops-wellarchitected-review` | 6-pillar assessment, 100-point scoring, AS-IS/TO-BE roadmap |

### Conversion and Scaffolding Skills

| Skill | Provides |
|-------|----------|
| `kiro-convert` | Plugin-to-Kiro-Power conversion workflow |
| `agentcore-create` | 5-phase AgentCore design, build, convert, deploy workflow |
| `co-agent` | Multi-AI collaboration (Kiro/Codex/Antigravity — `agy`, Gemini fallback) — review, decision support, ADR co-authoring, and `sync-context`; Claude chairs. Commands: `/co-agent:configure`, `/co-agent:sync-context`, `/co-agent:consensus` |
| `project-scaffolder` | Claude Code project structure patterns and conventions |
| `pr-autofix` | Poll AI + human PR review feedback and auto-fix issues (max 3 iterations) |
| `decision-reconcile` | Detect contradictions across accumulated ADRs (and ADR-vs-reality drift) via a diverse multi-agent panel (varied Claude model tiers + optional Kiro/Codex/Antigravity-or-Gemini, one review lens each), then draft a superseding ADR |

### Project Init Commands

| Command | What It Does |
|---------|--------------|
| `/init-project` | Initialize Claude Code project structure |
| `/sync-docs` | Synchronize documentation with code |
| `/add-adr` | Create Architecture Decision Record |
| `/add-module` | Add module directory with CLAUDE.md |
| `/add-runbook` | Create operational runbook |
| `/generate-readme` | Generate bilingual README.md |
| `/generate-changelog` | Generate bilingual CHANGELOG.md |
| `/health-check` | Validate project setup |

---

## Workflows

### Content Workflows

```
Presentations:     presentation-agent  -->  content-review-agent  -->  GitHub Pages
Static diagrams:   architecture-diagram-agent  -->  .drawio  -->  PNG export
Animated diagrams: animated-diagram-agent  -->  .html (SVG + SMIL)
Documents:         document-agent  -->  content-review-agent  -->  .md
GitBook:           gitbook-agent  -->  content-review-agent  -->  git push
Workshops:         workshop-agent  -->  content-review-agent  -->  Workshop Studio
```

### Operations Workflows

```
Incident response:  ops-coordinator  -->  specialist agents  -->  root cause  -->  resolve  -->  verify
Troubleshooting:    matched agent  -->  diagnose  -->  resolve  -->  verify
Health check:       ops-health-check skill  -->  6-domain assessment
Security audit:     ops-security-audit skill  -->  IAM + network + compliance
Well-Architected:   wellarchitected-agent  -->  6-pillar scoring  -->  AS-IS/TO-BE roadmap
```

### Conversion and Review Workflows

```
Kiro conversion:   plugin source  -->  kiro-converter-agent  -->  Kiro Power directory  -->  install/export
AgentCore deploy:  discovery  -->  design  -->  skill-first build  -->  AgentCore convert  -->  deploy
Co-agent collab:     prompt  -->  fan-out to Kiro/Codex/Antigravity(agy->gemini fallback)  -->  Claude synthesizes  -->  review / decision / ADR / sync-context
Doc sync:          /sync-docs  -->  doc-sync-checker  -->  quality scores  -->  update docs
```

Diagrams can be embedded into presentations, documents, or GitBook pages as part of a larger workflow.

---

## Quality Gate

All content passes through `content-review-agent` which scores on a 100-point scale across layout, terminology, language, accessibility, and structural completeness.

| Verdict | Score | Condition | Result |
|---------|-------|-----------|--------|
| **PASS** | >= 85 | Critical 0, Warning <= 3 | Approved for deployment |
| **REVIEW** | 70-84 | Critical 0, Warning 4-10 | Fix issues and re-review |
| **FAIL** | < 70 | Critical >= 1 or Warning > 10 | Cannot proceed |

---

## Project Structure

```
plugins/
├── aws-content-plugin/                # Content creation (9 agents, 8 skills)
│   ├── .claude-plugin/plugin.json
│   ├── CLAUDE.md
│   ├── agents/                        # 9 agents
│   │   ├── presentation-agent.md      # Format dispatcher (Web vs PPTX)
│   │   ├── reactive-presentation-agent.md # Interactive HTML slideshows
│   │   ├── architecture-diagram-agent.md  # Draw.io XML diagrams
│   │   ├── animated-diagram-agent.md  # SVG + SMIL animations
│   │   ├── document-agent.md          # Markdown documents & reports
│   │   ├── gitbook-agent.md           # GitBook documentation sites
│   │   ├── workshop-agent.md          # AWS Workshop Studio content
│   │   ├── brochure-agent.md          # Single-page responsive brochure
│   │   └── content-review-agent.md    # Cross-cutting quality review
│   └── skills/                        # 8 skills
│       ├── reactive-presentation/     # Presentation framework + AWS icons
│       ├── architecture-diagram/      # Draw.io templates & patterns
│       ├── animated-diagram/          # SMIL animation guide & templates
│       ├── gitbook/                   # GitBook structure & components
│       ├── workshop-creator/          # Workshop Studio directives & templates
│       ├── slide-fix/                 # Slide issue annotation processing
│       ├── brochure/                  # Responsive brochure design system
│       └── aws-light-fcd/             # Native PPTX decks (PptxGenJS, AWS Light theme)
│
├── aws-ops-plugin/                    # Infrastructure operations (10 agents, 6 skills)
│   ├── .claude-plugin/plugin.json
│   ├── CLAUDE.md
│   ├── agents/                        # 10 agents
│   │   ├── eks-agent.md               # EKS cluster operations
│   │   ├── network-agent.md           # VPC CNI, ALB/NLB, DNS
│   │   ├── iam-agent.md               # IRSA, Pod Identity, RBAC
│   │   ├── observability-agent.md     # CloudWatch, Prometheus, Grafana
│   │   ├── storage-agent.md           # EBS/EFS/FSx CSI drivers
│   │   ├── database-agent.md          # RDS, Aurora, DynamoDB, ElastiCache
│   │   ├── cost-agent.md              # Cost analysis & optimization
│   │   ├── analytics-agent.md         # OpenSearch, Athena, QuickSight, Kinesis
│   │   ├── ops-coordinator-agent.md   # Multi-domain incident coordination
│   │   └── wellarchitected-agent.md   # Well-Architected 6-pillar review
│   └── skills/                        # 6 skills
│       ├── ops-troubleshoot/          # Systematic troubleshooting
│       ├── ops-health-check/          # Infrastructure health assessment
│       ├── ops-network-diagnosis/     # VPC CNI, LB, DNS deep diagnosis
│       ├── ops-observability/         # CloudWatch, Prometheus, log analysis
│       ├── ops-security-audit/        # IAM audit, network security, compliance
│       └── ops-wellarchitected-review/ # 6-pillar scoring, AS-IS/TO-BE roadmap
│
├── kiro-power-converter/              # Claude Code → Kiro Power (1 agent, 1 skill)
│   ├── .claude-plugin/plugin.json
│   ├── CLAUDE.md
│   ├── agents/
│   │   └── kiro-converter-agent.md
│   └── skills/
│       └── kiro-convert/
│
├── agentcore-creator/                 # Claude Code → Bedrock AgentCore (1 agent, 1 skill)
│   ├── .claude-plugin/plugin.json
│   ├── CLAUDE.md
│   ├── agents/
│   │   └── agentcore-creator-agent.md
│   └── skills/
│       └── agentcore-create/
│
├── co-agent/                       # Multi-AI collaboration (1 agent, 1 skill, 3 commands)
│   ├── .claude-plugin/plugin.json
│   ├── CLAUDE.md
│   ├── agents/
│   │   └── co-agent.md
│   ├── commands/                   # /co-agent:configure, /co-agent:sync-context, /co-agent:consensus
│   └── skills/
│       └── co-agent/
│
└── project-init/                      # Project scaffolding (1 agent, 3 skills, 10 commands)
    ├── .claude-plugin/plugin.json
    ├── CLAUDE.md
    ├── agents/
    │   └── doc-sync-checker.md
    ├── commands/                       # 10 slash commands
    │   ├── init-project.md
    │   ├── sync-docs.md
    │   ├── add-adr.md
    │   ├── add-module.md
    │   ├── add-runbook.md
    │   ├── generate-readme.md
    │   ├── generate-changelog.md
    │   └── health-check.md
    └── skills/
        ├── project-scaffolder/
        ├── pr-autofix/
        └── decision-reconcile/
```
