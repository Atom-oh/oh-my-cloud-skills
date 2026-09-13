---
sidebar_position: 1
title: "프레젠테이션 요청 분류 에이전트"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="presentation-agent-dispatcher" />
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="라우팅-로직" />
<span id="키워드-분류" />
<span id="webinteractive-즉시-위임" />
<span id="pptx-pptx-경로" />
<span id="포맷-선택-질문" />
<span id="reactive-presentation-agent와의-관계" />


# 프레젠테이션 요청 분류 에이전트

프레젠테이션 요청을 인터랙티브 웹 슬라이드 또는 편집 가능한 PowerPoint로 분류합니다. 웹·인터랙티브 형식이 명시된 요청은 reactive-presentation으로, 기본 개체를 편집할 수 있는 AWS 라이트 테마 덱은 aws-light-fcd로 처리합니다. 요청 형식이 불명확하면 제작 전에 결과물의 형식을 확정합니다.

## 작업 흐름 {#workflow}

대상 독자, 발표 시간, 기술 수준, 언어, 출력 형식과 참고 템플릿을 확인합니다. 웹 덱은 상호작용을 유지하며 슬라이드 이미지로 내보낼 수 있습니다. 기본 PowerPoint 형식은 PptxGenJS와 편집 가능한 개체를 사용합니다.

## 결과물과 검증 {#output-and-verification}

편집 가능한 소스, 렌더링 결과, 관련 빌드 명령과 검증 근거를 제공합니다. 완료나 게시 전에 콘텐츠 리뷰 게이트를 통과해야 합니다. 파일을 저장했다는 사실만으로 리뷰를 통과한 것은 아닙니다.

[에이전트 명세](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/presentation-agent.md) · [스킬 가이드](/docs/aws-content-plugin/skills/reactive-presentation)

## 관련 링크 {#related-links}

- [인터랙티브 프레젠테이션 에이전트](./reactive-presentation-agent)
