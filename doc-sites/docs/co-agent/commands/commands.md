---
sidebar_position: 1
title: "co-agent commands"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="co-agent-명령" />
<span id="push_gate--pr_autofix-설정-추가분" />


# co-agent commands

## /co-agent:configure

Show merged settings and their origins. Configure peer models, profiles, effort where supported by the adapter, enablement, timeouts, context budgets, autosync, harness limits, PR autofix iterations, and optional PR/push gates.

```text
/co-agent:configure
/co-agent:configure set autosync on
/co-agent:configure set pr_autofix max_iterations 5
```

[Defaults and exact keys](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/co-agent.defaults.json)

Optional hook gates default off; required CI and branch protection remain independently enforced.

## /co-agent:sync-context

Generate marked AGENTS.md from CLAUDE.md and wire the Kiro steering bridge. Source hashes identify stale generated context; handwritten unmarked files are protected. Agy context is folded into peer input only after validation.

## /co-agent:consensus

Run the document-to-plan-to-implementation workflow. The host implements; peers review the plan and final diff. A READY peer is mandatory, and the pipeline uses configured round/call budgets and persisted run state.

## /co-agent:harness

The host designs, owns tests, reviews captured changes, and commits. An eligible cross-provider peer implements in isolated worktrees. Model/effort overrides and task parallelism come from harness configuration. Kiro is excluded as a harness implementer.

## /co-agent:setup

Detect plugin and CLI access paths, probe actual usability, and write readiness results. Authentication and model-call failures are actionable setup failures, not successful review coverage.

## /co-agent:pr-autofix

Poll review feedback, plan verified fixes, apply them in an isolated worktree, validate, commit, and push within the configured iteration limit. Recheck the new HEAD's reviews and CI; follow the repository's authorization and merge rules.

In Codex these command workflows are generated skill entries. Select the matching installed entry rather than assuming Claude command registration is shared.
