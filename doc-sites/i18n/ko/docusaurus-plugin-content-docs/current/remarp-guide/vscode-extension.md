---
sidebar_position: 11
title: "VS Code 확장"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
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


# VS Code 확장

이 저장소의 Remarp 확장은 소스 편집을 위한 구문 강조, 슬라이드 탐색, 미리 보기, 소스 빌드, 개요, 자동 완성과 이슈 주석을 제공합니다. 등록된 명령, 설정과 단축키의 기준은 패키지 매니페스트입니다.

## 로컬 설정 {#local-setup}

```bash
cd tools/remarp-vscode
npm install
npm run compile
```

VS Code에서 확장 프로젝트를 열고 Extension Development Host를 실행하거나 확장 도구로 VSIX를 패키징·설치합니다. 저장소의 패키지에 VS Code 엔진 요구 사항과 게시자가 명시되어 있지만, 문서만으로 특정 패키지가 현재 Marketplace에 게시되어 있다고 판단하지는 않습니다.

## 명령과 단축키 {#commands-and-shortcuts}

| 명령 ID | 기능 |
| --- | --- |
| `remarp.preview` | 간이 텍스트 미리 보기 열기 |
| `remarp.previewCompiled` | 저장·빌드 후 컴파일된 HTML 미리 보기 |
| `remarp.nextSlide` | 다음 슬라이드로 이동 |
| `remarp.prevSlide` | 이전 슬라이드로 이동 |
| `remarp.build` | HTML 빌드 |
| `remarp.submitIssues` | slide-fix 가이드 표시 |

매니페스트에는 편집기 언어가 Remarp일 때 슬라이드 탐색에 사용하는 Ctrl/Cmd+Shift+Right와 Left, 빌드에 사용하는 Ctrl/Cmd+Shift+B가 등록되어 있습니다. 과거 문서에 있던 Ctrl/Cmd+Shift+E는 등록되어 있지 않습니다.

## 설정 {#settings}

| 설정 | 기본값 | 목적 |
| --- | --- | --- |
| `remarp.buildScriptPath` | 비어 있음 | 자동 탐색보다 우선하는 변환기의 명시적 절대 경로 |
| `remarp.scrollSync` | true | 소스 커서와 미리 보기 슬라이드 동기화 |

현재 등록된 설정에는 `remarp.autoPreview`와 `remarp.buildOnSave`가 없습니다.

## 편집과 이슈 {#editing-and-issues}

미리 보기는 노트와 슬라이드별 이슈 주석을 제공합니다. `<!-- issue: ... -->`로 slide-fix에 전달할 수정 요청을 기록합니다. Markdown/CSS/Canvas 소스를 편집하고 다시 빌드한 뒤 브라우저에서 생성된 HTML을 확인합니다.

컴파일 미리 보기는 생성된 HTML과 공유 런타임·자산을 사용하며 Visual Edit 컨트롤이나 소스 역반영 기능은 제공하지 않습니다. 소스 변경 후 명령을 다시 실행합니다. 간이 텍스트 미리 보기는 입력 중 자동 갱신됩니다.

## 지원 범위 {#boundaries}

확장은 `.remarp.md`, `_presentation.md`, `_presentation.remarp.md`와 `remarp: true`가 있는 `.md`를 인식합니다. 빌드는 변경된 프로젝트 소스를 저장한 뒤 프레젠테이션 설정 파일이 있는 디렉터리를 빌드하고 `index.html`을 엽니다. 단독 소스는 `slides/default.html`을 엽니다. 저장·빌드 실패 시 오류를 표시하고 컴파일 미리 보기를 중단합니다. 빌드와 미리 보기 스크립트에는 작업 영역 신뢰가 필요합니다. 미리 보기·개요·탐색은 코드 펜스 안의 구분자를 무시합니다. 최종 브라우저 동작은 별도로 검증합니다.

[명령, 설정과 키 바인딩](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/package.json) · [편집기 구현](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/src/)
