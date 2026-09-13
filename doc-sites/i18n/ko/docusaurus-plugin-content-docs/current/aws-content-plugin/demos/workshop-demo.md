---
sidebar_position: 8
title: "워크숍 예제"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="workshop-demo" />
<span id="생성-프롬프트" />
<span id="생성된-프로젝트-구조" />
<span id="contentspecyaml" />
<span id="homepage-indexenmd" />
<span id="module-overview" />
<span id="module-1-environment-setup-30-min" />
<span id="module-2-create-eks-cluster-45-min" />
<span id="module-3-deploy-application-45-min" />
<span id="module-4-monitoring-45-min" />
<span id="technologies-youll-master" />
<span id="prerequisites" />
<span id="time-required" />
<span id="prerequisites-check" />
<span id="check-eksctl-version" />
<span id="check-kubectl-version" />
<span id="verify-aws-credentials" />
<span id="key-takeaways" />
<span id="iam-policy-staticiam-policyjson" />
<span id="workshop-directive-사용-예시" />
<span id="alert-types" />
<span id="code-with-copy-button" />
<span id="tabs-for-multi-option-content" />
<span id="주요-포인트" />


# 워크숍 예제

홈페이지, 순서가 지정된 모듈, 실습 페이지, 인프라 에셋과 학습자 확인 지점으로 구성된 EKS Workshop Studio 프로젝트를 설명합니다.

## 프로젝트 구조 {#project-shape}

프로젝트 루트에는 `contentspec.yaml`을, 모듈·실습 디렉터리에는 콘텐츠 페이지를, 정적 에셋에는 재사용할 이미지·템플릿을 둡니다. 홈페이지와 모듈 페이지는 목표와 사전 요구 사항을 설명합니다. 실습 페이지는 명령, 예상 결과, 검증과 정리 절차를 제공합니다.

## 콘텐츠 기능 {#content-features}

주의 사항에는 Workshop Studio 알림을, 명령에는 복사 가능한 코드 블록을, 실제 대안에는 탭을 사용합니다. 프런트매터로 제목과 순서를 지정합니다. 요청된 언어만 작성하며, 현지화된 입력·출력 예제는 고정 결과물로 유지할 수 있습니다.

## 인프라 검토 {#infrastructure-review}

인프라와 IAM은 실습에 맞게 구성합니다. 템플릿을 검증하고 권한 범위를 제한하며 퍼블릭 액세스를 통제하고 학습자가 생성하는 모든 리소스를 명시합니다. 과거 예제 템플릿을 현재 프로덕션 배포의 권장 사항으로 간주하지 않습니다.

현재 [워크숍 스킬](/docs/aws-content-plugin/skills/workshop-creator)에서 새 워크숍에 사용하는 디렉터리, 지시문, contentspec, 이벤트 매개변수와 인프라 참고 문서를 확인합니다.
