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

- [ ] **Step 2: Apply surgical fixes** (resize+title alone is expected to reach ~88 ≥ 80 — keep it minimal)
  - Resize the 3 off-scale icon cells to **78×78** (width/height); if an icon is nested inside a group/container, 48×48 is allowed. Keep their grid-aligned top-left. (The Transit Gateway icon at 60×60 is one of these.)
  - Add a **title** text cell at the top: a heading `mxCell` with `fontSize≥14`, `fontFamily=Amazon Ember`, value e.g. "Multi-VPC Architecture". **Placement constraints**: non-negative coords (negative coords trigger the canvas-margin deduction) and within the top band (y between 0 and ~140, e.g. y≈5); match aws-hybrid-idc's title-cell pattern.
  - **Do NOT equalize spacing or run a blind grid snap** — moving sibling icons risks a real overlap (fails the overlap regression guard) and re-introduces off-grid drift, for ~zero score benefit. ONLY if lint is still <80 after resize+title: surgically snap the 2 named off-grid elements to the nearest 5 (`tgw` 756→755, `cloudwatch` 147→145), then re-check overlap=0.
  - Do not change icon glyphs (the subnet glyph fix from 6ffa91f stays).

- [ ] **Step 3: Verify GREEN** (mechanical) —
  `python3 $SK/scripts/validate_drawio.py $SK/templates/aws-multi-vpc.drawio` → clean (valid XML, no overlaps);
  `python3 $SK/scripts/lint_layout.py $SK/templates/aws-multi-vpc.drawio; echo "exit=$?"` → score **≥80, exit 0**;
  then the SUITE must be green: `bash tests/run-all.sh; echo "suite exit=$?"` → **exit 0** (do NOT `grep "aws-multi-vpc"` — that matches `not ok` too and false-passes). If <80, read the remaining deductions and iterate.

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

- [ ] **Step 2: Apply surgical fixes** (title+fonts alone is expected to reach ~86 ≥ 80 — edges/grid are optional)
  - Add a **title** text cell (fontSize≥14, `fontFamily=Amazon Ember`) at the top — non-negative coords, top band (y 0–~140).
  - Set the **font** of **all 15 labeled cells** to **Amazon Ember** (fontFamily in the style string; Helvetica fallback) — D5 counts every labeled vertex, incl. the non-resIcon ones (illustration_*, lambda_function, role, cloudwatch-shape), not just resIcons.
  - **Optional, only if lint <80 after title+fonts**: surgically snap the off-grid `.5` coords to the nearest 5 (this file tolerated snapping — geometry rose to 94 — but verify containment), and/or apply the **numbered-flow** pattern (badges + legend) to secondary edges to ease the 18-edge note. Do not over-restructure a working diagram.

- [ ] **Step 3: Verify GREEN** (mechanical) —
  `validate_drawio.py` clean; `lint_layout.py … ; echo exit=$?` → **≥80, exit 0**;
  `bash tests/run-all.sh; echo "suite exit=$?"` → **exit 0** (do NOT grep the template name — `not ok` matches too).

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
