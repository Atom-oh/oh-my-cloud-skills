---
sidebar_position: 7
title: "Profile Page"
---

# Profile Page Skill

Build a **single-page, responsive personal profile / developer portfolio** as a
**self-contained HTML file** (one HTML entry with CSS inlined — no build step, no
framework), readable on mobile, tablet, and PC, hosted publicly on GitHub Pages.

A profile page is a **personal front door**, not a product pitch: sidebar identity
(photo, name, links), about, experience timeline, skills, and a real project showcase
with working GitHub + Live links (and an optional per-repo Demo link, asked from the user).

## Trigger Keywords

- "profile page", "portfolio", "developer portfolio", "about me page", "resume/CV page"
- "프로필 페이지", "포트폴리오", "자기소개 페이지", "프로젝트 소개 페이지"

## When this applies (and when it doesn't)

| Need | Use |
|------|-----|
| Personal "about me" / portfolio / project showcase page | **profile-page** (this skill) |
| Product/solution marketing landing page | `brochure` |
| Slide decks / talks / training | `reactive-presentation` |
| Multi-page documentation sites | `gitbook` |

## Workflow

```
gather facts (reuse existing page / GitHub / user confirmation) → write self-contained HTML
  → check_brochure.py (shared with brochure) → content-review-agent (≥85) → GitHub Pages (public)
```

| Phase | What happens |
|-------|--------------|
| 1. Gather facts | Preflight: confirm the target public GitHub Pages repo + `gh auth status`. Reuse an existing profile page if one exists; derive from GitHub via `gh` (**Pages-enabled repos are the primary showcase candidates**); optionally pull experience from a user-provided LinkedIn URL (WebFetch, user-confirmed candidate facts; expect the auth wall and fall back to asking); confirm the project selection with the user. **Never fabricate** roles, dates, or projects. |
| 2. Design | Read `references/profile-design.md`; reuse the person's existing aesthetic if any. |
| 3. Write HTML | One self-contained `.html` — sidebar + about + experience + skills + projects. |
| 4. Self-check + review | Reuses the `brochure` skill's `check_brochure.py` → `content-review-agent` (≥85). |
| 5. Deploy | GitHub Pages; confirm before overwriting an existing `index.html`; preserve unrelated files (CNAME, robots.txt, analytics). |

## Provided Resources

### references/

| Reference Doc | Description |
|---------------|-------------|
| `profile-design.md` | Section spine, sidebar layout, timeline pattern, project-card grid, tokens, accessibility checklist |

No separate self-check script ships with this skill — it reuses `brochure`'s
`scripts/check_brochure.py` (the same structural/responsive/a11y checks apply).

## Mandatory Rules

1. **Facts first** — no invented job titles, dates, or projects; verify Live/GitHub links resolve.
2. **Self-contained HTML** — single `.html`, inlined CSS, no build tooling.
3. **Responsive** — sidebar stacks above content on mobile, never hidden.
4. **Accessibility** — `:focus-visible`, `prefers-reduced-motion` if motion is used, avatar `alt` text.
5. **Preserve on refresh** — don't drop existing CNAME/robots.txt/analytics files or overwrite an existing page without confirming.
