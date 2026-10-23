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

## 탐색과 상세 정보 계층 {#navigation-and-detail-layers}

화면 오른쪽 위 모서리에 마우스를 올리면 덱 아젠다가 열립니다. Cmd+K,
Ctrl+K 또는 `/`를 누르면 슬라이드 제목, 화면에 보이는 내용과 상세 정보
텍스트를 검색합니다. 발표자 노트는 검색하지 않습니다. 아젠다와 검색은
덱 창에서만 제공되며 개요, 발표자 미리보기, 측정과 내보내기 화면에서는
숨겨집니다.

짧은 설명에는 툴팁을 사용합니다.

```markdown
[UDP 8472]{tip="Cilium VXLAN port"}
```

긴 설명에는 슬라이드 범위의 상세 정보 블록을 사용합니다.

```markdown
[UDP 8472]{detail=vxlan-8472}

:::detail vxlan-8472 "Why UDP 8472 is required"
tip: Cilium VXLAN tunnel port between hybrid nodes

The port carries VXLAN traffic between nodes.
:::
```

상세 정보 블록은 같은 슬라이드의 최상위에 있어야 합니다. ID가 중복되거나
참조할 블록이 없으면 CRITICAL `DETAIL_REF` 진단이 발생합니다. 툴팁은 마우스
호버와 키보드 포커스로 표시되며, 툴팁만 있는 용어는 터치도 지원합니다.
툴팁 위로 마우스를 옮기면 계속 읽을 수 있고 Esc로 닫을 수 있습니다.
상세 정보 패널은 클릭, Enter 또는 Space로 열고 Esc, 바깥 영역 클릭 또는
슬라이드 변경으로 닫습니다.

## 청중 수준에 맞는 설명 {#audience-aware-explanations}

독립적으로 열어 볼 수 있는 각 블록에서 낯선 용어, 업계 용어와 약자가
처음 의미 있게 등장할 때 설명을 붙입니다. API, JSON, EKS, S3처럼 업계에서
흔히 쓴다는 이유만으로 청중도 안다고 가정하지 않습니다. 모든 반복에
설명을 붙이기보다는, 한참 뒤 다시 나와 맥락을 잃기 쉬울 때 보충합니다.

**L100–200**(`level: 100`/`200` 또는 `beginner`/`intermediate`)에는 약자의
전체 이름, 쉬운 뜻, 실용적인 예시나 중요한 이유를 제공합니다. 호버에는
짧고 유용한 요약을 넣고 여러 문장으로 가르쳐야 하는 내용은 상세 정보
패널에 둡니다. L300–400은 더 간결하게 설명하되 낯선 전문 용어는 여전히
풀어 줍니다. 발표자 노트만으로 청중이 직접 볼 수 있는 설명을 대신할 수는
없습니다.

```markdown
[API]{detail=api}

:::detail api "How an API connects applications"
tip: API (Application Programming Interface): an agreed way for programs to request data or actions.

An API defines which requests a program accepts and what it returns.
For example, a weather app requests a forecast instead of collecting sensor data itself.
:::
```

- **차트:** 가까운 곳에 ‘차트 읽는 법’ 설명을 붙여 축, 단위, 대상과 기간,
  비교 기준, 핵심 해석, 한계나 출처 중 해당 차트와 데이터에 맞는 항목을
  안내합니다. 차트 이미지 자체가 아니라 접근 가능한 텍스트 캡션을 상세 정보
  열기 요소로 사용합니다.
- **인용문:** 인용한 문장을 보존하고 발언자나 출처를 표시합니다. ‘인용 맥락’
  설명에는 출처·배경과 이 인용이 중요한 이유를 넣습니다. 예시이거나 확인되지
  않은 인용은 명확히 표시하며 출처를 지어내지 않습니다.
- **정적 내보내기:** 핵심 주장, 차트 레이블과 단위, 핵심 해석, 인용 출처는
  화면에 남겨 둡니다. 호버와 상세 정보 계층은 내보낸 슬라이드 이미지에
  포함되지 않습니다.

콘텐츠 리뷰에서 설명의 누락 여부와 청중 수준 적합성을 확인합니다.
컴파일러는 주석 구조를 검사하며, 전문 용어를 식별하거나 사실의 정확성을
판단하지는 않습니다.

## 문장 품질 검사 {#copy-gates}

`EM_DASH`, `AI_TONE`, `AUDIENCE_TONE`은 소스 검증 경고이며 작성 단계에서 반드시
수정합니다. `SENTENCE_RUNON`은 렌더링 측정 경고입니다. 카드 설명은 주장
한 줄과 선택적인 이유 한 줄로 제한하고 추가 설명은 `:::detail`에 둡니다.

## 디자인과 노트 {#design-and-notes}

의미 기반 토큰과 클래스 기반 테마를 사용합니다. 브랜드 설정에는 프레임워크가 사용하는 `--pptx-*` 변수를 활용합니다. 글자 계층과 대비를 명확히 유지하고 공유 AWS 아이콘 라이브러리를 사용합니다. 메시지, 실무적 의미, 청중 반응 유도와 다음 내용으로의 전환을 설명하는 유용한 노트를 포함합니다.

## 도구와 내보내기 {#tools-and-exports}

소스 디렉터리에는 변환기, 테마 추출기, 내보내기 도구, 프레임워크 에셋, 아이콘과 참고 패턴이 있습니다. `build`, `sync`, `migrate`, `issues`와 `validate`는 변환기의 하위 명령입니다. 브라우저 내보내기와 스크린샷 기반 PPTX 도구는 네이티브 편집형 PowerPoint 생성과 구분합니다.

[빌드 CLI](/docs/remarp-guide/build-cli) · [문법](/docs/remarp-guide/syntax/frontmatter) · [디자인 토큰](/docs/remarp-guide/themes/css-variables)


[스킬, 리소스와 품질 요구 사항](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md)
