# ADR-005: Rejection Loop (Iterative Refinement)

## Status

Accepted (2026-04-15)

## Context

Remarp 프레젠테이션 빌드 시 콘텐츠 품질 문제(누락된 스피커 노트, 정적 HTML, 잘못된 프래그먼트 인덱스 등)가 빌드 후에야 발견되어 수정-빌드-검증 사이클이 길어졌다.

## Decision

`remarp_to_slides.py validate` 명령을 추가하여 빌드 전에 7개 이상의 규칙을 자동 검증하는 거절 루프를 도입한다. CRITICAL 이슈가 0건이어야 빌드를 진행할 수 있다.

검증 항목:
- 스피커 노트 존재 및 최소 길이 (150자)
- 프래그먼트 인덱스 연속성
- `:::html` 블록의 reactive 요소 존재
- `_presentation.md` 필수 frontmatter (ratio, footer)
- 슬라이드 타입별 필수 요소

## Consequences

- 빌드 전 품질 강제로 content-review-agent 리뷰 점수가 평균 15점 상승
- SKILL.md Phase 3에 validate 단계가 필수로 추가됨
- CI에서도 `--json` 플래그로 자동 검증 가능

## References

- Commit: 8aec151
- SKILL.md Phase 3 workflow

---

> **Reconciliation note (2026-06-11, decision-reconcile)** — 본 ADR의 검증 항목 목록에 있는 "`_presentation.md` 필수 frontmatter (ratio, footer)"는 *build-blocking(CRITICAL)*이 아닙니다. 실제 구현(`remarp_to_slides.py` `_validate_global_frontmatter()`)은 `ratio`/`footer` 누락을 **WARNING**으로 분류하며, 빌드를 막는 것은 frontmatter 블록 자체의 부재(`MISSING_FRONTMATTER`, CRITICAL)뿐입니다. ratio 검증 규칙은 [ADR-007](ADR-007-ratio-enforcement.md)이 정밀화합니다. 즉 "필수"는 *권장/경고 수준*으로 읽어야 하며, "CRITICAL 0건 게이트"는 frontmatter 부재 등 CRITICAL 항목에만 적용됩니다.
