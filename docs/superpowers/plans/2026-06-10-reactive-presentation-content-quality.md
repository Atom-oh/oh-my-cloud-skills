# reactive-presentation Content-Quality Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add aws-presentation's transferable content conventions to reactive-presentation — structured speaker notes, level-differentiated headline title voice, a consolidated Forbidden AI-tells section, and lint to enforce the mechanical parts.

**Architecture:** Docs (`SKILL.md`, `references/remarp-format-guide.md`, `references/slide-patterns.md`) gain the conventions; `remarp_to_slides.py validate` gains `NOTE_STRUCTURE` + `TITLE_LENGTH` rules; `content-review-agent.md` gains a source-omission cross-check. Notes stay plain text (no new parser).

**Tech Stack:** Markdown docs, stdlib Python (`remarp_to_slides.py`), bash structure tests under `tests/structure/` (sourced by `run-all.sh`).

> **Test-authoring rules (run-all.sh runs `set -euo pipefail`, SOURCES each test):** no shebang, no `exit`. `assert_contains <hay> <needle>` → `grep -q "$needle"` (needle must NOT start with `-`). `assert_grep_match <perl-pat> <text>` / `assert_grep_no_match` → `grep -qP` (2nd arg = CONTENT). Guard every substitution: `X="$(cat f 2>/dev/null || true)"`; tool output `OUT="$(python3 … 2>&1 || true)"`. `$RP` = `plugins/aws-content-plugin/skills/reactive-presentation`.

---

### Task 1: Structured speaker-note schema + `NOTE_STRUCTURE` lint

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/remarp-format-guide.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Test: `tests/structure/test-reactive-design-lint.sh` (extend — append)

- [ ] **Step 1: Write the failing test (append)**

```bash
# --- content-quality: NOTE_STRUCTURE ---
RP="plugins/aws-content-plugin/skills/reactive-presentation"
# docs document the schema
assert_contains "$(cat "$RP/references/remarp-format-guide.md" 2>/dev/null || true)" "[요약]" "remarp-format-guide documents [요약] note layer"
assert_contains "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "[요약]" "SKILL.md references the structured note schema"
# lint: a content slide whose :::notes lacks [요약] is flagged
SC="$RP/scripts/remarp_to_slides.py"
D="$(mktemp -d "${TMPDIR:-/tmp}/ns.XXXXXX")"
printf -- '---\nratio: "16:9"\n---\n' > "$D/_presentation.md"
printf -- '---\nremarp: true\n---\n## A title\n\nSome body text here.\n\n:::notes\n{timing: 2min}\nThis is a free-form note with no summary block, long enough to pass the length check easily by adding words and words and more words.\n:::\n' > "$D/01.md"
OUT="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_contains "$OUT" "NOTE_STRUCTURE" "lint flags notes missing [요약]"
# false positive guard: a structured note is clean
printf -- '---\nremarp: true\n---\n## A title\n\nSome body text here.\n\n:::notes\n{timing: 2min}\n[요약]\n• key point one here\n• key point two here\nThe spoken script in conversational Korean goes here with enough words to pass length.\n:::\n' > "$D/01.md"
OUT2="$(python3 "$SC" validate "$D" 2>&1 || true)"
assert_grep_no_match "NOTE_STRUCTURE" "$OUT2" "structured note not flagged"
rm -rf "$D"
```

- [ ] **Step 2: Run, verify FAIL** — `bash tests/run-all.sh 2>&1 | grep -i "NOTE_STRUCTURE\|note schema\|note layer" | head`

- [ ] **Step 3: Implement**
  - In `references/remarp-format-guide.md` (notes section) document the 5-layer schema: `{timing}`/`{cue}` (kept) + `[요약]` (3–5 bullets) → spoken script → `[약어]` (domain abbreviations; omit if none) → `[출처]` (conditional: claims/numbers) → `[변경이력]` (optional). Show a full `:::notes` example. In `SKILL.md` add a short subsection pointing to it and stating `[요약]` is recommended on content slides.
  - In `remarp_to_slides.py validate`, add rule **`NOTE_STRUCTURE`** (WARNING): for a content-type slide that HAS a `:::notes` block, flag if the block lacks a `[요약]` line. (Do not flag slides without notes — `MISSING_NOTES` already covers that; do not flag cover/section/agenda/quiz types.) Mirror the existing rule dict shape; keep `--json`.

- [ ] **Step 4: Run, verify PASS** — `bash tests/run-all.sh 2>&1 | tail -3`

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/references/remarp-format-guide.md plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py tests/structure/test-reactive-design-lint.sh
git commit -m "feat(reactive-presentation): structured speaker-note schema + NOTE_STRUCTURE lint"
```

---

### Task 2: Slide title voice + `TITLE_LENGTH` lint

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/references/slide-patterns.md`
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py`
- Test: `tests/structure/test-reactive-design-lint.sh` (extend — append)

- [ ] **Step 1: Write the failing test (append)**

```bash
# --- content-quality: title voice + TITLE_LENGTH ---
assert_contains "$(cat "$RP/SKILL.md" 2>/dev/null || true)" "체언 종결" "SKILL.md documents noun-ending subtitle voice"
assert_contains "$(cat "$RP/references/slide-patterns.md" 2>/dev/null || true)" "headline" "slide-patterns documents headline title voice"
# lint: an over-long title (>28 KO chars) is flagged
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
```

- [ ] **Step 2: Run, verify FAIL**

- [ ] **Step 3: Implement**
  - In `SKILL.md` + `references/slide-patterns.md` add a "Slide Title Voice" section: title = headline-with-edge (declarative/claim/question/reversal, ≤28 KO chars); subtitle = noun-ending (체언 종결, ≤45 KO chars). Include ✅/❌ examples. **Level gate**: recommend headline voice for `level` 100–200; allow clear descriptive titles for 300–400. Reference the `level` frontmatter field.
  - In `remarp_to_slides.py validate`, add rule **`TITLE_LENGTH`** (WARNING): a slide title (the `##`/`@title`) longer than 28 characters → flag (and subtitle > 45 if a subtitle field exists). Count characters with `len()` (code points). Mirror rule shape; keep `--json`.

- [ ] **Step 4: Run, verify PASS**

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md plugins/aws-content-plugin/skills/reactive-presentation/references/slide-patterns.md plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py tests/structure/test-reactive-design-lint.sh
git commit -m "feat(reactive-presentation): slide title voice guidance + TITLE_LENGTH lint"
```

---

### Task 3: Consolidated "Forbidden — AI-slide tells" section

**Files:**
- Modify: `plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md`
- Test: `tests/structure/test-reactive-design-lint.sh` (extend — append)

- [ ] **Step 1: Write the failing test (append)**

```bash
# --- content-quality: consolidated Forbidden AI-tells ---
SKL="$(cat "$RP/SKILL.md" 2>/dev/null || true)"
assert_contains "$SKL" "Forbidden" "SKILL.md has a consolidated Forbidden AI-tells section"
assert_contains "$SKL" "AI-slide tells" "Forbidden section titled for AI-slide tells"
# it ties tells to the enforcing lint rules
assert_contains "$SKL" "RAW_HEX" "Forbidden section references the RAW_HEX lint rule"
assert_contains "$SKL" "NOTE_STRUCTURE" "Forbidden section references the NOTE_STRUCTURE lint rule"
```

- [ ] **Step 2: Run, verify FAIL**

- [ ] **Step 3: Implement** — add a single sharp "## Forbidden — AI-slide tells" section to `SKILL.md` consolidating the existing scattered STOP-checks + transferred tells, each linked to its enforcing lint rule where mechanical (hardcoded hex→`RAW_HEX`/`INLINE_STYLE`/`RAW_RGBA`; magic-number type/off-scale→`OFF_SCALE`; dark-only/generic blue-teal→dual-theme; text-wall→`CONTENT_OVERFLOW`; gradient-text/decorative orbs/empty regions→guidance; descriptive encyclopedia titles→title-voice; free-form/missing notes→`NOTE_STRUCTURE`/`MISSING_NOTES`).

- [ ] **Step 4: Run, verify PASS**

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/skills/reactive-presentation/SKILL.md tests/structure/test-reactive-design-lint.sh
git commit -m "feat(reactive-presentation): consolidated Forbidden AI-slide-tells section (lint-linked)"
```

---

### Task 4: Source-omission cross-check in content-review-agent

**Files:**
- Modify: `plugins/aws-content-plugin/agents/content-review-agent.md`
- Test: `tests/structure/test-reactive-design-lint.sh` (extend — append)

- [ ] **Step 1: Write the failing test (append)**

```bash
# --- content-quality: source-omission cross-check ---
CRA="$(cat plugins/aws-content-plugin/agents/content-review-agent.md 2>/dev/null || true)"
assert_contains "$CRA" "omission" "content-review-agent has a source-omission cross-check"
assert_contains "$CRA" "diagram" "omission check lists architecture diagrams as a common gap"
```

- [ ] **Step 2: Run, verify FAIL**

- [ ] **Step 3: Implement** — add a "Source-omission cross-check" step to `content-review-agent.md`: after review, explicitly list which source sections did NOT make it into the deck (architecture diagrams, domestic/Korean case studies, comparison tables, incident/failure cases, timelines, partnerships) and flag gaps. Keep the agent's existing 100-point rubric intact.

- [ ] **Step 4: Run, verify PASS**

- [ ] **Step 5: Commit**

```bash
git add plugins/aws-content-plugin/agents/content-review-agent.md tests/structure/test-reactive-design-lint.sh
git commit -m "feat(content-review): source-omission cross-check after generation"
```

---

## Notes for the implementer
- Adapt, don't copy: `[출처]` conditional, `[변경이력]` optional/lightweight; title voice level-differentiated (100–200 headline, 300–400 descriptive OK).
- All new lint rules are WARNING (rejection-loop nudges), never CRITICAL — existing decks must not hard-fail.
- Stay within each task's declared files (scope_guard). No security mandates involved.
- After all tasks: full suite green; the P4 final gate reviews the cumulative diff.
