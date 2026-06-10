# tests/structure/test-reactive-design-lint.sh   (sourced by run-all.sh — no shebang, no exit)
RP="plugins/aws-content-plugin/skills/reactive-presentation"
for f in SKILL.md references/slide-patterns.md references/colors-reference.md; do
  N=$( { grep -oE "#[0-9a-fA-F]{6}" "$RP/$f" 2>/dev/null || true; } | wc -l | tr -d ' ')
  assert_eq "0" "$N" "$f has no raw 6-digit hex"
done
SN=$( { grep -oE "style=\"[^\"]*(color|background|padding|border-radius):[^\"]*\"" "$RP/SKILL.md" 2>/dev/null || true; } | wc -l | tr -d ' ')
assert_eq "0" "$SN" "SKILL.md templates carry no inline color/spacing styles"
assert_contains "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "var(--" "SKILL.md templates use CSS token vars"
assert_contains "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "card-grid" "SKILL.md uses token-backed primitives"
