---
sidebar_position: 2
title: "콘텐츠 제작"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="사용법-가이드" />
<span id="빠른-시작" />
<span id="에이전트-자동-호출" />
<span id="프레젠테이션-만들기" />
<span id="프롬프트-예시" />
<span id="에이전트-질문-항목" />
<span id="워크플로우" />
<span id="pptx-테마-적용" />
<span id="remarp-포맷" />
<span id="파일-구조" />
<span id="핵심-문법" />
<span id="frontmatter" />
<span id="빌드" />
<span id="아키텍처-다이어그램" />
<span id="애니메이션-다이어그램" />
<span id="문서-생성" />
<span id="gitbook--workshop" />
<span id="gitbook-문서-사이트" />
<span id="aws-workshop-studio" />
<span id="프로필-페이지-만들기-gh-home" />
<span id="준비물" />
<span id="프롬프트-예시-1" />
<span id="워크플로우-1" />
<span id="quality-gate" />
<span id="키보드-단축키" />
<span id="팁--트릭" />
<span id="블록-편집" />
<span id="증분-빌드" />
<span id="한국어영어-혼용-규칙" />
<span id="다이어그램-에이전트-선택" />
<span id="canvas-vs-html-선택-기준-v123" />


# 콘텐츠 제작

## 결과물부터 정의하기 {#start-from-the-deliverable}

대상 독자, 기술 수준, 언어, 발표 시간이나 페이지 범위, 출력 형식과 원본 자료를 명시합니다. 예를 들어 “발표자 노트, 간단한 트래픽 애니메이션과 복습 문제를 포함한 30분 분량의 영어 EKS 운영 웹 덱을 만들어 주세요”라고 요청합니다. 편집 가능한 PowerPoint가 필요하면 네이티브 AWS 라이트 작업 흐름을 명시합니다.

## 프레젠테이션 {#presentations}

웹 작업 흐름은 블록 계획, 선택적 PPTX 테마 추출, Remarp 작성, 소스 검증, HTML 빌드와 상호작용 테스트 순서로 진행합니다. 여러 파일로 된 덱은 `_presentation.md`와 번호순 블록 파일을 사용합니다. 편집의 기준은 소스이며, 필요한 경우 변경된 블록만 동기화합니다. 프로젝트와 목차를 영어로 출력하려면 `_presentation.md`에 `lang: en`을 지정하고 블록별 언어 재정의도 일치시킵니다. `--lang`은 단일 파일 빌드에만 적용됩니다. 전역 메타데이터 변경 후와 게시 전에는 전체 빌드를 실행합니다. `sync`는 변경된 블록 페이지만 갱신하며 병합 덱이나 공유 에셋은 갱신하지 않습니다.

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py sync ./my-presentation/
```

네이티브 PowerPoint는 aws-light-fcd 에셋과 PptxGenJS로 제작한 뒤 글꼴을 포함하고 덱을 확인합니다. 웹 덱의 PPTX 내보내기는 스크린샷 기반 슬라이드를 만들며, 애니메이션 HTML 개체를 편집 가능하게 변환하지는 않습니다.

## 다이어그램 {#diagrams}

지원되는 AWS 패턴에는 Draw.io 레이아웃 생성기를 사용합니다. 내보내기 전에 XML과 레이아웃을 검증하고 크기·색상 규칙은 기준 토큰 파일을 따릅니다. 반복되는 트래픽은 SVG 애니메이션으로, 시나리오 제어는 JavaScript/CSS로 구현합니다. 슬라이드의 Canvas는 상자·아이콘이 최대 네 개인 단순 선형 흐름에 사용합니다. 그룹, 분기나 더 큰 아키텍처에는 HTML/CSS를 사용합니다.

## 문서, 사이트와 워크숍 {#documents-sites-and-workshops}

문서 에이전트는 보고서와 비교 문서를 작성합니다. GitBook은 여러 페이지의 탐색 구조와 다양한 문서 구성 요소를 제공합니다. Workshop Creator는 Workshop Studio 구조, 지시문, 실습 검증과 정리를 지원합니다. Brochure는 제품·솔루션 소개 페이지를, gh-home은 경력, 기술과 대표 작업을 담은 개인 프로필을 만듭니다. 프로필을 갱신할 때는 기존 `index.html`을 덮어쓰기 전에 확인하고, 관련 없는 CNAME, robots.txt와 분석 파일은 보존합니다.

## 수정과 리뷰 {#revision-and-review}

Remarp 소스를 편집하거나 편집기에서 `<!-- issue: ... -->` 주석을 추가한 뒤 slide-fix를 실행하고 다시 빌드합니다. 키보드 탐색, 단계별 표시, Canvas 단계, 퀴즈, 탭과 반응형 레이아웃을 확인합니다. 승인된 게시 전에 콘텐츠 리뷰 게이트를 적용합니다. 설명은 요청된 언어로 작성하고 정확한 서비스명, 문법, 경로와 식별자를 보존합니다.

[Remarp 문법](/docs/remarp-guide/introduction) · [키보드 조작](/docs/remarp-guide/keyboard-shortcuts) · [콘텐츠 리뷰](/docs/aws-content-plugin/agents/content-review-agent)
