# ADR-009: agentcore-creator as-built — brainstorm-first 5-phase workflow

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status

Accepted (2026-06-11) — Supersedes ADR-004

## Context

ADR-004 proposed an `agentcore-creator` plugin to convert Claude Code plugins into Amazon Bedrock AgentCore deployments, specifying a **9-phase conversion workflow** (Source Selection → Plugin Discovery → Target Mapping → Conversion Options → Artifact Generation → Refinement → Deployment → Verification → Next Steps) and remained marked **Proposed / 제안됨**.

The plugin has since shipped, but the as-built design diverged from the proposal on two material points, and the ADR was never advanced:

1. **Status drift (C3):** `agentcore-creator` is registered in `marketplace.json`, ships all four reference files plus `convert_plugin_to_agentcore.py`, and is documented in the root `CLAUDE.md` as a live plugin (`/agentcore-create`) — yet ADR-004 still reads "Proposed".
2. **Design drift (C3):** the implemented `SKILL.md` is an **Interactive 5-phase workflow** — Discovery → Design → Skill-First Build → AgentCore Convert → Deploy — that starts from brainstorming and builds a Claude Code skill first, rather than the proposed pure 9-phase converter. The pivot (brainstorm-/skill-first, then convert) is a genuine change of decision, not a stale enumeration.

Flipping ADR-004 to "Accepted" would falsely assert that the 9-phase design shipped; it did not. Per ADR immutability, the proposal is preserved and superseded.

## Options Considered

### Option 1: Edit ADR-004 in place (flip to Accepted, rewrite to 5 phases)

- **Pros**: One file.
- **Cons**: Destroys the point-in-time record and retroactively blesses a design that was never built. Violates ADR immutability.

### Option 2: Author ADR-009 recording the as-built design and supersede ADR-004

- **Pros**: Preserves ADR-004 as the original proposal; records the actual 5-phase brainstorm-/skill-first workflow; provides a clean `Superseded by` link; captures the known MCP tool-name follow-up.
- **Cons**: Adds an ADR.

## Decision

Adopt Option 2. The as-built `agentcore-creator` uses an **interactive 5-phase workflow**: (1) Discovery — brainstorm agent requirements; (2) Design — component/architecture design with explicit user approval gates; (3) Skill-First Build — build the capability as a Claude Code skill first; (4) AgentCore Convert — map and generate deployment artifacts; (5) Deploy — AWS CLI deployment with per-step confirmation. Direct `convert <path>` invocations skip Phases 1–3 and enter at Phase 4.

This supersedes ADR-004's proposed 9-phase converter design and advances the decision to Accepted as embodied by the shipped plugin.

### Known follow-up (recorded, not resolved here)

The plugin's docs and `convert_plugin_to_agentcore.py` reference AgentCore MCP tools named `manage_agentcore_runtime` / `manage_agentcore_gateway` / `manage_agentcore_memory`. The actual MCP server exposes `create_agent_runtime`, `gateway_create`/`gateway_target_create`, `memory_create`, etc. — there is no `manage_agentcore_*` tool. This naming mismatch is an implementation error (consistent between ADR-004 and code, so not an ADR-vs-code drift) and is tracked as a separate, test-worthy code change, out of scope for this reconciliation.

## Consequences

### Positive

- The shipped 5-phase, skill-first design is recorded as the accepted decision.
- ADR-004 preserved unedited except for a status/link update — immutability respected.
- The MCP tool-name defect is captured so it is not lost.

### Negative

- Adds an ADR.
- The MCP tool-name fix remains outstanding until the follow-up change lands.

## References

- `plugins/agentcore-creator/skills/agentcore-create/SKILL.md` — the as-built 5-phase workflow
- `.claude-plugin/marketplace.json`, root `CLAUDE.md` — evidence the plugin shipped
- ADR-004: AgentCore Creator Skill — superseded by this ADR

---

<a id="korean"></a>

# 한국어

## 상태

승인됨 (2026-06-11) — ADR-004를 대체함 (Superseded by ADR-009 표기는 영문 섹션 참조)

## 배경

ADR-004는 Claude Code 플러그인을 Amazon Bedrock AgentCore 배포로 변환하는 `agentcore-creator` 플러그인을 제안하며 **9단계 변환 워크플로우**(소스 선택 → 플러그인 탐색 → 타겟 매핑 → 변환 옵션 → 아티팩트 생성 → 고도화 → 배포 → 검증 → 후속 안내)를 명시했고 **제안됨(Proposed)** 상태로 남아 있었습니다.

이후 플러그인은 출시되었으나 실제 구현이 제안과 두 가지 중요한 지점에서 갈라졌고 ADR은 갱신되지 않았습니다:

1. **상태 drift (C3):** `agentcore-creator`는 `marketplace.json`에 등록되고 4개 레퍼런스 파일과 `convert_plugin_to_agentcore.py`를 모두 출시했으며 루트 `CLAUDE.md`에 출시 플러그인(`/agentcore-create`)으로 문서화돼 있으나, ADR-004는 여전히 "제안됨"입니다.
2. **설계 drift (C3):** 구현된 `SKILL.md`는 브레인스토밍에서 시작해 Claude Code 스킬을 먼저 빌드하는 **대화형 5단계 워크플로우**(Discovery → Design → Skill-First Build → AgentCore Convert → Deploy)입니다. 이 전환(스킬 우선 후 변환)은 부수적 열거가 아니라 결정의 실질적 변경입니다.

ADR-004를 "승인됨"으로 바꾸면 9단계 설계가 출시된 것처럼 거짓 주장이 됩니다. ADR 불변성에 따라 제안은 보존하고 대체합니다.

## 검토한 옵션

### 옵션 1: ADR-004 원본 수정 (승인됨으로 전환, 5단계로 재작성)

- **장점**: 단일 파일.
- **단점**: 시점 기록 파괴, 빌드된 적 없는 설계를 소급 승인. 불변성 위반.

### 옵션 2: 실구현을 기록하는 ADR-009 작성 + ADR-004 대체

- **장점**: ADR-004를 원 제안으로 보존, 실제 5단계 스킬 우선 워크플로우 기록, 깔끔한 `Superseded by` 링크, MCP 도구명 후속 과제 포착.
- **단점**: ADR 추가.

## 결정

옵션 2 채택. 실구현 `agentcore-creator`는 **대화형 5단계 워크플로우**를 사용합니다: (1) Discovery — 에이전트 요구사항 브레인스토밍; (2) Design — 사용자 승인 게이트가 있는 컴포넌트/아키텍처 설계; (3) Skill-First Build — 기능을 먼저 Claude Code 스킬로 빌드; (4) AgentCore Convert — 매핑 및 배포 아티팩트 생성; (5) Deploy — 단계별 확인과 함께 AWS CLI 배포. 직접 `convert <path>` 호출은 Phase 1–3을 건너뛰고 Phase 4로 진입합니다.

이는 ADR-004의 제안된 9단계 변환기 설계를 대체하며, 출시된 플러그인으로 구현된 결정을 승인됨으로 진전시킵니다.

### 알려진 후속 과제 (여기서 기록만, 해결 아님)

플러그인 문서와 `convert_plugin_to_agentcore.py`는 AgentCore MCP 도구를 `manage_agentcore_runtime` / `manage_agentcore_gateway` / `manage_agentcore_memory`로 참조합니다. 실제 MCP 서버는 `create_agent_runtime`, `gateway_create`/`gateway_target_create`, `memory_create` 등을 노출하며 `manage_agentcore_*` 도구는 존재하지 않습니다. 이 명칭 불일치는 구현 오류(ADR-004와 코드가 서로 일치하므로 ADR-vs-코드 drift가 아님)이며, 별도의 테스트 가능한 코드 변경으로 추적되고 본 화해의 범위 밖입니다.

## 영향

### 긍정적

- 출시된 5단계 스킬 우선 설계가 승인된 결정으로 기록됨.
- ADR-004는 상태/링크 갱신 외 원문 보존 — 불변성 준수.
- MCP 도구명 결함이 유실되지 않도록 포착됨.

### 부정적

- ADR 추가.
- MCP 도구명 수정은 후속 변경이 반영될 때까지 미해결로 남음.

## 참고 자료

- `plugins/agentcore-creator/skills/agentcore-create/SKILL.md` — 실구현 5단계 워크플로우
- `.claude-plugin/marketplace.json`, 루트 `CLAUDE.md` — 플러그인 출시 증거
- ADR-004: AgentCore Creator Skill — 본 ADR로 대체됨
