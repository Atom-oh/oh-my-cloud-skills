# ADR-011: PR Review — L1 결정적 게이트 + Lens×Model 매트릭스

## Status

Accepted (2026-07-05)

## Context

ADR-009의 멀티-AI 패널(Codex + Kiro×3)은 리뷰어를 벤더로 다양화했지만, 4개 AI 모두
**동일한 "전부 다 봐" 프롬프트**로 diff를 리뷰했다. 이 구조는 다양성의 축이 벤더 하나뿐이라,
특정 검토 영역(예: 버전 정합·dangling 참조)을 한 모델이 놓치면 다른 모델도 같은 프롬프트로
같은 영역을 놓칠 확률이 높고, 리뷰 결과를 걸러내는 verification 단계도 없어 오탐이 그대로
코멘트에 실렸다. 또한 결정적으로(스크립트로) 검증 가능한 항목(JSON 유효성, dangling 참조,
버전 정합)까지 AI 호출로 처리해 불필요한 비용·지연·오탐 여지를 만들었다.

## Options Considered

1. **현행 유지(동일 프롬프트 브로드캐스트)** — 단순하나 다양성 축이 벤더 하나뿐, 사각지대 반복.
2. **lens 별 전담(모델 1개 : lens 1개)** — 벤더 다양성을 lens 교차확인과 교환, 특정 CLI 부재 시
   lens 가 통째로 빈다.
3. **lens×model 풀 매트릭스 + 결정적 pre-check 분리** (채택) — 벤더 다양성과 관점(lens) 다양성을
   동시에 최대화하고, 결정적으로 검증 가능한 것은 AI 이전에 스크립트로 뺀다.

## Decision

`.github/workflows/pr-review.yml`을 2단 게이트로 재구성한다
(design: `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md`):

- **L1(결정적, AI 호출 없음)** — `scripts/pr-review/precheck.sh`가 PR head 트리를 `git archive`로
  **데이터로만** 추출(실행 없음)해, base(신뢰) 체크아웃의 `scripts/test-plugins.py --root <트리>`
  로 매니페스트 JSON 유효성·dangling 참조·버전 정합을 검증한다. 실패 시 AI 패널을 호출하지 않고
  즉시 `VERDICT: FAIL` — 결정적 문제에 AI 비용을 쓰지 않는다.
- **L2–L5(lens×model 매트릭스)** — L1 통과 시 4 모델(Codex + Kiro×3) × 4 lens(L2=Skill/Agent
  품질, L3=보안, L4=코드 정확성, L5=문서 일관성) = 16개 독립 find 에이전트가 전부 병렬(`&`+`wait`)
  로 실행된다. 각 셀은 자기 lens 하나만 리뷰 — 스코프 축소로 셀당 응답이 짧아져, 병렬 실행 특성상
  벽시계가 현행(4콜, 전 영역 스코프)보다 오히려 단축될 개연성이 있다(최슬로우-of-16(좁은 스코프)
  < 최슬로우-of-4(넓은 스코프)).
- **의장**: Claude Fable 5(→Opus 4.8 폴백, ADR-009 유지)가 16개 셀을 lens 별로 종합.
  `CHAIR_TIMEOUT`을 120s→180s로 상향(입력이 4→16 출력으로 늘어난 데 대응).
- **비용은 제약으로 두지 않음**(사용자 결정) — 실제 상한은 러너 동시성/API rate-limit뿐이며,
  job `timeout-minutes`(50m)로 방어.
- ADR-009의 나머지 불변식(보안: base-checkout + fork PR 미실행, 데이터 거주성: Kiro 외부 송신
  accepted-risk, fail-closed VERDICT, 코멘트 upsert marker)은 변경 없이 유지.

## Consequences

- 커버리지가 "리뷰어 다양화"에서 "리뷰어×관점 매트릭스"로 체계화 — 사각지대 감소.
- 결정적으로 검증 가능한 매니페스트/버전 문제는 0 오탐·0 AI 비용으로 즉시 차단.
- AI 콜 수가 1×패널(4)에서 최대 4×패널(16)로 증가 — 의도된 트레이드오프(비용 비제약).
- Phase V(verify, hybrid-gate 완전형)는 이번 구현에 포함하지 않음 — 매트릭스 자체가 lens당
  4중 교차확인이라 오탐을 상당 부분 흡수한다고 판단; 실제 오탐이 문제되면 추가.
- 테스트: `tests/pr-review/test-run-panel.sh`(매트릭스 fan-out) +
  `tests/pr-review/test-precheck.sh`(L1) 신설, `tests/run-all.sh`에 `pass`/`fail` 브리지 추가해
  `tests/pr-review/*.sh`를 CI 집계에 포함(이전엔 미집계 gap).

## References

- ADR-009(멀티-AI 패널 원안), ADR-010(Antigravity 제거)
- `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md` (설계안)
- `.github/workflows/pr-review.yml`, `scripts/pr-review/{precheck,run-panel,synthesize,lib}.sh`,
  `scripts/test-plugins.py --root`
- `docs/ci-pr-review.md`, `docs/ci-pr-review-runbook.md`
- `tests/pr-review/{test-run-panel,test-precheck}.sh`
