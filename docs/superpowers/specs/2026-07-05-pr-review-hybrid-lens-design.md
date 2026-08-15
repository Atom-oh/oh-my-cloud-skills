# CI PR Review — Hybrid Lens Gate Redesign

**Status:** Historical — implemented (PR #103/#104, ADR-011). The model roster/flag
notation in this document (e.g. Kiro `kimi-k2.5`, `--v3 --mode default --trust-tools=fs_read`)
is a snapshot from design time and has not been updated since. **Treat
`docs/ci-pr-review.md`/the runbook/`scripts/pr-review/run-panel.sh` as the source of truth
for current live values** (the roster moved to `gpt-5.5` in ADR-012, and `--v3` was
removed in the same ADR).
**Date:** 2026-07-05
**Author:** Junseok Oh (with Claude)
**Scope:** `.github/workflows/pr-review.yml` + `scripts/pr-review/*`
**Related docs:** ADR-009 (current panel), ADR-011 (this design's matrix), ADR-012
(roster replacement), `docs/ci-pr-review.md`, `plugins/co-agent/skills/co-agent/references/hybrid-gate.md`

## 1. Summary

The current CI PR review (ADR-009) **diversifies reviewers** — Codex + Kiro×3 each review
the diff independently with the **same "look at everything" prompt**, and a Claude chair
synthesizes. The problem is that the only axis of diversity is **model vendor**, so 4 AIs
redundantly solve the same exam, and if they all miss a particular area (e.g. version
consistency, dangling references), **everyone misses it identically.** There's also no
stage that filters false positives, so noise flows straight into the comment.

This design expands the diversity axis into a **vendor × lens (perspective) matrix** — it
splits this marketplace's review scope into 5 lenses (§3), and has **each vendor×model
review each lens as an independent agent → the Claude chair synthesizes** (user decision:
full matrix with no cost constraint, §4.1). Conceptually, this ports the
**hybrid-gate (parallel find → chair triage → [optional] parallel verify)** pattern that
`co-agent:harness` already uses in this repo into CI.

Key insight: of the 5 lenses, **1 (Manifest Integrity) can be deterministically verified
by a script rather than an AI**, and that's more accurate anyway. So the gate is split
into a **deterministic pre-check (no AI) + AI judgment lenses**.

## 2. Goals / Non-Goals

**Goals**
- **Systematize** review coverage — give each review area a "responsible lens" to
  eliminate blind spots.
- Route **deterministically verifiable things** (JSON validity, dangling references,
  version consistency) to a script rather than an AI → zero false positives, fast,
  fail-closed.
- Focus AI on **areas requiring judgment** (security reasoning, code logic, skill
  description quality, doc consistency), while keeping vendor diversity.
- Add **chair triage (+ optional verify)** to remove unsupported findings (a stage the
  current design lacks).
- Preserve current invariants: `pull_request_target` base-checkout security, fail-closed
  `VERDICT`, comment upsert, data-residency policy (Kiro external transmission), timeouts,
  chair fallback.

**Non-Goals**
- Do not reuse the co-agent plugin (`co_agent_config.py`, etc.) in CI — CI stays
  independent as bash scripts (minimizing runner-image dependencies). hybrid-gate is
  referenced **conceptually only**.
- No new AI vendor added (keep Codex + Kiro×3; agy remains unable to run headlessly —
  ADR-010).
- No enabling of fork-PR review (keep the current `head.repo.full_name` gate).

## 3. Lens Classification (mapped to marketplace review areas)

The current `synthesize.sh` checklist is reorganized directly into 5 lenses. **L1 is
deterministic, L2–L5 are AI.**

| Lens | Name | Method | Review scope |
|------|------|------|-----------|
| **L1** | Manifest Integrity | **Script (deterministic)** | `plugin.json`/`marketplace.json` JSON validity, dangling agent/skill/command references, version consistency (plugin.json↔marketplace.json — git-tag consistency is out of scope: the PR head is a `.git`-less tree extracted via `git archive`, so `git describe` itself isn't possible) |
| **L2** | Skill/Agent Quality | AI | SKILL.md/agent frontmatter presence/structure, description trigger accuracy (vagueness/overreach), name collisions |
| **L3** | Security | AI | Hardcoded secrets, hook bash safety (destructive commands, unquoted variables, arbitrary code execution), script permissions |
| **L4** | Code Correctness | AI | Actual logic bugs/edge cases in `scripts/*.py`, `*.sh`, TS (remarp-vscode) |
| **L5** | Documentation Consistency | AI | README ↔ README.ko sync, co-agent panel notation consistency, architecture.md counts, missing bilingual content |

> L1 is implemented by reusing `scripts/test-plugins.py` (already exists) + the version-
> consistency snippet from `CLAUDE.md`. Since it validates the entire manifest set
> regardless of the diff and requires no AI call, it's the most reliable gate.

## 4. Phase Structure (F → T → V, adapted for CI)

hybrid-gate.md's round structure is condensed into a single CI round. In CI, a human fixes
things and pushes again to re-trigger the workflow, so **an internal loop-until-done
inside the workflow is unnecessary** — one round runs, and when a human fixes and pushes,
the next run naturally becomes the next round.

```
[L1 deterministic pre-check]  ── on FAIL, immediate fail-closed (before any AI call, zero cost)
        │ PASS
        ▼
[Phase F] parallel find  ── lens×model matrix fan-out: 4 models × L2–L5 = 16 agents (§4.1)
        │              each cell reviews only its own single lens, emits findings with severity tags
        ▼
[Phase T] chair triage ── Claude chair: citation verification → cross-check against diff → dedupe (lens/file/line)
        │              → remove unsupported/duplicate/trivial → produce a curated digest
        │              (empty digest → PASS, skip Phase V)
        ▼
[Phase V] parallel verify ── (optional — §4.1.1, omitted in single-round mode) re-fan-out the digest to the panel,
        │              CONFIRM/REFUTE per finding → only findings with majority support & chair code re-verification survive
        ▼
[VERDICT] FAIL if any surviving CRITICAL/MAJOR, else PASS (fail-closed preserved)
        ▼
[Comment upsert]  grouped by lens + consensus/dissent notation
```

### 4.1 Phase F — lens × model full matrix (decided)

**User decision (2026-07-05): go with the full matrix, with no cost constraint.** Each
panel member (vendor×model) reviews **each of L2–L5 as an independent agent** → the chair
synthesizes.

```
                L2(Quality)  L3(Security)  L4(Code)  L5(Docs)
Codex(gpt-5.5)    ▪         ▪         ▪         ▪
Kiro(opus-4.8)    ▪         ▪         ▪         ▪
Kiro(kimi-k2.5)   ▪         ▪         ▪         ▪
Kiro(glm-5)       ▪         ▪         ▪         ▪
```

= **4 models × 4 AI-lenses = 16 find agents** (L1 is a deterministic pre-check and outside
the matrix). All run **in parallel** (`&`+`wait`) so wall-clock time ≈ the single slowest
agent. Benefits:

- **4 independent opinions per lens** — cross-verification is already built into the find
  stage (decorrelates vendor bias).
- **4 lenses dedicated per model** — each model focuses per-perspective rather than
  "look at everything."
- Both diversity axes (**vendor × perspective**) maximized simultaneously — the most
  thorough coverage possible.

> Matrix cells are derived from `model list × lens list` (no hardcoding — extends the
> `KIRO_MODELS` array pattern already in `run-panel.sh`). If a particular CLI/model is
> missing, that entire **row is skipped gracefully**, and other models still cover the same
> lens, so no lens ever goes completely uncovered.

### 4.1.1 Revisiting the need for verify (Phase V)

Since the full matrix already gives 4x cross-verification per lens at the find stage,
verify is made **optional**:

- **(single round) matrix → chair synthesis** *(the form the user described, recommended
  starting point)* — the chair triages (citation check, code cross-check, dedupe) the 16
  finds, and that triage itself serves as verification. No separate V round. Simple, and
  matrix redundancy already absorbs most false positives.
- **(two-stage) matrix → chair digest → verify re-fan-out** — the full hybrid-gate form.
  The chair re-sends the digest to the 16 cells (or an In-Region subset) for
  CONFIRM/REFUTE. Highest precision assuming cost is ignored, but overlaps substantially
  with the matrix find's redundancy, so marginal gains diminish.

Recommendation: **start with single-round matrix → chair synthesis**, and add verify only
if false positives actually become a problem.

### 4.2 Phase T — chair triage (no external calls)

Performed by the chair (Claude Fable 5 → Opus fallback):
1. Citation verification — remove findings that reference a nonexistent file/line.
2. **Cross-check against the diff** — panel consensus is only a signal, not evidence
   (shared training bias). Confirm against the actual changes.
3. Dedupe (lens/file/line) and keep only what's meaningful — every CRITICAL/MAJOR
   candidate plus any MINOR the chair judges load-bearing. Remove style noise.
4. Write the digest (`/tmp/pr-review/digest.md`) — per finding: claim, severity, evidence
   (file/line), which panel member raised it. Keep it small (it must fit in the verify
   context).
   If the digest has **zero findings, the gate PASSes and Phase V is skipped** (verifying
   an empty digest would only invent findings).

### 4.3 Phase V — parallel verify

Re-fan-out the digest to the same panel (fixed verify prompt: CONFIRM/REFUTE per numbered
finding + cite evidence; do not restate the digest; only a missed CRITICAL may be newly
raised). The chair closes the round:
- A finding survives only if it passes **both** majority verify support **AND** the
  chair's own code re-verification.
- A well-supported majority REFUTE → removed (attribution noted: "N/M refuted").
- A new CRITICAL raised in Phase V → re-verified via triage and, if confirmed, folded into
  the digest (reflected in this verdict; the round itself is not restarted — single round
  in CI).

## 5. File changes vs. current

| File | Change |
|------|------|
| `.github/workflows/pr-review.yml` | Add an L1 deterministic pre-check step (before AI, early exit on FAIL). Generate 4 per-lens prompts (L2–L5). Extend the synthesize call to F→T (→ optional V). Render lens groups in the comment. |
| `scripts/pr-review/run-panel.sh` | Extend the fan-out loop into a `model list × LENSES` double loop — per-cell slot `slot/<tag>-<lens>.md`, and record "responded" per cell. If Phase V is adopted, reuse the same script for digest re-fan-out by parameterizing the prompt/input. |
| `scripts/pr-review/synthesize.sh` | Split into two roles — triage (digest generation) + verify synthesis — or parameterize by stage. Preserve the existing Fable→Opus fallback and fail-closed VERDICT logic. |
| `scripts/pr-review/precheck.sh` *(new)* | L1 deterministic validation — `test-plugins.py` + version consistency. Non-zero exit on FAIL. |
| `scripts/pr-review/lib.sh` | Extend shared helpers (slot/digest paths). |
| `tests/pr-review/*` | Add unit tests for precheck/triage/verify. |

## 6. Preserved invariants (unchanged)

- **Security**: `pull_request_target` + base-ref checkout (scripts are the trusted
  context, the diff is data). No fork-PR execution
  (`head.repo.full_name == github.repository`).
- **Data residency**: Codex/Claude = Bedrock us-east-1 In-Region (Pod Identity SigV4);
  Kiro = external API (diff sent externally). The Kiro-skip convention for sensitive diffs
  (ADR-009) stays as-is. Whether the verify stage sends the diff externally (Kiro) **a
  second time** needs confirmation in §8 Q2.
- **Fail-closed**: last line `VERDICT: PASS|FAIL`, FAIL if absent. L1 pre-check FAIL also
  fails immediately.
- **Comment upsert**: `<!-- oh-my-cloud-skills-pr-review -->` marker.
- **Chair fallback**: one fallback to Opus 4.8 if Fable 5 degrades.
- **Injection mitigation**: directives inside the panel/diff are treated purely as data;
  the verdict is decided only by rule; the chair cross-checks against the code.

## 7. Cost & Sizing

**User decision: token/dollar cost is not a constraint.** The only real remaining
constraints are **wall-clock time + runner concurrency**.

- AI calls/PR = single-round matrix means **16 find + 1 chair synthesis** (+16 verify for
  the two-stage version). Cost is disregarded.
- **Wall-clock time is actually likely to be shorter than the current design**: the 16
  finds run concurrently via `&`+`wait`, so wall-clock ≈ the single slowest cell (not a
  sequential sum). On top of that, per-cell scope narrows from the current "look at
  everything" to **a single lens**, so each cell's output generation is shorter and
  faster — **the slowest-of-16 (narrow scope) is likely faster than the slowest-of-4
  (full-scope)**. The retry probability also drops in tandem, since a smaller per-cell
  response is less likely to hit the timeout (300s).
- **2 offsetting factors (working against net gains)**: (1) the chair's input grows from
  4→16 outputs, lengthening the synthesis call — `CHAIR_TIMEOUT` (currently 120s) may need
  to be raised. However, lens-tagged input makes the chair's dedupe/grouping easier, so
  quality actually improves. (2) API rate limits — below.
- **The only real ceiling = runner concurrency + the 50-minute job timeout**. The
  self-hosted runner must handle 16 concurrent subprocesses (CPU/memory, API rate limits).
  Since the Kiro row is 12 cells (3 models × 4 lenses), Kiro API rate limits are the
  leading bottleneck candidate — if hit, retries would extend wall-clock time → observe,
  and if needed, split lenses into 2 batches or raise the timeout (§8 Q3).

## 8. Open Decisions (must be settled before implementation starts)

- **Q1 — lens assignment**: **Decided** — full matrix (lens × model), 16 find agents
  (§4.1).
- **Q2 — verify's external re-transmission**: if the two-stage version is adopted, Phase V
  sends the diff+digest **again** to Kiro (external). Not applicable for the single-round
  matrix. (Residency is accepted-risk since this is a public marketplace.)
- **Q3 — the actual ceiling**: not cost, but **runner concurrency/wall-clock time**.
  Observe whether 16 concurrent subprocesses run without hitting rate limits → split into
  batches or raise the job timeout if needed.
- **Q4 — single-round vs. two-stage**: single-round matrix→chair (recommended start) vs.
  two-stage hybrid (add verify). §4.1.1.
- **Q5 — ADR**: since this redesign changes ADR-009's "same-prompt fan-out," a **new ADR
  that supersedes/amends ADR-009** is required at implementation time (lens×model matrix
  + deterministic pre-check).

## 9. Migration & Compatibility

- Phased: (1) add the L1 deterministic pre-check first (immediate benefit, low risk) →
  (2) lens×model matrix fan-out + chair synthesis (single-round mode) → (3) add Phase V
  (verify) if false positives become a problem. Each stage is independently valuable, so
  incremental adoption is possible.
- Under the base-script execution model, review-logic changes take effect **starting with
  the PR after the one that introduces them** (no self-verification — ADR-009).
- Rollback: revert the scripts/workflow to return to the current single-round fan-out.
