# ADR-009: Multi-AI PR Review CI Panel

## Status

Accepted (2026-06-17)

## Context

PR 품질 게이트로 자동 코드/콘텐츠 리뷰가 필요했다. 단일 모델 리뷰는 편향·맹점이 있어, 서로 다른
모델 패밀리의 다중 관점을 모으고 Claude가 의장으로 종합하는 패널이 더 신뢰할 만하다. 호출은
self-hosted 러너의 노드 IAM(SigV4)으로 Amazon Bedrock을 사용한다.

## Options Considered

1. **단일 모델 1회 리뷰** — 간단하나 편향/맹점.
2. **멀티-AI fan-out + Claude 의장 종합 (fail-closed 게이트)** — 다중관점, 자문은 패널·결정은 Claude. (채택)

## Decision

`.github/workflows/pr-review.yml`(`pull_request_target`)에서:

- **패널 fan-out** — Codex(`openai.gpt-5.5`) + Kiro×3(`claude-opus-4.8`/`kimi-k2.5`/`glm-5`) →
  `scripts/pr-review/run-panel.sh`; **Claude Opus 4.8 의장**이 `synthesize.sh`로 종합.
- **게이트** — 마지막 줄 `VERDICT: PASS|FAIL` 룰로 job exit code 결정(**fail-closed**); `<!-- oh-my-cloud-skills-pr-review -->` 마커로 코멘트 upsert.
- **보안** — `pull_request_target`는 시크릿/쓰기 컨텍스트라 **base(신뢰) 브랜치 스크립트**를 체크아웃하고 PR 변경분은 `gh pr diff`로 데이터로만 수신(미실행). → 스크립트 수정은 **머지 후** PR부터 적용.
- **리전** — `gpt-5.5`(bedrock-mantle)·`opus-4-8` 모두 In-Region인 **us-east-1로 통일**(ADR 보강: us-east-2 페일오버는 gpt-5.5 단일리전이라 폐기).
- **diff 전달** — Codex는 stdin, **Kiro는 prompt 인자로 embed**(kiro-cli chat은 stdin 미독 → 미임베드 시 blind 리뷰).

## Consequences

- 매 PR 자동 다중관점 리뷰 + fail-closed 게이트.
- 패널 verdict는 **자문**(verify, not vote-count) — Claude 의장이 diff와 대조해 확정.
- Antigravity(`agy`)는 OAuth 인터랙티브 전용이라 헤드리스 CI에선 제외(Codex + Kiro만).
- base-script 실행 모델이라 리뷰 로직 변경의 자기검증이 불가(다음 PR에서 검증).

## References

- `.github/workflows/pr-review.yml`, `scripts/pr-review/{run-panel,synthesize,lib}.sh`
- `docs/ci-pr-review.md`, `tests/pr-review/test-run-panel.sh`
- PR #72 (도입), #87 (Kiro diff 전달), #88 (us-east-1 통일 — 리전 페일오버 폐기)
