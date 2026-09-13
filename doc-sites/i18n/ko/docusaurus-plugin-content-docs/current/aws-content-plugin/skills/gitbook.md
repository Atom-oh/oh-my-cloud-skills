---
sidebar_position: 4
title: "GitBook 스킬"
---

# GitBook 스킬

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="trigger-keywords" />
<span id="use-cases" />
<span id="provided-resources" />
<span id="references" />
<span id="project-structure" />
<span id="component-patterns-detail" />
<span id="hints-callouts" />
<span id="tabs" />
<span id="code-blocks" />
<span id="basic-code-block" />
<span id="code-with-title-and-line-numbers" />
<span id="supported-languages-40" />
<span id="expandable-sections" />
<span id="embedded-content" />
<span id="file-download" />
<span id="video-embed" />
<span id="external-page-embed" />
<span id="images-with-caption" />
<span id="sized-image" />
<span id="summarymd-writing-guide" />
<span id="basic-structure" />
<span id="syntax-rules" />
<span id="multi-level-hierarchy-example" />
<span id="best-practices" />
<span id="multi-language-setup" />
<span id="directory-structure-for-koreanenglish" />
<span id="gitbookyaml-for-multi-language" />
<span id="content-parity-rules" />
<span id="diagram-integration" />
<span id="drawio-png" />
<span id="animated-svg-iframe" />
<span id="mermaid-inline" />
<span id="korean-heading-anchors" />
<span id="quick-start-commands" />
<span id="usage-example" />
<span id="quality-review-required" />

탐색하기 쉬운 주제별 페이지와 다양한 GitBook 구성 요소로 체계적인 문서 사이트를 만듭니다.

## 구조 {#structure}

시작 페이지에는 README.md, 탐색에는 SUMMARY.md, 소스 설정에는 .gitbook.yaml을 사용하고 실제 페이지는 주제별 디렉터리에 둡니다. 탐색 계층은 빠르게 살펴볼 수 있도록 얕게 유지하며 목록의 모든 경로가 존재하는지 확인합니다.

## 구성 요소 {#components}

경고·팁에는 힌트, 대안에는 탭, 명령·파일에는 제목이 있는 코드 블록, 상세 설명에는 펼침 섹션을 사용합니다. 이미지에는 유용한 캡션과 대체 텍스트를 제공합니다. 다운로드, 동영상과 외부 임베드의 대상 경로는 유효해야 합니다. 출력 형식에 맞춰 정적 Draw.io 내보내기 결과, 지원되는 애니메이션 임베드나 Mermaid 다이어그램을 통합합니다.

## 언어와 앵커 {#language-and-anchors}

사용자가 요청한 언어를 사용합니다. 다국어 사이트를 만들 때는 언어별 루트를 명시하고 탐색 구조와 내용을 일치시킵니다. 이름을 변경할 때도 게시된 앵커는 유지합니다. 정확한 문법이나 과거 예제 텍스트는 영문 설명을 덧붙인 인용문으로 유지할 수 있습니다.

## 검증 {#validate}

SUMMARY.md, 상대 경로, 구성 요소 문법, 이미지 참조와 상호 링크를 확인합니다. 사이트를 빌드하고 주요 페이지를 확인한 뒤 콘텐츠 리뷰와 승인된 게시를 진행합니다.


[스킬, 리소스와 품질 요구 사항](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/gitbook/SKILL.md)
