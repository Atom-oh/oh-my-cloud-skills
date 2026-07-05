# ADR-009: Multi-AI PR Review CI Panel

## Status

Accepted (2026-06-17)

## Context

PR 품질 게이트로 자동 코드/콘텐츠 리뷰가 필요했다. 단일 모델 리뷰는 편향·맹점이 있어, 서로 다른
모델 패밀리의 다중 관점을 모으고 Claude가 의장으로 종합하는 패널이 더 신뢰할 만하다. 호출은
self-hosted 러너가 **EKS Pod Identity(SigV4)** 로 Amazon Bedrock을 호출한다(Pod Identity Association → 러너 IAM 역할).

## Options Considered

1. **단일 모델 1회 리뷰** — 간단하나 편향/맹점.
2. **멀티-AI fan-out + Claude 의장 종합 (fail-closed 게이트)** — 다중관점, 자문은 패널·결정은 Claude. (채택)

## Decision

`.github/workflows/pr-review.yml`(`pull_request_target`)에서:

- **패널 fan-out** — Codex(`openai.gpt-5.5`) + Kiro×3(`claude-opus-4.8`/`kimi-k2.5`/`glm-5`) →
  `scripts/pr-review/run-panel.sh`; **Claude Opus 4.8 의장**이 `synthesize.sh`로 종합.
- **게이트** — 마지막 줄 `VERDICT: PASS|FAIL` 룰로 job exit code 결정(**fail-closed**); `<!-- oh-my-cloud-skills-pr-review -->` 마커로 코멘트 upsert.
- **보안** — `pull_request_target`는 시크릿/쓰기 컨텍스트라 **base(신뢰) 브랜치 스크립트**를 체크아웃하고 PR 변경분은 `gh pr diff`로 데이터로만 수신(미실행). → 스크립트 수정은 **머지 후** PR부터 적용.
- **데이터 경계 (호출 경로별로 다름)** — **Codex / Claude(의장)** 는 Amazon Bedrock **us-east-1 In-Region**(`gpt-5.5`/`opus-4-8` 모두 In-Region), EKS Pod Identity SigV4. **Kiro** 는 **외부 API-key 기반 서비스**로 PR diff가 리전 밖으로 전송됨(In-Region 아님). (ADR 보강: us-east-2 페일오버는 `gpt-5.5` 단일리전이라 폐기 — #88.)
- **거주성 리스크 수용 + 강제 경로** — Kiro로의 외부 송신을 막는 "민감 diff 시 외부 패널 비활성화"는 현재 **수동(fail-open) 규약**이라, 사람이 토글을 잊으면 기본값으로 diff가 리전 밖으로 나간다. **이 repo에 한해 accepted-risk(by-design)**: 공개 마켓플레이스라 PR diff는 머지 시 어차피 공개 정보 → 외부 리뷰 API 전송의 거주성 리스크가 낮다. **이 CI를 비공개 repo로 fork하는 경우엔 fail-open이 부적절**하므로, 워크플로에 **강제 skip 게이트**(예: `no-external-review` 라벨 또는 민감 경로 매칭 시 `run-panel.sh`에서 Kiro 슬롯 skip)를 추가할 것 — 수동 규약에 의존하지 말 것.
- **diff 전달 + 인젝션 표면 (규약 예외 명시)** — Codex는 stdin, **Kiro는 prompt 인자로 embed**(kiro-cli chat은 stdin 미독 → 미임베드 시 blind 리뷰). 이는 레포 리뷰 규약 "미신뢰 콘텐츠는 STDIN, 커맨드라인 보간 금지"의 **의도적 예외**다. 완화책: (1) diff는 `"$KIRO_PROMPT"` **인용된 단일 argv**로 전달 → 셸/argument 인젝션 불가(eval 없음); (2) `pull_request_target` job은 `head.repo.full_name == github.repository` 게이트로 **fork PR 미실행**(트리거엔 push 권한 필요); (3) prompt-injection은 패널 출력을 **자문**으로만 다루고 Claude 의장이 diff와 대조해 확정(단일 verdict 비채택)으로 완화; (4) diff는 3000줄로 절단(라인 기준 — 극단 diff엔 byte-cap이 더 안전하나 현 구현 실위험 낮음).

## Consequences

- 매 PR 자동 다중관점 리뷰 + fail-closed 게이트.
- 패널 verdict는 **자문**(verify, not vote-count) — Claude 의장이 diff와 대조해 확정.
- Antigravity(`agy`)는 OAuth 인터랙티브 전용이라 헤드리스 CI에선 제외(Codex + Kiro만).
- base-script 실행 모델이라 리뷰 로직 변경의 자기검증이 불가(다음 PR에서 검증).

## References

- `.github/workflows/pr-review.yml`, `scripts/pr-review/{run-panel,synthesize,lib}.sh`
- `docs/ci-pr-review.md`, `tests/pr-review/test-run-panel.sh`
- PR #72 (도입), #87 (Kiro diff 전달), #88 (us-east-1 통일 — 리전 페일오버 폐기)
- **Amended by ADR-011** — L1 결정적 pre-check 추가 + lens×model 매트릭스로 패널 구조
  재편, Kiro diff 전달을 위 "prompt 인자로 embed"에서 `fs_read` 파일 참조로 전환(+env/cwd
  격리). ADR-009 본문의 원 결정(멀티-AI 패널 + Claude 의장 종합)은 반전되지 않아 Status는
  유지 — 확장·정제 내역은 ADR-011 참조.
