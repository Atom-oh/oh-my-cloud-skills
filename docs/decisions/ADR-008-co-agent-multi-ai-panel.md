# ADR-008: co-agent multi-AI panel as the marketplace review/decision mechanism

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status

Accepted (2026-06-11) — Supersedes ADR-003

## Context

ADR-003 decided to integrate the external `kiro-cli-plugin` (`whchoi98/kiro-cli-plugin`) into the Claude Code workflow, exposing interactive slash commands `/kiro-cli:review`, `/kiro-cli:task`, and `/kiro-cli:spec` to add multi-perspective and adversarial review. That decision was sound at the time, but the marketplace has since grown a first-party plugin, `co-agent`, that pursues the same goal — a second opinion beyond a single agent's perspective — through a different, more general mechanism, and `co-agent` is now the as-built path.

Two facts force a reconciliation: (1) `co-agent` exists and is documented in the root `CLAUDE.md` as a shipped plugin, but it has no ADR of its own; (2) `co-agent`'s adapter reference (`plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md`) explicitly states that the `/kiro-cli:*` interactive slash commands are "not this skill's automated fan-out" — `co-agent` instead calls `kiro-cli chat --no-interactive` headlessly. ADR-003 therefore describes an approach the repo no longer takes as its primary path, while remaining marked `Accepted` with no supersession link.

## Options Considered

### Option 1: Keep ADR-003 as-is and add no ADR for co-agent

- **Pros**: No churn.
- **Cons**: An `Accepted` ADR keeps pointing at the non-primary `/kiro-cli:*` interactive integration; the actual review mechanism (`co-agent`) stays undocumented as a decision. Future readers are misled.

### Option 2: Author ADR-008 for co-agent and supersede ADR-003

- **Pros**: Records the as-built decision (multi-AI panel: Kiro/Codex/Gemini fanned in parallel, Claude chairs and synthesizes), fills the missing-ADR gap for co-agent, and retires ADR-003's specific slash-command approach cleanly via a `Superseded by` link. Preserves ADR-003 as an immutable point-in-time record.
- **Cons**: Adds an ADR; ADR-003's external plugin remains technically installable for interactive use, so the supersession is of the *approach*, not an outright ban.

## Decision

Adopt Option 2. The marketplace's review/decision/ADR-co-authoring mechanism is the first-party `co-agent` plugin (1 agent, 1 skill, 2 commands), with four modes — Review, Decide, ADR, and sync-context. It fans the same prompt in parallel to whichever AI CLIs are installed — Kiro (`kiro-cli chat --no-interactive`), Codex (`codex exec -s read-only`), Gemini (`gemini -p … -o text`) — then **Claude chairs and synthesizes** (consensus vs. dissent). It degrades gracefully to a Claude-only answer when no external CLI is present.

This supersedes ADR-003's decision to rely on the external `kiro-cli-plugin`'s interactive `/kiro-cli:*` slash commands. Kiro remains a panel member, but via the headless `kiro-cli chat` subprocess path, not the interactive plugin commands.

## Consequences

### Positive

- The actual, shipped review mechanism is now recorded as a decision.
- Cross-vendor diversity (Kiro/Codex/Gemini) generalizes ADR-003's Kiro-only review.
- Graceful degradation: no hard dependency on any single external CLI.
- ADR-003 is preserved unedited except for a status/link update — immutability respected.

### Negative

- Adds an ADR to the log.
- The external `kiro-cli-plugin` from ADR-003 is no longer the primary path; teams relying on its interactive slash commands must switch to `co-agent` or use the plugin standalone.

## References

- `plugins/co-agent/` — the plugin this ADR records
- `plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md` — headless adapter syntax; disavowal of `/kiro-cli:*` for automated fan-out
- ADR-003: Kiro CLI deep review — superseded by this ADR

---

<a id="korean"></a>

# 한국어

## 상태

승인됨 (2026-06-11) — ADR-003을 대체함 (Superseded by ADR-008 표기는 영문 섹션 참조)

## 배경

ADR-003은 외부 `kiro-cli-plugin`(`whchoi98/kiro-cli-plugin`)을 Claude Code 워크플로우에 통합하여 `/kiro-cli:review`, `/kiro-cli:task`, `/kiro-cli:spec` 대화형 슬래시 명령으로 다중 관점·적대적 리뷰를 추가하기로 결정했습니다. 당시로서는 타당했으나, 이후 마켓플레이스에 동일한 목표(단일 에이전트 관점을 넘어선 second opinion)를 더 일반적인 방식으로 달성하는 자체(first-party) 플러그인 `co-agent`가 생겼고, 현재 실제 구현 경로는 `co-agent`입니다.

화해가 필요한 두 사실: (1) `co-agent`는 루트 `CLAUDE.md`에 출시된 플러그인으로 문서화돼 있으나 자체 ADR이 없습니다. (2) `co-agent`의 어댑터 레퍼런스(`plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md`)는 `/kiro-cli:*` 대화형 명령이 "이 스킬의 자동 fan-out이 아니다"라고 명시하며, 대신 `kiro-cli chat --no-interactive`를 headless로 호출합니다. 따라서 ADR-003은 더 이상 주 경로가 아닌 접근을 기술하면서도 `Accepted` 상태에 대체 링크가 없습니다.

## 검토한 옵션

### 옵션 1: ADR-003 유지 + co-agent ADR 미작성

- **장점**: 변경 없음.
- **단점**: `Accepted` ADR이 비주류 `/kiro-cli:*` 대화형 통합을 계속 가리키고, 실제 메커니즘(`co-agent`)은 결정으로 문서화되지 않아 독자를 오도.

### 옵션 2: co-agent용 ADR-008 작성 + ADR-003 대체

- **장점**: 실구현 결정(멀티 AI 패널: Kiro/Codex/Gemini 병렬 fan-out, Claude 의장 종합)을 기록하고, co-agent의 ADR 공백을 메우며, ADR-003의 슬래시 명령 접근을 `Superseded by` 링크로 정리. ADR-003은 불변 시점 기록으로 보존.
- **단점**: ADR 추가. ADR-003의 외부 플러그인은 대화형 용도로는 여전히 설치 가능하므로, 대체는 *접근 방식*의 대체이지 전면 금지는 아님.

## 결정

옵션 2 채택. 마켓플레이스의 리뷰/의사결정/ADR 공동작성 메커니즘은 자체 `co-agent` 플러그인(1 agent, 1 skill, 2 commands)이며 네 가지 모드(Review, Decide, ADR, sync-context)를 가집니다. 설치된 AI CLI(Kiro `kiro-cli chat --no-interactive`, Codex `codex exec -s read-only`, Gemini `gemini -p … -o text`)에 동일 프롬프트를 병렬 fan-out한 뒤 **Claude가 의장으로 종합**(합의 vs 이견)합니다. 외부 CLI가 없으면 Claude 단독 답변으로 graceful degrade합니다.

이는 외부 `kiro-cli-plugin`의 대화형 `/kiro-cli:*` 명령에 의존하기로 한 ADR-003의 결정을 대체합니다. Kiro는 패널 멤버로 남되, 대화형 플러그인 명령이 아닌 headless `kiro-cli chat` 경로로 참여합니다.

## 영향

### 긍정적

- 실제 출시된 리뷰 메커니즘이 결정으로 기록됨.
- Kiro 단독이던 ADR-003 리뷰를 Kiro/Codex/Gemini 교차 벤더 다양성으로 일반화.
- Graceful degradation: 단일 외부 CLI에 대한 강한 의존 없음.
- ADR-003은 상태/링크 갱신 외 원문 보존 — 불변성 준수.

### 부정적

- ADR 로그에 항목 추가.
- ADR-003의 외부 `kiro-cli-plugin`은 더 이상 주 경로가 아니므로, 대화형 슬래시 명령에 의존하던 경우 `co-agent` 전환 또는 플러그인 단독 사용 필요.

## 참고 자료

- `plugins/co-agent/` — 본 ADR이 기록하는 플러그인
- `plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md` — headless 어댑터 구문, `/kiro-cli:*` 자동 fan-out 비사용 명시
- ADR-003: Kiro CLI 심층 리뷰 — 본 ADR로 대체됨
