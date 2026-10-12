---
name: pr-status
description: Report a pull request's CI checks and AI review result as text — "pr status", "PR 상태", "리뷰 결과 확인", "CI 상태". Read-only; use when the pr-dash pane is unavailable (Codex, VS Code chat panel, claude -p) or the user wants the status in the conversation.
allowed-tools:
  - Bash(gh pr view:*)
  - Bash(gh auth status:*)
---

# PR status

Report the current state of one pull request without changing it. This is the text
form of the pr-dash pane: Codex, the VS Code chat panel and `claude -p` cannot draw a
mod's pane, so this procedure gives the same facts in the conversation.

## Workflow

Pick the PR → fetch one JSON snapshot → classify checks → read the trusted review
comment → report. Each step uses only the snapshot from step 1.

### Step 1: Fetch the snapshot

Use the number the user named; otherwise omit it to target the current branch's PR.

```bash
gh pr view [<number>] --json number,title,url,state,headRefOid,headRefName,baseRefName,mergeable,statusCheckRollup,comments
```

If `gh` is missing or unauthenticated (`gh auth status` fails), or it reports no pull
request for the branch, say so and stop. Do not guess a PR number.

### Step 2: Classify each check

| Entry type | Field values | Result |
|---|---|---|
| `CheckRun` | `status` not `COMPLETED` | pending |
| `CheckRun` | `COMPLETED` with `conclusion` `SUCCESS` or `NEUTRAL` | pass |
| `CheckRun` | `COMPLETED` with `conclusion` `SKIPPED` | skipped |
| `CheckRun` | `COMPLETED` with any other `conclusion` | fail |
| `StatusContext` | `state` `SUCCESS` / `PENDING` or `EXPECTED` / other | pass / pending / fail |

### Step 3: Read the AI review

Apply the trust rules in
[references/review-comment-format.md](references/review-comment-format.md): only the
newest bot-authored comment with the review marker counts, and only its first
visible `**Status: …**` line. Record the status, the reviewed commit and each
list item (`-`, `+`, `*`, `1.` or `1)`) under `### CRITICAL`, `### MAJOR` and
`### MINOR`.

## Output format

Report in this order, one line each unless a list is needed:

```text
PR #253 · OPEN · fix/x → main · head 4248c37
Checks: 3/3 pass  (AI Code Review ✓ · Codex package validation ✓ · Documentation site validation ✓)
Review: PASSED for the current head · C0 M0 m0
Links: <PR url> · <review comment url>
```

List each finding as `[MAJOR] <title>` below the review line. Write "review stale"
when the reviewed commit is not the head, and "no review comment yet" when none
qualifies. State that the report is informational and CI remains the merge gate.

## Boundaries

- Read-only. Do not merge, push, re-run workflows, comment or approve.
- When the user wants findings fixed, hand off to co-agent's `pr-autofix` skill.
  When they want to merge, follow the repository's merge rules with a fresh HEAD,
  check and review verification; this report is not that verification.
