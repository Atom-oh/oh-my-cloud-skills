# ADR-008: superpowers ⨯ oh-my-cloud-skills Integration Routing

## Status

Accepted (2026-06-17)

## Context

`superpowers` 워크플로우 플러그인(brainstorming / writing-plans / systematic-debugging /
finishing-a-development-branch / requesting-code-review 등 생명주기 스킬)이 함께 설치되면,
그 단계에서 우리 마켓플레이스의 도메인 전문 플러그인(aws-ops / aws-content / project-init /
co-agent)으로 작업을 넘겨야 한다. 그러나 `superpowers`는 **read-only**(우리가 수정하지 않음)
이므로, 통합 라우팅을 superpowers 쪽이 아니라 **우리 쪽 규약**으로 관리해야 한다.

## Options Considered

1. **superpowers 스킬을 fork/수정해 라우팅 삽입** — 업스트림 추적 불가, read-only 원칙 위반.
2. **루트 CLAUDE.md에 authoritative 라우팅 표 + 각 플러그인 CLAUDE.md에 상세** — superpowers는
   그대로 두고 우리 쪽에서 "어느 단계에 무엇을 호출하는지"를 항상-컨텍스트로 명시. (채택)

## Decision

루트 `CLAUDE.md`의 **"superpowers Integration Routing"** 표를 단일 권위 소스로 두고, 단계별로
다음과 같이 라우팅한다:

- **systematic-debugging** + AWS/EKS 증상 → `aws-ops`: `ops-troubleshoot` 또는 매칭 도메인 에이전트 (① active)
- **finishing-a-development-branch** → `project-init`: `/sync-docs` + `/generate-changelog` (+ 결정 시 `/add-adr`) (②)
- **requesting-code-review** + 비코드 산출물/IaC → `aws-content`: `content-review-agent`; IaC → `aws-ops`: `wellarchitected-agent` + `ops-security-audit` (③)
- **writing-plans** + AWS/IaC 변경 → AWS 보안 mandate shift-left 사전점검(`ops-security-audit`) (④)

`co-agent:consensus`는 별도로 `superpowers:subagent-driven-development` + writing-plans 출력을
재사용하되 멀티-AI 패널 게이트로 검증한다.

## Consequences

- superpowers의 방법론 + 우리의 도메인 명령을 결합 — 방법은 superpowers가, 도메인 실행은 우리가 제공.
- `superpowers`는 미수정 유지(업스트림 호환).
- 라우팅은 강제 훅이 아닌 **권장 규약**(superpowers가 그런 훅을 제공하지 않음) — 누락 가능성은 문서로 완화.

## References

- 루트 `CLAUDE.md` — "superpowers Integration Routing" 표
- `docs/superpowers/specs/2026-06-14-superpowers-integration-design.md`
- `plugins/aws-ops-plugin/CLAUDE.md`, `plugins/project-init/CLAUDE.md` — superpowers Handoff 섹션
- PR #74
