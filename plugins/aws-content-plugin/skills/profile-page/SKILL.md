---
name: profile-page
description: "Create a single-page, responsive personal profile / developer portfolio page as one self-contained HTML file — sidebar (photo, name, links) + about + experience timeline + skills + featured work + project showcase — deployed publicly via GitHub Pages. Use whenever the user wants a personal profile page, developer portfolio, 'about me' page, resume/CV page, '프로필 페이지', '포트폴리오', '자기소개 페이지', '개인 프로젝트 소개 페이지', or wants to showcase themselves and their projects on the web. Not for a product/solution marketing page (use brochure), slide decks (use reactive-presentation), or multi-page docs sites (use gitbook)."
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - WebFetch
---

# Profile Page

Build a **single-page, responsive personal profile / developer portfolio** as a **self-contained HTML page** (one HTML entry file with CSS inlined — no build step, no framework) — readable on mobile, tablet, and PC — that introduces a person, their experience, their skills, and their projects. Designed to be hosted **publicly** (GitHub Pages).

> **Path variable**: `{skill-dir}` in this document = `{plugin-dir}/skills/profile-page` in agent documents.

A profile page is **a personal front door**, not a product pitch and not a slide deck. A visitor should grasp *who this person is and what they've built* in a few seconds of scanning the sidebar, then be able to scroll through experience, skills, and real projects with working links.

## When this applies (and when it doesn't)

- **Use this skill** for: a personal "about me" / portfolio page, a developer's project showcase, a resume-as-a-webpage, "프로필 페이지" / "포트폴리오" requests.
- **Use `brochure`** instead for a product/solution/SaaS marketing landing page (a company or product is the subject, not a person).
- **Use `reactive-presentation`** instead for slide decks / talks.
- **Use `gitbook`** instead for multi-page documentation sites.

## Workflow

```
gather facts (reuse existing page / repo / user input) → write self-contained HTML
  → check_brochure.py (shared structural gate) → content-review-agent (≥85) → deploy to GitHub Pages (public)
```

### Phase 1 — Gather the facts (don't invent them)

Never fabricate job titles, dates, employers, talks, or project descriptions.

0. **Preflight — target repo + `gh` CLI**: the page ships to a **public GitHub Pages repo** (typically `<user>.github.io`). Confirm which repo is the target with `AskUserQuestion` if the user didn't say, and check `gh auth status`. With `gh` available, most facts below can be derived automatically; without it, everything must come from an existing page and the user — say so up front rather than degrading silently.
1. **Reuse first**: if the target repo already has a profile page (e.g. an existing `index.html` on a GitHub Pages user/org site), read it and treat its content as the source of truth to refresh, not replace blindly — carry over real links, dates, and descriptions unless the user says otherwise.
2. **Derive from GitHub** (needs `gh`): validate the username first (`^[A-Za-z0-9-]{1,39}$`) before interpolating it into any command, then `gh api users/<user>` (bio, location, links) and
   `gh api --paginate "users/<user>/repos?per_page=100&type=owner" --jq '.[] | select(.fork|not) | {name, description, html_url, homepage, has_pages}'`
   (`gh repo list --json` has no Pages field — `has_pages` only exists on the REST repo object, so go through `gh api`; the jq also drops forks, which are not the person's own work).
   **Prioritize repos with `has_pages: true` as showcase candidates** — they come with a working Live + GitHub link pair (Live = `homepage`, or the repo's Pages URL). Repos without Pages get a GitHub link only, and only if the user wants them included.
2b. **LinkedIn (optional input)**: if the user gives a LinkedIn profile URL (fetch `https://` URLs only — reject other schemes), try `WebFetch` on it for experience/title/education — expect LinkedIn's auth wall on unauthenticated requests (it usually blocks). Treat anything you do retrieve as *candidate* facts — show them to the user for confirmation before publishing — and when nothing verifiable comes back, say so and collect experience from the user instead (a single verifiable current role plus a "full history on LinkedIn" link is an honest fallback). Never pad the experience section with guesses.
3. **Confirm the selection and ask what's missing** with `AskUserQuestion` — which of the candidate projects to feature (never silently include every repo), and **per selected repo, whether a separate demo site exists** (a project card carries up to three links — GitHub, Live (Pages), Demo — and Demo can't be derived from the repo, so it must come from the user; omit it rather than guessing). Then any remaining gaps: name, title/role, location, 3–6 experience entries (company, period, one-line description), and skill categories.

Capture:
- **Identity**: name, title, org, location, avatar image, contact/social links (GitHub, LinkedIn, etc.).
- **About**: 1–2 short paragraphs, first person or third person to match the existing tone.
- **Experience**: reverse-chronological entries — period, role, company, one-line description each.
- **Skills**: grouped by category (e.g. Cloud, Languages, Tools) — real, current skills only.
- **Featured work** (optional): talks, blog posts, notable mentions — each with a link.
- **Projects**: name, one-line description, up to three links — GitHub URL + Live (Pages) URL + optional Demo URL (user-supplied, per repo) — verify every listed link resolves before shipping.

### Phase 2 — Commit to a design direction

Read **`references/profile-design.md`** before writing CSS — it has the section spine, sidebar layout pattern, timeline pattern, project-card grid, token sets (dark + light), and accessibility checklist.

Reuse the person's existing page's aesthetic if one exists (colors, fonts, tone) rather than replacing it with a generic template — a portfolio refresh should feel like the same person, updated.

### Phase 3 — Write the self-contained HTML

One `.html` file. Inline the CSS in a `<style>` block; system-font stack is fine (no CDN dependency required, unlike a brochure — a personal page can lean plainer).

Section spine (scale to what the person has; omit what doesn't apply):

```
header      — name + quick nav links (GitHub, LinkedIn, …)
sidebar     — avatar, name, title, org, location, links (sticky on desktop, stacked on mobile)
about       — 1-2 short paragraphs
experience  — reverse-chronological timeline
skills      — grouped tag chips
featured    — talks / blog posts (optional)
projects    — grouped project cards, each with GitHub + Live (Pages) links and an optional Demo link
footer      — copyright + links
```

**Responsive is mandatory** — verify all three tiers:
- **Mobile (~375-768px)**: sidebar stacks above content (single column); the sidebar's `position: sticky` becomes `position: static`.
- **Tablet/PC**: sidebar + content as a two-column grid (sidebar ~280px, content flexible).

Accessibility basics are not optional: viewport meta, `:focus-visible` on links, `prefers-reduced-motion` handling if any motion/transition is used, sufficient text contrast, `alt` text on the avatar image.

### Phase 4 — Self-check, then quality-gate

Reuse the brochure skill's structural checker — it checks tag balance, viewport meta, the mobile breakpoint, `:focus-visible`, `prefers-reduced-motion`, and that local asset references (avatar image, etc.) actually resolve. Pass `--mobile-breakpoint 768`: the checker's default (640) is the brochure design system's breakpoint, while this skill's design spec stacks the sidebar at 768px — without the flag a spec-compliant profile page would fail the gate:

```bash
python3 {skill-dir}/../brochure/scripts/check_brochure.py <profile.html> --mobile-breakpoint 768
```

Then invoke **content-review-agent** (`review content at <path>`). A score **≥ 85** is required before deploy — it catches inflated/fabricated claims, dead links, contradictions, and PII that shouldn't be public (private emails, phone numbers).

### Phase 5 — Deploy publicly (GitHub Pages)

A profile page must be **publicly reachable**. The typical target is the person's `<user>.github.io` (or org `.io`) repository, served from `main`/`gh-pages` with no build step.

- If an `index.html` already exists at the repo root, **confirm with the user before overwriting it** — it may contain content, tracking scripts, or ad tags not covered by this run's fact-gathering.
- Preserve unrelated existing files (CNAME, robots.txt, sitemap.xml, ads/analytics scripts, `.nojekyll`) — don't remove them as part of a profile-content refresh.
- Commit to the branch GitHub Pages serves from, push, and verify the live URL returns **200 without authentication** (`curl -o /dev/null -w '%{http_code}'`).
- Keep asset links relative so they survive whatever base path the Pages site uses.

## Bundled resources

- **`references/profile-design.md`** — section spine, sidebar layout, timeline pattern, project-card grid, token sets, accessibility checklist.
- Structural checker is **shared with `brochure`** (`../brochure/scripts/check_brochure.py`) — no duplicate script.

## Anti-patterns

- Inventing job titles, dates, or project descriptions instead of asking.
- Listing a project whose Live or GitHub link is actually dead.
- Dumping every public repo into the projects section instead of curating Pages-enabled candidates with the user.
- Replacing an existing page's whole aesthetic without being asked, when only a content refresh was requested.
- Dropping existing analytics/ads/SEO files (CNAME, robots.txt, sitemap.xml) while refreshing content.
- Hiding the sidebar entirely on mobile instead of stacking it above the content.
