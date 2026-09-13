---
sidebar_position: 2
title: "Create content"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="사용법-가이드" />
<span id="빠른-시작" />
<span id="에이전트-자동-호출" />
<span id="프레젠테이션-만들기" />
<span id="프롬프트-예시" />
<span id="에이전트-질문-항목" />
<span id="워크플로우" />
<span id="pptx-테마-적용" />
<span id="remarp-포맷" />
<span id="파일-구조" />
<span id="핵심-문법" />
<span id="frontmatter" />
<span id="빌드" />
<span id="아키텍처-다이어그램" />
<span id="애니메이션-다이어그램" />
<span id="문서-생성" />
<span id="gitbook--workshop" />
<span id="gitbook-문서-사이트" />
<span id="aws-workshop-studio" />
<span id="프로필-페이지-만들기-gh-home" />
<span id="준비물" />
<span id="프롬프트-예시-1" />
<span id="워크플로우-1" />
<span id="quality-gate" />
<span id="키보드-단축키" />
<span id="팁--트릭" />
<span id="블록-편집" />
<span id="증분-빌드" />
<span id="한국어영어-혼용-규칙" />
<span id="다이어그램-에이전트-선택" />
<span id="canvas-vs-html-선택-기준-v123" />


# Create content

## Start from the deliverable

State the audience, technical level, language, duration or page scope, output format, and source material. Example: “Create an English 30-minute EKS operations web deck with speaker notes, a small traffic animation, and review questions.” For editable PowerPoint, request the native AWS light workflow explicitly.

## Presentations

The web workflow plans blocks, optionally extracts a PPTX theme, authors Remarp, validates source, builds HTML, and tests interactions. A multi-file deck uses `_presentation.md` plus numbered block files. The source remains the editing authority; synchronize only changed blocks when appropriate. Set `lang: en` in `_presentation.md` for English project and table-of-contents output, and keep any block-level language overrides consistent. The `--lang` flag applies only to single-file builds. Use a full build after global metadata changes and before publishing; `sync` refreshes changed block pages, not the merged deck or shared assets.

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build ./my-presentation/
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py sync ./my-presentation/
```

Native PowerPoint uses aws-light-fcd assets and PptxGenJS, then embeds fonts and inspects the deck. Web-deck PPTX export produces screenshot-based slides; it does not make animated HTML objects editable.

## Diagrams

Use the Draw.io layout generator for supported AWS patterns. Validate XML and layout before export, and use the canonical token file for size/color rules. Animated SVG suits repeating traffic; JavaScript/CSS handles scenario controls. On a slide, use Canvas for at most four boxes/icons in a simple linear flow; use HTML/CSS for groups, branches, or larger architectures.

## Documents, sites, and workshops

The document agent writes reports and comparisons. GitBook supplies multi-page navigation and rich documentation components. Workshop Creator supplies Workshop Studio structure, directives, lab verification, and cleanup. Brochure builds product/solution landing pages; gh-home builds a personal profile with experience, skills, and selected work. For a profile refresh, confirm before overwriting an existing `index.html` and preserve unrelated CNAME, robots.txt, and analytics files.

## Revision and review

Edit Remarp source or add `<!-- issue: ... -->` annotations through the editor, then run slide-fix and rebuild. Inspect keyboard navigation, fragments, Canvas steps, quizzes, tabs, and responsive layout. Use the content-review gate before authorized publication. Keep prose in the requested language and preserve exact service names, syntax, paths, and identifiers.

[Remarp syntax](/docs/remarp-guide/introduction) · [Keyboard controls](/docs/remarp-guide/keyboard-shortcuts) · [Content review](/docs/aws-content-plugin/agents/content-review-agent)
