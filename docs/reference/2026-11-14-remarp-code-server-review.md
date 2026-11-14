# Remarp code-server review — 2026-11-14

This is a dated review record, not a release announcement or a waiver of current
validation requirements. The user requested a review of the installed Remarp
extension and an update of the public introduction/editor guides. Extension
source integration and a new VSIX release are separate from publishing those
guides.

## Implementations reviewed

| Target | Verified identity |
| --- | --- |
| Maintained source | `tools/remarp-vscode`, version 0.2.0, main `dc489ce91bd81d5aee5057e6f8af7c3baf874feb` |
| Checked-in VSIX | `remarp-vscode-0.1.0.vsix`, embedded manifest 0.1.0, no Studio command/files |
| Installed development build | `aws-cloud-skills.remarp-vscode` 0.3.0 |
| Matching development source | Existing dirty worktree on `fix/remarp-preview-aspect-ratio`, base `7625af08b0f6cf174a129906863d8790704d63a6`; not integrated into main |
| Real host | code-server 4.106.3 with VS Code 1.106.3, Linux arm64 |

All 17 compiled JavaScript modules and all 11 media files in the development
worktree matched the installed extension byte for byte. Its installed manifest
differed only by VS Code installation metadata. No worktree, stash, live editor
session, or installed extension was modified by the review.

Selected installed-file SHA-256 fingerprints:

| File | SHA-256 |
| --- | --- |
| `out/studioModel.js` | `5911f972b464efe2eb5367309d878ccb5a7e3b1b402b729563892ce61aab2068` |
| `out/studioSnapshot.js` | `820bf7b2a87fb25cf1dea043669300967972627664ebda83ef5abd9d3862dfc5` |
| `out/studioAssets.js` | `f7214d38c906042f7d223dcd4a3d82bd6b6873df32d8b19b3efdb21563d16aea` |
| `media/studio.js` | `267c2e1170613aaa26af7b1bed47f9140ca9c88a786f908ef0bc791715880de2` |

## Findings in the installed-matching 0.3.0 development build

### R1 — Major: structural Markdown accepted in a visual card-body edit

The development `src/studioModel.ts` text/body planner accepts a body containing a
newline and an unclosed code fence. The direct inspector edit is written before
the resulting source is compiled. An exact-span fixture using the installed
planner and main's real Remarp parser changed a two-slide deck into one parsed
slide. The bytes outside the edited span remain, but the fence changes their
meaning. Undo can recover the source; this is not disk deletion.

Carry forward main's structural-text guard before integrating this older-base
development work. It already rejects the same value, and accounts for compiler
line boundaries, slide separators, fences, colon blocks, and card-body headings.
Until corrected, perform structural Markdown changes in the source editor and
validate the complete deck.

### R2 — Major: quoted CSS imports omitted from staging

`src/studioSnapshot.ts` discovers `url(...)` dependencies but not ordinary
`@import "base.css"` or single-quoted imports. The development
`src/studioAssets.ts` bundler supports those forms and treats the imported
stylesheet as required, so a valid local stylesheet can prevent Studio rendering.

A temporary fixture staged `assets/main.css` but omitted its existing sibling
`assets/base.css`. Bundling failed with `Studio resource was not staged`. Copying
that one dependency into the temporary snapshot made the same operation succeed.
Bring staging and bundling dependency recognition into agreement while retaining
path, symlink, recursion, byte, and file-count bounds. Standalone compiled preview
was not shown broken by this reproduction.

### R3 — Minor: Play navigation discards an unsubmitted proposal draft

The Play observation handler in `media/studio.js` replaces the selected source
textarea and clears its dirty flag without the confirmation used by sidebar
navigation. A production-handler fixture replaced `UNSAVED USER DRAFT` with the
next slide's source. The source file itself was unchanged, so source Undo cannot
restore this textarea draft.

Preserve drafts by owning slide or use the same discard/preserve decision for
Play and sidebar navigation. Until corrected, copy out the draft or finish the
candidate decision before navigating. This issue also exists in main 0.2.0.

## Legacy main 0.2.0 code-server findings

- **Host delivery:** its shell checks `event.source` against itself and
  `window.parent`, but the actual VS Code webview API masks `window.parent` with
  the shell window. Production-handler checks under that rule reject real outer
  host messages while accepting the self-posted notices used by the mock tests.
- **Nested renderer resources:** its `asWebviewUri` iframe document cannot
  reliably resolve its owner through code-server's webview service worker. A
  targeted check of the actual worker returned `Could not resolve webview id`
  for the nested resource client, unlike the owning shell client.

The reviewed development build uses a separate host-message token and a bounded
bundled `srcdoc` renderer to address these boundaries. Its renderer remains an
opaque `allow-scripts` iframe without the VS Code API. Do not fix either boundary
by granting `allow-same-origin` or removing the message checks.

## Verification and limits

- Main 0.2.0: three Node test-file groups passed; seven real-Chromium tests passed
  with a mocked VS Code API. These are not real Extension Host certification.
- Installed-matching 0.3.0: 145 Node tests passed without recompiling or modifying
  the existing development worktree.
- Its real-host smoke test copied the extension, profile, and synthetic deck into
  a temporary password-authenticated loopback code-server instance. With the
  current main compiler it verified rendering, opaque isolation, rejected forged
  messages, source-buffer editing and Undo, and candidate Apply/Reject/cancellation.
  The generated source file remained unsaved as intended. Temporary server and
  browser processes were closed afterward.
- All three AI providers in that smoke test were deterministic fake CLI fixtures.
  It did not call paid providers, test real credentials, or certify live CLI/model
  compatibility. Authored-tab and image-heavy project coverage were not part of
  that synthetic real-host run.
- The passing suites do not negate R1–R3, which have separate targeted
  reproductions. No Marketplace availability or release approval is implied.

Public guidance must distinguish Approximate Text Preview, compiled preview, and
Studio. Manual clipboard handoff exists in main; explicit Generate with AI is a
development-build feature until integrated and released. Keep the public
limitations synchronized when these findings are fixed.
