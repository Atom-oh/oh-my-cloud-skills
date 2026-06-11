# Architecture-Diagram Layout-Gate Remediation — Design Spec

- **Date**: 2026-06-11
- **Status**: Approved (direction) — pending implementation plan
- **Branch**: `feat/architecture-diagram-improvements` (worktree; PR #55)
- **Target**: `plugins/aws-content-plugin/skills/architecture-diagram/templates/`

## Problem

Two committed templates fail the `lint_layout.py` design+geometry gate (80-point), so `tests/run-all.sh` is red (tests 31 & 33) and PR #55 cannot merge:
- **`aws-multi-vpc.drawio`** — 70/100 [geometry 88 · design 82]: 3 off-scale icons (40×40, 60×60 → must be **78×78**, or 48×48 if nested), **no title**, 2 elements off the 5px grid, 2 rows/cols with uneven spacing.
- **`aws-samples.drawio`** — 71/100 [geometry 86 · design 85]: **no title**, 15 labeled elements not using **Amazon Ember/Helvetica**, 15 elements off the 5px grid, 18 edges (>12) spaghetti risk.

The other templates (aws-basic, aws-hybrid-idc, aws-ppt-content) already pass; the negative test (messy diagram fails) passes — so the gate itself is correct.

## Goal

Bring both templates to **lint_layout ≥ 80** so tests 31 & 33 pass, **without** regressing the other templates or violating the design canon in `references/design-tokens.md`.

## Constraints (locked)

- **No blind `snap_grid.py`**: running it on `aws-multi-vpc` *regressed* it 70→67 (10px snap disturbed alignment). Grid drift must be fixed **surgically** — snap only the specific off-grid elements to the nearest 5px, preserving containment/spacing.
- **Icon canon**: one icon size — **78×78** (48×48 only when nested), per `design-tokens.md`. 40/60/64 are retired.
- **Fonts**: labeled cells use **Amazon Ember** (Helvetica fallback) per `design-tokens.md`.
- **Title**: every diagram needs a heading text cell (fontSize ≥ 14) at the top — match the title-cell pattern used by a *passing* template (e.g. aws-hybrid-idc).
- **Edges (aws-samples)**: 18 edges is a *soft* "consider" note; prefer the numbered-flow pattern (badges + legend) for secondary connections only if needed to clear 80 — do not over-restructure a working diagram.
- Do **not** touch passing templates, `layout_aws.py`, or the gate script. Valid draw.io XML must be preserved (`validate_drawio.py` clean).

## Success criterion (mechanical — this IS the test)

For each template: `python3 scripts/lint_layout.py <template>` exits 0 (score ≥ 80), and the corresponding `tests/run-all.sh` assertion (31/33) flips to `ok`. `validate_drawio.py` stays clean. Full suite green.

## Architecture / approach (per template)

**aws-multi-vpc** (70 → ≥80): resize the 3 off-scale icons to 78×78; add a title cell; surgically snap the 2 off-grid elements to the nearest 5px; even out the 2 uneven rows/cols.
**aws-samples** (71 → ≥80): add a title cell; set the 15 labels' font to Amazon Ember; surgically snap the 15 off-grid elements; if still < 80, apply numbered-flow badges to the secondary edges.

Quality is judged by the multi-model consensus gate (does it read as a finished, polished AWS diagram?) on top of the mechanical lint floor.

## Testing

- Per template: `lint_layout.py` ≥ 80 + `validate_drawio.py` clean.
- `tests/run-all.sh` → all green (31 & 33 flip to ok; the other template gates stay green).

## Phasing

1. **aws-multi-vpc** → ≥80 (icons 78×78 + title + surgical grid + spacing).
2. **aws-samples** → ≥80 (title + Amazon Ember fonts + surgical grid + optional numbered-flow).

## Out of scope

- Regenerating templates via `layout_aws.py` (these two are hand/browser-authored, not engine outputs).
- Changing the gate thresholds or `design-tokens.md` canon.
- The worktree's missing untracked `.claude/hooks/` (environment artifact, not a branch defect).
