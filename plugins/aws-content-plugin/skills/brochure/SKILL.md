---
name: brochure
description: "Create a single-page, responsive online brochure (landing page) for an AWS solution, product, or platform as one self-contained HTML file — editorial design, hero + value + features + embedded architecture diagram + CTA, deployed publicly via GitHub Pages. Use whenever the user wants a brochure, landing page, marketing one-pager, product overview page, solution showcase, '온라인 브로셔', '브로셔 만들어', '랜딩 페이지', '소개 페이지', or wants to present a cloud product's value and architecture on the web — even if they don't say the word 'brochure'. Not for slide decks (use reactive-presentation) or multi-page docs sites (use gitbook)."
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Brochure

Build a **single-page, responsive marketing brochure** for an AWS solution as a **self-contained HTML page** (one HTML entry file with CSS inlined — no build step, no framework — plus its architecture SVG as an adjacent asset) — readable on mobile, tablet, and PC — that leads with the product's core message, shows its key features, embeds its architecture diagram, and ends with a call to action. Designed to be hosted **publicly** (GitHub Pages), because that's what a brochure is for.

> **Path variable**: `{skill-dir}` in this document = `{plugin-dir}/skills/brochure` in agent documents.

A brochure is **persuasion + clarity**, not a slide deck and not a docs site. It is one scroll: a decision-maker should grasp *what this is and why it matters* in 10 seconds, and an engineer should be able to drill into features and architecture without leaving the page. Keep that dual audience in mind throughout.

## When this applies (and when it doesn't)

- **Use this skill** for: a product/solution landing page, a one-page overview, a "make a brochure" / "랜딩 페이지" request, a public showcase of a cloud product's value + architecture.
- **Use `reactive-presentation`** instead for slide decks / talks / training.
- **Use `gitbook`** instead for multi-page documentation sites.
- A brochure may **embed** an architecture diagram — produce it with the **`architecture-diagram`** skill, then embed the exported SVG (see Phase 3).

## Workflow

```
brochure-agent → gather product facts → (architecture-diagram skill → SVG)
  → (Playwright screenshots, if a reachable web UI exists) → write self-contained HTML
  → self-check script → content-review-agent (≥85) → deploy to GitHub Pages (public)
```

### Phase 1 — Gather the product facts (don't invent them)

A brochure lives or dies on accurate, specific content. Before writing markup, pin down — from the user, the repo, or a README — the facts you'll turn into copy. If the source exists (a repo, CLAUDE.md, README), read it; **don't fabricate metrics, feature counts, or service names** — inflated or wrong numbers are the fastest way to lose a technical reader's trust.

Capture:
- **One core message** (the headline promise) + a one-sentence subcopy.
- **3–5 proof metrics** (real numbers: pages, tools, regions, controls, latency…). Verify each against the source.
- **3 value pillars** (the "why"), and **6–10 features** (the "what").
- **The architecture** (components + primary flow) — for the embedded diagram.
- **Audience + language** (default: the user's language; this plugin's users are often Korean — mirror the request's language).
- **Security/positioning posture** if relevant (e.g. read-only, least-privilege).

If key facts are missing and can't be derived, ask with `AskUserQuestion` — a brochure with placeholder copy is worthless.

### Phase 2 — Commit to a design direction

Generic, templated pages read as "AI slop" and undercut a premium product. Commit to **one** intentional aesthetic and execute it precisely. The reference direction this skill ships with is an **editorial "paper + ink + one accent"** system (warm, document-like, data-dense, calm) — but the point is *intentionality*, not this exact theme. Reuse the brand's real colors when known.

Read **`references/design-system.md`** before writing CSS — it has the token set, type-pairing rules, the responsive breakpoints, the mobile architecture-rotation technique, the accessibility checklist, and the CSS gotchas that bite every time. The golden reference brochure is in **`assets/example-brochure/`** — open it to see the target quality bar; adapt, don't copy verbatim.

### Phase 3 — Build the architecture diagram (if the brochure shows one)

Most solution brochures benefit from an architecture visual. Produce it with the **`architecture-diagram`** skill (it validates layout + uses official AWS icons), export to **SVG**, and place it beside the brochure HTML. You'll embed it as a responsive `<img>` in Phase 4. Keep the diagram and the brochure copy telling the **same story** — same component names, same counts — so they don't contradict each other.

### Phase 3.5 — Capture product screenshots (required when the product has a reachable web UI)

A brochure that only describes a UI in prose reads as unfinished when the product actually
has one to show. **Skip this phase only when the product has no reachable web UI** — either
it has none at all (a CLI tool, a library, an API-only service) or none you can reach and the
user can't provide captures. That one condition is the skip rule everywhere (agent rule 9
says the same); when you skip, say so explicitly.

1. **Availability gate first.** The `browser_*` capture tools come from the **Playwright
   MCP server**, which brochure-agent declares in its frontmatter (`mcpServers:
   [playwright]` — the plugin starts it via `npx @playwright/mcp`). They should normally be
   available, but the server can fail to start in offline environments or ones missing
   npx/browser dependencies. If the tools aren't available, don't stall: ask the user (with
   `AskUserQuestion`) to either fix the Playwright setup or hand you screenshot files
   directly, and proceed with what they provide.
2. **Capture.** With Playwright MCP: `browser_navigate` to the product, `browser_resize` to a
   consistent desktop viewport (e.g. 1600×900) so every capture is uniform, then
   `browser_take_screenshot` for 4–6 representative screens — one per core use case
   (overview/dashboard, the flagship feature, a couple of secondary views), not every screen.
   If you have neither the tools nor user-provided images and no URL to reach, ask with
   `AskUserQuestion` rather than guessing or skipping silently.
3. **Use a sanitized/demo account, and redact before publishing.** A screenshot of a *live*
   console can bake sensitive data into pixels — account IDs, ARNs, session/token URL
   params, internal hostnames/CIDRs, customer names/data — that the text-based PII scan
   **cannot** see. Prefer a demo/sandbox account with fake data; before the deck goes public,
   **eyeball every screenshot** and blur/crop/retake anything real. This is a manual gate:
   the checker and content-review-agent scan text, not image contents.
4. **Embed.** Save each capture next to the brochure HTML under `screenshots/`, referenced
   with a relative path, `loading="lazy"`, a descriptive `alt` (what the screen shows, not
   just a filename), and a `<figcaption>` naming the screen. Resize/optimize each to roughly
   ≤100KB (e.g. via PIL) — a brochure shouldn't ship megabytes of unoptimized PNGs.

### Phase 4 — Write the self-contained HTML

One `.html` file. Inline the CSS in a `<style>` block; you may load distinctive fonts from a CDN but **always provide a system-font fallback** so the page still reads if the CDN is blocked. No build step, no framework.

Use this section spine (scale to the product; omit what doesn't apply):

```
nav (sticky, minimal anchors + one CTA)
hero        — eyebrow · headline (the core message) · subcopy · proof-metric chips · primary CTA
value       — a short problem framing, then 3 value pillars
features    — 6–10 feature cards
shots       — 4–6 product screenshots in a grid, each with a caption (required if the
              product has a web UI — see Phase 3.5; omit the section entirely otherwise)
[spec]      — optional table (tiers, tools, gateways, pricing…)
architecture— embedded SVG diagram (responsive; see design-system.md for the mobile-vertical rotation)
trust       — security posture / tech stack
cta         — closing call to action (centered)
footer
```

While you're in the `<head>`, add basic social-share metadata (`og:title`, `og:description`;
`og:image` too if you have a hosted preview image) — cheap to include, and it's what makes
a shared brochure link preview well in Slack/Discord/etc.

**Responsive is the whole job — design mobile-first and verify all three tiers:**
- **Mobile (~375px)**: single column; tables become stacked cards (never just hide the meaningful column); a wide architecture SVG is **rotated 90° to fill the vertical screen** (technique in `references/design-system.md`).
- **Tablet (~768px)**: 2-column grids.
- **PC (~1280px)**: full multi-column layout.

**Accessibility and the CSS gotchas in `references/design-system.md` are not optional** — skip-link, `:focus-visible`, `prefers-reduced-motion` (including SVG SMIL), WCAG-AA contrast, `aria-hidden` on decorative SVG, and the utility-class margin trap that silently breaks centering. They're cheap to add up front and expensive to retrofit.

### Phase 5 — Self-check, then quality-gate

Run the bundled checker, fix what it flags, then pass the mandatory content review:

```bash
python3 {skill-dir}/scripts/check_brochure.py <brochure.html>
```

It verifies tag balance, that the responsive/accessibility primitives are present (focus-visible, skip-link, reduced-motion, viewport meta, breakpoints), that every `<img>` has non-empty alt text, that referenced local assets (screenshots, the SVG) exist, and flags low-contrast muted-text tokens on a light background. It's a fast structural gate, not a substitute for looking at the page.

Then invoke **content-review-agent** (`review content at <path>`). A PASS on the applicable scale is required before deploy — normally **≥ 85/100**; if the reviewer can't run Playwright visual tests, it converts to the 90-point scale (PASS ≥ 77 — see the reviewer's Verdict table). It catches hallucinated services, inflated counts, contradictions between copy and diagram, PII (account IDs, internal CIDRs/IPs — strip them from a public brochure), and readability/accessibility issues.

### Phase 6 — Deploy publicly (GitHub Pages)

A brochure must be **publicly reachable** — that's its purpose. This is where teams get surprised: **if the product's own domain sits behind authentication** (e.g. a CloudFront + Cognito Lambda@Edge edge that gates *every* path), it can't host a public brochure there — every visitor hits a login wall — *unless* you carve out a public exception (an unauthenticated path/behavior in the edge function, or a separate public subdomain/bucket). Check the target's auth posture first; if there's no clean public bypass, use GitHub Pages.

The reliable public host is **GitHub Pages**:
- Drop the brochure into the repo's Pages source (commonly a Docusaurus `static/brochure/` or a `gh-pages` branch) so it ships as a static file at `/<base>/brochure/`.
- Commit to the branch the Pages workflow watches (often `main`) and let CI publish.
- Verify the live URL returns **200 without authentication** (`curl -o /dev/null -w '%{http_code}'`), and that the embedded SVG and any download links also resolve.

Relative asset links (`./awsops-arch.svg`) survive any base path; absolute `/` links break under a project-pages base — keep links relative.

## Bundled resources

- **`references/design-system.md`** — design tokens, type pairings, responsive breakpoints, the mobile architecture-rotation CSS, the accessibility checklist, and the CSS gotchas. **Read before writing CSS.**
- **`assets/example-brochure/`** — a complete golden-reference brochure (HTML + a `screenshots/` grid + architecture SVG) to calibrate quality. Adapt; don't ship verbatim.
- **`scripts/check_brochure.py`** — structural + responsive + accessibility self-check (Phase 5).

## Anti-patterns (these make a brochure feel cheap)

- Generic templated hero + purple-gradient-on-white — commit to an intentional aesthetic instead.
- Inflated or unverified numbers — a wrong tool count loses the engineer immediately.
- A wide architecture diagram left tiny and unreadable on mobile — rotate it.
- Hiding the meaningful table column on mobile instead of restacking it.
- Describing a real product UI in prose only, with no screenshots — if it exists and is reachable, show it.
- Baking volatile facts (version labels, dated counts) into hero copy — they age badly; keep them in a footer or omit.
- Deploying behind an auth edge and wondering why no one can see it.
