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

The repository's Remarp extension provides syntax highlighting, slide navigation, preview, source building, outline, completion, issue annotations, and editing support. Use the package manifest as the authority for registered commands, settings, and shortcuts.

## Local setup

```bash
cd tools/remarp-vscode
npm install
npm run compile
```

Open the extension project in VS Code and launch the Extension Development Host, or package/install a VSIX using the extension tooling. The checked-in package declares its VS Code engine requirement and publisher; documentation does not establish that a particular package is currently published in the Marketplace.

## Commands and shortcuts

| Command ID | Function |
| --- | --- |
| `remarp.preview` | Open preview |
| `remarp.nextSlide` | Move to next slide |
| `remarp.prevSlide` | Move to previous slide |
| `remarp.build` | Build HTML |
| `remarp.submitIssues` | Show the slide-fix guide |

The manifest registers Ctrl/Cmd+Shift+Right and Left for slide navigation, and Ctrl/Cmd+Shift+B for build while the editor language is Remarp. It does not register the previously documented Ctrl/Cmd+Shift+E shortcut.

## Settings

| Setting | Default | Purpose |
| --- | --- | --- |
| `remarp.buildScriptPath` | Empty | Explicit absolute converter path, before automatic discovery |
| `remarp.scrollSync` | true | Synchronize source cursor and preview slide |

`remarp.autoPreview` and `remarp.buildOnSave` are not current contributed settings.

## Editing and issues

Preview includes notes and slide-specific issue annotations. `<!-- issue: ... -->` records a repair request for slide-fix. Visual-edit helpers support CSS property writeback and Canvas position/size/step updates; inspect the source after editing. Remarp-generated HTML can carry generator/source metadata for preview and source discovery, but generated output is still rebuilt from source.

## Boundaries

The registered language extension is `.remarp.md`; the converter also accepts `.md` with `remarp: true`. Preview rendering and the production HTML builder are separate paths. Validate the final generated deck in a browser rather than treating preview success as complete production verification.

[Commands, settings, and keybindings](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/package.json) · [Editor implementation](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/src/)
