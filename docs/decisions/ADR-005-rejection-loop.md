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
