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
| `remarp.preview` | 미리 보기 열기 |
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

저장소에는 visual-edit/writeback과 HTML-preview 도구 클래스가 있지만 현재 등록된 미리 보기·빌드 명령에는 연결되어 있지 않습니다. 등록된 Visual Edit 명령이나 단축키가 없으므로 해당 도구 파일을 사용 가능한 편집 작업 흐름으로 간주하지 않습니다.

## 지원 범위 {#boundaries}

등록된 언어 확장자는 `.remarp.md`입니다. 확장은 `remarp: true`가 있는 `.md` 문서도 감지하며 활성화, 열기 또는 저장 시 편집기 언어를 Remarp로 바꾸어 메뉴, 단축키와 개요를 사용할 수 있게 합니다. 미리 보기 렌더링과 배포용 HTML 빌더는 서로 다른 경로입니다. 미리 보기 성공을 배포 결과의 완전한 검증으로 간주하지 말고 최종 생성된 덱을 브라우저에서 검증합니다.

[명령, 설정과 키 바인딩](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/package.json) · [편집기 구현](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/tools/remarp-vscode/src/)
