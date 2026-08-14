# Remarp VSCode Extension

Source: `tools/remarp-vscode/` | Entry: `src/extension.ts` | Preview: `src/preview.ts`

Extracted from the root `CLAUDE.md` (2026-08 token diet): this detail is only needed when
working on the extension itself — read it when working in `tools/remarp-vscode/`.

## Development

```bash
cd tools/remarp-vscode
npm install && npm run compile    # Build TypeScript
npx vsce package                  # Package .vsix
code --install-extension remarp-vscode-0.1.0.vsix  # Install locally
```

## File Detection

- `.remarp.md` extension → auto `remarp` language ID
- `.md` + frontmatter `remarp: true` → auto `remarp` language ID switch
- `.html` + `<meta name="generator" content="remarp">` → recognized as Remarp HTML

## Preview (2 modes)

| Mode | File | Rendering |
|------|------|-----------|
| Markdown | `.md` / `.remarp.md` | Slide parsing → HTML + sidebar (notes, issues, prompt bar) |
| HTML | Remarp HTML | Direct HTML load + resource path → webview URI conversion |

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

## Visual Edit Mode (PPT edit mode)

- **Activate**: `Cmd+Shift+E` / editor titlebar Edit button / per-slide floating Edit button
- **Features**: element drag (position), resize, Property Panel (font/color/margin)
- **CSS writeback**: changes → auto-written to `:::css` block in source `.md`
- **Canvas writeback**: canvas element move/resize → `:::canvas` DSL coordinates updated in source `.md`
- **Canvas editing**: drawio-style SVG overlay hitboxes for element select/move, waypoint editing, step animation control

## Key Files

| File | Role |
|------|------|
| `src/extension.ts` | Entry point: command registration, file detection, build script discovery |
| `src/preview.ts` | Preview panel: MD/HTML rendering, slide parsing, navigation |
| `src/htmlPreview.ts` | Dedicated HTML preview handler for Remarp HTML files |
| `src/outline.ts` | Slide outline provider for editor sidebar |
| `src/completions.ts` | Autocomplete: @directives, :::blocks, :::css, :::canvas DSL |
| `src/cssEditor.ts` | CSS editing: `:::css` block parse/create/update |
| `src/canvasEditor.ts` | Canvas editing: `:::canvas` DSL coordinates/size/step/animate-path update |
| `src/visualEditor.ts` | Visual editor controller: message routing (to CSS/Canvas editors) |
| `media/edit-mode.js` | Webview: drag/resize/property panel UI |
| `media/canvas-editor.js` | Webview: Canvas SVG overlay, hitbox, waypoint editing |
| `media/prompt-bar.js` | Webview: AI prompt bar UI for slide improvement |
