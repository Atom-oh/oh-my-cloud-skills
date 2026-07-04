# tests/structure/test-co-agent-pr-gate.sh   (sourced by run-all.sh — no shebang, no exit)
# Regression tests for the co-agent PR consensus gate (consensus_hooks.py pre-pr-gate):
# command matching (over/under-match), secret-scan TP/FP + deleted-only, quorum, --base quoting.

GATE_PY="plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py"
assert_file_exists "$GATE_PY" "consensus_hooks.py exists"

# helper: run a python predicate against the module, echo 1/0
_g() { python3 -c "
import sys; sys.path.insert(0,'plugins/co-agent/skills/co-agent/scripts')
import re, consensus_hooks as h
print(1 if ($1) else 0)
" 2>/dev/null; }

# --- command matching: real gh pr create (with prefixes/flags) matches; non-create / quoted don't
assert_eq "1" "$(_g "h._PR_CMD_RE.search('gh pr create')")"                 "matches bare gh pr create"
assert_eq "1" "$(_g "h._PR_CMD_RE.search('cd x && gh pr create')")"          "matches compound gh pr create"
assert_eq "1" "$(_g "h._PR_CMD_RE.search('gh -R o/r pr create')")"           "matches gh with flags before pr"
assert_eq "1" "$(_g "h._PR_CMD_RE.search('env GH_TOKEN=x gh pr create')")"   "matches env-prefixed gh pr create"
assert_eq "0" "$(_g "h._PR_CMD_RE.search('gh pr list')")"                    "does NOT match gh pr list"
assert_eq "0" "$(_g "h._PR_CMD_RE.search('git commit -m \"gh pr create\"')")" "does NOT match gh pr create in a string"

# --- secret scan: true positives (added/removed/context, quoted/unquoted, multiple key types)
assert_eq "1" "$(_g "h._scan_secret('+key = \"sk-ant-abcdefghij1234567890\"')[0]!=''")" "scan: anthropic key (added)"  # pragma: allowlist secret
assert_eq "1" "$(_g "h._scan_secret('+AKIAABCDEFGHIJKLMNOP')[0]!=''")"                  "scan: AWS AKIA"  # pragma: allowlist secret
assert_eq "1" "$(_g "h._scan_secret('+ASIAABCDEFGHIJKLMNOP')[0]!=''")"                  "scan: AWS ASIA temp key"  # pragma: allowlist secret
assert_eq "1" "$(_g "h._scan_secret('+SECRET=Abcdefghijklmnop123')[0]!=''")"            "scan: unquoted SECRET= env"  # pragma: allowlist secret
assert_eq "1" "$(_g "h._scan_secret(' password = \"hunter2hunter2here\"')[0]!=''")"     "scan: secret on a context line"  # pragma: allowlist secret
# --- secret scan: false-positive guards (code assignments must NOT match)
assert_eq "0" "$(_g "h._scan_secret('+    secret = _scan_secret(diff)')[0]!=''")"       "no FP: secret = call()"
assert_eq "0" "$(_g "h._scan_secret('+    api_key = config.value')[0]!=''")"            "no FP: api_key = identifier"
# --- secret scan: '++ ' added content (renders '+++ ') is NOT mistaken for a header
assert_eq "0" "$(_g "h._is_diff_header('+++ password = \"leakedsecret12345\"')")"       "'+++ content' is not a header"  # pragma: allowlist secret
assert_eq "1" "$(_g "h._is_diff_header('+++ b/config.py')")"                            "'+++ b/...' IS a header"
# --- secret scan: hunk-aware — a secret on a '+++ b/...'-rendered line INSIDE a hunk is scanned
#     (added content whose text starts '++ b/' renders '+++ b/'); a REAL pre-hunk header is skipped
assert_eq "1" "$(_g "h._scan_secret('@@ -1 +1 @@'+chr(10)+'+++ b/x AKIAABCDEFGHIJKLMNOP')[0]!=''")" "in-hunk '+++ b/' content with a secret is NOT skipped as header"  # pragma: allowlist secret
assert_eq "0" "$(_g "h._scan_secret('diff --git a/x b/x'+chr(10)+'+++ b/x AKIAABCDEFGHIJKLMNOP')[0]!=''")" "real pre-hunk '+++ b/' header is still skipped"  # pragma: allowlist secret
# --- secret scan: only ADDED lines hard-block; removed AND context are advisory (hard=False) so a
#     pre-existing committed secret near an unrelated change can't permanently block its PR
assert_eq "0" "$(_g "h._scan_secret('-password = \"oldsecret12345\"')[1]")"             "removed-only secret → not hard-block"  # pragma: allowlist secret
assert_eq "1" "$(_g "h._scan_secret('+password = \"newsecret12345\"')[1]")"             "added secret → hard-block"  # pragma: allowlist secret
assert_eq "0" "$(_g "h._scan_secret(' password = \"ctxsecret123456\"')[1]")"           "context-line secret → advisory, not hard-block"  # pragma: allowlist secret
assert_eq "1" "$(_g "h._scan_secret(' password = \"ctxsecret123456\"')[0]!=''")"       "context-line secret still refused (not fanned out)"  # pragma: allowlist secret

# --- allowlist is restricted to EXPLICIT markers (a loose "not a secret" no longer disarms it)
assert_eq "1" "$(_g "h._scan_secret('+password = \"realhunter2secret\"  # not a secret')[0]!=''")" "scan: real secret + 'not a secret' comment still detected"  # pragma: allowlist secret
assert_eq "0" "$(_g "h._scan_secret('+password = \"fixturehunter2val\"  # pragma: allowlist secret')[0]!=''")" "scan: explicit pragma:allowlist marker skips"

# --- cwd-changing compound (cd/pushd before gh pr create) is detected → gate skips that scope
assert_eq "1" "$(_g "h._PRECEDING_CD.search('cd sub')")"                    "_PRECEDING_CD matches a leading cd"
assert_eq "1" "$(_g "h._PRECEDING_CD.search('pushd /x')")"                  "_PRECEDING_CD matches pushd"
assert_eq "1" "$(_g "h._PRECEDING_CD.search('cd ')")"                       "_PRECEDING_CD matches 'cd \"my dir\"' (blanked → 'cd ')"
assert_eq "1" "$(_g "h._PRECEDING_CD.search('cd')")"                        "_PRECEDING_CD matches bare cd (→ home)"
assert_eq "0" "$(_g "h._PRECEDING_CD.search('git add .')")"                 "_PRECEDING_CD does NOT match non-cd"
assert_eq "0" "$(_g "h._PRECEDING_CD.search('cdrom_mount')")"               "_PRECEDING_CD does NOT match 'cdrom...'"

# --- state-changing git before gh pr create → skip+advisory; matched on quote-blanked cmd_detect
assert_eq "1" "$(_g "bool(h._PRECEDING_GIT_MUT.search('git commit -m x && '))")"       "_PRECEDING_GIT_MUT matches git commit"
assert_eq "1" "$(_g "bool(h._PRECEDING_GIT_MUT.search('git add -A && '))")"            "_PRECEDING_GIT_MUT matches git add"
assert_eq "0" "$(_g "bool(h._PRECEDING_GIT_MUT.search('git status && '))")"            "_PRECEDING_GIT_MUT does NOT match read-only git status"

# --- _flag_value: parses --base/--head from the quote-BLANKED cmd, ignoring a flag NAME that only
#     appears inside a quoted body, while preserving a legitimately quoted value (`--base 'main'`).
_fv_overmatch=$(python3 -c "
import sys; sys.path.insert(0,'plugins/co-agent/skills/co-agent/scripts')
import re, consensus_hooks as h
cmd = 'gh pr create --title \"switch --base to prod\" --base main'
det = re.sub(r'\x27[^\x27]*\x27|\"[^\"]*\"', lambda m: chr(32)*len(m.group()), cmd)
print(h._flag_value(cmd, det, r'--base|-B'))
" 2>/dev/null)
assert_eq "main" "$_fv_overmatch" "_flag_value ignores --base inside a quoted title, takes the real one"
_fv_quoted=$(python3 -c "
import sys; sys.path.insert(0,'plugins/co-agent/skills/co-agent/scripts')
import re, consensus_hooks as h
cmd = \"gh pr create --base 'main'\"
det = re.sub(r'\x27[^\x27]*\x27|\"[^\"]*\"', lambda m: chr(32)*len(m.group()), cmd)
print(h._flag_value(cmd, det, r'--base|-B'))
" 2>/dev/null)
assert_eq "main" "$_fv_quoted" "_flag_value preserves a quoted value (--base 'main' -> main)"

# --- env sanitizer: drops credential-looking vars not on the peer's auth whitelist, keeps PATH
_env_strip=$(PATH="$PATH" GH_TOKEN=x AWS_SECRET_ACCESS_KEY=y OPENAI_API_KEY=z python3 -c "
import sys; sys.path.insert(0,'plugins/co-agent/skills/co-agent/scripts')
import consensus_hooks as h
e = h._sanitized_env('codex')
print(int('GH_TOKEN' not in e and 'AWS_SECRET_ACCESS_KEY' not in e and 'OPENAI_API_KEY' in e and 'PATH' in e))
" 2>/dev/null)
assert_eq "1" "$_env_strip" "_sanitized_env drops GH_TOKEN/AWS_* but keeps codex OPENAI_API_KEY + PATH"
# --- env regex: PAT/generic-KEY/PWD suffixes are caught, but PATH/PWD/KEYBOARD are preserved
assert_eq "1" "$(_g "bool(h._SENSITIVE_ENV_RE.search('GITLAB_PAT'))")"      "env: GITLAB_PAT is sensitive"
assert_eq "1" "$(_g "bool(h._SENSITIVE_ENV_RE.search('OPENAI_KEY'))")"      "env: OPENAI_KEY is sensitive"
assert_eq "1" "$(_g "bool(h._SENSITIVE_ENV_RE.search('DB_PWD'))")"          "env: DB_PWD is sensitive"
assert_eq "0" "$(_g "bool(h._SENSITIVE_ENV_RE.search('PATH'))")"            "env: PATH is NOT stripped"
assert_eq "0" "$(_g "bool(h._SENSITIVE_ENV_RE.search('PWD'))")"             "env: bare PWD is NOT stripped"
assert_eq "0" "$(_g "bool(h._SENSITIVE_ENV_RE.search('KEYBOARD'))")"        "env: KEYBOARD is NOT stripped"

# --- verdict regex: a peer that naturally drifts to the past-tense "BLOCKED"/"PASSED" must
#     still be counted (not silently treated as an unparseable non-vote / dropped veto)
assert_eq "1" "$(_g "bool(h._VERDICT_RE.match('BLOCK: adds a hardcoded secret'))")"   "verdict: exact BLOCK: still matches"
assert_eq "1" "$(_g "bool(h._VERDICT_RE.match('BLOCKED: adds a hardcoded secret'))")" "verdict: BLOCKED variant also matches"
assert_eq "1" "$(_g "bool(h._VERDICT_RE.match('PASSED'))")"                           "verdict: PASSED variant also matches"
assert_eq "0" "$(_g "bool(h._VERDICT_RE.match('BLOCKING something unrelated'))")"     "verdict: BLOCKING (not a verdict token) does NOT match"
assert_eq "0" "$(_g "bool(h._VERDICT_RE.match('PASSWORD is not a verdict'))")"        "verdict: PASSWORD does NOT match"
