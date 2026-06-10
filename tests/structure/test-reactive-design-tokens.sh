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

TC="$(cat "$RP/assets/theme.css" 2>/dev/null || true)"
assert_grep_match "@import\s+url\(['\"]?design-tokens\.css" "$TC" "theme.css imports design-tokens.css"
assert_contains "$TC" ".theme-dark" "dark theme scope present"
assert_contains "$TC" ".theme-light" "light theme scope present"
assert_grep_match ":root, ?\.theme-light" "$TC" "light defaults applied via :root, .theme-light (beats design-tokens :root by source order)"
assert_grep_match "\.theme-dark[^}]*--surface-1" "$TC" "dark scope assigns --surface-1"
for cls in card-grid metric-card tab-set callout comparison flow-group; do
  assert_grep_match "\.$cls\b" "$TC" "component primitive .$cls defined in theme.css"
done
assert_grep_no_match "#00d4ff" "$TC" "theme.css has no legacy cyan literal"

TC3="$(cat "$RP/assets/theme.css" 2>/dev/null || true)"
for bad in "0\.17rem" "0\.21rem" "0\.29rem" "0\.42rem" "0\.58rem" "0\.67rem" "0\.83rem" "2\.7rem"; do
  assert_grep_no_match "$bad" "$TC3" "legacy off-scale value $bad removed"
done
assert_grep_no_match "var\(--yellow,\s*#f1c40f" "$TC3" "drifted --yellow fallback removed"
assert_grep_no_match "var\(--text-muted,\s*#8b8fa3" "$TC3" "drifted --text-muted fallback removed"
assert_grep_match "var\(--space-" "$TC3" "rules consume spacing tokens"
assert_grep_match "var\(--radius-" "$TC3" "rules consume radius tokens"

# --- FINAL-GATE: light-first cascade + theme-scoped legacy vars + callout roles ---
TC4="$(cat "$RP/assets/theme.css" 2>/dev/null || true)"
# Block-spanning checks: collapse newlines so [^}]* (line-oriented in grep -P)
# can span a multi-line CSS rule body up to the closing brace.
TC4FLAT="$(printf '%s' "$TC4" | tr '\n' ' ')"
assert_grep_match ":root, ?\.theme-light" "$TC4" "light default uses :root (wins specificity vs design-tokens :root)"
assert_grep_no_match ":where\(html\), ?\.theme-light" "$TC4" "no zero-specificity :where light default"
# legacy base vars are theme-scoped, not on a bare dark :root anymore
assert_grep_match "\.theme-dark[^}]*--bg-primary" "$TC4FLAT" "dark scope defines --bg-primary"
assert_grep_match "(:root, ?\.theme-light)[^}]*--bg-primary" "$TC4FLAT" "light scope defines --bg-primary"
# callout role variant bound to semantic role after primitive
assert_grep_match "\.callout\.callout-info[^}]*var\(--info" "$TC4FLAT" "callout-info bound to --info role token"

# --- P4 regression: the new design-tokens.css MUST ship with generated/exported decks ---
# (theme.css @imports it; if it isn't copied, every --space/--text/--radius token breaks)
REMARP="$(cat "$RP/scripts/remarp_to_slides.py" 2>/dev/null || true)"
assert_grep_match "_copy_framework_assets" "$REMARP" "framework asset-copy routine exists"
assert_grep_match "['\"]design-tokens\.css['\"]" "$REMARP" "remarp copies design-tokens.css to common/"
EXPORTJS="$(cat "$RP/assets/export-utils.js" 2>/dev/null || true)"
assert_grep_match "design-tokens\.css" "$EXPORTJS" "export-utils ZIP bundles design-tokens.css"
