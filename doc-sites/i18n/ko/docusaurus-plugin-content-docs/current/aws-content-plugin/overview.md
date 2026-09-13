---
sidebar_position: 1
title: "AWS 콘텐츠 플러그인"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="aws-content-plugin-개요" />
<span id="구성-요소" />
<span id="에이전트-9개" />
<span id="스킬-9개" />
<span id="워크플로우" />
<span id="프레젠테이션-워크플로우" />
<span id="다이어그램-워크플로우" />
<span id="애니메이션-다이어그램-워크플로우" />
<span id="문서-워크플로우" />
<span id="gitbook-워크플로우" />
<span id="workshop-워크플로우" />
<span id="quality-gate-필수" />
<span id="판정-기준" />
<span id="리뷰-루프" />
<span id="다이어그램-에이전트-선택-가이드" />
<span id="aws-아이콘" />


# AWS 콘텐츠 플러그인

웹 프레젠테이션, 편집 가능한 PowerPoint 덱, 다이어그램, 문서, 워크숍, 브로슈어와 포트폴리오 페이지를 제작합니다.

## 작업 흐름 선택 {#choose-a-workflow}

| 결과물 | 스킬 또는 에이전트 |
| --- | --- |
| 인터랙티브 HTML 슬라이드 | reactive-presentation |
| 기본 개체를 편집할 수 있는 AWS 라이트 PowerPoint | aws-light-fcd |
| AWS Draw.io 아키텍처 | architecture-diagram |
| 트래픽·시나리오 애니메이션 다이어그램 | animated-diagram |
| 기술 보고서·비교 문서 | document-agent |
| GitBook 문서 | gitbook |
| Workshop Studio 실습 | workshop-creator |
| 제품·솔루션 소개 페이지 | brochure |
| 개인 프로필·포트폴리오 | gh-home |
| Remarp 이슈 주석 반영 | slide-fix |

프레젠테이션 요청 분류 에이전트는 요청 형식에 따라 웹 또는 기본 PowerPoint 제작 경로를 선택합니다. 정적 다이어그램에는 Draw.io를, 웹 슬라이드의 복잡한 아키텍처에는 HTML/CSS를 사용합니다. 작은 선형 흐름에는 Canvas를 사용할 수 있습니다. 외부 Archify 결과물을 삽입할 수 있지만, Archify가 마켓플레이스에 추가로 포함된 플러그인은 아닙니다.

## 빌드와 리뷰 {#build-and-review}

대상 독자와 발표 흐름을 계획하고 편집 가능한 소스를 작성합니다. 형식을 검증하고 빌드하거나 내보낸 뒤 결과를 확인하고 content-review-agent를 실행합니다. 게시 전에 품질 게이트에서 PASS를 받아야 합니다. 다이어그램 내보내기는 XML이 유효하고 레이아웃 점수가 80 이상이어야 합니다.

## 공유 에셋 {#shared-assets}

제공된 아이콘 라이브러리와 기준 다이어그램 토큰을 사용합니다. 기본 PowerPoint의 `kit.icon()`은 같은 플러그인의 reactive-presentation 라이브러리를 참조하므로 복제하지 않습니다. 에셋 수와 현재 템플릿은 소스 디렉터리에서 확인합니다.

[Claude 구성 요소 매니페스트](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/.claude-plugin/plugin.json) · [Codex 패키지](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/.codex-plugin/plugin.json) · [다이어그램 토큰](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/architecture-diagram/references/design-tokens.md)
