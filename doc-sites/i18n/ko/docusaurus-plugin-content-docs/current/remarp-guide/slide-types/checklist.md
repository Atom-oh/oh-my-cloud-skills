---
sidebar_position: 7
title: "체크리스트 슬라이드"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="checklist-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="문법" />
<span id="예제" />
<span id="배포-전-체크리스트" />
<span id="환경-설정-체크리스트" />
<span id="yaml-피드백이-있는-체크리스트" />
<span id="yaml-피드백이-있는-경우" />
<span id="인터랙션" />
<span id="팁" />


# 체크리스트 슬라이드

퀴즈 채점 없이 완료 상태를 확인합니다.

## 소스 {#source}

```markdown
---
@type: checklist

## Review checklist

- [ ] Source reviewed
- [ ] Relevant checks passed
- [ ] Links verified
- [ ] Remaining limits recorded
```

## 렌더링과 상호작용 {#rendering-and-interaction}

체크박스가 퀴즈로 추론되지 않도록 `@type: checklist`를 사용합니다. 클릭하면 항목 상태와 checked 클래스가 전환됩니다. 지원되는 중첩 코드 피드백으로 설정 예제를 표시할 수 있습니다. 컴파일 결과를 확인하고 예제를 해당 항목의 범위로 제한합니다. 긴 체크리스트는 의미 있는 그룹으로 나눕니다.

빌드 전에 발표자 노트를 추가하고 소스를 검증합니다. 생성된 덱에서 슬라이드를 테스트합니다. HTML 구조와 CSS 클래스는 구현 세부 사항이며 동작 확인을 대신할 수 없습니다.

[지시문](../syntax/directives.md), [발표자 노트](../syntax/speaker-notes.md), [키보드 조작](../keyboard-shortcuts.md)을 참고합니다.
