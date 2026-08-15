# ADR-005: Rejection Loop (Iterative Refinement)

## Status

Accepted (2026-04-15)

## Context

When building a Remarp presentation, content quality problems (missing speaker notes, static HTML, incorrect fragment indices, etc.) were discovered only after the build, which lengthened the fix-build-verify cycle.

## Decision

Add a `remarp_to_slides.py validate` command that introduces a rejection loop, automatically checking 7 or more rules before the build. The build can proceed only when there are zero CRITICAL issues.

Validation items:
- Speaker notes present and meet minimum length (150 characters)
- Fragment index continuity
- Presence of reactive elements in `:::html` blocks
- Required `_presentation.md` frontmatter (ratio, footer)
- Required elements per slide type

## Consequences

- Enforcing quality before the build raised the average content-review-agent review score by 15 points
- The validate step was made mandatory in SKILL.md Phase 3
- Can also be validated automatically in CI via the `--json` flag

## References

- Commit: 8aec151
- SKILL.md Phase 3 workflow
