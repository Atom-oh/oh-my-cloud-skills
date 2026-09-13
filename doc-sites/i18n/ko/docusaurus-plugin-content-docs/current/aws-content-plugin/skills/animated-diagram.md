---
sidebar_position: 3
title: "애니메이션 다이어그램 스킬"
---

# 애니메이션 다이어그램 스킬

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="trigger-keywords" />
<span id="use-cases" />
<span id="provided-resources" />
<span id="references" />
<span id="templates" />
<span id="architecture" />
<span id="color-standards" />
<span id="smil-animation-patterns" />
<span id="traffic-dots-animatemotion" />
<span id="pulsing-glow-effect" />
<span id="sequential-stagger" />
<span id="dashed-line-flow-animation" />
<span id="sequential-highlight-step-by-step" />
<span id="interactive-scenario-patterns" />
<span id="scaling-scenario-eksasg" />
<span id="bluegreen-deployment-scenario" />
<span id="failover-simulation-scenario" />
<span id="smil-vs-css-animation-comparison" />
<span id="when-to-use-smil" />
<span id="when-to-use-javascript--css" />
<span id="decision-guide" />
<span id="animation-timing-guidelines" />
<span id="interactive-legend" />
<span id="usage-example" />
<span id="output-usage" />
<span id="quality-review-required" />
<span id="validation-checklist" />
<span id="smil-animation" />
<span id="interactive-animation" />

SVG 애니메이션이나 인터랙티브 HTML로 요청 트래픽, 자동 확장, 블루/그린 배포, 장애 조치와 서비스 간 상호작용을 시각화합니다.

## 애니메이션 방식 선택 {#select-the-motion-model}

반복되는 흐름은 SMIL `animateMotion`, 투명도·발광, 점선 오프셋과 순차 강조로 표현합니다. 시작·일시 정지·초기화, 복제본 수 변경, 마이그레이션과 장애 복구에는 JavaScript 상태 머신과 CSS 전환을 사용합니다.

기본 아키텍처는 정지 이미지로도 이해할 수 있게 유지합니다. 일관된 의미별 색상, 범례, 안정적인 레이블과 움직임을 위한 충분한 간격을 사용합니다. 관련 이벤트의 순서를 명확히 정하고 시간 설정을 하나의 시나리오 모델에서 관리합니다.

## 검증 {#verify}

각 시나리오, 초기화와 재생을 실행하고 작은 화면에서도 확인합니다. 콘솔 오류와 애니메이션 겹침을 검사합니다. 대상 환경이 지원하면 SVG나 HTML로 삽입하고, 움직임을 지원하지 않으면 정적 내보내기 결과를 제공합니다.

스킬의 참고 문서와 템플릿에서 트래픽 점, 발광, 순차 강조, 확장, 배포와 장애 조치 패턴을 정의합니다.


게시 전에 해당 평가 기준에 따라 콘텐츠 리뷰를 통과해야 합니다.

[스킬, 리소스와 품질 요구 사항](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/animated-diagram/SKILL.md)
