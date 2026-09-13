---
sidebar_position: 3
title: "애니메이션 다이어그램 에이전트"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="아키텍처-패턴" />
<span id="색상-코딩-표준" />
<span id="워크플로우" />
<span id="step-1-requirements-analysis" />
<span id="step-2-static-background" />
<span id="step-3-animation-layer" />
<span id="step-4-interactive-legend" />
<span id="애니메이션-타이밍-가이드라인" />
<span id="interactive-animation-pattern" />
<span id="시나리오-템플릿" />
<span id="출력물" />
<span id="사용-예시" />
<span id="협업-워크플로우" />


# 애니메이션 다이어그램 에이전트

아키텍처 다이어그램에 트래픽 흐름, 확장, 배포와 장애 조치 동작을 시각화합니다. 반복되는 SVG 움직임에는 SMIL을, 제어 기능·시나리오 전환·리소스 수명 주기 시뮬레이션에는 JavaScript/CSS 상태 머신을 사용합니다.

## 작업 흐름 {#workflow}

먼저 읽기 쉬운 정적 아키텍처를 구성한 뒤 움직임, 범례, 레이블과 제어 기능을 추가합니다. 의미별 색상을 일관되게 유지하고, 이벤트 순서가 드러나도록 시간차를 두며, 초기화와 재생 동작을 검증합니다. 정지 화면과 애니메이션 결과를 모두 검토합니다.

## 결과물과 검증 {#output-and-verification}

편집 가능한 소스, 렌더링 결과, 관련 빌드 명령과 검증 근거를 제공합니다. 완료나 게시 전에 콘텐츠 리뷰 게이트를 통과해야 합니다. 파일을 저장했다는 사실만으로 리뷰를 통과한 것은 아닙니다.

[에이전트 명세](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/animated-diagram-agent.md) · [스킬 가이드](/docs/aws-content-plugin/skills/animated-diagram)
