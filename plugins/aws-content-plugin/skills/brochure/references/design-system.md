# Brochure Design System

The reference aesthetic is an **editorial "paper + ink + one accent"** system: warm, document-like, data-dense, calm. It exists to give you a known-good starting point that avoids generic AI-template looks. Reuse the brand's real colors when you know them; otherwise this palette is a safe, premium default. The non-negotiable part isn't *this* theme — it's that you commit to **one** intentional direction and execute every detail (type, spacing, contrast, motion) precisely.

## 1. Tokens (CSS custom properties)

Define these on `:root` and reference them everywhere — a single token set is what keeps a page coherent.

```css
:root{
  /* accent — one brand color, used functionally (active / lead-series / CTA) */
  --accent:#D97757; --accent-hover:#B75E40; --accent-ink:#8E4830; --accent-50:#FBF1EC; --accent-100:#F5DCCF; --accent-200:#EEBFAA;
  /* ink — warm neutral ramp */
  --ink-100:#EDEBE4; --ink-200:#D7D3C7; --ink-400:#8A8474; --ink-500:#5F5A4D; --ink-800:#1F1E1D; --ink-900:#14130F;
  /* paper surfaces */
  --paper:#FAF9F5; --paper-muted:#F3F1EB; --white:#FFFFFF;
  /* semantic (use sparingly) */
  --positive:#10B981; --negative:#F43F5E;

  --bg:var(--paper); --surface:var(--white); --sunken:var(--paper-muted);
  --text:var(--ink-800); --text-2:var(--ink-500);
  --text-3:#6B665A;   /* muted text — NOT ink-400; see contrast note §6 */
  --line:var(--ink-100); --line-2:var(--ink-200);

  --shadow-card:0 1px 2px rgba(31,30,29,.04), 0 8px 28px rgba(31,30,29,.06);
  --maxw:1180px;
}
```

Functional color: accent = brand/active/CTA, positive = healthy/up, negative = risk/down. Plain ink carries everything else. Resist scattering color — dominant neutrals with one sharp accent read as premium; an evenly rainbow palette reads as a template.

## 2. Typography — pair, don't default

Avoid Inter/Roboto/Arial/system-only — they signal "AI default". Pick a **distinctive display face** + a **refined body face** + a **mono** for data/labels. A proven editorial trio:

- **Display** (eyebrows, brand, numerals): a characterful serif — e.g. **Fraunces** (optical, warm).
- **Body** (headings + prose, incl. Korean): **Pretendard** (covers Korean beautifully; weights to 900). For KR headlines use Pretendard 800; Fraunces is Latin-only, so reserve it for English/numeric accents.
- **Mono** (metrics, table labels, code): **JetBrains Mono**.

Load via CDN (`fonts.googleapis.com` for Fraunces/JetBrains; jsDelivr for Pretendard) but **always** declare a system fallback in the stack so the page survives a blocked CDN:

```css
--serif:"Fraunces",Georgia,serif;
--sans:"Pretendard Variable",Pretendard,-apple-system,system-ui,sans-serif;
--mono:"JetBrains Mono",ui-monospace,monospace;
```

Use **tabular numerals** wherever numbers line up: `font-variant-numeric:tabular-nums lining-nums`. Headline sizing with `clamp()` so it scales across tiers: `font-size:clamp(34px,5.4vw,60px)`.

**Line length vs. full-width text.** Cap measure (`max-width:NNch`) only on text in a *narrow* column — centered CTA copy, or a hero column that sits beside a figure — at ~50–65ch. **Never cap a block that spans the full content column** (section subheads, standalone lead paragraphs): a 62ch cap on a ~1072px column strips the text to ~half width and forces needless line breaks. Let those blocks use the full width (`max-width:none`). Add `text-wrap:pretty` to body/lead paragraphs (removes orphan words) and `text-wrap:balance` to headings (even multi-line splits). This is the most common reason a generated brochure looks half-empty on desktop.

## 3. Layout & responsive (mobile-first, 3 tiers)

Centered content column; section spine stacks vertically. Breakpoints:

| Tier | Width | Grid behavior |
|------|-------|---------------|
| Mobile | ≤ 640px | 1 column; tables → stacked cards; arch SVG rotated (see §5) |
| Tablet | 641–1024px | 2-column grids |
| PC | ≥ 1025px | full multi-column (3–4 col card grids) |

```css
.wrap{max-width:var(--maxw); margin:0 auto; padding:0 24px}
@media (max-width:1024px){ .grid-3{grid-template-columns:repeat(2,1fr)} }
@media (max-width:640px){ .grid-3{grid-template-columns:1fr} .wrap{padding:0 18px} }
```

**Responsive tables** — never just `display:none` the meaningful column on mobile (that strips the table's value). Restack each row as a card:

```css
@media (max-width:640px){
  table thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  table, table tbody, table tr{display:block;width:100%}
  table tr{border-bottom:1px solid var(--line);padding:14px 16px;position:relative}
  table td{display:block;border:0;padding:0}
  table td.name{padding-right:48px}              /* room for the count */
  table td.count{position:absolute;top:14px;right:16px}
}
```

## 4. Screenshot grid (`#shots`)

When the product has a web UI (Phase 3.5 of SKILL.md), lay the captures out as a card grid —
3 columns on PC, 2 on tablet, 1 on mobile; the first shot can span 2 columns (`.wide`) to lead
with the flagship screen. See the golden example's `#shots` section for a working copy.

```css
.shots{display:grid; grid-template-columns:repeat(3,1fr); gap:18px}
.shot.wide{grid-column:span 2}
@media (max-width:1024px){ .shots{grid-template-columns:repeat(2,1fr)} .shot.wide{grid-column:span 2} }
@media (max-width:640px){ .shots{grid-template-columns:1fr} .shot.wide{grid-column:span 1} }
.shot img{display:block;width:100%;border-radius:12px;border:1px solid var(--line)}
.shot figcaption{margin-top:8px;font-size:13px;color:var(--text-2)}
```

Each `<figure class="shot">` wraps one `<img loading="lazy" alt="...">` + a `<figcaption>`
naming the screen. `alt` describes what's shown (not the filename) — `check_brochure.py`
hard-fails on any `<img>` missing non-empty alt text.

## 5. Embedding the architecture diagram (the mobile-vertical trick)

Embed the exported SVG as a responsive `<img>`. On wide screens it fits the column; on mobile a landscape diagram becomes unreadably small — **rotate it 90° to fill the vertical screen**. A single exported SVG can't reflow, so rotation is the right call.

```html
<figure class="arch-figure"><img src="awsops-arch.svg" loading="lazy" alt="…architecture…"></figure>
<p class="arch-rot-hint">On mobile the diagram is rotated to vertical.</p>
```
```css
.arch-figure{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow-card);padding:14px;overflow:hidden}
.arch-figure img{display:block;width:100%;height:auto}
.arch-rot-hint{display:none}
@media (max-width:640px){
  /* SVG natural size W×H — set the container's aspect-ratio to H/W (portrait) */
  .arch-figure{position:relative;padding:0;aspect-ratio: <H> / <W>}
  .arch-figure img{position:absolute;top:50%;left:50%;max-width:none;
    width:calc((100vw - 36px) * <W> / <H>);   /* 36px = 2× the mobile .wrap padding */
    height:auto;transform:translate(-50%,-50%) rotate(90deg)}
  .arch-rot-hint{display:block;font-size:12.5px;color:var(--text-3);text-align:center;margin-top:12px}
}
```
Replace `<W>`/`<H>` with the SVG's `width`/`height` (read them from the SVG's `viewBox`/`width` attrs). The math makes the rotated landscape exactly fill the mobile content width.

## 6. Accessibility (cheap up front, expensive to retrofit)

- **Skip link** to main content: a visually-hidden `<a class="skip-link" href="#main">` that appears on `:focus`.
- **Focus-visible** on every interactive element — paper backgrounds make default focus rings faint:
  `:focus-visible{outline:2px solid var(--accent);outline-offset:3px}`
- **Reduced motion** — and remember **CSS can't stop SVG SMIL `<animate>`**; remove them with JS under the media query:
  ```js
  if (matchMedia('(prefers-reduced-motion: reduce)').matches)
    document.querySelectorAll('svg animate, svg animateTransform').forEach(a=>a.remove());
  ```
  Also gate CSS animations/transitions in `@media (prefers-reduced-motion:reduce)`.
- **Contrast (WCAG AA)** — `ink-400` (`#8A8474`) on paper is ~3.2:1 and **fails** for body text. Use `--text-3:#6B665A` (~4.6:1) for muted text, or bump size/weight. Never light-gray (`#999`,`#b0b0b0`) on paper.
- **Decorative SVG** gets `aria-hidden="true" focusable="false"`; meaningful diagrams get a real `alt`/`aria-label`. Tables get a `<caption>` (can be `.sr-only`).
- Tap targets ≥ 40px; on mobile let primary buttons go full-width.

## 7. CSS gotchas that bite every time

- **Utility-class margin trap (silent de-centering).** If a section carries two classes — a centering utility (`.wrap{margin:0 auto}`) and a spacing class (`.cta{margin:40px 0 0}`) — and the spacing class is declared *later*, its `margin` shorthand resets left/right to `0` and the block jams to the left. Fix: use `margin:40px auto 0` (keep `auto`), or set only `margin-top`. Equal-specificity selectors → source order wins.
- **`text-align:center` doesn't center fixed-width children** — give centered headings/paragraphs `margin:0 auto` (and a `max-width` for nice line length).
- **`box-sizing:border-box` globally** (`*{box-sizing:border-box}`) or padded full-width elements overflow.
- **Scroll-reveal that starts at `opacity:0`** will leave content invisible if the IntersectionObserver/JS doesn't run — ensure a no-JS/`prefers-reduced-motion` fallback sets it visible.

## 8. Content integrity

- Verify every metric against the source; an inflated count is the fastest way to lose a technical reader.
- Keep the brochure copy and the embedded diagram telling the **same** story (same names/counts) — contradictions read as carelessness.
- Strip PII from anything public: account IDs, internal CIDRs/IPs, private hostnames.
- Don't bake volatile facts (version labels, "as of" counts) into hero copy — they age; footer or omit.
