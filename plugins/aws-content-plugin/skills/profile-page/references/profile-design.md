# Profile Page Design System

A personal profile page reads best as a **calm, content-first two-column layout**: a fixed identity sidebar next to a scrolling content column. The example below is a proven, anonymized spine — adapt tokens/fonts to match the person's existing site if one exists, but keep the structural pattern (it's the part that makes the page scannable).

## 1. Section spine

```
header    — sticky top bar: name (left) + quick links (right, GitHub/LinkedIn/etc.)
main      — two-column grid: sidebar (~280px) | content (flexible)
  sidebar   — card: avatar, name, title, org, location, stacked link list
  content
    about       — 1-2 short paragraphs
    experience  — reverse-chronological timeline (dot + connecting line)
    skills      — category groups of tag chips
    featured    — talks / posts as small cards (optional — omit if none)
    projects    — grouped project cards, each with GitHub + Live links (+ optional Demo)
footer    — copyright + link recap
```

## 2. Tokens (dark, the common default for a dev portfolio)

```css
:root {
  --bg: #0d1117;
  --card: #161b22;
  --text: #e6edf3;
  --text-secondary: #8b949e;
  --accent: #FF9900;       /* pick the person's real brand/accent color */
  --border: #30363d;
  --tag-bg: #1f2937;
}
```

A light variant just inverts the ramp — keep the same structural CSS, swap the custom properties:

```css
:root[data-theme="light"] {
  --bg: #ffffff;
  --card: #f6f8fa;
  --text: #1f2328;
  --text-secondary: #57606a;
  --accent: #FF9900;
  --border: #d0d7de;
  --tag-bg: #eaeef2;
}
```

## 3. Layout & responsive

```css
.main {
  display: grid;
  grid-template-columns: 280px 1fr;
  max-width: 1100px;
  margin: 0 auto;
  gap: 3rem;
  padding: 2.5rem 2rem;
}
.sidebar { position: sticky; top: 80px; align-self: start; }

@media (max-width: 768px) {
  .main { grid-template-columns: 1fr; padding: 1.5rem 1rem; gap: 2rem; }
  .sidebar { position: static; }   /* stack above content, never hide it */
}
```

Single breakpoint at 768px is enough for this layout — the sidebar card and content column both already read fine as single-column blocks; there's no dense table to restack (unlike a brochure's spec table).

## 4. Experience timeline

A vertical line with a dot per entry; the most recent entry's dot is filled with the accent color, the rest are neutral:

```css
.timeline { position: relative; padding-left: 1.5rem; }
.timeline::before {
  content: ''; position: absolute; left: 0; top: 0.5rem; bottom: 0.5rem;
  width: 2px; background: var(--border);
}
.timeline-item { position: relative; margin-bottom: 1.75rem; padding-left: 1.25rem; }
.timeline-item::before {
  content: ''; position: absolute; left: -1.5rem; top: 0.55rem;
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--border); border: 2px solid var(--bg);
}
.timeline-item:first-child::before { background: var(--accent); }
```

Each entry: period (small, muted) → role + company (bold, accent on company name) → one-line description (muted).

## 5. Project cards

Group related projects under a category label; each card gets a label (type: Docs/Ops/Framework/…), title, one-line description, and **up to three links — GitHub + Live (Pages) + optional Demo** (a separate demo site, only when the user says one exists) — never ship a project card with a dead or missing link:

```css
.featured-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; }
.featured-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; }
.project-links { margin-top: 0.75rem; display: flex; gap: 1rem; font-size: 0.8rem; font-weight: 600; }
```

## 6. Accessibility

- `alt` text on the avatar image (the person's name is sufficient).
- `:focus-visible` on every link — a dark card background makes the default ring easy to miss:
  `:focus-visible{outline:2px solid var(--accent);outline-offset:2px}`
- If any hover/transition motion is used, gate it: `@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }`
- Viewport meta (`width=device-width, initial-scale=1.0`) is required for the mobile stack to apply.
- Don't rely on color alone to distinguish the "current" timeline entry — the accent-filled dot is a bonus, not the only signal (the entry's period text already communicates recency).

## 7. Content integrity

- Every experience entry, skill, and project must be real and current — a stale "current role" or a dead project link is the fastest way to undercut a portfolio's credibility.
- Verify Live and GitHub links actually resolve before shipping.
- Keep private contact info (personal phone, private email) off a public page; a public GitHub/LinkedIn link is the expected contact path.
