# reactive-presentation Design-System Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the reactive-presentation skill's output cohesive by construction — replace inline-hardcoded design literals with a token-driven, light-first design system.

**Architecture:** A new `design-tokens.css` holds all scales (type/spacing/radius/shadow/color-role/motion/z). `theme.css` imports it, defines class-based `.theme-light`/`.theme-dark` scopes (light is the default via a zero-specificity `:where()` fallback so it honors class-based theming without themeable vars on bare `:root`), and adds token-backed component primitives. SKILL.md templates and PPTX extraction consume tokens only. `validate` gains design-lint rules.

**Tech Stack:** Pure CSS custom properties (no build), stdlib Python (`remarp_to_slides.py`, `extract_pptx_theme.py`), bash structure tests under `tests/structure/` sourced by `run-all.sh`.

> **Test-authoring rules (run-all.sh runs `set -euo pipefail`):**
> - Tests are **sourced** — NO shebang, NO `exit`. Use exported helpers only.
> - Helper signatures (verified): `assert_contains <haystack> <needle>` → `echo "$haystack" | grep -q "$needle"` (needle is BRE and **must not start with `-`** — for `--token` checks use `assert_grep_match`). `assert_grep_match <perl-pattern> <text>` and `assert_grep_no_match <perl-pattern> <text>` → `echo "$text" | grep -qP "$pattern"` (text is content, not a path). `assert_eq <expected> <actual>`, `assert_file_exists <path>`.
> - **Guard every command substitution that may fail** (else `set -e`/`pipefail` aborts the whole suite): `X="$(cat f 2>/dev/null || true)"`; counts: `N=$( { grep -oE 'p' f || true; } | wc -l | tr -d ' ')`; tool output: `OUT="$(python3 … 2>&1 || true)"`.
> - For `--token` presence use `assert_grep_match "\-\-text-xs\b" "$T"` (Perl regex; `\b` ok).

---

### Task 1: Design-token foundation

**Files:**
- Create: `plugins/aws-content-plugin/skills/reactive-presentation/assets/design-tokens.css`
- Test: `tests/structure/test-reactive-design-tokens.sh`

- [ ] **Step 1: Write the failing test (source-safe)**

```bash
# tests/structure/test-reactive-design-tokens.sh   (sourced by run-all.sh — no shebang, no exit)
RP="plugins/aws-content-plugin/skills/reactive-presentation"
DT="$RP/assets/design-tokens.css"
assert_file_exists "$DT" "design-tokens.css exists"
T="$(cat "$DT" 2>/dev/null || true)"
# type scale: 8 steps xs..4xl, each via assert_grep_match (needle starts with --)
for tok in text-xs text-sm text-base text-lg text-xl text-2xl text-3xl text-4xl; do
  assert_grep_match "\-\-$tok\b" "$T" "type token --$tok defined"
done
# line-height + weight role tokens
for tok in leading-tight leading-normal leading-relaxed weight-regular weight-medium weight-semibold weight-bold; do
  assert_grep_match "\-\-$tok\b" "$T" "typography role token --$tok defined"
done
# spacing scale 1..8 (full)
for n in 1 2 3 4 5 6 7 8; do
  assert_grep_match "\-\-space-$n\b" "$T" "spacing token --space-$n defined"
done
# radius / shadow / motion / z
for tok in radius-sm radius-md radius-lg radius-pill shadow-1 shadow-2 shadow-3 shadow-glow \
           duration-fast duration-normal duration-slow z-base z-nav z-overlay z-modal z-toast; do
  assert_grep_match "\-\-$tok\b" "$T" "token --$tok defined"
done
# semantic color-role NAMES (values themed in Task 2)
for tok in surface-1 surface-2 surface-3 on-surface on-surface-muted accent accent-subtle accent-on \
           info info-subtle info-on success success-subtle success-on warning warning-subtle warning-on danger danger-subtle danger-on; do
  assert_grep_match "\-\-$tok\b" "$T" "color-role token --$tok defined"
done
# 8px-grid anchors: --space-2 == .5rem (8px), --space-4 == 1rem (16px)
assert_grep_match "\-\-space-2:\s*0?\.5rem" "$T" "--space-2 is 0.5rem (8px grid)"
assert_grep_match "\-\-space-4:\s*1rem" "$T" "--space-4 is 1rem (16px grid)"
# modular type anchor: base == 1rem
assert_grep_match "\-\-text-base:\s*1rem" "$T" "--text-base is 1rem"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -i "design-tokens\|type token\|spacing token" | head`
Expected: FAIL — file/tokens absent. (Suite must not abort — guards make absence a clean FAIL.)

- [ ] **Step 3: Write `design-tokens.css`**

On `:root`, define non-theme primitives with **concrete values**:
- **Type scale** (modular 1.25, base 1rem): `--text-xs:.64rem; --text-sm:.8rem; --text-base:1rem; --text-lg:1.25rem; --text-xl:1.563rem; --text-2xl:1.953rem; --text-3xl:2.441rem; --text-4xl:3.052rem`.
- **Line-height roles**: `--leading-tight:1.2; --leading-normal:1.5; --leading-relaxed:1.7`.
- **Weight roles**: `--weight-regular:400; --weight-medium:500; --weight-semibold:600; --weight-bold:700`.
- **Spacing (8px grid)**: `--space-1:.25rem; --space-2:.5rem; --space-3:.75rem; --space-4:1rem; --space-5:1.5rem; --space-6:2rem; --space-7:3rem; --space-8:4rem`.
- **Radius**: `--radius-sm:4px; --radius-md:8px; --radius-lg:12px; --radius-pill:9999px`.
- **Elevation**: `--shadow-1:0 1px 2px rgba(0,0,0,.06); --shadow-2:0 4px 12px rgba(0,0,0,.1); --shadow-3:0 12px 32px rgba(0,0,0,.16); --shadow-glow:0 0 20px var(--accent-subtle)`.
- **Motion**: `--duration-fast:150ms; --duration-normal:250ms; --duration-slow:400ms; --ease-out:cubic-bezier(.16,1,.3,1)`.
- **Z ladder**: `--z-base:0; --z-nav:100; --z-overlay:200; --z-modal:300; --z-toast:400`.
- **Semantic color-role NAMES only** (values assigned per theme in Task 2; here give neutral dark-ish placeholders so the file is valid standalone): `--surface-1/2/3`, `--on-surface`, `--on-surface-muted`, `--accent`, `--accent-subtle`, `--accent-on`, and `--info/--success/--warning/--danger` each with `-subtle` and `-on`.

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/design-tokens.css tests/structure/test-reactive-design-tokens.sh
git commit -m "feat(reactive-presentation): design-token foundation (type/spacing/radius/shadow/color-role/motion/z)"
```

---

### Task 2: Dual-theme scopes (light default) + token-backed component primitives

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme-override-template.css`
- Test: `tests/structure/test-reactive-design-tokens.sh` (extend)

- [ ] **Step 1: Extend the test (failing)**

```bash
# append to tests/structure/test-reactive-design-tokens.sh
TC="$(cat "$RP/assets/theme.css" 2>/dev/null || true)"
assert_grep_match "@import\s+url\(['\"]?design-tokens\.css" "$TC" "theme.css imports design-tokens.css"
assert_contains "$TC" ".theme-dark" "dark theme scope present"
assert_contains "$TC" ".theme-light" "light theme scope present"
# light is the default via a zero-specificity :where() fallback (NOT themeable vars on bare :root {)
assert_grep_match ":where\(" "$TC" "light defaults applied at zero specificity (:where)"
# each scope themes the role tokens (proves per-theme assignment, not per-component hardcode)
assert_grep_match "\.theme-dark[^}]*--surface-1" "$TC" "dark scope assigns --surface-1"
# component primitives that Task 4 templates will use must be DEFINED here
for cls in card-grid metric-card tab-set callout comparison flow-group; do
  assert_grep_match "\.$cls\b" "$TC" "component primitive .$cls defined in theme.css"
done
# primitives consume tokens, not raw hex (spot-check: no #00d4ff anywhere in theme.css)
assert_grep_no_match "#00d4ff" "$TC" "theme.css has no legacy cyan literal"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -i "theme scope\|imports design-tokens\|component primitive\|:where" | head`
Expected: FAIL.

- [ ] **Step 3: Implement**

- Add `@import url('design-tokens.css');` at the very top of `theme.css`.
- **Theme scoping**: assign the role-token VALUES per theme. Light defaults at zero specificity:
  `:where(html), .theme-light { --surface-1:#fff; --surface-2:#f6f7f9; --on-surface:#1a1d2e; --on-surface-muted:#5b6072; --accent:#5b51d8; --accent-subtle:rgba(91,81,216,.12); --accent-on:#fff; … semantic … }`
  and `.theme-dark { --surface-1:#0f1117; --surface-2:#1a1d2e; --on-surface:#e8eaf0; --on-surface-muted:#9ba1b8; --accent:#a29bfe; … }` (reproduce today's dark look). Using `:where()` keeps light as the no-class default without putting themeable vars in a specificity-bearing bare `:root` (honors the class-based contract; `.theme-dark` overrides).
- **Component primitives** (token-backed, theme-agnostic): define `.card-grid` (responsive grid, `gap:var(--space-3)`), `.metric-card`/`.callout`/`.comparison` (`background:var(--surface-2); color:var(--on-surface); border-radius:var(--radius-md); padding:var(--space-4); box-shadow:var(--shadow-1)`), `.tab-set`/`.tab-btn` (active = `var(--accent)`/`var(--accent-on)`), and ensure `.flow-group` uses tokens. These are what Task 4 templates reference.
- Refactor only the obviously themeable existing rules to role tokens; the bulk spacing/type/radius tokenization is Task 3. Update `theme-override-template.css` to override **role tokens** (`--accent`, `--surface-*`), not per-component colors.

- [ ] **Step 4: Run tests** — `bash tests/run-all.sh 2>&1 | tail -3` → PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css plugins/aws-content-plugin/skills/reactive-presentation/assets/theme-override-template.css tests/structure/test-reactive-design-tokens.sh
git commit -m "feat(reactive-presentation): light-default dual-theme scopes + token-backed component primitives"
```

---

### Task 3: Tokenize remaining theme.css component rules

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css`
- Test: `tests/structure/test-reactive-design-tokens.sh` (extend)

- [ ] **Step 1: Extend the test (failing)**

```bash
# append to tests/structure/test-reactive-design-tokens.sh
TC3="$(cat "$RP/assets/theme.css" 2>/dev/null || true)"
# the legacy fractional-rem spacing noise must be gone (sample offenders)
for bad in "0\.17rem" "0\.21rem" "0\.29rem" "0\.42rem" "0\.58rem" "0\.67rem" "0\.83rem" "2\.7rem"; do
  assert_grep_no_match "$bad" "$TC3" "legacy off-scale value $bad removed"
done
# inline var() fallback hexes (drifted 2nd source of truth) removed
assert_grep_no_match "var\(--yellow,\s*#f1c40f" "$TC3" "drifted --yellow fallback removed"
assert_grep_no_match "var\(--text-muted,\s*#8b8fa3" "$TC3" "drifted --text-muted fallback removed"
# components reference the scales
assert_grep_match "var\(--space-" "$TC3" "rules consume spacing tokens"
assert_grep_match "var\(--radius-" "$TC3" "rules consume radius tokens"
```

- [ ] **Step 2: Run** → FAIL (legacy values still present).

- [ ] **Step 3: Implement** — replace ad-hoc spacing/radius/shadow/font-size literals in the remaining component rules with the nearest scale token (`--space-*`, `--radius-*`, `--shadow-*`, `--text-*`). Remove inline `var(--x, #hex)` fallbacks. Map the legacy semantic colors (`--green/--yellow/--red/--blue/--cyan/--pink`) to the new semantic role tokens or `color-mix()` derivations.

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css tests/structure/test-reactive-design-tokens.sh
git commit -m "refactor(reactive-presentation): tokenize theme.css spacing/radius/shadow/type, drop drifted fallbacks"
```

---

### Task 4: Palette unification — detox SKILL.md + reference templates

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/slide-patterns.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/colors-reference.md`
- Test: `tests/structure/test-reactive-design-lint.sh` (new)

- [ ] **Step 1: Write the failing test (broad, source-safe)**

```bash
# tests/structure/test-reactive-design-lint.sh   (sourced — no shebang/exit)
RP="plugins/aws-content-plugin/skills/reactive-presentation"
# No raw 6-digit hex in the promoted authoring docs (templates must use tokens/classes)
for f in SKILL.md references/slide-patterns.md references/colors-reference.md; do
  N=$( { grep -oE "#[0-9a-fA-F]{6}" "$RP/$f" 2>/dev/null || true; } | wc -l | tr -d ' ')
  assert_eq "0" "$N" "$f has no raw 6-digit hex"
done
# No inline color/padding/border-radius in style="" within SKILL.md
SN=$( { grep -oE "style=\"[^\"]*(color|background|padding|border-radius):[^\"]*\"" "$RP/SKILL.md" 2>/dev/null || true; } | wc -l | tr -d ' ')
assert_eq "0" "$SN" "SKILL.md templates carry no inline color/spacing styles"
# Templates reference token vars / primitive classes instead
assert_contains "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "var(--" "SKILL.md templates use CSS token vars"
assert_contains "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "card-grid" "SKILL.md uses token-backed primitives"
```

- [ ] **Step 2: Run** → FAIL (legacy hardcoded hex/inline styles present).

- [ ] **Step 3: Implement** — rewrite the tab/card/flow copy-paste templates and the "색상 팔레트" table to use the Task-2 primitive classes (`.card-grid`, `.metric-card`, `.tab-set`, `.callout`, `.comparison`, `.flow-group`) and `var(--*)` tokens; no raw hex, no inline color/padding/radius styles. Replace the color table with semantic role names (info/success/warning/danger/accent → tokens). Add a one-line note: light is the default theme; opt back to dark with `class="… theme-dark"` on the deck root.

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md plugins/aws-content-plugin/skills/reactive-presentation/references/slide-patterns.md plugins/aws-content-plugin/skills/reactive-presentation/references/colors-reference.md tests/structure/test-reactive-design-lint.sh
git commit -m "feat(reactive-presentation): detox templates to token classes (unify palette, light default note)"
```

---

### Task 5: PPTX/brand extraction drives core tokens

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css`
- Test: `tests/structure/test-reactive-pptx-tokens.sh` (new)

- [ ] **Step 1: Write the failing test (verifies BOTH css wiring AND the generator)**

```bash
# tests/structure/test-reactive-pptx-tokens.sh   (sourced — no shebang/exit)
RP="plugins/aws-content-plugin/skills/reactive-presentation"
TC="$(cat "$RP/assets/theme.css" 2>/dev/null || true)"
# core accent role is wired THROUGH the brand token (matches var(--pptx-accent1) or var(--pptx-accent1, …))
assert_grep_match "var\(--pptx-accent1\b" "$TC" "theme.css wires --accent through brand token --pptx-accent1"
U=$( { grep -oE "var\(--pptx" "$RP/assets/theme.css" 2>/dev/null || true; } | wc -l | tr -d ' ')
assert_grep_match "^[1-9]" "$U" "theme.css consumes >=1 brand token (was 0)"
# the generator emits role/brand tokens (not legacy per-component colors). Invoke its CSS path.
GENOUT="$(cd "$RP" && python3 -c "
import sys; sys.path.insert(0,'scripts')
import extract_pptx_theme as e
fn = getattr(e,'build_override_css', None) or getattr(e,'generate_override_css', None) or getattr(e,'theme_to_css', None)
colors={'accent1':'#11AA22','accent2':'#3344FF','dk1':'#101010','lt1':'#FFFFFF'}
print(fn(colors) if fn else 'NO_FN')
" 2>/dev/null || true)"
assert_grep_match "--pptx-accent1|--accent" "$GENOUT" "override generator emits brand/role tokens"
```

> If the generator's function name differs, the implementer wires the test to the real entry point (one of the candidate names above) — the assertion is that generated CSS sets `--pptx-*`/role tokens, not `--green`/`--cyan` component colors.

- [ ] **Step 2: Run** → FAIL (0 brand-token uses today).

- [ ] **Step 3: Implement** — in `theme.css`, wire role tokens through brand tokens inside each scope, e.g. `--accent: var(--pptx-accent1, <theme-default>);` (and surfaces/semantic where a brand value exists). In `extract_pptx_theme.py`, make the generated `theme-override.css` set `--pptx-*` (and role) tokens. In `remarp_to_slides.py`, ensure any PPTX-derived CSS it emits/links sets tokens, not legacy `--green/--cyan` component vars. Preserve manifest/footer/logo behavior.

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css tests/structure/test-reactive-pptx-tokens.sh
git commit -m "feat(reactive-presentation): PPTX/brand extraction drives core design tokens"
```

---

### Task 6: Design-lint rules in `validate`

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Test: `tests/structure/test-reactive-design-lint.sh` (extend)

- [ ] **Step 1: Extend the test — true-positive + false-positive + JSON + severity**

```bash
# append to tests/structure/test-reactive-design-lint.sh
SC="$RP/scripts/remarp_to_slides.py"
D="$(mktemp -d "${TMPDIR:-/tmp}/rpl.XXXXXX")"
printf 'ratio: "16:9"\n' > "$D/_presentation.md"
# offending slide: raw hex + inline style + off-scale px + raw rgba inside :::html
printf -- '---\nremarp: true\n---\n## S\n\n:::html\n<div style="color:#00d4ff;padding:13px;background:rgba(0,0,0,.3)">x</div>\n:::\n' > "$D/01.md"
OUT="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_contains "$OUT" "RAW_HEX" "lint flags raw hex"
assert_contains "$OUT" "INLINE_STYLE" "lint flags inline style="
assert_contains "$OUT" "OFF_SCALE" "lint flags off-scale px (13px)"
assert_contains "$OUT" "RAW_RGBA" "lint flags raw rgba()"
JOUT="$(python3 "$SC" validate "$D" --json 2>&1 || true)"
assert_contains "$JOUT" "RAW_HEX" "json output carries rule ids"
# false-positive guard: a token/class-based slide is clean
printf -- '---\nremarp: true\n---\n## S\n\n:::html\n<div class="card-grid"><div class="metric-card">x</div></div>\n:::\n' > "$D/01.md"
OUT2="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_grep_no_match "RAW_HEX" "$OUT2" "token-based slide not flagged for hex"
assert_grep_no_match "INLINE_STYLE" "$OUT2" "token-based slide not flagged for inline style"
rm -rf "$D"
```

- [ ] **Step 2: Run** → FAIL (rules absent).

- [ ] **Step 3: Implement** — add `validate` rules: `RAW_HEX` (`#rgb`/`#rrggbb` in `:::html`/`:::css` — WARNING), `INLINE_STYLE` (a `style="…"` with color/background/padding/margin/border-radius — WARNING), `OFF_SCALE` (px/rem spacing not on the 8px scale — WARNING), `RAW_RGBA` (`rgba(`/`rgb(` literal in slide HTML — WARNING), and make body/content overflow a **CRITICAL** layout failure. Follow the existing rule-table format (id, severity, fix guidance); keep `--json` working with the new rule ids/severities. Fixtures use the correct frontmatter (`---\nremarp: true\n---`).

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py tests/structure/test-reactive-design-lint.sh
git commit -m "feat(reactive-presentation): design-lint rules (raw-hex/inline-style/off-scale/raw-rgba/overflow) in validate"
```

---

## Notes for the implementer

- **No silent regression**: decks with no theme class now default to light (zero-specificity `:where()`); the dark look is preserved under `.theme-dark`. Document the one-line opt-back-to-dark in SKILL.md.
- **Scope-lock**: stay within the union of the files listed across tasks (enforced by `scope_guard.py`).
- **Security mandates** still apply (no `0.0.0.0/0`, `Principal:"*"`, secrets in env) — not expected here; reject any such change.
- After all tasks: full suite green + build one representative deck and screenshot-verify **light + dark** at FHD/4K (SKILL Phase 8) before the P4 final gate.
