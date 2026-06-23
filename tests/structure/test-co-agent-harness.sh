#!/usr/bin/env bash
# Tests for co-agent:harness — implementer resolution, write-mode flags,
# stage-result/needs-human/rebind state, and the worktree helper.
CFG="plugins/co-agent/skills/co-agent/scripts/co_agent_config.py"
ST="plugins/co-agent/skills/co-agent/scripts/consensus_state.py"
WT="plugins/co-agent/skills/co-agent/scripts/worktree.py"

# --- Task 1 / R2-A: implementer resolution (sandbox CLIs only: codex, agy) ---
R=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness.XXXXXX")
assert_eq "codex" "$(python3 "$CFG" implementer --host claude --root "$R" 2>&1)" "default implementer for claude host = codex"
assert_eq "agy" "$(python3 "$CFG" implementer --host codex --root "$R" 2>&1)" "default implementer for codex host = agy (claude is not a sandbox CLI)"
python3 "$CFG" set harness implementer agy --root "$R" >/dev/null 2>&1
assert_eq "agy" "$(python3 "$CFG" implementer --host claude --root "$R" 2>&1)" "override to a sandbox CLI respected"
# non-sandbox implementers rejected at set time (claude/kiro-cli/gemini have no worktree sandbox)
python3 "$CFG" set harness implementer claude --root "$R" >/dev/null 2>&1 && C1=0 || C1=$?
assert_eq "2" "$C1" "non-sandbox implementer claude rejected (exit 2)"
python3 "$CFG" set harness implementer kiro-cli --root "$R" >/dev/null 2>&1 && C2=0 || C2=$?
assert_eq "2" "$C2" "non-sandbox implementer kiro-cli rejected (exit 2)"
# a valid sandbox implementer equal to the host is rejected at resolve time
python3 "$CFG" set harness implementer codex --root "$R" >/dev/null 2>&1
python3 "$CFG" implementer --host codex --root "$R" >/dev/null 2>&1 && IRC=0 || IRC=$?
assert_eq "2" "$IRC" "implementer equal to host rejected (exit 2)"
rm -rf "$R"

# --- Task 2 / R2-A: write-mode implementer flags (sandbox CLIs only) ---
R2=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness2.XXXXXX")
assert_contains "$(python3 "$CFG" impl-flags codex --host claude --root "$R2" 2>&1)" "workspace-write" "codex impl-flags use workspace-write sandbox"
assert_contains "$(python3 "$CFG" impl-flags agy --host claude --root "$R2" 2>&1)" "sandbox" "agy impl-flags keep sandbox"
# non-sandbox CLIs are not valid implementers — impl-flags rejects them
python3 "$CFG" impl-flags claude --host codex --root "$R2" >/dev/null 2>&1 && NF=0 || NF=$?
assert_eq "2" "$NF" "impl-flags rejects non-sandbox implementer claude (exit 2)"
python3 "$CFG" impl-flags codex --host codex --root "$R2" >/dev/null 2>&1 && HRC=0 || HRC=$?
assert_eq "2" "$HRC" "impl-flags rejects ai equal to host (exit 2)"
assert_grep_no_match "workspace-write|acceptEdits" "$(python3 "$CFG" flags codex --host claude --root "$R2" 2>&1)" "review flags stay read-only (no write sandbox)"
rm -rf "$R2"

# --- Task 3: needs-human status ---
R3=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness3.XXXXXX")
git -C "$R3" init -q
git -C "$R3" config user.email t@t.t; git -C "$R3" config user.name t
git -C "$R3" commit -q --allow-empty -m init >/dev/null 2>&1
python3 "$ST" init "$R3" --docs none --base HEAD >/dev/null 2>&1
python3 "$ST" set "$R3" status needs-human >/dev/null 2>&1 && NRC=0 || NRC=$?
assert_eq "0" "$NRC" "status needs-human accepted (exit 0)"
assert_eq "needs-human" "$(python3 "$ST" get "$R3" status 2>&1)" "get status returns needs-human"
python3 "$ST" set "$R3" status bogus >/dev/null 2>&1 && BRC=0 || BRC=$?
assert_eq "2" "$BRC" "invalid status still rejected (exit 2)"
rm -rf "$R3"

# --- Task 4: stage-result output gate ---
R4=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness4.XXXXXX")
python3 "$ST" stage-result check "$R4/missing.json" >/dev/null 2>&1 && M=0 || M=$?
assert_eq "1" "$M" "stage-result check on missing artifact fails (exit 1)"
python3 "$ST" stage-result write "$R4/plan-gate/result.json" --stage plan-gate --verdict PASS --rounds 1 --wall "$R4/stage_wall.tsv" >/dev/null 2>&1
assert_file_exists "$R4/plan-gate/result.json" "stage-result write creates result.json"
assert_json_valid "$R4/plan-gate/result.json" "result.json is valid JSON"
python3 "$ST" stage-result check "$R4/plan-gate/result.json" >/dev/null 2>&1 && C=0 || C=$?
assert_eq "0" "$C" "stage-result check on valid artifact passes (exit 0)"
assert_contains "$(cat "$R4/stage_wall.tsv")" "plan-gate" "stage_wall.tsv got a row"
# R2-E: the output gate must STOP on FAIL / green=false / in_scope=false
python3 "$ST" stage-result write "$R4/fail.json" --stage g --verdict FAIL >/dev/null 2>&1
python3 "$ST" stage-result check "$R4/fail.json" >/dev/null 2>&1 && FG=0 || FG=$?
assert_eq "1" "$FG" "stage-result check fails on verdict FAIL (exit 1)"
python3 "$ST" stage-result write "$R4/red.json" --stage t --verdict PASS --green false >/dev/null 2>&1
python3 "$ST" stage-result check "$R4/red.json" >/dev/null 2>&1 && RG=0 || RG=$?
assert_eq "1" "$RG" "stage-result check fails when green=false (exit 1)"
python3 "$ST" stage-result write "$R4/oos.json" --stage t --verdict PASS --in-scope false >/dev/null 2>&1
python3 "$ST" stage-result check "$R4/oos.json" >/dev/null 2>&1 && OG=0 || OG=$?
assert_eq "1" "$OG" "stage-result check fails when in_scope=false (exit 1)"
python3 "$ST" stage-result write "$R4/ok.json" --stage t --verdict PASS --green true --in-scope true >/dev/null 2>&1
python3 "$ST" stage-result check "$R4/ok.json" >/dev/null 2>&1 && OK=0 || OK=$?
assert_eq "0" "$OK" "stage-result check passes on PASS + green + in_scope (exit 0)"
rm -rf "$R4"

# --- Task 5: rebind after manual commit ---
R5=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness5.XXXXXX")
git -C "$R5" init -q
git -C "$R5" config user.email t@t.t; git -C "$R5" config user.name t
printf '.claude/\n' > "$R5/.gitignore"   # session state is gitignored (as in the real repo)
git -C "$R5" add .gitignore >/dev/null 2>&1
git -C "$R5" commit -q -m init >/dev/null 2>&1
python3 "$ST" init "$R5" --docs none --base HEAD >/dev/null 2>&1
git -C "$R5" commit -q --allow-empty -m "manual fix" >/dev/null 2>&1
python3 "$ST" verify "$R5" >/dev/null 2>&1 && V1=0 || V1=$?
assert_eq "1" "$V1" "verify fails after HEAD drift (exit 1)"
python3 "$ST" rebind "$R5" >/dev/null 2>&1 && RB=0 || RB=$?
assert_eq "0" "$RB" "rebind succeeds (exit 0)"
python3 "$ST" verify "$R5" >/dev/null 2>&1 && V2=0 || V2=$?
assert_eq "0" "$V2" "verify passes after rebind (exit 0)"
rm -rf "$R5"

# --- Task 6: worktree helper excludes gitignored, keeps new source ---
R6=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness6.XXXXXX")
git -C "$R6" init -q
git -C "$R6" config user.email t@t.t; git -C "$R6" config user.name t
printf 'secret.env\n' > "$R6/.gitignore"
git -C "$R6" add .gitignore >/dev/null 2>&1
git -C "$R6" commit -q -m init >/dev/null 2>&1
assert_file_exists "$WT" "worktree.py exists"
WTD="$R6/.wt-task0"
python3 "$WT" add "$WTD" --base HEAD --root "$R6" >/dev/null 2>&1 && A=0 || A=$?
assert_eq "0" "$A" "worktree add succeeds"
printf 'def f():\n    return 1\n' > "$WTD/feature.py"
printf 'TOKEN=abc\n' > "$WTD/secret.env"
DIFF=$(python3 "$WT" capture-diff "$WTD" 2>/dev/null)
assert_contains "$DIFF" "feature.py" "capture-diff includes the new non-ignored file"
assert_grep_no_match "secret.env" "$DIFF" "capture-diff excludes the gitignored file"
python3 "$WT" remove "$WTD" --root "$R6" >/dev/null 2>&1 && RM=0 || RM=$?
assert_eq "0" "$RM" "worktree remove succeeds"
assert_eq "" "$(git -C "$R6" worktree list --porcelain | grep -F "$WTD")" "no stale worktree ref after remove"
rm -rf "$R6"

# --- R2-BCD: capture-diff hardening (bypass cases) ---
R7=$(mktemp -d "${TMPDIR:-/tmp}/coagent-harness7.XXXXXX")
git -C "$R7" init -q
git -C "$R7" config user.email t@t.t; git -C "$R7" config user.name t
printf 'secret.env\n' > "$R7/.gitignore"
git -C "$R7" add .gitignore >/dev/null 2>&1
git -C "$R7" commit -q -m init >/dev/null 2>&1
W="$R7/.wt"
python3 "$WT" add "$W" --base HEAD --root "$R7" >/dev/null 2>&1
# B: peer force-stages an ignored file; capture-diff must reset the index and exclude it
printf 'TOKEN=abc\n' > "$W/secret.env"
git -C "$W" add -f secret.env >/dev/null 2>&1
printf 'def f():\n    return 1\n' > "$W/feature.py"
DIFF=$(python3 "$WT" capture-diff "$W" 2>/dev/null) && CD=0 || CD=$?
assert_grep_no_match "secret.env" "$DIFF" "capture-diff resets index — pre-staged (add -f) ignored file excluded"
assert_contains "$DIFF" "feature.py" "capture-diff still includes the legitimate new file"
# C: an external diff driver in the worktree must NOT execute during capture-diff
git -C "$W" config diff.evil.command "touch $W/PWNED" >/dev/null 2>&1
printf '*.py diff=evil\n' > "$W/.gitattributes"
python3 "$WT" capture-diff "$W" >/dev/null 2>&1
assert_eq "0" "$([ -e "$W/PWNED" ] && echo 1 || echo 0)" "capture-diff uses --no-ext-diff — external diff driver did NOT execute"
# D: capture-diff on a non-git path surfaces the failure (non-zero)
python3 "$WT" capture-diff "$R7/nope" >/dev/null 2>&1 && DF=0 || DF=$?
assert_grep_no_match "^0$" "$DF" "capture-diff on a non-git path returns non-zero"
# R2-H: `--base` as the last arg with no value must not crash (graceful exit 2, no IndexError)
ERR=$(python3 "$WT" add "$R7/.wt-x" --base 2>&1) && BR=0 || BR=$?
assert_eq "2" "$BR" "worktree add --base with no value → graceful exit 2"
assert_grep_no_match "IndexError|Traceback" "$ERR" "worktree add --base with no value → no Python traceback"
rm -rf "$R7"

# --- Task 7: delegated-implement reference ---
REF="plugins/co-agent/skills/co-agent/references/delegated-implement.md"
assert_file_exists "$REF" "delegated-implement.md exists"
assert_contains "$(cat "$REF" 2>/dev/null)" "workspace-write" "reference documents workspace-write sandbox"
assert_contains "$(cat "$REF" 2>/dev/null)" "capture-diff" "reference documents capture-diff"
assert_contains "$(cat "$REF" 2>/dev/null)" "only committer" "reference states host is the only committer"
assert_grep_no_match "AKIA[0-9A-Z]{16}|-----BEGIN" "$(cat "$REF" 2>/dev/null)" "reference has no leaked secrets"
# R2-F: the red test must be committed BEFORE the worktree is created (else --base HEAD omits it)
assert_grep_match "commit[^.]*(failing|red) test" "$(cat "$REF" 2>/dev/null)" "reference: host commits the red test before the worktree"

# --- Task 8: command + manifest wiring ---
CMD="plugins/co-agent/commands/harness.md"
assert_file_exists "$CMD" "harness command file exists"
assert_contains "$(cat "$CMD" 2>/dev/null)" "delegated-implement" "command links the delegated-implement reference"
assert_contains "$(cat "$CMD" 2>/dev/null)" "worktree" "command references the worktree isolation"
PJ="plugins/co-agent/.claude-plugin/plugin.json"
assert_eq "True" "$(python3 -c "import json;print('./commands/harness.md' in json.load(open('$PJ'))['commands'])" 2>&1)" "harness command registered in plugin.json"
assert_contains "$(cat plugins/co-agent/skills/co-agent/SKILL.md 2>/dev/null)" "harness" "SKILL.md mentions the harness mode"
