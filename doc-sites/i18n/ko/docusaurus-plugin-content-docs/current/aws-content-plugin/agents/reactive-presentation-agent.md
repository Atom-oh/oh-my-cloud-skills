---
sidebar_position: 2
title: "인터랙티브 프레젠테이션 에이전트"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="presentation-agent와의-관계" />
<span id="워크플로우" />
<span id="phase-1-planning--theme-setup" />
<span id="phase-2-content-authoring-remarp" />
<span id="phase-3-review--build" />
<span id="슬라이드-타입" />
<span id="canvas-vs-html-선택-기준-v123" />
<span id="html-architecture-패턴-박스-5-필수" />
<span id="키보드-단축키" />
<span id="출력물" />
<span id="협업-워크플로우" />


# 인터랙티브 프레젠테이션 에이전트

Remarp 소스를 작성하고 인터랙티브 HTML 슬라이드를 빌드한 뒤 브라우저에서 검증합니다. 콘텐츠, 코드, 비교, 탭, 퀴즈, 타임라인, 체크리스트와 단순 Canvas 슬라이드를 지원합니다.

## 작업 흐름 {#workflow}

발표 흐름과 블록을 계획하고 필요하면 제공된 PPTX의 테마를 추출합니다. 발표자 노트를 포함한
소스를 작성하고 사용자의 콘텐츠 승인을 받은 뒤 검증하고 빌드합니다. 탐색과 상호작용을
테스트하고 게시 전에 콘텐츠 리뷰를 수행합니다. 그룹이나 분기가 있는 아키텍처와
인터랙티브 계산기에는 HTML/CSS를 사용하며, Canvas는 작은 선형 흐름에만 사용합니다.

## 결과물과 검증 {#output-and-verification}

편집 가능한 소스, 렌더링 결과, 관련 빌드 명령과 검증 근거를 제공합니다. 완료나 게시 전에 콘텐츠 리뷰 게이트를 통과해야 합니다. 파일을 저장했다는 사실만으로 리뷰를 통과한 것은 아닙니다.

[에이전트 명세](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/reactive-presentation-agent.md) · [스킬 가이드](/docs/aws-content-plugin/skills/reactive-presentation)
