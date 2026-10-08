# tests/structure/test-reactive-fit.sh   (sourced by run-all.sh — no shebang, no exit)
# Regression for the reactive-space-fit spec: role font tokens, ReactiveFit engine,
# removed responsive @media block, measure_deck density gates, @fit round trip, docs.
RP="plugins/aws-content-plugin/skills/reactive-presentation"

# --- 1. design-tokens.css: role font-size tokens ---
DT="$RP/assets/design-tokens.css"
assert_file_exists "$DT" "design-tokens.css exists"
T="$(cat "$DT" 2>/dev/null || true)"
assert_grep_match "\-\-fs-title:\s*2\.667rem" "$T" "--fs-title is 2.667rem (64px = 32pt)"
assert_grep_match "\-\-fs-subtitle:\s*1\.333rem" "$T" "--fs-subtitle is 1.333rem (32px = 16pt)"
assert_grep_match "\-\-fs-body:\s*1\.333rem" "$T" "--fs-body is 1.333rem (32px = 16pt)"
assert_grep_match "\-\-fs-card:\s*1\.167rem" "$T" "--fs-card is 1.167rem (28px = 14pt)"
assert_grep_match "\-\-fs-caption:\s*0?\.917rem" "$T" "--fs-caption is .917rem (22px = 11pt floor)"
assert_grep_match "\-\-leading-body:\s*1\.45\b" "$T" "--leading-body is 1.45"

# --- 2. theme.css: consumes role tokens, ships .fit-box, drops the 1024px media block ---
TC="$(cat "$RP/assets/theme.css" 2>/dev/null || true)"
for tok in fs-title fs-body fs-card fs-caption; do
  assert_grep_match "var\(--$tok\)" "$TC" "theme.css consumes var(--$tok)"
done
assert_grep_match "^\.fit-box\s*\{" "$TC" "theme.css defines a .fit-box rule"
assert_grep_no_match "@media\s*\(max-width:\s*1024px\)" "$TC" "theme.css has no @media (max-width: 1024px) block (fixed canvas scaling)"
assert_grep_no_match "\.slide-img[^{]*\{[^}]*50vh" "$(printf '%s' "$TC" | tr '\n' ' ')" ".slide-img no longer uses 50vh"
assert_grep_match "^\.card-desc\s*\{" "$TC" ".card-desc primitive exists in theme.css"

# --- 3. slide-framework.js: ReactiveFit engine ---
JS="$RP/assets/slide-framework.js"
assert_file_exists "$JS" "slide-framework.js exists"
J="$(cat "$JS" 2>/dev/null || true)"
assert_contains "$J" "window.ReactiveFit" "framework exposes window.ReactiveFit"
assert_contains "$J" "function fitSlide" "framework defines fitSlide"
assert_contains "$J" "function fitAll" "framework defines fitAll"
assert_contains "$J" "data-fit-overflow" "framework marks data-fit-overflow when content spills at MIN scale"
assert_contains "$J" "fitScale" "framework caches the fit scale (dataset.fitScale)"
assert_contains "$J" "document.fonts" "framework re-fits after document.fonts.ready"
assert_contains "$J" "fit-box" "framework wraps body content in .fit-box"
assert_grep_match "canvas,\s*iframe,\s*\.archify" "$J" "framework skips pixel-exact canvas/iframe/archify content"
# The ReactiveFit IIFE sits outside the SlideFramework class: its assignment must
# come after the first top-level closing brace (the class's `}`).
CLASS_END="$(grep -nE '^}' "$JS" 2>/dev/null | head -1 | cut -d: -f1)"
RF_LINE="$(grep -n 'window\.ReactiveFit =' "$JS" 2>/dev/null | head -1 | cut -d: -f1)"
RF_AFTER_CLASS="no"
if [ -n "$CLASS_END" ] && [ -n "$RF_LINE" ] && [ "$RF_LINE" -gt "$CLASS_END" ]; then RF_AFTER_CLASS="yes"; fi
assert_eq "yes" "$RF_AFTER_CLASS" "window.ReactiveFit assignment (line ${RF_LINE:-?}) sits after the class closing brace (line ${CLASS_END:-?})"
if command -v node >/dev/null 2>&1; then
  NODE_CHECK="fail"
  node --check "$JS" >/dev/null 2>&1 && NODE_CHECK="ok"
  assert_eq "ok" "$NODE_CHECK" "slide-framework.js passes node --check"
fi

# --- 4. measure_deck.py / export_pptx.py: density gates + fit hook ---
MD="$RP/scripts/measure_deck.py"
EP="$RP/scripts/export_pptx.py"
assert_file_exists "$MD" "measure_deck.py exists"
assert_file_exists "$EP" "export_pptx.py exists"
M="$(cat "$MD" 2>/dev/null || true)"
for rule in UNDERFILL MIN_FONT FIT_OVERFLOW; do
  assert_contains "$M" "$rule" "measure_deck.py implements the $rule gate"
done
assert_contains "$M" "ReactiveFit.fitSlide" "measure_deck.py forces ReactiveFit.fitSlide before measuring"
assert_contains "$(cat "$EP" 2>/dev/null || true)" "ReactiveFit.fitSlide" "export_pptx.py forces ReactiveFit.fitSlide before capture"
PYC="$(mktemp -d "${TMPDIR:-/tmp}/rfitpyc.XXXXXX")"
PY_COMPILE="fail"
PYTHONPYCACHEPREFIX="$PYC" python3 -m py_compile "$MD" "$EP" >/dev/null 2>&1 && PY_COMPILE="ok"
assert_eq "ok" "$PY_COMPILE" "measure_deck.py and export_pptx.py pass py_compile"
rm -rf "$PYC"

# --- 5. Remarp round trip: frontmatter fit + @fit directive -> data-fit; bogus -> INVALID_FIT ---
SC="$RP/scripts/remarp_to_slides.py"
D="$(mktemp -d "${TMPDIR:-/tmp}/rfit.XXXXXX")"
printf -- '---\nremarp: true\nratio: "16:9"\nfit: shrink\n---\n## Off slide\n\n@fit: off\n\nBody text here.\n\n---\n\n## Default slide\n\nBody text here.\n' > "$D/deck.md"
BUILD_RC=0
PYTHONDONTWRITEBYTECODE=1 python3 "$SC" build "$D/deck.md" >/dev/null 2>&1 || BUILD_RC=$?
assert_eq "0" "$BUILD_RC" "remarp build of a fit-annotated single-file deck exits 0"
assert_file_exists "$D/slides/default.html" "single-file build emits slides/default.html"
HTML="$(cat "$D/slides/default.html" 2>/dev/null || true)"
assert_contains "$HTML" 'data-fit="off"' "@fit: off slide emits data-fit=\"off\""
assert_contains "$HTML" 'data-fit="shrink"' "undirected slide inherits frontmatter fit: shrink as data-fit=\"shrink\""
printf -- '---\nremarp: true\nratio: "16:9"\n---\n## Bogus slide\n\n@fit: bogus\n\nBody text here.\n' > "$D/bad.md"
VOUT="$(PYTHONDONTWRITEBYTECODE=1 python3 "$SC" validate "$D/bad.md" --json 2>&1 || true)"
assert_contains "$VOUT" "INVALID_FIT" "validate --json reports INVALID_FIT for @fit: bogus"
rm -rf "$D"

# --- 6. Docs mention the engine, gate rule IDs, directive and measurement script ---
assert_contains "$(cat "$RP/references/framework-contract.md" 2>/dev/null || true)" "ReactiveFit" "framework-contract.md documents ReactiveFit"
AR="$(cat "$RP/references/authoring-rules.md" 2>/dev/null || true)"
for rule in UNDERFILL MIN_FONT FIT_OVERFLOW INVALID_FIT; do
  assert_contains "$AR" "$rule" "authoring-rules.md documents the $rule rule"
done
assert_contains "$(cat "$RP/references/remarp-format-guide.md" 2>/dev/null || true)" "@fit" "remarp-format-guide.md documents the @fit directive"
assert_contains "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "measure_deck.py" "SKILL.md references measure_deck.py"

# --- 7. Review round 1: code blocks fit, tab panel stack, Korean wrap, heading colors, canvas ---
TCF="$(printf '%s' "$TC" | tr '\n' ' ')"
assert_grep_match "\.fit-box \.code-block\s*\{[^}]*max-height:\s*none" "$TCF" "code blocks inside .fit-box drop max-height"
assert_grep_match "\.fit-box \.code-block\s*\{[^}]*overflow:\s*visible" "$TCF" "code blocks inside .fit-box have no inner scroll (overflow: visible)"
assert_grep_match "\.fit-box \.code-block\s*\{[^}]*width:\s*max-content" "$TCF" "a long code line widens the block so ReactiveFit measures it"
assert_grep_match "\.tab-panels\s*\{[^}]*display:\s*grid" "$TCF" ".tab-panels is a grid stack"
assert_grep_match "\.tab-panels > \.tab-content\s*\{[^}]*grid-area:\s*1\s*/\s*1" "$TCF" "all tab panels share one grid cell (tallest panel sets the height)"
assert_grep_match "\.tab-panels > \.tab-content\s*\{[^}]*visibility:\s*hidden" "$TCF" "inactive stacked panels are visibility-hidden, not display:none"
assert_grep_match "\.tab-panels > \.tab-content\.active\s*\{[^}]*visibility:\s*visible" "$TCF" "the active stacked panel is visible"
assert_grep_match "\.slide-deck:lang\(ko\)\s*\{[^}]*text-wrap:\s*pretty" "$TCF" "Korean decks wrap body text with text-wrap: pretty"
assert_grep_match ":lang\(ko\) :is\(h1, h2, h3, h4\)\s*\{[^}]*text-wrap-style:\s*balance" "$TCF" "Korean headings use balanced wrapping"
assert_grep_match "\.slide :is\(h1, h2, h3, h4\)\.text-orange\s*\{" "$TCF" "heading utility colors out-rank .slide h3 (text-orange)"
assert_grep_match "^\.nowrap\s*\{[^}]*white-space:\s*nowrap" "$TC" ".nowrap utility exists"
assert_contains "$J" "tab-panels" "initTabs groups tab panels into a .tab-panels stack"
AU="$RP/assets/animation-utils.js"
DG_FONT="$(awk '/^function drawGroup\(/{f=1} f && /ctx\.font *=/{print NR; exit}' "$AU" 2>/dev/null)"
DG_MEASURE="$(awk '/^function drawGroup\(/{f=1} f && /ctx\.measureText\(/{print NR; exit}' "$AU" 2>/dev/null)"
DG_ORDER="no"
if [ -n "$DG_FONT" ] && [ -n "$DG_MEASURE" ] && [ "$DG_FONT" -lt "$DG_MEASURE" ]; then DG_ORDER="yes"; fi
assert_eq "yes" "$DG_ORDER" "drawGroup sets ctx.font (line ${DG_FONT:-?}) before measureText (line ${DG_MEASURE:-?})"
if command -v node >/dev/null 2>&1; then
  AU_CHECK="fail"
  node --check "$AU" >/dev/null 2>&1 && AU_CHECK="ok"
  assert_eq "ok" "$AU_CHECK" "animation-utils.js passes node --check"
fi

# --- 8. Review round 2: framework chrome (footer/logo/number) yields only to full-bleed visuals ---
assert_contains "$J" "slideHidesChrome(slide)" "framework decides chrome visibility in slideHidesChrome()"
assert_grep_match "FULL_BLEED_AREA\s*=\s*0\.6\b" "$J" "an <img> hides the chrome only when it covers >= 60% of the slide"
assert_contains "$J" "data-keep-chrome" "data-keep-chrome keeps the chrome on a slide"
assert_contains "$J" "data-hide-chrome" "data-hide-chrome hides the chrome on a slide"
assert_contains "$J" "\.full-bleed" "a .full-bleed element hides the chrome"
assert_grep_no_match "hide\s*=\s*slide\.querySelector\('img'\)" "$J" "a mere <img> (e.g. an inline icon) no longer hides the chrome"
FCT="$(cat "$RP/references/framework-contract.md" 2>/dev/null || true)"
assert_contains "$FCT" "data-keep-chrome" "framework-contract.md documents data-keep-chrome"
assert_contains "$FCT" "full-bleed" "framework-contract.md documents the full-bleed chrome rule"
if command -v node >/dev/null 2>&1; then
  # Behavioral check: load slide-framework.js in a bare VM and call slideHidesChrome() on
  # stub slides (1920x1080 rect; img rects in the same units).
  CHROME_OUT="$(node -e '
const fs = require("fs"), vm = require("vm");
const ctx = { window: {}, document: { addEventListener() {} } };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), ctx);
const hides = vm.runInContext("SlideFramework.prototype.slideHidesChrome", ctx);
const rect = (l, t, w, h) => ({ left: l, top: t, right: l + w, bottom: t + h, width: w, height: h });
const slide = (imgs, attrs = [], kids = []) => ({
  hasAttribute: a => attrs.includes(a),
  matches: s => attrs.some(a => s.includes("[" + a + "]")),
  querySelector: s => (kids.some(k => s.includes(k)) ? {} : null),
  querySelectorAll: () => imgs.map(r => ({ getBoundingClientRect: () => r })),
  getBoundingClientRect: () => rect(0, 0, 1920, 1080),
});
const full = rect(0, 0, 1920, 1080);
console.log([
  "icon=" + hides.call({}, slide([rect(100, 100, 48, 48), rect(400, 100, 48, 48)])),
  "half=" + hides.call({}, slide([rect(0, 0, 1920, 540)])),
  "big=" + hides.call({}, slide([rect(0, 0, 1536, 864)])),
  "full=" + hides.call({}, slide([full])),
  "keep=" + hides.call({}, slide([full], ["data-keep-chrome"])),
  "attr=" + hides.call({}, slide([], ["data-hide-chrome"])),
  "class=" + hides.call({}, slide([], [], [".full-bleed"])),
].join(" "));
' "$JS" 2>&1 || true)"
  assert_eq "icon=false half=false big=true full=true keep=false attr=true class=true" "$CHROME_OUT" "slideHidesChrome: icons and a half-slide image keep the chrome; >=60% image, data-hide-chrome, .full-bleed hide it; data-keep-chrome wins"
fi

# --- 9. Review round 3: deck stays in the viewport, quiz feedback is textual, thumbnail ids ---
TC9FLAT="$(tr '\n' ' ' < "$RP/assets/theme.css" 2>/dev/null || true)"
assert_grep_match "\.slide-deck \{[^}]*margin: 0;" "$TC9FLAT" ".slide-deck uses margin 0 so body centres an oversized deck (auto margins pushed it off-screen)"
assert_grep_no_match "\.slide-deck \{[^}]*margin: auto" "$TC9FLAT" ".slide-deck has no auto margin"
M9="$(cat "$RP/scripts/measure_deck.py" 2>/dev/null || true)"
assert_contains "$M9" "DECK_OFFSCREEN" "measure_deck.py checks that the scaled deck box is inside the viewport (DECK_OFFSCREEN)"
assert_contains "$M9" "hideSidebar" "DECK_OFFSCREEN also checks the deck with the sidebar hidden"
Q9="$(cat "$RP/assets/quiz-component.js" 2>/dev/null || true)"
assert_grep_match "feedback\.className = 'quiz-feedback'" "$Q9" "quiz-component creates .quiz-feedback when the author omitted it (no colour-only result)"
assert_contains "$Q9" "aria-live" "quiz feedback is announced (aria-live)"
assert_contains "$Q9" "shrinkOnly: true" "quiz re-fits the slide shrink-only after revealing feedback"
assert_grep_no_match "font-size: \.88rem" "$Q9" "quiz explanation text is not below the caption floor"
assert_contains "$(cat "$RP/assets/slide-framework.js" 2>/dev/null || true)" "removeAttribute('id')" "sidebar thumbnail clones drop ids (getElementById keeps returning the live slide)"
GD9="$(cat "$RP/assets/example-deck/index.html" 2>/dev/null || true)"
assert_contains "$GD9" 'class="quiz-feedback"' "golden deck quiz has a .quiz-feedback element"
assert_grep_match 'data-correct="true" data-explain="' "$GD9" "golden deck quiz options carry data-explain"
assert_grep_match "consolidateAfter" "$GD9" "golden deck NodePool sets consolidateAfter (required by the Karpenter v1.0 CRD)"
