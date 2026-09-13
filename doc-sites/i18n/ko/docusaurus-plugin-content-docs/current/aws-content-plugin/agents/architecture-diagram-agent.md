---
sidebar_position: 2
title: "아키텍처 다이어그램 에이전트"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="캔버스-크기" />
<span id="aws-그룹-박스-스타일" />
<span id="aws-cloud" />
<span id="region" />
<span id="vpc" />
<span id="aws-아이콘-카테고리-색상" />
<span id="parent-계층-규칙" />
<span id="워크플로우" />
<span id="아이콘-그리드-배치" />
<span id="출력물" />
<span id="사용-예시" />
<span id="협업-워크플로우" />


# 아키텍처 다이어그램 에이전트

YAML 레이아웃 생성기로 AWS Draw.io 다이어그램을 만들고, 지원하지 않는 구조는 XML을 직접 작성합니다. 편집 가능한 .drawio 파일과 검토를 마친 PNG 또는 SVG 내보내기 결과를 제공합니다.

## 작업 흐름 {#workflow}

아이콘 크기, 서브넷 색상, 글꼴과 간격에는 기준 디자인 토큰을 사용합니다. 정점의 부모 계층은 Cloud → Region → VPC → Subnet → service를 따르고, 연결선은 parent="1" 아래에 둡니다. XML과 셀 수를 검증하고 레이아웃 점수 80 이상을 확인한 뒤 내보냅니다. 렌더링 결과에 잘림이나 겹침이 없는지 확인합니다.

## 결과물과 검증 {#output-and-verification}

편집 가능한 소스, 렌더링 결과, 관련 빌드 명령과 검증 근거를 제공합니다. 완료나 게시 전에 콘텐츠 리뷰 게이트를 통과해야 합니다. 파일을 저장했다는 사실만으로 리뷰를 통과한 것은 아닙니다.

[에이전트 명세](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/architecture-diagram-agent.md) · [스킬 가이드](/docs/aws-content-plugin/skills/architecture-diagram)

[기준 다이어그램 토큰](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/references/design-tokens.md)
