# Remarp Slides: VS Code extension

Source-first presentation authoring with syntax highlighting, outline/completions,
approximate text preview, compiled HTML preview and **Design Studio** (0.2.1).
Remarp remains the source; generated HTML is never an independent editing target.

## Install and open Studio

Build/package commands are maintained in [CLAUDE.md](CLAUDE.md). Install the new
VSIX, not the repository's older `remarp-vscode-0.1.0.vsix`:

```bash
code --install-extension /tmp/remarp-vscode-0.2.1.vsix --force
```

For code-server, use `code-server --install-extension /tmp/remarp-vscode-0.2.1.vsix --force`
in the server terminal, or **Extensions: Install from VSIX...** in the browser UI.

Run **Developer: Reload Window** after installation and choose **Remarp: Open Design
Studio** from the Command Palette. Open a local `.remarp.md`, `_presentation.md`, or
ordinary `.md` with `remarp: true` frontmatter. Studio recognizes the current buffer,
including unsaved frontmatter. With no suitable active source, it uses the sole open
Remarp source or asks you to select a file. Studio requires
VS Code 1.85+, Python 3, workspace trust and a compiler supporting `studio`.
If automatic discovery selects an older installed plugin, configure:

```json
{
  "remarp.buildScriptPath": "/absolute/path/to/oh-my-cloud-skills/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
}
```

This repository does not establish that version 0.2.1 is published on Marketplace.
Installing the VS Code extension is separate from installing Claude/Codex skills.

## Design Studio workflow

- **Slides/Layers**: navigate actual compiler-rendered thumbnails and mapped elements.
- **Design**: select headings/cards, edit mapped text or the first safe card body
  span, change selected local CSS overrides and slide directives. Blank CSS fields
  remove a local override and inherit the theme.
- **Canvas**: move/resize simple box/icon nodes or enter geometry and reveal steps.
  Each released gesture produces one source transaction. Escape cancels a drag.
  Icon service names, arrows and complex domain-specific language (DSL) remain source-editable.
- **Play**: interact with the real presentation runtime; Design reveals fragments
  and Canvas steps for selection. Zoom affects the editor, not the source.
- **Reveal in source**: navigate to the owning file. Undo/Redo targets that source
  editor rather than an unrelated active document.
- **Unsaved changes**: debounce rebuilds into temporary snapshots. Studio neither
  saves source nor overwrites published HTML. Validation errors retain the last
  good preview, mark it stale and disable visual editing until a valid rebuild.
- **Resources**: referenced project-local assets are staged with size/count limits.
  Absolute/traversing paths and asset symlinks are rejected. Refresh after changing
  assets; automatic watching is limited to project source/config files.
  In code-server, the renderer receives a self-contained sandbox document rather
  than navigating to an internal VS Code resource URL. Local scripts, styles,
  CSS imports, fonts and images are bundled; runtime Canvas icons and logos use a
  finite image map. Remote HTTPS assets still require network access. Missing
  optional local media are reported without preventing the rest of the deck from
  rendering. Keep referenced assets inside the presentation project.

### Blank Studio or build errors

**Preview** and **Open Design Studio** are separate commands. Preview does not open
the editable Studio. Version 0.2.1 fixes two code-server startup failures: host
messages rejected after VS Code masks `window.parent`, and nested renderer URLs
that bypass the webview resource service worker. The renderer remains opaque
(`sandbox="allow-scripts"`); it never receives the VS Code API or host-channel token.

Build failures appear in Studio's status/diagnostics and the **Remarp Studio** Output
channel, including errors raised before the UI finishes loading. **Reveal in source**
works even without a successful build. A renderer that does not start within 15
seconds displays a diagnostic; use **Refresh** to retry. If the compiler reports an
unknown `studio` command, update the configured compiler path above.

Studio is not a general browser for arbitrary authored applications. Common inline
interaction handlers are converted to nonce-authorized listeners; nested documents
(including embedded Archify diagrams),
dynamic local script/module imports, and arbitrary local fetch requests are not
bundled. Use the standalone compiled presentation for those browser-only features.

### AI improvement: manual, reviewable handoff

1. Select a slide and enter a request; **Copy AI request** copies its source/context.
2. Run that request in your configured Claude, Codex or other AI session. No
   provider is automatically invoked and the extension stores no provider key.
3. Paste replacement slide source into **Selected slide source / AI response**.
4. **Preview candidate & diff** compiles without modifying the original and opens
   a read-only source diff. **Apply proposal** commits one revision-checked source
   edit; **Reject** leaves source untouched.

Typing or external source changes expire pending proposals. An outdated draft must
be reset from current source before it can be proposed again. Alternatively, **Add
/slide-fix issue** writes `<!-- issue: text -->`; run the skill separately in your AI
host. Studio does not bypass presentation validation, content review or deployment gates.

## Commands and existing authoring tools

| Command | Purpose |
|---------|---------|
| `Remarp: Open Design Studio` | Unsaved canonical preview, bounded source editing and candidate/diff workflow |
| `Remarp: Approximate Text Preview` | Fast unsaved text, speaker notes and issue annotations; not renderer parity |
| `Remarp: Build and Preview Compiled HTML` | Save/build source and inspect generated runtime/assets |
| `Remarp: Build HTML` | Save/build source without opening Studio |
| `Remarp: Next Slide` / `Previous Slide` | Source navigation (`Ctrl+Shift+Right/Left`, `Cmd` on Mac) |
| `Remarp: Show Slide Fix Guide` | Annotation count and instructions to run `/slide-fix` separately |

The Explorer outline tracks slide titles/types. IntelliSense and TextMate grammar
cover directives, colon blocks, fragments, YAML and Canvas DSL. Approximate preview
supports cursor synchronization (`remarp.scrollSync`); Studio is a separate panel.

Approximate Text Preview keeps the slide's aspect ratio while fitting the available
pane, without cropping it behind the notes sidebar. It defaults to 16:9, honors
`ratio: "4:3"`, and gives an explicit `size: 960x720` precedence over `ratio`.
This sizing does not make the approximate renderer identical to compiled output;
use Studio or Compiled HTML Preview to verify final layouts.

## Example

```markdown
---
remarp: true
ratio: "16:9"
title: My Presentation
---
@type: cards
## Options
### First option
Short explanation.
### Second option
Another explanation.
:::notes
Presenter guidance.
:::
---
@type: canvas
## Request flow
:::canvas
box api "API" at 80,180 size 120,50 color accent step 1
box service "Service" at 380,180 size 120,50 color blue step 2
arrow api -> service "request" step 3
:::
```

## Verification and MVP boundaries

```bash
npm test                     # TypeScript build, source planner and mocked host sessions
npm run test:browser          # Python Playwright + Chromium; localhost required
```

Browser tests exercise production shell/frame scripts with a message-recording VS
Code API fixture, not an installed Extension Development Host. Host transaction
tests mock VS Code but run the real Python compiler. Perform a real VS Code smoke
test before publishing: install/reload, open Studio, edit, undo, inspect candidate
and reject/apply. Packaging alone does not prove installation or Marketplace release.

This is not arbitrary WYSIWYG: unsupported/rich blocks remain source-only. Free
positioning applies only to mapped simple Canvas nodes, not cards or flow text.
Full stable identity reconciliation, slide reordering, automatic AI adapters and a
standalone browser host are not shipped. Rebuilds preserve selection by a unique
owning file/title or index and clear the element selection. Ordinary exports omit
Studio metadata. Legacy visual-edit controllers remain unwired in existing previews.

MIT. Part of [oh-my-cloud-skills](../../README.md).
