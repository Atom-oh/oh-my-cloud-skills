---
sidebar_position: 6
title: "타임라인 슬라이드"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="timeline-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="구조" />
<span id="예제" />
<span id="프로젝트-로드맵" />
<span id="서비스-진화" />
<span id="릴리스-일정" />
<span id="렌더링" />
<span id="스타일-클래스" />
<span id="팁" />


# 타임라인 슬라이드

단계, 마일스톤이나 출시 과정을 순서대로 보여 줍니다.

## 소스 {#source}

```markdown
---
@type: timeline

## Documentation update

### Audit
Compare instructions with actual source.

### Edit
Correct stale claims and examples.

### Verify
Build, check links, and review the result.
```

## 렌더링과 상호작용 {#rendering-and-interaction}

3단계 제목으로 타임라인 지점을 정의합니다. 설명은 짧게 유지하고 세부 내용은 별도 슬라이드에 둡니다. 렌더링 클래스에는 timeline-step, timeline-dot, timeline-connector와 렌더러가 할당한 active/done 상태가 포함됩니다. 타임라인의 날짜는 작성된 콘텐츠이며 기능 출시의 근거가 아닙니다.

빌드 전에 발표자 노트를 추가하고 소스를 검증합니다. 생성된 덱에서 슬라이드를 테스트합니다. HTML 구조와 CSS 클래스는 구현 세부 사항이며 동작 확인을 대신할 수 없습니다.

[지시문](../syntax/directives.md), [발표자 노트](../syntax/speaker-notes.md), [키보드 조작](../keyboard-shortcuts.md)을 참고합니다.
