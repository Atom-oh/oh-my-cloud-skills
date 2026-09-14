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

Use fenced code with the correct language. Remarp emits filename labels and line-highlight markers for technical slides.

````markdown
```python {filename="review.py" highlight="2-3"}
def summarize(checks):
    passed = [check for check in checks if check["passed"]]
    return len(passed), len(checks)
```
````

## Attributes and highlighting {#attributes-and-highlighting}

A filename identifies the source file. Highlight specifications select individual lines or ranges. Combine supported fence attributes rather than inserting presentation markup into the code itself. Keep excerpts short enough to read; use a code slide for a focused example and speaker notes for explanation.

## Diff blocks {#diff-blocks}

````markdown
```diff
- timeout = 5
+ timeout = 15
```
````

`diff` fences preserve literal `-` and `+` lines, but the current Remarp slide renderer has no diff-specific styling. This Docusaurus guide page renders separately from generated slides. For visual change annotations, author HTML/CSS where appropriate and inspect the generated slides.

Code fences may contain Python, JavaScript/TypeScript, YAML, JSON, Bash, or another language supported by the bundled highlighter. Syntax highlighting does not validate or execute the example.

## Rendering checks {#rendering-checks}

Inspect overflow, line wrapping, highlight contrast, filename labels, and the selected slide type. Auto-detection of long code blocks is a convenience; use an explicit type when the intended layout is important.
