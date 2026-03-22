# Workshop Studio Front Matter Reference

모든 Workshop Studio 콘텐츠 페이지의 Front Matter 설정 레퍼런스입니다.

---

## 페이지 구조

모든 콘텐츠 페이지는 두 부분으로 구성됩니다:

1. **Front Matter** (메타데이터) - 페이지 상단
2. **Markdown Content** (실제 내용) - Front Matter 아래

---

## Front Matter 문법

Front Matter는 **필수**이며, 파일 최상단에 `---`로 구분하여 작성합니다.

```markdown
---
title: "페이지 제목"
weight: 10
---

여기부터 마크다운 내용을 작성합니다.
```

---

## 지원되는 속성

| 속성 | 타입 | 설명 | 필수 | 기본값 |
|------|------|------|------|--------|
| `title` | `string` | 페이지 제목. 네비게이션 링크 텍스트로 사용됩니다. | **필수** | - |
| `weight` | `number` | 네비게이션에서의 정렬 순서. 낮은 값이 먼저 표시됩니다. | 선택 | - |
| `hidden` | `boolean` | `true`면 네비게이션에 표시되지 않습니다. | 선택 | `false` |

---

## 주의사항

1. **title은 필수입니다** - title이 없으면 빌드가 실패합니다.
2. **title은 따옴표로 감싸야 합니다** - `title: "제목"` 형식 사용
3. **잘못된 속성/값은 빌드 실패 원인** - 지원되는 속성만 사용하세요.

---

## 예제

### 기본 페이지

```yaml
---
title: "소개"
weight: 10
---
```

### 숨겨진 페이지

네비게이션에 표시되지 않지만 직접 링크로 접근 가능합니다.

```yaml
---
title: "부록 A - 참고 자료"
weight: 999
hidden: true
---
```

### 정렬 예제

같은 레벨의 페이지들:

```yaml
# 010_introduction/index.ko.md
---
title: "소개"
weight: 10
---

# 020_setup/index.ko.md
---
title: "사전 준비"
weight: 20
---

# 030_module1/index.ko.md
---
title: "모듈 1: 기본 설정"
weight: 30
---
```

### 같은 weight 처리

같은 weight를 가진 페이지들은 **사전순(lexicographic order)**으로 정렬됩니다.

```yaml
# 두 페이지가 weight: 10을 가지면
# 디렉토리/파일명의 알파벳순으로 정렬됨
```

---

## 워크샵 구조별 권장 weight

| 섹션 | weight 범위 | 예시 |
|------|-------------|------|
| Introduction | 1-9 | 1, 5 |
| Prerequisites | 10-19 | 10 |
| Module 1 | 20-29 | 20 |
| Module 2 | 30-39 | 30 |
| Module 3 | 40-49 | 40 |
| Cleanup | 90-99 | 90 |
| Appendix | 100+ | 100, hidden: true |

---

## 다국어 페이지

한국어와 영어 페이지는 같은 weight를 사용합니다:

```yaml
# index.ko.md
---
title: "소개"
weight: 10
---

# index.en.md
---
title: "Introduction"
weight: 10
---
```

---

## 흔한 실수

### 잘못된 예시

```yaml
# title 누락 - 빌드 실패
---
weight: 10
---

# 따옴표 누락 - 특수문자 포함 시 오류
---
title: Module 1: Setup
weight: 10
---

# 잘못된 속성
---
title: "제목"
author: "홍길동"  # 지원되지 않는 속성
---
```

### 올바른 예시

```yaml
---
title: "Module 1: Setup"
weight: 10
---
```
