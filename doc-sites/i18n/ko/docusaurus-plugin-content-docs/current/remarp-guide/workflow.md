---
sidebar_position: 3
title: "덱 작성과 수정"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="사용-워크플로우" />
<span id="전체-흐름" />
<span id="1단계-프레젠테이션-생성" />
<span id="2단계-vscode에서-편집" />
<span id="편집-예시--슬라이드-내용-수정" />
<span id="편집-예시--퀴즈-추가" />
<span id="편집-예시--canvas-다이어그램-추가" />
<span id="3단계-프롬프트로-반영" />
<span id="반영-프롬프트" />
<span id="예시" />
<span id="4단계-브라우저-프리뷰" />
<span id="키보드-조작" />
<span id="인터랙티브-슬라이드-조작" />
<span id="5단계-html-직접-편집-선택" />
<span id="확인-방법" />
<span id="visual-edit-모드" />
<span id="canvas-visual-edit" />
<span id="이슈-기반-리뷰-워크플로우" />
<span id="반복-편집-사이클" />
<span id="증분-빌드" />
<span id="슬라이드-타입-빠른-참조" />
<span id="다음-단계" />


# 덱 작성과 수정

## 기획과 생성 {#plan-and-generate}

대상 독자, 기술 수준, 언어, 발표 시간, 출력 형식과 원본 자료를 지정합니다. 블록과 슬라이드별 핵심 메시지를 계획합니다. 웹 결과물은 reactive-presentation 작업 흐름에서 Remarp 소스를 작성하고 브라우저로 볼 수 있는 덱을 빌드합니다.

## 소스 편집 {#edit-source}

편집기 미리 보기로 슬라이드를 탐색하고 노트를 확인합니다. 소스에서 콘텐츠, 지시문, 단계별 표시, 퀴즈, 탭이나 단순 Canvas DSL을 수정합니다. 현재 등록된 편집기 명령은 visual-edit/writeback 도구를 제공하지 않으므로 소스를 수정하고 다시 빌드합니다. 지원되는 진입점은 [편집기 가이드](./vscode-extension.md)를 확인합니다.

## 이슈 기반 수정 {#issue-based-revision}

영향을 받는 슬라이드와 관찰 가능한 문제를 포함해 구체적인 이슈를 `<!-- issue: ... -->`로 기록합니다. slide-fix를 실행해 소스를 확인·수정하고 해결된 주석을 제거합니다. 미해결 이슈는 보고서에 남깁니다. 변환기의 `issues` 명령으로 주석 목록을 확인합니다.

## 빌드와 검증 {#build-and-verify}

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/ --lang en
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py sync ./my-presentation/
```

첫 슬라이드와 대표 레이아웃을 확인합니다. 단계별 표시, 선택·탭 버튼, 퀴즈, Canvas 단계와 사용자 지정 입력 기능을 실행하고 노트와 발표자 보기를 확인합니다. 에셋과 콘솔 오류도 검사합니다. 유지할 수정은 Remarp 소스에 반영합니다. 다시 빌드하면 HTML에 직접 반영한 변경은 덮어써집니다. 전체 빌드는 병합 덱, 목차와 공유 에셋을 갱신하며 `sync`는 변경된 블록 페이지만 갱신합니다.

## 마무리 {#finish}

생성 결과와 편집 가능한 소스를 함께 보관하고 검증 근거를 기록한 뒤 콘텐츠 리뷰를 통과하고 승인된 게시를 진행합니다. 편집 가능한 PowerPoint 도형과 텍스트가 필요하면 네이티브 PowerPoint 작업 흐름을 사용합니다.

## 관련 링크 {#related-links}

- [콘텐츠](./slide-types/content.md)
- [Canvas DSL](./syntax/canvas-dsl.md)
- [단계별 표시](./syntax/fragments.md)
- [PPTX 추출](./themes/pptx-extraction.md)
