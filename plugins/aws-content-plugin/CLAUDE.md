# AWS Content Plugin — Claude Code Configuration

A unified plugin for AWS cloud content creation: presentations, architecture diagrams, animated diagrams, documents, GitBook documentation sites, workshops, and brochures.

---

## Workflow Patterns

### Presentation Workflow
```
# Web/HTML (interactive):
presentation-agent (dispatcher) → reactive-presentation-agent → validate (rejection loop) → build → content-review-agent → Deploy (GitHub Pages)
# Native PowerPoint (.pptx):
presentation-agent (dispatcher) → aws-light-fcd skill (PptxGenJS, AWS Light theme) → check_pptx.py (rejection loop, ≥80 AND zero geometry findings) → embed_fonts.py → content-review-agent → .pptx
```
> After authoring in Remarp, run the `remarp_to_slides.py validate` rejection loop: there must be zero CRITICAL findings before building.
> **PPTX branch**: on a "pptx/PowerPoint/ppt" keyword or when the user picks PPTX, the dispatcher routes to the `aws-light-fcd` skill (python-pptx is not hand-written because the skill owns the validated design system and font embedding). The single gate in the pipeline above is `check_pptx.py`: score ≥80 **and** zero `[geometry]` findings — a geometry defect fails regardless of score.

### Architecture Diagram Workflow
```
# Recommended (VPC/Multi-AZ · serverless · multi-region · hybrid):
architecture-diagram-agent → layout_aws.py (YAML spec → .drawio) → validate + lint (100/100) → PNG export
# Hand-authored (non-standard shapes only): → .drawio → validate + lint → PNG export
→ (embed in presentation/document/gitbook)
```
> For standard patterns, don't place coordinates by hand — use the `skills/architecture-diagram/scripts/layout_aws.py` spec generator. Golden examples: `skills/architecture-diagram/examples/`.

### Animated Diagram Workflow
```
animated-diagram-agent → .html + .svg → (embed in presentation/gitbook or standalone)
```

### Document Workflow
```
document-agent → content-review-agent → .md output
```

### GitBook Workflow
```
gitbook-agent → content-review-agent → GitBook pages → git push
```

### Workshop Workflow
```
workshop-agent → content-review-agent → Workshop Studio content
```

### Brochure Workflow
```
brochure-agent → gather product facts → (architecture-diagram → SVG) → (Playwright UI capture)
  → self-contained responsive HTML → check_brochure.py → content-review-agent (≥85)
  → GitHub Pages (public, verify no-auth 200)
```
> One self-contained HTML file (mobile/tablet/PC responsive). **A product with a web UI requires a real screenshot section** — capture it with Playwright MCP; if you don't know the URL or how to run it, ask. Build the architecture diagram with `architecture-diagram` and embed it as SVG, keeping the diagram consistent with the copy's story. **Public hosting is GitHub Pages** — a domain behind an auth edge (Cognito Lambda@Edge, etc.) can't be published there unless it has a public bypass path.

### Profile Page (gh-home) Workflow
```
gather facts (existing page / GitHub / user confirmation) → self-contained responsive HTML (sidebar+about+experience+skills+projects)
  → check_brochure.py (shared with the brochure skill) → content-review-agent (≥85) → GitHub Pages (public)
```
> A personal profile/portfolio page (the subject is a person, not a product/solution) — distinct from a brochure. Never invent career history or projects; populate it only from an existing page, GitHub, or user confirmation. If an existing `index.html` is present, **confirm before overwriting**, and preserve unrelated files such as CNAME/robots.txt/analytics scripts.

---

## Team Workflow Patterns (parallel orchestration)

**The default is a sequential workflow.** Team-based parallelism is used only when the triggers below are met:

| Trigger | Team | Pipeline |
|--------|----|-----------|
| Presentation ≥60 min or 3+ blocks | `content-presentation` | Multi-Phase |
| Workshop with 3+ modules | `content-workshop` | Multi-Phase |
| GitBook with 5+ chapters | `content-gitbook` | Block-Parallel |
| Presentation + diagram + document requested together | `content-cross-type` | Cross-Type |

When a trigger is met, spawn subagents (one in parallel per block); otherwise stay sequential. Also use this when the user explicitly says "in parallel / simultaneously / as a team."

> **Details** (the 4 Multi-Phase stages, Subagent Spawn Policy, Phase-to-phase data handoff, orchestration execution order, Block-Parallel): **`references/team-workflows.md`** — consult it when actually spawning a team.

---

## Quality Gate (Mandatory)

> **Rule: a deliverable must pass content-review-agent before it is declared deployed/complete.**
> This applies to new artifacts and substantive revisions. Minor touch-ups such as
> typo fixes or one-line edits can be applied without re-passing the gate, but at the
> moment completion/deployment is declared, a valid PASS review for that deliverable
> must exist.

### Auto-Trigger

As soon as a deliverable is finished — slide/animation `.html`, `.drawio`, technical-doc `.md`, GitBook/Workshop project, brochure/profile `.html`, `.pptx` (after the check_pptx.py gate + embed_fonts.py) — invoke content-review-agent with `review content at [path]`.

### Review Loop

On a FAIL/REVIEW verdict, fix and re-review. Declare completion/deployment only after PASS. If PASS still isn't reached after 3 re-reviews, hand the decision to the user.

### Verdict

| Verdict | Condition | Result |
|---------|-----------|--------|
| **PASS** | Critical 0, Warning ≤3, Score ≥85 | Approved |
| **REVIEW** | Critical 0, Warning 4-10, Score 70-84 | Fix and re-review |
| **FAIL** | Critical ≥1 or Warning >10 or Score <70 | Cannot proceed |

> Content exempt from Visual Testing (Markdown, Draw.io, Workshop, PPTX, or when
> Playwright is unavailable) uses the **90-point** scale: PASS ≥77 / REVIEW 63-76 /
> FAIL <63. The review report must state which scale it used.

---

## Agents

| Agent | Purpose |
|-------|---------|
| `presentation-agent` | Presentation format dispatcher (PPTX vs Web) |
| `reactive-presentation-agent` | Interactive HTML slideshows (reactive-presentation framework, Remarp) |
| `architecture-diagram-agent` | Static Draw.io XML diagrams → PNG/SVG export |
| `animated-diagram-agent` | Dynamic SVG diagrams with SMIL animations |
| `document-agent` | Markdown documents and reports |
| `gitbook-agent` | GitBook documentation sites |
| `workshop-agent` | AWS Workshop Studio content |
| `brochure-agent` | Single-page responsive marketing brochure (HTML → GitHub Pages) |
| `content-review-agent` | Cross-cutting quality review (all content types) |

## Skills

| Skill | Purpose |
|-------|---------|
| `reactive-presentation` | Presentation framework assets, scripts, references, AWS icons |
| `architecture-diagram` | Draw.io templates, AWS icon reference, layout patterns |
| `animated-diagram` | SMIL animation guide, HTML templates, AWS diagram patterns |
| `gitbook` | GitBook structure guide, component patterns |
| `slide-fix` | Issue annotation-based slide repair (reads `<!-- issue: -->`, fixes, rebuilds) |
| `workshop-creator` | Workshop Studio directives, templates, references |
| `brochure` | Responsive brochure design system, golden example, self-check script |
| `gh-home` | Personal profile / developer portfolio page design system — sidebar+timeline+project-card spine; reuses `brochure`'s self-check script |
| `aws-light-fcd` | Native **PPTX** decks (PptxGenJS) — AWS Light theme, Pretendard, 11 layout builders + arch-diagram kit; shares the 811-icon library via `kit.icon()` |

---

## AWS Icons (Mandatory)

AWS Architecture Icons are located in `skills/reactive-presentation/assets/aws-icons/`:
- `Architecture-Service-Icons_07312025/` — Service-level icons (121 categories)
- `Architecture-Group-Icons_07312025/` — Group icons (Cloud, VPC, Region, Subnet)
- `Category-Icons_07312025/` — Category-level icons (4 sizes)
- `Resource-Icons_07312025/` — Resource-level icons (22 categories)
- `others/` — Third-party icons (LangChain, Grafana, etc.)

> **Rule**: any slide that visually represents an AWS service (architecture, service
> introduction, diagrams) must use this bundle's **official icons** — do not draw ad hoc
> substitute graphics. Icons are not mandatory on slides where the service name only
> appears as text (agenda, code, comparison tables). Failing to use the official icons
> costs points in content-review-agent.

---

## Diagram Agent Selection Guide

| Need | Agent | Output |
|------|-------|--------|
| Static AWS architecture | `architecture-diagram-agent` | .drawio → .png |
| Animated traffic flow | `animated-diagram-agent` | .html with SVG + SMIL |
| Workshop inline diagram | `workshop-agent` (Mermaid) | Mermaid in markdown |
| Presentation Canvas animation | `reactive-presentation-agent` | Canvas JS in HTML slides |
