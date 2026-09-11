# Content workflow in Codex

Shared skill and agent procedures are available as Codex skills. For a generic
presentation request, use `presentation-agent` to select native PPTX or web slides.
Use `document-agent` for technical Markdown; other formats have named skills.

For every produced artifact, load `content-review-agent` and apply its actual
rubric before declaring completion or publishing. The gate is PASS at 85/100,
or 77/90 only for the rubric's visual-testing-exempt content. A local self-check
does not replace that review. If a separate reviewer is available, give it the
artifact and rubric; otherwise perform and disclose a separate review pass.
Missing visual evidence must be reported as unverified.

Playwright is bundled through the Codex MCP manifest. Use available browser tools
or the documented local Playwright path for visual checks. The PPTX icon library
is inside this same plugin's `skills/reactive-presentation/`; resolve it from the
installed plugin, not from a marketplace sibling's cache.
