---
sidebar_position: 4
title: "레이아웃"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="레이아웃" />
<span id="two-column-레이아웃" />
<span id="three-column-레이아웃" />
<span id="grid-2x2-레이아웃" />
<span id="split-레이아웃" />
<span id="split-left-왼쪽-콘텐츠" />
<span id="split-right-오른쪽-콘텐츠" />
<span id="레이아웃-선택-가이드" />
<span id="레이아웃과-프래그먼트-조합" />
<span id="중첩된-구조" />
<span id="json-format" />


# 레이아웃

슬라이드 콘텐츠 앞에 `@layout`을 지정하고 해당 블록 컨테이너를 사용합니다.

```markdown
---
@layout: two-column

## Review and verify

:::left
### Review
- Inspect changed behavior {.click order=1}
- Check source evidence {.click order=2}
:::

:::right
### Verify
- Run relevant checks {.click order=3}
- Record limits {.click order=4}
:::
```

## 레이아웃 선택 {#layout-choices}

| 레이아웃 | 컨테이너 | 용도 |
| --- | --- | --- |
| 기본 | 일반 Markdown | 하나의 메시지나 핵심 목록 |
| `two-column` | `:::left`, `:::right` | 서로 대응하는 개념 또는 코드·설명 |
| `three-column` | `:::col` 블록 세 개 | 비교 가능한 기능이나 단계 |
| `grid-2x2` | `:::cell` 블록 네 개 | 서로 관련된 네 범주 |
| `split-left` | 배경 영역과 왼쪽 콘텐츠 | 시각 자료 옆의 텍스트 |
| `split-right` | 배경 영역과 오른쪽 콘텐츠 | 텍스트 옆의 시각 자료 |

여러 열에 걸친 표시 순서를 명시합니다. 중첩 블록은 파서가 처리할 수 있도록 단순하게 유지하고 생성 결과를 확인합니다. 복잡한 카드나 그룹 다이어그램에는 프레임워크의 레이아웃 클래스와 함께 `:::html` 및 `:::css`를 사용합니다.
