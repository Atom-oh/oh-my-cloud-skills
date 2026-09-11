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
  jq -se '
    def uint($max): type == "number" and . == floor and . >= 0 and . <= $max;
    length == 1 and (.[0] |
      type == "object"
      and (.pr | uint(9007199254740991) and . > 0)
      and (.base_ref | type == "string" and length > 0)
      and (.iteration | uint(2147483647))
      and (.max_iter | uint(2147483647) and . > 0)
      and (.phase as $p | ["poll","gate","committing","stop","awaiting_review","checking_review","finalizing"] | index($p) != null)
      and (.review == null or (.review | type == "object"))
      and (.await_limit_seconds == null or (.await_limit_seconds | uint(2147483647) and . > 0))
      and (.await_started_at == null or (.await_started_at | uint(9007199254740991)))
      and (.await_deadline == null or (.await_deadline | uint(9007199254740991))))
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
  | .await_limit_seconds = $wait | .await_started_at //= null | .await_deadline //= null
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
| `diff_sha256` | SHA-256 of the requested diff captured for these refs |
| `handles` | Array of verified provider/run/check identifiers, including still-live runs |
| `requirements` | Object keyed by source; each value has `required` (boolean), nonempty `basis` (task/project/protection/config evidence), and any expected providers/lenses |
| `sources` | Object keyed by source; each value records the native `verdict` (`PASSED`, `BLOCKED`, `ERROR`, `PENDING`, `UNBOUND`, `NOT_REQUIRED`), reviewed `head`, `coverage_complete`, and unresolved `blocking_findings` |

Do not substitute a new diff identity for old evidence: if the requested refs/diff
changed, mark old source results unbound and collect new coverage first. A
`NOT_REQUIRED` result needs an explicit requirement basis, not an absent comment.
Keep a native `BLOCKED` verdict even when disputing a finding; obtain an updated
review rather than silently changing it to `PASSED`.

```bash
REVIEW_RECORD="$STATE_DIR/review-observation.tmp.json"
# The host has written the verified observation described in the table above.
jq --slurpfile record "$REVIEW_RECORD" --arg base "$BASE_REF" -s '
  def valid_observation:
    . as $r | type == "object"
    and (.head | test("^[0-9a-f]{40}$"))
    and (.base_sha | test("^[0-9a-f]{40}$"))
    and (.diff_sha256 | test("^[0-9a-f]{64}$"))
    and (.handles | type == "array")
    and (.requirements | type == "object" and length > 0)
    and (.requirements | all(.[]; (.required | type == "boolean") and (.basis | type == "string" and length > 0)))
    and (.sources | type == "object" and length > 0)
    and ((.requirements | keys) - (.sources | keys) | length == 0)
    and (.sources | all(.[]; .verdict as $v |
         ["PASSED","BLOCKED","ERROR","PENDING","UNBOUND","NOT_REQUIRED"] | index($v) != null))
    and (.sources | all(.[]; (.coverage_complete | type == "boolean")
         and (.blocking_findings | type == "array")))
    and (.sources | to_entries | all(.[]; .value.verdict != "NOT_REQUIRED"
         or ($r.requirements[.key].required == false and ($r.requirements[.key].basis | length > 0))));
  if length != 1 or (.[0] | type != "object") then error("state must contain exactly one JSON object")
  else .[0] end
  | if ($record | length) != 1 then error("observation must contain exactly one JSON document")
  elif ($record[0] | valid_observation | not) then error("invalid review observation")
  else .base_ref = $base | .review = $record[0] end
' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE" \
  || { echo "review checkpoint failed"; exit 1; }
rm -f "$REVIEW_RECORD"
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
renews the local budget while preserving `review.handles` and the git-derived
iteration count. Diagnose a stalled queue or missing runner separately.
Changing HEAD or diff does not renew this invocation's deadline.
