# Architecture-Diagram Layout-Gate Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Bring `aws-multi-vpc.drawio` (70) and `aws-samples.drawio` (71) to `lint_layout` ≥ 80 so `tests/run-all.sh` (tests 31 & 33) pass, without regressing other templates or the design canon.

**Architecture:** Surgical .drawio edits — icon sizes → 78×78, add title cells, set fonts to Amazon Ember, snap only off-grid elements to the nearest 5px (NO blind `snap_grid.py` — it regressed multi-vpc). The gate test already exists and fails; each task flips it green.

**Tech Stack:** draw.io XML, stdlib Python lint/validate scripts, bash structure tests.

> **The "test" already exists** — `lint_layout.py <template>` (exit 0 = ≥80) and `tests/run-all.sh` assertions 31/33. No new test file. Reference `references/design-tokens.md` for canon (78×78 icons, Amazon Ember, 5px grid). Run `validate_drawio.py` to keep XML valid.
> **Paths**: `SK=plugins/aws-content-plugin/skills/architecture-diagram`.

---

### Task 1: aws-multi-vpc.drawio → ≥80

**Files:**
- Modify: `plugins/aws-content-plugin/skills/architecture-diagram/templates/aws-multi-vpc.drawio`

- [ ] **Step 1: Confirm RED** — `python3 $SK/scripts/lint_layout.py $SK/templates/aws-multi-vpc.drawio` → score 70 (<80, exit 1). Note the exact deductions (3 off-scale icons 40×40/60×60; no title; 2 off-5px-grid e.g. `id=tgw` at 756,370; 2 uneven rows/cols).

- [ ] **Step 2: Apply surgical fixes**
  - Resize the 3 off-scale icon cells to **78×78** (width/height); if an icon is nested inside a group/container, 48×48 is allowed. Keep their grid-aligned top-left.
  - Add a **title** text cell at the top: a heading `mxCell` with `fontSize≥14` (match aws-hybrid-idc's title-cell style/value pattern), e.g. value "Multi-VPC Architecture", placed above the canvas content, width spanning, Amazon Ember font.
  - Snap ONLY the 2 off-grid elements (e.g. `tgw` 756,370 → 755,370) to the nearest multiple of 5 — do not move others.
  - Even out the 2 uneven rows/cols (equalize the gaps that vary >50%).
  - Do not change icon glyphs (the subnet glyph fix from 6ffa91f stays).

- [ ] **Step 3: Verify GREEN** —
  `python3 $SK/scripts/validate_drawio.py $SK/templates/aws-multi-vpc.drawio` → clean;
  `python3 $SK/scripts/lint_layout.py $SK/templates/aws-multi-vpc.drawio` → **≥80, exit 0**;
  `bash tests/run-all.sh 2>&1 | grep "aws-multi-vpc"` → `ok`. If <80, iterate (read the remaining deductions and address them).

- [ ] **Step 4: Commit**

```bash
git add plugins/aws-content-plugin/skills/architecture-diagram/templates/aws-multi-vpc.drawio
git commit -m "fix(architecture-diagram): aws-multi-vpc passes layout gate (icons 78x78, title, grid)"
```

---

### Task 2: aws-samples.drawio → ≥80

**Files:**
- Modify: `plugins/aws-content-plugin/skills/architecture-diagram/templates/aws-samples.drawio`

- [ ] **Step 1: Confirm RED** — `python3 $SK/scripts/lint_layout.py $SK/templates/aws-samples.drawio` → score 71 (<80). Deductions: no title; 15 labels not Amazon Ember; 15 off-5px-grid; 18 edges (soft spaghetti note).

- [ ] **Step 2: Apply surgical fixes**
  - Add a **title** text cell (fontSize≥14, Amazon Ember) at the top.
  - Set the **font** of the 15 labeled cells to **Amazon Ember** (fontFamily in the style string; Helvetica fallback) per design-tokens.md.
  - Snap the 15 off-grid elements to the nearest multiple of 5 (surgical; this file tolerated the grid snap well — geometry rose to 94 in testing — but verify no containment breaks).
  - If still <80 after title+fonts+grid, apply the **numbered-flow** pattern (badges + legend) to the secondary edges to reduce the 18-edge spaghetti penalty. Only if needed.

- [ ] **Step 3: Verify GREEN** —
  `validate_drawio.py` clean; `lint_layout.py` → **≥80, exit 0**;
  `bash tests/run-all.sh 2>&1 | grep "aws-samples"` → `ok`.

- [ ] **Step 4: Commit**

```bash
git add plugins/aws-content-plugin/skills/architecture-diagram/templates/aws-samples.drawio
git commit -m "fix(architecture-diagram): aws-samples passes layout gate (title, Amazon Ember fonts, grid)"
```

---

## Notes for the implementer
- **No blind `snap_grid.py`** — surgical per-element grid fixes only (it regressed multi-vpc 70→67).
- Preserve valid draw.io XML (`validate_drawio.py`) and don't touch other templates / the gate script / `layout_aws.py`.
- The multi-model gate judges visual polish on top of the lint floor — aim for a diagram that reads as finished, not just barely-80.
- After both tasks: full `tests/run-all.sh` green (31 & 33 flip to ok; others stay green).
