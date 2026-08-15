# ADR-007: Remarp Ratio Enforcement

## Status

Accepted (2026-04-27)

## Context

If the `ratio` field is missing from `_presentation.md`, the CSS variables `--slide-ratio-w`/`--slide-ratio-h` are never set, and the slide ratio breaks in the VSCode Extension preview. During the HTML build, the default value (16:9) is applied so the problem doesn't surface, but in the markdown preview the ratio doesn't match.

## Decision

Promote the `ratio` field to a required item in `_presentation.md` frontmatter:
1. Add `_validate_global_frontmatter()` to `remarp_to_slides.py validate` — WARNING when ratio is missing
2. Mark it as Required in the Frontmatter Fields table in `remarp-format-guide.md`
3. Add ratio-related guidance to `SKILL.md` Phase 1 (PPTX extraction) and Phase 2 (content authoring)

## Consequences

- Prevents ratio omission when creating new presentations
- Keeps the ratio consistent in the VSCode Extension preview
- The `slide_size.aspect_ratio` extracted from PPTX is automatically reflected

## References

- SKILL.md Phase 1, Phase 2
- `remarp-format-guide.md` Frontmatter Fields
- `remarp_to_slides.py` `_validate_global_frontmatter()`
