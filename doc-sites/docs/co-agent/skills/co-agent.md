---
sidebar_position: 1
title: "co-agent skill"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="트리거" />
<span id="step-0-패널-감지-항상-먼저" />
<span id="ai-cli-어댑터-read-only-자문" />
<span id="모드-1--review" />
<span id="모드-2--decide-잘-모르겠어--의사결정" />
<span id="모드-3--adr-협업" />
<span id="모드-4--sync-context-ai-컨텍스트-동기화" />
<span id="모드-5--consensus-자율-docplan구현-파이프라인" />
<span id="모드-6--harness-host-설계--peer-구현--패널-리뷰" />
<span id="모드-7--setup-패널-준비도-preflight" />
<span id="의장-원칙" />


# co-agent skill

Invoke this skill explicitly for a second opinion, multi-AI review, collaborative decision, or ADR. A plain code-review request does not automatically request external peer calls.

## Workflow {#workflow}

1. Determine the current host, requested mode, available peers, and validated context.
2. Run or consult setup probes; record missing CLIs, authentication failures, timeouts, and input limits.
3. Dispatch review/decide/ADR to available peers, or report solo operation. For consensus/harness, require READY coverage before continuing.
4. Check findings against source, surface disagreements, and return a host-authored result with verification evidence.

## Mode contracts {#mode-contracts}

The skill has six modes. Review inspects a defined diff or scope. Decide compares
explicit options. ADR gathers alternatives and consequences. Sync-context generates
shared instructions. Consensus lets the host implement behind review gates. Harness
uses an eligible READY peer, or an explicitly selected, authorized host plan when
no eligible writer is available. Host mode uses `--allow-host-implementation`;
configuration and readiness errors must be repaired before proceeding. An enabled,
fresh READY raw-CLI reviewer remains mandatory, and the host owns tests and commits.

`/co-agent:setup` is a separate command that measures readiness with real calls.

Peer adapter commands, input handling, model selection, and sandbox behavior are defined in the installed skill and its references. Inspect those rather than assuming that a CLI trust flag means filesystem confinement.

[Full skill contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/SKILL.md)
