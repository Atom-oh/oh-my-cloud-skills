# ADR-007: Remarp Ratio Enforcement

## Status

Accepted (2026-04-27)

## Context

`_presentation.md`에서 `ratio` 필드가 누락되면 CSS 변수 `--slide-ratio-w`/`--slide-ratio-h`가 설정되지 않아 VSCode Extension 프리뷰에서 슬라이드 비율이 깨진다. HTML 빌드 시에는 기본값(16:9)이 적용되어 문제가 드러나지 않지만, 마크다운 프리뷰에서는 비율이 맞지 않는다.

## Decision

`ratio` 필드를 `_presentation.md` frontmatter의 필수 항목으로 격상한다:
1. `remarp_to_slides.py validate`에 `_validate_global_frontmatter()` 추가 — ratio 누락 시 WARNING
2. `remarp-format-guide.md` Frontmatter Fields 테이블에 Required로 명시
3. `SKILL.md` Phase 1 (PPTX 추출)과 Phase 2 (콘텐츠 작성)에 ratio 관련 가이드 추가

## Consequences

- 새 프레젠테이션 생성 시 ratio 누락 방지
- VSCode Extension 프리뷰에서 일관된 비율 유지
- PPTX에서 추출한 `slide_size.aspect_ratio`가 자동으로 반영됨

## References

- SKILL.md Phase 1, Phase 2
- `remarp-format-guide.md` Frontmatter Fields
- `remarp_to_slides.py` `_validate_global_frontmatter()`
