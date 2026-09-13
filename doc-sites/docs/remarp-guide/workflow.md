---
sidebar_position: 3
title: "Author and revise a deck"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="사용-워크플로우" />
<span id="전체-흐름" />
<span id="1단계-프레젠테이션-생성" />
<span id="2단계-vscode에서-편집" />
<span id="편집-예시--슬라이드-내용-수정" />
<span id="편집-예시--퀴즈-추가" />
<span id="편집-예시--canvas-다이어그램-추가" />
<span id="3단계-프롬프트로-반영" />
<span id="반영-프롬프트" />
<span id="예시" />
<span id="4단계-브라우저-프리뷰" />
<span id="키보드-조작" />
<span id="인터랙티브-슬라이드-조작" />
<span id="5단계-html-직접-편집-선택" />
<span id="확인-방법" />
<span id="visual-edit-모드" />
<span id="canvas-visual-edit" />
<span id="이슈-기반-리뷰-워크플로우" />
<span id="반복-편집-사이클" />
<span id="증분-빌드" />
<span id="슬라이드-타입-빠른-참조" />
<span id="다음-단계" />


# Author and revise a deck

## Plan and generate

Specify audience, technical level, language, duration, output format, and source material. Plan blocks and the main message of each slide. For web output, the reactive-presentation workflow authors Remarp source and builds a browsable deck.

## Edit source

Use the editor preview to navigate slides and inspect notes. Modify content, directives, fragments, quizzes, tabs, or the simple Canvas DSL in the source. The current registered editor commands do not expose the visual-edit/writeback helpers; make those changes in source and rebuild. See the [editor guide](./vscode-extension.md) for the supported entry points.

## Issue-based revision

Record a specific issue as `<!-- issue: ... -->`, including the affected slide and observable problem. Run slide-fix to inspect and repair the source, remove resolved annotations, and leave unresolved issues visible in the report. List annotations using the converter's `issues` command.

## Build and verify

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/ --lang en
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py sync ./my-presentation/
```

Inspect the first slide and representative layouts; exercise fragments, option/tab buttons, quizzes, Canvas steps, and any custom input controls; check notes and presenter view; inspect asset and console failures. Keep durable edits in Remarp source; rebuilding overwrites direct HTML changes. A full build refreshes the merged deck, table of contents, and shared assets; `sync` updates changed block pages only.

## Finish

Keep the editable source with the generated output, record validation evidence, and pass content review before authorized publication. Use the native PowerPoint workflow when the deliverable requires editable PowerPoint shapes and text.

## Related links

- [content](./slide-types/content.md)
- [Canvas DSL](./syntax/canvas-dsl.md)
- [fragments](./syntax/fragments.md)
- [pptx extraction](./themes/pptx-extraction.md)
