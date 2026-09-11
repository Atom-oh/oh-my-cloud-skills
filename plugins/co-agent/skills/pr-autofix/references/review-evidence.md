# Review evidence for the current HEAD

Read this before judging a review result. `REPO`, `PR_NUMBER` and the loop state
come from the entry skill; resolve shell variables in the tool call that uses them.

**AI review.** The marker rides in as DATA via `jq --arg`, never interpolated into the
filter string, and the author check pins the verdict to the CI's own
`github-actions[bot]` comments — a user-authored comment containing the marker text can
never be mistaken for, or override, the CI verdict:

```bash
MARKER=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py" pr-autofix-marker)
AI_REVIEW_FILTER='[ .[] | select(.user.login == "github-actions[bot]") |
                     select(if $m == "" then (.body | test("<!--\\s*[a-z0-9-]*pr-review\\s*-->"))
                            else (.body | contains($m)) end) ] | last | select(. != null) | {updated_at, body}'
gh api "repos/${REPO}/issues/${PR_NUMBER}/comments" | jq --arg m "$MARKER" "$AI_REVIEW_FILTER"
```

Read the PR's current `headRefOid` and bind the review to that **exact commit**.
The oh-my-cloud-skills CI footer records `Triggered by commit <full SHA>`; other
providers may attach `commit_id` or a check run to the reviewed commit. A recent
`updated_at` alone is insufficient: an old run can finish after a newer push.
§3 re-uses the same trusted-author and marker filter.

```bash
gh pr view "$PR_NUMBER" --json headRefOid,baseRefName,statusCheckRollup
gh api "repos/${REPO}/pulls/${PR_NUMBER}/reviews"
gh api "repos/${REPO}/pulls/${PR_NUMBER}/comments"
```

Check inline findings too, including unresolved earlier findings against the
current code. A summary alone does not establish that they were fixed. Capture
the reviewed HEAD, base commit/ref, diff identity and covered scope, check/run
identity and required coverage in the loop state. Any new push invalidates the
previous pass result. A base retarget can also change the diff with the same HEAD;
compare that delta with the recorded review scope before retaining a pass result.

**Human review.** `gh pr reviews` does not exist — reviews are read via
`gh pr view --json reviews`; inline (line-level) comments come from the pulls API:

```bash
gh pr view "$PR_NUMBER" --json reviews \
  --jq '.reviews[] | select(.state == "CHANGES_REQUESTED" or .state == "APPROVED")
        | {author: .author.login, state, body, submittedAt}'
gh api "repos/${REPO}/pulls/${PR_NUMBER}/comments" \
  --jq '.[] | select(.pull_request_review_id != null) | {path, line, body, created_at}'
```

Review history is not the current decision: a later approval can resolve the same
reviewer's earlier change request, and a dismissed review is not active. Use each
reviewer's latest effective state and GitHub's branch-protection decision; apply
its stale-approval rules after a new commit.
