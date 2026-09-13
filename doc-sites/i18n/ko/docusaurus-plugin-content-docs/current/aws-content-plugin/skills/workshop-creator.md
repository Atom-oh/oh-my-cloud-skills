---
sidebar_position: 5
title: "워크숍 제작 스킬"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="trigger-keywords" />
<span id="commands" />
<span id="provided-resources" />
<span id="references" />
<span id="directory-structure" />
<span id="workshop-studio-directives-detail" />
<span id="alert-directive" />
<span id="leaf-syntax-simple-messages" />
<span id="container-syntax-complex-content" />
<span id="code-directive" />
<span id="code-properties" />
<span id="supported-languages-40" />
<span id="tabs-directive" />
<span id="image-directive" />
<span id="expand-directive" />
<span id="mermaid-diagrams" />
<span id="contentspecyaml-guide" />
<span id="basic-configuration" />
<span id="full-configuration-options" />
<span id="magic-variables" />
<span id="cloudformation-infrastructure-patterns" />
<span id="vpc--eks-pattern" />
<span id="serverless-pattern" />
<span id="best-practices" />
<span id="event-params--central-account" />
<span id="workshop-templates" />
<span id="homepage-template" />
<span id="prerequisites" />
<span id="lab-content-template" />
<span id="front-matter" />
<span id="best-practices-1" />
<span id="do" />
<span id="dont" />
<span id="bilingual-content" />
<span id="usage-example" />
<span id="quality-review-required" />


# 워크숍 제작 스킬

모듈, 실습, 에셋과 선택적 인프라를 포함한 AWS Workshop Studio 콘텐츠와 프로젝트 구조를 만듭니다.

## 프로젝트 배치 {#project-layout}

프로젝트에는 contentspec.yaml, 모듈·실습별 콘텐츠 페이지, 다이어그램과 인프라 템플릿 같은 정적 에셋이 있습니다. 페이지에는 따옴표로 감싼 `title`이 필요하며, 선택적인 `weight`로 탐색 순서를 지정합니다. 다른 필드는 원본 [프런트매터 참고 문서](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/workshop-creator/references/front-matter.md)를 따릅니다. Hugo의 `chapter: true`나 단축 코드 문법은 사용하지 않습니다.

## 작성 {#authoring}

Workshop Studio의 alert, code, tabs, image, expand와 Mermaid 지시문을 사용합니다. 복사 가능한 명령, 예상 출력, 확인 지점, 문제 해결과 정리 절차를 제공합니다. 운영체제나 배포 방식처럼 실제 대안이 있는 경우 탭으로 보여 줍니다. 인프라는 실습 범위로 제한하고, 워크숍이 이벤트 매개변수나 중앙 계정 리소스를 사용하면 이를 문서화합니다.

## 인프라와 언어 {#infrastructure-and-language}

사용 전에 CloudFormation과 IAM을 검증하고 저장소의 AWS 보안 규칙을 따르며 비밀 정보를 포함하지 않습니다. 요청된 경우에는 언어별 페이지 쌍을 만들고, 그렇지 않으면 하나의 언어를 일관되게 사용합니다. 실습에서 생성하는 모든 리소스와 학습자가 이를 검증하거나 제거하는 방법을 설명합니다.

## 리뷰 {#review}

contentspec 경로, 페이지 순서, 지시문 문법, 파일·에셋, 사전 요구 사항과 실습 완료 기준을 확인합니다. 승인된 환경에서 문서의 절차를 테스트하고 게시 전에 콘텐츠 리뷰를 수행합니다.


[스킬, 리소스와 품질 요구 사항](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/workshop-creator/SKILL.md)
