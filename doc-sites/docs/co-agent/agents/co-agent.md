---
sidebar_position: 1
title: "co-agent agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="트리거-키워드" />
<span id="핵심-역량" />
<span id="모드-라우팅" />
<span id="패널-감지-항상-step-0" />
<span id="의장-원칙-chair-principle-non-negotiable" />
<span id="다른-에이전트와의-연계" />
<span id="참고-파일" />


# co-agent agent

The co-agent orchestrator dispatches explicit multi-AI review, decision support, ADR collaboration, context synchronization, consensus, harness, and readiness checks. The current host synthesizes the result and owns the final decision.

## Routing and evidence {#routing-and-evidence}

Start with peer detection and the mode's readiness rules. Casual review/decide/ADR can use available peers or proceed solo with notice; consensus and harness require READY coverage. Use identical review context where comparison matters, record errors, and verify each material finding against the repository.

The host surfaces disagreements and attributes useful observations. It never substitutes vote counts for technical validation. Context sent to peers must pass the workflow's freshness and secret checks.

## Related workers {#related-workers}

`gate-chair` isolates triage and verification decisions. `harness-analyst` proposes configuration improvements from run records without applying them. PR autofix prepares bounded input for its planner and implementer workers. Project-init can write the resulting ADR; AWS specialists supply domain evidence when the subject warrants it.

[Agent contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/agents/co-agent.md) · [Codex entry point](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/.codex-plugin/skills/co-agent/SKILL.md)
