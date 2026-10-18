# Reactive-presentation: navigation, detail layer, preview fidelity, AI-tone gates

Date: 2026-10-18
Scope: `plugins/aws-content-plugin/skills/reactive-presentation` (framework assets,
`remarp_to_slides.py`, `measure_deck.py`, references, `reactive-presentation-agent`).

## Intent

Long, multi-block expert sessions (e.g. the 80-slide `eks-hybrid-nodes` deck,
`https://presentation.atomai.click/eks-hybrid-nodes/index.html`) need three things
the framework lacks today:

1. **Fast navigation during a live talk.** The presenter wants to jump to another
   session (block) or to a topic ("vxlan") without paging through slides, e.g. when
   time is short and a section must be skipped.
2. **Detail without clutter.** Tables and cards must stay terse. Explanations such as
   *why UDP 8472 must be open and when it is used* (slide 26, "Pod CIDR route는 불필요
   (node IP, UDP 8472은 필요)") belong in a layer the audience/presenter reaches on
   demand, not in the cell.
3. **Trustworthy presenter view and less "AI-written" feel.** The presenter view's
   current/next previews render differently from the real slide, and some copy still
   reads machine-written.

Success: the presenter can reach any block or keyword in two actions; dense slides
keep one-line cells while detail is one hover/click away; presenter previews match
the deck pixel-for-pixel in layout; validation catches the copy tells listed below.

## Goals

**Primary surface is the deck window** (user decision). HTML decks are often presented
from a single browser window with no presenter view; a presenter view means a second
browser window. All new navigation and detail UI (G1-G3) lives in the deck window.
Jumps go through the existing `goTo` → `showSlide` path, which already broadcasts the
slide change to an open presenter view (`slide-framework.js:631-634`), so the
presenter view follows without new message types. The presenter window does not get
its own agenda/search/sidebar in this change.

### G1. Hover agenda (top-right)
- A small hot zone in the top-right corner of the viewport. Hovering it opens an
  agenda panel; leaving it (with a short grace delay) closes it.
- Panel content: list of sessions (blocks) in deck order; each block expands to its
  slide titles with slide numbers. The current block/slide is highlighted.
- Clicking a block jumps to its first slide; clicking a slide title jumps to it.
- Works in the merged `index.html` and in a single-block HTML (then it lists that
  block's slides only).
- Hidden in presenter previews, PDF/PPTX export, `measure_deck` runs and overview mode.

### G2. ⌘K / Ctrl+K search (VitePress-style)
- `Cmd+K` (macOS) / `Ctrl+K` (others), and `/`, open a centered modal search box.
  `Esc` closes. Arrow keys move, `Enter` jumps.
- Index: slide titles, subtitles, visible body text (incl. table cells, card text,
  tab panels, fragments regardless of reveal state) and detail-layer text (G3).
  Speaker notes are **excluded** by default (builder's call: presenter-only content
  should not leak on a shared screen). Code blocks are included.
- Indexes every slide in the deck; excludes framework clones (left thumbnail sidebar,
  overview copies, presenter clones) so hits are not duplicated (builder's call).
- Matching: case-insensitive substring, Korean-safe (no word tokenizer needed);
  results ranked title hit > body hit > detail hit, then by slide order.
- Each result shows block name, slide number, slide title and a highlighted snippet.
- Jumping to a slide whose match sits inside a hidden tab or unrevealed fragment
  lands on the slide; revealing the exact element is a nice-to-have, not required.
- Must not steal keys while focus is in an input/textarea/contenteditable (quizzes).
- Built index is computed client-side from the DOM at load; no build-time JSON
  required.

### G3. Detail layer (tooltip + right sidebar)
Interaction (decided by the user):
- **Hover** on a marked term shows a **tooltip** with a short explanation.
- **Click** opens the **right sidebar** with the long explanation.
- A small **icon** (e.g. an "i"/expand glyph) appears next to the term **only when
  sidebar content exists**; the icon is the click target that signals "more here".
  Terms with only a tooltip get the dotted-underline affordance and no icon.
- For a term with sidebar content, clicking either the term text or its icon opens the
  sidebar. Clicking a tip-only term does nothing (builder's call); on touch devices a
  tap toggles its tooltip.
- Sidebar: slides in from the right, overlays (does not reflow) the deck, closes on
  `Esc`, on clicking outside, on its close button, and on slide change. One open at
  a time.
- Keyboard: the marked terms are focusable; `Enter` on a focused term opens the
  sidebar. Tooltips also show on focus.
- Arrow/space navigation keys must not be swallowed while the sidebar is open,
  except `Esc`.

Authoring (Remarp):
- Inline form for a short tooltip: `[UDP 8472]{tip="Cilium VXLAN 포트"}`.
- Block form for long content, referenced by id:
  ```
  [UDP 8472]{detail=vxlan-8472}

  :::detail vxlan-8472 "UDP 8472가 필요한 이유"
  tip: hybrid 노드 간 Cilium VXLAN 터널 포트
  (Markdown body: paragraphs, lists, code, tables allowed)
  :::
  ```
  A `:::detail` with a `tip:` line gives both tooltip and sidebar; without `tip:` the
  tooltip shows the detail title.
- Works inside table cells, cards and `:::html` blocks. Inside `:::html`, authors use
  the emitted HTML form directly: `<span class="rp-detail" data-tip="..."
  data-detail="vxlan-8472">UDP 8472</span>`; the `:::detail` block can live in the
  same slide.
- `:::detail` ids are slide-scoped; duplicate id or a reference to a missing id is a
  `validate` CRITICAL (`DETAIL_REF`).
- Export: PPTX/PDF screenshots never show tooltips/sidebar. `export_pptx.py` appends
  each slide's detail entries (title + text) to that slide's speaker notes under a
  `[디테일]` / `[Details]` heading so the content is not lost.

### G4. Presenter view preview fidelity (bug fix)
Root causes found in `assets/presenter-view.js`:
1. Previews lay slides out on a hard-coded **960×540** box (`.slide-scaler`,
   `_applyScale`) while the deck is a **1920×1080** design canvas (width from
   `--slide-ratio-w/h`, `theme.css` `.slide-deck`).
2. `html { font-size: 16px !important }` overrides the deck's fixed root font
   (`theme.css` `html { font-size: 24px }`); rem-based type no longer matches box size.
3. `body { font-family: ... !important }` for the presenter chrome inherits into the
   previews and replaces the deck font.
4. `_renderSlidePreview` sets `clone.className = 'slide active'`, dropping per-slide
   classes (`theme-dark`, layout classes); the deck's own classes, `data-fit`, theme
   preset and `lang` are not reproduced on the preview's `.slide-deck`.
Fix: render previews on the deck's real canvas size (read from the live
`.slide-deck`), preserve slide and deck classes/attributes and `lang`, scope the
presenter-chrome overrides so they never reach the preview subtree, and scale only by
transform. Previews show the fully revealed state of fragments for "next" and the
current reveal state for "current" (current behaviour for "current" is kept if it
already mirrors the main window). Canvas elements may render blank in clones; that
is out of scope unless trivial.

Also fix: the slide logo overlaps the bottom-left nav hint ("Spa[aws]ce" in the live
deck at 1600×900).

Regression check: a `measure_deck`-side (or dedicated test) comparison that the
preview clone of slide N has the same text-line layout as the real slide (e.g. same
bounding-box proportions of `.slide-body` children within tolerance).

### G5. AI-tone and copy-layout gates
- Remove the left colour bar from `.callout` (`theme.css:756`, `border-left: 4px
  solid`) and `.pain-quote` (`theme.css:1038`). Role is conveyed by a soft background
  tint and title colour only. Also check other primitives for similar accent bars.
- New `validate` lint `EM_DASH` at WARNING severity, so existing decks keep building
  (0 CRITICAL contract, `remarp_to_slides.py:1838`); the agent's authoring rejection
  loop and the agent prompt treat it as must-fix (builder's call). Scans em dash
  U+2014, middle dots U+00B7/U+30FB and their HTML entities in authored text,
  including speaker notes and `:::detail` bodies; excludes code spans/blocks, URLs and
  identifier-like attribute values. Today
  this rule is review-gate only (`references/authoring-rules.md` §2).
- New `validate` lint `AI_TONE` (WARN, does not block build):
  - more than 3 "→" in one slide's visible text;
  - formulaic labels repeated across the deck ("한 줄 정리", "핵심 정리", "핵심:",
    "Key takeaway") more than twice;
  - note clichés ("꼭 기억해 두세요", "중요한 포인트는", "결론적으로").
  Patterns live in one list in the script so they can be tuned.
- New `measure_deck` check `SENTENCE_RUNON` (WARN): a single text block containing
  two or more sentences where, after rendering, a sentence boundary falls mid-line
  and the block wraps to 3+ lines. Example: slide 8 card "API endpoint는 하나만 권장":
  "Public-only 또는 Private-only 권장. \"Public and Private\"는 ..." wraps as
  "Private-only / 권장." Fix guidance: one claim line + one reason line (separate
  elements or `<br>`), or move the reason to the detail layer.
- Update `authoring-rules.md` §2 table and the agent prompt: card description =
  one claim line + optional one reason line; reasons/elaboration go to `:::detail`.

## Non-goals
- Agenda, search or detail sidebar inside the presenter window; mirroring a detail
  sidebar between windows.
- Full-text search across multiple decks, fuzzy/typo-tolerant search, search in notes.
- Editing content from the sidebar; persisting sidebar state.
- Rewriting the existing `eks-hybrid-nodes` deck in this change (builder's call; the
  user did not answer whether to include it). The deck is in a separate repo; it can
  be updated afterwards using the new gates.
- Making canvas animations render inside presenter previews.

## Anti-goals (would be a failure even if it "works")
- Hover zone or icons visible in exported PPTX/PDF screenshots or in measure_deck
  geometry (false OVERLAP/OVERFLOW findings).
- Tooltip/sidebar shifting slide layout or triggering ReactiveFit re-fit.
- Search or agenda hijacking arrow/space keys during normal presenting.
- Detail icons on every term (icon appears only when sidebar content exists).
- Re-introducing decorative chrome (gradients, glow, colour bars) in the new UI.

## Constraints
- Vanilla JS/CSS in existing assets (`slide-framework.js`, `theme.css`,
  `presenter-view.js`); no new runtime dependency or CDN.
- Theme tokens only (`var(--surface-*)`, `--accent`, etc.); light and dark themes.
  Follow `references/framework-contract.md` and `design-tokens.css`.
- The new UI lives outside `.slide` elements (attached to body/deck chrome) so
  thumbnails, presenter clones and measure_deck ignore it; measure_deck's prepare
  step hides it explicitly.
- Generated Codex/Claude packages must be regenerated (`scripts/sync-codex-plugins.py`)
  — never hand-edit `packages/*`.
- Docs: update `REMARP.md`, `references/remarp-format-guide.md`,
  `references/keyboard-shortcuts.md`, `references/authoring-rules.md`, the agent
  prompt, and the public `doc-sites/` page(s) for reactive-presentation in both EN
  and KO if such pages document syntax/shortcuts. CHANGELOG entry.
- Tests: `bash tests/run-all.sh` plus the validation commands in the root
  `CLAUDE.md` pass; new lint rules and the `:::detail` parser get unit tests in the
  existing reactive-presentation test suite.

## Builder's discretion
- Exact hot-zone size, delays, animation, icon glyph and sidebar width.
- Block naming source in the merged deck (block frontmatter `title`, else first
  `# ` heading, else file stem) and how block boundaries are marked
  (e.g. `data-block`/`data-block-title` on each slide in `_build_merged_index`).
- Tooltip auto-placement logic; search result count cap.
- Whether `AI_TONE` thresholds are configurable via frontmatter.
