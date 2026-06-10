# reactive-presentation Design-System Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the reactive-presentation skill's output cohesive by construction — replace inline-hardcoded design literals with a token-driven, light-first design system.

**Architecture:** A new `design-tokens.css` holds all scales (type/spacing/radius/shadow/color-role/motion/z). `theme.css` imports it and moves themeable values into class-based `.theme-light` (default) / `.theme-dark` scopes. SKILL.md templates and PPTX extraction consume tokens only. `validate` gains design-lint rules that reject raw hex / inline style / off-scale spacing / overflow.

**Tech Stack:** Pure CSS custom properties (no build), stdlib Python (`remarp_to_slides.py`, `extract_pptx_theme.py`), bash structure tests under `tests/structure/` (sourced by `run-all.sh`, no shebang exec, shared assert helpers).

> **Path note:** `RP=plugins/aws-content-plugin/skills/reactive-presentation`. All test files are sourced by `tests/run-all.sh` — do NOT add a shebang or call `exit`; use the exported assert helpers (`assert_eq`, `assert_contains`, `assert_file_exists`, `assert_grep_match`, `assert_grep_no_match`). Escape BRE metacharacters in needles.

---

### Task 1: Design-token foundation

**Files:**
- Create: `plugins/aws-content-plugin/skills/reactive-presentation/assets/design-tokens.css`
- Test: `tests/structure/test-reactive-design-tokens.sh`

- [ ] **Step 1: Write the failing test**

```bash
# tests/structure/test-reactive-design-tokens.sh
RP="plugins/aws-content-plugin/skills/reactive-presentation"
DT="$RP/assets/design-tokens.css"
assert_file_exists "$DT" "design-tokens.css exists"
T="$(cat "$DT" 2>/dev/null)"
# type scale (modular, 8 steps)
for tok in --text-xs --text-sm --text-base --text-lg --text-xl --text-2xl --text-3xl --text-4xl; do
  assert_contains "$T" "$tok" "type token $tok defined"
done
# spacing scale (8px grid)
for tok in --space-1 --space-2 --space-3 --space-4 --space-5 --space-6 --space-8; do
  assert_contains "$T" "$tok" "spacing token $tok defined"
done
# radius / shadow / motion / z
for tok in --radius-sm --radius-md --radius-lg --radius-pill --shadow-1 --shadow-2 --shadow-3 --shadow-glow \
           --duration-fast --duration-normal --duration-slow --z-base --z-nav --z-overlay --z-modal --z-toast; do
  assert_contains "$T" "$tok" "token $tok defined"
done
# semantic color roles (theme-agnostic names)
for tok in --surface-1 --surface-2 --on-surface --on-surface-muted --accent --accent-subtle --accent-on \
           --info --success --warning --danger; do
  assert_contains "$T" "$tok" "color-role token $tok defined"
done
# 8px grid anchor: --space-2 must equal .5rem (8px)
assert_grep_match "\-\-space-2:[[:space:]]*0*\.5rem" "$T" "--space-2 is 0.5rem (8px grid)"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -i "design-tokens\|type token\|spacing token"`
Expected: FAIL — file/tokens absent.

- [ ] **Step 3: Write `design-tokens.css`**

Define non-theme primitives on `:root`: a modular **1.25** type scale seeded at `--text-base: 1rem` (`--text-xs:.64rem; --text-sm:.8rem; --text-base:1rem; --text-lg:1.25rem; --text-xl:1.563rem; --text-2xl:1.953rem; --text-3xl:2.441rem; --text-4xl:3.052rem`), an 8px spacing scale (`--space-1:.25rem; --space-2:.5rem; --space-3:.75rem; --space-4:1rem; --space-5:1.5rem; --space-6:2rem; --space-8:4rem`), radius (`--radius-sm:4px; --radius-md:8px; --radius-lg:12px; --radius-pill:9999px`), elevation (`--shadow-1/2/3` ascending + `--shadow-glow`), motion (`--duration-fast:150ms; --duration-normal:250ms; --duration-slow:400ms` + named easings), z-index ladder, and **semantic color-role NAMES** (`--surface-1/2/3`, `--on-surface`, `--on-surface-muted`, `--accent`, `--accent-subtle`, `--accent-on`, `--info/--success/--warning/--danger` each with `-subtle`/`-on`). Color-role *values* are assigned per theme in Task 2 (here, names may default to dark values as a baseline). Add line-height/weight role comments per type step.

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/design-tokens.css tests/structure/test-reactive-design-tokens.sh
git commit -m "feat(reactive-presentation): design-token foundation (type/spacing/radius/shadow/color-role)"
```

---

### Task 2: Dual-theme scopes (light-first) + tokenize theme.css

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme-override-template.css`
- Test: `tests/structure/test-reactive-design-tokens.sh` (extend)

- [ ] **Step 1: Extend the test (failing)**

```bash
# append to tests/structure/test-reactive-design-tokens.sh
TC="$(cat "$RP/assets/theme.css" 2>/dev/null)"
assert_contains "$TC" "@import" "theme.css imports design-tokens.css"
assert_contains "$TC" "design-tokens.css" "theme.css references design-tokens.css"
assert_contains "$TC" ".theme-light" "light theme scope present"
assert_contains "$TC" ".theme-dark" "dark theme scope present"
# light is the default: a .theme-light (or :root mapped to light) must set a light surface
assert_grep_match "\.theme-light" "$TC" "light scope defined"
# color-role values are assigned per theme, not hardcoded per component:
# the legacy bare --accent:#6c5ce7 line on :root must be gone (moved into a theme scope)
assert_grep_no_match "^[[:space:]]*--accent:[[:space:]]*#6c5ce7" "$TC" "legacy bare :root --accent removed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -i "theme scope\|imports design-tokens\|legacy bare"`
Expected: FAIL.

- [ ] **Step 3: Implement**

Add `@import url('design-tokens.css');` at the top of `theme.css`. Move every themeable color
(backgrounds, text, accent, semantic) out of bare `:root` into two scopes: `.theme-light { … }`
(clean light surfaces, restrained contrast — a real palette, not an inversion) and
`.theme-dark { … }` (reproduce today's dark look closely so existing decks don't regress).
Map the semantic role tokens (`--surface-*`, `--on-surface*`, `--accent*`, semantic) to concrete
values inside each scope. Make **light the default**: apply `.theme-light` styling when no theme
class is set (e.g. `:root` mirrors light, `.theme-dark` overrides). Refactor component rules to
consume role tokens + the Task-1 scales (`--space-*`, `--radius-*`, `--shadow-*`, `--text-*`)
instead of raw values; remove inline `var(--x, #hex)` fallbacks. Update
`theme-override-template.css` to override role tokens, not raw component colors.

- [ ] **Step 4: Run tests**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css plugins/aws-content-plugin/skills/reactive-presentation/assets/theme-override-template.css tests/structure/test-reactive-design-tokens.sh
git commit -m "feat(reactive-presentation): class-based light/dark theme scopes, light-first default, tokenized theme.css"
```

---

### Task 3: Palette unification — detox SKILL.md templates

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/slide-patterns.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/colors-reference.md`
- Test: `tests/structure/test-reactive-design-lint.sh` (new — also used by Task 5)

- [ ] **Step 1: Write the failing test**

```bash
# tests/structure/test-reactive-design-lint.sh
RP="plugins/aws-content-plugin/skills/reactive-presentation"
# No raw 6-digit hex inside SKILL.md :::html copy-paste templates (the cyan #00d4ff family).
HEXN=$(grep -oE "#00d4ff|#0a0e1a|#1a2540|#8b95a5|#b0b0b0|#00ff88" "$RP/SKILL.md" | wc -l | tr -d ' ')
assert_eq "0" "$HEXN" "SKILL.md templates contain no legacy hardcoded hex palette"
# Templates should reference CSS vars / token classes instead.
assert_contains "$(cat "$RP/SKILL.md")" "var(--" "SKILL.md templates use CSS token vars"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -i "legacy hardcoded hex\|token vars"`
Expected: FAIL (templates currently hardcode `#00d4ff` etc.).

- [ ] **Step 3: Implement**

Rewrite the SKILL.md tab/card/flow copy-paste templates and the "색상 팔레트" table to use
**token-backed classes** (`.card-grid`, `.metric-card`, `.tab-set`, `.flow-group`, `.callout`,
`.comparison`) and `var(--accent)`, `var(--surface-2)`, `var(--on-surface-muted)`, `var(--space-3)`,
`var(--radius-md)` — never raw hex or raw px. Keep tab/fragment behavior self-contained but
token-driven. Update `slide-patterns.md` and `colors-reference.md` examples to the same token
vocabulary; replace the hardcoded color table with semantic role names (info/success/warning/
danger/accent) mapped to tokens.

- [ ] **Step 4: Run tests**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md plugins/aws-content-plugin/skills/reactive-presentation/references/slide-patterns.md plugins/aws-content-plugin/skills/reactive-presentation/references/colors-reference.md tests/structure/test-reactive-design-lint.sh
git commit -m "feat(reactive-presentation): detox SKILL templates to token classes (unify palette)"
```

---

### Task 4: PPTX/brand extraction drives core tokens

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css`
- Test: `tests/structure/test-reactive-design-tokens.sh` (extend)

- [ ] **Step 1: Extend the test (failing)**

```bash
# append to tests/structure/test-reactive-design-tokens.sh
TC2="$(cat "$RP/assets/theme.css" 2>/dev/null)"
# brand tokens must now be CONSUMED (previously 10 defs / 0 uses)
USES=$(grep -cE "var\(--pptx" "$RP/assets/theme.css")
assert_grep_match "[1-9]" "$USES" "theme.css consumes at least one --pptx-* brand token"
# the core accent role falls back through the brand token
assert_contains "$TC2" "var(--pptx-accent1" "core accent wired to brand accent token"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -i "brand token"`
Expected: FAIL (0 uses today).

- [ ] **Step 3: Implement**

In `theme.css`, wire the core role tokens through the brand tokens inside each theme scope, e.g.
`--accent: var(--pptx-accent1, <theme-default>);` and similar for surfaces/semantic where a brand
value exists — so an extracted PPTX theme re-brands the whole deck (including the Task-3 token
components). Update `extract_pptx_theme.py` so its generated `theme-override.css` sets the
`--pptx-*` (and, where appropriate, the role) tokens rather than per-component colors. Preserve
the existing manifest/footer/logo behavior.

- [ ] **Step 4: Run tests**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/scripts/extract_pptx_theme.py plugins/aws-content-plugin/skills/reactive-presentation/assets/theme.css tests/structure/test-reactive-design-tokens.sh
git commit -m "feat(reactive-presentation): PPTX/brand extraction drives core design tokens"
```

---

### Task 5: Design-lint rules in `validate`

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Test: `tests/structure/test-reactive-design-lint.sh` (extend)

- [ ] **Step 1: Extend the test (failing) — true-positive + false-positive**

```bash
# append to tests/structure/test-reactive-design-lint.sh
SC="$RP/scripts/remarp_to_slides.py"
D=$(mktemp -d "${TMPDIR:-/tmp}/rpl.XXXXXX")
# a slide with a raw hex + inline style inside :::html → must be flagged
printf 'remarp: true\n---\n## S\n\n:::html\n<div style="color:#00d4ff;padding:13px">x</div>\n:::\n' > "$D/01.md"
printf 'ratio: "16:9"\n' > "$D/_presentation.md"
OUT=$(python3 "$SC" validate "$D" 2>&1)
assert_contains "$OUT" "RAW_HEX" "lint flags raw hex in :::html"
assert_contains "$OUT" "INLINE_STYLE" "lint flags inline style= in :::html"
# false positive guard: a token-based slide must NOT be flagged
printf 'remarp: true\n---\n## S\n\n:::html\n<div class="card-grid"><div class="metric-card">x</div></div>\n:::\n' > "$D/01.md"
OUT2=$(python3 "$SC" validate "$D" 2>&1)
assert_grep_no_match "RAW_HEX" "$OUT2" "token-based slide not flagged for hex"
rm -rf "$D"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -i "RAW_HEX\|INLINE_STYLE"`
Expected: FAIL (rules not implemented).

- [ ] **Step 3: Implement**

Add validation rules to the `validate` command: `RAW_HEX` (a `#rrggbb`/`#rgb` literal inside a
`:::html`/`:::css` block — WARNING, fix: use `var(--token)`), `INLINE_STYLE` (a `style="…"`
attribute carrying color/padding/margin/border-radius — WARNING, fix: token class), `OFF_SCALE`
(a px/rem spacing value not on the spacing scale — WARNING), and make `CONTENT_OVERFLOW`/body
overflow a CRITICAL layout failure rather than silently scrollable. Follow the existing rule
table format (rule id, severity, auto-fix guidance). Keep `--json` output working.

- [ ] **Step 4: Run tests**

Run: `bash tests/run-all.sh 2>&1 | tail -3`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py tests/structure/test-reactive-design-lint.sh
git commit -m "feat(reactive-presentation): design-lint rules (raw-hex/inline-style/off-scale/overflow) in validate"
```

---

## Notes for the implementer

- **No silent regression**: existing decks that set no theme class now default to light. Preserve the dark look under `.theme-dark` and document the one-line opt-back-to-dark in SKILL.md (Phase 1/6 theme setup).
- **Scope-lock**: stay within the files listed per task (enforced by `scope_guard.py`).
- **Security mandates** still apply (no `0.0.0.0/0`, no `Principal:"*"`, no secrets) — not expected to be touched here, but reject any such change.
- After all tasks: run the full suite + build one representative deck and screenshot-verify light + dark at FHD/4K (SKILL Phase 8) before the final gate.
