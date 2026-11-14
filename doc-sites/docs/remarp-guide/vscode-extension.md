---
sidebar_position: 11
title: "VS Code and code-server"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="vscode-확장" />
<span id="기능" />
<span id="구문-하이라이팅" />
<span id="라이브-프리뷰" />
<span id="visual-edit-모드" />
<span id="canvas-editor" />
<span id="css-writeback" />
<span id="canvas-writeback" />
<span id="이슈-어노테이션--ai-리뷰" />
<span id="html-파일-지원" />
<span id="문서-아웃라인" />
<span id="intellisense" />
<span id="설치-방법" />
<span id="vs-code-marketplace에서-설치" />
<span id="vsix에서-설치-로컬" />
<span id="개발-모드" />
<span id="사용법" />
<span id="키보드-단축키" />
<span id="슬라이드-네비게이션" />
<span id="프리뷰-내-네비게이션" />
<span id="명령어" />
<span id="설정" />
<span id="예제" />
<span id="요구-사항" />
<span id="알려진-제한-사항" />
<span id="marketplace-배포" />
<span id="사전-준비" />
<span id="1-publisher-생성" />
<span id="2-패키지--배포" />
<span id="3-버전-업데이트" />


# VS Code and code-server

Use **Remarp Slides** to edit presentation source, inspect compiled slides, or open Design Studio. This guide is for the person creating or changing a deck. If you received a presentation to deliver, use the [presenter's guide](/docs/aws-content-plugin/presenter-guide); you do not need to install the editor extension.

## Check your version first {#check-your-version}

The extension's version is separate from the cloud-skills plugin version. In the editor's **Extensions** view, open **Remarp Slides** and check its publisher, version, and installation location.

| Package | What the review established |
| --- | --- |
| Checked-in 0.1.0 VSIX | An older package without the Design Studio command |
| Maintained repository source 0.2.0 | Studio and both preview commands; manual AI handoff. Its Studio has known real-host delivery/resource problems in code-server |
| Separately reviewed local 0.3.0 development build | Newer code-server renderer and explicit AI generation. It is not the 0.2.0 source on main, and this guide does not establish that it is publicly released |

For code-server Studio, obtain a build that the maintainer has tested in a real code-server Extension Host. Do not install the old checked-in VSIX expecting Studio, or downgrade a newer installation just to match a filename in an example. If your package has different commands, compare its installed manifest rather than assuming every feature below is present.

The 0.3.0 development build has remaining [review findings](#reviewed-limitations); a successful smoke test does not make it a finished release.

## Install in the editor you actually use {#install-in-your-editor}

1. Obtain the intended VSIX from the maintainer and confirm its version.
2. In **desktop VS Code**, use the Extensions view's menu and **Install from VSIX...** on that computer.
3. In **code-server**, use the same command in the browser-based editor. Make sure the file is available to that server's installation workflow. Installing into desktop VS Code does not install into code-server.
4. Run **Developer: Reload Window**, then confirm that Remarp Slides is enabled in that editor.

If the maintainer supplied a VSIX on the code-server host, its terminal can also use:

```bash
code-server --install-extension /absolute/path/to/remarp-vscode.vsix
code-server --list-extensions --show-versions
```

The expected extension ID is **aws-cloud-skills.remarp-vscode**. A VSIX is the editor extension package, not a slide deck or the Claude/Codex plugin. This repository does not establish Marketplace availability for a particular version.

## Open a source file and connect the compiler {#open-and-configure}

1. Open the folder containing the presentation sources. For a multi-file project, open the folder containing its presentation settings and numbered blocks.
2. Open the actual Markdown slide source in the editor. Save a new file once before using build or Studio. Source detection recognizes the filename and Remarp frontmatter described under [Boundaries](#boundaries).
3. Confirm that the language indicator says **Remarp**. If it still says Markdown after adding frontmatter, save the file and select Remarp through the language selector if needed.
4. For builds and Studio, use a workspace you trust and a Python 3 interpreter available on the **extension host**. In code-server that means the server, not your laptop.
5. Set the compiler path when automatic discovery does not find the intended compiler.

Open the editor's settings, search for **Remarp Build Script Path**, or put this in the appropriate user/remote settings JSON after replacing the path:

```json
{
  "remarp.buildScriptPath": "/absolute/path/to/oh-my-cloud-skills/plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
}
```

Use a path that exists on the extension host. The extension does not install Python or bundle the compiler. A compiler for Studio must support its studio command. Automatic discovery checks nearby/workspace scripts, workspace plugin directories, and a bounded set of parent directories; it does not promise to search every Claude or Codex plugin cache.

## Choose the right view {#choose-a-view}

Open the Command Palette from the editor menu, with **F1**, or with **Ctrl+Shift+P / Command+Shift+P** where the browser allows it. Search for the command title below.

| Command title | Use it for | Save/build behavior |
| --- | --- | --- |
| Remarp: Approximate Text Preview | Quickly check wording, slide order, notes, and issue annotations | Updates as you type; its layout is not the compiler's final layout |
| Remarp: Build and Preview Compiled HTML | Inspect the actual generated slides and runtime | Saves relevant sources, builds, and opens the output; run again after edits |
| Remarp: Open Design Studio | Select and edit supported source-backed elements | Builds temporary snapshots of source buffers; supported edits change the buffer, which you save explicitly |

The compiled preview does not have Studio's visual source editing. The approximate preview can write issue annotations, so do not treat every preview interaction as strictly read-only. Use a tested Studio build for code-server as explained in the version section.

## First edit in Design Studio {#first-studio-edit}

1. Open the source file, run **Remarp: Open Design Studio**, and wait for a successful compiled snapshot. If a build fails, follow its diagnostic; a stale preview is not ready for editing.
2. Choose a slide from **Slides**, then an editable item from **Layers** or the slide overlay.
3. In **Selection**, change **Text / Markdown** or another available field. Available fields depend on that element's mapped source. For a first test, change a short heading using plain text.
4. Click outside the field to commit the edit. Check both the rebuilt preview and the changed Markdown buffer. Use **Reveal in source** to find the owning source.
5. Use **Undo** to confirm that you can reverse the edit. Save the source explicitly when satisfied.
6. Select **Play** to try interactions, then return to **Design** for selection and editing. Finish or copy out any unsubmitted proposal text before navigating in Play.
7. Build the complete presentation and check it in a standalone browser before presenting or sharing it.

If Studio is cramped beside the source editor, enlarge its editor group or adjust the split between them. **Zoom / Fit** changes your editor view; it does not change the deck's aspect ratio or typography.

### What the visual editor can change {#editable-elements}

| Element | Supported edits |
| --- | --- |
| Mapped headings/cards | Text and the first safe card-body span, when a field is available |
| Selected local styling | Allowlisted color, font size/weight, padding, bottom margin, and border radius |
| Slide settings | Available fit, columns, and layout choices |
| Simple Canvas boxes/icons | Position, size, label, and reveal step where supported |
| Complex HTML, arrows, service-icon names, or unsupported structures | Use Reveal in source and edit the source directly |

This is not unrestricted drag-and-drop page design. A missing editing field does not mean the content was lost; it can mean that the source span is not safe to rewrite visually. Keep structural Markdown changes in the source editor, particularly with the reviewed development build.

Source/configuration changes trigger snapshot rebuilds. After changing an image or another asset, use **Refresh**. Studio does not automatically replace your published HTML. A failed rebuild can retain the last good snapshot with visual editing disabled.

## Ask AI to improve one slide {#ai-editing}

### Manual handoff available in the maintained source {#manual-ai-handoff}

1. Select a slide and enter a specific improvement request.
2. Select **Copy AI request**. It copies the selected source and request to your clipboard; it does not call an AI service.
3. Paste into the AI tool you use, and ask for replacement source for that slide only.
4. Paste the returned source into **Selected slide source / AI response**.
5. Select **Preview candidate & diff**, inspect the candidate and source changes, then choose **Apply proposal** or **Reject**.
6. Check the updated source and save it when satisfied.

For example: “Shorten these two cards while preserving their technical meaning, speaker notes, and reveal order.” Keep an external copy of an unsubmitted response before changing slides.

### Explicit generation in the reviewed 0.3.0 development build {#development-ai-generation}

This subsection applies only when your installed build has **Generate with AI**. The maintained 0.2.0 package does not implement that button.

Choose a slide and provider, enter the request, then select **Generate with AI**. The development build runs the selected Claude, Kiro, or Codex CLI on the extension host. Opening Studio does not start generation. The request can use provider quota or incur charges, and the selected source is sent to that provider when you generate.

**AI settings** opens the relevant editor settings. Authentication and the executable must be available on the code-server host under the same user as the extension. The extension does not install the CLI or log you in. Available models and effort levels depend on that provider and CLI; leaving a model blank uses its default.

Review the compiled candidate and diff before **Apply proposal**. **Cancel AI** stops an outstanding request; **Reject** leaves the source unchanged. Applying a proposal edits the source buffer, not an automatically saved or published deck. The real-host review used fake provider CLIs to verify this flow; it did not certify live account authentication or model access.

## Local setup {#local-setup}

This section is for building the extension from a chosen source checkout. Check that checkout's package version before installing its output over an existing installation.

```bash
cd tools/remarp-vscode
npm ci
npm run compile
npx @vscode/vsce package --no-dependencies --out /tmp/remarp-vscode.vsix
```

Packaging may download the VSIX packaging tool if it is not already installed. Alternatively, open the extension project in desktop VS Code and use its Extension Development Host. Neither route proves that the resulting build works in code-server; test the actual target host too.

## Commands and shortcuts {#commands-and-shortcuts}

| Command ID | Function |
| --- | --- |
| `remarp.studio` | Open Design Studio |
| `remarp.preview` | Open approximate text preview |
| `remarp.previewCompiled` | Save, build and preview compiled HTML |
| `remarp.nextSlide` | Move to next slide |
| `remarp.prevSlide` | Move to previous slide |
| `remarp.build` | Build HTML |
| `remarp.submitIssues` | Show the slide-fix guide |

The manifest registers Ctrl/Cmd+Shift+Right and Left for source-slide navigation, and Ctrl/Cmd+Shift+B for build while the editor language is Remarp. It does not register the previously documented Ctrl/Cmd+Shift+E shortcut. These are editor shortcuts, not the [browser presentation controls](/docs/aws-content-plugin/presenter-guide#essential-controls). In a browser that intercepts a shortcut, use the editor menu or Command Palette.

## Settings {#settings}

| Setting | Default | Purpose |
| --- | --- | --- |
| `remarp.buildScriptPath` | Empty | Explicit absolute converter path, before automatic discovery |
| `remarp.scrollSync` | true | Synchronize source cursor and preview slide |

`remarp.autoPreview` and `remarp.buildOnSave` are not contributed settings in maintained 0.2.0. Extra AI settings in a development build do not imply that they exist in an older installed package.

## Editing and issues {#editing-and-issues}

Preview includes notes and slide-specific issue annotations. `<!-- issue: ... -->` records a repair request for slide-fix. **Show Slide Fix Guide** explains the handoff; it does not automatically run an AI reviewer or apply the fixes. Use [slide-fix](/docs/aws-content-plugin/skills/slide-fix) with your AI tool, then validate and rebuild the source.

Changes made in the presentation's browser-only speaker-note editor are separate from extension source edits. They do not update the Markdown that the extension opens.

## Troubleshoot the first run {#troubleshooting}

| Symptom | Check next |
| --- | --- |
| No Open Design Studio command | Installed version and editor location; the checked-in 0.1.0 VSIX does not contain Studio. Reload the editor after installing the intended package |
| Markdown file is not recognized | Remarp filename/frontmatter, saved initial file, and language mode |
| Compiler not found | Explicit compiler path on the server and Python 3 available to its Extension Host |
| Unknown studio command | The configured compiler is older than the Studio interface; choose the matching compiler |
| Studio stays blank in code-server | Check the installed version and diagnostics. Main 0.2.0 has real-host startup problems; use a verified newer build or the standalone compiled deck |
| Source changed but the compiled preview did not | Run Build and Preview Compiled HTML again; that panel does not continuously rebuild |
| Image changed but Studio shows the old image | Use Refresh and keep referenced assets inside the project |
| A field or diagram cannot be edited | Use Reveal in source; not every source construct has a safe visual-edit capability |
| AI button or settings are missing | Check the version. Maintained 0.2.0 uses the manual clipboard handoff |
| AI fails in a development build | Check the provider CLI on the server, authentication, supported options/model, and timeout; do not assume laptop authentication is shared |

## Reviewed limitations {#reviewed-limitations}

The [dated maintainer review](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/docs/reference/2026-11-14-remarp-code-server-review.md) distinguishes main source from the separately installed development build:

- **Main 0.2.0 in code-server:** Studio's host-message and nested-resource delivery can fail even though mocked browser tests pass. Use a real-host-verified package for Studio, and keep the standalone compiled deck as the final check.
- **Local 0.3.0 card-body editing:** structural Markdown such as a code fence can alter later slide structure. Use plain text for a bounded visual edit; make structural changes in source and validate the whole deck.
- **Local 0.3.0 CSS imports:** quoted local imports can be omitted during staging and prevent Studio from rendering. Keep a directly usable stylesheet or use standalone output until that staging path is corrected.
- **Unsubmitted proposal drafts:** navigating in Play can discard the draft. Copy it out or finish the candidate/apply decision before moving to another slide.

These findings describe the reviewed implementations, not a promise that every installation has the same behavior. The development build also excludes arbitrary nested documents and dynamic local resource loading from its bundled Studio renderer; use the standalone deck for embedded diagrams and final presentation testing.

## Boundaries {#boundaries}

The extension recognizes `.remarp.md`, `_presentation.md`, `_presentation.remarp.md`, and `.md` with `remarp: true`. Builds save dirty project sources and build the directory beside a presentation marker. **Build HTML** only builds; **Build and Preview Compiled HTML** opens the project's `index.html` or the compiler-reported output for standalone source. The usual standalone default is `slides/default.html`, but a named block can produce `slides/lesson.html`. Failed saves/builds show errors and stop compiled preview. Builds and preview scripts require workspace trust. Preview, outline and navigation ignore separators inside code fences.

The declared VS Code engine minimum is 1.85. This is a host extension using Node and local files, not a standalone editor that runs entirely inside a browser tab. For actual presentation, hand the recipient the browser deck and [presentation instructions](/docs/aws-content-plugin/presenter-guide), not the editor workspace.

[Commands, settings, and keybindings](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/package.json) · [Editor implementation](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/src/)
