---
sidebar_position: 1
title: "co-agent roles"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="트리거-키워드" />
<span id="핵심-역량" />
<span id="모드-라우팅" />
<span id="패널-감지-항상-step-0" />
<span id="의장-원칙-chair-principle-non-negotiable" />
<span id="다른-에이전트와의-연계" />
<span id="참고-파일" />
<span id="co-agent-agent" />
<span id="co-agent-에이전트" />


# co-agent roles

The canonical `/co-agent` skill runs orchestration in the current host. It handles
explicit multi-AI review, decision support and ADR collaboration, and routes context
synchronization, consensus and harness to their procedures. Setup remains a separate
readiness command. The host synthesizes the result and owns the final decision;
there is no separate `co-agent` orchestrator agent. This page retains its old address
for existing links.

## Routing and evidence {#routing-and-evidence}

Start with peer detection and the mode's readiness rules. Casual review/decide/ADR can use available peers or proceed solo with notice; consensus and harness require READY coverage. Use identical review context where comparison matters, record errors, and verify each material finding against the repository.

The host surfaces disagreements and attributes useful observations. It never substitutes vote counts for technical validation. Context sent to peers must pass the workflow's freshness and secret checks.

## Related workers {#related-workers}

Three agents remain because their capabilities are different:

| Agent | Responsibility and boundary |
| --- | --- |
| `gate-chair` | Verify findings, write the curated digest and judge verify rounds; no external AI fan-out, commits or configuration writes |
| `pr-autofix-planner` | Turn prepared feedback and constraints into a structured fix plan using read-only tools; never edit |
| `pr-autofix-implementer` | Apply approved plan items in an isolated worktree using edit-only tools; no Bash/network, verification and integration remain with the host |

The planner and implementer require inputs prepared by PR autofix, not bare user
requests. On Codex these entries supply procedures, not native roles or permission
grants; actual host capabilities must enforce the boundaries. Decision reconcile's
four dynamic review lenses remain unchanged and are not extra registered agents.
Project-init can write the resulting ADR; AWS specialists supply domain evidence
when the subject warrants it.

## Migration from retired agents {#retired-agent-migration}

| Retired invocation | Replacement |
| --- | --- |
| Native `co-agent:co-agent` agent | `/co-agent` skill in the current host; the existing Codex `co-agent` entry remains |
| `harness-analyst` agent or entry | `/co-agent:configure analyze [session-dir]` |

Analysis reads harness/consensus records and proposes configuration changes without
applying them. With fewer than three recorded runs, it reports observations only;
count runs by plan-gate records rather than individual stage rows. Applying any
proposal is a separate, authorized action.

Using the skill no longer forces the retired wrapper's `opus`/`xhigh` settings or
creates its user-scoped agent memory. It runs with the current host's model and
reasoning configuration; retained workers keep their own assignments. Existing
retired-agent memory is not moved or deleted, and is not automatically loaded by
the replacement procedures. Transfer only reviewed, relevant distilled observations
when needed; never blindly copy memory into shared context.

[Canonical skill](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/SKILL.md) · [Configuration procedure](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/configure.md) · [Codex entry point](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/.codex-plugin/skills/co-agent/SKILL.md)
