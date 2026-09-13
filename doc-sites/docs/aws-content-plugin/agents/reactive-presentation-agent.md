---
sidebar_position: 2
title: "Reactive presentation agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="presentation-agent와의-관계" />
<span id="워크플로우" />
<span id="phase-1-planning--theme-setup" />
<span id="phase-2-content-authoring-remarp" />
<span id="phase-3-review--build" />
<span id="슬라이드-타입" />
<span id="canvas-vs-html-선택-기준-v123" />
<span id="html-architecture-패턴-박스-5-필수" />
<span id="키보드-단축키" />
<span id="출력물" />
<span id="협업-워크플로우" />


# Reactive presentation agent

Authors Remarp source, builds interactive HTML slides, and verifies the presentation in a browser. It supports content, code, comparison, tabs, quiz, timeline, checklist, and simple Canvas slides.

## Workflow

Plan the story and blocks; extract a supplied PPTX theme when needed; author source with speaker notes; validate; build; test navigation and interactions; run content review before publication. Use HTML/CSS for grouped or branching architectures and interactive calculators, and Canvas only for small linear flows.

## Output and verification

Return the editable source, rendered output, relevant build commands, and verification evidence. The content-review gate applies before completion/publication; a successful file write alone is not a passing review.

[Agent contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/reactive-presentation-agent.md) · [Skill guide](/docs/aws-content-plugin/skills/reactive-presentation)
