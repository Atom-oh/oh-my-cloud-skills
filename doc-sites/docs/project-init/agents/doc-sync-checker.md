---
sidebar_position: 1
title: "Doc sync checker"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="doc-sync-checker-agent" />
<span id="기능" />
<span id="사용-방법" />
<span id="출력-형식" />


# Doc sync checker

Analyze whether project instructions and documentation match current code, commands, dependencies, and architecture. The checker detects missing module context, stale references, undocumented decisions, and quality gaps.

## Use

Run the project-init `sync-docs` workflow, or request a scoped documentation audit. Supply the relevant source paths and intended language. The checker produces evidence and proposed updates; its report is not proof that changes were applied or tested.

## Report

Identify the affected document, supporting source path, mismatch, and concrete correction. Assess command usability, architectural clarity, conciseness, freshness, and actionability. Use the current rubric from the agent rather than treating an old score as a permanent gate.

[Checker definition](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/project-init/agents/doc-sync-checker.md)
