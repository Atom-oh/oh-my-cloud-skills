# Co-agent push review classification and regression checks.
# --- co-agent push gate: the skip classes skip classes for commands whose
# pushed content cannot be described by the current-branch range. Before this, the gate
# reviewed its OWN root for a push aimed at another repo, and blocked a ref deletion on
# the unrelated diff of unpushed local commits. ---
_pgs() { python3 tests/hooks/_push_gate_skip_probe.py "$1"; }
# Normalize skip reasons when testing reviewable versus unreviewable refspecs.
_pgb() { python3 tests/hooks/_push_gate_skip_probe.py --normalized "$1"; }
assert_eq "GATED" "$(_pgs 'git push')" "push gate: a plain push is still gated"
assert_eq "GATED" "$(_pgs 'git push -u origin HEAD')" "push gate: flags do not change the classification"
assert_eq "skip:redirect" "$(_pgs 'git -C /other/repo push')" "push gate: a repo redirect is SKIPPED, not reviewed against the wrong root"
assert_eq "skip:redirect" "$(_pgs 'GIT_WORK_TREE=/elsewhere git push')" "push gate: an env-prefix work-tree redirect is SKIPPED too"
assert_eq "skip:delete" "$(_pgs 'git push origin --delete oldbranch')" "push gate: a ref deletion has no content to review"
assert_eq "GATED" "$(_pgs 'git push && rm --delete-after x')" "push gate: a --delete belonging to a LATER command does not suppress this push's review"

# A push whose content is not "current branch vs upstream" cannot be judged by the range
# the gate computes — reviewing it anyway lets unreviewed content pass or hard-blocks on
# an unrelated diff. The gate must skip it, and must still review an ordinary push.
assert_eq "GATED" "$(_pgb 'git push')" "refspec: a bare push is reviewed by the gate"
assert_eq "GATED" "$(_pgb 'git push origin')" "refspec: a lone remote still means the current branch"
assert_eq "GATED" "$(_pgb 'git push -u origin HEAD')" "refspec: HEAD names the current branch"
assert_eq "skip" "$(_pgb 'git push origin other-branch')" "refspec: an explicit branch refspec is skipped by the gate"
assert_eq "skip" "$(_pgb 'git push origin src:dst')" "refspec: a src:dst refspec is skipped by the gate"
assert_eq "skip" "$(_pgb 'git push --all')" "refspec: --all sends refs the computed range does not describe"
assert_eq "skip" "$(_pgb 'git push --tags')" "refspec: --tags likewise"
assert_eq "skip" "$(_pgb 'git push --mirror origin')" "refspec: --mirror likewise"

# Naming the CURRENT branch is the commonest push (`git push -u origin <branch>`) and sends
# exactly what the range describes, so it is reviewed. The branch is read from the hook's
# cwd, so these run inside a throwaway repo; anything unresolvable stays skipped.
_PG_ROOT="$PWD"
_PG_REPO="$(mktemp -d "${TMPDIR:-/tmp}/push-gate-repo-XXXXXX")"
_pgr() { (cd "$_PG_REPO" && python3 "$_PG_ROOT/tests/hooks/_push_gate_skip_probe.py" --normalized "$1"); }
git init -q -b feat-x "$_PG_REPO"
git -C "$_PG_REPO" -c user.name=t -c user.email=t@example.invalid commit -q --allow-empty -m init
assert_eq "GATED" "$(_pgr 'git push -u origin feat-x')" "refspec: the current branch named explicitly is reviewed by the gate"
assert_eq "GATED" "$(_pgr 'git push origin feat-x')" "refspec: the current branch without -u is reviewed too"
assert_eq "skip" "$(_pgr 'git push origin other-branch')" "refspec: another branch is still skipped when a branch resolves"
assert_eq "skip" "$(_pgr 'git push origin feat-x:other')" "refspec: src:dst naming the branch is still skipped"
assert_eq "skip" "$(_pgr 'git push origin feat-x other-branch')" "refspec: a second refspec after the current branch is skipped"
assert_eq "skip" "$(_pgr 'git push origin HEAD other-branch')" "refspec: a second refspec after HEAD is skipped"
git -C "$_PG_REPO" checkout -q --detach
assert_eq "skip" "$(_pgr 'git push origin feat-x')" "refspec: a detached HEAD cannot confirm the branch, so the push is skipped"
assert_eq "GATED" "$(_pgr 'git push -u origin HEAD')" "refspec: HEAD is still reviewed on a detached HEAD"
rm -rf "$_PG_REPO"
_PG_NOREPO="$(mktemp -d "${TMPDIR:-/tmp}/push-gate-norepo-XXXXXX")"
assert_eq "skip" "$( (cd "$_PG_NOREPO" && python3 "$_PG_ROOT/tests/hooks/_push_gate_skip_probe.py" --normalized 'git push origin feat-x') )" "refspec: outside a repository the branch is unresolved, so the push is skipped"
rm -rf "$_PG_NOREPO"

# --- co-agent push gate: --dry-run skip class, and the same compound-command fix as
# a dry-run-then-real-push in ONE invocation must still be
# gated on the real push, not blinded by the first occurrence's class. ---
assert_eq "skip:dry-run" "$(_pgs 'git push --dry-run')" "push gate: a lone --dry-run push is skipped"
assert_eq "skip" "$(_pgb 'git push --dry-run')" "dry-run: the gate skip a lone dry-run push"
assert_eq "GATED" "$(_pgs 'git push --dry-run && git push')" "push gate: dry-run THEN a real push in one invocation is still GATED"
assert_eq "GATED" "$(_pgb 'git push --dry-run && git push')" "dry-run compound: the gate still review the real push"

# --- co-agent push gate: bundled short flags, and the same all-occurrences fix
# applied to the inline CO_AGENT_PUSH_GATE=off bypass prefix ---
assert_eq "skip:dry-run" "$(_pgs 'git push -vn')" "push gate: bundled -vn dry-run is skipped"
assert_eq "skip:delete" "$(_pgs 'git push origin -fd foo')" "push gate: bundled -fd delete is skipped"
assert_eq "GATED" "$(_pgs 'git push -odeploy')" "push gate: -odeploy is a push-option value, not a bundled delete"
assert_eq "GATED" "$(_pgs 'git push -onotify')" "push gate: -onotify is a push-option value, not a bundled dry-run"
assert_eq "GATED" "$(_pgs 'git push -vodeploy')" "push gate: -vodeploy (-v -o deploy) is not a bundled delete despite the embedded 'd'"
assert_eq "GATED" "$(_pgs 'git push -vonotify')" "push gate: -vonotify (-v -o notify) is not a bundled dry-run despite the embedded 'n'"
assert_eq "GATED" "$(_pgs 'CO_AGENT_PUSH_GATE=off git push --dry-run && git push')" "push gate: bypass on the FIRST push only does not bypass the second, unprefixed push"
assert_eq "skip:bypass" "$(_pgs 'CO_AGENT_PUSH_GATE=off git push')" "push gate: a lone bypassed push is skipped"

assert_json_valid "plugins/co-agent/skills/co-agent/co-agent.defaults.json" "co-agent.defaults.json is valid JSON after adding push_gate"

if python3 -c "import py_compile" 2>/dev/null; then
  # `if python3 ...; then`, NOT `python3 ...` followed by `[ $? -eq 0 ]`: this file is
  # SOURCED by run-all.sh under `set -e`, so a bare failing command aborts the whole
  # suite — the fail branch below was unreachable and every later test silently skipped.
  if python3 -m py_compile \
    plugins/co-agent/skills/co-agent/scripts/consensus_hooks.py \
    plugins/co-agent/skills/co-agent/scripts/co_agent_config.py 2>/tmp/push-gate-pycompile.err; then
    pass "all push-gate-touched scripts compile cleanly"
  else
    fail "all push-gate-touched scripts compile cleanly" "$(cat /tmp/push-gate-pycompile.err)"
  fi
  rm -f /tmp/push-gate-pycompile.err
fi
