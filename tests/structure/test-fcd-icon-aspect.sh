FCD_ASPECT_LOG=$(mktemp "${TMPDIR:-/tmp}/fcd-icon-aspect.XXXXXX")
if node tests/structure/test-fcd-icon-aspect.cjs > "$FCD_ASPECT_LOG" 2>&1; then
    pass "AWS Light builders preserve icon proportions and slot geometry"
else
    cat "$FCD_ASPECT_LOG"
    fail "AWS Light builders preserve icon proportions and slot geometry"
fi
rm -f "$FCD_ASPECT_LOG"
