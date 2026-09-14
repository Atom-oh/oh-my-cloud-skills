# Remarp VSCode Extension

Source: `tools/remarp-vscode/` | Entry: `src/extension.ts` | Preview: `src/preview.ts`

Extracted from the root `CLAUDE.md` (2026-08 token diet): this detail is only needed when
working on the extension itself — read it when working in `tools/remarp-vscode/`.
Build/package commands are canonical in `tools/remarp-vscode/CLAUDE.md`, not here.

## File Detection

- `.remarp.md` extension → auto `remarp` language ID
- `_presentation.md` and `_presentation.remarp.md` → recognized project source
- `.md` + frontmatter `remarp: true` → auto `remarp` language ID switch
- `.html` + `<meta name="generator" content="remarp">` → recognized as Remarp HTML

## Preview commands

| Mode | File | Rendering |
|------|------|-----------|
| Approximate text (`remarp.preview`) | Remarp source | Unsaved slide text + notes/issues; not compiler parity |
| Compiled (`remarp.previewCompiled`) | Saved Remarp source | Build, then display generated HTML with its shared runtime/assets |

Builds save dirty project sources and use `build <directory>` beside either presentation marker (or `remarp.yaml`/`remarp.yml`), otherwise `build <file>`.
Compiled preview reads project `index.html` or standalone `slides/default.html` from disk after success; errors stop preview and open build output. Re-run after changes.
Builds and preview scripts require workspace trust. Text preview, outline and navigation share fence-aware boundaries (CRLF, backtick/tilde fences).

- **Sidebar layout**: Right panel with Speaker Notes + Issue badges + Prompt bar + Submit button
- **Arrow key slide navigation**: ←→ / Space / PageUp/PageDown (inside preview)
- **Scroll Sync**: `remarp.scrollSync` setting controls editor cursor ↔ preview slide sync
- **Source file tracking**: HTML `<meta name="remarp-source">` → auto-discovers `.md` file (up to 3 parent dirs)
- **Slide type rendering**: cover, compare, tabs, agenda, timeline, quiz, checklist, cards, code, steps, title, section, thankyou
- **Directive rendering**: `@background` → background image, `@badge` → overlay image

## Issue Annotation System

- **Prompt bar**: Sidebar input → inserts `<!-- issue: text -->` into source `.md`
- **Issue badges**: Yellow badges in sidebar, removable via × button
- **Slide fix**: `remarp.submitIssues` command → shows toast guiding user to run `/slide-fix` in Claude Code
- **`/slide-fix` skill**: Reads `<!-- issue: -->` annotations via `remarp_to_slides.py issues --json`, fixes each slide, removes annotations, rebuilds HTML
- **Auto-cleanup**: `/slide-fix` removes `<!-- issue: -->` comments after fixing

## Unwired visual-edit helpers

CSS/Canvas editing controllers remain unwired. Compiled preview injects no Edit
buttons or writeback bridge; modify source and rebuild. No edit-mode shortcut is registered.

## Key Files

| File | Role |
|------|------|
| `src/extension.ts` | Entry point: command registration, file detection, build script discovery |
| `src/preview.ts` | Preview panel: MD/HTML rendering, slide parsing, navigation |
| `src/compiledPreview.ts` | Compiled HTML preview handler for Remarp HTML files |
| `src/outline.ts` | Slide outline provider for editor sidebar |
| `src/completions.ts` | Autocomplete: @directives, :::blocks, :::css, :::canvas DSL |
| `src/cssEditor.ts` | CSS editing: `:::css` block parse/create/update |
| `src/canvasEditor.ts` | Canvas editing: `:::canvas` DSL coordinates/size/step/animate-path update |
| `src/visualEditor.ts` | Visual editor controller: message routing (to CSS/Canvas editors) |
| `media/edit-mode.js` | Webview: drag/resize/property panel UI |
| `media/canvas-editor.js` | Webview: Canvas SVG overlay, hitbox, waypoint editing |
| `media/prompt-bar.js` | Webview: AI prompt bar UI for slide improvement |
