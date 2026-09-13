---
sidebar_position: 3
title: "Decision reconcile"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="decision-reconcile-skill" />
<span id="핵심-아이디어--다양성-패널" />
<span id="검출하는-모순-유형" />
<span id="리뷰-렌즈-에이전트별-1개" />
<span id="워크플로우" />
<span id="종합-원칙" />
<span id="산출물--번복superseding-adr" />
<span id="스크립트" />
<span id="collect_adrspy" />
<span id="제약--주의" />
<span id="레퍼런스" />


# Decision reconcile

Review accumulated ADRs for contradictions with other decisions or with the current repository, then draft a superseding ADR backed by evidence.

## What it checks {#what-it-checks}

Look for incompatible technology choices, conflicting scope or constraints, outdated assumptions, decisions that drifted from implementation, and dependency chains invalidated by a later decision. The panel assigns different review lenses so agreement is not just repeated phrasing.

## Workflow {#workflow}

Collect ADRs and their status; trace referenced code and configuration; ask the available review panel for independent concerns; validate each claim; then present the contradictions and options. The host synthesizes the result rather than counting votes.

A superseding ADR identifies the replaced decision, explains the new evidence, records alternatives and consequences, and links both directions. Preserve historical ADRs instead of silently rewriting the record. Do not execute migrations merely because an ADR proposes one.

## Tooling and boundaries {#tooling-and-boundaries}

External peer fan-out sends the selected ADR text to third-party AI services and
requires consent for that scope. The [skill contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/decision-reconcile/SKILL.md)
defines that boundary.

`collect_adrs.py` builds the ADR input set. Source checks distinguish direct contradictions from intentional exceptions or decisions with different scopes. External peer availability and failures must be disclosed.

[Skill and reference contracts](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/decision-reconcile/SKILL.md)
