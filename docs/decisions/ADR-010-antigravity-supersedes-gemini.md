# ADR-010: Antigravity (`agy`) Supersedes the Gemini CLI

## Status

Accepted (2026-06-17)

## Context

co-agent 패널은 Gemini-family CLI를 한 슬롯으로 사용해 왔다. `gemini` CLI가 deprecated되고
**Antigravity(`agy`)** 가 Gemini-family 후속으로 등장하면서, `agy`와 `gemini`를 둘 다 fan-out하면
**동일 패밀리 중복**이 생긴다. 어느 것을 패널 멤버로 쓸지 일관 규칙이 필요하다.

## Options Considered

1. **둘 다 항상 실행** — 같은 모델 패밀리를 두 번 — 비용·중복, 합의 신호 왜곡.
2. **`agy` 우선, `gemini` 폴백** — 설치된 것 중 `agy`를 쓰고, 없으면 `gemini`, 둘 다 없으면 스킵. (채택)

## Decision

Gemini-family 슬롯의 우선순위를 **`agy` → `gemini` → 스킵**으로 고정한다:

- `agy`와 `gemini`가 모두 있으면 fan-out은 `agy`만 쓰고 `gemini`는 **스킵**(동일패밀리 중복 방지).
- `agy`가 없고 `gemini`만 있으면 `gemini` 사용(**하위호환**).
- 둘 다 없으면 그 슬롯은 스킵(graceful degrade).
- 적용 범위: co-agent 팬아웃(`ai-cli-adapters.md`), `decision-reconcile` 패널, 사용자 문서(README/architecture)의 패널 표기.
- 호출: `agy -p "<P>" --model "Gemini 3.1 Pro (High)" --sandbox`(read-only). `--dangerously-skip-permissions` 금지.

## Consequences

- 동일 패밀리 중복 제거; `gemini`만 있는 환경도 계속 동작.
- 사용자 문서의 패널 표기는 "Kiro/Codex/Antigravity"를 기본으로 하되 **Gemini 폴백을 명시**(완전 대체 아님).
- **`GEMINI.md` 파일명은 유지** — Antigravity/Gemini가 읽는 Gemini-family 컨텍스트 파일이며 CLI 선택과 무관.
- pr-review CI 패널에는 미적용 — `agy`가 OAuth 인터랙티브 전용이라 헤드리스 CI에서 인증 불가(거기선 Codex + Kiro만).

## References

- `plugins/co-agent/CLAUDE.md`, `plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md`
- `plugins/project-init/skills/decision-reconcile/SKILL.md` (probe/invoke 우선순위)
- README.md / README.ko.md / `docs/architecture.md` 패널 표기
