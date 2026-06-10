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

# --- Task 6: design-lint validate rules ---
SC="$RP/scripts/remarp_to_slides.py"
D="$(mktemp -d "${TMPDIR:-/tmp}/rpl.XXXXXX")"
printf -- '---\nratio: "16:9"\n---\n' > "$D/_presentation.md"
printf -- '---\nremarp: true\n---\n## S\n\n:::html\n<div style="color:#00d4ff;padding:13px;background:rgba(0,0,0,.3)">x</div>\n:::\n' > "$D/01.md"
OUT="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_contains "$OUT" "RAW_HEX" "lint flags raw hex"
assert_contains "$OUT" "INLINE_STYLE" "lint flags inline style="
assert_contains "$OUT" "OFF_SCALE" "lint flags off-scale px (13px)"
assert_contains "$OUT" "RAW_RGBA" "lint flags raw rgba()"
JOUT="$(python3 "$SC" validate "$D" --json 2>&1 || true)"
assert_contains "$JOUT" "RAW_HEX" "json output carries rule ids"
printf -- '---\nremarp: true\n---\n## S\n\n:::html\n<div class="card-grid"><div class="metric-card">x</div></div>\n:::\n' > "$D/01.md"
OUT2="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_grep_no_match "RAW_HEX" "$OUT2" "token slide not flagged for hex"
assert_grep_no_match "INLINE_STYLE" "$OUT2" "token slide not flagged for inline style"
rm -rf "$D"
