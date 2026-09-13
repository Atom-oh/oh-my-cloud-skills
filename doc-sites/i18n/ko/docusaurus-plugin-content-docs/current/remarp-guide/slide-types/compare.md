---
sidebar_position: 2
title: "비교 슬라이드"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="compare-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="자동-감지" />
<span id="예제" />
<span id="서비스-비교" />
<span id="아키텍처-패턴-비교" />
<span id="two-column과-함께-사용" />
<span id="렌더링" />
<span id="키보드-조작" />
<span id="팁" />


# 비교 슬라이드

선택 가능한 콘텐츠로 둘 이상의 대안을 비교합니다.

## 소스 {#source}

```markdown
---
@type: compare

## Build choices

### Local
Fast iteration with the current checkout.

### CI
Repeatable checks in the configured workflow.
```

## 렌더링과 상호작용 {#rendering-and-interaction}

3단계 제목으로 대안을 구분합니다. 파서는 반복되는 제목에서 비교 형식을 추론할 수 있지만, 탭이나 타임라인과 구분하려면 유형을 명시합니다. 선택 버튼과 Up/Down 순환을 테스트합니다. Left/Right는 일반 탐색을 계속 수행합니다. 대안 간에 동일한 비교 기준을 적용합니다.

빌드 전에 발표자 노트를 추가하고 소스를 검증합니다. 생성된 덱에서 슬라이드를 테스트합니다. HTML 구조와 CSS 클래스는 구현 세부 사항이며 동작 확인을 대신할 수 없습니다.

[지시문](../syntax/directives.md), [발표자 노트](../syntax/speaker-notes.md), [키보드 조작](../keyboard-shortcuts.md)을 참고합니다.
