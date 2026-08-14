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
> **Required**: After writing Remarp content, run the rejection loop via `remarp_to_slides.py validate`. Proceed to build only when CRITICAL issue count is 0.
> **PPTX branch**: When the "pptx/PowerPoint/ppt" keyword appears, or the user selects PPTX, the dispatcher routes to the `aws-light-fcd` skill. Writing python-pptx directly is forbidden — always call the skill. **Required**: proceed to embed_fonts.py only after `check_pptx.py` reports a score ≥80 **and** zero `[geometry]` findings (rejection loop) — a geometry defect fails the gate regardless of score.

### Architecture Diagram Workflow
```
# Recommended (VPC/Multi-AZ · serverless · multi-region · hybrid):
architecture-diagram-agent → layout_aws.py (YAML spec → .drawio) → validate + lint (100/100) → PNG export
# Hand-authored (non-standard shapes only): → .drawio → validate + lint → PNG export
→ (embed in presentation/document/gitbook)
```
> For standard patterns, do not hand-place coordinates — use the `skills/architecture-diagram/scripts/layout_aws.py` spec generator. Golden examples: `skills/architecture-diagram/examples/`.

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
> A single self-contained HTML file (responsive across mobile/tablet/PC). **A product with a web UI requires a screenshot section (4–6 shots)** — capture with Playwright MCP, and ask for confirmation if the URL or how to run it is unknown. Build the architecture with `architecture-diagram`, embed it as an SVG, and keep it telling the same story as the copy. **Public hosting is GitHub Pages** — a domain sitting behind an auth edge (e.g. Cognito Lambda@Edge) cannot be published there unless it has a public bypass path.

### Profile Page (gh-home) Workflow
```
gather facts (existing page / GitHub / user confirmation) → self-contained responsive HTML (sidebar+about+experience+skills+projects)
  → check_brochure.py (shared with the brochure skill) → content-review-agent (≥85) → GitHub Pages (public)
```
> A personal profile/portfolio page (subject is a person, not a product/solution) — distinct from brochure. Never fabricate experience or projects; fill them in only from an existing page, GitHub, or user confirmation. If an existing `index.html` exists, **confirm before overwriting**, and preserve unrelated files such as CNAME/robots.txt/analytics scripts.

---

## Team Workflow Patterns (Parallel Orchestration)

**The default is a sequential workflow.** Team-based parallel execution is used only when the triggers below are met:

| Trigger | Team | Pipeline |
|--------|----|-----------|
| Presentation ≥60 min or 3+ blocks | `content-presentation` | Multi-Phase |
| Workshop with 3+ modules | `content-workshop` | Multi-Phase |
| GitBook with 5+ chapters | `content-gitbook` | Block-Parallel |
| Simultaneous presentation+diagram+document request | `content-cross-type` | Cross-Type |

When a trigger is met, spawn subagents (one per block, in parallel); otherwise run sequentially. Also use this when the user explicitly asks for "parallel/at the same time/as a team."

> **Details** (the Multi-Phase 4 stages, Subagent Spawn Policy, inter-phase data handoff, orchestration execution order, Block-Parallel): **`references/team-workflows.md`** — consult this when actually spawning a team.

---

## Quality Gate (Mandatory)

> **Rule: a deliverable must pass content-review-agent before deployment/completion is declared.**
> This applies to new artifacts and substantive revisions. Minor touch-ups such as typo
> fixes or one-line edits can be applied without re-passing the gate, but at the moment
> completion/deployment is declared, a valid PASS review for that deliverable must exist.

### Auto-Trigger Conditions

content-review-agent is invoked automatically when the following conditions are met:

| Trigger | Condition | Action |
|---------|-----------|--------|
| HTML presentation complete | `.html` slide file finished | `review content at [file path]` |
| Diagram complete | `.drawio` or animated `.html` finished | `review content at [file path]` |
| Document complete | `.md` technical document finished | `review content at [file path]` |
| GitBook pages complete | GitBook project structure finished | `review content at [project path]` |
| Workshop content complete | Workshop module content finished | `review content at [project path]` |
| Brochure complete | Brochure `.html` finished | `review content at [file path]` |
| Profile page complete | Profile page `.html` finished | `review content at [file path]` |
| PPTX deck complete | `.pptx` finished (after check_pptx.py gate passes + embed_fonts.py runs) | `review content at [file path]` |

### Review Loop

1. Content agent finishes generating content
2. Invoke content-review-agent → produces a review report
3. On a FAIL/REVIEW verdict → fix and re-review (max 3 rounds)
4. Declare completion/deployment only after achieving PASS (≥85 points)
5. If still below PASS after 3 reviews → ask the user for a judgment call

### Verdict

| Verdict | Condition | Result |
|---------|-----------|--------|
| **PASS** | Critical 0, Warning ≤3, Score ≥85 | Approved |
| **REVIEW** | Critical 0, Warning 4-10, Score 70-84 | Fix and re-review |
| **FAIL** | Critical ≥1 or Warning >10 or Score <70 | Cannot proceed |

> Content exempt from Visual Testing (Markdown, Draw.io, Workshop, PPTX, or when Playwright
> is unavailable) is judged on a **90-point scale**: PASS ≥77 / REVIEW 63-76 / FAIL <63.
> The review report states which scale applies, so do not misjudge a 77-point PASS on the
> 90-point scale as "below 85."

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

> **Rule**: slides that visually represent AWS services (architecture, service intros,
> configuration diagrams) must use this bundle's **official icons** — hand-drawn
> substitute graphics are forbidden. Slides where a service name only appears in passing
> text (agenda, code, comparison tables) are not required to include icons.
> Not using the official icons is penalized by content-review-agent.

---

## Diagram Agent Selection Guide

| Need | Agent | Output |
|------|-------|--------|
| Static AWS architecture | `architecture-diagram-agent` | .drawio → .png |
| Animated traffic flow | `animated-diagram-agent` | .html with SVG + SMIL |
| Workshop inline diagram | `workshop-agent` (Mermaid) | Mermaid in markdown |
| Presentation Canvas animation | `reactive-presentation-agent` | Canvas JS in HTML slides |
