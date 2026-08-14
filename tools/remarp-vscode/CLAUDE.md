# Remarp VSCode Extension

VSCode extension for Remarp presentation format — preview, visual editing, and AI-assisted slide improvement.

## Build & Test

```bash
npm install && npm run compile    # Build TypeScript
npx vsce package                  # Package .vsix
code --install-extension remarp-vscode-*.vsix  # Install locally
```

## Architecture

| File | Role |
|------|------|
| `src/extension.ts` | Entry: command registration, file detection, build script discovery |
| `src/preview.ts` | Preview panel: MD/HTML rendering, slide parsing, navigation |
| `src/htmlPreview.ts` | Dedicated HTML preview for Remarp HTML files |
| `src/outline.ts` | Slide outline provider for editor sidebar |
| `src/completions.ts` | Autocomplete: @directives, :::blocks, :::css, :::canvas DSL |
| `src/cssEditor.ts` | CSS editing: `:::css` block parse/create/update |
| `src/canvasEditor.ts` | Canvas editing: `:::canvas` DSL coordinates/size/step |
| `src/visualEditor.ts` | Visual editor controller: message routing |
| `media/edit-mode.js` | Webview: drag/resize/property panel UI |
| `media/canvas-editor.js` | Webview: Canvas SVG overlay, hitbox, waypoint editing |
| `media/prompt-bar.js` | Webview: AI prompt bar UI |

## File Detection

- `.remarp.md` extension → auto `remarp` language ID
- `.md` + `remarp: true` frontmatter → auto language switch
- `.html` + `<meta name="generator" content="remarp">` → recognized as Remarp HTML

## Key Conventions

- Preview converts relative resource paths to webview URIs and injects CSP
- HTML `<meta name="remarp-source">` links generated HTML back to source `.md`
- Issue annotations (`<!-- issue: text -->`) flow between extension prompt bar and `/slide-fix` skill
- Visual edit mode (`Cmd+Shift+E`) writes CSS/canvas changes back to source `.md`

> Full detail — file detection rules, preview/sidebar behavior, key-file map,
> build/package commands — lives in `<repo-root>/docs/reference/remarp-vscode-extension.md`
> (extracted from the root CLAUDE.md, 2026-08 token diet).
