# ADR-008: superpowers x oh-my-cloud-skills Integration Routing

## Status

Accepted (2026-06-17)

## Context

When the `superpowers` workflow plugin (lifecycle skills such as brainstorming / writing-plans /
systematic-debugging / finishing-a-development-branch / requesting-code-review) is installed
alongside this marketplace, work needs to be handed off at the appropriate phase to our
marketplace's domain-specialist plugins (aws-ops / aws-content / project-init / co-agent).
However, since `superpowers` is **read-only** (we do not modify it), the integration routing
must be managed by **our own convention**, not by superpowers itself.

## Options Considered

1. **Fork/modify the superpowers skills to insert routing** — breaks upstream tracking, violates the read-only principle.
2. **An authoritative routing table in the root CLAUDE.md + detail in each plugin's CLAUDE.md** — leave superpowers
   untouched and always keep "what to call at which phase" explicit in our own always-in-context documentation. (Adopted)

## Decision

Treat the **"superpowers Integration Routing"** table in the root `CLAUDE.md` as the single
source of authority, and route by phase as follows:

- **systematic-debugging** + AWS/EKS symptom → `aws-ops`: `ops-troubleshoot` or the matched domain agent (① active)
- **finishing-a-development-branch** → `project-init`: `/sync-docs` + `/generate-changelog` (+ `/add-adr` if a decision was made) (②)
- **requesting-code-review** + non-code artifact/IaC → `aws-content`: `content-review-agent`; IaC → `aws-ops`: `wellarchitected-agent` + `ops-security-audit` (③)
- **writing-plans** + AWS/IaC change → AWS security mandate shift-left pre-check (`ops-security-audit`) (④)

`co-agent:consensus` separately reuses `superpowers:subagent-driven-development` + the
writing-plans output, but verifies it through the multi-AI panel gate.

## Consequences

- Combines superpowers' methodology with our domain commands — superpowers provides the method, we provide domain execution.
- `superpowers` remains unmodified (upstream-compatible).
- The routing is a **recommended convention**, not an enforced hook (superpowers provides no such hook) — the risk of omission is mitigated through documentation.

## References

- Root `CLAUDE.md` — "superpowers Integration Routing" table
- `docs/superpowers/specs/2026-06-14-superpowers-integration-design.md`
- `plugins/aws-ops-plugin/CLAUDE.md`, `plugins/project-init/CLAUDE.md` — superpowers Handoff sections
- Related decisions: ADR-009 (multi-AI PR review CI panel), ADR-010 (Antigravity/Gemini precedence)
- PR #74
