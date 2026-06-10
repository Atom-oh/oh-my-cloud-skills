# tests/structure/test-reactive-design-tokens.sh   (sourced by run-all.sh — no shebang, no exit)
RP="plugins/aws-content-plugin/skills/reactive-presentation"
DT="$RP/assets/design-tokens.css"
assert_file_exists "$DT" "design-tokens.css exists"
T="$(cat "$DT" 2>/dev/null || true)"
for tok in text-xs text-sm text-base text-lg text-xl text-2xl text-3xl text-4xl; do
  assert_grep_match "\-\-$tok\b" "$T" "type token --$tok defined"
done
for tok in leading-tight leading-normal leading-relaxed weight-regular weight-medium weight-semibold weight-bold; do
  assert_grep_match "\-\-$tok\b" "$T" "typography role token --$tok defined"
done
for n in 1 2 3 4 5 6 7 8; do
  assert_grep_match "\-\-space-$n\b" "$T" "spacing token --space-$n defined"
done
for tok in radius-sm radius-md radius-lg radius-pill shadow-1 shadow-2 shadow-3 shadow-glow \
           duration-fast duration-normal duration-slow z-base z-nav z-overlay z-modal z-toast; do
  assert_grep_match "\-\-$tok\b" "$T" "token --$tok defined"
done
for tok in surface-1 surface-2 surface-3 on-surface on-surface-muted accent accent-subtle accent-on \
           info info-subtle info-on success success-subtle success-on warning warning-subtle warning-on danger danger-subtle danger-on; do
  assert_grep_match "\-\-$tok\b" "$T" "color-role token --$tok defined"
done
assert_grep_match "\-\-space-2:\s*0?\.5rem" "$T" "--space-2 is 0.5rem (8px grid)"
assert_grep_match "\-\-space-4:\s*1rem" "$T" "--space-4 is 1rem (16px grid)"
assert_grep_match "\-\-text-base:\s*1rem" "$T" "--text-base is 1rem"
