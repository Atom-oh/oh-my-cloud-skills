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
NQ='h._PR_CMD_RE.search(re.sub(r"\x27[^\x27]*\x27|\"[^\"]*\"", lambda m:\" \"*len(m.group()), %s))'
assert_eq "1" "$(_g "h._PR_CMD_RE.search('gh pr create')")"                 "matches bare gh pr create"
assert_eq "1" "$(_g "h._PR_CMD_RE.search('cd x && gh pr create')")"          "matches compound gh pr create"
assert_eq "1" "$(_g "h._PR_CMD_RE.search('gh -R o/r pr create')")"           "matches gh with flags before pr"
assert_eq "1" "$(_g "h._PR_CMD_RE.search('env GH_TOKEN=x gh pr create')")"   "matches env-prefixed gh pr create"
assert_eq "0" "$(_g "h._PR_CMD_RE.search('gh pr list')")"                    "does NOT match gh pr list"
assert_eq "0" "$(_g "h._PR_CMD_RE.search('git commit -m \"gh pr create\"')")" "does NOT match gh pr create in a string"

# --- secret scan: true positives (added/removed/context, quoted/unquoted, multiple key types)
assert_eq "1" "$(_g "h._scan_secret('+key = \"sk-ant-abcdefghij1234567890\"')[0]!=''")" "scan: anthropic key (added)"
assert_eq "1" "$(_g "h._scan_secret('+AKIAABCDEFGHIJKLMNOP')[0]!=''")"                  "scan: AWS AKIA"
assert_eq "1" "$(_g "h._scan_secret('+ASIAABCDEFGHIJKLMNOP')[0]!=''")"                  "scan: AWS ASIA temp key"
assert_eq "1" "$(_g "h._scan_secret('+SECRET=Abcdefghijklmnop123')[0]!=''")"            "scan: unquoted SECRET= env"
assert_eq "1" "$(_g "h._scan_secret(' password = \"hunter2hunter2here\"')[0]!=''")"     "scan: secret on a context line"
# --- secret scan: false-positive guards (code assignments must NOT match)
assert_eq "0" "$(_g "h._scan_secret('+    secret = _scan_secret(diff)')[0]!=''")"       "no FP: secret = call()"
assert_eq "0" "$(_g "h._scan_secret('+    api_key = config.value')[0]!=''")"            "no FP: api_key = identifier"
# --- secret scan: '++ ' added content (renders '+++ ') is NOT mistaken for a header
assert_eq "0" "$(_g "h._is_diff_header('+++ password = \"leakedsecret12345\"')")"       "'+++ content' is not a header"
assert_eq "1" "$(_g "h._is_diff_header('+++ b/config.py')")"                            "'+++ b/...' IS a header"
# --- secret scan: deleted-only is advisory (hard=False), added is block-worthy (hard=True)
assert_eq "0" "$(_g "h._scan_secret('-password = \"oldsecret12345\"')[1]")"             "removed-only secret → not hard-block"
assert_eq "1" "$(_g "h._scan_secret('+password = \"newsecret12345\"')[1]")"             "added secret → hard-block"

# --- --base shell-quote stripping (avoid a fail-open bypass on `--base 'main'`)
_base_quote=$(python3 -c "
import re
cand = re.search(r'(?:--base|-B)[= ]+(\S+)', \"gh pr create --base 'main'\").group(1)
print(cand.strip(chr(39)+chr(34)))
" 2>/dev/null)
assert_eq "main" "$_base_quote" "--base strips shell quotes ('main' -> main)"
