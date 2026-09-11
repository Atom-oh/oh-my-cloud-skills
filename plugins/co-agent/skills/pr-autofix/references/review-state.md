# Review-loop state and checkpoints

Run Step 1's OPEN/branch guard before initializing state. This file grants no
merge authority. On Poll, repair `iteration` from Git with a warning; resolve the
actual PR base and reject failed counts rather than defaulting to zero:

```bash
BASE_REF=$(gh pr view "$PR_NUMBER" --json baseRefName --jq '.baseRefName')
GIT_ITER=$(git rev-list --count --grep="^fix: address review feedback" "origin/${BASE_REF}..HEAD") \
  || { echo "iteration count failed — treat as unknown, do not silently proceed as iteration 0"; exit 1; }
```

Initialize only absent state. Preserve invalid existing bytes and handles;
repair from verified evidence, never fresh defaults.

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

The host writes the observation below to `$STATE_DIR/review-observation.tmp.json`,
checkpoints it into `$STATE`, then removes it. Regenerate scratch input on resume;
the planner/implementer must not produce it.

| Field | Value and source |
|---|---|
| `head` | Requested PR `headRefOid`, full commit SHA |
| `base_sha` | `baseRefOid` used for this review; a commit SHA, not `base_ref`'s branch name |
| `diff_sha256` | SHA-256 of the exact bytes from `gh pr diff "$PR_NUMBER" --repo "$REPO" --color never`, captured between matching HEAD/base queries before review |
| `handles` | Array of verified provider/run/check identifiers, including still-live runs |
| `requirements` | Object keyed by source; each value has `required` (boolean), nonempty `basis` (task/project/protection/config evidence), and any expected providers/lenses |
| `sources` | Object keyed by source; each value records the native `verdict` (`PASSED`, `BLOCKED`, `ERROR`, `PENDING`, `UNBOUND`, `NOT_REQUIRED`), reviewed `head`, `coverage_complete`, and unresolved `blocking_findings` |

Changed scope needs new coverage, not relabeled old evidence. Bound verdicts must
match `head`; only `UNBOUND` and justified `NOT_REQUIRED` may lack it, and neither
satisfies a required source. Never rewrite `BLOCKED` to `PASSED`.

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

Checkpoint authenticated reviews and resolved findings first. This guard requires
fresh checks and matching local/remote/reviewed HEADs. An unchanged diff may retain
its reviewed base after advancement; `UNSTABLE`/`HAS_HOOKS` alone do not block.
Failure preserves state. The host separately rechecks authorized integration.

```bash
set -o pipefail
PR_FIELDS=number,state,headRefName,headRefOid,baseRefName,baseRefOid,reviewDecision,mergeStateStatus,mergeable
PR_BEFORE=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json "$PR_FIELDS") || exit 1
DIFF_SHA=$(gh pr diff "$PR_NUMBER" --repo "$REPO" --color never |
  python3 -c 'import hashlib, sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())') || exit 1
CHECKS="$STATE_DIR/required-checks.tmp.json"
HEAD_REF=$(printf '%s' "$PR_BEFORE" | jq -er '.headRefName | select(type == "string" and length > 0)') || exit 1
if gh pr checks "$PR_NUMBER" --repo "$REPO" --required --json name,bucket,state > "$CHECKS" 2> "$CHECKS.err"; then
  :
else
  CHECKS_RC=$?
  # gh emits this exact error only after successfully filtering an empty required set.
  EXPECTED_EMPTY="no required checks reported on the '$HEAD_REF' branch"
  if [ "$CHECKS_RC" -eq 1 ] && [ ! -s "$CHECKS" ] && [ "$(cat "$CHECKS.err")" = "$EXPECTED_EMPTY" ]; then
    printf '[]\n' > "$CHECKS"
  else
    echo "required check query did not pass; preserve state"; exit 1
  fi
fi
PR_AFTER=$(gh pr view "$PR_NUMBER" --repo "$REPO" --json "$PR_FIELDS") || exit 1
LOCAL_HEAD=$(git rev-parse --verify HEAD) || exit 1
jq -L "${CLAUDE_PLUGIN_ROOT}/skills/pr-autofix/scripts" -s \
  --slurpfile checks "$CHECKS" \
  --argjson before "$PR_BEFORE" --argjson after "$PR_AFTER" \
  --argjson pr "$PR_NUMBER" --arg diff "$DIFF_SHA" --arg local_head "$LOCAL_HEAD" '
  include "review_state";
  def scope: [.number, .headRefOid, .baseRefName, .baseRefOid];
  if length != 1 or (.[0] | valid_state | not) then error("invalid state")
  else .[0] end
  | if .phase != "checking_review" or .stop_reason != null or (.review | ready_review | not)
    then error("review evidence is not ready")
    elif .pr != $pr or $after.number != $pr
      or ($before | scope) != ($after | scope)
      or .review.head != $after.headRefOid
      or $local_head != $after.headRefOid
      or .base_ref != $after.baseRefName or .review.diff_sha256 != $diff
    then error("PR scope changed; collect review evidence again")
    elif $after.state != "OPEN" or $after.mergeable != "MERGEABLE"
      or ($after.mergeStateStatus | type != "string")
      or (["CLEAN","UNSTABLE","HAS_HOOKS"] | index($after.mergeStateStatus)) == null
      or ($after.reviewDecision != null and ($after.reviewDecision | type != "string"))
      or (["", "APPROVED", null] | index($after.reviewDecision)) == null
    then error("current PR protection or merge state is not ready")
    elif ($checks | length) != 1 or ($checks[0] | type != "array")
      or ($checks[0] | all(.[]; (.name | type == "string")
        and (.bucket == "pass" or .bucket == "skipping")
        and (.state | type == "string")
        and (.state as $s | ["SUCCESS","NEUTRAL","SKIPPED"] | index($s) != null)) | not)
    then error("required checks are not satisfied")
    else .phase = "stop" | .stop_reason = "clean" | .stop_detail = null end
' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" \
  || { echo "clean transition refused; preserve state and refresh evidence"; exit 1; }
rm -f "$CHECKS" "$CHECKS.err"
```

## Bound the local wait without restarting a remote job

Query saved handles first; judge completed results even after deadline expiry.
For a still-pending required run:

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

Expiry ends only this invocation: retain handles and do not cancel/rerun the remote
check. Explicit resume from `review_unavailable` renews the local budget, preserving
handles and iteration. Scope changes do not renew it; diagnose stalled queues separately.
