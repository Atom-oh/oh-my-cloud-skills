# Remarp VSCode Extension

VSCode extension for Remarp presentation format — compiler-backed Design Studio, previews and source issue annotations.

## Build & Test

Run from the repository root:

```bash
cd tools/remarp-vscode
npm install && npm run compile    # Build TypeScript
npx @vscode/vsce package --no-dependencies --out /tmp/remarp-vscode-0.2.0.vsix                  # Package .vsix
code --install-extension /tmp/remarp-vscode-0.2.0.vsix  # Install locally
```

## Architecture

| File | Role |
|------|------|
| `src/extension.ts` | Entry: command registration, file detection, build script discovery |
| `src/studio.ts` | Studio sessions: unsaved snapshots, builds, revision-checked transactions and proposals |
| `src/studioModel.ts` | Pure source patch planning and capability allowlists |
| `src/studioSnapshot.ts` | Bounded source/asset staging and path checks |
| `src/studioRenderer.ts` | Trusted shell and sandboxed compiler-renderer documents |
| `media/studio.js`, `media/studio-frame.js` | Studio UI and observation-only renderer bridge |
| `src/preview.ts` | Preview panel: MD/HTML rendering, slide parsing, navigation |
| `src/compiledPreview.ts` | Compiled HTML preview for Remarp HTML files |
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
- `remarp.studio` uses the canonical compiler `studio` command and writes mapped source spans only.
- Legacy `visualEditor`/`cssEditor`/`canvasEditor` controllers remain unwired; existing previews do not acquire Studio writeback.
- AI proposals use clipboard handoff, candidate compilation and read-only diff, not automatic provider calls.
- Run `npm test` plus `npm run test:browser` (Python Playwright/Chromium and localhost required). Browser tests mock the VS Code API; verify installation separately in a real Extension Host.

> Full detail — file detection rules, preview/sidebar behavior, key-file map — lives
> in `../../docs/reference/remarp-vscode-extension.md` (extracted from the root
> CLAUDE.md, 2026-08 token diet). Build/package commands: the block above is canonical.
