---
sidebar_position: 12
title: "Migrate from Marp"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="marp에서-마이그레이션" />
<span id="자동-변환" />
<span id="변환-테이블" />
<span id="하위-호환성" />
<span id="상세-변환-예제" />
<span id="frontmatter" />
<span id="블록-지정" />
<span id="슬라이드-타입" />
<span id="스피커-노트" />
<span id="canvas-슬라이드" />
<span id="무엇이-바뀌나요" />
<span id="바뀌는-것" />
<span id="그대로-유지되는-것" />
<span id="마이그레이션-체크리스트" />
<span id="1-frontmatter-업데이트" />
<span id="2-블록-분리-선택사항" />
<span id="3-디렉티브-변환" />
<span id="4-스피커-노트-변환" />
<span id="5-레이아웃-변환" />
<span id="6-인터랙티브-기능-추가-선택사항" />
<span id="점진적-마이그레이션" />


# Migrate from Marp

The converter can migrate an existing Marp file into a Remarp project. Migration prepares source; it does not guarantee complete visual or behavioral equivalence.

```bash
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py migrate old-talk.md -o /var/tmp/remarp-talk
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py validate /var/tmp/remarp-talk
python3 plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py build /var/tmp/remarp-talk --lang en
```

## Review the mapping

Change the deck marker to `remarp: true`; move global metadata into `_presentation.md` when splitting blocks; replace legacy slide comments with supported `@type`, `@layout`, background, and timing directives; convert speaker guidance into `:::notes`; and inspect column/layout blocks.

Ordinary headings, lists, code, and images usually remain recognizable Markdown. Interactive quizzes, tabs, Canvas steps, and fragment behavior need deliberate authoring and browser checks. Preserve required note markers and existing published links.

## Incremental migration

Keep the original as a reference, migrate one block, validate/build, compare its render, then continue. Use `.md` with Remarp frontmatter for new source; `.remarp.md` remains supported. Check asset paths, theme compatibility, notes, navigation, and exports before replacing the old deck.
