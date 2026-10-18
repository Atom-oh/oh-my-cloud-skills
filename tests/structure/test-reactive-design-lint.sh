# tests/structure/test-reactive-design-lint.sh   (sourced by run-all.sh — no shebang, no exit)
RP="plugins/aws-content-plugin/skills/reactive-presentation"
for f in SKILL.md references/authoring-rules.md references/slide-patterns.md references/colors-reference.md; do
  N=$( { grep -oE "#[0-9a-fA-F]{6}" "$RP/$f" 2>/dev/null || true; } | wc -l | tr -d ' ')
  assert_eq "0" "$N" "$f has no raw 6-digit hex"
done
# Authoring rules/templates were relocated from SKILL.md into references/authoring-rules.md
# (progressive disclosure — lean SKILL.md). Assert content lives in the skill (either file).
SKILL_ALL="$(cat "$RP/SKILL.md" "$RP/references/authoring-rules.md" 2>/dev/null || true)"
SN=$( { grep -oE "style=\"[^\"]*(color|background|padding|border-radius):[^\"]*\"" "$RP/SKILL.md" "$RP/references/authoring-rules.md" 2>/dev/null || true; } | wc -l | tr -d ' ')
assert_eq "0" "$SN" "SKILL/authoring-rules templates carry no inline color/spacing styles"
assert_contains "$SKILL_ALL" "var(--" "authoring templates use CSS token vars"
assert_contains "$SKILL_ALL" "card-grid" "authoring uses token-backed primitives"

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
assert_contains "$SKILL_ALL" "noun-form endings" "authoring documents noun-ending subtitle voice"
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

# --- content-quality: consolidated Forbidden AI-tells ---
SKL="$SKILL_ALL"
assert_contains "$SKL" "Forbidden" "skill has a consolidated Forbidden AI-tells section"
assert_contains "$SKL" "AI-slide tells" "Forbidden section titled for AI-slide tells"
assert_contains "$SKL" "RAW_HEX" "Forbidden section references the RAW_HEX lint rule"
assert_contains "$SKL" "NOTE_STRUCTURE" "Forbidden section references the NOTE_STRUCTURE lint rule"

# --- content-quality: source-omission cross-check ---
CRA="$(cat plugins/aws-content-plugin/agents/content-review-agent.md 2>/dev/null || true)"
assert_contains "$CRA" "omission" "content-review-agent has a source-omission cross-check"
assert_contains "$CRA" "diagram" "omission check lists architecture diagrams as a common gap"

# --- content-quality P4: section-divider (@type: title) must NOT trip NOTE_STRUCTURE/TITLE_LENGTH ---
SC="$RP/scripts/remarp_to_slides.py"
D="$(mktemp -d "${TMPDIR:-/tmp}/tsec.XXXXXX")"
printf -- '---\nratio: "16:9"\n---\n' > "$D/_presentation.md"
# a section divider: long title + a short transition note with no [요약] — both legit for a divider
printf -- '---\nremarp: true\n---\n@type: title\n## 2장. 관측성 스택 심화 아키텍처와 운영 전략 그리고 더 긴 제목\n\n:::notes\n{timing: 1min}\n다음 장으로 넘어가겠습니다. 이번 장에서는 관측성 스택을 깊이 다룹니다.\n:::\n' > "$D/01.md"
OUT="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_grep_no_match "NOTE_STRUCTURE" "$OUT" "section-divider not flagged for missing [요약]"
assert_grep_no_match "TITLE_LENGTH" "$OUT" "section-divider title length not flagged"
rm -rf "$D"

# --- reactive-nav-detail Task 6: detail layer, search and copy gates documented ---
RP6="plugins/aws-content-plugin/skills/reactive-presentation"
for f in "$RP6/REMARP.md" "$RP6/references/remarp-format-guide.md"; do
  F6="$(cat "$f" 2>/dev/null || true)"
  assert_contains "$F6" ":::detail" "$(basename "$f") documents :::detail"
  assert_contains "$F6" "{tip=" "$(basename "$f") documents {tip=...}"
done
assert_contains "$(cat "$RP6/references/keyboard-shortcuts.md" 2>/dev/null)" "Ctrl+K" "keyboard-shortcuts.md lists Ctrl+K search"
AR6="$(cat "$RP6/references/authoring-rules.md" 2>/dev/null || true)"
for rule in EM_DASH AI_TONE SENTENCE_RUNON; do
  assert_contains "$AR6" "$rule" "authoring-rules.md names the $rule rule"
done
assert_contains "$AR6" "one claim line" "authoring-rules.md states the one-claim-line card rule"
AG6="$(cat plugins/aws-content-plugin/agents/reactive-presentation-agent.md 2>/dev/null || true)"
assert_contains "$AG6" ":::detail" "reactive-presentation-agent prompt teaches :::detail"
assert_grep_match "EM_DASH[^\n]*(must|fix)" "$AG6" "agent prompt makes EM_DASH findings must-fix"
assert_contains "$(cat "$RP6/references/framework-guide.md" 2>/dev/null)" "deck-overlay.js" "framework-guide lists deck-overlay.js"
assert_contains "$(cat "$RP6/references/framework-contract.md" 2>/dev/null)" "rp-detail" "framework-contract documents the rp-detail DOM contract"
EX6="$(cat "$RP6/assets/example-deck/index.html" 2>/dev/null || true)"
assert_contains "$EX6" "deck-overlay.css" "example deck links deck-overlay.css"
assert_contains "$EX6" "data-detail=" "example deck has a detail-backed term"
assert_contains "$EX6" "rp-detail-store" "example deck has a detail store"
EX6_OV="$(grep -n 'deck-overlay.js' <<< "$EX6" | head -1 | cut -d: -f1)"
EX6_FW="$(grep -n 'slide-framework.js' <<< "$EX6" | head -1 | cut -d: -f1)"
EX6_ORDER="no"; [ -n "$EX6_OV" ] && [ -n "$EX6_FW" ] && [ "$EX6_OV" -lt "$EX6_FW" ] && EX6_ORDER="yes"
assert_eq "yes" "$EX6_ORDER" "example deck loads deck-overlay.js before slide-framework.js"
for f in doc-sites/docs/aws-content-plugin/skills/reactive-presentation.md \
         doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/aws-content-plugin/skills/reactive-presentation.md \
         doc-sites/docs/aws-content-plugin/agents/reactive-presentation-agent.md \
         doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/aws-content-plugin/agents/reactive-presentation-agent.md; do
  assert_contains "$(cat "$f" 2>/dev/null)" ":::detail" "$(echo "$f" | sed 's#.*/\(docs\|current\)/##') mentions :::detail"
done
for f in doc-sites/docs/aws-content-plugin/skills/reactive-presentation.md \
         doc-sites/i18n/ko/docusaurus-plugin-content-docs/current/aws-content-plugin/skills/reactive-presentation.md; do
  assert_contains "$(cat "$f" 2>/dev/null)" '<span id="keyboard-shortcuts" />' "$(basename "$(dirname "$f")")/$(basename "$f") keeps the keyboard-shortcuts anchor"
done
assert_contains "$(cat CHANGELOG.md)" "deck-overlay" "CHANGELOG mentions the deck overlay"
