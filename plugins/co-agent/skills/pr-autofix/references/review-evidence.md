# Review evidence for the current HEAD

Read this before judging a review result. `REPO`, `PR_NUMBER` and the loop state
come from the entry skill; resolve shell variables in the tool call that uses them.

**AI review.** The marker rides in as DATA via `jq --arg`, never interpolated into the
filter string, and the author check pins the verdict to the CI's own
`github-actions[bot]` comments — a user-authored comment containing the marker text can
never be mistaken for, or override, the CI verdict:

```bash
MARKER=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py" pr-autofix-marker)
REVIEW_COMMENT="$STATE_DIR/review-comment.tmp.json"
AI_REVIEW_FILTER='[ .[] | select(.user.login == "github-actions[bot]") |
                     select(if $m == "" then (.body | test("<!--\\s*[a-z0-9-]*pr-review\\s*-->"))
                            else (.body | contains($m)) end) ] | sort_by(.updated_at) | last |
                     select(. != null) | {id, author: .user.login, updated_at, body}'
set -o pipefail
gh api --paginate --slurp "repos/${REPO}/issues/${PR_NUMBER}/comments" |
  jq --arg m "$MARKER" "add | $AI_REVIEW_FILTER" > "$REVIEW_COMMENT" \
  || { echo "review retrieval failed"; exit 1; }
```

The configured workflow's machine verdict is its first unquoted, top-level
`**Status: PASSED**`, `**Status: BLOCKED**` or `**Status: ERROR**` line outside code
fences. Inline examples and blockquotes are not native verdicts. The bundled
parser enforces this grammar after the author/marker check:

```bash
if [ -s "$REVIEW_COMMENT" ]; then
  AI_VERDICT=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/pr-autofix/scripts/review_verdict.py" "$REVIEW_COMMENT") || exit 1
else
  AI_VERDICT=UNBOUND
fi
printf '%s\n' "$AI_VERDICT"
```

`BLOCKED` remains blocking even if the host disputes a finding; seek an updated
review or the provider's documented resolution. `PASSED` is necessary, not
sufficient: check commit/scope binding, required coverage, CI and unresolved
Critical/Major findings too. `ERROR` cannot pass. An absent or unbindable result
is `UNBOUND`, not `NOT_REQUIRED`; if it cannot be recovered, record the specific
`review_unavailable` blocker. Other providers need their documented equivalent
verdict and authenticated author/run identity.

Bind evidence to the current **exact `headRefOid`** using the CI footer
`Triggered by commit <full SHA>`, a provider `commit_id` or a bound check run.
`updated_at` alone is insufficient: old runs can finish after a newer push.

```bash
gh pr view "$PR_NUMBER" --json state,headRefOid,baseRefName,baseRefOid,statusCheckRollup,reviewDecision,mergeStateStatus,mergeable,mergeCommit
gh api --paginate "repos/${REPO}/pulls/${PR_NUMBER}/reviews"
gh api --paginate "repos/${REPO}/pulls/${PR_NUMBER}/comments"
```

Check inline findings too, including unresolved earlier findings against the
current code. A summary alone does not establish that they were fixed. Capture
the reviewed HEAD, base commit/ref, diff identity and covered scope, check/run
identity and required coverage in the single `review` checkpoint defined in
`review-state.md`. Any new push invalidates the
previous pass result. A base retarget can also change the diff with the same HEAD;
compare that delta with the recorded review scope before retaining a pass result.

**Human review.** Use the reviews and inline comments from the pulls API above.
Review history is not the current decision: a later approval can resolve the same
reviewer's earlier change request, and a dismissed review is not active. Use each
reviewer's latest effective state and GitHub's branch-protection decision; apply
its stale-approval rules after a new commit.

Use the PR-level `reviewDecision`, `mergeStateStatus` and `mergeable` returned
above for GitHub's effective gate state. `REVIEW_REQUIRED` and
`CHANGES_REQUESTED` cannot be treated as approval; `UNKNOWN` must be rechecked.
Do not interpret a permissions-related 404 from a branch-protection endpoint
as "no rules." A null `reviewDecision` alone is not a `NOT_REQUIRED` basis.
Combine the effective PR state with the user's task, project instructions and
configured review sources. For example, a human-feedback-only task in a repo
with no AI-review requirement or configuration can record AI as `NOT_REQUIRED`;
the same absent configuration is a blocker when the task requires AI review.

For still-live checks, retain their provider identifiers. GitHub Actions run
identifiers for the current commit can be queried with:

```bash
HEAD_SHA=$(gh pr view "$PR_NUMBER" --json headRefOid --jq '.headRefOid')
gh run list --commit "$HEAD_SHA" --json databaseId,workflowName,headSha,status,conclusion,createdAt
```

Query saved handles again before starting a new run. Current observations and
host-established requirement bases are written through the atomic checkpoint
in `review-state.md`; scratch query results are not independent loop state.
