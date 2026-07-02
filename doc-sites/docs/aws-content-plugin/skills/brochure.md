---
sidebar_position: 6
title: "Brochure"
---

# Brochure Skill

Build a **single-page, responsive marketing brochure** for an AWS solution as a
**self-contained HTML file** (one HTML entry with CSS inlined — no build step, no
framework — plus its architecture SVG as an adjacent asset), readable on mobile,
tablet, and PC, hosted publicly on GitHub Pages.

A brochure is **persuasion + clarity for a dual audience**: a decision-maker grasps the
value in 10 seconds, an engineer drills into features and architecture without leaving
the page. It is one scroll — not a slide deck, not a docs site.

## Trigger Keywords

- "brochure", "online brochure", "landing page", "marketing one-pager"
- "product overview page", "solution showcase"
- "브로셔", "브로셔 만들어", "온라인 브로셔", "랜딩 페이지", "소개 페이지"

## When this applies (and when it doesn't)

| Need | Use |
|------|-----|
| Product/solution landing page, one-page overview, public value+architecture showcase | **brochure** (this skill) |
| Slide decks / talks / training | `reactive-presentation` |
| Multi-page documentation sites | `gitbook` |

A brochure may **embed** an architecture diagram — produce it with the
**`architecture-diagram`** skill, then embed the exported SVG.

## Workflow

```
brochure-agent → gather product facts → (architecture-diagram skill → SVG)
  → write self-contained HTML → self-check script → content-review-agent (≥85)
  → deploy to GitHub Pages (public)
```

| Phase | What happens |
|-------|--------------|
| 1. Gather facts | Pin down core message, value props, features, metrics, architecture — from repo/README/user. **Never fabricate** metrics, feature counts, or service names. |
| 2. Architecture SVG | Generate via the `architecture-diagram` skill, export SVG, embed it. |
| 3. Write HTML | One self-contained `.html`, CSS inlined; editorial design direction (no generic purple-gradient templates). |
| 4. Responsive + a11y | 3-tier responsive (375/768/1280px), mobile tables → cards, WCAG-AA, `prefers-reduced-motion`. |
| 5. Review + deploy | Self-check script → `content-review-agent` (≥85) → public GitHub Pages. |

## Provided Resources

### references/

| Reference Doc | Description |
|---------------|-------------|
| `design-system.md` | Editorial design direction, responsive + accessibility checklist |

### assets/

| Asset | Description |
|-------|-------------|
| `example-brochure/` | Calibration exemplar — `index.html` + `awsops-arch.drawio`/`.svg` |

### scripts/

| Script | Description |
|--------|-------------|
| `check_brochure.py` | Self-check: self-containment, responsive breakpoints, accessibility, diagram embed |

## Mandatory Rules

1. **Facts first** — no invented metrics/feature-counts/service names.
2. **Self-contained HTML** — single `.html`, inlined CSS, system font fallback, no build tooling.
3. **3-tier responsive** — mobile/tablet/PC verified; mobile tables reflow to cards.
4. **Accessibility** — skip-link, `:focus-visible`, `prefers-reduced-motion`, WCAG-AA contrast.
5. **Design direction** — one intentional editorial direction, precisely executed.
6. **Diagram consistency** — brochure copy and the embedded diagram tell the same story (same components/numbers).
