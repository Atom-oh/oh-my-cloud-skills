---
sidebar_position: 1
title: "인터랙티브 프레젠테이션 스킬"
---

# 인터랙티브 프레젠테이션 스킬

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="trigger-keywords" />
<span id="provided-resources" />
<span id="assets" />
<span id="scripts" />
<span id="references" />
<span id="icons" />
<span id="key-features" />
<span id="remarp-format-recommended" />
<span id="pptx-theme-extraction" />
<span id="data-visualization-patterns" />
<span id="typography-hierarchy" />
<span id="css-only-charts" />
<span id="kpi-card-layout" />
<span id="chartjs-integration" />
<span id="canvas-vs-html-decision-guide" />
<span id="the-4-box-rule" />
<span id="decision-matrix" />
<span id="html-architecture-pattern" />
<span id="remarp-workflow-detail" />
<span id="step-1-theme-setup-optional" />
<span id="step-2-content-planning" />
<span id="step-3-create-project-structure" />
<span id="step-4-write-remarp-content" />
<span id="step-5-build-html" />
<span id="step-6-review--iterate" />
<span id="step-7-enhancement" />
<span id="step-8-quality-review" />
<span id="step-9-deploy" />
<span id="interactive-pattern-guide" />
<span id="simulator-pattern" />
<span id="calculator-pattern" />
<span id="dashboard-pattern" />
<span id="speaker-notes-writing-guide" />
<span id="requirements" />
<span id="structure-template" />
<span id="good-example" />
<span id="bad-example-what-not-to-do" />
<span id="slide-types" />
<span id="keyboard-shortcuts" />
<span id="usage-example" />
<span id="quality-review-required" />

Remarp로 발표자 노트, 키보드 탐색, 라이트·다크 테마, 퀴즈, 탭과 다이어그램이 있는 인터랙티브 HTML 덱을 만듭니다. 필요하면 PowerPoint 테마를 추출할 수 있습니다.

## 작업 흐름 {#workflow}

대상 독자, 메시지, 블록과 시간을 계획합니다. 공유 메타데이터에는 `_presentation.md`를, 블록에는 `remarp: true`가 지정된 번호순 `.md` 파일을 사용합니다. 슬라이드 지시문, 단계별 표시, 노트와 참조를 작성하고 검증한 뒤 빌드합니다. 렌더링된 덱을 확인하고 수정하며 게시 전에 콘텐츠 리뷰를 수행합니다.

## 콘텐츠와 상호작용 {#content-and-interaction}

지원하는 슬라이드 형식은 content, code, compare, Canvas, quiz, tabs, timeline과 checklist입니다. KPI 카드, 차트, 그룹이 있는 아키텍처와 읽기 쉬운 레이아웃에는 HTML/CSS 그리드를 사용합니다. 실제 입력·출력 상태를 다루는 계산기나 시뮬레이터에는 `:::script`를 사용합니다. Canvas는 상자·아이콘이 최대 네 개인 단순 선형 다이어그램으로 제한하며, 그룹과 분기에는 HTML/CSS를 사용합니다.

## 디자인과 노트 {#design-and-notes}

의미 기반 토큰과 클래스 기반 테마를 사용합니다. 브랜드 설정에는 프레임워크가 사용하는 `--pptx-*` 변수를 활용합니다. 글자 계층과 대비를 명확히 유지하고 공유 AWS 아이콘 라이브러리를 사용합니다. 메시지, 실무적 의미, 청중 반응 유도와 다음 내용으로의 전환을 설명하는 유용한 노트를 포함합니다.

## 도구와 내보내기 {#tools-and-exports}

소스 디렉터리에는 변환기, 테마 추출기, 내보내기 도구, 프레임워크 에셋, 아이콘과 참고 패턴이 있습니다. `build`, `sync`, `migrate`, `issues`와 `validate`는 변환기의 하위 명령입니다. 브라우저 내보내기와 스크린샷 기반 PPTX 도구는 네이티브 편집형 PowerPoint 생성과 구분합니다.

[빌드 CLI](/docs/remarp-guide/build-cli) · [문법](/docs/remarp-guide/syntax/frontmatter) · [디자인 토큰](/docs/remarp-guide/themes/css-variables)


[스킬, 리소스와 품질 요구 사항](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md)
