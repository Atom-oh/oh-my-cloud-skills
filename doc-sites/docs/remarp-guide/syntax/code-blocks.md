---
sidebar_position: 7
title: "Code blocks"
---

{/* Legacy section links retained after the English rewrite. */}
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


# Code blocks

Use fenced code with the correct language. Remarp supports filename labels, line highlights, and diff styling for readable technical slides.

````markdown
```python {filename="review.py" highlight="2-3"}
def summarize(checks):
    passed = [check for check in checks if check["passed"]]
    return len(passed), len(checks)
```
````

## Attributes and highlighting

A filename identifies the source file. Highlight specifications select individual lines or ranges. Combine supported fence attributes rather than inserting presentation markup into the code itself. Keep excerpts short enough to read; use a code slide for a focused example and speaker notes for explanation.

## Diff blocks

````markdown
```diff
- timeout = 5
+ timeout = 15
```
````

Use diff styling for the actual changed lines and explain why behavior changes. Code fences may contain Python, JavaScript/TypeScript, YAML, JSON, Bash, or another language supported by the bundled highlighter. The language label provides syntax highlighting; it does not validate or execute the example.

## Rendering checks

Inspect overflow, line wrapping, highlight contrast, filename labels, and the selected slide type. Auto-detection of long code blocks is a convenience; use an explicit type when the intended layout is important.
