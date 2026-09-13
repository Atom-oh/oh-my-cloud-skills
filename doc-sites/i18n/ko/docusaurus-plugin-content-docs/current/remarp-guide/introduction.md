---
sidebar_position: 1
title: "Remarp"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="remarp-소개" />
<span id="왜-remarp인가" />
<span id="비교표" />
<span id="핵심-장점" />
<span id="1-사람이-읽을-수-있는-마크다운" />
<span id="2-프래그먼트-애니메이션" />
<span id="3-canvas-dsl" />
<span id="4-스피커-노트--타이밍" />
<span id="5-pptx-테마-통합" />
<span id="6-멀티파일-프로젝트" />
<span id="7-인터랙티브-패턴" />
<span id="8-vscode-visual-edit" />
<span id="하위-호환성" />
<span id="다음-단계" />


# Remarp

Remarp는 이 저장소의 Markdown 기반 HTML 프레젠테이션 형식입니다. 일반 Markdown에 슬라이드 지시문, 단계별 표시, 발표자 노트, 단순 Canvas 다이어그램, 인터랙티브 슬라이드 유형, 테마 추출과 다중 파일 프로젝트 기능을 추가합니다.

## 작성 방식 {#authoring-model}

프런트매터에 `remarp: true`가 지정된 `.md` 파일을 사용합니다. 짧은 덱은 단일 파일로 작성하고, 긴 발표는 `_presentation.md`와 번호순 블록 파일로 구성합니다. 기존 소스와 편집기 연동을 위해 `.remarp.md`도 계속 지원합니다.

슬라이드는 `---`로 구분합니다. `@type: tabs` 같은 지시문은 콘텐츠 앞에 둡니다. `{.click}`으로 내용을 단계별로 표시하고 `:::notes`에 발표 안내를 작성합니다. 작은 Canvas DSL의 범위를 넘는 레이아웃과 인터랙티브 도구에는 HTML/CSS/script 블록을 사용합니다.

## 작업 흐름 {#workflow}

기획 → 작성 → 검증 → 빌드 → 브라우저 확인 → 콘텐츠 리뷰 순서로 진행합니다. 소스를 수정하고 다시 빌드합니다. 편집기가 변경 내용을 소스에 명시적으로 반영하는 경우가 아니라면 생성된 HTML을 유지 관리할 원본으로 간주하지 않습니다. Marp 마이그레이션을 지원하지만 생성 결과는 여전히 검증과 리뷰가 필요합니다.

## 다음 단계 {#next-steps}

[빠른 시작](/docs/remarp-guide/quick-start) · [프런트매터](/docs/remarp-guide/syntax/frontmatter) · [빌드 CLI](/docs/remarp-guide/build-cli) · [편집기](/docs/remarp-guide/vscode-extension)

## 관련 링크 {#related-links}

- [빠른 시작](./quick-start.md)
- [프런트매터](./syntax/frontmatter.md)
- [VS Code 확장](./vscode-extension.md)
- [Canvas DSL](./syntax/canvas-dsl.md)
