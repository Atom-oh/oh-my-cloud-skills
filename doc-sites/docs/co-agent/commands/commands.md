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

Optional hook gates default off; required CI and branch protection remain independent.
Enabling `pr_gate` or `push_gate` is consent to send the reviewed diff to third-party
peer services. A git-tracked `.claude/co-agent.local.json` cannot enable either gate;
see the [configuration contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/configure.md).

## /co-agent:sync-context

Generate marked AGENTS.md from CLAUDE.md and wire the Kiro steering bridge. Source hashes identify stale generated context; handwritten unmarked files are protected. Antigravity is no longer a co-agent peer.

## /co-agent:consensus

Run the document-to-plan-to-implementation workflow. The host implements; peers review the plan and final diff. A READY peer is mandatory, and the pipeline uses configured round/call budgets and persisted run state.

## /co-agent:harness

The host designs, owns tests, reviews captured changes, and commits. An eligible
READY peer implements in isolated worktrees. If none is available, explicitly select
an authorized host plan with `--allow-host-implementation`. An enabled, fresh READY
raw-CLI reviewer is mandatory in either mode. Configuration or readiness errors
stop planning. Kiro is excluded as an external implementer. Exact role and mode
rules are in the [harness contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/harness.md).

## /co-agent:setup

Detect plugin and CLI access paths, probe actual usability, and write readiness results. Authentication and model-call failures are actionable setup failures, not successful review coverage.

## /co-agent:pr-autofix

Poll review feedback, plan verified fixes, apply them in an isolated worktree, validate, commit, and push within the configured iteration limit. Recheck the new HEAD's reviews and CI; follow the repository's authorization and merge rules.

Set up the consumer's review workflow and paired gate helper first. The loop never
edits `.github/workflows/*`; see [PR autofix setup and boundaries](/docs/co-agent/skills/pr-autofix#limits-and-integration).

In Codex these command workflows are generated skill entries. Select the matching installed entry rather than assuming Claude command registration is shared.
