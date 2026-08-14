# Remarp VSCode Extension Issues

## How to Add Issues

After each iteration, add issues in the format below.
The skill parses this document and automatically processes Open issues.

### Issue Format

```markdown
### ISSUE-NNN: [title]
- **Category**: preview | visual-editor | completions | detection | navigation | build
- **Severity**: critical | major | minor
- **Affected**: `src/file.ts` (line ~100)
- **Description**: description of the problem
- **Expected**: expected behavior
- **Screenshot**: (optional) screenshot filename
```

### Categories

| Category | Target Files |
|----------|-------------|
| preview | `src/preview.ts`, `src/htmlPreview.ts` |
| visual-editor | `src/visualEditor.ts`, `src/cssEditor.ts`, `src/canvasEditor.ts`, `media/edit-mode.js`, `media/canvas-editor.js` |
| completions | `src/completions.ts` |
| detection | `src/extension.ts` (file detection, language ID switching) |
| navigation | `src/preview.ts` (slide nav, scroll sync) |
| build | `package.json`, `tsconfig.json`, packaging |

---

## Open

(no open issues currently)

---

## In Progress

(issues being fixed move here)

---

## Resolved

### ISSUE-001: Cannot select inner layers in Edit mode
- **Category**: visual-editor
- **Severity**: major
- **Affected**: `media/edit-mode.js` (line ~134)
- **Description**: Clicking an inner layer inside a nested `[data-remarp-id]` element fired the outer element's `_setupDrag` mousedown handler first, starting a drag, so the inner element could never be selected
- **Expected**: Clicking an inner layer should select that element
- **Fix**: In mousedown, check whether the click target is a nested `[data-remarp-id]`; if it is an inner element, call `selectElement(innerTarget)` instead of starting a drag

### ISSUE-002: Preview tab title doesn't show the filename
- **Category**: preview
- **Severity**: minor
- **Affected**: `src/preview.ts` (line ~56)
- **Description**: The preview panel title was hardcoded to "Remarp Preview", with no way to tell which file the preview was for
- **Expected**: Show the filename as "Remarp Preview - filename.md"
- **Fix**: Use `path.basename(document.uri.fsPath)` in `createOrShow` so the title includes the filename both when the panel is created and when an existing one is reused

### ISSUE-003: Images don't render in preview
- **Category**: preview
- **Severity**: major
- **Affected**: `src/preview.ts` (line ~349)
- **Description**: Relative-path images did not render in the markdown preview. The `<img src>` relative paths in the HTML returned by `_renderMarkdown` were not converted to webview URIs, so the security policy blocked them
- **Expected**: Relative-path images render correctly in the webview
- **Fix**: In `_getHtmlForSlide`, after `_renderMarkdown` returns, convert `<img src>` relative paths with `asWebviewUri()`

### ISSUE-004: Show prompt content instead of Canvas "preview unavailable"
- **Category**: preview
- **Severity**: minor
- **Affected**: `src/preview.ts` (line ~1443)
- **Description**: Canvas blocks only showed a "preview unavailable" message, with no way to check the DSL source content
- **Expected**: The Canvas DSL source code should be shown in a `<pre>` block so its content can be checked
- **Fix**: In the canvas case, render the HTML-escaped DSL source inside a `<pre class="canvas-source">` block

### ISSUE-005: HTML title doesn't show the filename
- **Category**: preview
- **Severity**: minor
- **Affected**: `src/preview.ts` (lines ~322, ~411)
- **Description**: The webview HTML document's `<title>` tag was hardcoded to "Remarp Preview". ISSUE-002 fixed the panel tab title but left the HTML-internal title unfixed
- **Expected**: The filename should be included, as `<title>Remarp Preview - filename.md</title>`
- **Fix**: Use `path.basename()` in the `<title>` tag of both `_getEmptyHtml` and `_getHtmlForSlide` so the filename is included
