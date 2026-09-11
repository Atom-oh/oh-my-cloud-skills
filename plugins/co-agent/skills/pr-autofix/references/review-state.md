# Review-loop state and checkpoints

Resolve the PR in Step 1 first. Initialize or migrate the single host-owned state
file before polling. This state controls review/fix/push only; it never grants merge
authorization or performs retarget/merge actions.

**Git is the repair source, not the truth.** On every Poll entry, cross-check
`iteration` against the git-derived count; on mismatch, adopt the git value and warn.
Use the PR's actual base — a hardcoded `origin/main` fails silently into `0` on a
`master`/`develop`/unfetched base, disabling every threshold including the `max_iter`
stop:

```bash
BASE_REF=$(gh pr view "$PR_NUMBER" --json baseRefName --jq '.baseRefName')
GIT_ITER=$(git rev-list --count --grep="^fix: address review feedback" "origin/${BASE_REF}..HEAD") \
  || { echo "iteration count failed — treat as unknown, do not silently proceed as iteration 0"; exit 1; }
```

Init / stop-reset / repair. Initialize only an absent file. Existing empty,
malformed, multi-document or invalid state is a recovery problem: preserve its
bytes and handles, report it, and repair from verified evidence before continuing.
Never silently replace damaged state with fresh defaults.

```bash
command -v jq >/dev/null || { echo "jq required for state management — stop"; exit 1; }
WAIT_SECONDS="${PR_AUTOFIX_WAIT_SECONDS:-3600}"
[[ "$WAIT_SECONDS" =~ ^[1-9][0-9]*$ && ${#WAIT_SECONDS} -le 10 ]] &&
  [ "$WAIT_SECONDS" -le 2147483647 ] || { echo "PR_AUTOFIX_WAIT_SECONDS must be an integer in 1..2147483647"; exit 1; }
pr_autofix_validate_state() {
  [ -f "$STATE" ] && [ -s "$STATE" ] && [ ! -L "$STATE" ] || return 1
  jq -L "${CLAUDE_PLUGIN_ROOT}/skills/pr-autofix/scripts" -se '
    include "review_state";
    length == 1 and (.[0] | valid_state)
  ' "$STATE" >/dev/null
}
if [ -e "$STATE" ] || [ -L "$STATE" ]; then
  pr_autofix_validate_state || { echo "existing state is invalid; preserve it and repair explicitly"; exit 1; }
fi
if [ ! -e "$STATE" ]; then
  MAX_ITER=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py" pr-autofix-iterations)
  jq -n --argjson pr "$PR_NUMBER" --arg base "$BASE_REF" --argjson it "$GIT_ITER" --argjson max "$MAX_ITER" --argjson wait "$WAIT_SECONDS" \
    '{pr: $pr, base_ref: $base, iteration: $it, max_iter: $max,
      replanned_this_pass: false, phase: "poll", stop_reason: null,
      stop_detail: null, review: null, await_limit_seconds: $wait,
      await_started_at: null, await_deadline: null,
      run_dir: null, sig: null, ld_sha: null}' > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" \
    || { echo "state init failed — stop, do not run stateless"; exit 1; }
elif [ "$(jq -r '.phase' "$STATE")" = "stop" ]; then
  MAX_ITER=$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py" pr-autofix-iterations)
  OLD_RUN=$(jq -r '.run_dir' "$STATE"); OLD_SIG=$(jq -r '.sig' "$STATE"); OLD_LD_SHA=$(jq -r '.ld_sha' "$STATE")
  LD="${CLAUDE_PLUGIN_ROOT}/skills/pr-autofix/scripts/land_delta.sh"
  if [ "$OLD_RUN" != "null" ] && [ -d "$OLD_RUN" ]; then
    bash "$LD" cleanup "$OLD_RUN" --script-sha "$OLD_LD_SHA" --sig "$OLD_SIG" --keep 2>/dev/null || true
  fi
  jq --argjson max "$MAX_ITER" '.phase = "poll" | .stop_reason = null | .stop_detail = null | .max_iter = $max
     | .await_started_at = null | .await_deadline = null
     | .replanned_this_pass = false | .run_dir = null | .sig = null | .ld_sha = null' \
    "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" || { echo "stop-reset failed — stop"; exit 1; }
fi
pr_autofix_validate_state || { echo "state validation failed"; exit 1; }
# Migrate legacy state without resetting iteration, live review handles or delta pointers.
jq --argjson wait "$WAIT_SECONDS" '
  .review //= null | .stop_detail //= null
  | .await_started_at //= null | .await_deadline //= null
  | if .await_deadline == null then .await_limit_seconds = $wait else . end
  | if .phase == "finalizing" then .phase = "poll" else . end
' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" \
  || { echo "state migration failed"; exit 1; }
if [ "$(jq -r '.iteration' "$STATE")" != "$GIT_ITER" ]; then
  echo "state/git iteration mismatch ($(jq -r '.iteration' "$STATE") vs $GIT_ITER) — adopting git value"
  jq --argjson it "$GIT_ITER" '.iteration = $it' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" \
    || { echo "state repair failed — stop"; exit 1; }
fi
MAX_ITER=$(jq -r '.max_iter' "$STATE"); ITERATION=$(jq -r '.iteration' "$STATE")
```

## Record an observation

After the queries in `review-evidence.md`, the host writes
`REVIEW_RECORD="$STATE_DIR/review-observation.tmp.json"` with the fields below.
This is disposable input, not a second state file: regenerate it on resume,
checkpoint the controlling values into `$STATE`, then remove the temporary file.
Never let the planner or implementer produce this record.

| Field | Value and source |
|---|---|
| `head` | Requested PR `headRefOid`, full commit SHA |
| `base_sha` | `baseRefOid` used for this review; a commit SHA, not `base_ref`'s branch name |
| `diff_sha256` | SHA-256 of the exact bytes from `gh pr diff "$PR_NUMBER" --repo "$REPO" --color never`, captured between matching HEAD/base queries before review |
| `handles` | Array of verified provider/run/check identifiers, including still-live runs |
| `requirements` | Object keyed by source; each value has `required` (boolean), nonempty `basis` (task/project/protection/config evidence), and any expected providers/lenses |
| `sources` | Object keyed by source; each value records the native `verdict` (`PASSED`, `BLOCKED`, `ERROR`, `PENDING`, `UNBOUND`, `NOT_REQUIRED`), reviewed `head`, `coverage_complete`, and unresolved `blocking_findings` |

Do not substitute a new diff identity for old evidence: if the requested refs/diff
changed, mark old source results unbound and collect new coverage first. A
`NOT_REQUIRED` result needs an explicit requirement basis, not an absent comment.
Bound source verdicts must name the checkpoint's exact HEAD. Only `UNBOUND` and
justified `NOT_REQUIRED` may carry no HEAD or a previous one; neither satisfies a
required source. Keep a native `BLOCKED` verdict even when disputing a finding; obtain an updated
review rather than silently changing it to `PASSED`.

```bash
REVIEW_RECORD="$STATE_DIR/review-observation.tmp.json"
# The host has written the verified observation described in the table above.
jq --slurpfile record "$REVIEW_RECORD" -L "${CLAUDE_PLUGIN_ROOT}/skills/pr-autofix/scripts" --arg base "$BASE_REF" -s '
  include "review_state";
  if length != 1 or (.[0] | valid_state | not) then error("invalid existing state")
  else .[0] end
  | if ($record | length) != 1 then error("observation must contain exactly one JSON document")
  elif ($record[0] | valid_observation | not) then error("invalid review observation")
  else .base_ref = $base | .review = $record[0] end
' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" \
  || { echo "review checkpoint failed"; exit 1; }
rm -f "$REVIEW_RECORD" "$STATE_DIR/review-comment.tmp.json"
```

## Mark clean

Run this only after the host has checked current authenticated reviews, inline
findings and required CI, and checkpointed every required source. The shared
validator refuses absent/malformed evidence, stale source HEADs, incomplete
required coverage and any unresolved blocking finding, including optional sources.
The native verdict cannot be replaced by an informal host conclusion.

The final reads also require an open, mergeable PR with GitHub's effective merge
state `CLEAN`. A pending/unknown/blocked state must be rechecked or diagnosed.
Capture diff bytes without command-substitution newline loss; a failed query or
changed HEAD/base/diff leaves the state file unchanged. The host must still check
HEAD and integration conditions immediately before its separately authorized merge.

```bash
set -o pipefail
PR_FIELDS=number,state,headRefOid,baseRefName,baseRefOid,reviewDecision,mergeStateStatus,mergeable
PR_BEFORE=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json "$PR_FIELDS") || exit 1
DIFF_SHA=$(gh pr diff "$PR_NUMBER" --repo "$REPO" --color never |
  python3 -c 'import hashlib, sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())') || exit 1
PR_AFTER=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json "$PR_FIELDS") || exit 1
jq -L "${CLAUDE_PLUGIN_ROOT}/skills/pr-autofix/scripts" -s \
  --argjson before "$PR_BEFORE" --argjson after "$PR_AFTER" \
  --argjson pr "$PR_NUMBER" --arg diff "$DIFF_SHA" '
  include "review_state";
  def scope: [.number, .headRefOid, .baseRefName, .baseRefOid];
  if length != 1 or (.[0] | valid_state | not) then error("invalid state")
  else .[0] end
  | if .phase != "checking_review" or .stop_reason != null or (.review | ready_review | not)
    then error("review evidence is not ready")
    elif .pr != $pr or $after.number != $pr
      or ($before | scope) != ($after | scope)
      or .review.head != $after.headRefOid or .review.base_sha != $after.baseRefOid
      or .base_ref != $after.baseRefName or .review.diff_sha256 != $diff
    then error("PR scope changed; collect review evidence again")
    elif $after.state != "OPEN" or $after.mergeable != "MERGEABLE"
      or $after.mergeStateStatus != "CLEAN"
      or ($after.reviewDecision != null and ($after.reviewDecision | type != "string"))
      or (["", "APPROVED", null] | index($after.reviewDecision)) == null
    then error("current PR protection or merge state is not ready")
    else .phase = "stop" | .stop_reason = "clean" | .stop_detail = null end
' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" \
  || { echo "clean transition refused; preserve state and refresh evidence"; exit 1; }
```

## Bound the local wait without restarting a remote job

Query the saved handles before entering this branch. A completed result is judged
normally even if the local deadline just expired. For a still-pending required run:

```bash
NOW=$(date +%s) || exit 1
jq -se '
  def uint($max): type == "number" and . == floor and . >= 0 and . <= $max;
  length == 1 and (.[0] |
    (.await_limit_seconds | uint(2147483647) and . > 0)
    and (.await_started_at == null or (.await_started_at | uint(9007199254740991)))
    and (.await_deadline == null or (.await_deadline | uint(9007199254740991))))
' "$STATE" >/dev/null || { echo "invalid wait bounds; preserve state"; exit 1; }
jq --argjson now "$NOW" '
  .phase = "awaiting_review"
  | .await_started_at //= $now
  | .await_deadline //= ($now + .await_limit_seconds)
' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" || exit 1
if [ "$NOW" -ge "$(jq -r '.await_deadline' "$STATE")" ]; then
  jq '.phase = "stop" | .stop_reason = "review_unavailable"
      | .stop_detail = "local wait budget exhausted; remote review remains pending; handles preserved"' \
    "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" || exit 1
  echo "Review still pending; invocation wait budget exhausted. Resume the same handles."
  exit 0
else
  WAIT_RC=$?
  [ "$WAIT_RC" -eq 1 ] || { echo "wait comparison failed"; exit 1; }
fi
```

This ends only the automation invocation, not the remote check. Do not cancel,
rerun or classify that check as failed from elapsed time alone. An explicit resume
from `stop_reason: "review_unavailable"` renews the local budget while preserving `review.handles` and the git-derived
iteration count. Diagnose a stalled queue or missing runner separately.
Changing HEAD or diff does not renew this invocation's deadline.
