if python3 -B tests/structure/test-kiro-worktree-preparation.py; then
  pass "Kiro preparation refuses collisions and symlink races; logs stay run-scoped"
else
  fail "Kiro preparation behavioral regressions"
fi
