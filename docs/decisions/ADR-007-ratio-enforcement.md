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

---

> **Reconciliation note (2026-06-11, decision-reconcile)** — 본 ADR은 [ADR-005](ADR-005-rejection-loop.md)의 검증 항목 목록(`_presentation.md` 필수 frontmatter (ratio, footer))을 정밀화합니다. `ratio`를 "필수 항목으로 격상"한다고 했으나 실제 강제 수준은 **WARNING**(누락 시 비차단 경고)이며 build-blocking이 아닙니다. `footer` 역시 구현상 WARNING입니다. 따라서 ADR-005의 "필수/CRITICAL 게이트" 표현과 본 ADR은 *심각도 = WARNING*으로 일치합니다.
