---
sidebar_position: 4
title: "퀴즈 슬라이드"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="quiz-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="자동-감지" />
<span id="문법" />
<span id="예제" />
<span id="단일-정답-퀴즈" />
<span id="복수-정답-퀴즈" />
<span id="설명이-포함된-퀴즈" />
<span id="렌더링" />
<span id="인터랙션" />
<span id="팁" />


# 퀴즈 슬라이드

핵심 지식을 묻는 질문을 제시하고 선택지를 고르면 피드백을 제공합니다.

## 소스 {#source}

```markdown
---
@type: quiz

## Source of truth

**Which file defines this site's locale configuration?**
- [ ] A screenshot
- [x] docusaurus.config.ts
- [ ] A release announcement
```

## 렌더링과 상호작용 {#rendering-and-interaction}

`[x]`는 정답을, `[ ]`는 오답 선택지를 표시합니다. 체크박스 콘텐츠는 퀴즈로 추론될 수 있으므로 완료 상태를 확인하려면 checklist를 명시합니다. 선택지는 간결하게 작성하고 정답을 설명합니다. 실제 선택·피드백 동작을 테스트합니다. 정답 표시가 여러 개 있다는 사실만으로 다중 선택 완료 규칙이 정해지지는 않습니다.

빌드 전에 발표자 노트를 추가하고 소스를 검증합니다. 생성된 덱에서 슬라이드를 테스트합니다. HTML 구조와 CSS 클래스는 구현 세부 사항이며 동작 확인을 대신할 수 없습니다.

[지시문](../syntax/directives.md), [발표자 노트](../syntax/speaker-notes.md), [키보드 조작](../keyboard-shortcuts.md)을 참고합니다.
