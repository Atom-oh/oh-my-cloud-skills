---
sidebar_position: 7
title: "코드 블록"
---

{/* 영문 개편 전의 기존 섹션 링크를 유지합니다. */}
<span id="코드-블록" />
<span id="기본-코드-블록" />
<span id="파일명-표시" />
<span id="라인-하이라이팅" />
<span id="하이라이트-형식" />
<span id="속성-조합" />
<span id="diff-모드" />
<span id="지원되는-언어" />
<span id="구문-강조-클래스" />
<span id="예제-다양한-코드-블록" />
<span id="lambda-핸들러" />
<span id="kubernetes-설정" />
<span id="설정-변경-비교" />
<span id="코드-슬라이드-타입" />


# 코드 블록

코드 블록에 올바른 언어를 지정합니다. Remarp는 기술 슬라이드에 파일명 레이블과 줄 강조 표시용 마커를 출력합니다.

````markdown
```python {filename="review.py" highlight="2-3"}
def summarize(checks):
    passed = [check for check in checks if check["passed"]]
    return len(passed), len(checks)
```
````

## 속성과 강조 {#attributes-and-highlighting}

파일명으로 소스 파일을 식별합니다. 강조 설정은 개별 줄이나 범위를 선택합니다. 코드 자체에 발표용 마크업을 넣지 말고 지원되는 코드 블록 속성을 조합합니다. 발췌 코드는 읽을 수 있을 만큼 짧게 유지합니다. 집중해서 보여 줄 예제에는 코드 슬라이드를, 설명에는 발표자 노트를 사용합니다.

## Diff 블록 {#diff-blocks}

````markdown
```diff
- timeout = 5
+ timeout = 15
```
````

`diff` 코드 블록은 `-`와 `+`로 시작하는 줄을 그대로 유지하지만, 현재 Remarp 슬라이드 렌더러는 diff 전용 스타일을 제공하지 않습니다. 이 Docusaurus 가이드 페이지는 생성된 슬라이드와 별도로 렌더링됩니다. 변경 내용을 시각적으로 표시하려면 필요에 따라 HTML/CSS를 직접 작성하고 생성된 슬라이드를 확인합니다.

코드 블록에는 Python, JavaScript/TypeScript, YAML, JSON, Bash 또는 제공된 구문 강조기가 지원하는 언어를 사용할 수 있습니다. 구문 강조는 예제를 검증하거나 실행하지 않습니다.

## 렌더링 확인 {#rendering-checks}

넘침, 줄 바꿈, 강조 대비, 파일명 레이블과 선택된 슬라이드 유형을 확인합니다. 긴 코드 블록의 자동 감지는 편의 기능이므로 의도한 레이아웃이 중요하면 유형을 명시합니다.
