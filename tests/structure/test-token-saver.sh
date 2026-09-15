TOKEN_SAVER_TEST_LOG=$(mktemp "${TMPDIR:-/tmp}/token-saver-test.XXXXXX")
if python3 tests/structure/test-token-saver.py > "$TOKEN_SAVER_TEST_LOG" 2>&1; then
    pass "token-saver injects bounded policy without changing host state"
else
    cat "$TOKEN_SAVER_TEST_LOG"
    fail "token-saver injects bounded policy without changing host state"
fi
rm -f "$TOKEN_SAVER_TEST_LOG"
