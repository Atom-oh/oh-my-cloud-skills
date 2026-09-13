---
sidebar_position: 5
title: "탭 슬라이드"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="tabs-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="구조" />
<span id="예제" />
<span id="언어별-코드-예제" />
<span id="배포-옵션" />
<span id="sam" />
<span id="cdk" />
<span id="cloudformation" />
<span id="pulumi" />


# 탭 슬라이드

대안별 코드, 설정이나 설명을 선택 가능한 탭으로 묶습니다.

## 소스 {#source}

```markdown
---
@type: tabs

## Validation modes

### Source
Inspect syntax and configuration before building.

### Browser
Check rendered content, controls, and navigation.
```

## 렌더링과 상호작용 {#rendering-and-interaction}

각 3단계 제목은 탭 레이블이 되고 뒤따르는 콘텐츠는 패널이 됩니다. `@type: tabs`를 명시하고 레이블을 짧게 유지하며 탭 버튼과 Up/Down 순환을 모두 테스트합니다. 코드 블록을 중첩해 설명하는 예제에서는 바깥쪽 Markdown 구분자의 길이를 더 길게 지정합니다.

빌드 전에 발표자 노트를 추가하고 소스를 검증합니다. 생성된 덱에서 슬라이드를 테스트합니다. HTML 구조와 CSS 클래스는 구현 세부 사항이며 동작 확인을 대신할 수 없습니다.

[지시문](../syntax/directives.md), [발표자 노트](../syntax/speaker-notes.md), [키보드 조작](../keyboard-shortcuts.md)을 참고합니다.
