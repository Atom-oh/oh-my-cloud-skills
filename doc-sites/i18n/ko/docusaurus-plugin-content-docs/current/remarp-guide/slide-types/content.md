---
sidebar_position: 1
title: "콘텐츠 슬라이드"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="content-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="예제" />
<span id="기본-콘텐츠" />
<span id="프래그먼트가-있는-콘텐츠" />
<span id="2단-레이아웃" />
<span id="배경과-타이밍" />
<span id="렌더링" />
<span id="팁" />


# 콘텐츠 슬라이드

핵심 문장, 목록, 표, 코드 발췌나 이미지를 보여 줄 때 사용합니다.

## 소스 {#source}

```markdown
---
@type: content
@timing: 2min

## Verify the change

- Read the affected path {.click order=1}
- Exercise the behavior {.click order=2}
- Report the result {.click order=3}
```

## 렌더링과 상호작용 {#rendering-and-interaction}

기본 레이아웃은 하나의 콘텐츠 영역입니다. 비교가 도움이 되면 열 레이아웃 블록을 추가하고 필요에 따라 배경·시간 지시문을 사용합니다. 핵심 메시지는 하나로 유지하며, 읽기 쉬운 계층과 실무적 의미를 설명하는 노트를 제공합니다.

빌드 전에 발표자 노트를 추가하고 소스를 검증합니다. 생성된 덱에서 슬라이드를 테스트합니다. HTML 구조와 CSS 클래스는 구현 세부 사항이며 동작 확인을 대신할 수 없습니다.

[지시문](../syntax/directives.md), [발표자 노트](../syntax/speaker-notes.md), [키보드 조작](../keyboard-shortcuts.md)을 참고합니다.
