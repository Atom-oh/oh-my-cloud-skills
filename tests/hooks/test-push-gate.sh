# Test the pre-push lens gate: kiro's hook_match.py git-push/push-scope-mismatch/bypass
# modes, and the co-agent + kiro plugin.json / hook script wiring. Companion to
# test-hooks.sh (file-existence/executable/syntax checks) and test-secret-patterns.sh
# (regex true/false-positive checks) — this file follows the same conventions.

HM="plugins/kiro/skills/kiro-delegate/scripts/hook_match.py"

_payload() {
  # Build the {"tool_input":{"command": "..."}} JSON payload hook_match.py reads from
  # stdin, via python3 (not string concatenation) so embedded quotes/backslashes in
  # the test commands are escaped correctly.
  python3 -c "import json,sys; print(json.dumps({'tool_input': {'command': sys.argv[1]}}))" "$1"
}

_hm() {
  # _hm <mode> <command>  →  exit code of hook_match.py <mode> on that command's payload
  _payload "$2" | python3 "$HM" "$1" >/dev/null 2>&1
  echo $?
}

# --- git-push: true positives ---
assert_eq "0" "$(_hm git-push 'git push')" "git-push: bare 'git push'"
assert_eq "0" "$(_hm git-push 'git push -u origin HEAD')" "git-push: with flags"
assert_eq "0" "$(_hm git-push 'git -C /repo push')" "git-push: -C before push"
assert_eq "0" "$(_hm git-push 'env FOO=1 git push')" "git-push: env prefix"
assert_eq "0" "$(_hm git-push 'foo && git push')" "git-push: compound command"
assert_eq "0" "$(_hm git-push '/usr/bin/git push')" "git-push: absolute git path"

# --- git-push: false positives (regression guards) ---
assert_eq "1" "$(_hm git-push 'echo "git push"')" "git-push: quoted string, not a real invocation"
assert_eq "1" "$(_hm git-push 'git push-notes')" "git-push: 'push-notes' is not the push subcommand"
assert_eq "1" "$(_hm git-push 'git commit -m "git push"')" "git-push: mention inside a commit message"

# --- bypass: shared mode, must recognize BOTH commit and push inline prefixes ---
assert_eq "0" "$(_hm bypass 'KIRO_REVIEW=off git push')" "bypass: inline prefix on git push"
assert_eq "0" "$(_hm bypass 'KIRO_REVIEW=off git commit -m x')" "bypass: inline prefix on git commit (unchanged)"
assert_eq "1" "$(_hm bypass 'NOTE=KIRO_REVIEW=off git push')" "bypass: value of a DIFFERENT var must not match"

# --- push-scope-mismatch: true positives ---
assert_eq "0" "$(_hm push-scope-mismatch 'cd ../other && git push')" "push-scope-mismatch: preceding cd"
assert_eq "0" "$(_hm push-scope-mismatch 'git commit -m x && git push')" "push-scope-mismatch: preceding commit (stale range)"
assert_eq "0" "$(_hm push-scope-mismatch 'git push origin --delete foo')" "push-scope-mismatch: --delete has nothing to review"
assert_eq "0" "$(_hm push-scope-mismatch 'git -C /elsewhere push')" "push-scope-mismatch: -C redirect"

# --- push-scope-mismatch: false positive (an ordinary push must NOT warn) ---
assert_eq "1" "$(_hm push-scope-mismatch 'git push')" "push-scope-mismatch: bare push is not a mismatch"
assert_eq "1" "$(_hm push-scope-mismatch 'git push -u origin HEAD')" "push-scope-mismatch: ordinary explicit push is not a mismatch"

# --- kiro_review.py lens merge: dedupe by (file, line), keep highest severity ---
MERGE_OUT="$(python3 -c "
import sys
sys.path.insert(0, 'plugins/kiro/skills/kiro-delegate/scripts')
import kiro_review as kr

def fake(root, diff, model, timeout, lens=None, **kw):
    # **kw so a new run_review kwarg (e.g. progress=) can't turn this stub into a
    # TypeError that the thread swallows and reports as a full-deadline timeout.
    data = {
        'correctness': [{'severity': 'warning', 'file': 'a.py', 'line': 1, 'issue': 'bug'}],
        'security': [{'severity': 'critical', 'file': 'a.py', 'line': 1, 'issue': 'secret'}],
        'scope': [],
    }
    return (data[lens], None, False)

kr.run_review = fake
merged, errors, trunc = kr.run_review_lenses('.', 'diff', None, 30, ['correctness', 'security', 'scope'])
assert errors == {}, errors
assert trunc is False
assert len(merged) == 1, merged
f = merged[0]
assert f['severity'] == 'critical', f
assert sorted(f['lenses']) == ['correctness', 'security'], f
print('OK')
" 2>&1)"
assert_eq "OK" "$MERGE_OUT" "kiro_review lens merge: warning+critical at the same (file,line) collapses to critical, both lenses tagged"

# --- ANSI-tolerant findings parse (kiro-cli colorizes its banner even into a file, and
#     each escape contains a literal '[' that bracket-scanning used to latch onto) ---
ANSI_OUT="$(python3 -c "
import sys
sys.path.insert(0, 'plugins/kiro/skills/kiro-delegate/scripts')
import kiro_review as kr
colored = ('Reading file: \x1b[38;5;141m/tmp/x/review.diff\x1b[0m, all lines\x1b[38;5;244m'
           ' (using tool: read)\x1b[0m\n\x1b[38;5;141m> \x1b[0m'
           '[{\"severity\":\"critical\",\"file\":\"r.py\",\"line\":6,\"issue\":\"injection\"}]')
got = kr._extract_json_array(colored)
assert got == [{'severity': 'critical', 'file': 'r.py', 'line': 6, 'issue': 'injection'}], got
assert kr._extract_json_array('\x1b[0m> \x1b[0m[]') == []
assert kr._extract_json_array('\x1b[38;5;141mprose only, no array') is None
assert kr._extract_json_array('[{\"severity\":\"warning\"}]') == [{'severity': 'warning'}]
print('OK')
" 2>&1)"
assert_eq "OK" "$ANSI_OUT" "kiro_review parses findings out of ANSI-colored CLI output (and still handles plain output)"

# --- push-gate exit framing: critical => BLOCKED, warning-only => CHAIR JUDGMENT ---
_framing() {
  # _framing <severity>  ->  "<exit>|<marker>"
  python3 -c "
import sys, io, contextlib
sys.path.insert(0, 'plugins/kiro/skills/kiro-delegate/scripts')
import kiro_review as kr

sev = sys.argv[1]
kr._resolve_push_range = lambda root: ('@{upstream}..HEAD', None)
kr._range_diff = lambda root, rng: ('diff --git a/x b/x\n+x\n', None)
kr.run_review_lenses = lambda root, diff, model, timeout, lenses, **kw: (
    [{'severity': sev, 'file': 'x.py', 'line': 3, 'issue': 'something', 'lenses': ['security']}],
    {}, False)
kr.kc.effective = lambda root: {'review': {'push_block': 'warning', 'timeout': 30}}

sys.argv = ['kiro_review.py', '--range', '--lenses', 'security', '--root', '.']
err = io.StringIO()
with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
    rc = kr.main()
text = err.getvalue()
marker = 'BLOCKED' if 'BLOCKED the push' in text else (
         'CHAIR' if 'CHAIR JUDGMENT REQUIRED' in text else 'NEITHER')
print(f'{rc}|{marker}')
" "$1" 2>&1
}
assert_eq "2|BLOCKED" "$(_framing critical)" "push gate: a critical finding exits 2 framed as BLOCKED"
assert_eq "2|CHAIR" "$(_framing warning)" "push gate: a warning-only set exits 2 framed as CHAIR JUDGMENT REQUIRED"

# --- co-agent push gate: lens round-robin keeps the call count at 3 for any panel size ---
RR_OUT="$(python3 -c "
import sys
sys.path.insert(0, 'plugins/co-agent/skills/co-agent/scripts')
import consensus_hooks as ch
lenses = list(ch._PUSH_LENSES)
assert lenses == ['correctness', 'security', 'scope'], lenses
for peers in (['a'], ['a', 'b'], ['a', 'b', 'c'], ['a', 'b', 'c', 'd']):
    assign = [(peers[i % len(peers)], l) for i, l in enumerate(lenses)]
    assert len(assign) == 3, (peers, assign)
    assert sorted(l for _, l in assign) == sorted(lenses), assign
print('OK')
" 2>&1)"
assert_eq "OK" "$RR_OUT" "co-agent push gate: 3 lenses always covered in exactly 3 calls, any panel size"

# --- plugin.json / hook script wiring ---
assert_json_valid "plugins/kiro/.claude-plugin/plugin.json" "kiro plugin.json is valid JSON after adding pre-push-review.sh"
assert_json_valid "plugins/co-agent/.claude-plugin/plugin.json" "co-agent plugin.json is valid JSON after adding pre-push-gate"
assert_contains "$(cat plugins/kiro/.claude-plugin/plugin.json)" "pre-push-review.sh" "kiro plugin.json registers pre-push-review.sh"
assert_contains "$(cat plugins/co-agent/.claude-plugin/plugin.json)" "pre-push-gate" "co-agent plugin.json registers pre-push-gate"

# --- SessionStart routing hook: the mechanism that makes default_delegate actually fire
#     (a plugin's CLAUDE.md is NOT injected into context, so the rule has to come from
#     a hook whose output does reach the model) ---
_routing() {
  # _routing '<kiro.local.json contents>'  ->  "<exit>|<blocks present>"
  local d; d=$(mktemp -d); git init -q "$d"; mkdir -p "$d/.claude"
  printf '%s\n' "$1" > "$d/.claude/kiro.local.json"
  local out rc
  # `|| rc=$?` — this file is SOURCED by run-all.sh, which runs under `set -e`, so a
  # bare non-zero command (or a `grep -q && assign` list whose grep misses) would abort
  # the entire test run silently. Every conditional below is an `if` for the same reason.
  rc=0
  out=$(cd "$d" && CLAUDE_PLUGIN_ROOT="$PWD_ROOT/plugins/kiro" \
        bash "$PWD_ROOT/plugins/kiro/hooks/session-routing.sh" 2>/dev/null) || rc=$?
  local marks=""
  if echo "$out" | grep -q "kiro loaded"; then marks="banner"; fi
  if echo "$out" | grep -q "default_delegate is ON"; then marks="$marks+delegate"; fi
  if echo "$out" | grep -q "websearch.enabled is ON"; then marks="$marks+websearch"; fi
  rm -rf "$d"
  echo "$rc|$marks"
}
PWD_ROOT="$PWD"
assert_eq "0|banner+delegate" "$(_routing '{"default_delegate": true}')" \
  "session-routing: default_delegate on emits the delegation routing rule"
assert_eq "0|banner+websearch" "$(_routing '{"default_delegate": false, "websearch": {"enabled": true}}')" \
  "session-routing: websearch on emits the search routing rule"
assert_eq "0|banner" "$(_routing '{"default_delegate": false, "websearch": {"enabled": false}}')" \
  "session-routing: both off stays quiet (banner only, no context noise)"
assert_eq "0|banner" "$(_routing 'not json at all')" \
  "session-routing: a malformed config still exits 0 with the banner (never fails startup)"
assert_contains "$(cat plugins/kiro/.claude-plugin/plugin.json)" "session-routing.sh" \
  "kiro plugin.json wires SessionStart to session-routing.sh"
assert_file_executable "plugins/kiro/hooks/session-routing.sh" "session-routing.sh is executable"
assert_bash_syntax "plugins/kiro/hooks/session-routing.sh" "session-routing.sh has valid bash syntax"

assert_file_exists "plugins/kiro/hooks/pre-push-review.sh" "pre-push-review.sh exists"
assert_file_executable "plugins/kiro/hooks/pre-push-review.sh" "pre-push-review.sh is executable"
assert_bash_syntax "plugins/kiro/hooks/pre-push-review.sh" "pre-push-review.sh has valid bash syntax"

assert_json_valid "plugins/kiro/skills/kiro-delegate/kiro.defaults.json" "kiro.defaults.json is valid JSON after adding on_push/push_block"
assert_json_valid "plugins/co-agent/skills/co-agent/co-agent.defaults.json" "co-agent.defaults.json is valid JSON after adding push_gate"

if python3 -c "import py_compile" 2>/dev/null; then
  python3 -m py_compile \
    plugins/kiro/skills/kiro-delegate/scripts/hook_match.py \
    plugins/kiro/skills/kiro-delegate/scripts/kiro_review.py \
    plugins/kiro/skills/kiro-delegate/scripts/kiro_config.py \
    plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py \
    plugins/co-agent/skills/co-agent/scripts/co_agent_config.py 2>/tmp/push-gate-pycompile.err
  if [ $? -eq 0 ]; then
    pass "all push-gate-touched scripts compile cleanly"
  else
    fail "all push-gate-touched scripts compile cleanly" "$(cat /tmp/push-gate-pycompile.err)"
  fi
  rm -f /tmp/push-gate-pycompile.err
fi
