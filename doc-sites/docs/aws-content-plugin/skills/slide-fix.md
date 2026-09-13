---
sidebar_position: 5
title: "Slide fix skill"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="trigger-keywords" />
<span id="워크플로우" />
<span id="작동-방식" />
<span id="1-issue-삽입-vscode-extension" />
<span id="2-issue-추출" />
<span id="3-수정-및-정리" />
<span id="vscode-extension-연동" />
<span id="사용-예시" />
<span id="quality-review" />


# Slide fix skill

Apply issue annotations from Remarp or the editor to the actual slide source.

## Annotation loop

```markdown
<!-- issue: The comparison labels overlap at the mobile viewport. -->
```

List annotations with `remarp_to_slides.py issues <path>`; use `--json` for structured output. Check each note against the relevant slide, fix the source/CSS/diagram, remove resolved annotations, and preserve unresolved ones with a clear report. Rebuild the affected blocks and reproduce the failing interaction or layout before claiming the issue is fixed.

The VS Code extension can attach annotations while previewing Remarp or generated HTML. Keep source and generated output aligned; direct HTML edits may otherwise be overwritten. Content review applies to the final candidate.


[Skill, resources, and quality requirements](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-content-plugin/skills/slide-fix/SKILL.md)
