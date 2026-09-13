---
sidebar_position: 1
title: "Presentation dispatcher"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="presentation-agent-dispatcher" />
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="라우팅-로직" />
<span id="키워드-분류" />
<span id="webinteractive-즉시-위임" />
<span id="pptx-pptx-경로" />
<span id="포맷-선택-질문" />
<span id="reactive-presentation-agent와의-관계" />


# Presentation dispatcher

Routes a presentation request to interactive web slides or editable PowerPoint. Explicit web/interactive requests use reactive-presentation; native editable AWS light decks use aws-light-fcd. If the requested format is unclear, establish the deliverable before building.

## Workflow {#workflow}

Determine audience, duration, technical level, language, output format, and any reference template. Web decks retain interaction and can be exported as slide images; native PowerPoint uses PptxGenJS and editable objects.

## Output and verification {#output-and-verification}

Return the editable source, rendered output, relevant build commands, and verification evidence. The content-review gate applies before completion/publication; a successful file write alone is not a passing review.

[Agent contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/agents/presentation-agent.md) · [Skill guide](/docs/aws-content-plugin/skills/reactive-presentation)

## Related links {#related-links}

- [Reactive Presentation Agent](./reactive-presentation-agent)
