# Remarp Design Studio: compiler-backed preview and source-safe editing

Date: 2026-10-21\
Status: Proposal; no editor implementation or browser prototype shipped by this spec.\
Inspected baseline: `2036419c`.\
Scope: the existing `tools/remarp-vscode/` extension and the canonical Remarp compiler.

## 1. Recommendation and boundaries

Build a design workspace for Remarp, not another Markdown preview and not an
HTML-first slide editor. The desired experience is: select something on a real
slide, change its content or supported properties, ask AI for a scoped revision,
compare the proposal, and apply it to the original Remarp. Generated HTML remains
an output, never the independent editable source.

Use the existing VS Code extension first. Keep the editor protocol and web UI
independent of VS Code so a browser host can follow without replacing the compiler.
The user has not yet selected a host surface; VS Code-first is a provisional
recommendation, not a confirmed preference. “Like Claude Design” describes the
requested canvas/inspector/AI iteration experience here, not a verified claim about
that product's implementation or complete feature parity.

[ADR-024](../../decisions/ADR-024-remarp-source-contract.md) currently accepts
source-first authoring, saved-source compiled preview, and **unsupported visual
writeback**. This proposal preserves the first principle but proposes changing the
last two boundaries. An accepted follow-up decision is required before releasing
unsaved-source preview or visual writeback as supported features. Do not add a
general-purpose layout domain-specific language (DSL) or silently convert Markdown
into absolute-positioned HTML.

### Goals

- Preview normal decks through the same compiler, theme, and runtime as exports.
- Edit supported elements without losing notes, comments, fragments, or formatting.
- Make text-editor changes and visual changes converge on the same source.
- Preserve slide selection, zoom, and interaction state across successful rebuilds.
- Give AI proposals a visible scope, source diff, and Apply/Reject boundary.

### Not in the first release

Arbitrary HTML/JavaScript visual editing; browser collaboration; editable native
PowerPoint; automatic deployment; new Remarp grammar; or a clone of another
product. Existing PDF and screenshot-based PPTX exports remain distinct from
source editing and native editable PPTX.

## 2. What exists and what is missing

These are checkout observations, not findings inferred only from a diff.

| Area | Current behavior | Consequence for the design |
|---|---|---|
| [Text preview](../../../tools/remarp-vscode/src/preview.ts) | Separate TypeScript Markdown renderer; text updates and issue messages | Useful fallback, not the fidelity authority |
| [Compiled preview](../../../tools/remarp-vscode/src/extension.ts) | `remarp.previewCompiled` saves project sources, builds, and loads fresh HTML into a new panel | Accurate renderer path exists; persistent live-preview coordination does not |
| [Compiled renderer](../../../tools/remarp-vscode/src/compiledPreview.ts) | Adds webview resource policy and base URL to compiler HTML | Retain asset resolution; do not attach a broad write bridge to authored scripts |
| [Visual controller](../../../tools/remarp-vscode/src/visualEditor.ts) | Move/resize/property helpers exist but activation does not instantiate this controller | Wiring it alone would not establish safe round trips |
| [CSS editor](../../../tools/remarp-vscode/src/cssEditor.ts) | Reconstructs an entire `:::css` block; identifies targets by slide index | Formatting/comments can be lost; index shifts can target the wrong slide |
| [Canvas editor](../../../tools/remarp-vscode/src/canvasEditor.ts) | Regex-based geometry edits with its own slide/block scanning | Needs canonical boundaries, scoped identities, and one transaction per gesture |
| [Prompt bar](../../../tools/remarp-vscode/media/prompt-bar.js) | Writes issue annotations | This is a `/slide-fix` handoff, not an already integrated AI designer |
| [Compiler](../../../plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py) | `Slide` has `raw_source`/`source_index`; `ParsedBlock` has nested structure but no element source spans | Add source provenance before general element writeback |

### Reproduced identity defect

A parsed cards slide with a `<card:0>` CSS target generates the selector
`[data-remarp-id="s0-card:0"]`, while its actual card DOM identifier is
`s0-card-0`. The selector does not match that card. The dormant CSS editor also
produces colon-form targets. A compiler-level target resolver and regression test
must precede inspector CSS writeback; merely loading `edit-mode.js` cannot fix this.

Other identity limits: `data-remarp-id` is positional, and a merged project's
`remarp-source` metadata is `index`, not a per-element owning Markdown file. The
editor must not infer ownership from that metadata or split a merged deck by index.

### Remarp is a structured document with renderable islands

The [format guide](../../../plugins/aws-content-plugin/skills/reactive-presentation/references/remarp-format-guide.md)
and compiler define several layers:

| Layer | Authoring meaning | Suitable editor |
|---|---|---|
| Global YAML / `_presentation.md` | Theme, ratio, speaker, ordered project blocks | Deck settings and project navigation |
| `---` and `@...` directives | Slide boundary, type, layout, fit, background, timing | Slide settings and structural operations |
| Markdown and nested `:::...` blocks | Text, cards, columns, tabs, notes, fragments | Typed content/structure editing |
| `:::canvas` DSL | Explicit node IDs, coordinates, sizes, connectors, steps | Diagram-style geometry editor |
| `:::css` | Authored overrides | Allowlisted properties with inheritance/reset |
| HTML/script, Mermaid, Archify and other embedded content | Specialized renderable islands | Source editing or dedicated adapters, not generic drag-to-CSS |

The compiler has 16 slide types: cover, title, content, compare, tabs, canvas,
quiz, code, checklist, steps, timeline, slider, cards, thankyou, agenda, iframe.
Supporting Preview for these types does not imply supporting every visual edit.
Code fences can contain `---` and apparent directives; nested blocks use colon
counts. A source scanner must respect both instead of splitting on every separator.

## 3. Workspace experience

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Remarp Studio   Design | Play   Theme   Zoom   Diagnostics   Export   │
├───────────────┬───────────────────────────────────┬──────────────────┤
│ Blocks/slides │                                   │ Selection        │
│ Thumbnails    │  Compiler-rendered slide          │ Content          │
│               │  Selection/geometry overlay       │ Layout / style   │
│ Layers        │                                   │ Reveal step      │
│ Source owner  │                                   │ Reset / source   │
├───────────────┴───────────────────────────────────┴──────────────────┤
│ AI: selection / slide / block / deck     Proposal → Diff → Apply     │
│ History / issues / speaker notes / source editor                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Main interactions

1. Open a Remarp file or project. Select a slide thumbnail; the owning file and
   current preview revision are visible.
2. Click a heading/card, or choose it in the layers tree. Inspect its semantic
   content and supported properties; “Reveal in source” selects its source range.
3. Edit text through a source-backed input. Start with plain text and selected
   Markdown fields, not arbitrary `contenteditable` HTML serialization. Complex
   rich text opens the selected Markdown span rather than destroying inline syntax.
4. For normal slides, change supported layout/directives and spacing; keep flow
   layout. For Canvas nodes, drag/resize or enter coordinates. Unsupported actions
   explain the limitation and offer source editing.
5. Ask, for example, “Shorten these two cards and equalize their spacing.” Show
   selected scope, proposed source changes, and a candidate preview. Apply once or
   reject without modifying the document.
6. Switch to Play for actual navigation, tabs, quiz, fragments, and Canvas steps.
   Design selection must not consume Play interactions.

The inspector distinguishes inherited theme values, slide settings, authored
element overrides, and computed render values. Reset removes the local override;
it does not hard-code the current theme's value. Hide unsupported properties rather
than suggesting that every DOM element can safely move or resize.

Provide keyboard selection through the layers tree, labeled inputs, visible focus,
numeric geometry alternatives, Undo/Redo, Escape-to-cancel, and input method editor
(IME)-safe text commit. UI theme and slide theme are independent; slides retain `.theme-dark` and
`.theme-light`. Thumbnails use the real renderer at reduced scale; virtualize them
instead of rendering a second approximate slide implementation.

## 4. Architecture: one renderer, one source authority

```text
VS Code documents + project files + asset manifest
                 │ revisioned snapshot
                 ▼
Canonical Python parser/compiler
  ├── semantic editor IR + lossless source spans
  ├── element/source map + supported capabilities
  └── HTML + existing theme/runtime + diagnostics
                 │ build generation
                 ▼
Studio webview shell ───── isolated slide renderer
  layers / inspector          rendered pixels / runtime state
  selection / AI diff         bounded geometry observations
                 │ typed user edit intent
                 ▼
Host transaction service → source patch → WorkspaceEdit → new snapshot
```

“IR” means intermediate representation; “CST” means concrete syntax tree. Add a
source-preserving token/CST layer alongside the current semantic parser, not a
second independent TypeScript interpretation of Remarp. Extend the compiler's
existing parse/build entry points to expose versioned editor data. No editor IR,
source-map CLI flag, or preview remote procedure call (RPC) interface is implemented
today; choose the concrete API
during implementation and feature-detect its version in the extension.

### 4.1 Source mapping and identity

Each editable node needs:

- Owning source Uniform Resource Identifier (URI), snapshot revision, exact source
  range, and semantic field.
- Parent slide/block identity and optional Canvas DSL identity.
- Render handle, legacy CSS target, and explicit capability list.
- Original tokens needed for minimal replacement, including quotes and whitespace.

Keep original text separately from normalized compiler text. Map normalized offsets
back to the original, then explicitly convert Python code-point positions to VS
Code UTF-16 positions. Test Korean, combining characters, emoji, CRLF, empty
slides, fenced examples, nested blocks, and preserved comments.

Do not use a content hash alone: duplicates collide and edits change hashes.
Start with revision-scoped editor handles and reconcile selections across rebuilds
using known source edits and semantic ownership. If reordering or duplicate content
is ambiguous, clear selection and require reselection rather than guessing. Canvas
IDs are scoped by source/slide/Canvas block. Persistent IDs across sessions would
require an explicit later syntax/metadata decision; an `@id` directive is not
assumed to exist.

Keep legacy runtime/CSS IDs separate. One canonical compiler resolver maps authored
CSS targets such as `card:0` to emitted handles. Structural reorder/delete commands
must remap any affected positional overrides or refuse the operation with a source
diff; a stable editor handle does not fix positional CSS semantics by itself.

### 4.2 Typed edit transactions

The shell submits intents such as `setText`, `setDirective`, `setCssProperty`,
`moveCanvasNode`, `resizeCanvasNode`, or `setRevealStep`. These are proposed
protocol operations, not current CLI commands. An intent includes an opaque mapped
target, document revisions, preview generation, operation ID, and validated values.
It does not grant the webview arbitrary paths, selectors, JavaScript, or shell execution.

The host owns target resolution and editing:

1. Verify workspace trust, supported protocol, target ownership and capability.
2. Validate types, length/range limits, escaping, and property allowlists.
3. Verify expected document revisions and unchanged target source spans.
4. Produce minimal non-overlapping patches; never rewrite the whole deck by default.
5. Apply one coherent `WorkspaceEdit` per completed user action, then recompile.

Serialize Studio transactions. Cancel/reject stale intents when source typing,
another editor, or an AI proposal changes the base. Do not rebuild through the
currently active editor: the session owns explicit document/project references.
VS Code `WorkspaceEdit` is not a promised multi-file compare-and-swap primitive.
Start with single-document gestures; recheck versions immediately before applying,
verify the result, and reconcile unexpected external changes without overwriting
them. Multi-file AI changes require a reviewed diff and separate conflict tests.
Use the host's Undo/Redo history rather than a second competing source history.

During drag, only the overlay shows a temporary position. Pointer release or a
numeric-field commit writes one change; Escape cancels. Auto-rebuild should not
create one source edit for every pointer movement.

### 4.3 Coordinate spaces

Use runtime-derived transforms, not raw `getBoundingClientRect()` pixels:

- Screen/webview coordinates include editor pan and zoom.
- Slide authoring coordinates follow the deck dimensions and fit transforms.
- Canvas DSL coordinates follow that Canvas block's declared width/height.

The current theme uses a 1080-high deck and ratio-derived width: normally
1920×1080 for 16:9. Legacy 960×540 variables are not the editor coordinate contract.
Canvas defaults are 960×400 and can be overridden. Use inverse composed transforms
for pointer-to-authoring conversion; do not confuse CSS pixels with device pixels.
Test autofit, browser zoom, editor zoom, pan, and non-16:9 decks independently.

### 4.4 Live builds and failures

Preview consumes unsaved document snapshots without automatically saving or
overwriting published output. Use an isolated temporary build/staging root,
preserve project-relative structure, and map assets through a host-controlled
manifest. Custom local images are not automatically bundled by today's compiler:
explicitly handle them, fonts, CSS-relative URLs, queries, and fragments. Resolve
real paths and symlinks; reject traversal outside allowed roots, and require
explicit permission for additional roots. Never make the whole filesystem a resource root.

Debounce source typing, serialize/coalesce builds, and discard older generation
results. Initially rebuild the complete snapshot project: ADR-024 permits full
regeneration; dependency-aware caching follows only with equivalent tests. Clear
temporary output on session close and process restart recovery.

Preserve the current slide, selection when unambiguous, zoom/pan, fragment step,
and active tab. Reapply only compatible state after a structural edit. While
compilation fails, keep the last good preview with a prominent **stale revision**
badge and source diagnostics. Disable visual writes against stale mappings; never
present old pixels as the successful result of a new edit.

Missing Python/compiler, untrusted workspace, or unsupported compiler API gets an
actionable fallback to source/approximate preview. Publish/build retains the
existing zero-CRITICAL validation contract. If a transient parseable draft cannot
pass that gate, show diagnostics and last-good output; any future draft-render
mode must be explicitly non-publishable and must not weaken `build`/`sync`.

### 4.5 Renderer isolation

Workspace trust permits invoking the selected compiler; it does not entitle
authored HTML or scripts to invoke arbitrary source edits. The outer shell owns
the VS Code bridge and loads only controlled editor scripts under its own CSP
(Content Security Policy). The deck is a separate sandboxed iframe, without the
outer bridge or a same-origin escape path.

Renderer messages are observations, not write commands. Check schema, size,
sender window, active generation and message channel; do not rely on origin alone
for sandboxed frames with opaque origins. Treat DOM labels/geometry as untrusted
data, and cross-check target handles against the host's source map. A malicious
deck must not trigger source writes merely by posting an edit-looking message.
Only explicit actions in the controlled editor UI reach the transaction service.

Prove resource loading, font fidelity, runtime communication and iframe separation
in an early spike before exposing writeback. Arbitrary `:::script`, iframe content,
and HTML islands receive no editing capabilities. Design mode can disable unsafe
authored scripts and marks that preview as restricted, not pixel-identical. Play
can run them only under explicit trust, still isolated and without write access.
Compiler-controlled interactions should retain fidelity in both modes. Remote
resources need bounded CSP policy and clear unavailable-resource diagnostics.

## 5. Editing coverage and AI integration

| Content | Initial editing | Later adapters / limits |
|---|---|---|
| Heading, paragraph, list item | Selected text/Markdown span | Rich inline formatting with lossless mappings |
| Slide directives | Existing type/layout/fit/background fields | Type conversion only with a source diff and loss checks |
| Theme | Supported frontmatter fields and inheritance | Shared tokens/assets without changing slide-source ownership |
| Cards, columns, steps, timeline | Text and supported layout/style properties | Reorder/add/delete with positional override remapping |
| Tabs, quiz, fragments, notes | Source-backed fields; real interaction preview | Typed answer/step editors that preserve reveal semantics |
| Canvas DSL | Label, geometry, size, supported style and step | Connectors/waypoints with scoped IDs and duplicate checks |
| Mermaid / Archify / charts | Accurate preview when supported, source editing | Specialized structured editors, no arbitrary node-to-CSS conversion |
| Raw HTML/script/iframe | Opaque island, source shortcut, restricted-mode notice | No generic visual writeback promise |

### AI workflow

An initial release may expose a scoped request and the existing issue-annotation
handoff to `/slide-fix`; label it as such. Do not portray annotation writing as an
executed AI call. A subsequent host adapter may integrate a configured Claude or
Codex session, using actual supported capabilities rather than invented agent APIs.

The integrated path is:

`select scope → disclose context → generate proposal → candidate preview + source diff → apply/reject`

Default scope is the selection or current slide, not the entire repository. Include
source revision, source spans, constraints, relevant theme/assets and diagnostics;
send screenshots or broader files only with visible user permission. Treat authored
notes, comments and embedded content as data, not instructions granting extra tools.
Provider authentication remains host-managed; do not embed credentials in webview
HTML, messages, source annotations, or logs.

Both deterministic inspector edits and AI edits use the same patch validation and
revision checks. AI output is a proposal, never unrestricted generated JavaScript
or an automatic shell command. Candidate previews use isolated source snapshots;
Reject leaves files unchanged. Variants derive from a named base revision and can
be compared without saving all candidates into the main deck. Applying an old
variant requires regeneration/review against the current source. Record accepted
changes in normal source/Undo history; Git commits and deployment stay opt-in.

## 6. Delivery order and maintained ownership

| Phase | Deliverable | Primary maintained paths | Exit condition |
|---|---|---|---|
| 0 | Renderer/resource/isolation spike and CSS target regression | `src/compiledPreview.ts`, compiler, extension tests | Fonts/assets/runtime work in isolated renderer; no renderer-triggered writes; `card:0` resolves correctly |
| 1 | Persistent canonical preview, snapshot builds, diagnostics/state | `src/extension.ts`, preview session/build coordinator under `src/`, compiler API | Unsaved typing updates accurately; stale generations never replace newer output; no forced saves |
| 2 | Source spans, editor IR, selection/layers and text/directive/style transactions | Compiler parser/generator; `src/source.ts`, transaction/protocol modules; Studio media | Single-element change round-trips losslessly; external typing and Undo remain coherent |
| 3 | Canvas editing and supported structural operations | `src/canvasEditor.ts`, `src/cssEditor.ts`, `src/visualEditor.ts`, editing media | Geometry correct across transforms; one gesture/one Undo; unsupported edits are explicit |
| 4 | Scoped AI proposals, candidate preview, diff/apply/reject | `media/prompt-bar.js`, host adapter, transaction service | No mutation before Apply; no stale proposal writes; consent and cancellation verified |
| 5 | Specialized adapters or optional browser host | Shared Studio protocol/UI, within existing tool scope | Equivalent rendering/source tests; separate browser filesystem/auth design accepted |

Do not start by enabling all dormant event handlers. Reuse useful interaction
code, but replace independent source splitting and whole-block serialization with
canonical mappings and transactions. Keep the existing approximate preview clearly
labeled until it can be retired without losing the dependency-free fallback.

The shared compiler lives in `plugins/aws-content-plugin/`; maintain it there and
regenerate **both** host packages and compatibility overlays after implementation
changes. Update extension guides, Remarp references and the accepted decision when
features actually ship. This dated design document itself changes no package behavior.

## 7. Acceptance and verification

| Dimension | Required evidence |
|---|---|
| Rendering | Compare compiled export and Studio deck region with identical fonts/theme/viewport/state; normal types, Full HD (FHD, 1920×1080)/4K, non-16:9, tabs/fragments/Canvas steps; exclude only editor chrome |
| Lossless edits | No-op preserves source byte-for-byte; one field edit changes only intended tokens; nested colon fences, code examples, notes, comments, unknown blocks, CRLF and Unicode fixtures |
| Identity | Duplicate slides/nodes, insertion/deletion/reorder, merged blocks and per-file ownership; ambiguous mapping disables edit rather than guessing; positional CSS remains attached to intended content |
| Transactions | Source typing during drag/build/AI, old messages, cancellation, Undo/Redo, failed apply, document close, session disposal and multi-file conflicts |
| Coordinates | Screen/slide/Canvas round trips under zoom/pan/autofit, variable ratios, browser scale and high-DPI displays |
| Isolation | Forged messages from authored scripts, raw HTML, iframes; traversal/symlink assets, CSS/URL injection, untrusted workspace; verify no file-write capability escapes |
| Projects | Single file and ordered multi-file deck, `_presentation.md`, relative images/fonts, missing/remote resources, changed theme and last-good stale output |
| Accessibility | Keyboard selection/commit/cancel, focus retention, screen-reader labels, numeric geometry controls, Korean IME, independent UI/slide themes |
| AI | Scoped context disclosure, diff/candidate preview, rejection without changes, stale variant handling, actual provider errors and opt-in execution |

Measure typing-to-preview latency and drag-frame smoothness on recorded hardware
and representative small/large decks. Initial design targets are <=1 second for a
warm single-slide update and <=16.7 ms overlay frame work; they are **unmeasured
targets**, not existing performance claims. Full-project rebuild behavior may miss
the latency target; optimize only after parity and source-safety tests exist.

Implementation verification includes extension `npm test`, compiler regressions,
browser interaction/screenshot tests, and all root-required marketplace checks.
Before publishing a deck, keep the existing Remarp validate/build, `check_deck.py`,
`measure_deck.py`, interactive screenshots, and content-review PASS gates. Preview
diagnostics are not certification of deployment quality.

### Investigation evidence and limitations

- Python parser probes confirmed that fenced `---`/directive-looking text remains
  literal and that the cards CSS selector mismatch above is real generated output.
- After installing locked development dependencies with install scripts disabled,
  the current extension's `npm test` passed all 19 tests. These validate current
  behavior, not the proposed Studio.
- No interactive Studio prototype, screenshot comparison, source-safe transaction
  implementation, or measured latency is provided by this design investigation.

## 8. Decision summary

The highest-leverage sequence is **canonical live preview → source mapping and
transactions → constrained visual editing → scoped AI proposals**. A polished
canvas without these foundations would merely make source/render drift easier to
create. Browser-first remains possible, but the existing extension is the fastest
place to prove fidelity, Undo, ownership and safety before expanding the host surface.
