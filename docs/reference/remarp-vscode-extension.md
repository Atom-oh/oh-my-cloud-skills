# Remarp VS Code extension

Maintained source: `tools/remarp-vscode/`. Installation, workflow and limitations
are canonical in its [README](../../tools/remarp-vscode/README.md); build/package
commands in [CLAUDE.md](../../tools/remarp-vscode/CLAUDE.md).

## Detection and preview modes

- `.remarp.md`, `_presentation.md` and `_presentation.remarp.md` are source entries.
- `.md` with frontmatter `remarp: true` switches to the `remarp` language.
- HTML with `<meta name="generator" content="remarp">` is recognized compiled HTML;
  `<meta name="remarp-source">` can locate its source (up to three parent directories).

| Command | Source | Contract |
|---------|--------|----------|
| `remarp.preview` | Unsaved source | Approximate text, notes/issues and cursor sync; no compiler parity |
| `remarp.previewCompiled` | Saved source | Save/build then inspect canonical HTML/runtime/assets |
| `remarp.studio` | Unsaved source snapshot | Canonical renderer, editor-only source map, bounded source writeback |

Normal builds save dirty project sources and run `build <directory>` beside a
presentation marker or `remarp.yaml`/`remarp.yml`, otherwise `build <file>`.
Compiled preview reads project `index.html` or the compiler-reported standalone
output (normally `slides/default.html`);
rerun after changes. Studio uses isolated temporary output and never saves source
or replaces those exports. Execution requires workspace trust.

## Studio contract (0.2.0)

`remarp_to_slides.py studio PATH --output DIR` runs canonical validation/build and
emits `studio.json` version 1 beside canonical `index.html` (project) or combined
`studio.html` (single file). Ordinary builds do not emit this editor metadata.
The map identifies actual render handles, owning relative files, source hashes,
original UTF-16 spans and conservative capabilities. CRLF/Unicode/comments are
preserved outside edited spans. Ambiguous spans are not visual-write capabilities.

The extension stages bounded source/config files and referenced local assets.
Sources are limited to 5 MiB/250 files; assets to 32 MiB/2,000 files/4,000 entries.
Traversal, escaping realpaths and asset symlinks fail closed. Compiler processes
have a 60-second timeout. Live resources plus two recent staging directories are
retained; failure paths prune old stages and disposal removes temporary output.
Source/config changes rebuild automatically; asset changes require Refresh.

A nonce-controlled shell owns the VS Code API. Canonical authored code executes
in a separate URL iframe with `sandbox="allow-scripts"`, never `allow-same-origin`.
Renderer observations may update geometry/navigation only; even edit-looking
messages cannot be forwarded as source writes. The host resolves capabilities,
serializes received intents and checks generation, source hashes/document versions
and trust before one `WorkspaceEdit`. Failed compilation keeps a last-good stale
preview with edits disabled. Source-only islands remain accessible through Reveal.

Mapped heading/card text, first safe card body spans, allowlisted CSS/directives and
simple Canvas box/icon geometry/reveal steps are editable. A card without body text has
no body span, because an empty span could only be filled by gluing text onto a heading line;
edit it in source. Icon names, arrows,
complex domain-specific language (DSL) and arbitrary DOM/layout operations are not. CSS indexed card targets
resolve to actual hyphenated renderer IDs. Canvas drags account for both editor and
Canvas scales; pointer release commits once and Escape cancels.

AI uses selected-slide clipboard handoff, pasted replacement source, candidate
compilation and a read-only virtual-document diff before Apply/Reject. Source changes
expire proposals. This is not an automatic provider adapter; no host skills are
invoked by the UI. Issue comments can instead be handled by `/slide-fix` separately.
See [ADR-028](../decisions/ADR-028-remarp-design-studio.md), which partially supersedes
ADR-024 but retains source-first authoring and no general layout DSL.

## Implementation map

| File | Responsibility |
|------|----------------|
| `src/extension.ts` | Command activation, file detection and compiler discovery |
| `src/studio.ts` | Snapshots, serial builds/messages, revisions, edits, proposals, diff and lifecycle |
| `src/studioModel.ts` | Pure allowlisted edit planning and span application |
| `src/studioSnapshot.ts` | Path bounds, hashes and referenced-asset staging |
| `src/studioRenderer.ts` | Controlled shell and isolated renderer resource rewriting |
| `media/studio.js`, `studio.css` | Navigation, layers, inspector, overlay, gesture and proposal UI |
| `media/studio-frame.js` | Renderer runtime/geometry observations, no VS Code API |
| `scripts/remarp_studio.py` (reactive-presentation) | Canonical compiler-backed editor source map |
| `src/preview.ts`, `compiledPreview.ts` | Existing approximate/compiled previews, not Studio writeback |
| `src/outline.ts`, `completions.ts` | Outline and authoring completions |

Legacy `visualEditor.ts`, `cssEditor.ts`, `canvasEditor.ts` and their older webview
assets remain unwired; their presence does not imply additional Studio capabilities.
No stable identity registry, structural reorder, standalone browser host or automatic
AI adapter is implemented. Component tests distinguish real compiler/Chromium probes
from mocked VS Code APIs; a real installed Extension Host smoke test remains separate.
