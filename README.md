# oh-my-cloud-skills

[한국어](README.ko.md)

AWS cloud plugins for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — content creation and infrastructure operations.

**What you can do:**

*Content Creation (aws-content-plugin):*
- **Interactive HTML/CSS/JS presentations** — Canvas animations, quizzes, presenter view, deployed to GitHub Pages
- **AWS architecture diagrams** — Draw.io XML with auto-layout, exportable to PNG/SVG
- **Animated traffic flow diagrams** — SVG + SMIL animations with interactive legends
- **Technical documents** — Professional Markdown reports and comparisons
- **GitBook documentation sites** — Structured docs with navigation and components
- **AWS Workshop Studio content** — Hands-on labs with multi-language support

*Infrastructure Operations (aws-ops-plugin):*
- **EKS troubleshooting** — Node issues, upgrades, add-ons, 5-minute triage
- **Network diagnostics** — VPC CNI, ALB/NLB, DNS, IP exhaustion
- **IAM & security** — IRSA, Pod Identity, RBAC, policy validation
- **Observability** — CloudWatch, Container Insights, Prometheus, X-Ray
- **Cost optimization** — Pricing analysis, savings plans, right-sizing

---

## Installation

```bash
# Add the marketplace
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills

# Install plugins
/plugin install aws-content-plugin@oh-my-cloud-skills
/plugin install aws-ops-plugin@oh-my-cloud-skills
```

For local development:
```bash
# Load plugins from local directory
claude --plugin-dir ./plugins/aws-content-plugin
claude --plugin-dir ./plugins/aws-ops-plugin
```

Uninstall:
```bash
# Uninstall plugins
/plugin uninstall aws-content-plugin@oh-my-cloud-skills
/plugin uninstall aws-ops-plugin@oh-my-cloud-skills

# Remove the marketplace
/plugin marketplace remove oh-my-cloud-skills
```

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
│   ├── export-utils.js             # PDF export and ZIP download
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
| Pain Quote | Customer problem statement with challenge list |

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| `<-` `->` | Previous / Next slide |
| `Space` | Next slide |
| `F` | Toggle fullscreen |
| `P` | Open presenter view (new window) |
| `Esc` | Exit fullscreen |
| `Home` / `End` | First / Last slide |

### How it works

1. **Plan** — Claude asks about topic, audience, duration, language, and optional PPTX template for corporate branding
2. **Author** — Writes Marp markdown as the content source of truth
3. **Generate** — Builds HTML files with Canvas animations and interactive elements inline
4. **Review** — Interactive feedback loop: edit Marp directly, request changes via prompt, or proceed
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

Before generating content, Claude asks 7 planning questions to tailor the presentation:

| # | Question | Description | Default |
|---|----------|-------------|---------|
| 1 | Topic and audience | Technical depth, pain points, learning objectives | — |
| 2 | Duration | Total length — determines block count and slide count | — |
| 3 | Blocks | 20-35 min per block with 5 min breaks between blocks | Auto-split based on duration |
| 4 | Target repo | GitHub repo for deployment | `~/reactive_presentation/` |
| 5 | Language | Korean or English (technical terms always in English) | Korean |
| 6 | PPTX template | Corporate branding `.pptx` file for theme extraction | None (dark theme) |
| 7 | Speaker info | Name and affiliation for the cover slide (stored for reuse) | — |

After gathering answers, Claude writes Marp markdown content and generates interactive HTML slides.

#### Review and Iteration

After Claude generates the initial content, you enter a review loop with three options:

1. **Edit Marp directly** — Open the `.md` file in your editor, make changes, then say "done". Claude reads your edits and updates the HTML to match.

2. **Request changes via prompt** — Describe what to change (e.g., "add a quiz after slide 5", "reduce the timeline to 3 steps"). Claude updates both the Marp source and HTML files.

3. **Proceed** — If the content looks good, approve it and move to the enhancement phase where Canvas animations and interactive elements are added.

This loop repeats until you are satisfied. Marp markdown stays in sync with the HTML at all times — Marp is the content source of truth, HTML adds interactivity on top.

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
| `cloudwatch-agent` | Observability | "Set up Container Insights for EKS" |
| `storage-agent` | Storage | "PVC stuck in Pending state" |
| `database-agent` | Database | "Aurora connection timeout from EKS" |
| `cost-agent` | Cost | "Analyze my EKS cluster costs" |
| `ops-coordinator-agent` | Incidents | "Production outage, coordinate response" |

### Skills

| Skill | Trigger | What It Does |
|-------|---------|--------------|
| `ops-troubleshoot` | "troubleshoot", "debug" | Systematic 5-min triage → investigate → resolve → postmortem |
| `ops-health-check` | "health check" | Full 6-domain infrastructure assessment |
| `ops-network-diagnosis` | "network issue" | VPC CNI, Load Balancer, DNS deep diagnosis |
| `ops-observability` | "monitoring setup" | CloudWatch, Prometheus, log analysis |
| `ops-security-audit` | "security audit" | IAM audit, network security, compliance |

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
                └── Logs    → cloudwatch-agent
              ← Aggregate → Root cause → Resolve → Verify
```

All agents activate automatically when Claude detects matching keywords.

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
| `content-review-agent` | Quality review | "Review the presentation" | Review report |

### Operations Agents

| Agent | Domain | Example Prompt | Output |
|-------|--------|----------------|--------|
| `eks-agent` | EKS clusters | "Node NotReady, troubleshoot" | Diagnosis + fix |
| `network-agent` | Networking | "VPC CNI IP exhaustion" | Diagnosis + fix |
| `iam-agent` | IAM/RBAC | "Pod can't access S3" | Policy fix |
| `cloudwatch-agent` | Observability | "Set up Container Insights" | Config + queries |
| `storage-agent` | Storage | "PVC stuck in Pending" | Diagnosis + fix |
| `database-agent` | Database | "Aurora timeout from EKS" | Diagnosis + fix |
| `cost-agent` | Cost | "Analyze cluster costs" | Cost report |
| `ops-coordinator-agent` | Incidents | "Production outage" | Coordinated response |

All agents activate automatically when Claude detects matching keywords in your prompt.

---

## Skills

### Content Skills

| Skill | Provides |
|-------|----------|
| `reactive-presentation` | Presentation framework (CSS/JS), Marp conversion scripts, AWS icon extraction, slide pattern reference |
| `architecture-diagram` | Draw.io XML templates, AWS icon reference, layout patterns |
| `animated-diagram` | SMIL animation guide, HTML wrapper templates, traffic flow patterns |
| `gitbook` | GitBook structure guide, component patterns, navigation templates |
| `workshop-creator` | Workshop Studio directives, module templates, CloudFormation references |

### Operations Skills

| Skill | Provides |
|-------|----------|
| `ops-troubleshoot` | Systematic troubleshooting framework, incident response procedures |
| `ops-health-check` | Infrastructure health assessment across 6 domains |
| `ops-network-diagnosis` | VPC CNI, Load Balancer, DNS deep diagnosis references |
| `ops-observability` | CloudWatch, Prometheus, log analysis configuration |
| `ops-security-audit` | IAM audit, network security, compliance scan procedures |

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
Incident response: ops-coordinator  -->  specialist agents  -->  root cause  -->  resolve  -->  verify
Troubleshooting:   matched agent  -->  diagnose  -->  resolve  -->  verify
Health check:      ops-health-check skill  -->  6-domain assessment
Security audit:    ops-security-audit skill  -->  IAM + network + compliance
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
├── aws-content-plugin/                # Content creation plugin
│   ├── .claude-plugin/plugin.json     # Plugin manifest (7 agents, 5 skills)
│   ├── CLAUDE.md                      # Auto-invocation rules & workflows
│   ├── agents/
│   │   ├── presentation-agent.md      # Interactive HTML slideshows
│   │   ├── architecture-diagram-agent.md # Draw.io XML diagrams
│   │   ├── animated-diagram-agent.md  # SVG + SMIL animations
│   │   ├── document-agent.md          # Markdown documents & reports
│   │   ├── gitbook-agent.md           # GitBook documentation sites
│   │   ├── workshop-agent.md          # AWS Workshop Studio content
│   │   └── content-review-agent.md    # Cross-cutting quality review
│   └── skills/
│       ├── reactive-presentation/     # Presentation framework + AWS icons
│       │   ├── SKILL.md               # Workflow & slide type reference
│       │   ├── assets/                # theme.css, slide-framework.js, export-utils.js, ...
│       │   ├── scripts/               # marp_to_slides.py, extract_pptx_theme.py
│       │   ├── references/            # framework-guide.md, slide-patterns.md
│       │   └── icons/                 # AWS Architecture Icons (4,224 files)
│       ├── architecture-diagram/      # Draw.io templates & patterns
│       ├── animated-diagram/          # SMIL animation guide & templates
│       ├── gitbook/                   # GitBook structure & components
│       └── workshop-creator/          # Workshop Studio directives & templates
│
└── aws-ops-plugin/                    # Infrastructure operations plugin
    ├── .claude-plugin/plugin.json     # Plugin manifest (8 agents, 5 skills)
    ├── .mcp.json                      # AWS MCP servers configuration
    ├── CLAUDE.md                      # Auto-invocation rules & workflows
    ├── agents/
    │   ├── eks-agent.md               # EKS cluster operations
    │   ├── network-agent.md           # VPC CNI, ALB/NLB, DNS
    │   ├── iam-agent.md               # IRSA, Pod Identity, RBAC
    │   ├── cloudwatch-agent.md        # Metrics, logs, alarms, X-Ray
    │   ├── storage-agent.md           # EBS/EFS/FSx CSI drivers
    │   ├── database-agent.md          # RDS, Aurora, DynamoDB, ElastiCache
    │   ├── cost-agent.md              # Cost analysis & optimization
    │   └── ops-coordinator-agent.md   # Multi-domain incident coordination
    └── skills/
        ├── ops-troubleshoot/          # Systematic troubleshooting
        ├── ops-health-check/          # Infrastructure health assessment
        ├── ops-network-diagnosis/     # VPC CNI, LB, DNS deep diagnosis
        ├── ops-observability/         # CloudWatch, Prometheus, log analysis
        └── ops-security-audit/        # IAM audit, network security, compliance
```
