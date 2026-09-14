---
sidebar_position: 11
title: "VS Code extension"
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


# VS Code extension

The repository's Remarp extension provides syntax highlighting, slide navigation, preview, source building, outline, completion, and issue annotations for source editing. Use the package manifest as the authority for registered commands, settings, and shortcuts.

## Local setup {#local-setup}

```bash
cd tools/remarp-vscode
npm install
npm run compile
```

Open the extension project in VS Code and launch the Extension Development Host, or package/install a VSIX using the extension tooling. The checked-in package declares its VS Code engine requirement and publisher; documentation does not establish that a particular package is currently published in the Marketplace.

## Commands and shortcuts {#commands-and-shortcuts}

| Command ID | Function |
| --- | --- |
| `remarp.preview` | Open approximate text preview |
| `remarp.previewCompiled` | Save, build and preview compiled HTML |
| `remarp.nextSlide` | Move to next slide |
| `remarp.prevSlide` | Move to previous slide |
| `remarp.build` | Build HTML |
| `remarp.submitIssues` | Show the slide-fix guide |

The manifest registers Ctrl/Cmd+Shift+Right and Left for slide navigation, and Ctrl/Cmd+Shift+B for build while the editor language is Remarp. It does not register the previously documented Ctrl/Cmd+Shift+E shortcut.

## Settings {#settings}

| Setting | Default | Purpose |
| --- | --- | --- |
| `remarp.buildScriptPath` | Empty | Explicit absolute converter path, before automatic discovery |
| `remarp.scrollSync` | true | Synchronize source cursor and preview slide |

`remarp.autoPreview` and `remarp.buildOnSave` are not current contributed settings.

## Editing and issues {#editing-and-issues}

Preview includes notes and slide-specific issue annotations. `<!-- issue: ... -->` records a repair request for slide-fix. Edit the Markdown/CSS/Canvas source, rebuild, and inspect the generated HTML in a browser.

Compiled preview uses the generated HTML and shared runtime/assets, with no Visual Edit controls or writeback. Re-run the command after source changes; the approximate text preview updates as you type.

## Boundaries {#boundaries}

The extension recognizes `.remarp.md`, `_presentation.md`, `_presentation.remarp.md`, and `.md` with `remarp: true`. Builds save dirty project sources and build the directory beside a presentation marker, opening `index.html`; standalone source opens `slides/default.html`. Failed saves/builds show errors and stop compiled preview. Builds and preview scripts require workspace trust. Preview, outline and navigation ignore separators inside code fences. Validate final browser behavior separately.

[Commands, settings, and keybindings](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/package.json) · [Editor implementation](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/src/)
