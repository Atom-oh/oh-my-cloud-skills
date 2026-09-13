---
sidebar_position: 6
title: "Timeline slides"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="timeline-슬라이드" />
<span id="기본-문법" />
<span id="디렉티브" />
<span id="구조" />
<span id="예제" />
<span id="프로젝트-로드맵" />
<span id="서비스-진화" />
<span id="릴리스-일정" />
<span id="렌더링" />
<span id="스타일-클래스" />
<span id="팁" />


# Timeline slides

Present ordered phases, milestones, or release stages.

## Source

```markdown
---
@type: timeline

## Documentation update

### Audit
Compare instructions with actual source.

### Edit
Correct stale claims and examples.

### Verify
Build, check links, and review the result.
```

## Rendering and interaction

Third-level headings define timeline points. Keep each description short and put detail on a separate slide. Rendered classes include timeline-step, timeline-dot, timeline-connector, and active/done states where assigned by the renderer. Dates in a timeline are authored content, not evidence of a feature release.

Add speaker notes and run source validation before building. Test the slide in the generated deck; the HTML structure and CSS classes are implementation details, not a substitute for checking behavior.

See [directives](../syntax/directives.md), [speaker notes](../syntax/speaker-notes.md), and [keyboard controls](../keyboard-shortcuts.md).
