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

# --- content-quality: NOTE_STRUCTURE ---
RP="plugins/aws-content-plugin/skills/reactive-presentation"
# `[요약]` must match as a LITERAL — assert_contains uses grep BRE (no -F) where `[요약]` is a
# bracket expression (any one of 요/약). Use assert_grep_match with PCRE-escaped brackets.
assert_grep_match "\[요약\]" "$(cat "$RP/references/remarp-format-guide.md" 2>/dev/null || true)" "remarp-format-guide documents [요약] note layer"
assert_grep_match "\[요약\]" "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "SKILL.md references the structured note schema"
SC="$RP/scripts/remarp_to_slides.py"
D="$(mktemp -d "${TMPDIR:-/tmp}/ns.XXXXXX")"
printf -- '---\nratio: "16:9"\n---\n' > "$D/_presentation.md"
printf -- '---\nremarp: true\n---\n## A title\n\nSome body text here.\n\n:::notes\n{timing: 2min}\nThis is a free-form note with no summary block, long enough to pass the length check easily by adding words and words and more words.\n:::\n' > "$D/01.md"
OUT="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_contains "$OUT" "NOTE_STRUCTURE" "lint flags notes missing [요약]"
printf -- '---\nremarp: true\n---\n## A title\n\nSome body text here.\n\n:::notes\n{timing: 2min}\n[요약]\n• key point one here\n• key point two here\nThe spoken script in conversational Korean goes here with enough words to pass length.\n:::\n' > "$D/01.md"
OUT2="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_grep_no_match "NOTE_STRUCTURE" "$OUT2" "structured note not flagged"
rm -rf "$D"

# --- content-quality: title voice + TITLE_LENGTH ---
assert_contains "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "체언 종결" "SKILL.md documents noun-ending subtitle voice"
assert_contains "$(cat "$RP/references/slide-patterns.md" 2>/dev/null || true)" "headline" "slide-patterns documents headline title voice"
SC="$RP/scripts/remarp_to_slides.py"
D="$(mktemp -d "${TMPDIR:-/tmp}/tl.XXXXXX")"
printf -- '---\nratio: "16:9"\n---\n' > "$D/_presentation.md"
printf -- '---\nremarp: true\n---\n## 이것은 스물여덟 글자를 훨씬 넘어가는 아주 길고 장황한 슬라이드 제목입니다 정말로\n\nbody\n' > "$D/01.md"
OUT="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_contains "$OUT" "TITLE_LENGTH" "lint flags over-long title"
printf -- '---\nremarp: true\n---\n## 비용은 싸졌고 모델은 똑똑해졌다\n\nbody\n' > "$D/01.md"
OUT2="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_grep_no_match "TITLE_LENGTH" "$OUT2" "concise title not flagged"
rm -rf "$D"
