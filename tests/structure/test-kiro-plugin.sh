#!/usr/bin/env bash
# Tests for the kiro plugin — settings layering, review script (block levels,
# fail-open), setup helpers, and reused co-agent scripts (worktree/scope_guard parity).

SK="plugins/kiro/skills/kiro-delegate/scripts"
CFG="$SK/kiro_config.py"
REVIEW="$SK/kiro_review.py"
SETUP="$SK/kiro_setup.py"
WT="$SK/worktree.py"
SG="$SK/scope_guard.py"
PP="$SK/parse_plan.py"

# --- manifest + wiring ---
PJ="plugins/kiro/.claude-plugin/plugin.json"
assert_file_exists "$PJ" "kiro plugin.json exists"
assert_json_valid "$PJ" "kiro plugin.json valid"
assert_eq "True" "$(python3 -c "import json; print('./hooks/pre-commit-review.sh' in open('plugins/kiro/hooks/pre-commit-review.sh').read() or True)" 2>&1)" "sanity: python3 available"
assert_contains "$(cat "$PJ")" "pre-commit-review.sh" "plugin.json wires the pre-commit review hook"
HOOK="plugins/kiro/hooks/pre-commit-review.sh"
assert_file_exists "$HOOK" "pre-commit-review.sh exists"
assert_file_executable "$HOOK" "pre-commit-review.sh is executable"
assert_bash_syntax "$HOOK" "pre-commit-review.sh valid syntax"

for f in "$CFG" "$REVIEW" "$SETUP" "$WT" "$SG" "$PP"; do
  assert_file_exists "$f" "$(basename "$f") exists"
  assert_file_executable "$f" "$(basename "$f") is executable"
done

# reused-from-co-agent scripts must be byte-identical to their source (no silent drift)
for name in worktree.py scope_guard.py parse_plan.py; do
  SRC="plugins/co-agent/skills/co-agent/scripts/$name"
  DST="$SK/$name"
  if [ -f "$SRC" ] && diff -q "$SRC" "$DST" >/dev/null 2>&1; then
    pass "$name is byte-identical to co-agent's copy (no drift)"
  else
    fail "$name is byte-identical to co-agent's copy (no drift)" "diff: $(diff "$SRC" "$DST" 2>&1 | head -3)"
  fi
done

# --- kiro_config.py: layered settings ---
R=$(mktemp -d "${TMPDIR:-/tmp}/kiro-cfg.XXXXXX")
assert_eq "1" "$(python3 "$CFG" default-delegate --root "$R" >/dev/null 2>&1; echo $?)" "default_delegate is off by default (exit 1)"
python3 "$CFG" set default_delegate on --root "$R" >/dev/null 2>&1
assert_eq "0" "$(python3 "$CFG" default-delegate --root "$R" >/dev/null 2>&1; echo $?)" "set default_delegate on takes effect"
python3 "$CFG" set delegate model "gpt-5.3-codex-mini" --root "$R" >/dev/null 2>&1
assert_eq "gpt-5.3-codex-mini" "$(python3 "$CFG" delegate-model --root "$R" 2>&1)" "delegate model set/read roundtrip"
python3 "$CFG" set review model "gpt-5.6-sol" --root "$R" >/dev/null 2>&1
assert_eq "gpt-5.6-sol" "$(python3 "$CFG" review-model --root "$R" 2>&1)" "review model set/read roundtrip"
assert_eq "critical" "$(python3 "$CFG" block --root "$R" 2>&1)" "review block defaults to critical"
python3 "$CFG" set review block warning --root "$R" >/dev/null 2>&1
assert_eq "warning" "$(python3 "$CFG" block --root "$R" 2>&1)" "review block set/read roundtrip"
python3 "$CFG" set review block bogus --root "$R" >/dev/null 2>&1 && BC=0 || BC=$?
assert_eq "2" "$BC" "invalid review block value rejected (exit 2)"
python3 "$CFG" set delegate model "bad;rm -rf" --root "$R" >/dev/null 2>&1 && MC=0 || MC=$?
assert_eq "2" "$MC" "model with shell metacharacters rejected (exit 2)"
python3 "$CFG" set delegate parallel_tasks 0 --root "$R" >/dev/null 2>&1 && PC=0 || PC=$?
assert_eq "2" "$PC" "parallel_tasks below 1 rejected (exit 2)"
assert_eq "3" "$(python3 "$CFG" parallel-tasks --root "$R" 2>&1)" "parallel_tasks defaults to 3"
assert_eq "2" "$(python3 "$CFG" max-fix-rounds --root "$R" 2>&1)" "max_fix_rounds defaults to 2"
rm -rf "$R"

# --- kiro_review.py: block-level gating on a canned diff (no real kiro-cli call) ---
R2=$(mktemp -d "${TMPDIR:-/tmp}/kiro-review.XXXXXX")
DIFFFILE="$R2/sample.diff"
printf 'diff --git a/f.py b/f.py\n+++ b/f.py\n@@ -0,0 +1,1 @@\n+bad code\n' > "$DIFFFILE"

# Simulate a "no kiro-cli" environment: strip every PATH entry that actually contains a
# kiro-cli binary (not just prepend an empty dir, which wouldn't shadow one already
# present further down PATH) — python3/git/etc. stay reachable via the remaining entries.
NOKIRO_PATH=$(IFS=:; for d in $PATH; do [ -x "$d/kiro-cli" ] || printf '%s:' "$d"; done)
OUT=$(PATH="${NOKIRO_PATH%:}" python3 "$REVIEW" --diff "$DIFFFILE" --root "$R2" 2>&1) && RC=0 || RC=$?
assert_eq "0" "$RC" "review fails OPEN (exit 0) when kiro-cli is not on PATH"
assert_contains "$OUT" "skipped" "review reports the fail-open reason"
rm -rf "$R2"

# Empty diff short-circuits cleanly regardless of kiro-cli availability
R3=$(mktemp -d "${TMPDIR:-/tmp}/kiro-review2.XXXXXX")
printf '' > "$R3/empty.diff"
OUT3=$(python3 "$REVIEW" --diff "$R3/empty.diff" --root "$R3" 2>&1) && RC3=0 || RC3=$?
assert_eq "0" "$RC3" "review on an empty diff exits 0"
assert_contains "$OUT3" "no changes to review" "review on an empty diff reports nothing to review"
rm -rf "$R3"

# --- kiro_setup.py: absent kiro-cli reports ABSENT, not a crash ---
R4=$(mktemp -d "${TMPDIR:-/tmp}/kiro-setup.XXXXXX")
PROBE=$(PATH="${NOKIRO_PATH%:}" python3 "$SETUP" probe 2>&1)
assert_contains "$PROBE" "ABSENT" "kiro_setup.py probe reports ABSENT when kiro-cli is missing"

# write-agents produces both custom-agent JSON files, valid JSON, correct tool scoping
python3 "$SETUP" write-agents --root "$R4" >/dev/null 2>&1
IMPL="$R4/.kiro/agents/kiro-implementer.json"
REV="$R4/.kiro/agents/kiro-reviewer.json"
assert_file_exists "$IMPL" "write-agents creates kiro-implementer.json"
assert_file_exists "$REV" "write-agents creates kiro-reviewer.json"
assert_json_valid "$IMPL" "kiro-implementer.json is valid JSON"
assert_json_valid "$REV" "kiro-reviewer.json is valid JSON"
assert_grep_no_match "fs_write" "$(python3 -c "import json;print(json.load(open('$REV'))['tools'])")" "kiro-reviewer has no fs_write tool (read-only)"
assert_contains "$(python3 -c "import json;print(json.load(open('$IMPL'))['tools'])")" "fs_write" "kiro-implementer has fs_write tool"
# re-run without --force must not clobber (idempotent skip)
python3 -c "import json; json.dump({'name':'hand-edited'}, open('$IMPL','w'))"
python3 "$SETUP" write-agents --root "$R4" >/dev/null 2>&1
assert_contains "$(cat "$IMPL")" "hand-edited" "write-agents without --force does not overwrite an existing agent file"
python3 "$SETUP" write-agents --root "$R4" --force >/dev/null 2>&1
assert_grep_no_match "hand-edited" "$(cat "$IMPL")" "write-agents --force overwrites an existing agent file"
rm -rf "$R4"

# --- worktree + scope_guard reused verbatim: sanity smoke test (full coverage lives
#     in test-co-agent-harness.sh against the shared source) ---
R5=$(mktemp -d "${TMPDIR:-/tmp}/kiro-wt.XXXXXX")
git -C "$R5" init -q
git -C "$R5" config user.email t@t.t; git -C "$R5" config user.name t
git -C "$R5" commit -q --allow-empty -m init >/dev/null 2>&1
WTD="$R5/.wt-task0"
python3 "$WT" add "$WTD" --base HEAD --root "$R5" >/dev/null 2>&1 && A=0 || A=$?
assert_eq "0" "$A" "kiro plugin's worktree.py add works standalone"
printf 'def f():\n    return 1\n' > "$WTD/feature.py"
DIFF=$(python3 "$WT" capture-diff --root "$R5" "$WTD" 2>/dev/null)
assert_contains "$DIFF" "feature.py" "kiro plugin's worktree.py capture-diff works standalone"
python3 "$WT" remove "$WTD" --root "$R5" >/dev/null 2>&1
rm -rf "$R5"

# scope_guard against a tasks.md-shaped plan (backtick-wrapped Files: block)
R6=$(mktemp -d "${TMPDIR:-/tmp}/kiro-sg.XXXXXX")
cat > "$R6/tasks.md" <<'EOF'
## Task 1: add a helper

**Files:**
- Create: `src/helper.py`
- Modify: `src/main.py`

- [ ] write the helper
EOF
python3 "$SG" --plan "$R6/tasks.md" src/helper.py >/dev/null 2>&1 && SGIN=0 || SGIN=$?
assert_eq "0" "$SGIN" "scope_guard.py accepts a path declared in tasks.md"
python3 "$SG" --plan "$R6/tasks.md" src/unrelated.py >/dev/null 2>&1 && SGOUT=0 || SGOUT=$?
assert_eq "1" "$SGOUT" "scope_guard.py rejects a path NOT declared in tasks.md"
rm -rf "$R6"

# --- spec-format reference documents the backtick pitfall (single most common authoring bug) ---
REF="plugins/kiro/skills/kiro-delegate/references/spec-format.md"
assert_file_exists "$REF" "spec-format.md exists"
assert_contains "$(cat "$REF")" "backtick" "spec-format.md documents the backtick-wrapped path requirement"

# --- CLAUDE.md documents the trust boundary consistently with co-agent's stance on kiro ---
assert_contains "$(cat plugins/kiro/CLAUDE.md)" "no cwd-confined write sandbox" "kiro plugin CLAUDE.md documents why co-agent refuses Kiro as an implementer"
assert_contains "$(cat plugins/co-agent/skills/co-agent/scripts/co_agent_config.py)" 'SANDBOX_IMPLEMENTERS = ("codex", "agy")' "co-agent still excludes kiro-cli from SANDBOX_IMPLEMENTERS (consistency check)"
